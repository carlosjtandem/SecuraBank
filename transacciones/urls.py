from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, ListarTransaccionesView, CreateTransaccionView

# 1) Creamos el router para exponer las rutas del ViewSet
router = DefaultRouter()
# El primer parámetro 'r''' indica el prefijo vacío, lo que hará que
# el ViewSet responda en /api/transacciones/ (ver proyecto principal más abajo)
router.register(r'', TransactionViewSet, basename='transacciones')


urlpatterns = [
    # 2) Rutas opcionales para tus vistas genéricas personalizadas
    path('listar/', ListarTransaccionesView.as_view(), name='list_transferencia'),
    path('crear/', CreateTransaccionView.as_view(), name='create_transferencia'),

    # 3) Incluir las rutas del router:
    #    / -> GET para listar (list), POST para crear (create), 
    #    /{pk}/ -> GET (retrieve), PUT (update), PATCH (partial_update), DELETE (destroy)
    path('', include(router.urls)),
]