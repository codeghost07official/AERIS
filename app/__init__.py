
import os
import tempfile

from flask import Flask
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


def create_app():
    app = Flask(__name__)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required.")

    app.config["SECRET_KEY"] = secret_key
    app.config["UPLOAD_FOLDER"] = os.getenv(
        "UPLOAD_FOLDER",
        os.path.join(tempfile.gettempdir(), "aeris-uploads"),
    )
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.config["GOOGLE_REDIRECT_URI"] = os.getenv("GOOGLE_REDIRECT_URI")
    app.config["SESSION_COOKIE_SECURE"] = os.getenv(
        "SESSION_COOKIE_SECURE", ""
    ).lower() in {"1", "true", "yes"}

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize Google OAuth
    from app.auth import oauth
    oauth.init_app(app)

    # Register blueprints
    from app.routes import main
    from app.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    from app.database import init_db
    init_db()

    return app
