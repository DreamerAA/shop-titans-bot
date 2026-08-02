import unittest
from pathlib import Path

import numpy as np

from bot.hiring.skills import RecognizedSkill, SkillAnalysis, SkillRecognizer
from bot.hiring.vision import NormalizedROI, TemplateMatch, load_template


class SkillAnalysisTests(unittest.TestCase):
    @staticmethod
    def analysis(second_skill):
        return SkillAnalysis(
            fixed_skill=TemplateMatch("fixed", 1.0, 1.0, (0, 0), (10, 10)),
            random_skills=(
                RecognizedSkill(1, "juggernaut", 0.95, "extra_conditioning", 0.80),
                RecognizedSkill(2, second_skill, 0.93, "sturdy", 0.81),
            ),
            allowed_skills=frozenset({"juggernaut", "impervious"}),
        )

    def test_accepts_only_when_both_random_skills_are_allowed(self):
        self.assertTrue(self.analysis("impervious").accepted)

    def test_rejects_when_either_random_skill_is_not_allowed(self):
        self.assertFalse(self.analysis("sturdy").accepted)

    def test_unknown_slot_blocks_rejection_even_when_other_skill_is_bad(self):
        analysis = self.analysis("sturdy")
        ambiguous_allowed = RecognizedSkill(
            1,
            "juggernaut",
            0.90,
            "extra_conditioning",
            0.89,
            confident=False,
        )
        analysis = SkillAnalysis(
            fixed_skill=analysis.fixed_skill,
            random_skills=(ambiguous_allowed, analysis.random_skills[1]),
            allowed_skills=analysis.allowed_skills,
        )

        self.assertEqual("unknown", analysis.decision)

    def test_never_accepts_an_ambiguous_allowed_skill(self):
        analysis = self.analysis("impervious")
        ambiguous = RecognizedSkill(
            1,
            "juggernaut",
            0.90,
            "extra_conditioning",
            0.89,
            confident=False,
        )
        analysis = SkillAnalysis(
            fixed_skill=analysis.fixed_skill,
            random_skills=(ambiguous, analysis.random_skills[1]),
            allowed_skills=analysis.allowed_skills,
        )

        self.assertEqual("unknown", analysis.decision)


class SkillPaletteTests(unittest.TestCase):
    @staticmethod
    def analysis(second_skill):
        return SkillAnalysisTests.analysis(second_skill)

    def test_matching_palette_beats_same_shape_with_different_rarity_color(self):
        actual_sturdy = (8.0, 172.0, 123.0)
        sturdy_template = (9.0, 159.0, 123.0)
        impervious_template = (18.0, 221.0, 165.0)

        sturdy_score = SkillRecognizer._palette_similarity(actual_sturdy, sturdy_template)
        impervious_score = SkillRecognizer._palette_similarity(actual_sturdy, impervious_template)

        self.assertGreater(sturdy_score, impervious_score + 0.25)

    def test_real_same_shape_icons_use_palette_to_find_sturdy(self):
        skill_row = load_template(Path(__file__).parent / "data" / "hiring" / "barch_skill_row.png")
        image = np.zeros((200, 400, 3), dtype=np.uint8)
        image[70:125, 100:279] = skill_row

        analysis = SkillRecognizer().analyze(
            image,
            "soldier",
            frozenset({"impervious", "extra_plating"}),
        )

        self.assertEqual(
            ("sturdy", "extra_plating"),
            tuple(skill.skill_id for skill in analysis.random_skills),
        )
        self.assertEqual("reject", analysis.decision)

    def test_locates_responsive_druid_row_and_recognizes_both_skills(self):
        image = load_template(
            Path(__file__).parent / "data" / "hiring" / "druid_wide_skill_row.png"
        )
        recognizer = SkillRecognizer()
        fixed = recognizer._find_contour_row(
            image,
            expected_size=55,
            roi=NormalizedROI(0.0, 0.0, 1.0, 1.0),
            hero_class="druid",
        )
        allowed = frozenset({"adept", "death_dealer", "double_cast", "all_natural"})
        skills = (
            recognizer._classify_slot(image, fixed, 1, allowed),
            recognizer._classify_slot(image, fixed, 2, allowed),
        )

        self.assertEqual((27, 22), fixed.top_left)
        self.assertEqual(62, fixed.slot_step)
        self.assertEqual(("acrobatics", "fast_learner"), tuple(s.skill_id for s in skills))
        self.assertTrue(all(skill.confident for skill in skills))

    def test_aligned_shape_separates_extra_conditioning_from_juggernaut(self):
        image = load_template(
            Path(__file__).parent / "data" / "hiring" / "wesley_wide_skill_row.png"
        )
        recognizer = SkillRecognizer()
        fixed = recognizer._find_contour_row(
            image,
            expected_size=55,
            roi=NormalizedROI(0.0, 0.0, 1.0, 1.0),
            hero_class="druid",
        )
        allowed = frozenset({"adept", "death_dealer", "double_cast", "all_natural"})
        second = recognizer._classify_slot(image, fixed, 2, allowed)

        self.assertEqual("extra_conditioning", second.skill_id)
        self.assertEqual("juggernaut", second.runner_up_id)
        self.assertGreater(second.margin, 0.015)
        self.assertTrue(second.confident)

    def test_does_not_treat_two_similar_bad_templates_as_recognized(self):
        analysis = self.analysis("impervious")
        ambiguous_bad = RecognizedSkill(
            1,
            "fast_learner",
            0.84,
            "super_genius",
            0.839,
            confident=False,
            decision_hint="rejected",
        )
        analysis = SkillAnalysis(
            fixed_skill=analysis.fixed_skill,
            random_skills=(ambiguous_bad, analysis.random_skills[1]),
            allowed_skills=analysis.allowed_skills,
        )

        self.assertEqual("unknown", analysis.decision)

    def test_does_not_accept_two_similar_allowed_templates_without_identity(self):
        analysis = self.analysis("impervious")
        ambiguous_allowed = RecognizedSkill(
            1,
            "juggernaut",
            0.91,
            "impervious",
            0.90,
            confident=False,
            decision_hint="allowed",
        )
        analysis = SkillAnalysis(
            fixed_skill=analysis.fixed_skill,
            random_skills=(ambiguous_allowed, analysis.random_skills[1]),
            allowed_skills=analysis.allowed_skills,
        )

        self.assertEqual("unknown", analysis.decision)


if __name__ == "__main__":
    unittest.main()
