"""Window-scoped input for the hiring workflow."""

import time
from dataclasses import dataclass
from typing import Tuple

from pynput.mouse import Button, Controller

from bot.hiring.capture import WindowFrame
from bot.windowing import WindowLocator


class UnsafeInputError(RuntimeError):
    """Raised when a requested click cannot be tied safely to the game window."""


@dataclass(frozen=True)
class ClickResult:
    client_point: Tuple[int, int]
    desktop_point: Tuple[int, int]


@dataclass(frozen=True)
class DragResult:
    client_start: Tuple[int, int]
    client_end: Tuple[int, int]
    desktop_start: Tuple[int, int]
    desktop_end: Tuple[int, int]


class WindowInput:
    """Translate client coordinates and click only after focusing the game."""

    def __init__(
        self,
        locator: WindowLocator,
        mouse: Controller = None,
        method: str = "window_message",
    ):
        self.locator = locator
        self.mouse = mouse or Controller()
        self.method = method

    def click(self, frame: WindowFrame, client_point: Tuple[int, int]) -> ClickResult:
        self._validate_client_point(frame, client_point)

        if self.method == "window_message":
            current = self.locator.post_client_click(frame.window, client_point)
            return ClickResult(
                client_point=client_point,
                desktop_point=current.client_rect.to_desktop(client_point),
            )
        if self.method != "foreground_mouse":
            raise UnsafeInputError(f"Unsupported input method: {self.method}")

        current = self.locator.activate(frame.window)
        desktop_point = current.client_rect.to_desktop(client_point)
        original_position = self.mouse.position
        try:
            self._move_and_verify(desktop_point)
            self.mouse.press(Button.left)
            time.sleep(0.08)
            self.mouse.release(Button.left)
        finally:
            time.sleep(0.1)
            self.mouse.position = original_position
        return ClickResult(client_point=client_point, desktop_point=desktop_point)

    def drag(
        self,
        frame: WindowFrame,
        client_start: Tuple[int, int],
        client_end: Tuple[int, int],
        duration: float = 0.5,
    ) -> DragResult:
        """Perform a bounded foreground drag inside the verified game client."""

        self._validate_client_point(frame, client_start)
        self._validate_client_point(frame, client_end)
        if self.method != "foreground_mouse":
            raise UnsafeInputError("Dragging requires the 'foreground_mouse' input method")
        if duration <= 0:
            raise UnsafeInputError("Drag duration must be greater than zero")

        current = self.locator.activate(frame.window)
        desktop_start = current.client_rect.to_desktop(client_start)
        desktop_end = current.client_rect.to_desktop(client_end)
        original_position = self.mouse.position
        pressed = False
        try:
            self._move_and_verify(desktop_start)
            self.mouse.press(Button.left)
            pressed = True
            steps = max(2, round(duration / 0.02))
            for step in range(1, steps + 1):
                fraction = step / steps
                self.mouse.position = (
                    round(desktop_start[0] + (desktop_end[0] - desktop_start[0]) * fraction),
                    round(desktop_start[1] + (desktop_end[1] - desktop_start[1]) * fraction),
                )
                time.sleep(duration / steps)
            self._verify_position(desktop_end)
        finally:
            if pressed:
                self.mouse.release(Button.left)
            time.sleep(0.1)
            self.mouse.position = original_position

        return DragResult(
            client_start=client_start,
            client_end=client_end,
            desktop_start=desktop_start,
            desktop_end=desktop_end,
        )

    @staticmethod
    def _validate_client_point(frame: WindowFrame, client_point: Tuple[int, int]) -> None:
        x, y = client_point
        if not (0 <= x < frame.client_rect.width and 0 <= y < frame.client_rect.height):
            raise UnsafeInputError(
                f"Client point lies outside the captured game frame: {client_point}"
            )

    def _move_and_verify(self, desktop_point: Tuple[int, int]) -> None:
        actual_position = None
        for _attempt in range(3):
            self.mouse.position = desktop_point
            time.sleep(0.1)
            actual_position = self.mouse.position
            if self._positions_match(actual_position, desktop_point):
                return
        raise UnsafeInputError(
            f"Windows moved the cursor to {actual_position}, expected {desktop_point} "
            "after three attempts"
        )

    @staticmethod
    def _positions_match(actual_position, desktop_point: Tuple[int, int]) -> bool:
        return bool(
            actual_position is not None
            and abs(actual_position[0] - desktop_point[0]) <= 2
            and abs(actual_position[1] - desktop_point[1]) <= 2
        )

    def _verify_position(self, desktop_point: Tuple[int, int]) -> None:
        actual_position = self.mouse.position
        if not self._positions_match(actual_position, desktop_point):
            raise UnsafeInputError(
                f"Windows moved the cursor to {actual_position}, expected {desktop_point}"
            )
