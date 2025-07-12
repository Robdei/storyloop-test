"""Main routes for the application."""
from flask import Blueprint, redirect, url_for
from flask_login import current_user

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Redirect authenticated users to dashboard, show landing page for others."""
    if current_user.is_authenticated:
        return redirect(url_for("story.dashboard"))
    return redirect(url_for("auth.login"))