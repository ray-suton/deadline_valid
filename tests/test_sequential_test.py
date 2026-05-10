import unittest

from src.fixed_horizon import one_sided_sign_test_pvalue
from src.sequential_test import SignMixtureEProcess, evaluate_trace, paired_outcome


class SequentialTestTests(unittest.TestCase):
    def test_paired_outcome(self) -> None:
        self.assertEqual(paired_outcome(1, 0), 1)
        self.assertEqual(paired_outcome(0, 1), -1)
        self.assertEqual(paired_outcome(1, 1), 0)

    def test_e_process_starts_at_one(self) -> None:
        process = SignMixtureEProcess(alpha=0.05)
        self.assertAlmostEqual(process.e_value(), 1.0)

    def test_trace_rejects_after_strong_win_streak(self) -> None:
        records = [(f"p{i}", 1, 0) for i in range(1, 10)]
        result = evaluate_trace(records, alpha=0.05)
        self.assertEqual(result["decision"], "reject_null")
        self.assertTrue(result["stopped_early"])

    def test_sign_test_pvalue(self) -> None:
        self.assertAlmostEqual(one_sided_sign_test_pvalue(0, 0), 1.0)
        self.assertAlmostEqual(one_sided_sign_test_pvalue(3, 0), 0.125)


if __name__ == "__main__":
    unittest.main()
