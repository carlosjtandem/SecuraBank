from django.urls import path
from accounts import views

urlpatterns = [
    path('',views.render_accounts,name='accounts')
]
