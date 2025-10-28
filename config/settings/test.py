from .base import *  # noqa

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SPECTACULAR_SETTINGS = {
    "TITLE": "Test API",
    "SERVE_INCLUDE_SCHEMA": False,
}

TMDB_BEARER = "Bearer test-token"
