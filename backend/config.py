import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = None
    DATABASE = str(ROOT / 'database' / 'quiz.db')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 1024 * 1024


def environment_config():
    production = os.environ.get('APP_ENV', 'development').lower() == 'production'
    secret = os.environ.get('SECRET_KEY', '')
    if production and len(secret) < 32:
        raise RuntimeError('Production requires SECRET_KEY with at least 32 characters.')
    if production and not os.environ.get('DATABASE_PATH'):
        raise RuntimeError('Production requires DATABASE_PATH.')
    database = os.environ.get('DATABASE_PATH') or Config.DATABASE
    if production and not Path(database).is_absolute():
        raise RuntimeError('Production DATABASE_PATH must be an absolute path.')
    return {
        'SECRET_KEY': secret or secrets.token_hex(32),
        'DATABASE': database,
        'SESSION_COOKIE_SECURE': production,
    }
