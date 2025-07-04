# trading.py

import time
import cv2
from bot.core.status import get_status
from bot.matching.ocr import (
    extract_cost,
    extract_avaliable_energy,
    extract_max_energy,
    extract_energy_for_raise_price,
    extract_energy_for_lower_price,
)
from bot.control.interaction import find_and_click, find
from bot.settings import GameStatus
from bot.screen import get_screen_shot
from bot.matching.matcher import find_dialog_box_pos
from bot.utility import pic_path
from bot.control.mouse import set_mouse_position, click_left


def go_chat() -> bool:
    """Переходит в чат. Возвращает True при успехе, False при отказе."""
    if not find_and_click("chat"):
        return False

    if find("feilure"):
        assert find_and_click("deny")
        return False

    return True


def step_trading():
    """Один шаг торгового цикла: оценка диалога, принятие решения, клик по нужной кнопке."""
    assert get_status() == GameStatus.MAIN_WINDOW

    screen = get_screen_shot()
    dialog_template_rgba = cv2.imread(pic_path("dialog_template"), cv2.IMREAD_UNCHANGED)
    dialog_pos = find_dialog_box_pos(screen, dialog_template_rgba, threshold=0.6)
    assert dialog_pos is not None

    set_mouse_position(dialog_pos)
    click_left()
    time.sleep(1.5)

    status = get_status()
    print("💬 Status:", status)
    max_energy = extract_max_energy()
    avaliable_energy = 0

    def get_avaliable_energy():
        avaliable_energy = extract_avaliable_energy()
        print(f"⚡ Avaliable energy: {avaliable_energy}/{max_energy}")
        return avaliable_energy

    while status in (
        GameStatus.SELL_DIALOG,
        GameStatus.REFILL_DIALOG,
        GameStatus.BUY_DIALOG,
        GameStatus.SPECIAL_OFFER_DIALOG,
    ):
        # TODO: refactoring - create StateMachine

        if status == GameStatus.REFILL_DIALOG:
            assert find_and_click("deny")
            status = get_status()
            continue
        if status == GameStatus.SPECIAL_OFFER_DIALOG:
            assert find_and_click("close")
            status = get_status()
            continue

        if status == GameStatus.BUY_DIALOG:
            assert find_and_click("chat")
            assert find_and_click("buy")
            status = get_status()
            continue

        # assert find_and_click("deny")
        # status = get_status()
        # continue

        if find("series"):
            assert find_and_click("chat")
            assert find_and_click("sell")
            status = get_status()
            continue

        cost = extract_cost()
        avaliable_energy = get_avaliable_energy()

        if cost < 400_000:
            energy_lower = extract_energy_for_lower_price()
            print("⬇️ Energy for lower price:", energy_lower)
            if energy_lower + avaliable_energy > max_energy:
                assert find_and_click("deny")
                status = get_status()
                continue

            if not go_chat():
                status = get_status()
                continue

            assert find("success")
            avaliable_energy = get_avaliable_energy()

            if energy_lower + avaliable_energy > max_energy:
                assert find_and_click("deny")
                status = get_status()
                continue

            assert find_and_click("lower_price")

        elif cost < 500_000:
            if not go_chat():
                status = get_status()
                continue
            assert find("success")

        else:  # cost >= 500_000
            energy_raise = extract_energy_for_raise_price()
            print("⬆️ Energy for raise price:", energy_raise)

            if energy_raise > avaliable_energy:
                assert find_and_click("deny")
                status = get_status()
                continue

            if not go_chat():
                status = get_status()
                continue

            assert find("success")
            assert find_and_click("raise_price_avaliable")

        assert find_and_click("sell")
        status = get_status()
