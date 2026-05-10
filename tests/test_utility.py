import os
import tempfile
import unittest

from src.utility import deadline_utility, ensure_dir, is_correct, normalize_answer, write_json


class UtilityTests(unittest.TestCase):
    def test_normalize_answer(self) -> None:
        self.assertEqual(normalize_answer("  New   York "), "new york")

    def test_is_correct(self) -> None:
        self.assertTrue(is_correct("Paris", "paris"))
        self.assertFalse(is_correct("Lyon", "paris"))

    def test_deadline_utility(self) -> None:
        self.assertEqual(deadline_utility(correct=True, finished=True), 1)
        self.assertEqual(deadline_utility(correct=True, finished=False), 0)
        self.assertEqual(deadline_utility(correct=False, finished=True), 0)

    def test_write_json_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "a", "b", "payload.json")
            ensure_dir(os.path.join(tmpdir, "a"))
            write_json(target, {"ok": True})
            self.assertTrue(os.path.exists(target))


if __name__ == "__main__":
    unittest.main()
