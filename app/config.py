import os
from pathlib import Path

from dotenv import load_dotenv


# Load variables from the project's .env file.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """
    Central configuration for the AERIS Flask application.
    """

    # ------------------------------------------------------------------
    # Flask
    # ------------------------------------------------------------------

    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not configured. "
            "Add SECRET_KEY to the .env file before starting AERIS."
        )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Add DATABASE_URL to the .env file before starting AERIS."
        )

    # ------------------------------------------------------------------
    # Google OAuth
    # ------------------------------------------------------------------

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # ------------------------------------------------------------------
    # Upload configuration
    # ------------------------------------------------------------------

    UPLOAD_FOLDER = BASE_DIR / "uploads"

    TELEMETRY_UPLOAD_FOLDER = UPLOAD_FOLDER / "telemetry"
    IMAGE_UPLOAD_FOLDER = UPLOAD_FOLDER / "images"

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Allowed telemetry files.
    ALLOWED_TELEMETRY_EXTENSIONS = {
        "csv",
    }

    # Allowed spacecraft image files.
    ALLOWED_IMAGE_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "tif",
        "tiff",
        "webp",
    }

    # ------------------------------------------------------------------
    # Machine-learning configuration
    # ------------------------------------------------------------------

    # Isolation Forest defaults.
    TELEMETRY_CONTAMINATION = 0.05
    TELEMETRY_RANDOM_STATE = 42
    TELEMETRY_MAX_SAMPLES = "auto"

    # Minimum number of valid numerical observations required
    # before performing telemetry anomaly detection.
    MIN_TELEMETRY_ROWS = 10

    # ------------------------------------------------------------------
    # Image-analysis configuration
    # ------------------------------------------------------------------

    # Maximum dimensions used when processing very large images.
    IMAGE_MAX_WIDTH = 4096
    IMAGE_MAX_HEIGHT = 4096

    # ------------------------------------------------------------------
    # Security configuration
    # ------------------------------------------------------------------

    # Prevent Flask from trusting arbitrary host information.
    # This can be overridden through the environment if necessary.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Set this to True in production when HTTPS is enabled.
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )

    # ------------------------------------------------------------------
    # Application metadata
    # ------------------------------------------------------------------

    APP_NAME = "AERIS"
    APP_FULL_NAME = "Aerospace Equipment & Reliability Intelligence System"
    PROJECT_TYPE = "Class XII CBSE AI Capstone Project"

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    HISTORY_PER_PAGE = 20