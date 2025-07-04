# status.py

import time

from bot.control.interaction import find, find_and_click
from bot.settings import GameStatus, settings


def check_is_main_window() -> bool:
    """Проверка, открыт ли главный экран (по кнопке 'create')."""
    return find("create") is not None


def check_not_enough_resources() -> bool:
    """Проверка сообщения о нехватке ресурсов."""
    return find("not_enough") is not None


def check_ending_cells() -> bool:
    """Проверка, что ячейки производства закончились."""
    return find("ending_cell") is not None


def check_reconnect():
    """Цикл переподключения при разрыве соединения."""
    pos = find_and_click("reconnect")
    while find("create") is None and pos is not None:
        print("🔁 Переподключение...")
        time.sleep(settings.wt_reconnection_sec)
        pos = find_and_click("reconnect")
    if not (find("create") is not None or find("reconnect") is None):
        raise RuntimeError("Не удалось переподключиться. Проверьте соединение с интернетом.")


def get_status() -> GameStatus:
    """Определяет текущее состояние интерфейса игры."""
    time.sleep(settings.wt_status_sec)  # Задержка для стабильности определения статуса
    if check_is_main_window():
        return GameStatus.MAIN_WINDOW
    if find("special_offer"):
        return GameStatus.SPECIAL_OFFER_DIALOG
    if find("sell") and find("deny"):
        return GameStatus.SELL_DIALOG
    if find("refill") and find("deny"):
        return GameStatus.REFILL_DIALOG
    if find("buy") and find("deny"):
        return GameStatus.BUY_DIALOG
    return GameStatus.OTHER
