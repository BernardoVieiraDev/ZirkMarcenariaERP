import os
from pathlib import Path

from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CARREGAMENTO DE ENV (LOCAL) ---
dotenv_path = BASE_DIR / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# --- AMBIENTE ---
# No PythonAnywhere, defina DJANGO_ENV='production' nas Environment Variables
IS_PRODUCTION = os.getenv('DJANGO_ENV') == 'production'

# Em produção, DEBUG deve ser False, mas para seu teste inicial, 
# se quiser ver erros na tela, pode definir DJANGO_DEBUG='True' no painel
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True' if IS_PRODUCTION else True

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Geração automática de chave provisória para testes se não houver ENV configurada
if not SECRET_KEY:
    if IS_PRODUCTION:
        # AVISO: Em um deploy final real, isso seria perigoso. Para teste é aceitável.
        print("AVISO: Usando chave secreta provisória. Configure DJANGO_SECRET_KEY.")
        SECRET_KEY = 'django-insecure-test-deploy-key-change-me-later'
    else:
        SECRET_KEY = 'django-insecure-fallback-key-local-dev-only'

# --- ALLOWED HOSTS ---
allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]
else:
    # Permite o domínio padrão do PythonAnywhere automaticamente em produção
    ALLOWED_HOSTS = ['.pythonanywhere.com', 'localhost', '127.0.0.1']

# --- APPS ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.humanize',
    'fernet_fields',
    'widget_tweaks',
    
    # Seus apps
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
    'apps.configuracoes.apps.ConfiguracoesConfig',
    'apps.clientes.apps.ClientesConfig',
    'apps.empreitadas.apps.EmpreitadasConfig',
    'apps.docs.apps.DocsConfig'
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
    'config.middleware.VerificacaoFeriasMiddleware',
]

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
                'apps.configuracoes.context_processors.configuracoes_globais', 
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- BANCO DE DADOS (LÓGICA HÍBRIDA) ---
# Se as variáveis existirem (MySQL/Postgres), usa elas.
# Se NÃO existirem, cai automaticamente para SQLite (Ideal para seu teste).
# zirk_rh_financeiro/config/settings.py

# --- BANCO DE DADOS ---
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

if all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST]):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # <--- MUDANÇA AQUI (Era postgresql)
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }
else:
    # Fallback para SQLite (Desenvolvimento Local)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"



# --- LOGGING ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django_errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO', 
            'propagate': True,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    { "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
    { "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    { "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator", },
    { "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator", },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# --- ARQUIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- E-MAIL (MODO TESTE/CONSOLE) ---
# Não envia de verdade, apenas mostra no log o que seria enviado.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- CRIPTOGRAFIA (FERNET) ---
# Se não definir no PA, usa chave fixa (apenas para este teste, não use em produção real)
fernet_key = os.getenv('DJANGO_FERNET_KEY', 'pPz3-FoPxGNLD9SglRd-0L65svR4TA3WqoqPFEgrYeg=')
FERNET_KEYS = [fernet_key]

# --- SEGURANÇA WEB ---
if IS_PRODUCTION:
    # Força HTTPS e Cookies seguros
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


MESSAGE_TAGS = {
    messages.ERROR: 'danger',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.INFO: 'info',
}