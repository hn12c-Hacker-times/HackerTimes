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

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.herokuapp.com']
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://hackertimes-0dd5aa346ba7.herokuapp.com'
    'https://hackertimes-0dd5aa346ba7.herokuapp.com/submit/'
]

# Application definition
INSTALLED_APPS = [
    'News',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
AWS_ACCESS_KEY_ID = "ASIAVLRKON4XKBWGUGVO"
AWS_SECRET_ACCESS_KEY = "cLfiZmxc33qlkZO4tkRjLVN/+zTvNOj9LlFpjBgL"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEFwaCXVzLXdlc3QtMiJHMEUCIFGBLJDfNskQsiFcbykpYPX4K/lbg6z0l/uislKZyUm8AiEA3iYZmctg7uwUrP0S9XN9WegoxvFucUlQfPRwXlwNrZEqxgII1f//////////ARABGgwzNjgzODI0NzE5ODIiDDa3rAJbruVzOcCPViqaAsNPlTXlguqzXxWiuCiyDgVfO6ajnVff15lXowWHbyMXElReiDihZ1Wo1YtKdCd8YNeXZziTIn+vnzY5YC69H5NPClPikU6pXN5ULdNtmIivtyc3I99/jwloLtYEvkipmkvwB6p4YoL4AT+7hrc5zeukyACpoEKu3LHygbdWN51fTBz5laMeEZZN8fc+gWd/G29QRvi5HgqQSyV4bms8VMd5TTvYbrG1m/N/LMAycfSvsRNqAbDdm2e7VwFvQlsvHV/Z/2lhk4+vgXo0IDQLh2pe7uM28PKuCmSm4sUTSny6lGsn2X7gZ7CfWZeBb2ryRaKVGWF2WlwzfZ5wE3vvPwYIdmpqRKYnSvdtoFnBp5jOg5h0S9R0ouVRbTCOwZ25BjqdATkS2l40lpT1fANtKvwu4z/RJ1F6bX9PRxsXogSg3YzmU/qmqmLukOmP5GTlg6r7eLGXPXakyyPJ+ZUgplxU8nNnr0MkRdInBS61cJCRqqcuUFyg7X6AvpYIVRMxgt+5XJM1VRIaQgtO6YtBjoS+p/qiWmNvmapAqaaVudmBdVC5OXtUR+/ejqeUd723xKF7xtkTV0r3vMhbjeaANW0="
AWS_STORAGE_BUCKET_NAME = "hn12c-hackertimes"
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_CUSTOM_DOMAIN = f'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com'