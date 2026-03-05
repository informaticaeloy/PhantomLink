# config.py
import os


class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-muy-segura-cambiar-en-produccion-123456'
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 8 * 60 * 60  # 8 horas en segundos

    # Configuración del proxy
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    TIMEOUT = 30  # segundos
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    # Rutas
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    USERS_CSV = os.path.join(DATA_DIR, 'users.csv')
    ALLOWED_URLS_CSV = os.path.join(DATA_DIR, 'allowed_urls.csv')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')

    # Configuración de logs
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB por archivo de log
    MAX_LOG_FILES = 5  # Mantener 5 archivos de log por usuario