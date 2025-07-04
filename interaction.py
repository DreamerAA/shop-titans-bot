# interaction.py
# для find, find_and_click — взаимодействие с экраном на уровне поиска

from screen import get_screen_shot
from utility import pic_path
from matcher import find_template
from ocr import find_text_position
from settings import settings
from mouse_control import set_mouse_position, click_left
import time


def find(data: str, method: str = "template", **kwargs):
    screen = get_screen_shot(settings.monitor)
    if method == "template":
        return find_template(screen, pic_path(data), **kwargs)
    elif method == "ocr":
        return find_text_position(screen, data)


def find_and_click(data: str, method: str = "template", **kwargs):
    pos = find(data, method, **kwargs)
    if pos is not None:
        set_mouse_position(pos)
        click_left()
        time.sleep(1.5)
        print("FOUNDED:", data)
    else:
        print("NOT FOUNDED:", data)
    return pos


def to_main():
    set_mouse_position((1920, 200))
    click_left()
