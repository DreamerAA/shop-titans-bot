"""Entrypoint for hero-hiring automation and diagnostics."""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

from bot.hiring import HiringConfigError, load_hiring_config
from bot.hiring.capture import WindowCapture, WindowCaptureError, WindowFrame, save_window_frame
from bot.hiring.checkpoint import HiringCheckpointError
from bot.hiring.hero_cards import HeroCardFinder
from bot.hiring.input import UnsafeInputError, WindowInput
from bot.hiring.ocr import ActionDialogNameReader, HeroCardNameReader
from bot.hiring.recovery import RecoveryRunner, UnsafeRecoveryError
from bot.hiring.skills import SkillRecognitionError, SkillRecognizer
from bot.hiring.state import HiringScreen, HiringStateDetector, annotate_detection
from bot.hiring.workflow import HiringWorkflow, HiringWorkflowError
from bot.windowing import WindowActivationError, WindowLocator, WindowNotFoundError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Shop Titans hero hiring automation")
    parser.add_argument(
        "--config",
        default="configs/hiring.template.yaml",
        help="Path to the hiring YAML config",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--run",
        action="store_true",
        help="Run the verified hiring loop until a suitable hero is found",
    )
    mode.add_argument(
        "--capture-only",
        action="store_true",
        help="Locate the game window and save its client area without clicking",
    )
    mode.add_argument(
        "--state-only",
        action="store_true",
        help="Recognize the current screen and suggested action without clicking",
    )
    mode.add_argument(
        "--recover-once",
        action="store_true",
        help="Perform one verified close/reconnect action and recognize the resulting screen",
    )
    mode.add_argument(
        "--advance-once",
        action="store_true",
        help="Perform one verified recovery/navigation action and recognize the next screen",
    )
    mode.add_argument(
        "--scroll-characters-once",
        action="store_true",
        help="Perform one verified leftward drag of the responsive hero-card carousel",
    )
    mode.add_argument(
        "--scroll-characters-right-once",
        action="store_true",
        help="Perform one verified rightward drag of the responsive hero-card carousel",
    )
    mode.add_argument(
        "--open-hero",
        metavar="NAME",
        help="Open one hero after verifying exact name, level 10, and the new-hero alert",
    )
    mode.add_argument(
        "--analyze-skills",
        action="store_true",
        help="Recognize both randomized skills twice and print an accept/reject decision",
    )
    mode.add_argument(
        "--open-reject-actions",
        action="store_true",
        help="Open hero actions only after two matching rejected skill analyses",
    )
    mode.add_argument(
        "--open-fire-confirmation",
        metavar="NAME",
        help="Open the fire confirmation after verifying the actions dialog and hero name twice",
    )
    mode.add_argument(
        "--confirm-fire",
        metavar="NAME",
        help="Confirm the already verified pending dismissal and verify return to characters",
    )
    parser.add_argument(
        "--output",
        default="bot/data/hiring/diagnostics/window.png",
        help="Diagnostic PNG path used with --capture-only",
    )
    parser.add_argument(
        "--capture-method",
        choices=("window", "desktop"),
        help="Override the configured capture method for diagnostics",
    )
    return parser


