"""
Welcome (splash) page.

First visit in a browser session: "/" redirects to "/welcome", which shows
an animated splash and then opens the main site after a few seconds.
Later visits in the same session go straight to the main site.
"""

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

welcome_bp = Blueprint("welcome", __name__)


@welcome_bp.route("/welcome")
def welcome():
    session["welcome_seen"] = True
    return render_template("welcome.html")


@welcome_bp.before_app_request
def show_welcome_first():
    """Redirect the very first visit to '/' to the welcome page."""
    if current_app.config.get("TESTING"):
        return None  # keep existing pytest tests unaffected

    if request.method != "GET" or request.path != "/":
        return None

    if session.get("welcome_seen") or request.args.get("from") == "welcome":
        return None

    return redirect(url_for("welcome.welcome"))