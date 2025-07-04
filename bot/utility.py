import os
from typing import Optional, Tuple

import cv2
import numpy as np


def pic_path(name: str) -> str:
    """Путь к шаблону изображения по имени."""
    return f"./bot/data/templates/{name}.png"


def save_cv_image(name: str, image, folder="./bot/data/"):
    """Сохраняет изображение (RGB) в указанную папку."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{name}.png")
    cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    print(f"✅ Сохранено: {path}")


def load_cv_image(name: str, folder="screenshots") -> np.ndarray:
    """Загружает RGB-изображение из файла."""
    path = os.path.join(folder, f"{name}.png")
    image_bgr = cv2.imread(path)
    if image_bgr is None:
        raise FileNotFoundError(f"Файл не найден: {path}")
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def color_filter(
    img: np.ndarray,
    rgb: Optional[Tuple[int, int, int]] = None,
    lower: Optional[Tuple[int, int, int]] = None,
    upper: Optional[Tuple[int, int, int]] = None,
) -> np.ndarray:
    """Применяет фильтр по RGB, возвращает маску и изображение."""
    if rgb is None and (lower is None or upper is None):
        raise ValueError("Необходимо указать либо rgb, либо lower и upper")
    if rgb is not None:
        r, g, b = rgb
        lower = np.array([max(r - 3, 0), max(g - 3, 0), max(b - 3, 0)])
        upper = np.array([min(r + 3, 255), min(g + 3, 255), min(b + 3, 255)])
    mask = cv2.inRange(img, lower, upper)
    return cv2.bitwise_and(img, img, mask=mask)
