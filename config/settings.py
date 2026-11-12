import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-insegura-troque-em-producao")
NA_VERCEL = bool(os.getenv("VERCEL"))
DEBUG = os.getenv("DEBUG", "0" if NA_VERCEL else "1") == "1"  # na Vercel o padrão é desligado
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "https://*.vercel.app").split(",") if o]

INSTALLED_APPS = [
    "core",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.projeto",
            ],
        },
    },
]

# Banco: Supabase (Postgres) via DATABASE_URL; sem ela, cai no SQLite local.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=60,
        ssl_require=os.getenv("DATABASE_URL", "").startswith("postgres"),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
WHITENOISE_USE_FINDERS = DEBUG  # em desenvolvimento serve direto de static/
WHITENOISE_AUTOREFRESH = DEBUG
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Dados do projeto exibidos no site
PIX_CHAVE = os.getenv("PIX_CHAVE", "0dd14994-3e18-4e3f-aaea-c0d2480c65d1")
PIX_COPIA_COLA = os.getenv("PIX_COPIA_COLA", "00020126580014br.gov.bcb.pix01360dd14994-3e18-4e3f-aaea-c0d2480c65d127600016BR.COM.PAGSEGURO0136517FFAD1-BEEB-4A9A-8D59-7109A46BF1F85204549953039865802BR5925MELINO JOSE DE CARVALHO N6011Sao Goncalo62290525PAGS0000000002611051531726304CA8C")
PIX_FAVORECIDO = os.getenv("PIX_FAVORECIDO", "Melino José de Carvalho Neto")
WHATSAPP = os.getenv("WHATSAPP", "5521998412052")  # só dígitos, com DDI
WHATSAPP_EXIBIR = os.getenv("WHATSAPP_EXIBIR", "(21) 99841-2052")
INSTAGRAM_CT_URL = os.getenv("INSTAGRAM_CT_URL", "https://www.instagram.com/ct.salvacao.sg/")
INSTAGRAM_CT_USUARIO = os.getenv("INSTAGRAM_CT_USUARIO", "@ct.salvacao.sg")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://www.instagram.com/projetosalvacaosg/")
INSTAGRAM_USUARIO = os.getenv("INSTAGRAM_USUARIO", "@projetosalvacaosg")

# Velocidade: sessão no cookie assinado (sem consulta ao banco) e usuário em cache curto.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
AUTHENTICATION_BACKENDS = ["core.auth.UsuarioEmCache"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "painel"}}

X_FRAME_OPTIONS = "SAMEORIGIN"  # permite abrir os formulários em caixinha (iframe do próprio site)

# Segurança em produção (quando DEBUG está desligado): cookies só por HTTPS e confia no aviso do proxy da Vercel.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"

# Usuário mestre: manda em tudo e não pode ser apagado nem rebaixado por outras pessoas.
USUARIO_MESTRE = os.getenv("USUARIO_MESTRE", "Melino")
