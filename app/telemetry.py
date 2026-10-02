
import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest


def create_plain_language_explanation(
    observations,
    anomaly_count,
    anomaly_percentage,
):
    if anomaly_count:
        line_word = "line" if anomaly_count == 1 else "lines"
        finding = (
            f"AERIS found {anomaly_count} unusual {line_word} "
            f"({anomaly_percentage:g}%). These differences could be a warning "
            "that some equipment needs a closer look, helping the team decide "
            "what to inspect. They are not proof that anything is broken."
        )
    else:
        finding = (
            f"AERIS found 0 unusual lines ({anomaly_percentage:g}%). No numbers "
            "stood out, but this cannot prove that all equipment is working "
            "perfectly."
        )

    return (
        f"This file has {observations} lines of numbers recorded from "
        f"spacecraft equipment. AERIS checked whether any numbers looked "
        f"different from the others. {finding}"
    )


def analyze_telemetry(file_path):
    try:
        df = pd.read_csv(file_path)

        if df.empty:
            raise ValueError("The uploaded CSV contains no observations.")

        if len(df.columns) < 1:
            raise ValueError("No columns were found in the CSV.")

        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty:
            raise ValueError(
                "The CSV must contain at least one numerical column."
            )

        numeric_df = numeric_df.replace(
            [np.inf, -np.inf],
            np.nan
        )

        numeric_df = numeric_df.dropna(axis=1, how="all")

        if numeric_df.empty:
            raise ValueError(
                "No usable numerical measurements were found."
            )

        numeric_df = numeric_df.fillna(
            numeric_df.median()
        )

        numeric_df = numeric_df.loc[
            :, numeric_df.nunique() > 1
        ]

        if numeric_df.empty:
            raise ValueError(
                "All numerical measurements are constant."
            )

        observations = len(numeric_df)

        if observations < 5:
            raise ValueError(
                "At least 5 usable observations are required."
            )

        model = IsolationForest(
            n_estimators=100,
            contamination="auto",
            random_state=42
        )

        predictions = model.fit_predict(numeric_df)

        anomaly_mask = predictions == -1

        anomaly_count = int(np.sum(anomaly_mask))
        anomaly_percentage = round(
            (anomaly_count / observations) * 100,
            2
        )

        anomaly_indices = np.flatnonzero(anomaly_mask).tolist()
        anomaly_rows = [
            int(numeric_df.index[i]) for i in anomaly_indices
        ]

        column_stats = {}

        for column in numeric_df.columns:
            values = numeric_df[column]

            column_stats[column] = {
                "mean": round(float(values.mean()), 3),
                "min": round(float(values.min()), 3),
                "max": round(float(values.max()), 3),
                "std": round(float(values.std()), 3)
            }

        if anomaly_count == 0:
            finding = (
                "No unusual observations were detected by the model."
            )
        else:
            finding = (
                f"{anomaly_count} unusual observations were detected "
                f"across the analyzed measurements."
            )

        if anomaly_percentage >= 10:
            interpretation = (
                "The dataset contains a noticeable proportion of "
                "unusual readings. Further investigation is recommended."
            )
        elif anomaly_count > 0:
            interpretation = (
                "Some readings differ from the dominant data patterns. "
                "Review the affected measurements."
            )
        else:
            interpretation = (
                "The analyzed readings show no detected anomalies. "
                "This does not guarantee equipment health."
            )

        summary = (
            f"Analyzed {observations} observations across "
            f"{len(numeric_df.columns)} numerical parameters. "
            f"Detected {anomaly_count} anomalies "
            f"({anomaly_percentage}%). {finding}"
        )
        plain_language_explanation = create_plain_language_explanation(
            observations,
            anomaly_count,
            anomaly_percentage,
        )

        return {
            "success": True,
            "observations": observations,
            "columns": numeric_df.columns.tolist(),
            "anomaly_count": anomaly_count,
            "anomaly_percentage": anomaly_percentage,
            "anomaly_rows": anomaly_rows,
            "finding": finding,
            "interpretation": interpretation,
            "summary": summary,
            "plain_language_explanation": plain_language_explanation,
            "column_stats": column_stats,
            "chart_data": {
                "labels": list(range(observations)),
                "anomalies": anomaly_mask.astype(int).tolist()
            }
        }

    except Exception as error:
        raise ValueError(
            f"Telemetry analysis failed: {str(error)}"
        ) from error