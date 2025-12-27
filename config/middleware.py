from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se o usuário NÃO está logado
        if not request.user.is_authenticated:
            path = request.path_info
            
            # Pega a URL de login e admin
            login_url = settings.LOGIN_URL
            
            # Lista de exceções (URLs que podem ser acessadas sem login)
            # 1. A própria página de login (para não dar loop infinito)
            # 2. A rota de logout
            # 3. O painel admin (o Django admin tem login próprio, mas é bom deixar acessível para configurações)
            # 4. Arquivos estáticos
            if path != login_url and not path.startswith('/admin/') and not path.startswith('/static/') and not path.startswith('/media/'):
                return redirect(f"{login_url}?next={path}")

        return self.get_response(request)