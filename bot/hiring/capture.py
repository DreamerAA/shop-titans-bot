"""Capture frames from the located Shop Titans client area."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union

import cv2
import mss
import numpy as np
from PIL import ImageGrab

from bot.windowing import ClientRect, GameWindow, WindowLocator


class WindowCaptureError(RuntimeError):
    """Raised when a frame cannot be captured safely."""


@dataclass(frozen=True)
class WindowFrame:
    image: np.ndarray
    window: GameWindow
    captured_at: float

    @property
    def client_rect(self) -> ClientRect:
        return self.window.client_rect

    def to_desktop(self, point: Tuple[int, int]) -> Tuple[int, int]:
        return self.client_rect.to_desktop(point)

    def to_client(self, point: Tuple[int, int]) -> Tuple[int, int]:
        return self.client_rect.to_client(point)


class WindowCapture:
    def __init__(self, locator: WindowLocator, method: str = "window"):
        self.locator = locator
        self.method = method

    def capture(self, window: GameWindow) -> WindowFrame:
        current = self.locator.refresh(window)
        if current.is_minimized:
            raise WindowCaptureError("Game window is minimized")

        if self.method == "window":
            image = self._capture_window(current)
        elif self.method == "desktop":
            image = self._capture_desktop(current)
        else:
            raise WindowCaptureError(f"Unsupported capture method: {self.method}")
        if image.shape[:2] != (current.client_rect.height, current.client_rect.width):
            raise WindowCaptureError(
                "Captured frame size does not match the current game client rectangle"
            )
        return WindowFrame(image=image, window=current, captured_at=time.time())

    @staticmethod
    def _capture_desktop(window: GameWindow) -> np.ndarray:
        with mss.mss() as screenshotter:
            raw = screenshotter.grab(window.client_rect.as_mss_monitor())
        return cv2.cvtColor(np.asarray(raw), cv2.COLOR_BGRA2RGB)

    @staticmethod
    def _capture_window(window: GameWindow) -> np.ndarray:
        """Capture by HWND so overlapping windows do not leak into the frame."""

        direct = ImageGrab.grab(window=window.handle)
        image = np.asarray(direct.convert("RGB"))
        direct.close()

        client = window.client_rect
        outer = window.window_rect
        if image.shape[:2] == (client.height, client.width):
            return image
        if image.shape[:2] != (outer.height, outer.width):
            raise WindowCaptureError(
                "Direct window capture returned unexpected size: "
                f"{image.shape[1]}x{image.shape[0]}"
            )

        left = client.left - outer.left
        top = client.top - outer.top
        right = left + client.width
        bottom = top + client.height
        if left < 0 or top < 0 or right > image.shape[1] or bottom > image.shape[0]:
            raise WindowCaptureError("Client area lies outside the direct window capture")
        return image[top:bottom, left:right].copy()


def save_window_frame(frame: WindowFrame, path: Union[str, Path]) -> Path:
    """Save an RGB frame as PNG for diagnostics."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_bgr = cv2.cvtColor(frame.image, cv2.COLOR_RGB2BGR)
    if not cv2.imwrite(str(output_path), image_bgr):
        raise WindowCaptureError(f"Failed to save diagnostic frame: {output_path}")
    return output_path
