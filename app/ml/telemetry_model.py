"""Telemetry anomaly detection for AERIS.

This module uses real machine-learning techniques to identify unusual
telemetry observations. Isolation Forest is the primary method because
its results are relatively easy to explain in a Class XII project.
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def _json_safe(value: Any) -> Any:
    """Convert NumPy/Pandas values into JSON-compatible Python values."""
    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if pd.isna(value):
        return None

    return value


def _clean_numeric_data(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Extract and clean usable numerical telemetry columns."""

    numeric_dataframe = dataframe.select_dtypes(include=[np.number]).copy()

    if numeric_dataframe.empty:
        raise ValueError(
            "The CSV does not contain any numerical telemetry columns."
        )

    # Replace infinite values with missing values.
    numeric_dataframe = numeric_dataframe.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # Remove columns containing no usable values.
    numeric_dataframe = numeric_dataframe.dropna(
        axis=1,
        how="all",
    )

    if numeric_dataframe.empty:
        raise ValueError(
            "The telemetry file does not contain usable numerical data."
        )

    # Fill remaining missing values with each column's median.
    for column in numeric_dataframe.columns:
        median = numeric_dataframe[column].median()

        if pd.isna(median):
            numeric_dataframe[column] = numeric_dataframe[column].fillna(0)
        else:
            numeric_dataframe[column] = numeric_dataframe[column].fillna(median)

    numeric_dataframe = numeric_dataframe.replace(
        [np.inf, -np.inf],
        np.nan,
    ).fillna(0)

    return numeric_dataframe, list(numeric_dataframe.columns)


def _build_chart_data(
    dataframe: pd.DataFrame,
    anomaly_mask: np.ndarray,
) -> list[dict[str, Any]]:
    """Create compact chart data for the frontend."""

    numeric_columns = list(
        dataframe.select_dtypes(include=[np.number]).columns
    )

    if not numeric_columns:
        return []

    # Use the first numerical feature for a simple, explainable chart.
    feature = numeric_columns[0]

    chart_data = []

    for index, value in enumerate(dataframe[feature].tolist()):
        chart_data.append(
            {
                "index": index,
                "value": _json_safe(value),
                "anomaly": bool(anomaly_mask[index]),
            }
        )

    return chart_data


