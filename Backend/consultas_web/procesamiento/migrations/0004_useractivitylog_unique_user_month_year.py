# Generated by Django 5.0.2 on 2024-12-06 17:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procesamiento', '0003_useractivitylog_año_useractivitylog_mes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='useractivitylog',
            constraint=models.UniqueConstraint(fields=('usuario', 'mes', 'año', 'fecha_y_hora_deslogueo'), name='unique_user_month_year'),
        ),
    ]