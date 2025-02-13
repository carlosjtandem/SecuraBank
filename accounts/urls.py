from rest_framework.routers import DefaultRouter
from .views import UserAccountsView, AllAccountsView, AccountListView, CrearCuentaView, get_user_accounts, AccountViewSet
#from .views import AccountViewSet, AccountListView, CrearCuentaView, get_user_accounts

from django.urls import path, include


router = DefaultRouter()
# Registrar sin sub-ruta, para que sea /api/cuentas/ para la lista y /api/cuentas/{pk}/ para detalles
router.register(r'', AccountViewSet, basename='accounts')

urlpatterns = [
    path('user-accounts/', UserAccountsView.as_view(), name='user_accounts'),
    path('all-accounts/', AllAccountsView.as_view(), name='all_accounts'),
    path('', AccountListView.as_view(), name='listar_cuentas'),
    path('crear/', CrearCuentaView.as_view(), name='crear_cuenta'),
    path('accounts/', include(router.urls)),
    path('get_user_accounts/', get_user_accounts, name='get_user_accounts'),
    path('list/', AccountListView.as_view(), name='listar_cuentas'),
]
