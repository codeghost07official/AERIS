"""Telemetry upload and anomaly-analysis routes for AERIS."""

import json
import os
import uuid

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.database import create_analysis_record


telemetry_bp = Blueprint("telemetry", __name__)


def _allowed_file(filename):
    """Return True when the uploaded filename has an allowed extension."""
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in current_app.config.get(
        "ALLOWED_TELEMETRY_EXTENSIONS",
        {"csv"},
    )


def _save_upload(file):
    """Save a telemetry upload using a UUID-based storage filename."""
    original_filename = secure_filename(file.filename)

    if not original_filename:
        raise ValueError("The uploaded file has an invalid filename.")

    if not _allowed_file(original_filename):
        raise ValueError("Only CSV telemetry files are allowed.")

    extension = original_filename.rsplit(".", 1)[1].lower()
    storage_filename = f"{uuid.uuid4().hex}.{extension}"

    upload_directory = current_app.config["TELEMETRY_UPLOAD_FOLDER"]
    os.makedirs(upload_directory, exist_ok=True)

    file_path = os.path.join(upload_directory, storage_filename)
    file.save(file_path)

    return original_filename, storage_filename, file_path


@telemetry_bp.route("/telemetry", methods=["GET"])
@login_required
def telemetry():
    """Display the telemetry analysis page."""
    return render_template("telemetry.html")


@telemetry_bp.route("/telemetry/analyze", methods=["POST"])
@login_required
def analyze():
    """Upload a telemetry file, analyze it, and store the result."""

    # The HTML form uses name="file".
    uploaded_file = request.files.get("file")

    if uploaded_file is None or not uploaded_file.filename:
        flash("Please select a telemetry CSV file.", "error")
        return redirect(url_for("telemetry.telemetry"))

    method = request.form.get(
        "method",
        "isolation_forest",
    ).strip().lower()

    allowed_methods = {"isolation_forest", "pca"}

    if method not in allowed_methods:
        flash("Invalid analysis method selected.", "error")
        return redirect(url_for("telemetry.telemetry"))

    file_path = None

    try:
        original_filename, storage_filename, file_path = _save_upload(
            uploaded_file
        )

        from app.ml.telemetry_model import analyze_telemetry

        result = analyze_telemetry(
            file_path=file_path,
            method=method,
        )

        result_data = dict(result)

        # Convert data into JSON-compatible Python objects before storage.
        result_json = json.loads(
            json.dumps(result_data, default=str)
        )

        analysis_record = create_analysis_record(
            user_id=current_user.id,
            analysis_type="telemetry",
            filename=original_filename,
            status="completed",
            total_observations=result_json.get(
                "total_observations",
                0,
            ),
            anomalies_detected=result_json.get(
                "anomalies_detected",
                0,
            ),
            anomaly_rate=result_json.get(
                "anomaly_rate",
                0,
            ),
            features_used=result_json.get(
                "features_used",
                0,
            ),
            method=result_json.get(
                "method",
                method,
            ),
            method_description=result_json.get(
                "method_description",
                "",
            ),
            file_path=file_path,
            result_data=result_json,
        )

        result_json["analysis_id"] = (
            analysis_record.get("id")
            if isinstance(analysis_record, dict)
            else analysis_record
        )

        result_json["filename"] = original_filename
        result_json["status"] = "completed"

        return render_template(
            "telemetry.html",
            result=result_json,
            analysis=result_json,
        )

    except ValueError as exc:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        flash(str(exc), "error")
        return redirect(url_for("telemetry.telemetry"))

    except Exception:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        current_app.logger.exception(
            "Telemetry analysis failed."
        )

        flash(
            "Telemetry analysis could not be completed. "
            "Please check the CSV format and try again.",
            "error",
        )

        return redirect(url_for("telemetry.telemetry"))