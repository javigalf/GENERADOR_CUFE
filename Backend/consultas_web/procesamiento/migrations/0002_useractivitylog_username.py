# Generated by Django 5.0.2 on 2024-12-06 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procesamiento', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractivitylog',
            name='username',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
