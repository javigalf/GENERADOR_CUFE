# Generated by Django 5.0.2 on 2024-12-06 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procesamiento', '0002_useractivitylog_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractivitylog',
            name='año',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='useractivitylog',
            name='mes',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
