from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from src.utility import PolicyOutcome, PromptExample, deadline_utility, is_correct


class Policy(ABC):
    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id

    @abstractmethod
    def run(self, example: PromptExample, deadline_s: float) -> PolicyOutcome:
        raise NotImplementedError


class GreedyPolicy(Policy):
    def __init__(self, policy_id: str, trace_name: str) -> None:
        super().__init__(policy_id)
        self.trace_name = trace_name

    def run(self, example: PromptExample, deadline_s: float) -> PolicyOutcome:
        trace = example.traces[self.trace_name]
        finished = trace.latency_s <= deadline_s
        predicted_answer = trace.answer if finished else None
        correct = is_correct(predicted_answer, example.answer)
        return PolicyOutcome(
            prompt_id=example.prompt_id,
            policy_id=self.policy_id,
            deadline_s=deadline_s,
            predicted_answer=predicted_answer,
            correct=correct,
            finished=finished,
            latency_s=trace.latency_s if finished else None,
            utility=deadline_utility(correct, finished),
            details={"trace_name": self.trace_name, "confidence": trace.confidence},
        )


class SelfConsistencyPolicy(Policy):
    def __init__(self, policy_id: str, trace_names: list[str]) -> None:
        super().__init__(policy_id)
        self.trace_names = trace_names

    def run(self, example: PromptExample, deadline_s: float) -> PolicyOutcome:
        completed_names: list[str] = []
        completed_answers: list[str] = []
        completed_confidences: list[float] = []
        total_latency = 0.0
        for trace_name in self.trace_names:
            trace = example.traces[trace_name]
            if total_latency + trace.latency_s > deadline_s:
                break
            total_latency += trace.latency_s
            completed_names.append(trace_name)
            completed_answers.append(trace.answer)
            completed_confidences.append(trace.confidence)
        if not completed_answers:
            return PolicyOutcome(
                prompt_id=example.prompt_id,
                policy_id=self.policy_id,
                deadline_s=deadline_s,
                predicted_answer=None,
                correct=False,
                finished=False,
                latency_s=None,
                utility=0,
                details={"completed_traces": [], "vote_count": 0},
            )
        predicted_answer = _majority_vote(completed_answers, completed_confidences)
        correct = is_correct(predicted_answer, example.answer)
        return PolicyOutcome(
            prompt_id=example.prompt_id,
            policy_id=self.policy_id,
            deadline_s=deadline_s,
            predicted_answer=predicted_answer,
            correct=correct,
            finished=True,
            latency_s=total_latency,
            utility=deadline_utility(correct, True),
            details={
                "completed_traces": completed_names,
                "vote_count": len(completed_answers),
                "completed_confidences": completed_confidences,
            },
        )


class BudgetAwarePolicy(Policy):
    def __init__(
        self,
        policy_id: str,
        greedy_trace: str,
        fallback_trace: str,
        confidence_threshold: float,
    ) -> None:
        super().__init__(policy_id)
        self.greedy_trace = greedy_trace
        self.fallback_trace = fallback_trace
        self.confidence_threshold = confidence_threshold

    def run(self, example: PromptExample, deadline_s: float) -> PolicyOutcome:
        greedy = example.traces[self.greedy_trace]
        if greedy.latency_s > deadline_s:
            return PolicyOutcome(
                prompt_id=example.prompt_id,
                policy_id=self.policy_id,
                deadline_s=deadline_s,
                predicted_answer=None,
                correct=False,
                finished=False,
                latency_s=None,
                utility=0,
                details={"stage": "timeout_before_greedy"},
            )

        predicted_answer = greedy.answer
        latency_s = greedy.latency_s
        stage = "greedy_stop"
        if greedy.confidence < self.confidence_threshold:
            fallback = example.traces[self.fallback_trace]
            if greedy.latency_s + fallback.latency_s <= deadline_s and fallback.confidence > greedy.confidence:
                predicted_answer = fallback.answer
                latency_s = greedy.latency_s + fallback.latency_s
                stage = "fallback_used"
            else:
                stage = "fallback_skipped"

        correct = is_correct(predicted_answer, example.answer)
        return PolicyOutcome(
            prompt_id=example.prompt_id,
            policy_id=self.policy_id,
            deadline_s=deadline_s,
            predicted_answer=predicted_answer,
            correct=correct,
            finished=True,
            latency_s=latency_s,
            utility=deadline_utility(correct, True),
            details={"stage": stage, "greedy_confidence": greedy.confidence},
        )


