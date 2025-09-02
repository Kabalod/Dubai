"""
Полноценная система аутентификации с Google OAuth и OTP
Поддержка регистрации через email с OTP кодами и Google OAuth
"""
import json
import os
import secrets
import requests
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPCode, GoogleOAuthState, UserProfile

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Простой health check"""
    # Диагностика database подключения
    db_engine = settings.DATABASES['default']['ENGINE']
    db_name = str(settings.DATABASES['default']['NAME'])
    db_url_exists = bool(os.environ.get('DATABASE_URL'))
    
    return Response({
        "status": "ok",
        "service": "auth-backend",
        "debug": settings.DEBUG,
        "database": db_engine.split('.')[-1],  # 'postgresql' или 'sqlite3'
        "database_name": db_name,
        "database_url_set": db_url_exists,
        "auth": "ready"
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_init(request):
    """Инициация Google OAuth"""
    try:
        # Создаем состояние OAuth для безопасности
        oauth_state = GoogleOAuthState.generate_state()
        
        # Определяем redirect URI в зависимости от окружения
        if settings.DEBUG:
            redirect_uri = "http://localhost:8000/api/auth/google/callback/"
        else:
            redirect_uri = "https://dubai.up.railway.app/api/auth/google/callback/"
        
        # Создаем URL для Google OAuth
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': oauth_state.state,
            'access_type': 'online',
            'prompt': 'select_account'
        }
        
        auth_url = f"{base_url}?{urlencode(params)}"
        
        return Response({
            'auth_url': auth_url,
            'state': oauth_state.state,
            'redirect_uri': redirect_uri,
            'message': 'Click auth_url to authenticate with Google'
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to initialize Google OAuth',
            'details': str(e) if settings.DEBUG else 'Please try again'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def google_auth_callback(request):
    """Google OAuth callback с реальной интеграцией"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    
    if error:
        return HttpResponseRedirect(f"{frontend_url}/auth#error={error}")
    
    if not code or not state:
        return HttpResponseRedirect(f"{frontend_url}/auth#error=missing_params")
    
    try:
        # Проверяем состояние OAuth
        oauth_state = GoogleOAuthState.objects.filter(
            state=state,
            is_used=False
        ).first()
        
        if not oauth_state or not oauth_state.is_valid():
            return HttpResponseRedirect(f"{frontend_url}/auth#error=invalid_state")
        
        # Помечаем состояние как использованное
        oauth_state.mark_used()
        
        # Обмениваем код на токены Google
        redirect_uri = "https://dubai.up.railway.app/api/auth/google/callback/"
        if settings.DEBUG:
            redirect_uri = "http://localhost:8000/api/auth/google/callback/"
            
        token_data = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }
        
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data=token_data,
            timeout=10
        )
        
        if not token_response.ok:
            return HttpResponseRedirect(f"{frontend_url}/auth#error=token_exchange_failed")
        
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        
        if not access_token:
            return HttpResponseRedirect(f"{frontend_url}/auth#error=no_access_token")
        
        # Получаем информацию о пользователе из Google
        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if not user_response.ok:
            return HttpResponseRedirect(f"{frontend_url}/auth#error=user_info_failed")
        
        google_user = user_response.json()
        google_id = google_user.get('id')
        email = google_user.get('email')
        first_name = google_user.get('given_name', '')
        last_name = google_user.get('family_name', '')
        
        if not email or not google_id:
            return HttpResponseRedirect(f"{frontend_url}/auth#error=incomplete_user_data")
        
        # Создаем или получаем пользователя
        with transaction.atomic():
            # Сначала проверяем по Google ID
            try:
                profile = UserProfile.objects.get(google_id=google_id)
                user = profile.user
                created = False
            except UserProfile.DoesNotExist:
                # Проверяем по email
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': True
                    }
                )
                
                # Создаем или обновляем профиль
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'google_id': google_id,
                        'email_verified': True,
                        'registration_method': 'google_oauth'
                    }
                )
                
                if not profile_created and not profile.google_id:
                    profile.google_id = google_id
                    profile.email_verified = True
                    profile.save(update_fields=['google_id', 'email_verified'])
        
        # Создаем JWT токены
        refresh = RefreshToken.for_user(user)
        jwt_access_token = refresh.access_token
        
        # Редирект на frontend с токенами
        redirect_url = f"{frontend_url}/auth#access={jwt_access_token}&refresh={refresh}&success=true&method=google"
        return HttpResponseRedirect(redirect_url)
        
    except requests.RequestException as e:
        return HttpResponseRedirect(f"{frontend_url}/auth#error=google_api_error")
    except Exception as e:
        error_detail = str(e) if settings.DEBUG else "callback_failed"
        return HttpResponseRedirect(f"{frontend_url}/auth#error={error_detail}")

