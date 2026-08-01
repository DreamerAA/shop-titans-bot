"""Win32 game-window discovery without external dependencies."""

import ctypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class WindowNotFoundError(RuntimeError):
    """Raised when no suitable game window can be found."""


@dataclass(frozen=True)
class ClientRect:
    """Client-area rectangle expressed in desktop coordinates."""

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def to_desktop(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """Translate a client-relative point into desktop coordinates."""

        x, y = point
        return self.left + x, self.top + y

    def to_client(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """Translate a desktop point into client-relative coordinates."""

        x, y = point
        return x - self.left, y - self.top

    def as_mss_monitor(self) -> Dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class GameWindow:
    handle: int
    process_id: int
    process_name: Optional[str]
    title: str
    window_rect: ClientRect
    client_rect: ClientRect
    is_minimized: bool


if sys.platform == "win32":
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _ENUM_WINDOWS_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    _user32.EnumWindows.argtypes = [_ENUM_WINDOWS_PROC, wintypes.LPARAM]
    _user32.EnumWindows.restype = wintypes.BOOL
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.IsWindowVisible.restype = wintypes.BOOL
    _user32.IsIconic.argtypes = [wintypes.HWND]
    _user32.IsIconic.restype = wintypes.BOOL
    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.GetWindowTextLengthW.restype = ctypes.c_int
    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetWindowTextW.restype = ctypes.c_int
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetClientRect.restype = wintypes.BOOL
    _user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetWindowRect.restype = wintypes.BOOL
    _user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    _user32.ClientToScreen.restype = wintypes.BOOL

    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL


def enable_dpi_awareness() -> None:
    """Best-effort per-monitor DPI awareness for correct Win32 coordinates."""

    if sys.platform != "win32":
        return
    try:
        set_context = _user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = wintypes.BOOL
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        set_context(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            _user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


class WindowLocator:
    """Locate a visible top-level window belonging to the game process."""

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def __init__(
        self,
        process_name: str,
        title_contains: Optional[str] = None,
        min_client_width: int = 640,
        min_client_height: int = 480,
    ):
        if sys.platform != "win32":
            raise OSError("Shop Titans window discovery is supported only on Windows")
        self.process_name = self._normalize_process_name(process_name)
        self.title_contains = title_contains.casefold() if title_contains else None
        self.min_client_width = min_client_width
        self.min_client_height = min_client_height
        self._process_names: Dict[int, Optional[str]] = {}
        enable_dpi_awareness()

    @staticmethod
    def _normalize_process_name(process_name: str) -> str:
        name = Path(process_name).name.casefold()
        return name if name.endswith(".exe") else f"{name}.exe"

    def _get_process_name(self, process_id: int) -> Optional[str]:
        if process_id in self._process_names:
            return self._process_names[process_id]

        handle = _kernel32.OpenProcess(self._PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
        if not handle:
            self._process_names[process_id] = None
            return None
        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not _kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                result = None
            else:
                result = os.path.basename(buffer.value)
        finally:
            _kernel32.CloseHandle(handle)

        self._process_names[process_id] = result
        return result

    @staticmethod
    def _get_title(handle: int) -> str:
        length = _user32.GetWindowTextLengthW(handle)
        if length <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(handle, buffer, len(buffer))
        return buffer.value

    @staticmethod
    def _get_client_rect(handle: int) -> Optional[ClientRect]:
        rect = wintypes.RECT()
        if not _user32.GetClientRect(handle, ctypes.byref(rect)):
            return None
        origin = wintypes.POINT(0, 0)
        if not _user32.ClientToScreen(handle, ctypes.byref(origin)):
            return None
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return None
        return ClientRect(left=origin.x, top=origin.y, width=width, height=height)

    @staticmethod
    def _get_window_rect(handle: int) -> Optional[ClientRect]:
        rect = wintypes.RECT()
        if not _user32.GetWindowRect(handle, ctypes.byref(rect)):
            return None
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return None
        return ClientRect(left=rect.left, top=rect.top, width=width, height=height)

    def list_windows(self) -> List[GameWindow]:
        windows: List[GameWindow] = []
        callback_errors: List[BaseException] = []

        @_ENUM_WINDOWS_PROC
        def callback(handle, _):
            try:
                if not _user32.IsWindowVisible(handle):
                    return True
                process_id = wintypes.DWORD()
                _user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
                client_rect = self._get_client_rect(handle)
                window_rect = self._get_window_rect(handle)
                if client_rect is None or window_rect is None:
                    return True
                windows.append(
                    GameWindow(
                        handle=handle,
                        process_id=int(process_id.value),
                        process_name=self._get_process_name(int(process_id.value)),
                        title=self._get_title(handle),
                        window_rect=window_rect,
                        client_rect=client_rect,
                        is_minimized=bool(_user32.IsIconic(handle)),
                    )
                )
                return True
            except BaseException as exc:
                callback_errors.append(exc)
                return False

        enumeration_succeeded = _user32.EnumWindows(callback, 0)
        if callback_errors:
            raise OSError(f"Failed while inspecting a top-level window: {callback_errors[0]}")
        if not enumeration_succeeded:
            error = ctypes.get_last_error()
            raise OSError(error, "EnumWindows failed")
        return windows

    def find(self) -> GameWindow:
        candidates = []
        for window in self.list_windows():
            process_matches = (
                window.process_name is not None
                and self._normalize_process_name(window.process_name) == self.process_name
            )
            title_matches = self.title_contains and self.title_contains in window.title.casefold()
            if not process_matches and not title_matches:
                continue
            if window.client_rect.width < self.min_client_width:
                continue
            if window.client_rect.height < self.min_client_height:
                continue
            candidates.append(window)

        if not candidates:
            raise WindowNotFoundError(
                f"No visible window found for process {self.process_name!r} "
                f"with client area at least {self.min_client_width}x{self.min_client_height}"
            )

        candidates.sort(
            key=lambda window: (
                window.is_minimized,
                -(window.client_rect.width * window.client_rect.height),
            )
        )
        return candidates[0]

    def refresh(self, window: GameWindow) -> GameWindow:
        """Refresh geometry for a window that may have moved or resized."""

        for current in self.list_windows():
            if current.handle == window.handle:
                return current
        raise WindowNotFoundError(f"Game window no longer exists: handle={window.handle}")
