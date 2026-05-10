import json
import os
import tempfile
import unittest

from scripts.validate_trace_bank import TraceBankValidationError, validate_trace_bank


ROOT = os.path.dirname(os.path.dirname(__file__))


class TraceBankValidatorTests(unittest.TestCase):
    def test_current_benchmark_passes_default_validation(self) -> None:
        path = os.path.join(ROOT, "data", "benchmarks", "replay_math_v1.jsonl")
        summary = validate_trace_bank([path])
        self.assertGreater(summary["prompt_count"], 0)
        self.assertGreater(summary["trace_count"], 0)

    def test_duplicate_prompt_id_fails(self) -> None:
        record = {
            "id": "dup1",
            "prompt": "2 + 2",
            "answer": "4",
            "traces": {
                "greedy": {"answer": "4", "latency_s": 0.2, "confidence": 0.9},
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "dup.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
                handle.write(json.dumps(record) + "\n")
            with self.assertRaises(TraceBankValidationError):
                validate_trace_bank([path])

    def test_upgrade_mode_requires_extra_fields(self) -> None:
        record = {
            "id": "p1",
            "prompt": "2 + 2",
            "answer": "4",
            "metadata": {},
            "traces": {
                "greedy": {"answer": "4", "latency_s": 0.2, "confidence": 0.9},
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "minimal.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            with self.assertRaises(TraceBankValidationError):
                validate_trace_bank([path], require_upgrade_fields=True)

    def test_multiple_choice_requires_canonical_option_answers(self) -> None:
        record = {
            "id": "mcq1",
            "prompt": "Pick one option",
            "answer": "B",
            "metadata": {
                "answer_type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
            },
            "traces": {
                "greedy": {
                    "answer": "Answer: B",
                    "latency_s": 0.2,
                    "confidence": 0.8,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "mcq.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            with self.assertRaises(TraceBankValidationError):
                validate_trace_bank([path])


if __name__ == "__main__":
    unittest.main()
