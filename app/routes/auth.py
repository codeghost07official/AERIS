from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import (
    create_user,
    get_user_by_email,
    get_user_by_google_id,
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
)


class User:
    """
    Lightweight Flask-Login user object.

    This object converts the database user dictionary into the
    interface expected by Flask-Login.
    """

    def __init__(self, user_data):
        self.id = str(user_data["id"])
        self.email = user_data.get("email")
        self.password_hash = user_data.get("password_hash")
        self.name = user_data.get("name")
        self.google_id = user_data.get("google_id")
        self.created_at = user_data.get("created_at")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


def user_from_database(user_data):
    """
    Convert a database record into a Flask-Login User object.
    """
    if not user_data:
        return None

    return User(user_data)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle email/password login.
    """
    if request.method == "GET":
        return render_template("auth/login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter both your email and password.", "error")
        return render_template("auth/login.html")

    user_data = get_user_by_email(email)

    if not user_data:
        flash("Invalid email or password.", "error")
        return render_template("auth/login.html")

    password_hash = user_data.get("password_hash")

    if not password_hash:
        flash(
            "This account uses Google authentication. "
            "Please continue with Google.",
            "error",
        )
        return render_template("auth/login.html")

    if not check_password_hash(password_hash, password):
        flash("Invalid email or password.", "error")
        return render_template("auth/login.html")

    user = user_from_database(user_data)

    login_user(user)

    flash("Welcome back to AERIS.", "success")

    next_page = request.args.get("next")

    if next_page and next_page.startswith("/"):
        return redirect(next_page)

    return redirect(url_for("main.dashboard"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new AERIS account.
    """
    if request.method == "GET":
        return render_template("auth/register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name:
        flash("Please enter your name.", "error")
        return render_template("auth/register.html")

    if not email:
        flash("Please enter your email address.", "error")
        return render_template("auth/register.html")

    if not password:
        flash("Please enter a password.", "error")
        return render_template("auth/register.html")

    if len(password) < 8:
        flash(
            "Password must contain at least 8 characters.",
            "error",
        )
        return render_template("auth/register.html")

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return render_template("auth/register.html")

    existing_user = get_user_by_email(email)

    if existing_user:
        flash(
            "An account with this email address already exists.",
            "error",
        )
        return redirect(url_for("auth.login"))

    password_hash = generate_password_hash(password)

    try:
        user_data = create_user(
            email=email,
            password_hash=password_hash,
            name=name,
        )
    except Exception:
        flash(
            "Unable to create your account right now. "
            "Please try again.",
            "error",
        )
        return render_template("auth/register.html")

    user = user_from_database(user_data)

    login_user(user)

    flash("Your AERIS account has been created.", "success")

    return redirect(url_for("main.dashboard"))


@auth_bp.route("/google")
def google_login():
    """
    Begin Google OAuth authentication.

    The actual OAuth client is intentionally handled only when
    Google credentials are configured.
    """
    from flask import current_app

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        flash(
            "Google authentication is not configured yet.",
            "error",
        )
        return redirect(url_for("auth.login"))

    flash(
        "Google authentication will be enabled when OAuth is configured.",
        "info",
    )

    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    """
    Sign out the current user.
    """
    logout_user()

    flash("You have been signed out.", "success")

    return redirect(url_for("auth.login"))