"""Configuration loading and validation for hero hiring."""

from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Mapping, Optional, Union

import yaml

from bot.hiring.catalog import HERO_CLASSES, SKILLS


class HiringConfigError(ValueError):
    """Raised when hiring configuration is unsafe or inconsistent."""


@dataclass(frozen=True)
class HiringLimits:
    max_gold_spent: int
    max_attempts: int = 100


@dataclass(frozen=True)
class WindowConfig:
    process_name: str = "ShopTitan.exe"
    title_contains: Optional[str] = "Shop Titans"
    capture_method: str = "desktop"
    input_method: str = "foreground_mouse"
    min_client_width: int = 640
    min_client_height: int = 480


@dataclass(frozen=True)
class HiringConfig:
    window: WindowConfig
    category: str
    hero_class: str
    allowed_skills: FrozenSet[str]
    limits: HiringLimits


def _require_mapping(value, path: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise HiringConfigError(f"'{path}' must be a YAML mapping")
    return value


def _require_string(value, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HiringConfigError(f"'{path}' must be a non-empty string")
    return value.strip()


def _require_non_negative_int(value, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HiringConfigError(f"'{path}' must be a non-negative integer")
    return value


def _require_positive_int(value, path: str) -> int:
    value = _require_non_negative_int(value, path)
    if value == 0:
        raise HiringConfigError(f"'{path}' must be greater than zero")
    return value


def _parse_allowed_skills(value) -> FrozenSet[str]:
    if not isinstance(value, list) or not value:
        raise HiringConfigError("'hiring.allowed_skills' must be a non-empty list")
    if any(not isinstance(skill, str) or not skill.strip() for skill in value):
        raise HiringConfigError("Every value in 'hiring.allowed_skills' must be a string")

    normalized = frozenset(skill.strip().lower() for skill in value)
    unknown = sorted(normalized.difference(SKILLS))
    if unknown:
        available = ", ".join(sorted(SKILLS))
        raise HiringConfigError(
            f"Unknown hiring skill(s): {', '.join(unknown)}. Available skills: {available}"
        )
    return normalized


def parse_hiring_config(data: Mapping) -> HiringConfig:
    """Validate already loaded YAML data and return an immutable config."""

    root = _require_mapping(data, "root")
    window_data = _require_mapping(root.get("window", {}), "window")
    hiring = _require_mapping(root.get("hiring"), "hiring")

    title_contains = window_data.get("title_contains", "Shop Titans")
    if title_contains is not None:
        title_contains = _require_string(title_contains, "window.title_contains")
    window = WindowConfig(
        process_name=_require_string(
            window_data.get("process_name", "ShopTitan.exe"), "window.process_name"
        ),
        title_contains=title_contains,
        capture_method=_require_string(
            window_data.get("capture_method", "desktop"), "window.capture_method"
        ).lower(),
        input_method=_require_string(
            window_data.get("input_method", "foreground_mouse"), "window.input_method"
        ).lower(),
        min_client_width=_require_positive_int(
            window_data.get("min_client_width", 640), "window.min_client_width"
        ),
        min_client_height=_require_positive_int(
            window_data.get("min_client_height", 480), "window.min_client_height"
        ),
    )
    if window.capture_method not in {"window", "desktop"}:
        raise HiringConfigError("'window.capture_method' must be either 'window' or 'desktop'")

    category = _require_string(hiring.get("category"), "hiring.category").lower()
    if category not in HERO_CLASSES:
        raise HiringConfigError(
            f"Unknown hero category: {category!r}. Available categories: "
            f"{', '.join(sorted(HERO_CLASSES))}"
        )
    if window.input_method not in {"foreground_mouse", "window_message"}:
        raise HiringConfigError(
            "'window.input_method' must be either 'foreground_mouse' or 'window_message'"
        )

    hero_class = _require_string(hiring.get("class"), "hiring.class").lower()
    if hero_class not in HERO_CLASSES[category]:
        raise HiringConfigError(
            f"Hero class {hero_class!r} does not belong to category {category!r}. "
            f"Available classes: {', '.join(HERO_CLASSES[category])}"
        )

    allowed_skills = _parse_allowed_skills(hiring.get("allowed_skills"))
    limits_data = _require_mapping(hiring.get("limits", {}), "hiring.limits")
    limits = HiringLimits(
        max_gold_spent=_require_non_negative_int(
            limits_data.get("max_gold_spent"), "hiring.limits.max_gold_spent"
        ),
        max_attempts=_require_positive_int(
            limits_data.get("max_attempts", 100), "hiring.limits.max_attempts"
        ),
    )

    return HiringConfig(
        window=window,
        category=category,
        hero_class=hero_class,
        allowed_skills=allowed_skills,
        limits=limits,
    )


def load_hiring_config(path: Union[str, Path]) -> HiringConfig:
    """Load and validate a hiring YAML file before any game interaction."""

    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
    except FileNotFoundError as exc:
        raise HiringConfigError(f"Hiring config not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise HiringConfigError(f"Invalid YAML in hiring config {config_path}: {exc}") from exc

    return parse_hiring_config(data)
