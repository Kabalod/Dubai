"""
Улучшенная система аутентификации без дополнительных моделей
Поддержка Google OAuth и OTP через cache/session
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
from django.core.cache import cache
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# === CACHE KEYS ===
OTP_CACHE_KEY = "otp:{email}"
OAUTH_STATE_CACHE_KEY = "oauth_state:{state}"

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Простой health check"""
    db_engine = settings.DATABASES['default']['ENGINE']
    db_name = str(settings.DATABASES['default']['NAME'])
    db_url_exists = bool(os.environ.get('DATABASE_URL'))
    
    return Response({
        "status": "ok",
        "service": "auth-backend-enhanced",
        "debug": settings.DEBUG,
        "database": db_engine.split('.')[-1],
        "database_name": db_name,
        "database_url_set": db_url_exists,
        "auth": "ready",
        "features": ["google_oauth", "otp_email", "jwt_tokens"]
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
        # Генерируем OTP код
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Сохраняем в cache на 10 минут
        cache_key = OTP_CACHE_KEY.format(email=email)
        cache_data = {
            'code': otp_code,
            'attempts': 0,
            'max_attempts': 3,
            'created_at': timezone.now().isoformat()
        }
        cache.set(cache_key, cache_data, timeout=600)  # 10 минут
        
        # Отправляем email
        subject = 'Dubai Real Estate - Verification Code'
        message = f"""
Hello!

Your verification code for Dubai Real Estate Platform is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Dubai Real Estate Team
        """.strip()
        
        email_sent = True
        try:
            # Детальное логирование
            print(f"📧 Отправляем OTP email на {email} с кодом: {otp_code}")
            print(f"📧 From email: {settings.DEFAULT_FROM_EMAIL}")
            print(f"📧 Email backend: {settings.EMAIL_BACKEND}")
            
            if hasattr(settings, 'ANYMAIL') and settings.ANYMAIL.get('SENDGRID_API_KEY'):
                print(f"📧 SendGrid API Key: {settings.ANYMAIL['SENDGRID_API_KEY'][:20]}...")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            print(f"✅ OTP email успешно отправлен на {email}")
            
        except Exception as e:
            email_sent = False
            print(f"❌ Ошибка отправки OTP email: {e}")
            print(f"❌ Тип ошибки: {type(e).__name__}")
            
            if 'sendgrid' in str(e).lower() or 'forbidden' in str(e).lower():
                print("❌ Возможные причины SendGrid ошибки:")
                print("   - Неверный API ключ")
                print("   - From email не верифицирован в SendGrid")
                print("   - Недостаточно прав у API ключа")
        
        response_data = {
            'message': 'OTP code sent successfully',
            'email': email,
            'expires_in': 600,
            'email_sent': email_sent
        }
        
        # Определяем когда показывать OTP код
        is_production = os.environ.get('RAILWAY_ENVIRONMENT_NAME') is not None
        
        # В DEBUG режиме или когда используется file backend добавляем OTP код
        if settings.DEBUG and not is_production:
            response_data['otp_code'] = otp_code
            response_data['note'] = 'DEBUG: OTP code provided for testing'
        elif 'filebased' in settings.EMAIL_BACKEND:
            response_data['otp_code'] = otp_code
            response_data['note'] = 'Development: OTP code (check /tmp/emails/ for email content)'
        
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
        # Получаем данные из cache
        cache_key = OTP_CACHE_KEY.format(email=email)
        cache_data = cache.get(cache_key)
        
        if not cache_data:
            return Response({
                'error': 'No valid OTP code found for this email or code expired'
            }, status=400)
        
        # Проверяем попытки
        if cache_data['attempts'] >= cache_data['max_attempts']:
            cache.delete(cache_key)
            return Response({
                'error': 'Too many failed attempts. Please request a new code.'
            }, status=400)
        
        # Увеличиваем счетчик попыток
        cache_data['attempts'] += 1
        cache.set(cache_key, cache_data, timeout=600)
        
        # Проверяем код
        if cache_data['code'] != code:
            remaining_attempts = cache_data['max_attempts'] - cache_data['attempts']
            return Response({
                'error': 'Invalid OTP code',
                'remaining_attempts': remaining_attempts
            }, status=400)
        
        # Код верный - удаляем из cache и создаем/получаем пользователя
        cache.delete(cache_key)
        
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
def google_auth_init(request):
    """Инициация Google OAuth"""
    try:
        # Создаем состояние OAuth для безопасности
        state = secrets.token_urlsafe(32)
        
        # Сохраняем состояние в cache на 15 минут
        cache_key = OAUTH_STATE_CACHE_KEY.format(state=state)
        cache.set(cache_key, {
            'created_at': timezone.now().isoformat(),
            'used': False
        }, timeout=900)  # 15 минут
        
        # Определяем redirect URI
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
            'state': state,
            'access_type': 'online',
            'prompt': 'select_account'
        }
        
        auth_url = f"{base_url}?{urlencode(params)}"
        
        return Response({
            'auth_url': auth_url,
            'state': state,
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
    """Google OAuth callback"""
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
        cache_key = OAUTH_STATE_CACHE_KEY.format(state=state)
        cache_data = cache.get(cache_key)
        
        if not cache_data or cache_data.get('used', False):
            return HttpResponseRedirect(f"{frontend_url}/auth#error=invalid_state")
        
        # Помечаем как использованное
        cache_data['used'] = True
        cache.set(cache_key, cache_data, timeout=900)
        
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
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
        
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
def register_user(request):
    """Регистрация пользователя через OTP"""
    try:
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=400)
        
        # Проверяем что пользователь не существует
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'User with this email already exists',
                'suggestion': 'Try logging in instead'
            }, status=400)
        
        # Создаем простой OTP код вместо вызова функции
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Сохраняем в cache на 10 минут
        cache_key = OTP_CACHE_KEY.format(email=email)
        cache_data = {
            'code': otp_code,
            'attempts': 0,
            'max_attempts': 3,
            'created_at': timezone.now().isoformat()
        }
        cache.set(cache_key, cache_data, timeout=600)  # 10 минут
        
        # Отправляем email
        email_sent = True
        email_error = None
        
        try:
            subject = 'Dubai Real Estate - Verification Code'
            message = f"""Hello{' ' + first_name if first_name else ''}!

Your verification code for Dubai Real Estate Platform is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Dubai Real Estate Team""".strip()
            
            # Детальное логирование для диагностики
            print(f"📧 Отправляем email на {email} с OTP: {otp_code}")
            print(f"📧 From email: {settings.DEFAULT_FROM_EMAIL}")
            print(f"📧 Email backend: {settings.EMAIL_BACKEND}")
            
            # Проверяем наличие SendGrid настроек
            if hasattr(settings, 'ANYMAIL') and settings.ANYMAIL.get('SENDGRID_API_KEY'):
                print(f"📧 SendGrid API Key: {settings.ANYMAIL['SENDGRID_API_KEY'][:20]}...")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            print(f"✅ Email успешно отправлен на {email}")
            
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            print(f"❌ Тип ошибки: {type(e).__name__}")
            
            # Дополнительная диагностика для SendGrid ошибок
            if 'sendgrid' in str(e).lower() or 'forbidden' in str(e).lower():
                print("❌ Возможные причины SendGrid ошибки:")
                print("   - Неверный API ключ")
                print("   - From email не верифицирован в SendGrid")
                print("   - Недостаточно прав у API ключа")
            
            email_sent = False
            email_error = str(e)
        
        response_data = {
            'message': 'Registration initiated. Please check your email for verification code.',
            'email': email,
            'email_sent': email_sent,
            'next_step': 'verify_otp',
            'expires_in': 600
        }
        
        # Определяем когда показывать OTP код
        is_production = os.environ.get('RAILWAY_ENVIRONMENT_NAME') is not None
        
        # В DEBUG режиме или когда используется file backend добавляем OTP код
        if settings.DEBUG and not is_production:
            response_data['otp_code'] = otp_code
            response_data['note'] = 'DEBUG: OTP code provided for testing'
        elif 'filebased' in settings.EMAIL_BACKEND:
            response_data['otp_code'] = otp_code
            response_data['note'] = 'Development: OTP code (check /tmp/emails/ for email content)'
        
        # Добавляем информацию об ошибке если есть (только для разработки)
        if email_error and not is_production:
            response_data['email_error'] = email_error
        
        return Response(response_data, status=201)
        
    except Exception as e:
        return Response({
            'error': 'Registration failed',
            'details': str(e) if settings.DEBUG else 'Please try again later'
        }, status=500)

# Mock endpoints для тестирования
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

@api_view(['POST'])
@permission_classes([AllowAny])
def simple_login(request):
    """Простой логин для тестирования"""
    try:
        email = request.data.get('email', 'test@test.com')
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
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
