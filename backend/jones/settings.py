import os
from datetime import timedelta
from pathlib import Path

def _split_csv(val):
    """Split a string by comma or semicolon (Cloud Run env vars use ';')."""
    if ';' in val:
        return [x.strip() for x in val.split(';') if x.strip()]
    return [x.strip() for x in val.split(',') if x.strip()]

try:
    from decouple import config, Csv  # type: ignore
except Exception:
    def config(key, default=None, cast=None):
        val = os.getenv(key, default)
        if cast is Csv and isinstance(val, str):
            return _split_csv(val)
        return val
    class Csv:
        pass

try:
    import dj_database_url  # type: ignore
except Exception:
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-d+#3@+ej6n6h-hvb(i4_uc@46m529hf_7!8u49#%2$r6qvh!$v')
DEBUG = str(config('DEBUG', default='False')).lower() in ('1', 'true', 'yes', 'on')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='localhost,127.0.0.1,backend')

# Admin API Key for CMS product management
ADMIN_API_KEY = config('ADMIN_API_KEY', default='')

SITE_NAME = 'Jones'
SITE_DESC = ('Discover Endless Possibilities with Custom Prints - From Trendy Apparel '
             'to Unique Accessories and Home Décor, Find the Perfect Product to Express Your Style!')
SITE_LOGO = '/static/images/logo.png'
SITE_FAVICON = '/static/images/favicon.png'
SITE_META_IMAGE = '/static/images/meta_image.png'
PROFILE_AVATAR_DEFAULT = '/static/images/default_avatar.png'

SITE_URL = config('SITE_URL', default='http://localhost:3000/')
DJANGO_BASE_URL = config('DJANGO_BASE_URL', default='http://localhost:8000')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = str(config('SECURE_SSL_REDIRECT', default='False')).lower() in ('1', 'true', 'yes', 'on')

# Only bind cookies to a parent domain when explicitly configured via
# COOKIE_DOMAIN env (e.g. ".jones.com" to share sessions across
# www and bare apex). Otherwise leave cookies host-only so the admin
# works on any mapped domain without the browser refusing to send the
# CSRF cookie back on a different parent.
COOKIE_DOMAIN = (config('COOKIE_DOMAIN', default='') or '').strip()
if COOKIE_DOMAIN and COOKIE_DOMAIN.lower() != 'none':
    SESSION_COOKIE_DOMAIN = COOKIE_DOMAIN
    CSRF_COOKIE_DOMAIN = COOKIE_DOMAIN
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'profiles',
    'articles',
    'utils',
    'pod_shop',
    'myshop',
    'django_cleanup',
    'easy_thumbnails',
    'django_extensions',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'drf_spectacular',
    'corsheaders',
    'ckeditor',
    'django_ace',
    'captcha',
    'django_filters',
    'crispy_forms',
    'django_jsonform',
    'crispy_bootstrap5',
    'static_sitemaps',
    'django_crontab',
    'django_countries',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth.registration',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    # Keep last so its ready() hook can strip other apps' admin registrations.
    'media_library',
]

SITE_ID = 1

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 400,
        'width': '100%',
        'extraAllowedContent': '*(*);*{*}',
        'allowedContent': True,
        'removePlugins': 'stylesheetparser',
        'forcePasteAsPlainText': False,
    },
    'full': {
        'toolbar': 'Full',
        'height': 400,
        'width': '100%',
        'extraAllowedContent': '*(*);*{*}',
        'allowedContent': True,
        'removePlugins': 'stylesheetparser',
        'forcePasteAsPlainText': False,
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'utils.middleware.BotBlockerMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'djangorestframework_camel_case.middleware.CamelCaseMiddleWare',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'jones.urls'

WSGI_APPLICATION = 'jones.wsgi.application'

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
                'utils.context_processors.site_common',
            ],
        },
    },
]

DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL and dj_database_url:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    PG_NAME = config('POSTGRES_DB', default=None)
    PG_USER = config('POSTGRES_USER', default=None)
    PG_PASSWORD = config('POSTGRES_PASSWORD', default=None)
    PG_HOST = config('DB_HOST', default='db')
    PG_PORT = config('DB_PORT', default='5432')
    if all([PG_NAME, PG_USER, PG_PASSWORD]):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': PG_NAME,
                'USER': PG_USER,
                'PASSWORD': PG_PASSWORD,
                'HOST': PG_HOST,
                'PORT': PG_PORT,
                'CONN_MAX_AGE': 600,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
}

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': False,
    'USER_DETAILS_SERIALIZER': 'profiles.api.serializers.CustomUserDetailsSerializer',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(config('JWT_ACCESS_MINUTES', default='30'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(config('JWT_REFRESH_DAYS', default='1'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'jones_API',
    'DESCRIPTION': 'Pezura',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

CORS_ALLOW_HEADERS = (
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Origin",
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

_raw_cors = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv()
)
if isinstance(_raw_cors, list):
    _expanded_cors = []
    for item in _raw_cors:
        _expanded_cors.extend(_split_csv(item))
    _raw_cors = _expanded_cors
CORS_ALLOWED_ORIGINS = [origin.rstrip('/') for origin in _raw_cors]
CORS_ALLOW_CREDENTIALS = True

_raw_csrf = config(
    'CSRF_TRUSTED_ORIGINS',
    cast=Csv(),
    default='http://localhost:8000,http://127.0.0.1:8000'
)
# Handle case where decouple's Csv() didn't split semicolons
if isinstance(_raw_csrf, list):
    _expanded = []
    for item in _raw_csrf:
        _expanded.extend(_split_csv(item))
    _raw_csrf = _expanded
CSRF_TRUSTED_ORIGINS = [origin.rstrip('/') for origin in _raw_csrf]

# Always include the Django API base URL in trusted origins
if DJANGO_BASE_URL.rstrip('/') not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(DJANGO_BASE_URL.rstrip('/'))

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 400,
        'width': '100%',
        'extraAllowedContent': '*(*);*{*}',
        'allowedContent': True,
        'removePlugins': 'stylesheetparser',
        'forcePasteAsPlainText': False,
    },
    'full': {
        'toolbar': 'Full',
        'height': 400,
        'width': '100%',
        'extraAllowedContent': '*(*);*{*}',
        'allowedContent': True,
        'removePlugins': 'stylesheetparser',
        'forcePasteAsPlainText': False,
    },
}

REDIS_URL = config('REDIS_URL', default=None)
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
        }
    }

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_BLACKLIST = [
    'fuck', 'pussy', 'cunt', 'cock', 'ass', 'shit', 'concac', 'cailon', 'dick',
    'hcm', 'congsan', 'dmcs', 'csvn', 'hochiminh', 'bacho', 'moderator', 'admin', 'administrator'
]
ACCOUNT_USERNAME_MIN_LENGTH = 6
USERNAME_MIN_LENGTH = 6

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id', 'first_name', 'last_name', 'middle_name', 'name',
            'name_format', 'picture', 'short_name'
        ],
        'EXCHANGE_TOKEN': True,
        'LOCALE_FUNC': 'path.to.callable',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v13.0',
        'GRAPH_API_URL': 'https://graph.facebook.com/v13.0',
    }
}

STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = config('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))
MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# ── Storage backends (Django 5 STORAGES dict) ───────────────────────────────
# If GS_BUCKET_NAME is set, upload media to Google Cloud Storage.
# URLs are served same-domain via a Vercel rewrite:
#   jones.com/admin/uploads/:path*  →  storage.googleapis.com/<bucket>/:path*
# Keeping the admin URL on the primary domain avoids the SEO/referrer loss
# that comes with serving product images from storage.googleapis.com.
GS_BUCKET_NAME = config('GS_BUCKET_NAME', default='')

if GS_BUCKET_NAME:
    GS_DEFAULT_ACL = config('GS_DEFAULT_ACL', default='publicRead')
    GS_CUSTOM_ENDPOINT = config(
        'GS_CUSTOM_ENDPOINT',
        default='https://jones.com/images',
    )
    MEDIA_URL = GS_CUSTOM_ENDPOINT.rstrip('/') + '/'
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
            'OPTIONS': {
                'bucket_name': GS_BUCKET_NAME,
                'default_acl': GS_DEFAULT_ACL,
                'querystring_auth': False,
                'file_overwrite': False,
                'custom_endpoint': GS_CUSTOM_ENDPOINT,
                'object_parameters': {'cache_control': 'public, max-age=31536000, immutable'},
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
else:
    MEDIA_URL = config('MEDIA_URL', default='/media/')
    STORAGES = {
        # SequentialFileSystemStorage replaces Django 5's random 7-char
        # collision suffix with a predictable -1, -2, -3 counter so the FE
        # SEO layer can build canonical image URLs from the slug alone.
        'default': {'BACKEND': 'jones.storage.SequentialFileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False

NEXTJS_LOGIN_COOKIE_EXPIRE_DAYS = int(config('NEXTJS_LOGIN_COOKIE_EXPIRE_DAYS', default='30'))
NEXTJS_REDIRECT_URL = config('NEXTJS_REDIRECT_URL', default='http://localhost:8000/')
NEXTJS_JWT_KEY_NAME = 'jones_jwt'
NEXTJS_REFRESH_TOKEN_KEY_NAME = 'jones_refresh'
# Redirect to admin root after login when using Django auth
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = NEXTJS_REDIRECT_URL

# Admin Panel Authentication
LOGIN_URL = 'admin:login'

STATICSITEMAPS_REFRESH_AFTER = 60 * 3
STATICSITEMAPS_ROOT_SITEMAP = 'musicGearShop.sitemaps.sitemaps'
STATICSITEMAPS_INDEX_TEMPLATE = 'sitemap_index.xml'
STATICSITEMAPS_MOCK_SITE = True
STATICSITEMAPS_MOCK_SITE_NAME = 'fulfillnext'
STATICSITEMAPS_PING_GOOGLE = False
STATICSITEMAPS_ROOT_DIR = ''
STATICSITEMAPS_USE_GZIP = True
STATICSITEMAPS_URL = config(
    'STATICSITEMAPS_URL',
    default=f"{DJANGO_BASE_URL.rstrip('/')}/media/static_sitemaps/",
)
STATICSITEMAPS_MOCK_SITE_PROTOCOL = config(
    'STATICSITEMAPS_PROTOCOL',
    default='https' if DJANGO_BASE_URL.startswith('https') else 'http'
)

LOG_DIR = config('LOG_DIR', default=str(BASE_DIR / 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'}},
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'filename': os.path.join(LOG_DIR, 'django_app_errors.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {'class': 'logging.StreamHandler', 'level': 'INFO', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cron Jobs Configuration
CRONJOBS = [
    # Generate sitemap every hour at minute 0
    ('0 * * * *', 'pod_shop.management.commands.generate_sitemap.Command', [], {'verbosity': 1}),
    
    # Alternative: Generate sitemap every 30 minutes
    # ('*/30 * * * *', 'pod_shop.management.commands.generate_sitemap.Command'),
    
    # Log output to file
    # ('0 * * * *', 'pod_shop.management.commands.generate_sitemap.Command', [], {}, '>> /var/log/sitemap_cron.log 2>&1'),
]

# Set timezone for cron jobs
CRONTAB_DJANGO_MANAGE_PATH = '/app/manage.py'
CRONTAB_PYTHON_EXECUTABLE = '/usr/local/bin/python'

try:
    from .local_settings import *  
except ImportError:
    pass

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# ─── Bot Blocker Configuration ───────────────────────────────────────────────────
BOT_BLOCKER_ENABLED = True
BOT_BLOCKER_RATE_LIMIT = 120  # Max API requests per minute per IP
BOT_BLOCKER_WHITELIST_IPS = [
    # Add trusted IPs here (e.g., your frontend server IP, monitoring services)
    # '1.2.3.4',
]
BOT_BLOCKER_API_PREFIXES = ['/api/']  # Paths to protect