@api_view(['POST'])
@permission_classes([AllowAny])
def simple_login(request):
    """Простой логин для тестирования"""
    try:
        user, created = User.objects.get_or_create(
            email='test@test.com',
            defaults={
                'username': 'test@test.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
            }
        )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Login failed'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Регистрация пользователя через OTP (новый API)"""
    try:
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email:
            return Response({
                'error': 'Email is required',
                'message': 'Registration failed'
            }, status=400)
        
        # Проверяем что пользователь не существует
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'User with this email already exists',
                'message': 'Registration failed',
                'suggestion': 'Try logging in instead'
            }, status=400)
        
        # Создаем и отправляем OTP код
        otp = OTPCode.generate_for_email(email)
        email_sent = otp.send_email(
            subject='Dubai Real Estate - Registration Verification',
            template=f"""
Hello {first_name or 'there'}!

Thank you for registering with Dubai Real Estate Platform.

Your verification code is: {otp.code}

This code will expire in 10 minutes.

After verification, you'll have access to:
- Property listings and analytics
- Market insights and reports
- Advanced search filters

If you didn't request this registration, please ignore this email.

Best regards,
Dubai Real Estate Team
            """.strip()
        )
        
        response_data = {
            'message': 'Registration initiated. Please check your email for verification code.',
            'email': email,
            'email_sent': email_sent,
            'next_step': 'verify_otp'
        }
        
        # В режиме отладки возвращаем код
        if settings.DEBUG:
            response_data['otp_code'] = otp.code
            response_data['note'] = 'DEBUG: OTP code provided for testing'
        
        return Response(response_data, status=201)
        
    except Exception as e:
        return Response({
            'error': 'Registration failed',
            'details': str(e) if settings.DEBUG else 'Please try again later'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user_legacy(request):
    """Старый API регистрации с паролем (для совместимости)"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email or not password:
            return Response({
                'error': 'Email and password are required',
                'message': 'Registration failed'
            }, status=400)
        
        # Проверяем что пользователь не существует
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'User already exists',
                'message': 'Registration failed'
            }, status=400)
        
        # Создаем пользователя
        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Создаем профиль
            UserProfile.objects.create(
                user=user,
                email_verified=True,  # считаем верифицированным при регистрации с паролем
                registration_method='admin'  # или 'password'
            )
        
        # Отправляем приветственное письмо
        try:
            subject = 'Welcome to Dubai Real Estate Platform'
            message = f'''
            Hi {first_name or email}!
            
            Welcome to Dubai Real Estate Platform!
            Your account has been successfully created.
            
            You can now login to access property data and analytics.
            
            Best regards,
            Dubai Real Estate Team
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            
        except Exception as email_error:
            print(f"Email sending failed: {email_error}")
        
        # Генерируем токены для автоматического входа
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'email_sent': True
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Registration failed'
        }, status=500)


# --- Дополнительные endpoints для OTP и API ---

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """Получение CSRF токена"""
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    return Response({
        'csrfToken': csrf_token,
        'message': 'CSRF token generated'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def send_otp(request):
    """Отправка OTP кода на email"""
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=400)
    
    try:
        # Создаем или получаем OTP код
        otp = OTPCode.generate_for_email(email)
        
        # Отправляем email с кодом
        email_sent = otp.send_email(
            subject='Dubai Real Estate - Verification Code',
        )
        
        response_data = {
            'message': 'OTP code sent successfully',
            'email': email,
            'expires_in': 600,  # 10 минут
            'email_sent': email_sent
        }
        
        # В режиме отладки возвращаем код в ответе для тестирования
        if settings.DEBUG:
            response_data['otp_code'] = otp.code
            response_data['note'] = 'DEBUG: OTP code provided in response for testing'
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'error': 'Failed to send OTP code',
            'details': str(e) if settings.DEBUG else 'Please try again later'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def verify_otp(request):
    """Верификация OTP кода и создание/вход пользователя"""
    email = request.data.get('email')
    code = request.data.get('code')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not email or not code:
        return Response({
            'error': 'Email and code are required'
        }, status=400)
    
    try:
        # Находим действующий OTP код
        otp = OTPCode.objects.filter(
            email=email,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp:
            return Response({
                'error': 'No valid OTP code found for this email'
            }, status=400)
        
        # Верифицируем код
        if not otp.verify(code):
            remaining_attempts = max(0, otp.max_attempts - otp.attempts)
            return Response({
                'error': 'Invalid OTP code',
                'remaining_attempts': remaining_attempts,
                'code_expired': not otp.is_valid()
            }, status=400)
        
        # Код верный - создаем или получаем пользователя
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            
            # Создаем или обновляем профиль
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'email_verified': True,
                    'registration_method': 'email_otp'
                }
            )
            
            if not profile.email_verified:
                profile.email_verified = True
                profile.save(update_fields=['email_verified'])
        
        # Создаем JWT токены
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'OTP verified successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email_verified': profile.email_verified,
                'is_new_user': created
            }
        })
        
    except Exception as e:
        return Response({
            'error': 'OTP verification failed',
            'details': str(e) if settings.DEBUG else 'Please try again'
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_stats(request):
    """Mock статистика для MVP"""
    return Response({
        'total_properties': 1250,
        'avg_price': 850000,
        'price_change': 5.2,
        'total_sales': 89,
        'status': 'ok'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_properties(request):
    """Mock свойства для MVP"""
    return Response({
        'results': [
            {
                'id': '1',
                'title': 'Luxury Apartment in Downtown Dubai',
                'price': 1200000,
                'area': 'Downtown Dubai',
                'bedrooms': 2,
                'bathrooms': 2
            },
            {
                'id': '2', 
                'title': 'Villa in Palm Jumeirah',
                'price': 3500000,
                'area': 'Palm Jumeirah',
                'bedrooms': 4,
                'bathrooms': 5
            }
        ],
        'count': 2,
        'status': 'ok'
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def force_login(request):
    """Принудительный логин для тестирования"""
    email = request.GET.get('email') or request.data.get('email') or 'admin@test.com'
    
    # Создаем или получаем пользователя
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Создаем JWT токены
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Force login successful',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_new_user': created
        },
        'note': 'TESTING ONLY - auto-created admin user'
    })