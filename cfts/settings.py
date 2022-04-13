'''
Jan 21st, 2022

Oh boy, here we go. Adding comments 'cause no one else ever bothered to... me included. If you are reading this then welcome to the web team and welcome to CFTS.
My name is Alex but everyone (at work) calls me Xander. I'm going to do my best and add comments to try and explain how this all works so that one day
you can take over this project once I'm gone.

At the moment this project is kept on my personal github account https://github.com/Alexander-Alvarado/cftsPublic, it may move in the future.

At the time of writing this we are using Django 4.0.3 and Python 3.9
'''

import os
'''
you are going to need to make a network.py file in the same directory that this settings file lives, this file holds all of the network specific settings.
in the network file will go the SECRET_KEY, DEBUG, ALLOWED_HOSTS, and NETWORK settings for that network
'''
import cfts.network as ENV
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ENV.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENV.DEBUG

'''
in the SIPR production network file you will see that there are some hosts that don't start with cfts, these were the hosts for the legacy transfer service.
those hosts are accepted and redirected to the new cfts host
'''
ALLOWED_HOSTS = ENV.ALLOWED_HOSTS

'''
this is the name of the network the system is being hosted on, ex: SIPR, NIPR, CPN-X
these names should match the Network objects in the database
'''
NETWORK = ENV.NETWORK

KEYS_DIR = os.path.join(BASE_DIR, "KEYS")

# setting this to True will dissable all request submission and display a message on the homepage
DISABLE_SUBMISSIONS = ENV.DISABLE_SUBMISSIONS

SKIP_FILE_REVIEW = ENV.SKIP_FILE_REVIEW

PRIVATE_KEY_PASSWORD = ENV.PRIVATE_KEY_PASSWORD

# Application definition

INSTALLED_APPS = [
    'django_static_jquery_ui',
    'pages.apps.PagesConfig',  # came from the pages > apps.py tells django its an app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # used to determine a users browser, we don't like Internet Explore around here
    'django_user_agents',
    # used to easily add bootstrap styling to Django generated html forms
    'crispy_forms',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# defining what bootstrap classes to add to different levels of the Django messages framework
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

ROOT_URLCONF = 'cfts.urls'

LOGIN_URL = '/login'

LOGOUT_REDIRECT_URL = '/frontend'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Here we set the location of the templates
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'cfts.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Error Logging for running in IIS, logs can be found in the logs/ folder
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        },
    },
    'formatters': {
        'timestamp': {
            'format': '{asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'debugTrue': {
            'level': 'ERROR',
            'filters': ['require_debug_true'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'maxBytes': 1024*1024*1,
            'backupCount': 5,
            'formatter': 'timestamp'
        },
        'debugFalse': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'maxBytes': 1024*1024*1,
            'backupCount': 5,
            'formatter': 'timestamp'
        },
        'file': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/sql.log'),
            'maxBytes': 1024*1024*1,
            'backupCount': 5,
        },
        'console': {
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'timestamp'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['debugTrue', 'debugFalse', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        # 'django.db.backends': {
        #     'handlers': ['file'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'cfts\static')
]

'''
this is very important!!! this changes the behavior of the Django "collectstatic" command. so many issues have been caused due to browsers caching and not refetching static files.
this setting appends all collected static file names with an MD5 hash of the file contents and will inject the new filenames into all of the html templates.
this means that any modifications to a static file will change the file name and require the browser to fetch the new modified static file.
the class for this setting can be found in the static.py file in the same directory as this settings file

Important: to use this properly you need to collect static files with the following command: "python manage.py collectstatic --clear --noinput"
the --clear flag will delete all static files before recollecting them, the --noinput flag is just for convenience
'''
STATICFILES_STORAGE = 'cfts.static.ManifestStaticFilesStorageSubClass'

UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
PULLS_DIR = os.path.join(BASE_DIR, 'pulls')
TEMP_FILES_DIR = os.path.join(BASE_DIR, 'tempFiles')
SCANTOOL_DIR = os.path.join(BASE_DIR, 'cfts\scan')
SCANTOOL_TEMPDIR = os.path.join(SCANTOOL_DIR, 'temp')
DROPS_TEMPDIR = os.path.join(BASE_DIR, 'cfts\drop')
DROPS_DIR = os.path.join(BASE_DIR, 'drops')
