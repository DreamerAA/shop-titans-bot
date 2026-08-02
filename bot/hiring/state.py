"""Recognize high-level hiring screens without performing input."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import cv2
import numpy as np

from bot.hiring.assets import TemplateSpec, get_template
from bot.hiring.ocr import HeroNameReader
from bot.hiring.vision import MultiScaleMatcher, TemplateMatch, load_template


class HiringScreen(str, Enum):
    RECONNECT = "reconnect"
    NAME_ENTRY = "name_entry"
    CHARACTERS = "characters"
    HIRING = "hiring"
    HERO_DETAILS = "hero_details"
    HERO_ACTIONS = "hero_actions"
    FIRE_CONFIRMATION = "fire_confirmation"
    MAIN = "main"
    BLOCKING_DIALOG = "blocking_dialog"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ScreenDetection:
    screen: HiringScreen
    evidence: Optional[TemplateMatch] = None
    suggested_action: Optional[str] = None
    hero_name: Optional[str] = None


class HiringStateDetector:
    """Detect known screens in priority order using stable controls."""

    checks: Tuple[Tuple[HiringScreen, str, Optional[str]], ...] = (
        (HiringScreen.RECONNECT, "reconnect", "reconnect"),
        (HiringScreen.NAME_ENTRY, "name_header", None),
        (HiringScreen.FIRE_CONFIRMATION, "confirm_fire", "confirm_fire"),
        (HiringScreen.HERO_ACTIONS, "fire", "fire"),
        (HiringScreen.HERO_DETAILS, "details_tab", None),
        (HiringScreen.CHARACTERS, "new_hero", "new_hero"),
        (HiringScreen.CHARACTERS, "heroes_tab", None),
        (HiringScreen.HIRING, "hiring_header", None),
        (HiringScreen.MAIN, "characters", "characters"),
        (HiringScreen.BLOCKING_DIALOG, "close", "close"),
    )

    def __init__(
        self,
        matcher: Optional[MultiScaleMatcher] = None,
        name_reader: Optional[HeroNameReader] = None,
    ):
        self.matcher = matcher or MultiScaleMatcher()
        self.name_reader = name_reader or HeroNameReader()
        self.known_scales: dict[str, float] = {}

    def _preferred_scales(self, spec: TemplateSpec) -> Tuple[float, ...]:
        preferred = []
        known = self.known_scales.get(spec.id)
        if known is not None:
            preferred.append(known)
        if 1.0 in spec.scales and 1.0 not in preferred:
            preferred.append(1.0)
        if not preferred:
            preferred.append(min(spec.scales, key=lambda scale: abs(scale - 1.0)))
        return tuple(preferred)

    def _find(
        self,
        image: np.ndarray,
        spec: TemplateSpec,
        scales: Optional[Tuple[float, ...]] = None,
    ) -> Optional[TemplateMatch]:
        match = self.matcher.find(
            image=image,
            template=load_template(spec.path),
            template_id=spec.id,
            scales=scales or spec.scales,
            threshold=spec.threshold,
            roi=spec.roi,
        )
        if match is not None:
            self.known_scales[spec.id] = match.scale
        return match

    def find_template(self, image: np.ndarray, template_id: str) -> Optional[TemplateMatch]:
        """Find a registered control without changing high-level state precedence."""

        spec = get_template(template_id)
        match = self._find(image, spec, self._preferred_scales(spec))
        if match is not None:
            return match
        return self._find(image, spec)

    def detect(self, image: np.ndarray) -> ScreenDetection:
        for preferred_only in (True, False):
            for screen, template_id, suggested_action in self.checks:
                spec = get_template(template_id)
                match = self._find(
                    image,
                    spec,
                    self._preferred_scales(spec) if preferred_only else spec.scales,
                )
                if match is None:
                    continue
                if screen == HiringScreen.NAME_ENTRY:
                    button = self.find_template(image, "confirm_free_hire")
                    action = "confirm_free_hire"
                    if button is None:
                        button = self.find_template(image, "confirm_gold_hire")
                        action = "confirm_gold_hire"
                    return ScreenDetection(
                        screen=screen,
                        evidence=button or match,
                        suggested_action=action if button is not None else None,
                        hero_name=self.name_reader.read(image, match),
                    )
                if screen == HiringScreen.HIRING:
                    hire_free = self.find_template(image, "hire_free")
                    if hire_free is not None:
                        return ScreenDetection(
                            screen=screen,
                            evidence=hire_free,
                            suggested_action="hire_free",
                        )
                return ScreenDetection(
                    screen=screen,
                    evidence=match,
                    suggested_action=suggested_action,
                )
        return ScreenDetection(screen=HiringScreen.UNKNOWN)


def annotate_detection(image: np.ndarray, detection: ScreenDetection) -> np.ndarray:
    """Draw the recognized control and state on a copy of an RGB frame."""

    annotated = image.copy()
    label = detection.screen.value
    if detection.evidence is not None:
        match = detection.evidence
        cv2.rectangle(annotated, match.top_left, match.bottom_right, (0, 255, 0), 3)
        label += f" {match.template_id}={match.score:.3f} scale={match.scale:.2f}"
    if detection.hero_name:
        label += f" name={detection.hero_name}"
    cv2.rectangle(annotated, (8, 8), (min(annotated.shape[1] - 8, 780), 52), (0, 0, 0), -1)
    cv2.putText(
        annotated,
        label,
        (18, 39),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    return annotated
