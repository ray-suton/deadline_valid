from __future__ import annotations

import math

from src.sequential_test import paired_outcome


def one_sided_sign_test_pvalue(wins: int, losses: int) -> float:
    total = wins + losses
    if total == 0:
        return 1.0
    return sum(math.comb(total, k) for k in range(wins, total + 1)) / (2**total)


def fixed_horizon_summary(records: list[tuple[str, int, int]], alpha: float = 0.05) -> dict[str, object]:
    wins = 0
    losses = 0
    ties = 0
    for _, u_a, u_b in records:
        outcome = paired_outcome(u_a, u_b)
        if outcome == 1:
            wins += 1
        elif outcome == -1:
            losses += 1
        else:
            ties += 1
    pvalue = one_sided_sign_test_pvalue(wins, losses)
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "discordant": wins + losses,
        "p_value": round(pvalue, 8),
        "reject_null": pvalue <= alpha,
    }


def naive_repeated_peeking(records: list[tuple[str, int, int]], alpha: float = 0.05) -> dict[str, object]:
    wins = 0
    losses = 0
    ties = 0
    trace: list[dict[str, object]] = []
    stop_step = None
    for step, (prompt_id, u_a, u_b) in enumerate(records, start=1):
        outcome = paired_outcome(u_a, u_b)
        if outcome == 1:
            wins += 1
        elif outcome == -1:
            losses += 1
        else:
            ties += 1
        pvalue = one_sided_sign_test_pvalue(wins, losses)
        stopped = pvalue <= alpha
        trace.append(
            {
                "step": step,
                "prompt_id": prompt_id,
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "p_value": round(pvalue, 8),
                "stopped": stopped,
            }
        )
        if stopped:
            stop_step = step
            break
    final_p = trace[-1]["p_value"] if trace else 1.0
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "discordant": wins + losses,
        "final_p_value": final_p,
        "stopped_early": stop_step is not None,
        "stop_step": stop_step,
        "trace": trace,
    }
