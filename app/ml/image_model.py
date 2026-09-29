"""Computer-vision feature analysis for AERIS."""

from __future__ import annotations

import os
from typing import Any

import cv2
import numpy as np
from PIL import Image


def _safe_float(value: Any) -> float:
    """Convert a numerical value into a JSON-compatible float."""
    value = float(value)

    if not np.isfinite(value):
        return 0.0

    return value


def _calculate_edge_density(gray_image: np.ndarray) -> float:
    """Calculate the percentage of pixels detected as edges."""

    edges = cv2.Canny(
        gray_image,
        threshold1=100,
        threshold2=200,
    )

    total_pixels = edges.size

    if total_pixels == 0:
        return 0.0

    edge_pixels = np.count_nonzero(edges)

    return _safe_float(
        edge_pixels / total_pixels
    )


def analyze_image(file_path: str) -> dict[str, Any]:
    """Analyze measurable visual characteristics of an image.

    The analysis intentionally focuses on measurable image properties rather
    than claiming that the system can definitively diagnose spacecraft damage.
    """

    if not file_path:
        raise ValueError("No image file was provided.")

    if not os.path.isfile(file_path):
        raise ValueError("The image file could not be found.")

    try:
        with Image.open(file_path) as image:
            image.verify()
    except Exception as exc:
        raise ValueError(
            "The uploaded file is not a valid readable image."
        ) from exc

    try:
        image = Image.open(file_path).convert("RGB")
        rgb_array = np.asarray(image)

        if rgb_array.size == 0:
            raise ValueError("The uploaded image contains no pixel data.")

        height, width = rgb_array.shape[:2]
        channels = 3

        # Convert RGB data to grayscale for brightness, contrast,
        # sharpness, and edge calculations.
        gray_image = cv2.cvtColor(
            rgb_array,
            cv2.COLOR_RGB2GRAY,
        )

        brightness = float(np.mean(gray_image))
        contrast = float(np.std(gray_image))

        # Variance of the Laplacian is a common measurable sharpness
        # indicator. Higher values generally indicate stronger fine detail.
        laplacian = cv2.Laplacian(
            gray_image,
            cv2.CV_64F,
        )

        sharpness = float(laplacian.var())

        edge_density = _calculate_edge_density(
            gray_image
        )

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "The image could not be processed."
        ) from exc

    explanation = (
        "Brightness represents the average pixel intensity of the image. "
        "Contrast represents the variation in pixel intensity. "
        "Sharpness is estimated using the variance of the Laplacian, "
        "which measures fine image detail. Edge density estimates the "
        "proportion of the image containing detected edges. These are "
        "measurable visual indicators and should not be interpreted as "
        "definitive evidence of spacecraft damage or equipment failure."
    )

    return {
        "width": int(width),
        "height": int(height),
        "channels": int(channels),
        "brightness": round(_safe_float(brightness), 4),
        "contrast": round(_safe_float(contrast), 4),
        "sharpness": round(_safe_float(sharpness), 4),
        "edge_density": round(_safe_float(edge_density), 6),
        "feature_count": 4,
        "feature_names": [
            "brightness",
            "contrast",
            "sharpness",
            "edge_density",
        ],
        "explanation": explanation,
    }