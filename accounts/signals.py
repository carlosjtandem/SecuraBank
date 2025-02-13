from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Account

@receiver(post_save, sender=User)
def create_default_account(sender, instance, created, **kwargs):
    """
    Cada vez que se crea un nuevo usuario, generamos una cuenta principal con saldo inicial de 125.
    """
    if created:
        Account.objects.create(
            user=instance,
            name="Cuenta Principal",
            account_number=f"ACC-{instance.id}",
            saldo=125.00
        )
