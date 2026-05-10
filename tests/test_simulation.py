import unittest

from scripts.simulate_null import simulate_null, simulate_power_grid


class SimulationTests(unittest.TestCase):
    def test_simulate_null_returns_rate_summary(self) -> None:
        summary = simulate_null(
            trials=20,
            prompts=12,
            tie_rate=0.35,
            alpha=0.05,
            seed=7,
        )
        self.assertEqual(summary["trials"], 20)
        self.assertEqual(summary["prompts"], 12)
        self.assertIn("example_trace", summary)
        self.assertGreaterEqual(summary["sequential_false_positive_rate"], 0.0)
        self.assertLessEqual(summary["sequential_false_positive_rate"], 1.0)
        self.assertGreaterEqual(summary["fixed_false_positive_rate"], 0.0)
        self.assertLessEqual(summary["fixed_false_positive_rate"], 1.0)

    def test_simulate_power_grid_recommends_budget_for_strong_effect(self) -> None:
        summary = simulate_power_grid(
            trials=5,
            prompt_grid=[10, 20],
            tie_rate=0.35,
            alpha=0.05,
            seed=7,
            win_probabilities=[1.0],
            target_power=0.8,
        )
        self.assertEqual(len(summary["rows"]), 2)
        row = next(row for row in summary["rows"] if row["prompts"] == 20)
        self.assertEqual(row["win_probability"], 1.0)
        self.assertEqual(row["sequential_power"], 1.0)
        self.assertEqual(summary["recommendations"][0]["recommended_prompt_budget"], 20)


if __name__ == "__main__":
    unittest.main()
