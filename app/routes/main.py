"""Main application routes for the AERIS dashboard."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.database import get_dashboard_statistics, get_recent_analyses


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Render the public landing page.

    If the user is already authenticated, redirecting through the dashboard
    keeps the application flow simple and avoids showing duplicate entry
    points.
    """
    if current_user.is_authenticated:
        return dashboard()

    return render_template("dashboard.html", authenticated=False)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Render the authenticated AERIS dashboard."""

    try:
        statistics = get_dashboard_statistics(current_user.id)
    except Exception:
        statistics = {
            "total_analyses": 0,
            "telemetry_analyses": 0,
            "image_analyses": 0,
            "anomalies_detected": 0,
        }

    try:
        recent_analyses = get_recent_analyses(current_user.id, limit=5)
    except Exception:
        recent_analyses = []

    return render_template(
        "dashboard.html",
        authenticated=True,
        user=current_user,
        statistics=statistics,
        recent_analyses=recent_analyses,
    )


@main_bp.route("/profile")
@login_required
def profile():
    """Render the authenticated user's profile page."""

    return render_template(
        "profile.html",
        user=current_user,
    )