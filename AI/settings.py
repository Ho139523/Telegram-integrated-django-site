from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
 
# Build paths inside the project like this: BASE_DIR / 'subdir'. 
BASE_DIR = Path(__file__).resolve().parent.parent 
 
 
# Quick-start development settings - unsuitable for production 
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/ 
 
# SECURITY WARNING: keep the secret key used in production secret! 
SECRET_KEY = os.environ.get('SECRET_KEY')
 
# SECURITY WARNING: don't run with debug turned on in production! 
DEBUG = True

BASE_URL = os.environ.get("BASE_URL")


ALLOWED_HOSTS = [
    '192.168.1.141',
    '127.0.0.1',
    'localhost',
    "intellium.ir",
    "intellium.ir:8443",
    "www.intellium.ir",
    "www.intellium.ir:8443",
]

CSRF_TRUSTED_ORIGINS = [
    "https://intellium.ir",
    "https://intellium.ir:8443",
]
 

current_site = 'https://intellium.ir'
SITE_API = 'https://intellium.ir'
 
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
    'widget_tweaks',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'crispy_forms',
    'crispy_bootstrap5',
    'tailwind',
    'theme',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    'django_celery_beat',

    # Apps
    'products',
    'accounts',
    'heartpred',
    'myapi',
    'cv',
    'mainpage',
    'telbot',
    'aiobot',
    'payment',
    'ai_chat',
    'subscription',
    'payments.apps.PaymentsConfig',
    'balebot',
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]


CORS_ALLOWED_ORIGINS = [
    "https://intellium.ir",
    "https://intellium.ir:8443",
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
        'ENGINE': os.environ.get("engine"), 
        'NAME': BASE_DIR / os.environ.get("db_dir"), 
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
 
TIME_ZONE = 'Asia/Tehran' 
 
USE_I18N = True 
 
USE_TZ = True 
 


# Static files (CSS, JavaScript, Images)
STATIC_URL = os.environ.get('STATIC_URL', '/static/')
STATIC_ROOT = os.environ.get('STATIC_ROOT', BASE_DIR / 'staticfiles')

# Media files
MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', BASE_DIR / 'media')

# Additional locations of static files
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # اگر static folder جداگانه دارید
]

# اطمینان از اینکه collectstatic کار می‌کند
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'




# Default primary key field type 
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field 
 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 
AUTH_USER_MODEL = os.environ.get('AUTH_USER_MODEL') 
 
 
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND') 
EMAIL_HOST = os.environ.get('EMAIL_HOST') 
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS') 
EMAIL_PORT = os.environ.get('EMAIL_PORT') 
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') 
EMAIL_HOST_PASSWORD =os.environ.get('EMAIL_HOST_PASSWORD')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default backend
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth backend
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")  # از گوگل بگیر
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")  # از گوگل بگیر
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://your-domain.com/socials/complete/google-oauth2/'  # مسیر redirect واقعی سایت



ACCOUNT_LOGIN_METHODS = {'email', 'username'}

ACCOUNT_SIGNUP_FIELDS = [
    'email*',
    'username*',
    'password1*',
    'password2*',
]



SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'none'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}


# LOGIN_URL = "auth/login/google-oauth2"
LOGOUT_REDIRECT_URL = 'mainpage:home'


SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True




CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = 'bootstrap5'


SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # میتوانید session auth هم اضافه کنید برای admin panel:
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/day',
        'anon': '100/day',
    },
}




ZARINPAL = {
    'MERCHANT_ID': os.environ.get('MECHANT_ID'),  # مرچنت کد شما
    'CALLBACK_URL': BASE_URL + '/verify/',  # آدرس بازگشت
    'SANDBOX': True,  # برای محیط تست (False برای محیط واقعی)
}


SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"
FORCE_SCRIPT_NAME = ""


# تنظیم کش
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# مدت زمان اعتبار لینک پرداخت (ثانیه)
PAYMENT_LINK_TIMEOUT = 3600  # 1 ساعت

TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = ["127.0.0.1"]

##################################### AIOGRAM Security

BOT_SECRET_KEY = os.environ.get("BOT_SECRET_KEY", "please-change-me-in-prod")
BOT_SIGNATURE_EXPIRES = int(os.environ.get("BOT_SIGNATURE_EXPIRES", "60"))
BOT_NONCE_EXPIRES = int(os.environ.get("BOT_NONCE_EXPIRES", "300"))

TG_SESSION_STRING = "1BJWap1wBu455l3Q-PYf0gQkifW8PZXBOYoCAPy-6f5Fa51tPiiuAve2RFuvTbKwz9tn5CLVm6MlgsyF9W_HBQELdfpUkglfWD_hy6l-KsAG9_TJy-jcB1Vnp_QocYvxjzDrIUNLT3WNa15l5NA8xl0WGFWPbkJ4uKEknu1P_GsH8QR33vojCPRo5EGJ_6qw5q0j2halPIbUAJRmOvzCluVQ1za5U9SvQzvmCZphzNz29Py3BzL9HfHzGZampY2m8RNvwtt7MmSjSvQcV9-wOk4UT_hyzOUHhnEXEy9A_HqHLAMVfygbWBGilPAB0lyHsFZSM-pcRIQFIn2EzAm2yijsHiu3TWU4="


from urllib.parse import urlparse, urlunparse

def force_port_in_url(request, url):
    parsed = urlparse(url)
    # اگر پورت نیست، اضافه کن
    if parsed.port is None:
        parsed = parsed._replace(netloc=f"{parsed.hostname}:8443")
    return urlunparse(parsed)


REST_FRAMEWORK['URL_FIELD_NAME'] = 'url'
REST_FRAMEWORK['URL_TRANSFORM'] = force_port_in_url


from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}


AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_LOCK_OUT_AT_FAILURE = True


CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_TIMEZONE = 'Asia/Tehran'


REDIS_URL = "redis://127.0.0.1:6379/0"


# AI/settings.py
APPEND_SLASH = False  # اضافه کن
