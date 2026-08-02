"""Locate a newly hired hero card using independent visual evidence."""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from bot.hiring.assets import get_template
from bot.hiring.ocr import HeroCardNameReader, OCRTextMatch
from bot.hiring.vision import MultiScaleMatcher, TemplateMatch, load_template


@dataclass(frozen=True)
class HeroCardMatch:
    name: OCRTextMatch
    level: TemplateMatch
    alert: Optional[TemplateMatch]
    click_point: tuple[int, int]


class HeroCardFinder:
    """Require exact name OCR, level 10, and a new-hero alert on one card."""

    def __init__(
        self,
        name_reader: Optional[HeroCardNameReader] = None,
        matcher: Optional[MultiScaleMatcher] = None,
    ):
        self.name_reader = name_reader or HeroCardNameReader()
        self.matcher = matcher or MultiScaleMatcher()

    def _find_template(
        self,
        image: np.ndarray,
        template_id: str,
        bounds: tuple[int, int, int, int],
    ) -> Optional[TemplateMatch]:
        spec = get_template(template_id)
        left, top, right, bottom = bounds
        match = self.matcher.find(
            image=image[top:bottom, left:right],
            template=load_template(spec.path),
            template_id=spec.id,
            scales=spec.scales,
            threshold=spec.threshold,
            roi=None,
        )
        if match is None:
            return None
        return TemplateMatch(
            template_id=match.template_id,
            score=match.score,
            scale=match.scale,
            top_left=(match.top_left[0] + left, match.top_left[1] + top),
            size=match.size,
        )

    def find(
        self,
        image: np.ndarray,
        hero_name: str,
        *,
        require_alert: bool = True,
    ) -> Optional[HeroCardMatch]:
        name = self.name_reader.find(image, hero_name)
        if name is None:
            return None

        height, width = image.shape[:2]
        horizontal_gap = round(width * 0.08)
        card_top = max(0, name.center[1] - round(height * 0.12))
        card_bottom = min(height, name.center[1])
        level = self._find_template(
            image,
            "level_10",
            (
                max(0, name.center[0] - horizontal_gap),
                card_top,
                name.center[0],
                card_bottom,
            ),
        )
        if level is None:
            return None

        if not (level.center[0] < name.center[0] and level.center[1] < name.center[1]):
            return None

        alert = None
        if require_alert:
            alert = self._find_template(
                image,
                "new_hero_alert",
                (
                    name.center[0],
                    card_top,
                    min(width, name.center[0] + horizontal_gap),
                    card_bottom,
                ),
            )
            if alert is None or not (
                name.center[0] < alert.center[0] and alert.center[1] < name.center[1]
            ):
                return None

        portrait_y = max(0, name.center[1] - round(height * 0.05))
        return HeroCardMatch(
            name=name,
            level=level,
            alert=alert,
            click_point=(name.center[0], portrait_y),
        )
