import os
import sys
from pathlib import Path

# --- 1. CONFIGURAÇÃO DE CAMINHO (ESSENCIAL PARA PYTHONANYWHERE) ---
# Adiciona a pasta do projeto ao path do Python se não estiver lá
# Isso garante que o Python encontre o módulo 'config'
path_home = Path(__file__).resolve().parent.parent
if str(path_home) not in sys.path:
    sys.path.append(str(path_home))

# --- 2. CORREÇÃO DE COMPATIBILIDADE (MONKEY PATCH) ---
# Executa antes de qualquer importação do Django para evitar o erro na lib de criptografia
import django.utils.encoding
if not hasattr(django.utils.encoding, "force_text"):
    django.utils.encoding.force_text = django.utils.encoding.force_str

# --- 3. INICIALIZAÇÃO PADRÃO ---
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()