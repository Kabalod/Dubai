"""
Dubai MVP URLs Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Корневой view
def root_view(request):
    return JsonResponse({
        "service": "dubai-auth-backend",
        "status": "ok", 
        "version": "mvp",
        "endpoints": {
            "health": "/api/health/",
            "api": "/api/",
            "admin": "/admin/",
            "google_auth": "/api/auth/google/login/"
        }
    })

urlpatterns = [
    # Корневая страница
    path("", root_view),
    
    # API endpoints
    path("api/", include("realty.api.urls")),
    
    # Admin
    path("admin/", admin.site.urls),
    
    # Main app (опционально)
    path("main/", include("realty.main.urls")),
    
    # Reports (опционально)
    path("reports/", include("realty.reports.urls")),
]
