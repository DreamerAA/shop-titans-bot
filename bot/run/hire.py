"""Entrypoint for hero-hiring automation and diagnostics."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from bot.hiring import HiringConfigError, load_hiring_config
from bot.hiring.capture import WindowCapture, WindowCaptureError, save_window_frame
from bot.windowing import WindowLocator, WindowNotFoundError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Shop Titans hero hiring automation")
    parser.add_argument(
        "--config",
        default="configs/hiring.template.yaml",
        help="Path to the hiring YAML config",
    )
    parser.add_argument(
        "--capture-only",
        action="store_true",
        help="Locate the game window and save its client area without clicking",
    )
    parser.add_argument(
        "--output",
        default="bot/data/hiring/diagnostics/window.png",
        help="Diagnostic PNG path used with --capture-only",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.capture_only:
        print(
            "The hiring workflow is not connected yet. Use --capture-only for a safe diagnostic.",
            file=sys.stderr,
        )
        return 2

    try:
        config = load_hiring_config(args.config)
        locator = WindowLocator(
            process_name=config.window.process_name,
            title_contains=config.window.title_contains,
            min_client_width=config.window.min_client_width,
            min_client_height=config.window.min_client_height,
        )
        window = locator.find()
        frame = WindowCapture(locator, method=config.window.capture_method).capture(window)
        output = save_window_frame(frame, Path(args.output))
    except (HiringConfigError, WindowNotFoundError, WindowCaptureError, OSError) as exc:
        print(f"Hiring diagnostic failed: {exc}", file=sys.stderr)
        return 1

    rect = frame.client_rect
    print(
        "Game window captured successfully: "
        f"handle={window.handle}, pid={window.process_id}, process={window.process_name!r}, "
        f"title={window.title!r}, client={rect.width}x{rect.height}@({rect.left},{rect.top}), "
        f"method={config.window.capture_method}, output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
