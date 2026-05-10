import unittest

from src.policies import BudgetAwarePolicy, GreedyPolicy, SelectiveAbstainPolicy, SelfConsistencyPolicy
from src.utility import PromptExample, TraceCandidate


def make_example() -> PromptExample:
    return PromptExample(
        prompt_id="ex1",
        prompt="2 + 2",
        answer="4",
        traces={
            "greedy": TraceCandidate(answer="5", latency_s=0.4, confidence=0.4),
            "sample_1": TraceCandidate(answer="4", latency_s=0.4, confidence=0.7),
            "sample_2": TraceCandidate(answer="4", latency_s=0.5, confidence=0.8),
            "sample_3": TraceCandidate(answer="5", latency_s=0.6, confidence=0.4),
            "deliberate": TraceCandidate(answer="4", latency_s=1.0, confidence=0.95),
        },
    )


class PolicyTests(unittest.TestCase):
    def test_greedy_policy_times_out(self) -> None:
        policy = GreedyPolicy("greedy", "greedy")
        outcome = policy.run(make_example(), deadline_s=0.2)
        self.assertFalse(outcome.finished)
        self.assertEqual(outcome.utility, 0)

    def test_self_consistency_majority_vote(self) -> None:
        policy = SelfConsistencyPolicy("sc", ["sample_1", "sample_2", "sample_3"])
        outcome = policy.run(make_example(), deadline_s=1.0)
        self.assertTrue(outcome.finished)
        self.assertEqual(outcome.predicted_answer, "4")
        self.assertEqual(outcome.utility, 1)

    def test_budget_aware_uses_fallback(self) -> None:
        policy = BudgetAwarePolicy("budget", "greedy", "deliberate", 0.8)
        outcome = policy.run(make_example(), deadline_s=2.0)
        self.assertEqual(outcome.predicted_answer, "4")
        self.assertEqual(outcome.details["stage"], "fallback_used")

    def test_selective_abstain_abstains_on_low_confidence(self) -> None:
        policy = SelectiveAbstainPolicy("abstain", "greedy", 0.75)
        outcome = policy.run(make_example(), deadline_s=1.0)
        self.assertTrue(outcome.finished)
        self.assertIsNone(outcome.predicted_answer)
        self.assertEqual(outcome.utility, 0)
        self.assertEqual(outcome.details["stage"], "abstain")

    def test_selective_abstain_answers_when_confident(self) -> None:
        policy = SelectiveAbstainPolicy("abstain", "sample_2", 0.75)
        outcome = policy.run(make_example(), deadline_s=1.0)
        self.assertTrue(outcome.finished)
        self.assertEqual(outcome.predicted_answer, "4")
        self.assertEqual(outcome.utility, 1)
        self.assertEqual(outcome.details["stage"], "answer")


if __name__ == "__main__":
    unittest.main()
