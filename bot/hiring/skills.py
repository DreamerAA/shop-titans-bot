"""Recognize the two randomized skills shown on a newly hired hero."""

import math
from dataclasses import dataclass
from itertools import combinations
from typing import FrozenSet, List, Optional, Tuple

import cv2
import numpy as np

from bot.hiring.assets import TEMPLATE_ROOT, get_template, scales
from bot.hiring.catalog import SKILLS
from bot.hiring.vision import MultiScaleMatcher, NormalizedROI, TemplateMatch, load_template


class SkillRecognitionError(RuntimeError):
    """Raised when skill evidence is missing or ambiguous."""


@dataclass(frozen=True)
class RecognizedSkill:
    position: int
    skill_id: str
    score: float
    runner_up_id: str
    runner_up_score: float
    confident: bool = True
    decision_hint: Optional[str] = None
    best_allowed_id: Optional[str] = None
    best_allowed_score: float = 0.0
    best_rejected_id: Optional[str] = None
    best_rejected_score: float = 0.0
    shape_score: float = 0.0
    palette_score: float = 0.0

    @property
    def margin(self) -> float:
        return self.score - self.runner_up_score


@dataclass(frozen=True)
class SkillAnalysis:
    fixed_skill: TemplateMatch
    random_skills: Tuple[RecognizedSkill, RecognizedSkill]
    allowed_skills: FrozenSet[str]

    def _slot_decision(self, skill: RecognizedSkill) -> str:
        if skill.decision_hint is not None:
            return skill.decision_hint
        if not skill.confident:
            return "uncertain"
        return "allowed" if skill.skill_id in self.allowed_skills else "rejected"

    @property
    def decision(self) -> str:
        if any(not skill.confident for skill in self.random_skills):
            return "unknown"
        slot_decisions = tuple(self._slot_decision(skill) for skill in self.random_skills)
        if "rejected" in slot_decisions:
            return "reject"
        if slot_decisions == ("allowed", "allowed"):
            return "accept"
        return "uncertain"

    @property
    def unrecognized_skills(self) -> Tuple[RecognizedSkill, ...]:
        return tuple(skill for skill in self.random_skills if not skill.confident)

    @property
    def accepted(self) -> bool:
        return self.decision == "accept"


