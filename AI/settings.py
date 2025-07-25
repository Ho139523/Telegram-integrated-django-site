from decouple import config
from pathlib import Path
 
# Build paths inside the project like this: BASE_DIR / 'subdir'. 
BASE_DIR = Path(__file__).resolve().parent.parent 
 
 
# Quick-start development settings - unsuitable for production 
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/ 
 
# SECURITY WARNING: keep the secret key used in production secret! 
SECRET_KEY = config('SECRET_KEY') 
 
# SECURITY WARNING: don't run with debug turned on in production! 
DEBUG = True 
 
# ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=[], cast=lambda v: [s.strip() for s in v.split(',')]) 
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']#config('ALLOWED_HOSTS', cast=Csv())
CSRF_TRUSTED_ORIGINS = ['https://*.ngrok-free.app', 'https://*.serveo.net', 'https://*.loca.lt', 'https://*.trycloudflare.com', 'https://intelleum.ir']
 
 
LOGIN_REDIRECT_URL='accounts:profile' 
LOGIN_URL='accounts:login' 
 
 
# Application definition 
 
INSTALLED_APPS = [ 
    'django.contrib.admin', 
    'django.contrib.auth', 
    'django.contrib.contenttypes', 
    'django.contrib.sessions', 
    'django.contrib.messages', 
    'django.contrib.staticfiles',
    
    # Packages
    "rest_framework", 
    'widget_tweaks',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    "social_django",
    'crispy_forms',
    'crispy_bootstrap5',
    'tailwind',
    'theme',
    
    # Apps
    'accounts', 
    'heartpred', 
    "myapi", 
    "cv",
    "mainpage",
    "products",
    "telbot",
    "payment",
]


if DEBUG:
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)
    mimetypes.add_type("application/javascript", ".js", True)


import os

# Create log directory if it doesn't exist
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)




LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {name} | {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'errors': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'level': 'ERROR',
            'formatter': 'verbose',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'errors'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },

    'root': {
        'handlers': ['console', 'errors'],
        'level': 'WARNING',
    },
}




 
MIDDLEWARE = [ 
    'django.middleware.security.SecurityMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # Disable CSRF temporarily (only for testing)
    # 'django.middleware.csrf.CsrfViewMiddleware',
]


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

 
ROOT_URLCONF = 'AI.urls' 
 
TEMPLATES = [ 
    { 
        'BACKEND': 'django.template.backends.django.DjangoTemplates', 
        'DIRS': [BASE_DIR / 'templates'], 
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
 
WSGI_APPLICATION = 'AI.wsgi.application' 
 
 
# Database 
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases 
 
DATABASES = { 
    'default': { 
        'ENGINE': config("engine"), 
        'NAME': BASE_DIR / config("db_dir"), 
    } 
} 
 
 
# Password validation 
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators 
 
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
# https://docs.djangoproject.com/en/4.2/topics/i18n/ 
 
LANGUAGE_CODE = 'en-us' 
 
TIME_ZONE = 'UTC' 
 
USE_I18N = True 
 
USE_TZ = True 
 
 
# Static files (CSS, JavaScript, Images) 
# https://docs.djangoproject.com/en/4.2/howto/static-files/ 
 
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "theme" / "static",
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


 
MEDIA_URL = config('MEDIA_URL') 
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT') 
 
# Default primary key field type 
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field 
 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 
AUTH_USER_MODEL = config('AUTH_USER_MODEL') 
 
 
EMAIL_BACKEND = config('EMAIL_BACKEND') 
EMAIL_HOST = config('EMAIL_HOST') 
EMAIL_USE_TLS = config('EMAIL_USE_TLS') 
EMAIL_PORT = config('EMAIL_PORT') 
EMAIL_HOST_USER = config('EMAIL_HOST_USER') 
EMAIL_HOST_PASSWORD =config('EMAIL_HOST_PASSWORD')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',  # Ensure this is properly listed
    'allauth.account.auth_backends.AuthenticationBackend',
]



SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://public-cups-nail.loca.lt/socials/complete/google-oauth2/'

SITE_ID = 1


# LOGIN_URL = "auth/login/google-oauth2"
LOGOUT_REDIRECT_URL = 'mainpage:home'
SOCIAL_AUTH_URL_NAMESPACE = 'social'


SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True


SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'utils.funcs.django_social_redirect.custom_complete',  # Moved here
)

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = 'bootstrap5'


#SECURE_SSL_REDIRECT = True
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
#SECURE_HSTS_SECONDS = 31536000
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#SECURE_HSTS_PRELOAD = True


# DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
# FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
# FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB


ZARINPAL = {
    'MERCHANT_ID': config('MECHANT_ID'),  # مرچنت کد شما
    'CALLBACK_URL': 'https://intelleum.ir/verify/',  # آدرس بازگشت
    'SANDBOX': True,  # برای محیط تست (False برای محیط واقعی)
}


SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"
CSRF_TRUSTED_ORIGINS = ['https://intelleum.ir']


# تنظیم کش
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# مدت زمان اعتبار لینک پرداخت (ثانیه)
PAYMENT_LINK_TIMEOUT = 3600  # 1 ساعت

TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = ["127.0.0.1"]
