from django.db import models
from django.contrib.auth.models import User
from core.models import Polo
from django.conf import settings

class PerfilUsuario(models.Model):
    ROLES = [
        ('admin_global', 'Administrador Global'),
        ('diretoria', 'Diretoria'),
        ('coordenador', 'Coordenador'),
        ('secretaria', 'Secretaria'),
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    polo = models.ForeignKey(Polo, on_delete=models.CASCADE, related_name='usuarios_perfil', null=True, blank=True)
    cargo = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        polo_nome = self.polo.nome if self.polo else "Sem polo"
        return f"{self.user.username} ({self.get_cargo_display()}) - {polo_nome}"

    @property
    def is_admin_global(self):
        return self.cargo == 'admin_global'
