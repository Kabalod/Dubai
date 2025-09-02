"""
Модели для системы аутентификации
"""
import secrets
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


class OTPCode(models.Model):
    """Модель для OTP кодов"""
    email = models.EmailField(max_length=255, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'auth_otp_codes'
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['code', 'is_used']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} - {self.code}"
    
    @classmethod
    def generate_for_email(cls, email):
        """Генерирует новый OTP код для email"""
        # Деактивируем все старые коды для этого email
        cls.objects.filter(email=email, is_used=False).update(is_used=True)
        
        # Создаем новый код
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=10)  # 10 минут
        
        otp = cls.objects.create(
            email=email,
            code=code,
            expires_at=expires_at
        )
        
        return otp
    
    def is_valid(self):
        """Проверяет валидность OTP кода"""
        return (
            not self.is_used 
            and self.attempts < self.max_attempts 
            and timezone.now() < self.expires_at
        )
    
    def verify(self, input_code):
        """Верифицирует OTP код"""
        self.attempts += 1
        self.save(update_fields=['attempts'])
        
        if not self.is_valid():
            return False
            
        if self.code == input_code:
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True
            
        return False
    
    def send_email(self, subject=None, template=None):
        """Отправляет OTP код на email"""
        if not subject:
            subject = 'Dubai Real Estate - Verification Code'
            
        if not template:
            message = f"""
Hello!

Your verification code for Dubai Real Estate Platform is: {self.code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Dubai Real Estate Team
            """.strip()
        else:
            message = template.format(code=self.code, email=self.email)
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send OTP email to {self.email}: {e}")
            return False


class GoogleOAuthState(models.Model):
    """Модель для хранения состояния Google OAuth"""
    state = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_google_oauth_states'
        indexes = [
            models.Index(fields=['state', 'is_used']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"OAuth State {self.state[:8]}... for {self.email or 'unknown'}"
    
    @classmethod
    def generate_state(cls, email=None):
        """Генерирует новое состояние OAuth"""
        state = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(minutes=15)  # 15 минут
        
        oauth_state = cls.objects.create(
            state=state,
            email=email or '',
            expires_at=expires_at
        )
        
        return oauth_state
    
    def is_valid(self):
        """Проверяет валидность состояния"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_used(self):
        """Помечает состояние как использованное"""
        self.is_used = True
        self.save(update_fields=['is_used'])


class UserProfile(models.Model):
    """Расширение модели пользователя"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    registration_method = models.CharField(
        max_length=20,
        choices=[
            ('email_otp', 'Email OTP'),
            ('google_oauth', 'Google OAuth'),
            ('admin', 'Admin Created'),
        ],
        default='email_otp'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user_profiles'
        indexes = [
            models.Index(fields=['google_id']),
            models.Index(fields=['email_verified']),
            models.Index(fields=['registration_method']),
        ]
    
    def __str__(self):
        return f"Profile for {self.user.email}"

