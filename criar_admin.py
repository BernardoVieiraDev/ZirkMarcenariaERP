import os
import django

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.dashboard.models import PerfilUsuario

def criar():
    username = "BernardoVieira"
    password = "Jovelina2"
    cpf = "01853353655"

    # Verifica se usuario existe
    if not User.objects.filter(username=username).exists():
        print(f"Criando usuário {username}...")
        user = User.objects.create_user(username=username, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        
        # Cria perfil criptografado
        PerfilUsuario.objects.create(user=user, cpf=cpf)
        print("✅ SUCESSO! Usuário e CPF Criptografado criados.")
    else:
        print("⚠️ Usuário já existe.")

if __name__ == "__main__":
    criar()