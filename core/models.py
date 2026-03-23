from django.db import models

# Create your models here.
from django.db import models
from django.utils.text import slugify

class Polo(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    endereco = models.CharField(max_length=300, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    cor_principal = models.CharField(max_length=20, default='#004AAD')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
