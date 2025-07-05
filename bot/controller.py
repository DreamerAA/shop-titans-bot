import threading


class BotController:
    def __init__(self):
        self._should_stop = threading.Event()
        self._exception_callback = None

    def stop(self):
        self._should_stop.set()

    def should_stop(self):
        return self._should_stop.is_set()

    def set_exception_callback(self, func):
        self._exception_callback = func

    def notify_exception(self, exc: Exception):
        if self._exception_callback:
            self._exception_callback(exc)
