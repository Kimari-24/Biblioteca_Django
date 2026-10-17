"""
Django settings for config project.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-n1rw2z%l+a!yho7m(ffmyj*u!+ga*gxfd@_gis3x@u+0xj9=3r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'features.accounts',
    'features.books',
    'features.loans',
    'features.dashboard',
    'features.seeder',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.session_user',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Firebase
# Los valores viven en el archivo .env (no se sube a git).
FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', '')
FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', '')
FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '')
FIREBASE_MEASUREMENT_ID = os.environ.get('FIREBASE_MEASUREMENT_ID', '')
FIREBASE_CREDENTIALS_PATH = BASE_DIR / os.environ.get(
    'FIREBASE_CREDENTIALS_PATH', 'firebase/serviceAccountKey.json'
)

# Cuenta de servicio desde variables de entorno (útil al desplegar sin subir el .json).
# Si FIREBASE_PRIVATE_KEY no está definida, se usa el archivo de FIREBASE_CREDENTIALS_PATH.
FIREBASE_SERVICE_ACCOUNT = None
if os.environ.get('FIREBASE_PRIVATE_KEY'):
    FIREBASE_SERVICE_ACCOUNT = {
        'type': 'service_account',
        'project_id': FIREBASE_PROJECT_ID,
        'private_key_id': os.environ.get('FIREBASE_PRIVATE_KEY_ID', ''),
        'private_key': os.environ['FIREBASE_PRIVATE_KEY'].replace('\\n', '\n'),
        'client_email': os.environ.get('FIREBASE_CLIENT_EMAIL', ''),
        'client_id': os.environ.get('FIREBASE_CLIENT_ID', ''),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': os.environ.get('FIREBASE_CLIENT_CERT_URL', ''),
        'universe_domain': 'googleapis.com',
    }

# Reglas de negocio de la biblioteca
LOAN_DAYS = 14          # días de plazo de un préstamo
MAX_ACTIVE_LOANS = 3    # préstamos activos simultáneos por estudiante

# Login
LOGIN_URL = 'accounts:login'

# Paginación
PAGE_SIZE = 10

# True cuando se corre `python manage.py test`: los tests nunca deben tocar Firestore
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
