import unittest
from unittest.mock import Mock, patch

from bot.hiring.input import WindowInput


class RetryMouse:
    def __init__(self):
        self.actual = (0, 0)
        self.assignments = 0

    @property
    def position(self):
        return self.actual

    @position.setter
    def position(self, value):
        self.assignments += 1
        self.actual = (36, 0) if self.assignments == 1 else value


class WindowInputTests(unittest.TestCase):
    def test_retries_transient_cursor_repositioning(self):
        mouse = RetryMouse()
        window_input = WindowInput(Mock(), mouse=mouse, method="foreground_mouse")

        with patch("bot.hiring.input.time.sleep"):
            window_input._move_and_verify((-135, 736))

        self.assertEqual(2, mouse.assignments)
        self.assertEqual((-135, 736), mouse.position)


if __name__ == "__main__":
    unittest.main()
