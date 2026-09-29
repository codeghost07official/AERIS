"""Flask route package for AERIS.

This package contains the application's route blueprints for:
- Authentication
- Main dashboard
- Telemetry analysis
- Image analysis
- Analysis history
"""

from .auth import auth_bp
from .main import main_bp
from .telemetry import telemetry_bp
from .images import images_bp
from .history import history_bp

__all__ = [
    "auth_bp",
    "main_bp",
    "telemetry_bp",
    "images_bp",
    "history_bp",
]