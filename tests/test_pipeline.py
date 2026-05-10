import os
import tempfile
import unittest

from scripts.analyze_results import analyze_results
from src.run_eval import run_evaluation


ROOT = os.path.dirname(os.path.dirname(__file__))


class PipelineTests(unittest.TestCase):
    def test_run_evaluation_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_evaluation(
                benchmarks_config_path=os.path.join(ROOT, "configs", "benchmarks.json"),
                policies_config_path=os.path.join(ROOT, "configs", "policies.json"),
                out_dir=tmpdir,
                alpha=0.05,
            )
            self.assertGreater(result["manifest"]["prompt_run_count"], 0)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "manifest.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "comparison_summaries.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "utility_summary.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "reference_summary.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "reference_prompt_runs.json")))
            summary = analyze_results(tmpdir)
            self.assertEqual(summary["utility_row_count"], 12)
            self.assertEqual(summary["comparison_row_count"], 36)
            summary_path = os.path.join(tmpdir, "analysis", "summary.md")
            sample_cases_path = os.path.join(tmpdir, "analysis", "sample_cases.md")
            self.assertTrue(os.path.exists(summary_path))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "analysis", "leaderboard.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "analysis", "decision_summary.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "analysis", "difficulty_utility_summary.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "analysis", "difficulty_leaderboard.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "analysis", "no_time_limit_summary.csv")))
            self.assertTrue(
                os.path.exists(os.path.join(tmpdir, "analysis", "no_time_limit_comparison_summary.csv"))
            )
            self.assertTrue(
                os.path.exists(os.path.join(tmpdir, "analysis", "no_time_limit_decision_summary.csv"))
            )
            self.assertTrue(os.path.exists(sample_cases_path))

            with open(summary_path, "r", encoding="utf-8") as handle:
                summary_markdown = handle.read()
            self.assertIn("## No-Time-Limit Reference", summary_markdown)
            self.assertIn("## Difficulty Leaderboard", summary_markdown)
            self.assertIn("## Sequential Decisions", summary_markdown)

            with open(sample_cases_path, "r", encoding="utf-8") as handle:
                sample_cases_markdown = handle.read()
            self.assertIn("No-limit output", sample_cases_markdown)


if __name__ == "__main__":
    unittest.main()
