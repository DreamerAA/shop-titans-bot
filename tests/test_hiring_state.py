import unittest
from unittest.mock import Mock, patch

import numpy as np

from bot.hiring.assets import TemplateSpec
from bot.hiring.state import HiringStateDetector
from bot.hiring.vision import TemplateMatch


class HiringStateDetectorTests(unittest.TestCase):
    def test_reuses_successful_scale_before_full_range(self):
        spec = TemplateSpec("control", "unused.png", 0.8, (0.5, 1.0, 1.5))
        match = TemplateMatch("control", 0.9, 1.5, (10, 20), (30, 40))
        matcher = Mock()
        matcher.find.side_effect = (None, match, match)
        detector = HiringStateDetector(matcher=matcher)
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        with (
            patch("bot.hiring.state.get_template", return_value=spec),
            patch(
                "bot.hiring.state.load_template",
                return_value=image,
            ),
        ):
            self.assertEqual(detector.find_template(image, "control"), match)
            self.assertEqual(detector.find_template(image, "control"), match)

        self.assertEqual(matcher.find.call_args_list[0].kwargs["scales"], (1.0,))
        self.assertEqual(matcher.find.call_args_list[1].kwargs["scales"], spec.scales)
        self.assertEqual(matcher.find.call_args_list[2].kwargs["scales"], (1.5, 1.0))


if __name__ == "__main__":
    unittest.main()
