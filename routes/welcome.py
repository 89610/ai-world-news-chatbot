"""
Welcome (splash) page.

Every time the server starts, the first visit to "/" in a browser shows the
welcome page, which then opens the main site after a few seconds. Later
visits during the same server run go straight to the main site.

How: each server start generates a new random ID. The browser session stores
the ID it last saw the welcome page for. A new server run means a new ID, so
the welcome page shows again.
"""

import uuid

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

welcome_bp = Blueprint("welcome", __name__)

# Changes on every server start
SERVER_RUN_ID = uuid.uuid4().hex


@welcome_bp.route("/welcome")
def welcome():
    session["welcome_seen"] = SERVER_RUN_ID
    return render_template("welcome.html")


@welcome_bp.before_app_request
def show_welcome_first():
    """Redirect the first visit to '/' after each server start to the welcome page."""
    if current_app.config.get("TESTING"):
        return None  # keep existing pytest tests unaffected

    if request.method != "GET" or request.path != "/":
        return None

    if session.get("welcome_seen") == SERVER_RUN_ID or request.args.get("from") == "welcome":
        return None

    return redirect(url_for("welcome.welcome"))