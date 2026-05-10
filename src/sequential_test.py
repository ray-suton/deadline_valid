from __future__ import annotations

import math
from dataclasses import dataclass


DEFAULT_GRID = (0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)


@dataclass
class TraceStep:
    step: int
    prompt_id: str
    wins: int
    losses: int
    ties: int
    discordant: int
    e_value: float
    log_e_value: float
    stopped: bool
    decision: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "prompt_id": self.prompt_id,
            "wins": self.wins,
            "losses": self.losses,
            "ties": self.ties,
            "discordant": self.discordant,
            "e_value": round(self.e_value, 8),
            "log_e_value": round(self.log_e_value, 8),
            "stopped": self.stopped,
            "decision": self.decision,
        }


class SignMixtureEProcess:
    def __init__(self, alpha: float = 0.05, grid: tuple[float, ...] = DEFAULT_GRID) -> None:
        self.alpha = alpha
        self.threshold = 1.0 / alpha
        self.grid = grid
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self._log_weights = [math.log(1.0 / len(grid)) for _ in grid]

    def update(self, outcome: int) -> None:
        if outcome not in (-1, 0, 1):
            raise ValueError(f"Outcome must be -1, 0, or 1; got {outcome}")
        if outcome == 1:
            self.wins += 1
        elif outcome == -1:
            self.losses += 1
        else:
            self.ties += 1

    @property
    def discordant(self) -> int:
        return self.wins + self.losses

    def e_value(self) -> float:
        if self.discordant == 0:
            return 1.0
        log_terms = []
        for weight, alt in zip(self._log_weights, self.grid):
            log_lr = self.wins * math.log(2.0 * alt) + self.losses * math.log(2.0 * (1.0 - alt))
            log_terms.append(weight + log_lr)
        max_log = max(log_terms)
        return math.exp(max_log) * sum(math.exp(term - max_log) for term in log_terms)

    def log_e_value(self) -> float:
        return math.log(self.e_value())

    def decision(self) -> str:
        return "reject_null" if self.e_value() >= self.threshold else "continue"


def paired_outcome(u_a: int, u_b: int) -> int:
    if u_a > u_b:
        return 1
    if u_b > u_a:
        return -1
    return 0


def evaluate_trace(
    records: list[tuple[str, int, int]],
    alpha: float = 0.05,
    grid: tuple[float, ...] = DEFAULT_GRID,
) -> dict[str, object]:
    test = SignMixtureEProcess(alpha=alpha, grid=grid)
    trace: list[dict[str, object]] = []
    stop_step = None
    for step, (prompt_id, u_a, u_b) in enumerate(records, start=1):
        test.update(paired_outcome(u_a, u_b))
        decision = test.decision()
        stopped = decision == "reject_null"
        trace_step = TraceStep(
            step=step,
            prompt_id=prompt_id,
            wins=test.wins,
            losses=test.losses,
            ties=test.ties,
            discordant=test.discordant,
            e_value=test.e_value(),
            log_e_value=test.log_e_value(),
            stopped=stopped,
            decision=decision,
        )
        trace.append(trace_step.to_dict())
        if stopped and stop_step is None:
            stop_step = step
            break
    return {
        "alpha": alpha,
        "threshold": round(test.threshold, 8),
        "wins": test.wins,
        "losses": test.losses,
        "ties": test.ties,
        "discordant": test.discordant,
        "final_e_value": round(test.e_value(), 8),
        "decision": test.decision(),
        "stopped_early": stop_step is not None,
        "stop_step": stop_step,
        "trace": trace,
    }
