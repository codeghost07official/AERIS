"""Machine-learning modules for AERIS.

This package contains the real AI/ML components used by AERIS:
- Telemetry anomaly detection
- Image feature analysis
"""

from .telemetry_model import analyze_telemetry
from .image_model import analyze_image

__all__ = [
    "analyze_telemetry",
    "analyze_image",
]