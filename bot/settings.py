import easyocr
from pynput.mouse import Controller
from enum import Enum, auto
from typing import Tuple
import mss
from itertools import count


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


class Settings:
    def __init__(self):
        self.mouse = Controller()
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[2]  # Dual-monitor setup assumed
        self.ru_reader = easyocr.Reader(["ru"], gpu=True)
        self.en_reader = easyocr.Reader(["en"], gpu=True)
        self.energy_borders = (2967, 3165, 72, 128)
        self.cost_borders = (825, 3000, 505, 660)
        self.raise_borders = (2669, 2800, 1015, 1085)
        self.lower_borders = (2590, 2690, 830, 895)
        self.ready_borders = (3346, 3532, 1854, 1902)

        self.rgb_ready_upper = (255, 242, 146)
        self.rgb_ready_lower = (250, 190, 20)
        self.rgb_raise_unav = (178, 178, 178)
        self.rgb_raise_av = (231, 104, 106)
        self.rgb_lower = (255, 255, 255)
        self.rgb_cost = (255, 210, 0)
        self.rgb_energy = (255, 255, 255)

    @property
    def ready_position(self) -> Tuple[int, int]:
        return (self.ready_borders[0] + self.ready_borders[1]) // 2, (
            self.ready_borders[2] + self.ready_borders[3]
        ) // 2


settings = Settings()