def _build_anomaly_rows(
    original_dataframe: pd.DataFrame,
    anomaly_mask: np.ndarray,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return the original observations classified as anomalous."""

    anomaly_indices = np.where(anomaly_mask)[0]

    columns = list(original_dataframe.columns)
    rows = []

    for index in anomaly_indices:
        row = {}

        for column in columns:
            row[column] = _json_safe(
                original_dataframe.iloc[index][column]
            )

        row["_row_number"] = int(index + 1)
        rows.append(row)

    return rows, columns


def _isolation_forest(
    values: np.ndarray,
    contamination: float,
    random_state: int,
) -> np.ndarray:
    """Run Isolation Forest and return a Boolean anomaly mask."""

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
        n_jobs=-1,
    )

    predictions = model.fit_predict(values)

    # Isolation Forest returns -1 for anomalies and 1 for normal points.
    return predictions == -1


def _pca_detection(
    values: np.ndarray,
    contamination: float,
) -> tuple[np.ndarray, PCA]:
    """Use PCA reconstruction error as an alternative anomaly detector."""

    n_samples, n_features = values.shape

    if n_features < 2:
        raise ValueError(
            "PCA analysis requires at least two numerical telemetry features."
        )

    components = min(
        2,
        n_features,
        n_samples,
    )

    pca = PCA(n_components=components)
    transformed = pca.fit_transform(values)
    reconstructed = pca.inverse_transform(transformed)

    reconstruction_error = np.mean(
        np.square(values - reconstructed),
        axis=1,
    )

    threshold = np.quantile(
        reconstruction_error,
        1.0 - contamination,
    )

    anomaly_mask = reconstruction_error >= threshold

    return anomaly_mask, pca


def analyze_telemetry(
    file_path: str,
    method: str = "isolation_forest",
) -> dict[str, Any]:
    """Analyze a telemetry CSV and identify unusual observations.

    Parameters
    ----------
    file_path:
        Path to the uploaded CSV file.

    method:
        Either ``isolation_forest`` or ``pca``.

    Returns
    -------
    dict
        JSON-compatible analysis results used by the Flask templates.
    """

    if not file_path:
        raise ValueError("No telemetry file was provided.")

    if not os.path.isfile(file_path):
        raise ValueError("The telemetry file could not be found.")

    method = method.lower().strip()

    if method not in {"isolation_forest", "pca"}:
        raise ValueError(
            "Unsupported telemetry analysis method."
        )

    try:
        dataframe = pd.read_csv(file_path)
    except Exception as exc:
        raise ValueError(
            "The uploaded file could not be read as a valid CSV."
        ) from exc

    if dataframe.empty:
        raise ValueError("The telemetry CSV is empty.")

    minimum_rows = int(
        _get_config_value(
            "MIN_TELEMETRY_ROWS",
            10,
        )
    )

    if len(dataframe) < minimum_rows:
        raise ValueError(
            f"At least {minimum_rows} telemetry observations are required."
        )

    original_dataframe = dataframe.copy()

    numeric_dataframe, feature_names = _clean_numeric_data(
        dataframe
    )

    if len(numeric_dataframe) < minimum_rows:
        raise ValueError(
            f"At least {minimum_rows} valid telemetry observations are required."
        )

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(
        numeric_dataframe.to_numpy(dtype=float)
    )

    contamination = float(
        _get_config_value(
            "TELEMETRY_CONTAMINATION",
            0.05,
        )
    )

    contamination = min(
        max(contamination, 0.001),
        0.49,
    )

    random_state = int(
        _get_config_value(
            "TELEMETRY_RANDOM_STATE",
            42,
        )
    )

    if method == "isolation_forest":
        anomaly_mask = _isolation_forest(
            scaled_values,
            contamination,
            random_state,
        )

        method_name = "Isolation Forest"

        method_description = (
            "Isolation Forest identifies observations that are easier to "
            "separate from the majority of the dataset. Such observations "
            "are flagged as potential anomalies. An anomaly does not "
            "automatically mean equipment failure; it indicates a telemetry "
            "pattern that deserves further investigation."
        )

    else:
        anomaly_mask, _ = _pca_detection(
            scaled_values,
            contamination,
        )

        method_name = "PCA Reconstruction Analysis"

        method_description = (
            "PCA reduces the telemetry data to its main patterns and "
            "measures how well each observation can be reconstructed. "
            "Observations with unusually large reconstruction errors are "
            "flagged as potential anomalies. This is an analytical "
            "indicator, not proof of equipment failure."
        )

    total_observations = len(numeric_dataframe)
    anomalies_detected = int(np.sum(anomaly_mask))

    anomaly_rate = (
        (anomalies_detected / total_observations) * 100
        if total_observations
        else 0.0
    )

    chart_data = _build_chart_data(
        numeric_dataframe,
        anomaly_mask,
    )

    anomaly_rows, anomaly_columns = _build_anomaly_rows(
        original_dataframe,
        anomaly_mask,
    )

    return {
        "total_observations": int(total_observations),
        "anomalies_detected": anomalies_detected,
        "anomaly_rate": round(anomaly_rate, 2),
        "features_used": int(len(feature_names)),
        "feature_count": int(len(feature_names)),
        "feature_names": feature_names,
        "method": method_name,
        "method_key": method,
        "method_description": method_description,
        "chart_data": chart_data,
        "anomaly_rows": anomaly_rows,
        "anomaly_columns": anomaly_columns,
    }


def _get_config_value(name: str, default: Any) -> Any:
    """Read a Flask configuration value when an application context exists."""

    try:
        from flask import current_app

        return current_app.config.get(name, default)
    except RuntimeError:
        return default