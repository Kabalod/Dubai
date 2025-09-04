"""
Полноценная система аутентификации с SendGrid OTP
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
from django.core.cache import cache
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# === CACHE KEYS ===
OTP_CACHE_KEY = "otp:{email}"
GOOGLE_STATE_CACHE_KEY = "google_state:{state}"

# === OTP STORAGE FUNCTIONS ===
def store_otp_data(email, data):
    """Сохраняем OTP данные в кэш с fallback на сессии"""
    cache_key = OTP_CACHE_KEY.format(email=email)
    try:
        cache.set(cache_key, data, timeout=600)
        print(f"✅ OTP сохранен в кэш: {cache_key}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения в кэш: {e}")
        # Fallback: сохраняем в базе данных
        try:
            from django.contrib.sessions.models import Session
            from django.utils import timezone
            import json
            
            # Создаем временную запись в базе данных
            from .models import OTPData
            OTPData.objects.update_or_create(
                email=email,
                defaults={
                    'data': json.dumps(data),
                    'expires_at': timezone.now() + timezone.timedelta(minutes=10)
                }
            )
            print(f"✅ OTP сохранен в БД как fallback: {email}")
            return True
        except Exception as db_error:
            print(f"❌ Ошибка сохранения в БД: {db_error}")
            return False

def get_otp_data(email):
    """Получаем OTP данные из кэша с fallback на БД"""
    cache_key = OTP_CACHE_KEY.format(email=email)
    try:
        data = cache.get(cache_key)
        if data:
            print(f"✅ OTP найден в кэше: {cache_key}")
            return data
    except Exception as e:
        print(f"❌ Ошибка получения из кэша: {e}")
    
    # Fallback: получаем из базы данных
    try:
        from .models import OTPData
        from django.utils import timezone
        import json
        
        otp_record = OTPData.objects.filter(
            email=email,
            expires_at__gt=timezone.now()
        ).first()
        
        if otp_record:
            data = json.loads(otp_record.data)
            print(f"✅ OTP найден в БД: {email}")
            return data
    except Exception as db_error:
        print(f"❌ Ошибка получения из БД: {db_error}")
    
    print(f"❌ OTP не найден для {email}")
    return None

def delete_otp_data(email):
    """Удаляем OTP данные из кэша и БД"""
    cache_key = OTP_CACHE_KEY.format(email=email)
    try:
        cache.delete(cache_key)
        print(f"✅ OTP удален из кэша: {cache_key}")
    except Exception as e:
        print(f"❌ Ошибка удаления из кэша: {e}")
    
    # Также удаляем из БД
    try:
        from .models import OTPData
        OTPData.objects.filter(email=email).delete()
        print(f"✅ OTP удален из БД: {email}")
    except Exception as db_error:
        print(f"❌ Ошибка удаления из БД: {db_error}")

# === HEALTH CHECK ===
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check для мониторинга"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'email_backend': settings.EMAIL_BACKEND,
        'sendgrid_configured': hasattr(settings, 'ANYMAIL') and bool(settings.ANYMAIL.get('SENDGRID_API_KEY'))
    })

# === CSRF TOKEN ===
@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """Возвращает CSRF токен для frontend"""
    from django.middleware.csrf import get_token
    return Response({'csrfToken': get_token(request)})

# === OTP FUNCTIONS ===

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
        cache_data = {
            'code': otp_code,
            'attempts': 0,
            'max_attempts': 3,
            'created_at': timezone.now().isoformat()
        }
        store_otp_data(email, cache_data)
        
        # Отправляем email
        subject = 'Dubai Real Estate - Verification Code'
        message = f"""Hello!

Your verification code for Dubai Real Estate Platform is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Dubai Real Estate Team""".strip()
        
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
        print(f"🔍 Ищем OTP для: {email}")
        cache_data = get_otp_data(email)
        print(f"🔍 Данные OTP: {cache_data}")
        
        if not cache_data:
            print(f"❌ OTP не найден для {email}")
            return Response({
                'error': 'No valid OTP code found for this email or code expired'
            }, status=400)
        
        # Проверяем попытки
        if cache_data['attempts'] >= cache_data['max_attempts']:
            delete_otp_data(email)
            return Response({
                'error': 'Too many failed attempts. Please request a new code.'
            }, status=400)
        
        # Проверяем код
        if cache_data['code'] != code:
            cache_data['attempts'] += 1
            store_otp_data(email, cache_data)
            return Response({
                'error': 'Invalid OTP code',
                'attempts_left': cache_data['max_attempts'] - cache_data['attempts']
            }, status=400)
        
        # Получаем пароль и данные пользователя из кэша ДО удаления
        cached_password = cache_data.get('password')
        cached_first_name = cache_data.get('first_name', first_name)
        cached_last_name = cache_data.get('last_name', last_name)
        
        # Код правильный - удаляем из cache
        delete_otp_data(email)
        
        # Создаем или получаем пользователя
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': cached_first_name,
                    'last_name': cached_last_name,
                    'is_active': True,
                }
            )
            
            # Если пользователь был создан и есть пароль - устанавливаем его
            if created and cached_password:
                user.set_password(cached_password)  # Правильно хешируем пароль
                print(f"✅ Password set for new user: {email}")
            
            # Обновляем имя если передано
            if cached_first_name and not user.first_name:
                user.first_name = cached_first_name
            if cached_last_name and not user.last_name:
                user.last_name = cached_last_name
            user.save()
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        
        print(f"✅ OTP верифицирован для {email}, пользователь {'создан' if created else 'найден'}")
        
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
                'is_active': user.is_active,
            }
        })
        
    except Exception as e:
        return Response({
            'error': 'OTP verification failed',
            'details': str(e) if settings.DEBUG else 'Please try again'
        }, status=500)

# === REGISTRATION ===
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def register_user(request):
    """Регистрация пользователя с автоматической отправкой OTP"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email:
            return Response({
                'error': 'Email is required',
                'message': 'Registration failed'
            }, status=400)
        
        if not password:
            return Response({
                'error': 'Password is required',
                'message': 'Registration failed'
            }, status=400)
        
        # Проверяем что пользователь не существует
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'User with this email already exists',
                'suggestion': 'Try logging in instead'
            }, status=400)
        
        # Генерируем OTP код
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Сохраняем в cache на 10 минут (включая пароль и данные пользователя)
        cache_data = {
            'code': otp_code,
            'password': password,  # Сохраняем пароль для создания пользователя
            'first_name': first_name,
            'last_name': last_name,
            'attempts': 0,
            'max_attempts': 3,
            'created_at': timezone.now().isoformat()
        }
        print(f"💾 Сохраняем OTP для: {email}")
        print(f"💾 Данные OTP: {cache_data}")
        store_otp_data(email, cache_data)
        print(f"✅ OTP сохранен на 10 минут")
        
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

