# Generated by Django 5.1.6 on 2025-02-13 03:38

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Cuenta Principal', max_length=100)),
                ('account_number', models.CharField(max_length=30, unique=True)),
                ('estado', models.CharField(choices=[('activa', 'Activa'), ('inactiva', 'Inactiva')], default='activa', max_length=50)),
                ('saldo', models.DecimalField(decimal_places=2, default=125.0, max_digits=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('owner', models.CharField(blank=True, max_length=150, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
