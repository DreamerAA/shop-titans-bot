# trading.py

import time

import cv2

from bot.control.interaction import find, find_and_click
from bot.control.mouse import click_left, set_mouse_position
from bot.core.status import get_status
from bot.matching.matcher import find_dialog_box_pos
from bot.matching.ocr import (
    extract_avaliable_energy,
    extract_cost,
    extract_energy_for_lower_price,
    extract_energy_for_raise_price,
    extract_max_energy,
)
from bot.screen import get_screen_shot
from bot.settings import GameStatus, get_settings
from bot.utility import pic_path


def go_chat() -> bool:
    """Переходит в чат. Возвращает True при успехе, False при отказе."""
    if not find_and_click("chat"):
        return False

    if find("feilure"):
        if not find_and_click("deny"):
            raise RuntimeError("Не удалось закрыть диалог отказа от чата.")
        return False

    return True


def step_trading():
    """
    Один шаг торгового цикла: оценка диалога, принятие решения,
    клик по нужной кнопке.
    """
    status = get_status()
    if status != GameStatus.MAIN_WINDOW:
        print("Current status is ", status)
        raise RuntimeError("Not in main window, cannot start trading")

    screen = get_screen_shot()
    dialog_template_rgba = cv2.imread(pic_path("dialog_template"), cv2.IMREAD_UNCHANGED)
    dialog_pos = find_dialog_box_pos(screen, dialog_template_rgba, threshold=0.6)
    if dialog_pos is None:
        print("❗️ No dialog found, skipping trading step.")
        return

    set_mouse_position(dialog_pos)
    click_left()
    time.sleep(get_settings().wt_click_sec)

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
            if find_and_click("deny") is None:
                raise RuntimeError("Не удалось закрыть диалог отказа от пополнения товаров.")
            status = get_status()
            continue
        if status == GameStatus.SPECIAL_OFFER_DIALOG:
            if find_and_click("close") is None:
                raise RuntimeError("Не удалось закрыть диалог специального предложения.")
            status = get_status()
            continue

        if status == GameStatus.BUY_DIALOG:
            if find_and_click("chat") is None:
                raise RuntimeError("Не удалось открыть чат в диалоге покупки.")
            if find_and_click("buy") is None:
                raise RuntimeError("Не удалось кликнуть по кнопке покупки в диалоге покупки.")
            status = get_status()
            continue

        # Расскомментируй если не хочешь продавать свои товары
        # if find_and_click("deny") is None:
        #    raise RuntimeError("Не удалось закрыть диалог отказа от продажи.")
        # status = get_status()
        # continue

        if find("series"):
            if find_and_click("chat") is None:
                raise RuntimeError("Не удалось открыть чат в диалоге серии.")
            if find_and_click("sell") is None:
                raise RuntimeError("Не удалось кликнуть по кнопке продажи в диалоге серии.")
            status = get_status()
            continue

        cost = extract_cost()
        avaliable_energy = get_avaliable_energy()

        if cost < 400_000:
            energy_lower = extract_energy_for_lower_price()
            print("⬇️ Energy for lower price:", energy_lower)
            if energy_lower + avaliable_energy > max_energy:
                if find_and_click("deny") is None:
                    raise RuntimeError("Не удалось закрыть диалог отказа от понижения цены.")
                status = get_status()
                continue

            if not go_chat():
                status = get_status()
                continue

            if find("success") is None:
                raise RuntimeError("Не удалось найти сообщение об успешном понижении цены.")
            avaliable_energy = get_avaliable_energy()

            if energy_lower + avaliable_energy > max_energy:
                if find_and_click("deny") is None:
                    raise RuntimeError("Не удалось закрыть диалог отказа от понижения цены.")
                status = get_status()
                continue

            if find_and_click("lower_price") is None:
                raise RuntimeError("Не удалось кликнуть по кнопке понижения цены.")
        elif cost < 500_000:
            if not go_chat():
                status = get_status()
                continue
            if find("success") is None:
                raise RuntimeError("Не удалось найти сообщение об успешном повышении цены.")

        else:  # cost >= 500_000
            energy_raise = extract_energy_for_raise_price()
            print("⬆️ Energy for raise price:", energy_raise)

            if energy_raise > avaliable_energy:
                if find_and_click("deny") is None:
                    raise RuntimeError("Не удалось закрыть диалог отказа от повышения цены.")
                status = get_status()
                continue

            if not go_chat():
                status = get_status()
                continue

            if find("success") is None:
                raise RuntimeError("Не удалось найти сообщение об успешном повышении цены.")
            if find_and_click("raise_price_avaliable") is None:
                raise RuntimeError("Не удалось кликнуть по кнопке повышения цены.")

        if find_and_click("sell") is None:
            raise RuntimeError("Не удалось кликнуть по кнопке продажи.")
        status = get_status()
