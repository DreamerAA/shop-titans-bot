import time
from logic.status import (
    check_reconnect,
    check_ending_cells,
    check_is_main_window,
    check_not_enough_resources,
)
from interaction import find_and_click, to_main
from mouse_control import set_mouse_position, click_left

from screen import get_screen_shot, get_region_from_screen, save_part_screen
from settings import settings
from utility import color_filter


def check_production_ready() -> bool:
    screen = get_screen_shot()
    part_screen = get_region_from_screen(screen, settings.ready_borders)
    result = color_filter(
        part_screen, upper=settings.rgb_ready_upper, lower=settings.rgb_ready_lower
    )
    results = settings.ru_reader.readtext(result)
    if len(results) != 1:
        return False
    result = results[0]
    rect, text, confidence = result
    text = text.lower().replace("0", "o")
    print(f"found text: {text}, confidence: {confidence}")
    if text != "готово":
        return False
    return True


def assemble_products() -> bool:
    """
    Забирает произведенные предметы из производственных ячеек.
    Возвращает True, если что-то было забрано.
    """
    was_click = False
    while check_production_ready():
        print("has ready production")
        set_mouse_position(settings.ready_position)
        click_left()
        time.sleep(1.0)

        while find_and_click("ok") is not None:
            print("click_on_ok", True)
        while find_and_click("take") is not None:
            print("click_on_take", True)
        if find_and_click("close") is not None:
            print("click_on_close", True)

        was_click = True
    print("hasnt ready production")
    return was_click


def set_one_production(names: list[str]):
    """
    Производит один из предметов из списка `names`.
    Последовательно проверяет доступность ресурсов и ячеек.
    """
    i = 0
    index = i % len(names)
    check_reconnect()
    assert find_and_click("create")

    if check_ending_cells():
        to_main()
        return

    blocked = {i: False for i in range(len(names))}

    while True:
        name = names[index]
        res = find_and_click(name)
        if res is None:
            if check_not_enough_resources():
                find_and_click("close")
                blocked[index] = True
                if all(blocked.values()):
                    break
                while blocked[index]:
                    i += 1
                    index = i % len(names)

            if check_is_main_window():
                break
    to_main()


def set_split_production(data: list[tuple[str, int]]):
    """
    Производит указанные предметы поштучно (несколько наименований).
    data — список кортежей (имя, количество).
    """
    assert find_and_click("create")

    for name, count in data:
        for _ in range(count):
            if check_ending_cells():
                to_main()
                return

            find_and_click(name)

            if check_not_enough_resources():
                find_and_click("close")
                break
