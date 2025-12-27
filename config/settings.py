from pathlib import Path
import django.utils.encoding
# Correção de compatibilidade para django-fernet-fields
django.utils.encoding.force_text = django.utils.encoding.force_str

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-t&059x1p(n6=+#u3vdr0gn^y79+26x48j(ss47ou(!^n#o8t+e"

# SECURITY WARNING: don't run with debug turned on in production!
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
    'apps.funcionarios.apps.FuncionariosConfig',
    'apps.dashboard.apps.DashboardConfig',
    'apps.financeiro.pagar.apps.PagarConfig',
    'apps.financeiro.receber.apps.ReceberConfig',
    'apps.ferias.apps.FeriasConfig',
    'apps.banco_horas.apps.BancoHorasConfig',
    'apps.comissionamento.apps.ComissionamentoConfig',
    'apps.relatorios.apps.RelatoriosConfig',
    'apps.rescisao.apps.RescisaoConfig'

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware customizado deve ficar por último ou após o AuthenticationMiddleware
    "config.middleware.LoginRequiredMiddleware", 
]
LOGIN_URL = '/'             # A raiz será a tela de login
LOGIN_REDIRECT_URL = '/dashboard/'  # Para onde vai após logar
LOGOUT_REDIRECT_URL = '/'   # Para onde vai após sair

# Defina o caminho das URLs para o novo nome de pasta (config)
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

# Alteração no WSGI para o novo nome da pasta
WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = "pt-br"
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True  
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FERNET_KEYS = [
    'pPz3-FoPxGNLD9SglRd-0L65svR4TA3WqoqPFEgrYeg=',
]