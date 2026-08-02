import tempfile
import unittest
from pathlib import Path

from bot.hiring.checkpoint import HiringCheckpointError, HiringCheckpointStore
from bot.hiring.config import parse_hiring_config


class HiringCheckpointTests(unittest.TestCase):
    @staticmethod
    def config(allowed_skill="juggernaut"):
        return parse_hiring_config(
            {
                "hiring": {
                    "category": "warrior",
                    "class": "soldier",
                    "allowed_skills": [allowed_skill],
                    "limits": {"max_gold_spent": 1_000_000, "max_attempts": 100},
                }
            }
        )

    def test_round_trips_resume_state_and_clears_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            store = HiringCheckpointStore(self.config(), path)

            store.save("САБРИНА", attempts=3, gold_spent=50_000)
            checkpoint = store.load()

            self.assertEqual("САБРИНА", checkpoint.hero_name)
            self.assertEqual(3, checkpoint.attempts)
            self.assertEqual(50_000, checkpoint.gold_spent)
            store.clear()
            self.assertIsNone(store.load())

    def test_rejects_checkpoint_from_different_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            HiringCheckpointStore(self.config(), path).save(None, 0, 0)

            with self.assertRaisesRegex(HiringCheckpointError, "different configuration"):
                HiringCheckpointStore(self.config("impervious"), path).load()


if __name__ == "__main__":
    unittest.main()
