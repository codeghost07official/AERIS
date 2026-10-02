import unittest

from app.telemetry import create_plain_language_explanation


class PlainLanguageExplanationTests(unittest.TestCase):
    def test_explains_detected_lines_with_actual_percentage(self):
        explanation = create_plain_language_explanation(20, 3, 15.0)

        self.assertIn(
            "20 lines of numbers recorded from spacecraft equipment",
            explanation,
        )
        self.assertIn("checked whether any numbers looked different", explanation)
        self.assertIn("3 unusual lines (15%)", explanation)
        self.assertIn("equipment needs a closer look", explanation)
        self.assertIn("not proof that anything is broken", explanation)
        self.assertNotIn("telemetry", explanation.lower())
        self.assertNotIn("anomaly", explanation.lower())

    def test_singular_result_uses_singular_wording(self):
        explanation = create_plain_language_explanation(10, 1, 10.0)

        self.assertIn("1 unusual line (10%)", explanation)

    def test_explains_when_no_lines_stood_out(self):
        explanation = create_plain_language_explanation(8, 0, 0.0)

        self.assertIn("8 lines of numbers recorded from spacecraft equipment", explanation)
        self.assertIn("0 unusual lines (0%)", explanation)
        self.assertIn(
            "cannot prove that all equipment is working perfectly",
            explanation,
        )


if __name__ == "__main__":
    unittest.main()