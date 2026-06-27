import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    FIREBASE_KEY_PATH = os.getenv('FIREBASE_KEY_PATH', './firebase-key.json')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET', '')
    FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY', '')

    RETELL_API_KEY = os.getenv('RETELL_API_KEY', '')
    RETELL_API_BASE_URL = os.getenv('RETELL_API_BASE_URL', 'https://api.retellai.com')
    RETELL_AGENT_ID = os.getenv('RETELL_AGENT_ID', '')
    RETELL_WEBHOOK_SECRET = os.getenv('RETELL_WEBHOOK_SECRET', '')

    GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', os.getenv('GOOGLE_PLACES_API_KEY', ''))

    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