# === GOOGLE OAUTH ===
@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_init(request):
    """Инициация Google OAuth"""
    try:
        state = secrets.token_urlsafe(32)
        
        # Сохраняем state в cache на 10 минут
        cache_key = GOOGLE_STATE_CACHE_KEY.format(state=state)
        cache.set(cache_key, {'created_at': timezone.now().isoformat()}, timeout=600)
        
        # Формируем URL для авторизации
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback'),
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
            'message': 'Redirect to auth_url to authenticate with Google'
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
    
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    if error:
        return HttpResponseRedirect(f"{frontend_url}/auth?error={error}")
    
    if not code or not state:
        return HttpResponseRedirect(f"{frontend_url}/auth?error=missing_parameters")
    
    try:
        # Проверяем state
        cache_key = GOOGLE_STATE_CACHE_KEY.format(state=state)
        if not cache.get(cache_key):
            return HttpResponseRedirect(f"{frontend_url}/auth?error=invalid_state")
        
        # Удаляем state из cache
        cache.delete(cache_key)
        
        # Обмениваем код на токен
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback')
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()
        
        # Получаем информацию о пользователе
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={tokens['access_token']}"
        user_response = requests.get(user_info_url)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Создаем или получаем пользователя
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=user_info['email'],
                defaults={
                    'username': user_info['email'],
                    'first_name': user_info.get('given_name', ''),
                    'last_name': user_info.get('family_name', ''),
                    'is_active': True,
                }
            )
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        
        print(f"✅ Google OAuth успешен для {user.email}, пользователь {'создан' if created else 'найден'}")
        
        # Редиректим на фронтенд с токенами в hash (как ожидает фронтенд)
        redirect_url = f"{frontend_url}/auth#access={refresh.access_token}&refresh={refresh}&email={user.email}"
        return HttpResponseRedirect(redirect_url)
        
    except Exception as e:
        print(f"❌ Google OAuth ошибка: {e}")
        return HttpResponseRedirect(f"{frontend_url}/auth?error=oauth_failed")

# === SIMPLE LOGIN ===
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def simple_login(request):
    """Правильный логин с проверкой пароля"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email:
        return Response({'error': 'Email is required'}, status=400)
    
    if not password:
        return Response({'error': 'Password is required'}, status=400)
    
    try:
        # Ищем пользователя по email
        user = User.objects.get(email=email)
        
        # Проверяем пароль
        if not user.check_password(password):
            return Response({
                'error': 'Invalid email or password',
                'message': 'Login failed'
            }, status=401)
        
        # Проверяем что пользователь активен
        if not user.is_active:
            return Response({
                'error': 'Account is disabled',
                'message': 'Login failed'
            }, status=401)
        
        # Генерируем токены только при успешной аутентификации
        refresh = RefreshToken.for_user(user)
        
        print(f"✅ Successful login for: {email}")
        
        return Response({
            'message': 'Login successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
            }
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'Invalid email or password',
            'message': 'Login failed'
        }, status=401)

# === MOCK DATA ===
@api_view(['GET'])
@permission_classes([AllowAny])
def mock_stats(request):
    """Mock статистика"""
    return Response({
        'total_properties': 12543,
        'average_price': 2850000,
        'growth_rate': 15.8
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def mock_properties(request):
    """Mock недвижимость"""
    limit = int(request.GET.get('limit', 10))
    properties = []
    for i in range(min(limit, 20)):
        properties.append({
            'id': i + 1,
            'title': f'Property {i + 1}',
            'price': 1500000 + i * 100000,
            'location': 'Dubai Marina',
            'type': 'apartment'
        })
    return Response({'results': properties})

