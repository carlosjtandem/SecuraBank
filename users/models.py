from django.contrib.auth.models import User
from django.db import models
from django_otp.models import Device

#librerias para restablecer contraseña
from django.utils.timezone import now
import uuid

#clase para almacenar los dispositivos TOTP
class TOTPDevice(Device):
    """
    Dispositivo TOTP para MFA (integrado con django-otp).
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='totp_devices'
    )

    name = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

#cuenta de usuario
#class Account(models.Model):
#    user = models.OneToOneField(User, on_delete=models.CASCADE)  
#    numero_cuenta = models.CharField(max_length=50, unique=True)
#    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#   def __str__(self):
#        return f"{self.user.username} - {self.numero_cuenta}"

#clase para almacenar los intentos de inicio de sesión
class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts')
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    is_mfa_attempt = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Success' if self.successful else 'Failure'} at {self.timestamp} (MFA: {self.is_mfa_attempt})"

    class Meta:
        ordering = ['-timestamp']

#clase para almacenar el token de restablecimiento de contraseña
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=now)