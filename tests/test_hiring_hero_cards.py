import unittest
from unittest.mock import Mock, patch

import numpy as np

from bot.hiring.hero_cards import HeroCardFinder
from bot.hiring.ocr import OCRTextMatch
from bot.hiring.vision import TemplateMatch


class HeroCardFinderTests(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((1000, 1920, 3), dtype=np.uint8)
        self.name = OCRTextMatch("ЛЭРИС", 0.99, (960, 820))
        self.level = TemplateMatch("level_10", 0.95, 1.0, (875, 725), (32, 32))
        self.alert = TemplateMatch("new_hero_alert", 0.96, 1.0, (990, 715), (40, 41))
        self.name_reader = Mock()
        self.name_reader.find.return_value = self.name
        self.name_reader.find_in_bounds.return_value = self.name
        self.finder = HeroCardFinder(name_reader=self.name_reader)

    def test_resume_accepts_exact_name_and_level_without_cleared_alert(self):
        with patch.object(self.finder, "_find_template", side_effect=(None, self.level)):
            match = self.finder.find(self.image, "ЛЭРИС", require_alert=False)

        self.assertIsNotNone(match)
        self.assertIsNone(match.alert)

    def test_new_hire_still_requires_alert_on_same_card(self):
        with patch.object(self.finder, "_find_template", return_value=None):
            match = self.finder.find(self.image, "ЛЭРИС", require_alert=True)

        self.assertIsNone(match)

    def test_new_hire_reads_only_card_bounded_by_alert(self):
        with patch.object(
            self.finder,
            "_find_template",
            side_effect=(self.alert, self.level),
        ):
            match = self.finder.find(self.image, "ЛЭРИС", require_alert=True)

        self.assertIsNotNone(match)
        self.name_reader.find.assert_not_called()
        bounds = self.name_reader.find_in_bounds.call_args.args[2]
        self.assertLess(bounds[0], self.name.center[0])
        self.assertGreater(bounds[2], self.name.center[0])


if __name__ == "__main__":
    unittest.main()
