# Generated by Django 5.0.2 on 2024-12-06 17:30

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procesamiento', '0004_useractivitylog_unique_user_month_year'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='useractivitylog',
            name='unique_user_month_year',
        ),
        migrations.AddConstraint(
            model_name='useractivitylog',
            constraint=models.UniqueConstraint(fields=('usuario', 'mes', 'año'), name='unique_user_month_year'),
        ),
    ]