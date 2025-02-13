from rest_framework import serializers
from .models import Transaction, CURRENCY_CHOICES
from accounts.serializers import AccountSerializer  

class TransactionSerializer(serializers.ModelSerializer):
    from_account = AccountSerializer(read_only=True)
    to_account = AccountSerializer(read_only=True)
    moneda = serializers.ChoiceField(choices=CURRENCY_CHOICES, default='USD')
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'from_account',
            'to_account',
            'monto',
            'moneda',
            'fecha',
            'transa_ubicacion',
            'estado'
        ]
        read_only_fields = ['id', 'fecha', 'estado']
