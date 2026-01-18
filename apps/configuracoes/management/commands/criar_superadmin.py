from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.dashboard.models import PerfilUsuario

class Command(BaseCommand):
    help = 'Cria o superusuário BernardoVieira com Perfil associado para acesso administrativo'

    def handle(self, *args, **options):
        username = "BernardoVieira"
        password = "Jovelina2"
        cpf = "01853353655"

        # Verifica se usuário existe
        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Criando usuário {username}...")
            
            # Cria o usuário com método helper para lidar com hash de senha corretamente
            user = User.objects.create_user(username=username, password=password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            # Verifica e cria perfil
            if not PerfilUsuario.objects.filter(user=user).exists():
                PerfilUsuario.objects.create(user=user, cpf=cpf)
                self.stdout.write(self.style.SUCCESS("✅ SUCESSO! PerfilUsuario criado e vinculado."))
            
            self.stdout.write(self.style.SUCCESS(f"✅ SUCESSO! Superusuário '{username}' criado."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ O usuário '{username}' já existe."))
            
            # Opcional: Garante que ele seja superusuário mesmo se já existir
            user = User.objects.get(username=username)
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"🔄 Permissões de superusuário atualizadas para '{username}'."))