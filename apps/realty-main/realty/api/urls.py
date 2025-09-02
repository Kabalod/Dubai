from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = "api"

urlpatterns = [
    # Health Check
    path("health/", views.health_check, name="health_check"),
    
    # CSRF Token
    path("csrf/", views.CSRFTokenView.as_view(), name="csrf_token"),
    
    # Authentication
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.PasswordLoginView.as_view(), name="password_login"),  # Обычный логин для тестовых пользователей
    
    # OTP Authentication - полный цикл
    path("auth/send-otp/", views.SendOTPView.as_view(), name="send_otp"),  # Отправка OTP кода
    path("auth/verify-otp/", views.VerifyOTPView.as_view(), name="verify_otp"),  # Верификация OTP кода
    path("auth/otp-login/", views.OTPLoginView.as_view(), name="otp_login"),  # Legacy OTP логин
    path("auth/check-user/", views.CheckUserView.as_view(), name="check_user"),
    
    # Google OAuth
    path("auth/google/login/", views.GoogleAuthInitView.as_view(), name="google_auth_init"),
    path("auth/google/callback/", views.GoogleAuthCallbackView.as_view(), name="google_auth_callback"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/password/reset/", views.PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("auth/password/reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    # User Profile
    path("profile/me/", views.UserProfileView.as_view(), name="user_profile"),
    
    # Properties API (Mock Data)
    path("properties/", views.PropertiesListView.as_view(), name="properties_list"),
    path("properties/<str:listing_id>/", views.PropertyDetailView.as_view(), name="property_detail"),
    path("areas/", views.AreasListView.as_view(), name="areas_list"),
    path("stats/", views.PropertyStatsView.as_view(), name="property_stats"),
    # Alias для совместимости: /api/analytics/ → статистика
    path("analytics/", views.PropertyStatsView.as_view(), name="property_stats_alias"),
    path("buildings/", views.BuildingsListView.as_view(), name="buildings_list"),
    path("reports/", views.ReportsView.as_view(), name="reports_list_create"),
    path("reports/history/", views.ReportsView.as_view(), name="reports_history"),
    path("reports/generate/", views.ReportsView.as_view(), name="reports_generate"),

    # Admin Views
    path("admin/users/", views.UserProfileAdminView.as_view(), name="admin_users"),
    path("admin/payments/", views.PaymentAdminView.as_view(), name="admin_payments"),
    
    # Payment Intent
    path("create-payment-intent/", views.CreatePaymentIntentView.as_view(), name="create_payment_intent"),

    # Webhooks
    path("webhooks/stripe/", views.StripeWebhookView.as_view(), name="stripe_webhook"),
]
