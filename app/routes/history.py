"""Analysis history routes for AERIS."""

import os

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.database import (
    delete_analysis_record,
    get_analysis_by_id,
    get_analysis_history,
)


history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@login_required
def history():
    """Display the authenticated user's analysis history."""

    page = current_app.config.get("HISTORY_PAGE_SIZE", 10)

    try:
        analyses = get_analysis_history(
            user_id=current_user.id,
            limit=page,
        )
    except Exception:
        current_app.logger.exception("Unable to load analysis history.")
        analyses = []
        flash(
            "Analysis history could not be loaded.",
            "error",
        )

    return render_template(
        "history.html",
        analyses=analyses,
        history=analyses,
    )


@history_bp.route("/history/<analysis_id>", methods=["GET"])
@login_required
def detail(analysis_id):
    """Display the detailed report for one user's analysis."""

    if not analysis_id:
        flash("Invalid analysis ID.", "error")
        return redirect(url_for("history.history"))

    try:
        analysis = get_analysis_by_id(
            analysis_id=analysis_id,
            user_id=current_user.id,
        )
    except Exception:
        current_app.logger.exception(
            "Unable to retrieve analysis %s.",
            analysis_id,
        )
        flash(
            "The requested analysis could not be loaded.",
            "error",
        )
        return redirect(url_for("history.history"))

    if not analysis:
        flash(
            "Analysis not found or you do not have access to it.",
            "error",
        )
        return redirect(url_for("history.history"))

    report = dict(analysis)

    result_data = report.get("result_data")

    if isinstance(result_data, dict):
        report.update(result_data)

    report["id"] = report.get("id", analysis_id)
    report["analysis_id"] = report.get("analysis_id", analysis_id)

    return render_template(
        "report.html",
        analysis=report,
        report=report,
    )


@history_bp.route("/history/<analysis_id>/delete", methods=["POST"])
@login_required
def delete(analysis_id):
    """Delete an analysis owned by the authenticated user."""

    if not analysis_id:
        flash("Invalid analysis ID.", "error")
        return redirect(url_for("history.history"))

    try:
        analysis = get_analysis_by_id(
            analysis_id=analysis_id,
            user_id=current_user.id,
        )

        if not analysis:
            flash(
                "Analysis not found or you do not have access to it.",
                "error",
            )
            return redirect(url_for("history.history"))

        deleted = delete_analysis_record(
            analysis_id=analysis_id,
            user_id=current_user.id,
        )

        if deleted:
            file_path = analysis.get("file_path")

            if file_path and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    current_app.logger.warning(
                        "Could not remove analysis file: %s",
                        file_path,
                    )

            flash("Analysis deleted successfully.", "success")
        else:
            flash(
                "The analysis could not be deleted.",
                "error",
            )

    except Exception:
        current_app.logger.exception(
            "Unable to delete analysis %s.",
            analysis_id,
        )
        flash(
            "An error occurred while deleting the analysis.",
            "error",
        )

    return redirect(url_for("history.history"))