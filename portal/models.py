# portal/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import Polo


class User(AbstractUser):
    TIPO_USUARIO = [
        ('global', 'Global'),
        ('polo', 'Polo'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_USUARIO, default='polo')
    polo = models.ForeignKey(Polo, on_delete=models.SET_NULL, null=True, blank=True, related_name='portal_usuarios')

    def __str__(self):
        return f"{self.username} ({self.tipo})"
    
    @property
    def is_global(self):
        return self.tipo == 'global'
