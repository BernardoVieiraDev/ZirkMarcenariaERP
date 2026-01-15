from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils import timezone

from apps.ferias.service import atualizar_todos_periodos


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
    
class VerificacaoFeriasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Só roda se o usuário estiver logado para não pesar acessos públicos (se houver)
        if request.user.is_authenticated:
            # Tenta pegar uma chave no cache chamada 'ferias_verificadas_hoje'
            # A chave é baseada na data de hoje (ex: ferias_check_2023-10-27)
            hoje = timezone.now().date().isoformat()
            chave_cache = f'ferias_check_{hoje}'
            
            ja_verificou = cache.get(chave_cache)

            if not ja_verificou:
                # Se não verificou hoje ainda, roda a atualização
                try:
                    atualizar_todos_periodos()
                    # Salva no cache por 24h para não rodar de novo hoje
                    # (86400 segundos = 1 dia)
                    cache.set(chave_cache, True, 86400)
                except Exception as e:
                    # Loga o erro mas não para o site
                    print(f"Erro ao atualizar férias automáticas: {e}")

        response = self.get_response(request)
        return response