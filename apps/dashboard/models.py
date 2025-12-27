from django.db import models
from django.contrib.auth.models import User
from fernet_fields import EncryptedCharField

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    # REMOVIDO O unique=True
    cpf = EncryptedCharField("CPF", max_length=14, help_text="Formato: 000.000.000-00")

    def __str__(self):
        return f"Perfil de {self.user.username}"