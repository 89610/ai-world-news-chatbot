"""
AI World News Chatbot
----------------------
Application factory and entry point.

WHY THE FACTORY PATTERN:
Rather than a bare module-level `app = Flask(__name__)`, create_app()
lets the same codebase spin up under different configs (development,
testing, production) and makes the app testable — pytest can create a
fresh app instance per test without import-order side effects.

Run locally with:
    python app.py
"""

import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from database import init_db

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    # Railway (and most cloud hosts) terminate HTTPS at their edge
    # proxy, then forward requests to this app over plain HTTP
    # internally. Without ProxyFix, Flask doesn't realize the original
    # connection was secure — which can cause login/session cookies to
    # behave inconsistently, especially on mobile browsers that
    # enforce cookie security rules more strictly than desktop ones.
    # ProxyFix reads the proxy's X-Forwarded-* headers so Flask treats
    # the request correctly as HTTPS.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400 if app.config.get("ENV") == "production" else 0

    os.makedirs(app.instance_path, exist_ok=True)

    # --- Database -----------------------------------------------------
    init_db(app)

    # --- Auth -----------------------------------------------------------
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)
    csrf.init_app(app)

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Please sign in first.", "auth_required": True}), 401
        return redirect(url_for("auth.login", next=request.path))

    # --- Blueprints -----------------------------------------------------
    from routes.home import home_bp
    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.news import news_bp
    from routes.chat import chat_bp
    from routes.bookmark import bookmark_bp
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(bookmark_bp)

    # JSON API blueprints are exempt from Flask-WTF's CSRF check since
    # they're called via fetch() with a JSON body, not an HTML <form>.
    csrf.exempt(news_bp)
    csrf.exempt(chat_bp)
    csrf.exempt(bookmark_bp)

    # --- Error handlers ---------------------------------------------------
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("500.html"), 500

    # --- Template globals -------------------------------------------------
    @app.context_processor
    def inject_globals():
        import datetime
        return {
            "app_name": "AI World News Chatbot",
            "current_year": datetime.datetime.now().year,
        }

    # --- Template filters ---------------------------------------------------
    @app.template_filter("timeago")
    def timeago_filter(iso_string):
        import datetime as _dt

        if not iso_string:
            return ""
        try:
            published = _dt.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            return iso_string

        delta = _dt.datetime.utcnow() - published
        seconds = delta.total_seconds()
        if seconds < 3600:
            return f"{max(int(seconds // 60), 1)} min ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        return f"{int(seconds // 86400)} days ago"

    return app


app = create_app()

if __name__ == "__main__":
    import webbrowser

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open("http://127.0.0.1:5000")

    app.run(debug=app.config.get("DEBUG", True))
    

    