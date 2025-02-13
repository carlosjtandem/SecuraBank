from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'account_number', 'saldo')
    # puedes agregar list_filter, search_fields, etc.