import os
from dotenv import load_dotenv
from pathlib import Path
import dj_database_url
import mimetypes

# Cargar variables de entorno
load_dotenv()

GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
if not GOOGLE_OAUTH_CLIENT_ID:
    raise ValueError(
        'GOOGLE_OAUTH_CLIENT_ID is missing.'
        'Have you put it in a file at core/.env ?'
    )

# Configuraciones para Google Sign-in
SECURE_REFERRER_POLICY = 'no-referrer-when-downgrade'
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

mimetypes.add_type("text/css", ".css", True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-&r5%tl8g52!zxo8bgn%6d1lb%a76tfx86o$#lokq5vv()2ik9d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    'https://editor.swagger.io',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://hackertimes-0dd5aa346ba7.herokuapp.com',
    'https://hackertimes-0dd5aa346ba7.herokuapp.com/submit/',

]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',  # Agregar 'authorization' si es necesario para tus cabeceras
    'X-API-Key',
    'X-api-key',
]

# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    'https://editor.swagger.io',
    'http://localhost:8000',
]
# Application definition
INSTALLED_APPS = [
    'News',
    'API',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'corsheaders',
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'News.middleware.APIKeyMiddleware',
]

ROOT_URLCONF = 'HackerTimes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'HackerTimes.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static/",
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AWS Configuration
AWS_ACCESS_KEY_ID = "ASIAVLRKON4XM2LCIDGK"
AWS_SECRET_ACCESS_KEY = "Fyej77/T+mILau+ZnTMJXZyBPfOLqyj/GguIydET"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEMr//////////wEaCXVzLXdlc3QtMiJIMEYCIQCt1SW4h6v1aXX6yZEHMD6WNoG8eeedsNZYA4gmTu5DFwIhALKgDYcN6q/2KBWS6Jet4v1NbDz4mWryE1xWLfnFTK6KKr0CCHMQARoMMzY4MzgyNDcxOTgyIgykmJiz6Kf8MvtPSlsqmgIgzkGnMsdyfAL1mVSRMT3weo6Dl+8ub5Gwxc55Q8ElgaUn6p7j2+fvGnU41RDsCFIXqus65rDAHoNHwl76gwY0D1QXBanv8iBVSLjKUZyeRaLI/6M62+fqMp8LBg3iRqy+YViVXJ/r6/+d0K1CL4X295oh83f0ilil0iuuJu9mNASX7vGIYnu47mS5HwMUBLGoQwFDTMgdUYZjkHwObdMo3ItRDM4SRcGROaQMCfS5vPFd9CYdWQpC9sPv0xi9p33m2RiXfiS56zlUQIJvwf/FZGYbKkeOvWeFIWBvyP+EkZ4jb9h5/h1ZqOe8MeD673uyAvj0CDeXAp1sa9xJY4JdwgV9klyY6tbuMlSJf9t6RwqZIBmb2PXomJww+aGmugY6nAFz5NrZcmTnLKbfbdgTmUdqt8TO9WWhjjfZzElJQUmM2u268GO5j8/fy4bMAUjbq72nBpGqyZoAFu2kd7pa+rWRUlAWw7+g7dWpHGkEBjTq0nuKMTI6pIDjVmrMyDcFXVXCN4M2GkMSoUPEWtJVzy9tnceX3e81IF6NGns361EVTaGX/X22Pe9NmDgZAysqeLf3YqGTkuDF0VnqPGA="
AWS_STORAGE_BUCKET_NAME = "hn12c-hackertimes"
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_CUSTOM_DOMAIN = f'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com'
