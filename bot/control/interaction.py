# interaction.py
# для find, find_and_click — взаимодействие с экраном на уровне поиска

import time

from bot.control.mouse import click_left, set_mouse_position
from bot.matching.matcher import find_template
from bot.matching.ocr import find_text_position
from bot.screen import get_screen_shot
from bot.settings import get_settings
from bot.utility import pic_path


def find(data: str, method: str = "template", **kwargs):
    screen = get_screen_shot(get_settings().monitor)
    if method == "template":
        return find_template(screen, pic_path(data), **kwargs)
    elif method == "ocr":
        return find_text_position(screen, data)


def find_and_click(data: str, method: str = "template", **kwargs):
    pos = find(data, method, **kwargs)
    if pos is not None:
        set_mouse_position(pos)
        click_left()
        time.sleep(get_settings().wt_click_sec)
        print("FOUNDED:", data)
    else:
        print("NOT FOUNDED:", data)
    return pos


def to_main():
    set_mouse_position((1920, 200))
    click_left()
