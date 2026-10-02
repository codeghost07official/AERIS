import unittest

from app.image_analysis import create_image_explanation


class ImageExplanationTests(unittest.TestCase):
    def test_low_visibility_suggests_a_clearer_view_for_inspection(self):
        explanation = create_image_explanation(
            brightness=40,
            contrast=20,
            sharpness=10,
            edge_density=2,
        )

        self.assertIn("possible spacecraft equipment problems", explanation)
        self.assertIn("equipment", explanation)
        self.assertIn("picture is dark", explanation)
        self.assertIn("did not identify a specific equipment issue", explanation)
        self.assertIn("some areas blend together", explanation)
        self.assertIn("small details are hard to see", explanation)
        self.assertIn("clearer picture or a closer human review", explanation)
        self.assertIn("cannot tell whether the equipment is normal or faulty", explanation)
        self.assertIn("or identify damage", explanation)
        self.assertIn("person should inspect anything that looks unusual", explanation)

    def test_clearer_image_does_not_claim_an_equipment_warning(self):
        explanation = create_image_explanation(
            brightness=120,
            contrast=45,
            sharpness=80,
            edge_density=12,
        )

        self.assertIn("easier to review", explanation)
        self.assertIn("did not find a clear warning sign", explanation)
        self.assertIn("Several outlines are visible for a person to look over", explanation)
        self.assertNotIn("crack", explanation.lower())
        self.assertNotIn("failed", explanation.lower())


if __name__ == "__main__":
    unittest.main()
