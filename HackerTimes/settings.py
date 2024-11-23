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
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
AWS_ACCESS_KEY_ID = "ASIAVLRKON4XNDXOJ4XH"
AWS_SECRET_ACCESS_KEY = "JyqzKxKCDm41g1ioGFAEXAfbpcif9ewSSQ3B826n"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEGMaCXVzLXdlc3QtMiJHMEUCIQC1T7nyAHJEAzyd91EneWpkGOHzwHPcJ4uL2+ItUPg9fgIgfGTiF/MnVKqXQtSLgaZWrC3xbgA/BF0JBrklYFLuAMYqxgII7P//////////ARABGgwzNjgzODI0NzE5ODIiDOCspHI8YrDQXUvI8SqaAthRgZt+LMPFqLxYUrmQ49pxE1cpbSdf6ygowXiVPtWDBpJTOY5SclOmYJ4MtbumQ1E9CeK9v70+hxu286fxjjI53RjE96UEm4t20STtVpjPvRU5sszZlb1p1WnXcut8sa+0u1JhbWC12mAHZs5Khvltbs/OsTsDZdTbsUoTVvnk1eWhD5e5Q52d6FWfiQHntVHqCRUwh9G+6k0cJWtSjXOOi9R1DH3Vnwc7F0+WAFKJX9YfX4bMO8u21G9FJJZpf6UpAdAlmhc3o8jDnw04o7XT97Ye2ByxjoN6fJiNXUDuwghXil/1aSXmq57U+T4H7dSbrYdAvIfRSYDq/vs+pNosieHRbZA+8lYoXW2vEpl0LSRnC7RZilFiCTDhste5BjqdAbuPtmyTXgXeRn3P4nSan4jt3kdX75ScKytq9mxuJpYf7P7cyksPBW25izyvObqUFYLAPMSuRIoEa/iYKFTzD5tf4YaXYmRMtuszzklGCjMPEKsfSSRUhGnymcfHXkDFVoENO190lXxN6Tjk1LNfO86S4Neixf4OQ0zxL6vExhWrwyROWWyjVZt1GCP7vxj/drIDtbMBOaC3PEAtSic="
AWS_STORAGE_BUCKET_NAME = "hn12c-hackertimes"
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_CUSTOM_DOMAIN = f'https://hn12c-hackertimes.s3.us-east-1.amazonaws.com'

# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    "https://editor.swagger.io",
    "http://localhost:8000",
]