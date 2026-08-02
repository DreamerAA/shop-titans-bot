import unittest

import numpy as np

from bot.hiring.ocr import (
    ActionDialogNameReader,
    GoldCostReader,
    HeroCardNameReader,
    HeroNameReader,
    HiringPanelReader,
)
from bot.hiring.vision import TemplateMatch


class FakeReader:
    def __init__(self, results):
        self.results = results

    def readtext(self, _image, **_kwargs):
        return self.results


class HiringOCRTests(unittest.TestCase):
    def test_reads_generated_name_relative_to_dialog_header(self):
        reader = FakeReader([([[0, 0], [70, 0], [70, 20], [0, 20]], "САБРИНА", 0.99)])
        header = TemplateMatch("name_header", 1.0, 1.0, (100, 50), (100, 30))

        name = HeroNameReader(reader).read(np.zeros((300, 400, 3), dtype=np.uint8), header)

        self.assertEqual("САБРИНА", name)

    def test_finds_exact_card_name_and_returns_global_center(self):
        reader = FakeReader([([[40, 10], [120, 10], [120, 30], [40, 30]], "САБРИНА", 0.95)])
        image = np.zeros((1000, 500, 3), dtype=np.uint8)

        match = HeroCardNameReader(reader).find(image, "сабрина")

        self.assertIsNotNone(match)
        self.assertEqual((80, 700), match.center)

    def test_accepts_one_ocr_duplicated_letter_in_card_name(self):
        reader = FakeReader([([[40, 10], [120, 10], [120, 30], [40, 30]], "ДДЖОРДИ", 0.81)])
        image = np.zeros((1000, 500, 3), dtype=np.uint8)

        match = HeroCardNameReader(reader).find(image, "ДЖОРДИ")

        self.assertIsNotNone(match)
        self.assertEqual("ДДЖОРДИ", match.text)

    def test_accepts_exact_long_card_name_at_lower_confidence(self):
        reader = FakeReader([([[40, 10], [140, 10], [140, 30], [40, 30]], "ЛОГАРСОН", 0.665)])
        image = np.zeros((1000, 500, 3), dtype=np.uint8)

        match = HeroCardNameReader(reader).find(image, "ЛОГАРСОН")

        self.assertIsNotNone(match)

    def test_accepts_missing_breve_in_card_name(self):
        reader = FakeReader([([[40, 10], [140, 10], [140, 30], [40, 30]], "РЕИНОЛЬД", 0.999)])
        image = np.zeros((1000, 500, 3), dtype=np.uint8)

        match = HeroCardNameReader(reader).find(image, "РЕЙНОЛЬД")

        self.assertIsNotNone(match)

    def test_does_not_fuzzily_accept_a_different_card_name(self):
        reader = FakeReader([([[40, 10], [120, 10], [120, 30], [40, 30]], "ДЖАРДИ", 0.99)])
        image = np.zeros((1000, 500, 3), dtype=np.uint8)

        match = HeroCardNameReader(reader).find(image, "ДЖОРДИ")

        self.assertIsNone(match)

    def test_accepts_exact_short_name_in_actions_at_lower_confidence(self):
        reader = FakeReader([([[40, 10], [120, 10], [120, 30], [40, 30]], "БАРЧ", 0.742)])
        image = np.zeros((1000, 1000, 3), dtype=np.uint8)

        match = ActionDialogNameReader(reader).find(image, "БАРЧ")

        self.assertIsNotNone(match)

    def test_reads_responsive_hiring_panel_labels_with_global_geometry(self):
        reader = FakeReader(
            [
                ([[20, 5], [80, 5], [80, 25], [20, 25]], "ЗАКЛИНАТЕЛЬ", 0.94),
                ([[20, 55], [60, 55], [60, 75], [20, 75]], "ДРУИД", 0.97),
            ]
        )

        matches = HiringPanelReader(reader).read_labels(np.zeros((400, 600, 3), dtype=np.uint8))

        self.assertEqual("ДРУИД", matches["ДРУИД"].text)
        self.assertEqual((190, 165), matches["ДРУИД"].center)
        self.assertEqual((40, 20), matches["ДРУИД"].size)

    def test_reads_gold_cost_without_thousands_separator(self):
        reader = FakeReader([([[0, 0], [50, 0], [50, 20], [0, 20]], "50.000", 0.97)])
        button = TemplateMatch("confirm_gold_hire", 1.0, 1.0, (10, 20), (120, 43))

        cost = GoldCostReader(reader).read_cost(np.zeros((100, 200, 3), dtype=np.uint8), button)

        self.assertEqual(50_000, cost)


if __name__ == "__main__":
    unittest.main()
