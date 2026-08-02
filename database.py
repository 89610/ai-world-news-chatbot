"""
Database initialization.

WHY THIS FILE EXISTS:
`db` (SQLAlchemy) and `bcrypt` (password hashing) are defined here,
separately from app.py, so model files in `models/` can import them
without a circular import. Flask-Migrate is wired up too, so schema
changes going forward are tracked as versioned migrations instead of
relying only on db.create_all(), which can't alter existing tables.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


def init_db(app):
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    with app.app_context():
        from models import user, bookmark, history, news_cache, user_session  # noqa: F401

        db.create_all()