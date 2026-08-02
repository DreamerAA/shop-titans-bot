"""Template registry used by the hiring workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from bot.hiring.vision import NormalizedROI

TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "data" / "templates"


@dataclass(frozen=True)
class TemplateSpec:
    id: str
    relative_path: str
    threshold: float
    scales: Tuple[float, ...]
    roi: Optional[NormalizedROI] = None

    @property
    def path(self) -> Path:
        return TEMPLATE_ROOT / self.relative_path


def scales(start: float, stop: float, step: float) -> Tuple[float, ...]:
    count = int(round((stop - start) / step))
    return tuple(round(start + index * step, 3) for index in range(count + 1))


BOTTOM_CONTROLS = NormalizedROI(0.0, 0.7, 0.85, 1.0)
BOTTOM_CENTER = NormalizedROI(0.15, 0.65, 0.85, 1.0)
BOTTOM_FULL = NormalizedROI(0.0, 0.55, 1.0, 1.0)
CENTER_PANEL = NormalizedROI(0.2, 0.2, 0.8, 1.0)
DIALOG_AREA = NormalizedROI(0.3, 0.1, 0.82, 0.72)
RIGHT_PANEL = NormalizedROI(0.55, 0.2, 1.0, 0.9)
CENTER_DIALOG = NormalizedROI(0.3, 0.25, 0.7, 0.75)
BOTTOM_TABS = NormalizedROI(0.65, 0.88, 0.85, 1.0)
HERO_CARD_TOPS = NormalizedROI(0.0, 0.65, 1.0, 0.82)
HERO_PANEL = NormalizedROI(0.3, 0.2, 0.85, 0.65)


TEMPLATES = {
    "characters": TemplateSpec(
        id="characters",
        relative_path="hiring/controls/characters_core.png",
        # Notification badges overlap the top-right corner of this control.
        threshold=0.82,
        scales=scales(0.6, 2.2, 0.1),
        roi=BOTTOM_CONTROLS,
    ),
    "new_hero": TemplateSpec(
        id="new_hero",
        relative_path="hiring/controls/new_hero.png",
        threshold=0.84,
        scales=scales(0.45, 2.2, 0.05),
        roi=BOTTOM_FULL,
    ),
    "heroes_tab": TemplateSpec(
        id="heroes_tab",
        relative_path="hiring/controls/heroes_tab.png",
        threshold=0.86,
        scales=scales(0.45, 2.0, 0.05),
        roi=BOTTOM_TABS,
    ),
    "new_hero_alert": TemplateSpec(
        id="new_hero_alert",
        relative_path="hiring/controls/new_hero_alert.png",
        # The alert pulses between bright and dark frames; name + level geometry
        # below supplies the additional safety check.
        threshold=0.60,
        scales=scales(0.45, 2.0, 0.05),
        roi=HERO_CARD_TOPS,
    ),
    "level_10": TemplateSpec(
        id="level_10",
        relative_path="hiring/controls/level_10.png",
        threshold=0.84,
        scales=scales(0.45, 2.0, 0.05),
        roi=HERO_CARD_TOPS,
    ),
    "hiring_header": TemplateSpec(
        id="hiring_header",
        relative_path="hiring/controls/hiring_header.png",
        threshold=0.86,
        scales=scales(0.45, 2.0, 0.05),
        roi=RIGHT_PANEL,
    ),
    "hire_free": TemplateSpec(
        id="hire_free",
        relative_path="hiring/controls/hire_free.png",
        threshold=0.82,
        scales=scales(0.45, 2.0, 0.05),
        roi=RIGHT_PANEL,
    ),
    "hire": TemplateSpec(
        id="hire",
        relative_path="hiring/controls/hire.png",
        threshold=0.82,
        scales=scales(0.45, 2.0, 0.05),
        roi=RIGHT_PANEL,
    ),
    "warrior_category_selected": TemplateSpec(
        id="warrior_category_selected",
        relative_path="hiring/controls/warrior_category_selected.png",
        threshold=0.88,
        scales=scales(0.45, 2.0, 0.05),
        roi=CENTER_PANEL,
    ),
    "rogue_category_selected": TemplateSpec(
        id="rogue_category_selected",
        relative_path="hiring/controls/rogue_category_selected.png",
        threshold=0.88,
        scales=scales(0.45, 2.0, 0.05),
        roi=CENTER_PANEL,
    ),
    "spellcaster_category_selected": TemplateSpec(
        id="spellcaster_category_selected",
        relative_path="hiring/controls/spellcaster_category_selected.png",
        threshold=0.88,
        scales=scales(0.45, 2.0, 0.05),
        roi=CENTER_PANEL,
    ),
    "warrior_selected": TemplateSpec(
        id="warrior_selected",
        relative_path="hiring/controls/warrior_selected.png",
        threshold=0.86,
        scales=scales(0.45, 2.0, 0.05),
        roi=RIGHT_PANEL,
    ),
    "soldier_selected": TemplateSpec(
        id="soldier_selected",
        relative_path="hiring/controls/soldier_selected.png",
        threshold=0.86,
        scales=scales(0.45, 2.0, 0.05),
        roi=RIGHT_PANEL,
    ),
    "name_header": TemplateSpec(
        id="name_header",
        relative_path="hiring/controls/name_header.png",
        threshold=0.88,
        scales=scales(0.45, 2.0, 0.05),
        roi=CENTER_DIALOG,
    ),
    "confirm_free_hire": TemplateSpec(
        id="confirm_free_hire",
        relative_path="hiring/controls/confirm_free_hire.png",
        threshold=0.82,
        scales=scales(0.45, 2.0, 0.05),
        roi=CENTER_DIALOG,
    ),
    "confirm_gold_hire": TemplateSpec(
        id="confirm_gold_hire",
        relative_path="hiring/controls/confirm_gold_hire.png",
        threshold=0.82,
        scales=scales(0.45, 2.0, 0.05),
        roi=CENTER_DIALOG,
    ),
    "gear": TemplateSpec(
        id="gear",
        relative_path="hiring/controls/gear.png",
        threshold=0.86,
        scales=scales(0.6, 2.2, 0.1),
        roi=CENTER_PANEL,
    ),
    "details_tab": TemplateSpec(
        id="details_tab",
        relative_path="hiring/controls/details_tab.png",
        threshold=0.86,
        scales=scales(0.45, 2.0, 0.05),
        roi=HERO_PANEL,
    ),
    "fire": TemplateSpec(
        id="fire",
        relative_path="hiring/controls/fire.png",
        threshold=0.85,
        scales=scales(0.6, 2.2, 0.1),
        roi=CENTER_PANEL,
    ),
    "confirm_fire": TemplateSpec(
        id="confirm_fire",
        relative_path="hiring/controls/confirm_fire.png",
        threshold=0.88,
        scales=scales(0.6, 2.2, 0.1),
        roi=CENTER_PANEL,
    ),
    "reconnect": TemplateSpec(
        id="reconnect",
        relative_path="controls/reconnect.png",
        threshold=0.82,
        scales=scales(0.35, 1.0, 0.05),
        roi=CENTER_PANEL,
    ),
    "close": TemplateSpec(
        id="close",
        relative_path="controls/close.png",
        threshold=0.85,
        scales=scales(0.35, 1.25, 0.05),
        roi=DIALOG_AREA,
    ),
}


def get_template(template_id: str) -> TemplateSpec:
    try:
        return TEMPLATES[template_id]
    except KeyError as exc:
        raise KeyError(f"Unknown UI template: {template_id}") from exc
