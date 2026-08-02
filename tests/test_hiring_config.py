import tempfile
import unittest
from pathlib import Path

import yaml

from bot.hiring.catalog import HERO_CLASSES, SKILLS
from bot.hiring.config import HiringConfigError, load_hiring_config, parse_hiring_config


class HiringCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_provided_classes_and_skills(self):
        self.assertEqual(21, sum(len(classes) for classes in HERO_CLASSES.values()))
        self.assertEqual(58, len(SKILLS))
        self.assertEqual("epic", SKILLS["adept"].rarity)
        self.assertEqual("epic", SKILLS["double_cast"].rarity)
        self.assertEqual("rare", SKILLS["all_natural"].rarity)
        self.assertEqual("epic", SKILLS["death_dealer"].rarity)
        self.assertEqual("usual", SKILLS["dagger_master"].rarity)
        self.assertEqual("usual", SKILLS["shield_master"].rarity)


class HiringConfigTests(unittest.TestCase):
    def valid_data(self):
        return {
            "window": {
                "process_name": "ShopTitan.exe",
                "title_contains": "Shop Titans",
                "capture_method": "desktop",
                "input_method": "foreground_mouse",
                "min_client_width": 640,
                "min_client_height": 480,
            },
            "hiring": {
                "category": "warrior",
                "class": "soldier",
                "allowed_skills": [
                    "extra_plating",
                    "impervious",
                    "juggernaut",
                    "thick_skin",
                ],
                "limits": {"max_gold_spent": 1_000_000, "max_attempts": 100},
            },
        }

    def test_parses_soldier_configuration(self):
        config = parse_hiring_config(self.valid_data())

        self.assertEqual("warrior", config.category)
        self.assertEqual("soldier", config.hero_class)
        self.assertEqual("ShopTitan.exe", config.window.process_name)
        self.assertEqual("desktop", config.window.capture_method)
        self.assertEqual("foreground_mouse", config.window.input_method)
        self.assertEqual(1_000_000, config.limits.max_gold_spent)
        self.assertEqual(4, len(config.allowed_skills))

    def test_parses_requested_druid_configuration(self):
        data = self.valid_data()
        data["hiring"].update(
            {
                "category": "spellcaster",
                "class": "druid",
                "allowed_skills": [
                    "adept",
                    "death_dealer",
                    "double_cast",
                    "all_natural",
                ],
            }
        )

        config = parse_hiring_config(data)

        self.assertEqual("spellcaster", config.category)
        self.assertEqual("druid", config.hero_class)

    def test_unknown_skill_fails_before_runtime(self):
        data = self.valid_data()
        data["hiring"]["allowed_skills"].append("unknown_skill")

        with self.assertRaisesRegex(HiringConfigError, "unknown_skill"):
            parse_hiring_config(data)

    def test_class_must_belong_to_selected_category(self):
        data = self.valid_data()
        data["hiring"]["class"] = "mage"

        with self.assertRaisesRegex(HiringConfigError, "does not belong"):
            parse_hiring_config(data)

    def test_loads_yaml_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hiring.yaml"
            path.write_text(yaml.safe_dump(self.valid_data()), encoding="utf-8")

            config = load_hiring_config(path)

        self.assertEqual("soldier", config.hero_class)


if __name__ == "__main__":
    unittest.main()
