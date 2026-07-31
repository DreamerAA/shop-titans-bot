# matcher.py

from typing import Optional, Tuple

import cv2
import numpy as np


def find_template(
    screen: np.ndarray, template_path: str, threshold: float = 0.8
) -> Tuple[int, int] | None:
    """Ищет шаблонное изображение на экране. Возвращает центр совпадения."""
    template_bgr = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template_bgr is None:
        raise FileNotFoundError(f"Template not found: {template_path}")
    template = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2RGB)

    w, h = template.shape[1], template.shape[0]
    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val < threshold:
        return None

    return (int(max_loc[0] + w / 2), int(max_loc[1] + h / 2))


def find_dialog_box_pos(
    screen: np.ndarray,
    dialog_template_rgba: np.ndarray,
    threshold: float = 0.8,
) -> Optional[Tuple[int, int]]:
    """Ищет позицию диалогового окна по маске"""
    """альфа-канала с масштабированием."""
    bgr_template = dialog_template_rgba[:, :, :3]
    alpha_mask = dialog_template_rgba[:, :, 3]
    mask = (alpha_mask > 128).astype(np.uint8) * 255

    scales = [0.8, 0.9, 1.0, 1.1, 1.2]
    best_val = 0
    best_pos = None

    for scale in scales:
        resized_template = cv2.resize(bgr_template, None, fx=scale, fy=scale)
        resized_mask = cv2.resize(
            mask,
            (resized_template.shape[1], resized_template.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

        res = cv2.matchTemplate(screen, resized_template, cv2.TM_CCOEFF_NORMED, mask=resized_mask)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val > best_val:
            best_val = max_val
            best_pos = max_loc

    if best_val < threshold or best_pos is None:
        return None

    w, h = dialog_template_rgba.shape[1], dialog_template_rgba.shape[0]
    return (int(best_pos[0] + w / 2), int(best_pos[1] + h / 2))
