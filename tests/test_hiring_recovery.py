import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from bot.hiring.recovery import RecoveryRunner, UnsafeRecoveryError
from bot.hiring.state import HiringScreen, ScreenDetection


class StaticDetector:
    def __init__(self, detection):
        self.detection = detection

    def detect(self, _):
        return self.detection


class RecoveryPolicyTests(unittest.TestCase):
    def test_refuses_non_recovery_action_before_click(self):
        detection = ScreenDetection(
            screen=HiringScreen.MAIN,
            suggested_action="characters",
        )
        frame = SimpleNamespace(image=None, window=object())
        capture = SimpleNamespace(capture=lambda _: frame)
        window_input = SimpleNamespace(click=Mock())
        runner = RecoveryRunner(capture, StaticDetector(detection), window_input)

        with self.assertRaisesRegex(UnsafeRecoveryError, "no allowed recovery"):
            runner.recover_once(frame.window)

        window_input.click.assert_not_called()


if __name__ == "__main__":
    unittest.main()
