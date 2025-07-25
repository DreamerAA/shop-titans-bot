from enum import Enum, auto
from itertools import count
from typing import Tuple

import easyocr
import mss
import yaml
from pynput.mouse import Controller


class GameStatus(Enum):
    MAIN_WINDOW = auto()
    SELL_DIALOG = auto()
    REFILL_DIALOG = auto()
    BUY_DIALOG = auto()
    SPECIAL_OFFER_DIALOG = auto()
    OTHER = auto()


class CounterWithCurrent:
    def __init__(self, start=0):
        self._counter = count(start)
        self.current = start - 1

    def next(self):
        self.current = next(self._counter)
        return self.current


class Cache:
    key_last_screen_shot: str = "last_screen_shot"

    def __init__(self):
        self._cache = {}

    def get(self, key, default=None):
        return self._cache.get(key, default)

    def set(self, key, value):
        self._cache[key] = value

    def remove(self, key):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()


class Settings:
    def __init__(self, config_path="configs/template.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self.cache = Cache()
        self.mouse = Controller()
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[cfg.get("monitor_index", 1)]

        self.ru_reader = easyocr.Reader(["ru"], gpu=True)
        self.en_reader = easyocr.Reader(["en"], gpu=True)

        self.energy_borders = tuple(cfg["regions"]["energy_borders"])
        self.cost_borders = tuple(cfg["regions"]["cost_borders"])
        self.raise_borders = tuple(cfg["regions"]["raise_borders"])
        self.lower_borders = tuple(cfg["regions"]["lower_borders"])
        self.ready_borders = tuple(cfg["regions"]["ready_borders"])

        colors = cfg.get("colors", {})
        self.rgb_ready_upper = tuple(colors["rgb_ready_upper"])
        self.rgb_ready_lower = tuple(colors["rgb_ready_lower"])
        self.rgb_raise_unav = tuple(colors["rgb_raise_unav"])
        self.rgb_raise_av = tuple(colors["rgb_raise_av"])
        self.rgb_lower = tuple(colors["rgb_lower"])
        self.rgb_cost = tuple(colors["rgb_cost"])
        self.rgb_energy = tuple(colors["rgb_energy"])

        # wt = wait time
        self.wt_cycle_min = cfg.get("wait_time_cycle_min", 2)
        self.wt_click_sec = cfg.get("wait_time_click_sec", 1.5)
        self.wt_reconnection_sec = cfg.get("wait_time_reconnection_sec", 15)
        self.wt_status_sec = cfg.get("wait_time_status_sec", 1.5)
        self.wt_production_sec = cfg.get("wait_time_production_sec", 1)

        self.cost_lower: float = cfg.get("cost_lower", 400_000)
        self.cost_same: float = cfg.get("cost_same", 500_000)

        self.telegram_token: str = cfg.get("telegram_token", None)
        self.allowed_user_id: int = cfg.get("allowed_user_id", None)

    @property
    def ready_position(self) -> Tuple[int, int]:
        x1, x2, y1, y2 = self.ready_borders
        return (x1 + x2) // 2, (y1 + y2) // 2

    def invalidate_screeenshot_cache(self):
        """Удалить кэш скриншота экрана."""
        self.cache.remove(self.cache.key_last_screen_shot)
        print("🗑️ Screenshot cache invalidated.")

    def save_screenshot_cache(self, img):
        """Сохранить скриншот в кэш."""
        self.cache.set(self.cache.key_last_screen_shot, img)
        print("🖼️ Screenshot cache updated.")

    def get_screenshot_cached(self):
        """Получить скриншот из кэша."""
        return self.cache.get(self.cache.key_last_screen_shot, None)


_settings_instance = None


def get_settings(config_path="config.yaml"):
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_path=config_path)
    return _settings_instance