class SkillRecognizer:
    """Anchor on the three-skill row, then classify its two random slots in color."""

    def __init__(
        self,
        minimum_score: float = 0.80,
        # Shape and HSV palette are combined below. A small but non-zero margin
        # still rejects visually ambiguous or missing catalog entries.
        minimum_margin: float = 0.015,
        minimum_allowed_margin: float = 0.015,
        minimum_rejected_score: float = 0.75,
        minimum_rejected_margin: float = 0.03,
    ):
        self.anchor_matcher = MultiScaleMatcher()
        self.color_matcher = MultiScaleMatcher(grayscale=False)
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin
        self.minimum_allowed_margin = minimum_allowed_margin
        self.minimum_rejected_score = minimum_rejected_score
        self.minimum_rejected_margin = minimum_rejected_margin

    @staticmethod
    def _inner_icon(template: np.ndarray) -> np.ndarray:
        height, width = template.shape[:2]
        top, bottom = round(height * 0.15), round(height * 0.85)
        left, right = round(width * 0.15), round(width * 0.85)
        return template[top:bottom, left:right]

    @staticmethod
    def _color_signature(image: np.ndarray) -> Tuple[float, float, float]:
        """Return the median HSV palette of the colored skill-tile pixels."""

        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).reshape(-1, 3)
        colored = hsv[(hsv[:, 1] > 45) & (hsv[:, 2] > 35)]
        if len(colored) < 10:
            colored = hsv
        hue = float(np.median(colored[:, 0]))  # type: ignore[arg-type]
        saturation = float(np.median(colored[:, 1]))  # type: ignore[arg-type]
        value = float(np.median(colored[:, 2]))  # type: ignore[arg-type]
        return hue, saturation, value

    @staticmethod
    def _palette_similarity(
        first: Tuple[float, float, float],
        second: Tuple[float, float, float],
    ) -> float:
        """Compare HSV palettes while treating hue as a circular coordinate."""

        hue_delta = abs(first[0] - second[0])
        hue_delta = min(hue_delta, 180.0 - hue_delta) / 30.0
        saturation_delta = abs(first[1] - second[1]) / 100.0
        value_delta = abs(first[2] - second[2]) / 100.0
        distance = math.sqrt(
            hue_delta * hue_delta + saturation_delta * saturation_delta + value_delta * value_delta
        )
        return math.exp(-1.5 * distance)

    def _find_fixed_skill(self, image: np.ndarray, hero_class: str) -> TemplateMatch:
        path = TEMPLATE_ROOT / "hiring" / "classes" / hero_class / "fixed_skill.png"
        if path.is_file():
            match = self.anchor_matcher.find(
                image=image,
                template=load_template(path),
                template_id=f"{hero_class}_fixed_skill",
                scales=scales(0.45, 1.8, 0.05),
                threshold=0.82,
                roi=NormalizedROI(0.15, 0.25, 0.75, 0.9),
            )
            if match is not None:
                return match

        # Responsive layouts can move the hero and the three-skill row to the
        # other side of the panel. Use the Details tab only for UI scale, then
        # locate the three equally sized, aligned tile borders geometrically.
        details_spec = get_template("details_tab")
        details = self.anchor_matcher.find(
            image=image,
            template=load_template(details_spec.path),
            template_id=details_spec.id,
            scales=details_spec.scales,
            threshold=details_spec.threshold,
            roi=details_spec.roi,
        )
        if details is None:
            raise SkillRecognitionError(
                f"Could not locate either the fixed skill or Details anchor for {hero_class!r}"
            )
        expected_size = round(55 * details.scale)
        return self._find_contour_row(
            image,
            expected_size,
            NormalizedROI(0.1, 0.2, 0.8, 0.9),
            hero_class,
        )

    @staticmethod
    def _find_contour_row(
        image: np.ndarray,
        expected_size: int,
        roi: NormalizedROI,
        hero_class: str,
    ) -> TemplateMatch:
        left, top, right, bottom = roi.pixels(image)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 60, 160)
        contours, _hierarchy = cv2.findContours(
            edges,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        candidates: List[Tuple[int, int, int, int, float]] = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if (
                x < left
                or y < top
                or x + width > right
                or y + height > bottom
                or not 0.8 * expected_size <= width <= 1.2 * expected_size
                or not 0.8 * expected_size <= height <= 1.2 * expected_size
                or not 0.9 <= width / height <= 1.1
                or area < 0.65 * width * height
            ):
                continue
            candidate = (x, y, width, height, float(area))
            duplicate_index = next(
                (
                    index
                    for index, existing in enumerate(candidates)
                    if abs(existing[0] - x) <= 2
                    and abs(existing[1] - y) <= 2
                    and abs(existing[2] - width) <= 2
                    and abs(existing[3] - height) <= 2
                ),
                None,
            )
            if duplicate_index is None:
                candidates.append(candidate)
            elif area > candidates[duplicate_index][4]:
                candidates[duplicate_index] = candidate

        rows = []
        for group in combinations(candidates, 3):
            ordered = sorted(group, key=lambda item: item[0])
            xs = [item[0] for item in ordered]
            ys = [item[1] for item in ordered]
            sizes = [(item[2] + item[3]) / 2.0 for item in ordered]
            gaps = (xs[1] - xs[0], xs[2] - xs[1])
            if (
                max(ys) - min(ys) > max(3, 0.08 * expected_size)
                or max(sizes) - min(sizes) > 0.12 * expected_size
                or not all(0.95 * expected_size <= gap <= 1.35 * expected_size for gap in gaps)
                or abs(gaps[0] - gaps[1]) > 0.15 * expected_size
            ):
                continue
            error = (
                (max(ys) - min(ys))
                + (max(sizes) - min(sizes))
                + abs(gaps[0] - gaps[1])
                + abs(sum(sizes) / 3.0 - expected_size)
            ) / expected_size
            rows.append((error, ordered, gaps))
        if not rows:
            raise SkillRecognitionError("Could not find one aligned row of three skill tiles")
        _error, ordered, gaps = min(rows, key=lambda item: item[0])
        first = ordered[0]
        width = round(sum(item[2] for item in ordered) / 3.0)
        height = round(sum(item[3] for item in ordered) / 3.0)
        return TemplateMatch(
            template_id=f"{hero_class}_fixed_contour",
            score=max(0.0, 1.0 - min(1.0, _error)),
            scale=width / 55.0,
            top_left=(first[0], round(sum(item[1] for item in ordered) / 3.0)),
            size=(width, height),
            slot_step=round(sum(gaps) / 2.0),
        )

    def _classify_slot(
        self,
        image: np.ndarray,
        fixed: TemplateMatch,
        position: int,
        allowed_skills: FrozenSet[str],
    ) -> RecognizedSkill:
        slot_step = fixed.slot_step or round(fixed.size[0] * 1.13)
        padding = max(4, round(fixed.size[0] * 0.15))
        left = max(0, fixed.top_left[0] + slot_step * position - padding)
        top = max(0, fixed.top_left[1] - padding)
        right = min(image.shape[1], left + fixed.size[0] + padding * 2)
        bottom = min(image.shape[0], top + fixed.size[1] + padding * 2)
        slot = image[top:bottom, left:right]

        tile_left = fixed.top_left[0] + slot_step * position
        tile_top = fixed.top_left[1]
        tile_right = min(image.shape[1], tile_left + fixed.size[0])
        tile_bottom = min(image.shape[0], tile_top + fixed.size[1])
        actual_tile = image[tile_top:tile_bottom, tile_left:tile_right]
        if actual_tile.shape[:2] != (fixed.size[1], fixed.size[0]):
            raise SkillRecognitionError(f"Random skill position {position} lies outside the frame")
        actual_palette = self._color_signature(self._inner_icon(actual_tile))
        actual_inner = self._inner_icon(actual_tile)
        actual_gray = cv2.cvtColor(actual_inner, cv2.COLOR_RGB2GRAY)

        candidates = []
        candidate_evidence = {}
        skill_root = TEMPLATE_ROOT / "hiring" / "skills"
        for skill in SKILLS.values():
            template = self._inner_icon(load_template(skill_root / skill.template_filename))
            match = self.color_matcher.find(
                image=slot,
                template=template,
                template_id=skill.id,
                scales=scales(0.7, 2.0, 0.05),
                threshold=0.0,
            )
            if match is not None:
                aligned_template = cv2.resize(
                    template,
                    (actual_inner.shape[1], actual_inner.shape[0]),
                    interpolation=cv2.INTER_CUBIC,
                )
                aligned_score = float(
                    cv2.matchTemplate(
                        actual_gray,
                        cv2.cvtColor(aligned_template, cv2.COLOR_RGB2GRAY),
                        cv2.TM_CCOEFF_NORMED,
                    )[0, 0]
                )
                shape_score = 0.80 * match.score + 0.20 * aligned_score
                palette_score = self._palette_similarity(
                    actual_palette,
                    self._color_signature(template),
                )
                combined_score = 0.65 * shape_score + 0.35 * palette_score
                candidates.append(
                    TemplateMatch(
                        template_id=match.template_id,
                        score=combined_score,
                        scale=match.scale,
                        top_left=match.top_left,
                        size=match.size,
                    )
                )
                candidate_evidence[match.template_id] = (shape_score, palette_score)

        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        if len(candidates) < 2:
            raise SkillRecognitionError(
                f"Not enough candidates for random skill position {position}"
            )
        best, runner_up = candidates[:2]
        best_shape_score, best_palette_score = candidate_evidence[best.template_id]
        confident = (
            best.score >= self.minimum_score and best.score - runner_up.score >= self.minimum_margin
        )
        allowed_candidates = [
            candidate for candidate in candidates if candidate.template_id in allowed_skills
        ]
        rejected_candidates = [
            candidate for candidate in candidates if candidate.template_id not in allowed_skills
        ]
        if not allowed_candidates or not rejected_candidates:
            raise SkillRecognitionError("Skill catalog must contain allowed and rejected templates")
        best_allowed = allowed_candidates[0]
        best_rejected = rejected_candidates[0]
        if (
            best_allowed.score >= self.minimum_score
            and best_allowed.score - best_rejected.score >= self.minimum_allowed_margin
        ):
            decision_hint = "allowed"
        elif (
            best_rejected.score >= self.minimum_rejected_score
            and best_rejected.score - best_allowed.score >= self.minimum_rejected_margin
        ):
            decision_hint = "rejected"
        else:
            decision_hint = "uncertain"
        return RecognizedSkill(
            position=position,
            skill_id=best.template_id,
            score=best.score,
            runner_up_id=runner_up.template_id,
            runner_up_score=runner_up.score,
            confident=confident,
            decision_hint=decision_hint,
            best_allowed_id=best_allowed.template_id,
            best_allowed_score=best_allowed.score,
            best_rejected_id=best_rejected.template_id,
            best_rejected_score=best_rejected.score,
            shape_score=best_shape_score,
            palette_score=best_palette_score,
        )

    def analyze(
        self,
        image: np.ndarray,
        hero_class: str,
        allowed_skills: FrozenSet[str],
    ) -> SkillAnalysis:
        fixed = self._find_fixed_skill(image, hero_class)
        random_skills = (
            self._classify_slot(image, fixed, 1, allowed_skills),
            self._classify_slot(image, fixed, 2, allowed_skills),
        )
        return SkillAnalysis(
            fixed_skill=fixed,
            random_skills=random_skills,
            allowed_skills=allowed_skills,
        )
