from io import BytesIO
from datetime import timedelta
import qrcode
import qrcode.image.svg

from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# django-otp
from django_otp.plugins.otp_totp.models import TOTPDevice

import qrcode
import qrcode.image.svg

from .serializers import (
    RegisterSerializer, 
    CustomTokenObtainPairSerializer, 
    TOTPDeviceSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserSerializer
)

from .models import LoginAttempt

# ========== MFA (TOTP) ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_mfa_qr(request):
    """
    Genera el código QR para configurar TOTP en la app de Autenticación (Google Auth, Authy, etc.).
    """
    user = request.user
    device, created = TOTPDevice.objects.get_or_create(user=user, name='default')
    
    # Si el dispositivo aún no está confirmado, generamos el QR
    if not device.confirmed:
        qr_url = device.config_url
        img = qrcode.make(qr_url, image_factory=qrcode.image.svg.SvgImage)
        buffer = BytesIO()
        img.save(buffer)
        svg = buffer.getvalue().decode()
        return Response({
            'qr_code': svg, 
            'secret': device.bin_key
        })
    return Response({'detail': 'MFA ya está configurado.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])  # Permitido para usuarios sin tokens (MFA pendiente)
def confirm_mfa(request):
    """
    Endpoint que NO requiere estar autenticado,
    pues el usuario aún no tiene tokens (MFA pendiente).
    Se espera { username, token } en el body.
    Implementa control de intentos de MFA y bloqueo tras 3 intentos fallidos en 5 minutos.
    """
    username = request.data.get('username')
    totp_code = request.data.get('token')

    if not username or not totp_code:
        return Response({'detail': 'Faltan campos.'}, status=status.HTTP_400_BAD_REQUEST)

    # Buscar el usuario
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

    # Verificar si el usuario está bloqueado por intentos fallidos de MFA
    block_duration = timedelta(minutes=5)
    recent_mfa_attempts = LoginAttempt.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - block_duration,
        successful=False,
        is_mfa_attempt=True
    )
    failed_mfa_attempts = recent_mfa_attempts.count()

    if failed_mfa_attempts >= 3:
        return Response(
            {"detail": "Demasiados intentos fallidos de MFA. Inténtalo de nuevo más tarde."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Buscar su dispositivo TOTP (confirmado o en proceso)
    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    if device and device.verify_token(totp_code):
        # Generar tokens al verificar TOTP
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Registrar intento exitoso de MFA
        LoginAttempt.objects.create(user=user, successful=True, is_mfa_attempt=True)

        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'detail': 'MFA verificado',
        }, status=status.HTTP_200_OK)
    else:
        # Registrar intento fallido de MFA
        LoginAttempt.objects.create(user=user, successful=False, is_mfa_attempt=True)
        return Response({'detail': 'Token MFA inválido.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfa_status(request):
    user = request.user
    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()

    if device:
        return Response({
            'mfa_enabled': True,
            'device_name': device.name,
            'confirmed': device.confirmed,
        })
    return Response({'mfa_enabled': False}, status=status.HTTP_404_NOT_FOUND)

# revisar si borrar esta vista
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resend_mfa_code(request):
    """
    Permite reenviar el código MFA.
    En este caso, simplemente regenera el QR code si el dispositivo ya está confirmado.
    """
    user = request.user
    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    if device and not device.confirmed:
        qr_url = device.config_url
        img = qrcode.make(qr_url, image_factory=qrcode.image.svg.SvgImage)
        buffer = BytesIO()
        img.save(buffer)
        svg = buffer.getvalue().decode()
        return Response({
            'qr_code': svg, 
            'secret': device.bin_key
        })
    else:
        return Response({'detail': 'MFA ya está configurado o dispositivo confirmado.'}, status=status.HTTP_400_BAD_REQUEST)

# ========== OBTENER DATOS DEL USUARIO ==========
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    """
    Retorna la información básica del usuario autenticado (first_name, last_name, email, etc).
    """
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

# ========== REGISTRO ==========

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

# ========== LOGIN (JWT) ==========

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para forzar MFA antes de entregar tokens.
    Implementa control de intentos de login y bloqueo tras 3 intentos fallidos en 5 minutos.
    """
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        # Si el usuario existe, verificar intentos fallidos recientes
        if user:
            block_duration = timedelta(minutes=5)
            recent_attempts = LoginAttempt.objects.filter(
                user=user,
                timestamp__gte=timezone.now() - block_duration,
                successful=False
            )
            failed_attempts = recent_attempts.count()

            if failed_attempts >= 3:
                return Response(
                    {"detail": "Demasiados intentos fallidos. Inténtalo de nuevo más tarde."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

        # Procesar login
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            # Registrar intento fallido
            if user:
                LoginAttempt.objects.create(user=user, successful=False, is_mfa_attempt=False)
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.user  # Usuario autenticado

        # Registrar intento exitoso
        LoginAttempt.objects.create(user=user, successful=True, is_mfa_attempt=False)

        # Revisar si el usuario tiene TOTPDevice confirmado
        has_mfa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        if has_mfa:
            # MFA está configurado, así que NO devolvemos tokens todavía
            return Response({
                "mfa_required": True,
                "detail": "Se requiere MFA"
            }, status=status.HTTP_200_OK)
        else:
            # Si NO hay MFA, retornamos tokens normalmente
            tokens = serializer.validated_data
            return Response(tokens, status=status.HTTP_200_OK)

# ========== LOGOUT ==========

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    """
    Cierra la sesión invalidando el token (colocándolo en blacklist).
    """
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Sesión cerrada exitosamente."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": "Error al cerrar sesión."}, status=status.HTTP_400_BAD_REQUEST)

# ========== RECUPERACIÓN DE CONTRASEÑA ==========

class PasswordResetRequestView(generics.GenericAPIView):
    """
    Solicitud de reseteo: genera un token y un uid y los manda por correo.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # URL que tu frontend React manejará para restablecer la contraseña
        reset_url = f"http://localhost:3000/reset-password/?uid={uid}&token={token}"

        # Enviar correo electrónico
        subject = "Restablece tu contraseña"
        message = render_to_string('password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

        return Response({"detail": "Se ha enviado un correo para restablecer la contraseña."}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    """
    El usuario da el POST con uid, token y new_password.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contraseña restablecida correctamente."}, status=status.HTTP_200_OK)

# ========== USUARIOS ==========

class UserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    Vista para permitir obtener/actualizar datos del usuario autenticado.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