def _save_annotated_frame(frame: WindowFrame, output: Path) -> None:
    detection = HiringStateDetector().detect(frame.image)
    annotated = WindowFrame(
        image=annotate_detection(frame.image, detection),
        window=frame.window,
        captured_at=frame.captured_at,
    )
    save_window_frame(annotated, output)

    if detection.evidence is None:
        print(f"Detected state: {detection.screen.value}; no actionable template found")
        return
    desktop_point = frame.to_desktop(detection.evidence.center)
    print(
        f"Detected state: {detection.screen.value}; "
        f"evidence={detection.evidence.template_id}; score={detection.evidence.score:.3f}; "
        f"scale={detection.evidence.scale:.2f}; "
        f"client_point={detection.evidence.center}; desktop_point={desktop_point}; "
        f"suggested_action={detection.suggested_action!r}; "
        f"hero_name={detection.hero_name!r}"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        config = load_hiring_config(args.config)
        locator = WindowLocator(
            process_name=config.window.process_name,
            title_contains=config.window.title_contains,
            min_client_width=config.window.min_client_width,
            min_client_height=config.window.min_client_height,
        )
        window = locator.find()
        capture_method = args.capture_method or config.window.capture_method
        capture = WindowCapture(locator, method=capture_method)
        frame = capture.capture(window)
        output = Path(args.output)
        if args.run:
            workflow_result = HiringWorkflow(
                config=config,
                capture=capture,
                detector=HiringStateDetector(),
                window_input=WindowInput(locator, method=config.window.input_method),
            ).run(window)
            frame = capture.capture(window)
            _save_annotated_frame(frame, output)
            print(
                f"Suitable hero found: name={workflow_result.hero_name!r}; "
                f"skills={workflow_result.skills}; attempts={workflow_result.attempts}; "
                f"gold_spent={workflow_result.gold_spent}"
            )
        elif args.confirm_fire:
            detector = HiringStateDetector()
            before = detector.detect(frame.image)
            verified_frame = capture.capture(window)
            verified = detector.detect(verified_frame.image)
            if (
                before.screen != HiringScreen.FIRE_CONFIRMATION
                or verified.screen != HiringScreen.FIRE_CONFIRMATION
                or before.evidence is None
                or verified.evidence is None
                or abs(before.evidence.center[0] - verified.evidence.center[0]) > 4
                or abs(before.evidence.center[1] - verified.evidence.center[1]) > 4
            ):
                raise UnsafeRecoveryError(
                    "Refusing to confirm dismissal: two fresh captures did not agree "
                    "on the pending fire confirmation"
                )
            click = WindowInput(locator, method=config.window.input_method).click(
                verified_frame,
                verified.evidence.center,
            )
            deadline = time.monotonic() + 5.0
            time.sleep(0.8)
            while True:
                frame = capture.capture(window)
                after = detector.detect(frame.image)
                if after.screen == HiringScreen.CHARACTERS:
                    break
                if time.monotonic() >= deadline:
                    raise UnsafeRecoveryError(
                        "Dismissal was confirmed, but the character list did not reappear"
                    )
                time.sleep(0.25)
            remaining = HeroCardNameReader().find(frame.image, args.confirm_fire)
            if remaining is not None:
                raise UnsafeRecoveryError(
                    f"Dismissal was confirmed, but hero {remaining.text!r} is still visible"
                )
            _save_annotated_frame(frame, output)
            print(
                f"Confirmed dismissal of the verified pending hero {args.confirm_fire!r}; "
                f"client={click.client_point}, desktop={click.desktop_point}"
            )
        elif args.open_fire_confirmation:
            detector = HiringStateDetector()
            name_reader = ActionDialogNameReader()
            before = detector.detect(frame.image)
            fire = detector.find_template(frame.image, "fire")
            name = name_reader.find(frame.image, args.open_fire_confirmation)
            verified_frame = capture.capture(window)
            verified = detector.detect(verified_frame.image)
            verified_fire = detector.find_template(verified_frame.image, "fire")
            verified_name = name_reader.find(verified_frame.image, args.open_fire_confirmation)
            if (
                before.screen != HiringScreen.HERO_ACTIONS
                or verified.screen != HiringScreen.HERO_ACTIONS
                or fire is None
                or verified_fire is None
                or name is None
                or verified_name is None
                or abs(fire.center[0] - verified_fire.center[0]) > 4
                or abs(fire.center[1] - verified_fire.center[1]) > 4
            ):
                raise UnsafeRecoveryError(
                    "Refusing to open fire confirmation: two fresh captures did not agree "
                    "on the actions screen, hero name, and fire control"
                )
            click = WindowInput(locator, method=config.window.input_method).click(
                verified_frame,
                verified_fire.center,
            )
            time.sleep(0.8)
            frame = capture.capture(window)
            _save_annotated_frame(frame, output)
            print(
                f"Opened fire confirmation for {verified_name.text!r}; "
                f"client={click.client_point}, desktop={click.desktop_point}"
            )
        elif args.open_reject_actions:
            detector = HiringStateDetector()
            recognizer = SkillRecognizer()
            before = detector.detect(frame.image)
            analysis = recognizer.analyze(
                frame.image,
                config.hero_class,
                config.allowed_skills,
            )
            gear = detector.find_template(frame.image, "gear")
            verified_frame = capture.capture(window)
            verified = detector.detect(verified_frame.image)
            verified_analysis = recognizer.analyze(
                verified_frame.image,
                config.hero_class,
                config.allowed_skills,
            )
            verified_gear = detector.find_template(verified_frame.image, "gear")
            first_ids = tuple(skill.skill_id for skill in analysis.random_skills)
            verified_ids = tuple(skill.skill_id for skill in verified_analysis.random_skills)
            if analysis.decision != "reject" or verified_analysis.decision != "reject":
                raise UnsafeRecoveryError(
                    "Refusing to reject a hero without two explicit reject decisions"
                )
            if (
                before.screen != HiringScreen.HERO_DETAILS
                or verified.screen != HiringScreen.HERO_DETAILS
                or first_ids != verified_ids
                or gear is None
                or verified_gear is None
                or abs(gear.center[0] - verified_gear.center[0]) > 4
                or abs(gear.center[1] - verified_gear.center[1]) > 4
            ):
                raise UnsafeRecoveryError(
                    "Refusing to open reject actions: two fresh captures did not agree on "
                    "the rejected skills and gear control"
                )
            click = WindowInput(locator, method=config.window.input_method).click(
                verified_frame,
                verified_gear.center,
            )
            time.sleep(0.8)
            frame = capture.capture(window)
            _save_annotated_frame(frame, output)
            print(
                f"Opened actions for rejected skills {verified_ids}; "
                f"client={click.client_point}, desktop={click.desktop_point}"
            )
        elif args.analyze_skills:
            detector = HiringStateDetector()
            recognizer = SkillRecognizer()
            before = detector.detect(frame.image)
            analysis = recognizer.analyze(
                frame.image,
                config.hero_class,
                config.allowed_skills,
            )
            verified_frame = capture.capture(window)
            verified = detector.detect(verified_frame.image)
            verified_analysis = recognizer.analyze(
                verified_frame.image,
                config.hero_class,
                config.allowed_skills,
            )
            first_ids = tuple(skill.skill_id for skill in analysis.random_skills)
            verified_ids = tuple(skill.skill_id for skill in verified_analysis.random_skills)
            if (
                before.screen != HiringScreen.HERO_DETAILS
                or verified.screen != HiringScreen.HERO_DETAILS
                or first_ids != verified_ids
            ):
                raise UnsafeRecoveryError(
                    "Refusing skill decision: two fresh captures did not agree on "
                    "the hero-details screen and both randomized skills"
                )
            frame = verified_frame
            _save_annotated_frame(frame, output)
            evidence = ", ".join(
                f"{skill.skill_id}={skill.score:.3f} "
                f"(runner-up {skill.runner_up_id}={skill.runner_up_score:.3f}, "
                f"shape={skill.shape_score:.3f}, palette={skill.palette_score:.3f}, "
                f"identity_confident={skill.confident}, outcome={skill.decision_hint}, "
                f"best_allowed={skill.best_allowed_id}:{skill.best_allowed_score:.3f}, "
                f"best_rejected={skill.best_rejected_id}:{skill.best_rejected_score:.3f})"
                for skill in verified_analysis.random_skills
            )
            print(
                f"Skill decision: {verified_analysis.decision}; "
                f"random_skills={verified_ids}; evidence={evidence}"
            )
        elif args.open_hero:
            detector = HiringStateDetector()
            finder = HeroCardFinder()
            before = detector.detect(frame.image)
            card = finder.find(frame.image, args.open_hero)
            verified_frame = capture.capture(window)
            verified = detector.detect(verified_frame.image)
            verified_card = finder.find(verified_frame.image, args.open_hero)
            if (
                before.screen != HiringScreen.CHARACTERS
                or verified.screen != HiringScreen.CHARACTERS
                or card is None
                or verified_card is None
                or abs(card.click_point[0] - verified_card.click_point[0]) > 4
                or abs(card.click_point[1] - verified_card.click_point[1]) > 4
            ):
                raise UnsafeRecoveryError(
                    "Refusing to open hero: two fresh captures did not agree on the "
                    "character screen and verified card"
                )
            click = WindowInput(locator, method=config.window.input_method).click(
                verified_frame,
                verified_card.click_point,
            )
            deadline = time.monotonic() + 5.0
            time.sleep(0.8)
            while True:
                frame = capture.capture(window)
                after = detector.detect(frame.image)
                if after.screen not in {HiringScreen.CHARACTERS, HiringScreen.UNKNOWN}:
                    break
                if time.monotonic() >= deadline:
                    break
                time.sleep(0.25)
            _save_annotated_frame(frame, output)
            print(
                f"Opened verified hero {verified_card.name.text!r}; "
                f"name_confidence={verified_card.name.confidence:.3f}; "
                f"client={click.client_point}, desktop={click.desktop_point}"
            )
        elif args.scroll_characters_once or args.scroll_characters_right_once:
            detector = HiringStateDetector()
            before = detector.detect(frame.image)
            verified_frame = capture.capture(window)
            verified = detector.detect(verified_frame.image)
            if (
                before.screen != HiringScreen.CHARACTERS
                or verified.screen != HiringScreen.CHARACTERS
            ):
                raise UnsafeRecoveryError(
                    "Refusing to drag: two fresh captures did not both show the character list"
                )
            width, height = verified_frame.client_rect.width, verified_frame.client_rect.height
            if args.scroll_characters_right_once:
                start_fraction, end_fraction = 0.35, 0.88
            else:
                start_fraction, end_fraction = 0.88, 0.35
            drag = WindowInput(locator, method=config.window.input_method).drag(
                verified_frame,
                client_start=(round(width * start_fraction), round(height * 0.82)),
                client_end=(round(width * end_fraction), round(height * 0.82)),
            )
            time.sleep(0.6)
            frame = capture.capture(window)
            _save_annotated_frame(frame, output)
            print(
                f"Character carousel dragged client={drag.client_start}->{drag.client_end}; "
                f"desktop={drag.desktop_start}->{drag.desktop_end}"
            )
        elif args.recover_once or args.advance_once:
            detector = HiringStateDetector()
            allowed_actions = {"close", "reconnect"}
            if args.advance_once:
                allowed_actions.update({"characters", "new_hero"})
                if config.category == "warrior" and config.hero_class == "soldier":
                    allowed_actions.update({"hire_free", "confirm_free_hire"})
            recovery_result = RecoveryRunner(
                capture=capture,
                detector=detector,
                window_input=WindowInput(locator, method=config.window.input_method),
                allowed_actions=allowed_actions,
            ).recover_once(frame.window)
            annotated = WindowFrame(
                image=annotate_detection(recovery_result.after_frame.image, recovery_result.after),
                window=recovery_result.after_frame.window,
                captured_at=recovery_result.after_frame.captured_at,
            )
            save_window_frame(annotated, output)
            print(
                f"Recovery clicked {recovery_result.before.suggested_action!r} at "
                f"client={recovery_result.click.client_point}, "
                f"desktop={recovery_result.click.desktop_point}; "
                f"state changed {recovery_result.before.screen.value} -> "
                f"{recovery_result.after.screen.value}; "
                f"hero_name={recovery_result.before.hero_name!r}"
            )
            frame = recovery_result.after_frame
        elif args.state_only:
            _save_annotated_frame(frame, output)
        else:
            save_window_frame(frame, output)
    except (
        HiringConfigError,
        WindowNotFoundError,
        WindowActivationError,
        WindowCaptureError,
        UnsafeInputError,
        UnsafeRecoveryError,
        SkillRecognitionError,
        HiringWorkflowError,
        HiringCheckpointError,
        OSError,
    ) as exc:
        print(f"Hiring diagnostic failed: {exc}", file=sys.stderr)
        return 1

    rect = frame.client_rect
    print(
        "Game window captured successfully: "
        f"handle={window.handle}, pid={window.process_id}, process={window.process_name!r}, "
        f"title={window.title!r}, client={rect.width}x{rect.height}@({rect.left},{rect.top}), "
        f"method={capture_method}, output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
