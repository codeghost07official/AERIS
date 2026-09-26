import os

from flask import Flask
from flask_login import LoginManager

from app.config import Config
from app.database import get_user_by_id


login_manager = LoginManager()


def create_app():
    """
    Application factory for the AERIS Flask application.

    AERIS:
    Aerospace Equipment & Reliability Intelligence System
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directories exist.
    os.makedirs(app.config["TELEMETRY_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["IMAGE_UPLOAD_FOLDER"], exist_ok=True)

    # Initialize Flask-Login.
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load an authenticated user from the database.

        Flask-Login stores the user's ID in the session and calls
        this function whenever the current user needs to be restored.
        """
        try:
            return get_user_by_id(user_id)
        except Exception:
            return None

    # Register application blueprints.
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.telemetry import telemetry_bp
    from app.routes.images import images_bp
    from app.routes.history import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(history_bp)

    return app