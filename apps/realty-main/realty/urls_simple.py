"""
Упрощенные URLs для Railway - ТОЛЬКО авторизация
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from . import auth_views

# Простой корневой view
def root_view(request):
    return JsonResponse({
        "service": "dubai-auth-backend",
        "status": "ok",
        "version": "mvp-updated",
        "cache_bust": "2025-01-30-01-30",
        "endpoints": {
            "health": "/api/health/",
            "csrf": "/api/csrf/",
            "send_otp": "/api/auth/send-otp/",
            "verify_otp": "/api/auth/verify-otp/",
            "google_auth": "/api/auth/google/login/",
            "simple_auth": "/api/auth/login/",
            "stats": "/api/stats/",
            "properties": "/api/properties/"
        }
    })

urlpatterns = [
    # Корневая страница
    path("", root_view),
    
    # Health check
    path("healthz/", lambda request: JsonResponse({"status": "ok", "service": "auth-only"})),
    
    # API - прямые endpoints без модулей
    path("api/health/", auth_views.health_check, name="health_check"),
    path("api/csrf/", auth_views.csrf_token_view, name="csrf_token"),
    path("api/auth/register/", auth_views.register_user, name="register"),
    path("api/auth/send-otp/", auth_views.send_otp, name="send_otp"),
    path("api/auth/verify-otp/", auth_views.verify_otp, name="verify_otp"),
    path("api/auth/google/login/", auth_views.google_auth_init, name="google_init"),
    path("api/auth/google/callback/", auth_views.google_auth_callback, name="google_callback"),
    path("api/auth/login/", auth_views.simple_login, name="simple_login"),
    path("api/auth/force-login/", auth_views.force_login, name="force_login"),
    path("api/stats/", auth_views.mock_stats, name="stats"),
    path("api/properties/", auth_views.mock_properties, name="properties"),
    
    # Admin (опционально)
    path("admin/", admin.site.urls),
]
