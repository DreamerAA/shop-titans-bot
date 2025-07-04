import cv2
import mss
import numpy as np

from bot.settings import get_settings


def get_screen_shot(monitor=None) -> np.ndarray:
    """Сделать скриншот с экрана и вернуть RGB-массив."""
    monitor = monitor or get_settings().monitor
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB)


def get_region_from_screen(screen: np.ndarray, borders: tuple) -> np.ndarray:
    """Вернуть выделенную область по заданным границам (x1, x2, y1, y2)."""
    x1, x2, y1, y2 = borders
    return screen[y1:y2, x1:x2]


def save_part_screen(borders: tuple, name: str):
    """Сохранить участок экрана в файл."""
    screen = get_screen_shot()
    region = get_region_from_screen(screen, borders)
    from utility import save_cv_image  # отложенный импорт

    save_cv_image(name, region)
