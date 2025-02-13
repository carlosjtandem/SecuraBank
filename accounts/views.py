from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction as db_transaction
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Account
from .serializers import AccountSerializer

@api_view(['GET'])
def get_user_accounts(request):
    """
    Retorna todas las cuentas pertenecientes al usuario autenticado.
    """
    user = request.user  
    accounts = Account.objects.filter(user=user)  
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

class UserAccountsView(generics.ListAPIView):
    """
    Devuelve las cuentas asociadas al usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

class AllAccountsView(generics.ListAPIView):
    """
    Devuelve todas las cuentas registradas en el sistema.
    Si se desea excluir las cuentas del usuario actual, se puede modificar el queryset.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountSerializer

    def get_queryset(self):
        # Para incluir todas las cuentas:
        return Account.objects.all()
        # Para excluir las cuentas del usuario actual:
        # return Account.objects.exclude(user=self.request.user)

class AccountViewSet(viewsets.ModelViewSet):
    """
    CRUD de cuentas
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Cada usuario ve solo sus cuentas
        """
        return Account.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Asignar automáticamente el 'user' a la cuenta.
        """
        data = request.data.copy()
        data['user'] = request.user.id  # Forzar la cuenta al usuario logueado
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Bloque transaccional
        with db_transaction.atomic():
            self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
   
    def perform_create(self, serializer):
        import uuid
        # Generar un número de cuenta único
        account_number = str(uuid.uuid4()).replace('-', '')[:12].upper()
        serializer.save(
            user=self.request.user, 
            account_number=account_number
        )

class AccountListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista todas las cuentas que pertenecen al usuario autenticado.
        """
        cuentas = Account.objects.filter(user=request.user)
        serializer = AccountSerializer(cuentas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CrearCuentaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Crea una nueva cuenta y la asigna al usuario autenticado.
        """
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Asigna la cuenta al usuario autenticado
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)