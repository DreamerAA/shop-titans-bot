"""Persistent resume state for a long-running hiring loop."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from bot.hiring.config import HiringConfig


class HiringCheckpointError(RuntimeError):
    """Raised when a checkpoint is malformed or belongs to another config."""


@dataclass(frozen=True)
class HiringCheckpoint:
    signature: str
    hero_name: Optional[str]
    attempts: int
    gold_spent: int


class HiringCheckpointStore:
    def __init__(
        self,
        config: HiringConfig,
        path: Path = Path("bot/data/hiring/checkpoint.json"),
    ):
        self.path = path
        self.signature = "|".join(
            (
                config.category,
                config.hero_class,
                ",".join(sorted(config.allowed_skills)),
                str(config.limits.max_gold_spent),
                str(config.limits.max_attempts),
            )
        )

    def load(self) -> Optional[HiringCheckpoint]:
        if not self.path.is_file():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            checkpoint = HiringCheckpoint(
                signature=str(data["signature"]),
                hero_name=data.get("hero_name"),
                attempts=int(data["attempts"]),
                gold_spent=int(data["gold_spent"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HiringCheckpointError(f"Invalid hiring checkpoint: {self.path}") from exc
        if checkpoint.signature != self.signature:
            raise HiringCheckpointError(
                "Hiring checkpoint belongs to a different configuration; "
                f"remove it before starting: {self.path}"
            )
        if checkpoint.attempts < 0 or checkpoint.gold_spent < 0:
            raise HiringCheckpointError(f"Invalid negative counters in checkpoint: {self.path}")
        return checkpoint

    def save(self, hero_name: Optional[str], attempts: int, gold_spent: int) -> None:
        checkpoint = HiringCheckpoint(
            signature=self.signature,
            hero_name=hero_name,
            attempts=attempts,
            gold_spent=gold_spent,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(checkpoint), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
