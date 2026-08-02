"""Small, lazily initialized OCR helpers for the hiring workflow."""

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from bot.hiring.vision import NormalizedROI, TemplateMatch

CYRILLIC_NAME_ALLOWLIST = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ-"
_SHARED_READER: Optional[Any] = None


def _get_shared_reader():
    global _SHARED_READER
    if _SHARED_READER is None:
        import easyocr

        _SHARED_READER = easyocr.Reader(["ru"], gpu=False, verbose=False)
    return _SHARED_READER


@dataclass(frozen=True)
class OCRTextMatch:
    text: str
    confidence: float
    center: tuple[int, int]
    size: tuple[int, int] = (0, 0)


class HeroNameReader:
    """Read the generated name from a name dialog anchored by its header."""

    def __init__(self, reader: Optional[Any] = None):
        self._reader = reader

    def _get_reader(self):
        if self._reader is None:
            self._reader = _get_shared_reader()
        return self._reader

    def read(self, image: np.ndarray, header: TemplateMatch) -> Optional[str]:
        scale = header.scale
        left = max(0, header.top_left[0] - round(30 * scale))
        right = min(image.shape[1], header.bottom_right[0] + round(30 * scale))
        top = max(0, header.top_left[1] + round(75 * scale))
        bottom = min(image.shape[0], header.top_left[1] + round(155 * scale))
        if right <= left or bottom <= top:
            return None

        results = self._get_reader().readtext(
            image[top:bottom, left:right],
            detail=1,
            paragraph=False,
            allowlist=CYRILLIC_NAME_ALLOWLIST,
        )
        candidates = []
        for _box, text, confidence in results:
            normalized = re.sub(r"[^А-ЯЁ-]", "", text.upper())
            if normalized:
                candidates.append((float(confidence), normalized))
        if not candidates:
            return None
        return max(candidates)[1]


class HiringPanelReader(HeroNameReader):
    """Read exact category and class labels from a responsive hiring panel."""

    def read_labels(
        self,
        image: np.ndarray,
        bounds: Optional[tuple[int, int, int, int]] = None,
    ) -> Dict[str, OCRTextMatch]:
        if bounds is None:
            left, top, right, bottom = NormalizedROI(0.25, 0.25, 1.0, 0.85).pixels(image)
        else:
            left, top, right, bottom = bounds
        results = self._get_reader().readtext(
            image[top:bottom, left:right],
            detail=1,
            paragraph=False,
            allowlist=CYRILLIC_NAME_ALLOWLIST,
        )
        matches: Dict[str, OCRTextMatch] = {}
        for box, text, confidence in results:
            normalized = re.sub(r"[^А-ЯЁ-]", "", text.upper())
            if not normalized or float(confidence) < 0.65:
                continue
            xs = [float(point[0]) for point in box]
            ys = [float(point[1]) for point in box]
            match = OCRTextMatch(
                text=normalized,
                confidence=float(confidence),
                center=(round(sum(xs) / len(xs)) + left, round(sum(ys) / len(ys)) + top),
                size=(round(max(xs) - min(xs)), round(max(ys) - min(ys))),
            )
            previous = matches.get(normalized)
            if previous is None or match.confidence > previous.confidence:
                matches[normalized] = match
        return matches


class GoldCostReader(HeroNameReader):
    """Read the gold price from the gold confirmation button."""

    def read_cost(self, image: np.ndarray, button: TemplateMatch) -> Optional[int]:
        left, top = button.top_left
        right, bottom = button.bottom_right
        results = self._get_reader().readtext(
            image[top:bottom, left:right],
            detail=1,
            paragraph=False,
            allowlist="0123456789.",
        )
        candidates = []
        for _box, text, confidence in results:
            digits = re.sub(r"\D", "", text)
            if digits and float(confidence) >= 0.50:
                candidates.append((float(confidence), int(digits)))
        if not candidates:
            return None
        return max(candidates)[1]


class HeroCardNameReader(HeroNameReader):
    """Find an exact generated name in the responsive character-card strip."""

    @staticmethod
    def _canonical_name(value: str) -> str:
        return value.replace("Ё", "Е").replace("Й", "И")

    @staticmethod
    def _matches_target(candidate: str, target: str) -> bool:
        candidate_key = HeroCardNameReader._canonical_name(candidate)
        target_key = HeroCardNameReader._canonical_name(target)
        if candidate_key == target_key:
            return True
        if len(candidate_key) != len(target_key) + 1:
            return False
        for index in range(len(candidate_key) - 1):
            if (
                candidate_key[index] == candidate_key[index + 1]
                and candidate_key[:index] + candidate_key[index + 1 :] == target_key
            ):
                return True
        return False

    def find(self, image: np.ndarray, target_name: str) -> Optional[OCRTextMatch]:
        top = round(image.shape[0] * 0.68)
        bottom = round(image.shape[0] * 0.94)
        return self.find_in_bounds(
            image,
            target_name,
            (0, top, image.shape[1], bottom),
        )

    def find_in_bounds(
        self,
        image: np.ndarray,
        target_name: str,
        bounds: tuple[int, int, int, int],
    ) -> Optional[OCRTextMatch]:
        target = re.sub(r"[^А-ЯЁ-]", "", target_name.upper())
        if not target:
            return None

        left, top, right, bottom = bounds
        results = self._get_reader().readtext(
            image[top:bottom, left:right],
            detail=1,
            paragraph=False,
            allowlist=CYRILLIC_NAME_ALLOWLIST,
        )
        candidates = []
        for box, text, confidence in results:
            normalized = re.sub(r"[^А-ЯЁ-]", "", text.upper())
            canonical_match = self._canonical_name(normalized) == self._canonical_name(target)
            minimum_confidence = 0.60 if canonical_match else 0.75
            if (
                not self._matches_target(normalized, target)
                or float(confidence) < minimum_confidence
            ):
                continue
            center_x = round(sum(float(point[0]) for point in box) / len(box)) + left
            center_y = round(sum(float(point[1]) for point in box) / len(box)) + top
            candidates.append(
                OCRTextMatch(
                    text=normalized,
                    confidence=float(confidence),
                    center=(center_x, center_y),
                )
            )
        if not candidates:
            return None
        return max(candidates, key=lambda candidate: candidate.confidence)


class ActionDialogNameReader(HeroNameReader):
    """Find the expected hero name inside the centered actions dialog."""

    def find(self, image: np.ndarray, target_name: str) -> Optional[OCRTextMatch]:
        target = re.sub(r"[^А-ЯЁ-]", "", target_name.upper())
        if not target:
            return None
        left, top, right, bottom = NormalizedROI(0.3, 0.35, 0.7, 0.65).pixels(image)
        results = self._get_reader().readtext(
            image[top:bottom, left:right],
            detail=1,
            paragraph=False,
            allowlist=CYRILLIC_NAME_ALLOWLIST,
        )
        for box, text, confidence in results:
            normalized = re.sub(r"[^А-ЯЁ-]", "", text.upper())
            # Short four-letter names can score just below 0.75 even when every
            # character is exact. This reader is additionally guarded by two
            # captures of the hero-actions screen and the Fire control.
            if normalized != target or float(confidence) < 0.70:
                continue
            center_x = round(sum(float(point[0]) for point in box) / len(box)) + left
            center_y = round(sum(float(point[1]) for point in box) / len(box)) + top
            return OCRTextMatch(
                text=normalized,
                confidence=float(confidence),
                center=(center_x, center_y),
            )
        return None
