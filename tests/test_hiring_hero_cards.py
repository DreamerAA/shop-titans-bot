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
        self.finder = HeroCardFinder(name_reader=Mock(find=Mock(return_value=self.name)))

    def test_resume_accepts_exact_name_and_level_without_cleared_alert(self):
        with patch.object(self.finder, "_find_template", return_value=self.level):
            match = self.finder.find(self.image, "ЛЭРИС", require_alert=False)

        self.assertIsNotNone(match)
        self.assertIsNone(match.alert)

    def test_new_hire_still_requires_alert_on_same_card(self):
        with patch.object(self.finder, "_find_template", side_effect=(self.level, None)):
            match = self.finder.find(self.image, "ЛЭРИС", require_alert=True)

        self.assertIsNone(match)


if __name__ == "__main__":
    unittest.main()
