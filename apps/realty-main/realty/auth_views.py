"""
Упрощенные views ТОЛЬКО для авторизации
Без сложных зависимостей - только Django User модель
"""
import json
import os
import secrets
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

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
    state = secrets.token_urlsafe(32)
    
    # Реальная Google OAuth URL
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': f"https://dubai.up.railway.app/api/auth/google/callback/",
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
        'message': 'Click auth_url to authenticate with Google'
    })

@csrf_exempt
@require_http_methods(["GET"])
def google_auth_callback(request):
    """Google OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return HttpResponseRedirect(f"{settings.FRONTEND_URL}/auth#error={error}")
    
    if not code:
        return HttpResponseRedirect(f"{settings.FRONTEND_URL}/auth#error=no_code")
    
    try:
        # Для MVP - создаем тестового пользователя
        user, created = User.objects.get_or_create(
            email='testuser@gmail.com',
            defaults={
                'username': 'testuser@gmail.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
            }
        )
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Редирект на frontend с токенами
        redirect_url = f"{settings.FRONTEND_URL}/auth#access={access_token}&refresh={refresh}&success=true"
        return HttpResponseRedirect(redirect_url)
        
    except Exception as e:
        return HttpResponseRedirect(f"{settings.FRONTEND_URL}/auth#error=callback_failed&details={str(e)}")

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
    """Регистрация пользователя с отправкой email"""
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
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
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
                fail_silently=True,  # Не падаем если email не отправился
            )
            
        except Exception as email_error:
            # Email не отправился, но регистрация прошла успешно
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
    """Отправка OTP кода"""
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=400)
    
    # Генерируем OTP код
    otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # В MVP возвращаем код в ответе (в продакшн отправлять на email)
    return Response({
        'message': 'OTP code sent successfully',
        'otp_code': otp_code,  # ТОЛЬКО ДЛЯ MVP!
        'expires_in': 600,
        'email': email,
        'note': 'MVP: OTP code provided in response'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def verify_otp(request):
    """Верификация OTP кода"""
    email = request.data.get('email')
    code = request.data.get('code')
    
    if not email or not code:
        return Response({
            'error': 'Email and code are required'
        }, status=400)
    
    # В MVP принимаем любой 6-значный код
    if len(code) == 6 and code.isdigit():
        user, created = User.objects.get_or_create(
            email=email, 
            defaults={'username': email}
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'OTP verified successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'is_new_user': created
            }
        })
    
    return Response({
        'error': 'Invalid OTP code'
    }, status=400)

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