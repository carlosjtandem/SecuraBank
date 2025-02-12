from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


from .views import (
    RegisterView,
    CustomTokenObtainPairView,

    generate_mfa_qr,
    confirm_mfa,
    mfa_status,
    resend_mfa_code,
    get_user,              # <-- Importamos get_user
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)

urlpatterns = [
    # Registro
    path('register/', RegisterView.as_view(), name='auth_register'),

    # Login (JWT)
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Refresh token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # MFA
    path('mfa/generate/', generate_mfa_qr, name='mfa_generate'),
    path('mfa/confirm/', confirm_mfa, name='mfa_confirm'),
    path('mfa/status/', mfa_status, name='mfa_status'),
    path('mfa/resend/', resend_mfa_code, name='mfa_resend'),  # adicional si se requiere

    # Logout
    path('logout/', LogoutView.as_view(), name='auth_logout'),

    # Recuperación de contraseña
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
