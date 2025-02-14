# Django REST Framework (DRF) - API y Autenticación
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes

# Modelos y Serialización
from .models import Transaction
from .serializers import TransactionSerializer

# Gestión de Usuarios y Cuentas
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from accounts.models import Account

# Seguridad y Autenticación Multifactor (MFA)
from django_otp.models import Device  # Dispositivo MFA con django-otp
from django_otp.plugins.otp_totp.models import TOTPDevice  # Dispositivo TOTP para MFA
from users.utils import verify_mfa_code  # Función para verificar códigos MFA

# Base de Datos
from django.db import transaction as db_transaction

#class RealizarTransferenciaView(APIView):
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]  # Solo usuarios autenticados

    def get_queryset(self):
        # Cada usuario solo ve sus transacciones
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Obtener datos de la transacción
        from_account_id = self.request.data.get('from_account')
        to_account_id = self.request.data.get('to_account')
        monto = float(self.request.data.get('monto'))

        # 1) Verificar que la cuenta de origen existe y pertenece al usuario
        from_account = get_object_or_404(Account, id=from_account_id, user=self.request.user)

        # 2) Verificar que la cuenta de destino existe
        to_account = get_object_or_404(Account, id=to_account_id)

        # 3) Verificar saldo suficiente
        if from_account.saldo < monto:
            return Response(
                {"error": "Saldo insuficiente en la cuenta de origen"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4) Actualizar los saldos
        from_account.saldo -= monto
        to_account.saldo += monto

        # Guardar los cambios en las cuentas
        from_account.save()
        to_account.save()

        # Crear la transacción
        serializer.save(
            user=self.request.user,
            from_account=from_account,
            to_account=to_account,
            monto=monto,
            estado='completada'  # Cambiar el estado a "completada"
        )

class CreateTransaccionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from_account_id = request.data.get('from_account')
        to_account_id = request.data.get('to_account')
        amount = request.data.get('amount')
        currency = request.data.get('currency')

        if not from_account_id or not to_account_id or not amount:
            return Response({"error": "Faltan datos para la transferencia."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from_account = Account.objects.get(id=from_account_id, user=request.user)
        except Account.DoesNotExist:
            return Response({"error": "Cuenta de origen no existe o no pertenece al usuario."}, status=status.HTTP_404_NOT_FOUND)

        try:
            to_account = Account.objects.get(id=to_account_id)
        except Account.DoesNotExist:
            return Response({"error": "Cuenta destino no existe."}, status=status.HTTP_404_NOT_FOUND)

        try:
            amount = float(amount)
        except ValueError:
            return Response({"error": "El monto debe ser un número válido."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si el monto supera 500, en cuyo caso se requiere MFA
        if amount > 500:
            # Obtener el código MFA enviado por el usuario
            mfa_code = request.data.get('mfa_code')
            if not mfa_code:
                return Response({'detail': 'Se requiere un código MFA para esta transacción.'}, status=status.HTTP_400_BAD_REQUEST)

            # Verificar el código MFA usando el método de la app users
            if not verify_mfa_code(request.user, mfa_code):
                return Response({'detail': 'Código MFA inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        # (Opcional) Verificar si la cuenta origen tiene saldo suficiente
        if from_account.balance < amount:
            return Response({'error': 'Fondos insuficientes en la cuenta origen.'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear la transacción
        transaccion = Transaction.objects.create(
            id_usuario=request.user,
            from_account=from_account,
            to_account=to_account,
            monto=amount,
            moneda=currency,
            ubicacion=request.data.get('location', ''),
            estado='completada'  # Ajusta esto según la lógica de tu negocio
        )

        # (Opcional) Actualizar los saldos de las cuentas
        from_account.balance -= amount
        to_account.balance += amount
        from_account.save()
        to_account.save()

        serializer = TransactionSerializer(transaccion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class ListarTransaccionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista todas las transacciones del usuario autenticado.
        """
        usuario = request.user
        transacciones = Transaction.objects.filter(user=usuario).order_by('-fecha')
        serializer = TransactionSerializer(transacciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_transfer_mfa(request):
    """
    Verifica el código MFA para transferencias.
    """
    mfa_code = request.data.get('mfa_code')
    if not mfa_code:
        return Response({'detail': 'Se requiere un código MFA.'}, status=400)
    
    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if device and device.verify_token(mfa_code):
        return Response({'detail': 'Código MFA válido.'}, status=200)
    else:
        return Response({'detail': 'Código MFA inválido.'}, status=400)