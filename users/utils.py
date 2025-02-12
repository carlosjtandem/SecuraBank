from django_otp.models import Device

def verify_mfa_code(user, mfa_code):
    """
    Verifica el código MFA para el usuario.
    Retorna True si el código es válido, False en caso contrario.
    """
    device = Device.objects.filter(user=user, confirmed=True).first()
    if device and device.verify_token(mfa_code):
        return True
    return False
