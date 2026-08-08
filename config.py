"""
Configuration classes for the AI World News Chatbot.

WHY THIS FILE EXISTS:
All secrets (API keys, DB credentials, secret keys) must live in
environment variables, never hardcoded in source — this file is the
single place that reads those variables and turns them into settings
Flask understands. Copy `.env.example` to `.env` and fill in real
values before running the app.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables from a local .env file, if present


class BaseConfig:
    """Settings shared across every environment (dev/test/prod)."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")

    # --- MySQL ----------------------------------------------------------
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "ai_news_chatbot")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_pre_ping + pool_recycle prevent the classic "MySQL server has
    # gone away" error that shows up after a connection sits idle past
    # MySQL's own timeout.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- News APIs (Phase 4) ------------------------------------------
    NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
    GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
    GUARDIAN_API_KEY = os.environ.get("GUARDIAN_API_KEY", "")
    NYTIMES_API_KEY = os.environ.get("NYTIMES_API_KEY", "")
    MEDIASTACK_API_KEY = os.environ.get("MEDIASTACK_API_KEY", "")

    # --- AI Chatbot (Phase 5) -------------------------------------------
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    CHATBOT_MODEL = os.environ.get("CHATBOT_MODEL", "gemini-flash-latest")

    # --- Newsletter email (Phase 6) --------------------------------------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME", "")

    # --- Caching ----------------------------------------------------------
    NEWS_CACHE_TTL_SECONDS = int(os.environ.get("NEWS_CACHE_TTL_SECONDS", "300"))

    # --- File uploads (profile pictures) ---------------------------------
    # Stored on Cloudinary, NOT the local server disk — Railway (and
    # most cheap hosts) wipe local files on every restart/redeploy,
    # which is exactly why uploaded pictures were disappearing.
    # Cloudinary gives a permanent URL that survives restarts forever.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB cap per uploaded file
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

    # --- Sessions ("Remember Me") -----------------------------------------
    REMEMBER_COOKIE_DURATION_DAYS = int(os.environ.get("REMEMBER_COOKIE_DURATION_DAYS", "30"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"
    # No MySQL password configured yet? Fall back to a local SQLite
    # file so the app is runnable immediately, before MySQL is set up.
    if not BaseConfig.MYSQL_PASSWORD and BaseConfig.MYSQL_HOST == "localhost":
        SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    # Cookies only sent over HTTPS, and "Lax" SameSite policy — the
    # standard, safe settings for a real deployed site. Not set in
    # DevelopmentConfig since localhost runs over plain HTTP, and a
    # Secure-only cookie would silently break local login.
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_SAMESITE = "Lax"


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


_CONFIGS = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(name: str = None):
    """Resolve a config class by name, defaulting to FLASK_ENV then development."""
    name = name or os.environ.get("FLASK_ENV", "development")
    return _CONFIGS.get(name, DevelopmentConfig)
