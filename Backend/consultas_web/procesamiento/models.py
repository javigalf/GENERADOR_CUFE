from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models

class UserActivityLog(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, blank=True)
    fecha_y_hora_logueo = models.DateTimeField(null=True, blank=True)
    fecha_y_hora_deslogueo = models.DateTimeField(null=True, blank=True)
    cantidad_registros_gestionados = models.IntegerField(default=0)
    mes = models.IntegerField(null=True, blank=True)
    año = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'mes', 'año'], name='unique_user_month_year')
        ]

    def save(self, *args, **kwargs):
        if self.usuario and not self.username:
            self.username = self.usuario.username
        super().save(*args, **kwargs)