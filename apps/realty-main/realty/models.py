"""
Модели для хранения OTP данных
"""
from django.db import models
from django.utils import timezone

class OTPData(models.Model):
    """Временное хранение OTP данных"""
    email = models.EmailField(unique=True)
    data = models.TextField()  # JSON данные
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'otp_data'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} (expires: {self.expires_at})"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
