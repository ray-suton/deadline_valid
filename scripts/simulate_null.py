from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from statistics import median

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.fixed_horizon import fixed_horizon_summary, naive_repeated_peeking
from src.sequential_test import evaluate_trace
from src.utility import ensure_dir, write_json


def write_csv(path: str, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def generate_records(
    prompts: int,
    tie_rate: float,
    win_probability: float,
    rng: random.Random,
) -> list[tuple[str, int, int]]:
    records: list[tuple[str, int, int]] = []
    for prompt_index in range(prompts):
        if rng.random() < tie_rate:
            utility_a = 0
            utility_b = 0
        elif rng.random() < win_probability:
            utility_a = 1
            utility_b = 0
        else:
            utility_a = 0
            utility_b = 1
        records.append((f"sim_{prompt_index + 1}", utility_a, utility_b))
    return records


def stop_step_stats(stop_steps: list[int]) -> tuple[float | None, float | None]:
    if not stop_steps:
        return None, None
    return round(float(median(stop_steps)), 2), round(sum(stop_steps) / len(stop_steps), 2)


def simulate_rejection_rates(
    trials: int,
    prompts: int,
    tie_rate: float,
    alpha: float,
    seed: int,
    win_probability: float,
) -> dict[str, object]:
    rng = random.Random(seed)
    sequential_rejects = 0
    fixed_rejects = 0
    naive_rejects = 0
    sequential_stop_steps: list[int] = []
    naive_stop_steps: list[int] = []
    example_trace = None

    for _ in range(trials):
        records = generate_records(
            prompts=prompts,
            tie_rate=tie_rate,
            win_probability=win_probability,
            rng=rng,
        )
        sequential = evaluate_trace(records, alpha=alpha)
        fixed = fixed_horizon_summary(records, alpha=alpha)
        naive = naive_repeated_peeking(records, alpha=alpha)
        sequential_rejects += int(sequential["decision"] == "reject_null")
        fixed_rejects += int(fixed["reject_null"])
        naive_rejects += int(bool(naive["stop_step"]))
        if sequential["stop_step"] is not None:
            sequential_stop_steps.append(int(sequential["stop_step"]))
        if naive["stop_step"] is not None:
            naive_stop_steps.append(int(naive["stop_step"]))
        if example_trace is None:
            example_trace = {
                "sequential": sequential,
                "fixed_horizon": fixed,
                "naive_peeking": naive,
            }

    median_sequential_stop_step, mean_sequential_stop_step = stop_step_stats(sequential_stop_steps)
    median_naive_stop_step, mean_naive_stop_step = stop_step_stats(naive_stop_steps)
    return {
        "trials": trials,
        "prompts": prompts,
        "tie_rate": tie_rate,
        "alpha": alpha,
        "seed": seed,
        "win_probability": win_probability,
        "expected_mean_difference": round((1.0 - tie_rate) * ((2.0 * win_probability) - 1.0), 6),
        "sequential_reject_rate": round(sequential_rejects / trials, 6),
        "fixed_reject_rate": round(fixed_rejects / trials, 6),
        "naive_reject_rate": round(naive_rejects / trials, 6),
        "median_sequential_stop_step": median_sequential_stop_step,
        "mean_sequential_stop_step": mean_sequential_stop_step,
        "median_naive_stop_step": median_naive_stop_step,
        "mean_naive_stop_step": mean_naive_stop_step,
        "example_trace": example_trace,
    }


def simulate_null(
    trials: int,
    prompts: int,
    tie_rate: float,
    alpha: float,
    seed: int,
) -> dict[str, object]:
    summary = simulate_rejection_rates(
        trials=trials,
        prompts=prompts,
        tie_rate=tie_rate,
        alpha=alpha,
        seed=seed,
        win_probability=0.5,
    )
    return {
        "trials": trials,
        "prompts": prompts,
        "tie_rate": tie_rate,
        "alpha": alpha,
        "seed": seed,
        "sequential_false_positive_rate": summary["sequential_reject_rate"],
        "fixed_false_positive_rate": summary["fixed_reject_rate"],
        "naive_false_positive_rate": summary["naive_reject_rate"],
        "example_trace": summary["example_trace"],
    }


def simulate_power_grid(
    trials: int,
    prompt_grid: list[int],
    tie_rate: float,
    alpha: float,
    seed: int,
    win_probabilities: list[float],
    target_power: float,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for config_index, win_probability in enumerate(sorted(win_probabilities)):
        for prompt_index, prompts in enumerate(sorted(prompt_grid)):
            config_seed = seed + (config_index * 10_000) + prompt_index
            summary = simulate_rejection_rates(
                trials=trials,
                prompts=prompts,
                tie_rate=tie_rate,
                alpha=alpha,
                seed=config_seed,
                win_probability=win_probability,
            )
            rows.append(
                {
                    "prompts": prompts,
                    "win_probability": win_probability,
                    "expected_mean_difference": summary["expected_mean_difference"],
                    "sequential_power": summary["sequential_reject_rate"],
                    "fixed_power": summary["fixed_reject_rate"],
                    "naive_reject_rate": summary["naive_reject_rate"],
                    "median_sequential_stop_step": summary["median_sequential_stop_step"],
                    "mean_sequential_stop_step": summary["mean_sequential_stop_step"],
                }
            )

    recommendations: list[dict[str, object]] = []
    for win_probability in sorted(win_probabilities):
        matching_rows = [row for row in rows if float(row["win_probability"]) == float(win_probability)]
        recommended_row = next(
            (row for row in matching_rows if float(row["sequential_power"]) >= target_power),
            None,
        )
        recommendations.append(
            {
                "win_probability": win_probability,
                "expected_mean_difference": round((1.0 - tie_rate) * ((2.0 * win_probability) - 1.0), 6),
                "target_power": target_power,
                "recommended_prompt_budget": recommended_row["prompts"] if recommended_row else None,
            }
        )

    return {
        "trials": trials,
        "tie_rate": tie_rate,
        "alpha": alpha,
        "seed": seed,
        "target_power": target_power,
        "prompt_grid": sorted(prompt_grid),
        "win_probabilities": sorted(win_probabilities),
        "rows": rows,
        "recommendations": recommendations,
    }


def render_power_markdown(summary: dict[str, object]) -> str:
    rows = list(summary["rows"])
    recommendations = list(summary["recommendations"])
    lines = [
        "# Power Simulation Summary",
        "",
        f"- Trials per grid point: {summary['trials']}",
        f"- Tie rate: {float(summary['tie_rate']):.2f}",
        f"- Alpha: {float(summary['alpha']):.2f}",
        f"- Target power: {float(summary['target_power']):.2f}",
        "",
        "## Grid Results",
        "",
        "| Win prob | Expected mean diff | Prompts | Sequential power | Fixed power | Median seq stop |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        median_stop = (
            ""
            if row["median_sequential_stop_step"] is None
            else f"{float(row['median_sequential_stop_step']):.2f}"
        )
        lines.append(
            "| "
            f"{float(row['win_probability']):.2f} | "
            f"{float(row['expected_mean_difference']):.3f} | "
            f"{int(row['prompts'])} | "
            f"{float(row['sequential_power']):.3f} | "
            f"{float(row['fixed_power']):.3f} | "
            f"{median_stop} |"
        )

    lines.extend(["", "## Prompt Budget Recommendations", ""])
    for recommendation in recommendations:
        recommended_budget = recommendation["recommended_prompt_budget"]
        if recommended_budget is None:
            lines.append(
                f"- Win prob {float(recommendation['win_probability']):.2f} "
                f"(expected mean diff {float(recommendation['expected_mean_difference']):.3f}): "
                "no prompt budget in the current grid reached target power."
            )
        else:
            lines.append(
                f"- Win prob {float(recommendation['win_probability']):.2f} "
                f"(expected mean diff {float(recommendation['expected_mean_difference']):.3f}): "
                f"{int(recommended_budget)} prompts reaches target sequential power."
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--prompts", type=int, default=80)
    parser.add_argument("--tie-rate", type=float, default=0.35)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--power-prompt-grid", type=int, nargs="+", default=[40, 80, 120, 160])
    parser.add_argument("--power-win-probabilities", type=float, nargs="+", default=[0.55, 0.6, 0.65, 0.7])
    parser.add_argument("--target-power", type=float, default=0.8)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    ensure_dir(args.out)
    null_summary = simulate_null(
        trials=args.trials,
        prompts=args.prompts,
        tie_rate=args.tie_rate,
        alpha=args.alpha,
        seed=args.seed,
    )
    power_summary = simulate_power_grid(
        trials=args.trials,
        prompt_grid=list(args.power_prompt_grid),
        tie_rate=args.tie_rate,
        alpha=args.alpha,
        seed=args.seed,
        win_probabilities=list(args.power_win_probabilities),
        target_power=args.target_power,
    )
    write_json(os.path.join(args.out, "null_simulation_summary.json"), null_summary)
    write_json(os.path.join(args.out, "power_simulation_summary.json"), power_summary)
    write_csv(
        os.path.join(args.out, "power_simulation_summary.csv"),
        list(power_summary["rows"]),
        [
            "prompts",
            "win_probability",
            "expected_mean_difference",
            "sequential_power",
            "fixed_power",
            "naive_reject_rate",
            "median_sequential_stop_step",
            "mean_sequential_stop_step",
        ],
    )
    write_markdown(
        os.path.join(args.out, "power_simulation_summary.md"),
        render_power_markdown(power_summary),
    )
    print(
        "Sequential FPR:",
        null_summary["sequential_false_positive_rate"],
        "Fixed FPR:",
        null_summary["fixed_false_positive_rate"],
        "Naive FPR:",
        null_summary["naive_false_positive_rate"],
    )
    print(
        "Power study grid points:",
        len(power_summary["rows"]),
        "Recommendations with target power:",
        sum(
            1
            for row in power_summary["recommendations"]
            if row["recommended_prompt_budget"] is not None
        ),
    )


if __name__ == "__main__":
    main()
