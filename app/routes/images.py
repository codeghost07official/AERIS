"""Image upload and computer-vision analysis routes for AERIS."""

import json
import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.database import create_analysis_record
from app.ml.image_model import analyze_image


images_bp = Blueprint("images", __name__)


def _allowed_file(filename):
    """Return True when the uploaded filename has an allowed image extension."""
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    allowed_extensions = current_app.config.get(
        "ALLOWED_IMAGE_EXTENSIONS",
        {"jpg", "jpeg", "png", "bmp", "tif", "tiff", "webp"},
    )

    return extension in allowed_extensions


def _save_upload(file):
    """Save an image using a secure UUID-based storage filename."""
    original_filename = secure_filename(file.filename)

    if not original_filename:
        raise ValueError("The uploaded file has an invalid filename.")

    if not _allowed_file(original_filename):
        raise ValueError(
            "Unsupported image format. Please upload JPG, JPEG, PNG, BMP, "
            "TIF, TIFF, or WEBP."
        )

    extension = original_filename.rsplit(".", 1)[1].lower()
    storage_filename = f"{uuid.uuid4().hex}.{extension}"

    upload_directory = current_app.config["IMAGE_UPLOAD_FOLDER"]
    os.makedirs(upload_directory, exist_ok=True)

    file_path = os.path.join(upload_directory, storage_filename)
    file.save(file_path)

    return original_filename, storage_filename, file_path


@images_bp.route("/images", methods=["GET"])
@login_required
def images():
    """Display the image-analysis page."""
    return render_template("images.html")


@images_bp.route("/images/analyze", methods=["POST"])
@login_required
def analyze():
    """Upload an image, calculate measurable visual features, and store results."""

    uploaded_file = request.files.get("image_file")

    if uploaded_file is None or not uploaded_file.filename:
        flash("Please select an image file.", "error")
        return redirect(url_for("images.images"))

    file_path = None

    try:
        original_filename, storage_filename, file_path = _save_upload(uploaded_file)

        result = analyze_image(file_path)

        result_data = json.loads(
            json.dumps(dict(result), default=str)
        )

        result_data["filename"] = original_filename
        result_data["status"] = "completed"

        image_url = url_for(
            "static",
            filename=f"uploads/images/{storage_filename}",
        )

        result_data["image_url"] = image_url

        analysis_record = create_analysis_record(
            user_id=current_user.id,
            analysis_type="image",
            filename=original_filename,
            status="completed",
            total_observations=1,
            anomalies_detected=0,
            anomaly_rate=0,
            features_used=result_data.get("feature_count", 0),
            method="image_feature_analysis",
            method_description=(
                "Computer-vision feature analysis using measurable image "
                "properties including brightness, contrast, sharpness, "
                "and edge density."
            ),
            file_path=file_path,
            result_data=result_data,
        )

        result_data["analysis_id"] = (
            analysis_record.get("id")
            if isinstance(analysis_record, dict)
            else analysis_record
        )

        return render_template(
            "images.html",
            result=result_data,
            analysis=result_data,
        )

    except ValueError as exc:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        flash(str(exc), "error")
        return redirect(url_for("images.images"))

    except Exception:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        current_app.logger.exception("Image analysis failed.")

        flash(
            "Image analysis could not be completed. "
            "Please check the image and try again.",
            "error",
        )
        return redirect(url_for("images.images"))