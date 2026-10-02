
import os
import uuid

from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)
from werkzeug.utils import secure_filename

from app.database import delete_analysis, save_analysis, get_user_history

from app.telemetry import analyze_telemetry
from app.image_analysis import analyze_image

main = Blueprint("main", __name__)

ALLOWED_TELEMETRY = {"csv"}
ALLOWED_IMAGES = {"jpg", "jpeg", "png"}

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))

        return function(*args, **kwargs)

    return wrapper


def save_uploaded_file(file, allowed_extensions):
    if not file or not file.filename:
        raise ValueError("Please select a file.")

    filename = secure_filename(file.filename)

    if "." not in filename:
        raise ValueError("Invalid filename.")

    extension = filename.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise ValueError("Unsupported file format.")

    unique_name = f"{uuid.uuid4().hex}_{filename}"

    upload_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        unique_name
    )

    file.save(upload_path)

    return upload_path, filename


@main.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    return redirect(url_for("auth.login"))


@main.route("/dashboard")
@login_required
def dashboard():
    history = get_user_history(session["user_id"], limit=5)

    return render_template(
        "dashboard.html",
        history=history
    )


@main.route("/analyze/telemetry", methods=["POST"])
@login_required
def telemetry_upload():
    uploaded_path = None

    try:
        file = request.files.get("telemetry_file")

        uploaded_path, original_filename = save_uploaded_file(
            file,
            ALLOWED_TELEMETRY
        )

        result = analyze_telemetry(uploaded_path)

        save_analysis(
            user_id=session["user_id"],
            filename=original_filename,
            analysis_type="Telemetry",
            observations=result["observations"],
            anomaly_count=result["anomaly_count"],
            anomaly_percentage=result["anomaly_percentage"],
            summary=result["summary"],
            plain_language_explanation=result["plain_language_explanation"],
        )

        return render_template(
            "results.html",
            result=result,
            filename=original_filename,
            analysis_type="Telemetry"
        )

    except Exception as error:
        current_app.logger.exception("Telemetry analysis failed")
        flash(str(error), "error")
        return redirect(url_for("main.dashboard"))

    finally:
        if uploaded_path and os.path.exists(uploaded_path):
            os.remove(uploaded_path)


@main.route("/analyze/image", methods=["POST"])
@login_required
def image_upload():
    uploaded_path = None

    try:
        file = request.files.get("image_file")

        uploaded_path, original_filename = save_uploaded_file(
            file,
            ALLOWED_IMAGES
        )

        result = analyze_image(uploaded_path)

        save_analysis(
            user_id=session["user_id"],
            filename=original_filename,
            analysis_type="Image",
            observations=1,
            anomaly_count=0,
            anomaly_percentage=0,
            summary=result["summary"],
            plain_language_explanation=result["plain_language_explanation"],
        )

        return render_template(
            "results.html",
            result=result,
            filename=original_filename,
            analysis_type="Image"
        )

    except Exception as error:
        current_app.logger.exception("Image analysis failed")
        flash(str(error), "error")
        return redirect(url_for("main.dashboard"))

    finally:
        if uploaded_path and os.path.exists(uploaded_path):
            os.remove(uploaded_path)


@main.route("/history")
@login_required
def history():
    records = get_user_history(
        session["user_id"],
        limit=50
    )

    return render_template(
        "history.html",
        records=records
    )


@main.route("/history/<analysis_id>/delete", methods=["POST"])
@login_required
def delete_history_item(analysis_id):
    try:
        deleted = delete_analysis(session["user_id"], analysis_id)
    except (TypeError, ValueError):
        deleted = False

    if deleted:
        flash("Analysis deleted.", "success")
    else:
        flash("Analysis record was not found.", "error")

    return redirect(url_for("main.history"))