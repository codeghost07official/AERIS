
import os

import psycopg

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import create_user, get_db_connection

auth = Blueprint("auth", __name__)

oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")

        try:
            password_hash = generate_password_hash(password)
            user_id = create_user(name, email, password_hash)

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))

        except psycopg.errors.UniqueViolation:
            flash("An account with this email already exists.", "error")

        except Exception:
            current_app.logger.exception("Registration failed")
            flash(
                "Registration failed. Please check the server log.",
                "error",
            )

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:

                    cur.execute(
                        """
                        SELECT id, name, email, password_hash
                        FROM public.users
                        WHERE email = %s
                        """,
                        (email,),
                    )

                    user = cur.fetchone()

            if (
                user
                and user["password_hash"]
                and check_password_hash(
                    user["password_hash"],
                    password,
                )
            ):

                session.clear()
                session["user_id"] = str(user["id"])
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]

                return redirect(url_for("main.dashboard"))

            flash("Invalid email or password.", "error")

        except Exception:
            current_app.logger.exception("Login failed")
            flash("Login failed due to a database error.", "error")

    return render_template("login.html")


@auth.route("/google")
def google_login():

    redirect_uri = url_for(
        "auth.google_callback",
        _external=True,
    )

    return google.authorize_redirect(redirect_uri)


@auth.route("/google/callback")
def google_callback():

    try:
        token = google.authorize_access_token()

        user_info = token.get("userinfo")

        if not user_info:
            user_info = google.parse_id_token(token)

        email = user_info.get("email", "").strip().lower()
        name = user_info.get("name") or "AERIS User"
        google_id = user_info.get("sub")

        if not email or not google_id or not user_info.get("email_verified"):
            flash(
                "Google account details could not be retrieved.",
                "error",
            )
            return redirect(url_for("auth.login"))

        with get_db_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id, name, email
                    FROM public.users
                    WHERE email = %s
                    """,
                    (email,),
                )

                user = cur.fetchone()

                if user:

                    cur.execute(
                        """
                        UPDATE public.users
                        SET google_id = %s
                        WHERE id = %s
                        """,
                        (google_id, user["id"]),
                    )

                    user_id = user["id"]
                    user_name = user["name"]

                else:
                    user_id = create_user(
                        name,
                        email,
                        google_id=google_id,
                    )
                    user_name = name

        session.clear()
        session["user_id"] = str(user_id)
        session["user_name"] = user_name
        session["user_email"] = email

        return redirect(url_for("main.dashboard"))

    except Exception:
        current_app.logger.exception(
            "Google authentication failed"
        )

        flash(
            "Google sign-in could not be completed.",
            "error",
        )

        return redirect(url_for("auth.login"))


@auth.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))