class SelectiveAbstainPolicy(Policy):
    def __init__(
        self,
        policy_id: str,
        trace_name: str,
        confidence_threshold: float,
    ) -> None:
        super().__init__(policy_id)
        self.trace_name = trace_name
        self.confidence_threshold = confidence_threshold

    def run(self, example: PromptExample, deadline_s: float) -> PolicyOutcome:
        trace = example.traces[self.trace_name]
        if trace.latency_s > deadline_s:
            return PolicyOutcome(
                prompt_id=example.prompt_id,
                policy_id=self.policy_id,
                deadline_s=deadline_s,
                predicted_answer=None,
                correct=False,
                finished=False,
                latency_s=None,
                utility=0,
                details={"stage": "timeout_before_trace", "confidence": trace.confidence},
            )

        if trace.confidence < self.confidence_threshold:
            return PolicyOutcome(
                prompt_id=example.prompt_id,
                policy_id=self.policy_id,
                deadline_s=deadline_s,
                predicted_answer=None,
                correct=False,
                finished=True,
                latency_s=trace.latency_s,
                utility=0,
                details={"stage": "abstain", "confidence": trace.confidence},
            )

        predicted_answer = trace.answer
        correct = is_correct(predicted_answer, example.answer)
        return PolicyOutcome(
            prompt_id=example.prompt_id,
            policy_id=self.policy_id,
            deadline_s=deadline_s,
            predicted_answer=predicted_answer,
            correct=correct,
            finished=True,
            latency_s=trace.latency_s,
            utility=deadline_utility(correct, True),
            details={"stage": "answer", "confidence": trace.confidence},
        )


def _majority_vote(answers: list[str], confidences: list[float]) -> str:
    votes: dict[str, int] = defaultdict(int)
    confidence_mass: dict[str, float] = defaultdict(float)
    first_seen: dict[str, int] = {}
    for index, answer in enumerate(answers):
        votes[answer] += 1
        confidence_mass[answer] += confidences[index]
        first_seen.setdefault(answer, index)
    ordered = sorted(
        votes,
        key=lambda answer: (
            votes[answer],
            confidence_mass[answer],
            -first_seen[answer],
        ),
        reverse=True,
    )
    return ordered[0]


def build_policies(raw_policies: list[dict[str, Any]]) -> list[Policy]:
    policies: list[Policy] = []
    for raw in raw_policies:
        policy_type = raw["type"]
        policy_id = raw["id"]
        if policy_type == "greedy":
            policies.append(GreedyPolicy(policy_id, raw.get("trace_name", "greedy")))
        elif policy_type == "self_consistency":
            policies.append(SelfConsistencyPolicy(policy_id, list(raw["trace_names"])))
        elif policy_type == "budget_aware":
            policies.append(
                BudgetAwarePolicy(
                    policy_id=policy_id,
                    greedy_trace=raw.get("greedy_trace", "greedy"),
                    fallback_trace=raw.get("fallback_trace", "deliberate"),
                    confidence_threshold=float(raw.get("confidence_threshold", 0.8)),
                )
            )
        elif policy_type == "selective_abstain":
            policies.append(
                SelectiveAbstainPolicy(
                    policy_id=policy_id,
                    trace_name=raw.get("trace_name", "greedy"),
                    confidence_threshold=float(raw.get("confidence_threshold", 0.75)),
                )
            )
        else:
            raise ValueError(f"Unsupported policy type: {policy_type}")
    return policies
