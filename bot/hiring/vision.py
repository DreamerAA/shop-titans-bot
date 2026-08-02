"""Resolution-tolerant template matching for the hiring workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np


@dataclass(frozen=True)
class NormalizedROI:
    """Search region expressed as fractions of the frame dimensions."""

    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self):
        if not (0 <= self.left < self.right <= 1 and 0 <= self.top < self.bottom <= 1):
            raise ValueError("Normalized ROI coordinates must be ordered and between 0 and 1")

    def pixels(self, image: np.ndarray) -> Tuple[int, int, int, int]:
        height, width = image.shape[:2]
        return (
            int(round(self.left * width)),
            int(round(self.top * height)),
            int(round(self.right * width)),
            int(round(self.bottom * height)),
        )


@dataclass(frozen=True)
class TemplateMatch:
    template_id: str
    score: float
    scale: float
    top_left: Tuple[int, int]
    size: Tuple[int, int]
    slot_step: Optional[int] = None

    @property
    def center(self) -> Tuple[int, int]:
        x, y = self.top_left
        width, height = self.size
        return x + width // 2, y + height // 2

    @property
    def bottom_right(self) -> Tuple[int, int]:
        x, y = self.top_left
        width, height = self.size
        return x + width, y + height


def load_template(path: Union[str, Path]) -> np.ndarray:
    """Load a template with Unicode-safe Windows path handling."""

    template_path = Path(path)
    data = np.fromfile(str(template_path), dtype=np.uint8)
    template = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template not found or unreadable: {template_path}")
    return cv2.cvtColor(template, cv2.COLOR_BGR2RGB)


class MultiScaleMatcher:
    """Find the strongest template match over an explicit scale range."""

    def __init__(self, grayscale: bool = True):
        self.grayscale = grayscale

    def find(
        self,
        image: np.ndarray,
        template: np.ndarray,
        template_id: str,
        scales: Tuple[float, ...],
        threshold: float,
        roi: Optional[NormalizedROI] = None,
    ) -> Optional[TemplateMatch]:
        if image.ndim != 3 or template.ndim != 3:
            raise ValueError("Matcher expects RGB images")

        if roi is None:
            region = image
            offset_x = offset_y = 0
        else:
            left, top, right, bottom = roi.pixels(image)
            region = image[top:bottom, left:right]
            offset_x, offset_y = left, top

        if self.grayscale:
            match_region = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
            match_template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        else:
            match_region = region
            match_template = template
        best: Optional[TemplateMatch] = None

        for scale in scales:
            width = max(1, int(round(match_template.shape[1] * scale)))
            height = max(1, int(round(match_template.shape[0] * scale)))
            if width > match_region.shape[1] or height > match_region.shape[0]:
                continue
            interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
            resized = cv2.resize(match_template, (width, height), interpolation=interpolation)
            result = cv2.matchTemplate(match_region, resized, cv2.TM_CCOEFF_NORMED)
            _, score, _, location = cv2.minMaxLoc(result)
            if not np.isfinite(score):
                continue
            match = TemplateMatch(
                template_id=template_id,
                score=float(score),
                scale=scale,
                top_left=(location[0] + offset_x, location[1] + offset_y),
                size=(width, height),
            )
            if best is None or match.score > best.score:
                best = match

        if best is None or best.score < threshold:
            return None
        return best
