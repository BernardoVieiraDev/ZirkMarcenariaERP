import os
from pathlib import Path
import django.utils.encoding
from dotenv import load_dotenv  # <--- NOVO: Importa a lib

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# Correção de compatibilidade
django.utils.encoding.force_text = django.utils.encoding.force_str

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA DAS CHAVES (Agora vindo do ambiente) ---
# Se não encontrar no ambiente (ex: local sem .env), usa uma chave insegura apenas para rodar,
# mas no servidor TEM QUE TER a variável configurada.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'chave-insegura-apenas-para-desenvolvimento-local-123')

# Chave de Criptografia (Fernet)
fernet_key_env = os.getenv('DJANGO_FERNET_KEY')
if fernet_key_env:
    FERNET_KEYS = [fernet_key_env]
else:
    # Chave de fallback APENAS para dev local. Em produção, use a variável de ambiente!
    FERNET_KEYS = ['pPz3-FoPxGNLD9SglRd-0L65svR4TA3WqoqPFEgrYeg=']


# --- CONFIGURAÇÃO DE AMBIENTE ---
# Detecta se estamos em produção verificando se as variáveis do banco PostgreSQL existem
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

IS_PRODUCTION = all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST])

if IS_PRODUCTION:
    DEBUG = False
    ALLOWED_HOSTS = ['*'] # No PythonAnywhere isso é seguro pois o host é validado pelo Nginx
    
    # --- SEGURANÇA HTTPS (CRÍTICO PARA PRODUÇÃO) ---
    SECURE_SSL_REDIRECT = True      # Redireciona tudo para HTTPS
    SESSION_COOKIE_SECURE = True    # Cookie de sessão só via HTTPS
    CSRF_COOKIE_SECURE = True       # Cookie de proteção CSRF só via HTTPS
    SECURE_BROWSER_XSS_FILTER = True
else:
    DEBUG = True
    ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.humanize',
    'apps.funcionarios.apps.FuncionariosConfig',
    'apps.dashboard.apps.DashboardConfig',
    'apps.financeiro.pagar.apps.PagarConfig',
    'apps.financeiro.receber.apps.ReceberConfig',
    'apps.ferias.apps.FeriasConfig',
    'apps.banco_horas.apps.BancoHorasConfig',
    'apps.comissionamento.apps.ComissionamentoConfig',
    'apps.relatorios.apps.RelatoriosConfig',
    'apps.rescisao.apps.RescisaoConfig',
    'apps.socios.apps.SociosConfig',
    'apps.financeiro.fluxo.apps.FluxoConfig',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.LoginRequiredMiddleware", 
]

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- BANCO DE DADOS HÍBRIDO ---
if IS_PRODUCTION:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    print("⚠️  Ambiente LOCAL detectado: Usando SQLite.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
    { "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    { "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator", },
    { "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator", },
]

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True  
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / 'static']

# Arquivos de Mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"