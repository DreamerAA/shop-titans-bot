import threading


class BotController:
    def __init__(self, config_path: str):
        self._game_is_running = False
        self._should_stop = threading.Event()
        self._should_start = threading.Event()
        self._exception_callback = None
        self.config_path = config_path

    def set_game_running(self, running: bool):
        self._game_is_running = running

    def is_game_running(self):
        return self._game_is_running

    def stop(self):
        self._should_stop.set()

    def start(self):
        self._should_stop.clear()
        self._should_start.set()

    def should_stop(self):
        return self._should_stop.is_set()

    def should_start(self):
        return self._should_start.is_set()

    def set_exception_callback(self, func):
        self._exception_callback = func

    def notify_exception(self, exc: Exception):
        if self._exception_callback:
            self._exception_callback(exc)
