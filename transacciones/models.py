from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Account

# Lista de opciones de monedas basadas en ISO 4217
# monedas
CURRENCY_CHOICES = [
    ('USD', 'Dólar estadounidense'),
    ('EUR', 'Euro'),
    ('GBP', 'Libra esterlina'),
    ('JPY', 'Yen japonés'),
    ('MXN', 'Peso mexicano'),
    ('CAD', 'Dólar canadiense'),
    ('AUD', 'Dólar australiano'),
    ('CHF', 'Franco suizo'),
    ('CNY', 'Yuan chino'),
    ('SEK', 'Corona sueca'),
]

class Transaction(models.Model):
    ESTADOS = (
        ('proceso', 'Proceso'),
        ('completada', 'Completada'),
        ('fallida', 'Fallida'),
        ('revertida', 'Revertida'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='Transacciones',
        default=1  

    )
    # usario - cuentas
    from_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='outgoing_transactions',
        default=1, 

    )
    # Cuenta destino
    to_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='incoming_transactions',
        default=1, 

    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    fecha = models.DateTimeField(default=timezone.now)
    transa_ubicacion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='proceso'
    )

    def __str__(self):
        return f"Transacción {self.id} - {self.user} - {self.monto} : {self.moneda}"
