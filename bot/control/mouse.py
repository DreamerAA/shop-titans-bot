from typing import Tuple

from pynput.mouse import Button

from bot.settings import settings


def set_mouse_position(position: Tuple[int, int]):
    """Установить позицию мыши на экране."""
    settings.mouse.position = position


def get_mouse_position() -> Tuple[int, int]:
    """Получить текущую позицию мыши."""
    return settings.mouse.position


def click_left():
    """Сделать одиночный левый клик."""
    settings.mouse.click(Button.left, 1)


def click_right():
    """Сделать одиночный правый клик."""
    settings.mouse.click(Button.right, 1)


def double_click_left():
    """Сделать двойной левый клик."""
    settings.mouse.click(Button.left, 2)


def move_mouse(dx: int, dy: int):
    """Сместить мышь на заданное расстояние."""
    x, y = settings.mouse.position
    settings.mouse.position = (x + dx, y + dy)
