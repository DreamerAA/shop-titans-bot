"""Stable identifiers for hero classes and recognizable skills."""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class SkillDefinition:
    """Metadata for a skill template.

    ``id`` is the stable value used in configuration files. The Russian name
    is kept for logs and diagnostics. Template files will use ``id`` as their
    ASCII-only filename so OpenCV can load them reliably on Windows.
    """

    id: str
    name_ru: str

    @property
    def template_filename(self) -> str:
        return f"{self.id}.png"


HERO_CLASSES: Dict[str, Tuple[str, ...]] = {
    "warrior": (
        "soldier",
        "barbarian",
        "knight",
        "ranger",
        "samurai",
        "berserker",
        "dark_knight",
    ),
    "rogue": (
        "thief",
        "monk",
        "musketeer",
        "wanderer",
        "ninja",
        "dancer",
        "velite",
    ),
    "spellcaster": (
        "mage",
        "cleric",
        "druid",
        "sorcerer",
        "spellblade",
        "geomancer",
        "chronomancer",
    ),
}


_SKILL_NAMES_RU = {
    "acrobatics": "Акробатика",
    "fast_healer": "Быстрое исцеление",
    "fast_learner": "Быстрое обучение",
    "whirlwind_attack": "Вихрь",
    "warlord": "Военачальник",
    "survivor": "Выживший",
    "telling_blows": "Говорящие удары",
    "juggernaut": "Джагернаут",
    "extra_conditioning": "Дополнительная отработка",
    "extra_plating": "Дополнительные латы",
    "perfect_form": "Идеальная стойка",
    "battering_blows": "Избиение",
    "mace_master": "Мастер булав",
    "spear_master": "Мастер копья",
    "throw_daggers": "Метание кинжалов",
    "sword_master": "Мечник",
    "power_attack": "Мощная атака",
    "on_guard": "На страже",
    "impervious": "Непробиваемость",
    "deception": "Обман",
    "maintenance": "Обслуживание",
    "flame_brand": "Огненный клинок",
    "eagle_eyes": "Орлиный глаз",
    "axe_master": "Повелитель топоров",
    "all_natural": "Природный дар",
    "perforate": "Протыкание",
    "sturdy": "Прочность",
    "blurred_movement": "Размытость",
    "sunder": "Раскол",
    "cleave": "Рассекание",
    "extended_warranty": "Расширенная гарантия",
    "super_genius": "Сверхгениальность",
    "shining_blade": "Сияющий клинок",
    "deadly_criticals": "Смертельные критические удары",
    "toughness": "Стойкость",
    "thick_skin": "Толстая кожа",
    "death_dealer": "Торговец смертью",
    "smite": "Удар небес",
    "caltrops": "Шипы",
}


SKILLS: Dict[str, SkillDefinition] = {
    skill_id: SkillDefinition(id=skill_id, name_ru=name_ru)
    for skill_id, name_ru in _SKILL_NAMES_RU.items()
}
