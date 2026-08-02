import unittest

import numpy as np

from bot.hiring.vision import MultiScaleMatcher, NormalizedROI


class MultiScaleMatcherTests(unittest.TestCase):
    def test_finds_template_inside_roi_and_returns_global_coordinates(self):
        random = np.random.default_rng(42)
        template = random.integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        image = np.zeros((100, 160, 3), dtype=np.uint8)
        image[60:72, 100:116] = template

        match = MultiScaleMatcher().find(
            image=image,
            template=template,
            template_id="test",
            scales=(0.8, 1.0, 1.2),
            threshold=0.9,
            roi=NormalizedROI(0.5, 0.5, 1.0, 1.0),
        )

        self.assertIsNotNone(match)
        self.assertEqual((100, 60), match.top_left)
        self.assertEqual((108, 66), match.center)
        self.assertAlmostEqual(1.0, match.score, places=5)

    def test_returns_none_below_threshold(self):
        random = np.random.default_rng(7)
        image = random.integers(0, 256, size=(80, 100, 3), dtype=np.uint8)
        template = random.integers(0, 256, size=(10, 12, 3), dtype=np.uint8)

        match = MultiScaleMatcher().find(
            image=image,
            template=template,
            template_id="missing",
            scales=(1.0,),
            threshold=0.99,
        )

        self.assertIsNone(match)


class NormalizedROITests(unittest.TestCase):
    def test_converts_fractional_coordinates_to_pixels(self):
        image = np.zeros((100, 200, 3), dtype=np.uint8)

        self.assertEqual((20, 20, 180, 80), NormalizedROI(0.1, 0.2, 0.9, 0.8).pixels(image))


if __name__ == "__main__":
    unittest.main()
