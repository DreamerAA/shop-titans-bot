# ocr.py

import re
from typing import List, Tuple

import numpy as np

from bot.screen import get_region_from_screen, get_screen_shot
from bot.settings import get_settings
from bot.utility import color_filter


def find_text_position(screen: np.ndarray, target_texts: str | List[str]) -> Tuple[int, int] | None:
    """Ищет позицию текста на изображении, используя EasyOCR."""
    if isinstance(target_texts, str):
        target_texts = [target_texts]

    def no_cyrillic(text: str) -> bool:
        return re.search(r"[а-яА-ЯёЁ]", text) is None

    results = get_settings().ru_reader.readtext(screen)

    for bbox, text, confidence in results:
        if no_cyrillic(text):
            continue
        text = text.replace("@", "О")
        for target in target_texts:
            if target.lower() in text.lower():
                x = int(sum(p[0] for p in bbox) / 4)
                y = int(sum(p[1] for p in bbox) / 4)
                return (x, y)

    return None


def extract_number_with_commas(
    screen: np.ndarray,
    preprocess_func=None,
) -> List[Tuple[str, Tuple[int, int], float]]:
    """Извлекает числа, используя английский OCR.
    Поддерживает запятые и дроби."""
    processed = preprocess_func(screen) if preprocess_func else screen
    results = get_settings().en_reader.readtext(processed)

    pattern = re.compile(r"^[+-]?\d{1,3}(,\d{3})*(/\d{1,3}(,\d{3})*)?$|^-?\d+(\/\d+)?$")
    numbers = []

    for bbox, text, confidence in results:
        clean = (
            text.replace("O", "0")
            .replace("О", "0")
            .replace(" ", "")
            .replace("-", "")
            .replace("+", "")
            .replace(",", "")
            .replace("'", "")
            .replace("`", "")
            .replace("~", "")
        )
        if not pattern.match(clean):
            continue
        x = int(sum(p[0] for p in bbox) / 4)
        y = int(sum(p[1] for p in bbox) / 4)
        numbers.append((clean, (x, y), confidence))

    return numbers


def extract_cost() -> int:
    """Извлекает стоимость из области cost_borders."""
    settings = get_settings()
    screen = get_screen_shot()
    region = get_region_from_screen(screen, settings.cost_borders)
    filtered = color_filter(region, settings.rgb_cost)
    result = extract_number_with_commas(filtered)
    if len(result) != 1:
        raise ValueError("Не удалось извлечь стоимость, результат: " + str(result))
    return int(result[0][0])


def extract_avaliable_energy() -> int:
    """Извлекает доступную энергию (до слэша)."""
    settings = get_settings()
    screen = get_screen_shot()
    region = get_region_from_screen(screen, settings.energy_borders)
    result = extract_number_with_commas(
        region, preprocess_func=lambda x: color_filter(x, settings.rgb_energy)
    )
    if len(result) != 1:
        raise ValueError("Не удалось извлечь доступную энергию, результат: " + str(result))
    return int(result[0][0].split("/")[0])


def extract_max_energy() -> int:
    """Извлекает максимальную энергию (после слэша)."""

    settings = get_settings()
    screen = get_screen_shot()
    region = get_region_from_screen(screen, settings.energy_borders)
    result = extract_number_with_commas(
        region, preprocess_func=lambda x: color_filter(x, settings.rgb_energy)
    )
    if len(result) != 1:
        raise ValueError("Не удалось извлечь максимальную энергию, результат: " + str(result))

    return int(result[0][0].split("/")[1])


def extract_energy_for_price(borders, rgb_1, rgb_2=None) -> int:
    """
    Извлекает числовое значение энергии из указанной области экрана с применением цветового фильтра.
    Если указаны два цвета — сравнивает по уверенности.
    """
    screen = get_screen_shot()
    region = get_region_from_screen(screen, borders)

    if rgb_2 is None or rgb_1 == rgb_2:
        results = extract_number_with_commas(
            region, preprocess_func=lambda x: color_filter(x, rgb_1)
        )
    else:
        res1 = extract_number_with_commas(region, preprocess_func=lambda x: color_filter(x, rgb_1))
        res2 = extract_number_with_commas(region, preprocess_func=lambda x: color_filter(x, rgb_2))
        results = res1 + res2

    if not results:
        raise ValueError("Не удалось извлечь энергию для цены")
    best = max(results, key=lambda r: r[2])  # по confidence
    return int(best[0])


def extract_energy_for_raise_price() -> int:
    settings = get_settings()
    return extract_energy_for_price(
        settings.raise_borders, settings.rgb_raise_unav, settings.rgb_raise_av
    )


def extract_energy_for_lower_price() -> int:
    settings = get_settings()
    return extract_energy_for_price(settings.lower_borders, settings.rgb_lower)
