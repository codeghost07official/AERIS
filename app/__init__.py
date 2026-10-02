
import os
from flask import Flask
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

load_dotenv(".env")


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "aeris-development-key")
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path, "static", "uploads"
    )
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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

