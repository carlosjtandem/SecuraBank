from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RealizarTransferenciaView, ListarTransaccionesView, verify_transfer_mfa


router = DefaultRouter()

urlpatterns = [
    path('realizar_transferencia/', RealizarTransferenciaView.as_view(), name='realizar_transferencia'),
    path('/', ListarTransaccionesView.as_view(), name='list_transferencia'),
    path('verify-mfa/', verify_transfer_mfa, name='verify_transferencia'),
]

urlpatterns = router.urls