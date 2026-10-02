import io
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

from app import create_app
import app.routes as routes


class ReportExplanationTests(unittest.TestCase):
    def setUp(self):
        with patch("app.database.init_db"):
            app = create_app()

        app.testing = True
        self.client = app.test_client()
        self.user_id = str(uuid.uuid4())
        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["user_name"] = "Test User"

    def test_csv_report_shows_and_saves_explanation(self):
        csv_data = (
            b"temperature,voltage\n"
            b"10,3.1\n11,3.2\n12,3.3\n13,3.4\n"
            b"14,3.5\n15,3.6\n16,3.7\n17,3.8\n"
        )

        with patch.object(routes, "save_analysis") as save_analysis:
            response = self.client.post(
                "/analyze/telemetry",
                data={
                    "telemetry_file": (io.BytesIO(csv_data), "sample.csv")
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"In everyday terms", response.data)
        self.assertIn(
            b"This file has 8 lines of numbers recorded from spacecraft equipment.",
            response.data,
        )
        saved_result = save_analysis.call_args.kwargs
        saved_explanation = saved_result["plain_language_explanation"]
        self.assertIn("8 lines", saved_explanation)
        self.assertIn(
            f"{saved_result['anomaly_count']} unusual "
            f"{'line' if saved_result['anomaly_count'] == 1 else 'lines'} "
            f"({saved_result['anomaly_percentage']:g}%)",
            saved_explanation,
        )

    def test_history_displays_saved_explanation(self):
        explanation = (
            "This CSV contains 8 rows of readings for temperature and voltage. "
            "No rows clearly stood out from the others."
        )
        records = [{
            "id": uuid.uuid4(),
            "filename": "sample.csv",
            "analysis_type": "Telemetry",
            "observations": 8,
            "anomaly_count": 0,
            "anomaly_percentage": 0,
            "created_at": datetime(2026, 10, 2),
            "summary": "Analysis summary",
            "plain_language_explanation": explanation,
        }]

        with patch.object(routes, "get_user_history", return_value=records):
            response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"In everyday terms:", response.data)
        self.assertIn(explanation.encode(), response.data)
        self.assertIn(b"Delete", response.data)
        self.assertIn(b"return confirm(", response.data)

    def test_image_report_shows_and_saves_explanation(self):
        result = {
            "width": 20,
            "height": 10,
            "brightness": 40,
            "contrast": 20,
            "sharpness": 10,
            "edge_density": 2,
            "brightness_note": "The image is relatively dark.",
            "contrast_note": "Low contrast between image regions.",
            "sharpness_note": "The image may contain limited fine detail.",
            "edge_note": "Relatively few prominent edges were detected.",
            "interpretation": "Image characteristics only.",
            "summary": "Analyzed a 20 x 10 image.",
            "plain_language_explanation": (
                "Pictures help people look over spacecraft equipment. "
                "The picture is dark, so some equipment details may be hard "
                "to see. These clues can help someone decide on a closer "
                "look, but they do not prove damage."
            ),
        }

        with patch.object(routes, "analyze_image", return_value=result):
            with patch.object(routes, "save_analysis") as save_analysis:
                response = self.client.post(
                    "/analyze/image",
                    data={"image_file": (io.BytesIO(b"image"), "spacecraft.jpg")},
                    content_type="multipart/form-data",
                )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"In everyday terms", response.data)
        self.assertIn(b"spacecraft equipment", response.data)
        self.assertEqual(
            save_analysis.call_args.kwargs["plain_language_explanation"],
            result["plain_language_explanation"],
        )

    def test_delete_post_targets_only_the_signed_in_user_record(self):
        analysis_id = str(uuid.uuid4())

        with patch.object(routes, "delete_analysis", return_value=True) as delete:
            with patch.object(routes, "get_user_history", return_value=[]):
                response = self.client.post(
                    f"/history/{analysis_id}/delete",
                    follow_redirects=True,
                )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No Analysis History", response.data)
        delete.assert_called_once_with(self.user_id, analysis_id)

    def test_delete_requires_login(self):
        with self.client.session_transaction() as session:
            session.clear()

        with patch.object(routes, "delete_analysis") as delete:
            response = self.client.post(
                f"/history/{uuid.uuid4()}/delete"
            )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))
        delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
