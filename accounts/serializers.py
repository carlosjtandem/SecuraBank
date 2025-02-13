from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()  # Campo virtual que no existe en la BD


    class Meta:
        model = Account
        fields = ['id', 'account_number', 'saldo', 'created_at', 'name', 'estado', 'owner']
        read_only_fields = ['id', 'account_number', 'saldo', 'created_at']

    def get_owner(self, obj):
        return obj.user.username