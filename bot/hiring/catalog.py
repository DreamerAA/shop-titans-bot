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
    rarity: str

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

HERO_CATEGORY_NAMES_RU = {
    "warrior": "ВОИН",
    "rogue": "СТРАННИК",
    "spellcaster": "ЗАКЛИНАТЕЛЬ",
}

HERO_CLASS_NAMES_RU = {
    "soldier": "СОЛДАТ",
    "barbarian": "ВАРВАР",
    "knight": "РЫЦАРЬ",
    "ranger": "ОХОТНИК",
    "samurai": "САМУРАЙ",
    "berserker": "БЕРСЕРК",
    "dark_knight": "ТЁМНЫЙ РЫЦАРЬ",
    "thief": "ВОР",
    "monk": "МОНАХ",
    "musketeer": "МУШКЕТЁР",
    "wanderer": "БРОДЯГА",
    "ninja": "НИНДЗЯ",
    "dancer": "ТАНЦОР",
    "velite": "ВЕЛИТ",
    "mage": "МАГ",
    "cleric": "СВЯЩЕННИК",
    "druid": "ДРУИД",
    "sorcerer": "ВОЛШЕБНИК",
    "spellblade": "ЧУДОТВОРЕЦ",
    "geomancer": "ГЕОМАНТ",
    "chronomancer": "ХРОНОМАНТ",
}


_SKILL_NAMES_RU = {
    "acrobatics": "Акробатика",
    "adept": "Архимаг",
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
    "antimagic_net": "Сеть против магии",
    "arcane_blast": "Магический взрыв",
    "bow_master": "Мастер лучник",
    "catalyst_master": "Мастер катализаторов",
    "curse": "Проклятье",
    "dagger_master": "Эксперт по кинжалам",
    "dance_of_blades": "Танец клинков",
    "double_cast": "Двойное заклинание",
    "fireball": "Огненный шар",
    "instrument_master": "Мастер инструментов",
    "mage_armor": "Доспехи мага",
    "magic_darts": "Магические дротики",
    "mana_shield": "Щит маны",
    "marksman": "Снайпер",
    "shield_master": "Король щитов",
    "staff_master": "Мастер посоха",
    "wall_of_force": "Стена силы",
    "wand_master": "Мастер палочки",
}


_SKILL_RARITIES = {
    "usual": {
        "acrobatics",
        "arcane_blast",
        "axe_master",
        "bow_master",
        "catalyst_master",
        "cleave",
        "dagger_master",
        "eagle_eyes",
        "fast_learner",
        "instrument_master",
        "mace_master",
        "mage_armor",
        "magic_darts",
        "maintenance",
        "on_guard",
        "perforate",
        "shield_master",
        "smite",
        "spear_master",
        "staff_master",
        "sturdy",
        "sword_master",
        "wand_master",
    },
    "rare": {
        "all_natural",
        "antimagic_net",
        "caltrops",
        "curse",
        "deadly_criticals",
        "deception",
        "extra_conditioning",
        "fast_healer",
        "fireball",
        "flame_brand",
        "juggernaut",
        "power_attack",
        "shining_blade",
        "sunder",
        "telling_blows",
        "thick_skin",
        "throw_daggers",
        "toughness",
        "wall_of_force",
    },
    "epic": {
        "adept",
        "battering_blows",
        "blurred_movement",
        "dance_of_blades",
        "death_dealer",
        "double_cast",
        "extended_warranty",
        "extra_plating",
        "impervious",
        "mana_shield",
        "marksman",
        "perfect_form",
        "super_genius",
        "survivor",
        "warlord",
        "whirlwind_attack",
    },
}


def _rarity_for(skill_id: str) -> str:
    matches = [rarity for rarity, skill_ids in _SKILL_RARITIES.items() if skill_id in skill_ids]
    if len(matches) != 1:
        raise ValueError(f"Skill {skill_id!r} must have exactly one rarity, got {matches}")
    return matches[0]


SKILLS: Dict[str, SkillDefinition] = {
    skill_id: SkillDefinition(
        id=skill_id,
        name_ru=name_ru,
        rarity=_rarity_for(skill_id),
    )
    for skill_id, name_ru in _SKILL_NAMES_RU.items()
}
