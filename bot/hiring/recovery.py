"""Conservative one-step recovery from known blocking screens."""

import time
from dataclasses import dataclass

from bot.hiring.capture import WindowCapture, WindowFrame
from bot.hiring.input import ClickResult, WindowInput
from bot.hiring.state import HiringStateDetector, ScreenDetection
from bot.windowing import GameWindow


class UnsafeRecoveryError(RuntimeError):
    """Raised instead of clicking when recovery cannot be verified twice."""


@dataclass(frozen=True)
class RecoveryResult:
    before: ScreenDetection
    after: ScreenDetection
    after_frame: WindowFrame
    click: ClickResult


class RecoveryRunner:
    def __init__(
        self,
        capture: WindowCapture,
        detector: HiringStateDetector,
        window_input: WindowInput,
        wait_after_click: float = 1.0,
        allowed_actions=frozenset({"close", "reconnect"}),
    ):
        self.capture = capture
        self.detector = detector
        self.window_input = window_input
        self.wait_after_click = wait_after_click
        self.allowed_actions = frozenset(allowed_actions)

    def recover_once(self, window: GameWindow) -> RecoveryResult:
        verification_frame = self.capture.capture(window)
        before = self.detector.detect(verification_frame.image)
        action = before.suggested_action
        if action not in self.allowed_actions or before.evidence is None:
            raise UnsafeRecoveryError(
                f"State {before.screen.value!r} has no allowed recovery action"
            )

        # A second fresh frame prevents a click based on stale UI coordinates.
        fresh_frame = self.capture.capture(verification_frame.window)
        fresh = self.detector.detect(fresh_frame.image)
        if fresh.screen != before.screen or fresh.suggested_action != action:
            raise UnsafeRecoveryError(
                "Game state changed while verifying recovery; no click was performed"
            )
        if fresh.evidence is None:
            raise UnsafeRecoveryError("Recovery target disappeared before the click")

        click = self.window_input.click(fresh_frame, fresh.evidence.center)
        deadline = time.monotonic() + max(5.0, self.wait_after_click)
        while True:
            time.sleep(self.wait_after_click)
            after_frame = self.capture.capture(fresh_frame.window)
            after = self.detector.detect(after_frame.image)
            if after.screen != before.screen or after.suggested_action != action:
                return RecoveryResult(
                    before=before,
                    after=after,
                    after_frame=after_frame,
                    click=click,
                )
            if time.monotonic() >= deadline:
                raise UnsafeRecoveryError(
                    f"Recovery click was sent, but state remained {before.screen.value!r}"
                )
