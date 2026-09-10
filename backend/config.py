import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Config:
    # Set SECRET_KEY in the environment to keep sessions across restarts.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DATABASE = str(ROOT / 'database' / 'quiz.db')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 1024 * 1024
