"""Stateful end-to-end hero hiring workflow."""

import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from bot.hiring.capture import WindowCapture, WindowFrame
from bot.hiring.catalog import HERO_CATEGORY_NAMES_RU, HERO_CLASS_NAMES_RU, HERO_CLASSES
from bot.hiring.checkpoint import HiringCheckpointStore
from bot.hiring.config import HiringConfig
from bot.hiring.hero_cards import HeroCardFinder, HeroCardMatch
from bot.hiring.input import WindowInput
from bot.hiring.ocr import ActionDialogNameReader, GoldCostReader, HiringPanelReader, OCRTextMatch
from bot.hiring.skills import SkillAnalysis, SkillRecognizer
from bot.hiring.state import HiringScreen, HiringStateDetector, ScreenDetection
from bot.hiring.vision import TemplateMatch
from bot.windowing import GameWindow


class HiringWorkflowError(RuntimeError):
    """Raised when the workflow cannot continue without an unsafe assumption."""


@dataclass(frozen=True)
class HiringWorkflowResult:
    hero_name: str
    attempts: int
    gold_spent: int
    skills: Tuple[str, str]


class HiringWorkflow:
    """Run the verified hiring loop until both random skills are allowed."""

    def __init__(
        self,
        config: HiringConfig,
        capture: WindowCapture,
        detector: HiringStateDetector,
        window_input: WindowInput,
        event: Callable[[str], None] = print,
        checkpoint_store: Optional[HiringCheckpointStore] = None,
    ):
        self.config = config
        self.capture = capture
        self.detector = detector
        self.window_input = window_input
        self.event = event
        self.card_finder = HeroCardFinder()
        self.skill_recognizer = SkillRecognizer()
        self.action_name_reader = ActionDialogNameReader()
        self.hiring_panel_reader = HiringPanelReader()
        self.gold_cost_reader = GoldCostReader()
        self.checkpoint_store = checkpoint_store or HiringCheckpointStore(config)
        checkpoint = self.checkpoint_store.load()
        self.attempts = checkpoint.attempts if checkpoint else 0
        self.gold_spent = checkpoint.gold_spent if checkpoint else 0
        self.hero_name = checkpoint.hero_name if checkpoint else None
        # Opening a hero clears the red alert. A resumed checkpoint therefore
        # identifies the card by its exact remembered name and level 10; the
        # destructive action dialog verifies the exact name again before firing.
        self.require_new_hero_alert = not bool(checkpoint and checkpoint.hero_name)
        self.character_scrolls = 0
        self.hiring_label_bounds: Optional[Tuple[int, int, int, int]] = None
        self.hiring_frame_size: Optional[Tuple[int, int]] = None

    def _save_checkpoint(self) -> None:
        self.checkpoint_store.save(self.hero_name, self.attempts, self.gold_spent)

    def _capture_known(
        self,
        window: GameWindow,
        timeout: float = 5.0,
    ) -> Tuple[WindowFrame, ScreenDetection]:
        deadline = time.monotonic() + timeout
        while True:
            frame = self.capture.capture(window)
            detection = self.detector.detect(frame.image)
            if detection.screen != HiringScreen.UNKNOWN:
                return frame, detection
            if time.monotonic() >= deadline:
                raise HiringWorkflowError("The game screen remained unknown for five seconds")
            time.sleep(0.25)

    def _wait_for_screen(
        self,
        window: GameWindow,
        expected: HiringScreen,
        timeout: float = 8.0,
    ) -> None:
        deadline = time.monotonic() + timeout
        last_screen = HiringScreen.UNKNOWN
        while time.monotonic() < deadline:
            frame = self.capture.capture(window)
            detection = self.detector.detect(frame.image)
            last_screen = detection.screen
            if detection.screen == expected:
                return
            time.sleep(0.25)
        raise HiringWorkflowError(
            f"Expected screen {expected.value!r} did not appear; last screen was "
            f"{last_screen.value!r}"
        )

    @staticmethod
    def _same_target(first: TemplateMatch, second: TemplateMatch) -> bool:
        return (
            first.template_id == second.template_id
            and abs(first.center[0] - second.center[0]) <= 4
            and abs(first.center[1] - second.center[1]) <= 4
        )

    def _verified_template_click(
        self,
        window: GameWindow,
        screen: HiringScreen,
        template_id: str,
    ) -> None:
        first_frame, first_state = self._capture_known(window)
        first = self.detector.find_template(first_frame.image, template_id)
        second_frame, second_state = self._capture_known(first_frame.window)
        second = self.detector.find_template(second_frame.image, template_id)
        if (
            first_state.screen != screen
            or second_state.screen != screen
            or first is None
            or second is None
            or not self._same_target(first, second)
        ):
            raise HiringWorkflowError(
                f"Refusing {template_id!r}: two captures did not agree on {screen.value!r}"
            )
        click = self.window_input.click(second_frame, second.center)
        self.event(
            f"clicked {template_id}: client={click.client_point}, desktop={click.desktop_point}"
        )
        time.sleep(0.8)

    def _verified_drag(self, window: GameWindow, direction: str) -> None:
        first_frame, first = self._capture_known(window)
        second_frame, second = self._capture_known(first_frame.window)
        if first.screen != HiringScreen.CHARACTERS or second.screen != HiringScreen.CHARACTERS:
            raise HiringWorkflowError("Refusing to scroll outside the character list")
        width, height = second_frame.client_rect.width, second_frame.client_rect.height
        if direction == "left":
            start_fraction, end_fraction = 0.88, 0.35
        elif direction == "right":
            start_fraction, end_fraction = 0.35, 0.88
        else:
            raise HiringWorkflowError(f"Unknown carousel direction: {direction!r}")
        drag = self.window_input.drag(
            second_frame,
            client_start=(round(width * start_fraction), round(height * 0.82)),
            client_end=(round(width * end_fraction), round(height * 0.82)),
        )
        self.character_scrolls += 1
        self.event(
            f"dragged character carousel {direction}: {drag.client_start}->{drag.client_end}"
        )
        time.sleep(0.8)

    def _verified_card(
        self,
        window: GameWindow,
        hero_name: str,
        require_alert: bool,
    ) -> HeroCardMatch:
        # EasyOCR can take 7-8 seconds for one full-width character strip on
        # CPU. The old six-second deadline could expire after the first valid
        # capture, before a second stationary position could be observed.
        deadline = time.monotonic() + 45.0
        previous: Optional[HeroCardMatch] = None
        for _capture_attempt in range(6):
            frame, state = self._capture_known(window)
            current = self.card_finder.find(
                frame.image,
                hero_name,
                require_alert=require_alert,
            )
            if (
                state.screen == HiringScreen.CHARACTERS
                and previous is not None
                and current is not None
                and abs(previous.click_point[0] - current.click_point[0]) <= 4
                and abs(previous.click_point[1] - current.click_point[1]) <= 4
            ):
                break
            if current is not None:
                previous = current
            if time.monotonic() >= deadline:
                raise HiringWorkflowError(
                    f"Hero card {hero_name!r} did not settle before the OCR deadline"
                )
            time.sleep(0.3)
        else:
            raise HiringWorkflowError(
                f"Hero card {hero_name!r} did not settle after six verification captures"
            )

        self.window_input.click(frame, current.click_point)
        alert_score = f"{current.alert.score:.3f}" if current.alert is not None else "resume"
        self.event(
            f"opened hero {hero_name}: OCR={current.name.confidence:.3f}, "
            f"level={current.level.score:.3f}, alert={alert_score}"
        )
        time.sleep(0.8)
        return current

    def _card_is_stably_visible(
        self,
        window: GameWindow,
        hero_name: str,
        require_alert: bool,
    ) -> bool:
        previous: Optional[HeroCardMatch] = None
        for _attempt in range(3):
            frame, state = self._capture_known(window)
            current = self.card_finder.find(
                frame.image,
                hero_name,
                require_alert=require_alert,
            )
            if (
                state.screen == HiringScreen.CHARACTERS
                and previous is not None
                and current is not None
                and abs(previous.click_point[0] - current.click_point[0]) <= 4
                and abs(previous.click_point[1] - current.click_point[1]) <= 4
            ):
                return True
            if current is not None:
                previous = current
            time.sleep(0.3)
        return False

    @staticmethod
    def _label_key(value: str) -> str:
        return value.replace(" ", "").upper()

    def _verified_hiring_labels(
        self,
        window: GameWindow,
    ) -> Tuple[
        WindowFrame,
        Dict[str, OCRTextMatch],
        WindowFrame,
        Dict[str, OCRTextMatch],
    ]:
        first_frame, first_state = self._capture_known(window)
        second_frame, second_state = self._capture_known(first_frame.window)
        first_labels = self._read_hiring_labels(first_frame)
        second_labels = self._read_hiring_labels(second_frame)
        category_keys = tuple(
            self._label_key(HERO_CATEGORY_NAMES_RU[category]) for category in HERO_CLASSES
        )
        stable = True
        for key in category_keys:
            first = first_labels.get(key)
            second = second_labels.get(key)
            if (
                first is None
                or second is None
                or abs(first.center[0] - second.center[0]) > 6
                or abs(first.center[1] - second.center[1]) > 6
            ):
                stable = False
        if (
            first_state.screen != HiringScreen.HIRING
            or second_state.screen != HiringScreen.HIRING
            or not stable
        ):
            raise HiringWorkflowError(
                "Two captures did not agree on all three hiring category labels"
            )
        return first_frame, first_labels, second_frame, second_labels

    def _read_hiring_labels(self, frame: WindowFrame) -> Dict[str, OCRTextMatch]:
        frame_size = (frame.image.shape[1], frame.image.shape[0])
        if self.hiring_frame_size != frame_size:
            self.hiring_label_bounds = None
            self.hiring_frame_size = frame_size

        labels = self.hiring_panel_reader.read_labels(
            frame.image,
            self.hiring_label_bounds,
        )
        category_keys = tuple(
            self._label_key(HERO_CATEGORY_NAMES_RU[category]) for category in HERO_CLASSES
        )
        if self.hiring_label_bounds is not None and not all(key in labels for key in category_keys):
            labels = self.hiring_panel_reader.read_labels(frame.image)

        if all(key in labels for key in category_keys):
            panel_left, ui_scale = self._panel_geometry(labels)
            category_y = round(
                sum(labels[key].center[1] for key in category_keys) / len(category_keys)
            )
            width, height = frame_size
            self.hiring_label_bounds = (
                max(0, round(panel_left - 8 * ui_scale)),
                max(0, round(category_y - 20 * ui_scale)),
                min(width, round(panel_left + 299 * ui_scale)),
                min(height, round(category_y + 105 * ui_scale)),
            )
        return labels

    def _panel_geometry(
        self,
        labels: Dict[str, OCRTextMatch],
    ) -> Tuple[float, float]:
        matches = [
            labels[self._label_key(HERO_CATEGORY_NAMES_RU[category])] for category in HERO_CLASSES
        ]
        first_gap = matches[1].center[0] - matches[0].center[0]
        second_gap = matches[2].center[0] - matches[1].center[0]
        if (
            first_gap <= 0
            or second_gap <= 0
            or abs(first_gap - second_gap) > 0.15 * max(first_gap, second_gap)
        ):
            raise HiringWorkflowError("Hiring category labels have inconsistent geometry")
        spacing = (first_gap + second_gap) / 2.0
        ui_scale = spacing / 97.0
        panel_left = matches[0].center[0] - spacing / 2.0
        return panel_left, ui_scale

    def _selected_class(
        self,
        labels: Dict[str, OCRTextMatch],
        category: str,
    ) -> Optional[str]:
        category_match = labels[self._label_key(HERO_CATEGORY_NAMES_RU[category])]
        _, ui_scale = self._panel_geometry(labels)
        candidates = []
        for hero_class in HERO_CLASSES[category]:
            match = labels.get(self._label_key(HERO_CLASS_NAMES_RU[hero_class]))
            if match is None:
                continue
            delta_y = match.center[1] - category_match.center[1]
            if 45 * ui_scale <= delta_y <= 105 * ui_scale:
                candidates.append(hero_class)
        if len(candidates) > 1:
            raise HiringWorkflowError(f"Multiple selected class labels found: {candidates}")
        return candidates[0] if candidates else None

    def _verified_hire(self, window: GameWindow) -> None:
        first_frame, first_labels, second_frame, second_labels = self._verified_hiring_labels(
            window
        )
        category_key = self._label_key(HERO_CATEGORY_NAMES_RU[self.config.category])
        first_selected = self._selected_class(first_labels, self.config.category)
        second_selected = self._selected_class(second_labels, self.config.category)

        if first_selected != self.config.hero_class or second_selected != self.config.hero_class:
            self.window_input.click(second_frame, second_labels[category_key].center)
            self.event(f"selected hero category {self.config.category}")
            time.sleep(0.8)

            first_frame, first_labels, second_frame, second_labels = self._verified_hiring_labels(
                window
            )
            first_selected = self._selected_class(first_labels, self.config.category)
            second_selected = self._selected_class(second_labels, self.config.category)
            if first_selected is None or first_selected != second_selected:
                raise HiringWorkflowError(
                    f"Category {self.config.category!r} did not expose one stable class label"
                )

        if second_selected != self.config.hero_class:
            panel_left, ui_scale = self._panel_geometry(second_labels)
            classes = HERO_CLASSES[self.config.category]
            class_index = classes.index(self.config.hero_class)
            category = second_labels[category_key]
            point = (
                round(panel_left + (class_index + 0.5) * (269.0 / len(classes)) * ui_scale),
                round(category.center[1] + 36.0 * ui_scale),
            )
            self.window_input.click(second_frame, point)
            self.event(f"selected hero class {self.config.hero_class}")
            time.sleep(0.8)
            first_frame, first_labels, second_frame, second_labels = self._verified_hiring_labels(
                window
            )
            first_selected = self._selected_class(first_labels, self.config.category)
            second_selected = self._selected_class(second_labels, self.config.category)
        if first_selected != self.config.hero_class or second_selected != self.config.hero_class:
            raise HiringWorkflowError(
                f"Two captures did not show selected class {self.config.hero_class!r}"
            )

        first_hire = self.detector.find_template(first_frame.image, "hire_free")
        second_hire = self.detector.find_template(second_frame.image, "hire_free")
        action = "hire_free"
        if first_hire is None or second_hire is None:
            first_hire = self.detector.find_template(first_frame.image, "hire")
            second_hire = self.detector.find_template(second_frame.image, "hire")
            action = "hire"
        if (
            first_hire is None
            or second_hire is None
            or not self._same_target(first_hire, second_hire)
        ):
            raise HiringWorkflowError("Two captures did not agree on the class hire button")
        self.window_input.click(second_frame, second_hire.center)
        self.event(f"clicked verified {action} for {self.config.category}/{self.config.hero_class}")
        time.sleep(0.8)

    def _verified_name_hire(self, window: GameWindow) -> str:
        first_frame, first = self._capture_known(window)
        second_frame, second = self._capture_known(first_frame.window)
        if (
            first.screen != HiringScreen.NAME_ENTRY
            or second.screen != HiringScreen.NAME_ENTRY
            or not first.hero_name
            or first.hero_name != second.hero_name
            or first.evidence is None
            or second.evidence is None
            or not self._same_target(first.evidence, second.evidence)
            or first.suggested_action != second.suggested_action
            or second.suggested_action not in {"confirm_free_hire", "confirm_gold_hire"}
        ):
            raise HiringWorkflowError("Two captures did not agree on the name and payment dialog")
        if second.suggested_action == "confirm_gold_hire":
            first_cost = self.gold_cost_reader.read_cost(first_frame.image, first.evidence)
            second_cost = self.gold_cost_reader.read_cost(second_frame.image, second.evidence)
            if first_cost is None or first_cost != second_cost or first_cost <= 0:
                raise HiringWorkflowError("Two captures did not agree on a positive gold price")
            cost = first_cost
        else:
            cost = 0
        projected_gold = self.gold_spent + cost
        if projected_gold > self.config.limits.max_gold_spent:
            raise HiringWorkflowError(
                f"Refusing hire costing {cost}: projected gold {projected_gold} exceeds "
                f"limit {self.config.limits.max_gold_spent}"
            )
        self.window_input.click(second_frame, second.evidence.center)
        self.attempts += 1
        self.gold_spent = projected_gold
        self.hero_name = second.hero_name
        self.require_new_hero_alert = True
        self._save_checkpoint()
        self.event(
            f"hired attempt {self.attempts}: name={second.hero_name}, "
            f"cost={cost}, total_gold={self.gold_spent}"
        )
        self._wait_for_screen(second_frame.window, HiringScreen.CHARACTERS)
        return second.hero_name

    def _verified_skills(self, window: GameWindow) -> SkillAnalysis:
        first_frame, first_state = self._capture_known(window)
        first = self.skill_recognizer.analyze(
            first_frame.image,
            self.config.hero_class,
            self.config.allowed_skills,
        )
        second_frame, second_state = self._capture_known(first_frame.window)
        second = self.skill_recognizer.analyze(
            second_frame.image,
            self.config.hero_class,
            self.config.allowed_skills,
        )
        first_ids = tuple(skill.skill_id for skill in first.random_skills)
        second_ids = tuple(skill.skill_id for skill in second.random_skills)
        if (
            first_state.screen != HiringScreen.HERO_DETAILS
            or second_state.screen != HiringScreen.HERO_DETAILS
            or first_ids != second_ids
        ):
            raise HiringWorkflowError("Two captures did not agree on both randomized skills")
        return second

    def _verified_action_name(self, window: GameWindow, hero_name: str) -> None:
        first_frame, first_state = self._capture_known(window)
        first_name = self.action_name_reader.find(first_frame.image, hero_name)
        first_fire = self.detector.find_template(first_frame.image, "fire")
        second_frame, second_state = self._capture_known(first_frame.window)
        second_name = self.action_name_reader.find(second_frame.image, hero_name)
        second_fire = self.detector.find_template(second_frame.image, "fire")
        if (
            first_state.screen != HiringScreen.HERO_ACTIONS
            or second_state.screen != HiringScreen.HERO_ACTIONS
            or first_name is None
            or second_name is None
            or first_fire is None
            or second_fire is None
            or not self._same_target(first_fire, second_fire)
        ):
            raise HiringWorkflowError("Hero actions did not preserve the verified hero name")
        self.window_input.click(second_frame, second_fire.center)
        self.event(f"opened fire confirmation for {hero_name}")
        time.sleep(0.8)

    def run(self, window: GameWindow) -> HiringWorkflowResult:
        if self.gold_spent > self.config.limits.max_gold_spent:
            raise HiringWorkflowError(
                f"Saved gold total {self.gold_spent} exceeds configured limit "
                f"{self.config.limits.max_gold_spent}; no clicks were performed"
            )

        max_steps = self.config.limits.max_attempts * 30 + 100
        for _step in range(max_steps):
            frame, state = self._capture_known(window)
            self.event(f"state={state.screen.value}")

            if state.screen == HiringScreen.RECONNECT:
                self._verified_template_click(frame.window, state.screen, "reconnect")
            elif state.screen == HiringScreen.BLOCKING_DIALOG:
                self._verified_template_click(frame.window, state.screen, "close")
            elif state.screen == HiringScreen.MAIN:
                self._verified_template_click(frame.window, state.screen, "characters")
            elif state.screen == HiringScreen.CHARACTERS:
                if self.hero_name:
                    card = self.card_finder.find(
                        frame.image,
                        self.hero_name,
                        require_alert=self.require_new_hero_alert,
                    )
                    if card is not None or self._card_is_stably_visible(
                        frame.window,
                        self.hero_name,
                        self.require_new_hero_alert,
                    ):
                        self._verified_card(
                            frame.window,
                            self.hero_name,
                            self.require_new_hero_alert,
                        )
                        self.character_scrolls = 0
                    elif self.character_scrolls < 4:
                        # First reach the beginning, where a fresh hire normally
                        # appears. If it is not there, sweep the full strip.
                        self._verified_drag(frame.window, "right")
                    elif self.character_scrolls < 12:
                        self._verified_drag(frame.window, "left")
                    else:
                        raise HiringWorkflowError(
                            f"Could not find newly hired hero {self.hero_name!r} "
                            "after a bidirectional carousel search"
                        )
                else:
                    new_hero = self.detector.find_template(frame.image, "new_hero")
                    if new_hero is not None:
                        self._verified_template_click(frame.window, state.screen, "new_hero")
                        self.character_scrolls = 0
                    elif self.character_scrolls < 4:
                        self._verified_drag(frame.window, "right")
                    else:
                        raise HiringWorkflowError(
                            "Could not return to the New Hero card after four scrolls"
                        )
            elif state.screen == HiringScreen.HIRING:
                self._verified_hire(frame.window)
            elif state.screen == HiringScreen.NAME_ENTRY:
                if self.attempts >= self.config.limits.max_attempts:
                    raise HiringWorkflowError(
                        f"Maximum hiring attempts reached: {self.config.limits.max_attempts}"
                    )
                self.hero_name = self._verified_name_hire(frame.window)
                self.character_scrolls = 0
            elif state.screen == HiringScreen.HERO_DETAILS:
                if not self.hero_name:
                    raise HiringWorkflowError("Hero details opened without a remembered hero name")
                analysis = self._verified_skills(frame.window)
                skill_ids = (
                    analysis.random_skills[0].skill_id,
                    analysis.random_skills[1].skill_id,
                )
                self.event(f"skills={skill_ids}; decision={analysis.decision}")
                if analysis.accepted:
                    self.checkpoint_store.clear()
                    return HiringWorkflowResult(
                        hero_name=self.hero_name,
                        attempts=self.attempts,
                        gold_spent=self.gold_spent,
                        skills=skill_ids,
                    )
                if analysis.decision == "unknown":
                    evidence = ", ".join(
                        f"slot {skill.position}: {skill.skill_id}={skill.score:.3f}, "
                        f"runner-up {skill.runner_up_id}={skill.runner_up_score:.3f}"
                        for skill in analysis.unrecognized_skills
                    )
                    raise HiringWorkflowError(
                        "One or more skill icons are missing from the catalog or ambiguous; "
                        f"hero was not dismissed ({evidence})"
                    )
                if analysis.decision == "uncertain":
                    raise HiringWorkflowError(
                        "Skill decision remained uncertain; hero was not dismissed"
                    )
                self._verified_template_click(frame.window, state.screen, "gear")
            elif state.screen == HiringScreen.HERO_ACTIONS:
                if not self.hero_name:
                    raise HiringWorkflowError("Hero actions opened without a remembered hero name")
                self._verified_action_name(frame.window, self.hero_name)
            elif state.screen == HiringScreen.FIRE_CONFIRMATION:
                if not self.hero_name:
                    raise HiringWorkflowError(
                        "Fire confirmation opened without a remembered hero name"
                    )
                dismissed_name = self.hero_name
                self._verified_template_click(frame.window, state.screen, "confirm_fire")
                self.event(f"dismissed rejected hero {dismissed_name}")
                self.hero_name = None
                self.require_new_hero_alert = False
                self.character_scrolls = 0
                self._save_checkpoint()
            else:
                raise HiringWorkflowError(f"Unsupported workflow state: {state.screen.value}")

            if self.gold_spent > self.config.limits.max_gold_spent:
                raise HiringWorkflowError(
                    f"Gold budget exceeded: {self.gold_spent} > "
                    f"{self.config.limits.max_gold_spent}"
                )

        raise HiringWorkflowError("Workflow step limit reached before a suitable hero was found")
