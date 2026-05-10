from __future__ import annotations

import argparse
import itertools
import os
from datetime import datetime, timezone

from src.fixed_horizon import fixed_horizon_summary, naive_repeated_peeking
from src.policies import build_policies
from src.sequential_test import evaluate_trace
from src.utility import (
    ensure_dir,
    format_deadline_label,
    load_benchmark,
    load_json,
    resolve_path,
    write_json,
)


def expand_comparison_pairs(
    pairs: list[list[str]],
    include_reverse_pairs: bool,
) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for left_id, right_id in pairs:
        for candidate in (
            [(left_id, right_id), (right_id, left_id)]
            if include_reverse_pairs
            else [(left_id, right_id)]
        ):
            if candidate not in seen:
                ordered.append(candidate)
                seen.add(candidate)
    return ordered


def outcome_payload(outcome: object, benchmark_id: str) -> dict[str, object]:
    payload = outcome.to_dict()
    payload["benchmark_id"] = benchmark_id
    payload["deadline_label"] = format_deadline_label(float(payload["deadline_s"]))
    return payload


def reference_outcome_payload(outcome: object, benchmark_id: str) -> dict[str, object]:
    payload = outcome.to_dict()
    payload.pop("deadline_s", None)
    payload["benchmark_id"] = benchmark_id
    payload["reference_mode"] = "no_time_limit"
    payload["reference_label"] = "no_limit"
    return payload


def summarize_runs(
    *,
    benchmark_id: str,
    policy_id: str,
    prompt_runs: list[dict[str, object]],
    deadline_s: float | None = None,
    reference_mode: str | None = None,
) -> dict[str, object]:
    summary = {
        "benchmark_id": benchmark_id,
        "policy_id": policy_id,
        "mean_utility": round(sum(int(row["utility"]) for row in prompt_runs) / len(prompt_runs), 6),
        "prompt_count": len(prompt_runs),
        "mean_latency_s": round(
            sum(float(row["latency_s"]) for row in prompt_runs if row["latency_s"] is not None)
            / max(1, sum(1 for row in prompt_runs if row["latency_s"] is not None)),
            6,
        ),
    }
    if deadline_s is not None:
        summary["deadline_s"] = deadline_s
        summary["deadline_label"] = format_deadline_label(deadline_s)
    if reference_mode is not None:
        summary["reference_mode"] = reference_mode
        summary["reference_label"] = "no_limit"
    return summary


def compare_runs(
    *,
    benchmark_id: str,
    left_id: str,
    right_id: str,
    left_runs: list[dict[str, object]],
    right_runs: list[dict[str, object]],
    alpha: float,
    deadline_s: float | None = None,
    reference_mode: str | None = None,
) -> dict[str, object]:
    records = [
        (left["prompt_id"], int(left["utility"]), int(right["utility"]))
        for left, right in zip(left_runs, right_runs)
    ]
    mean_utility_a = round(
        sum(int(row["utility"]) for row in left_runs) / len(left_runs),
        6,
    )
    mean_utility_b = round(
        sum(int(row["utility"]) for row in right_runs) / len(right_runs),
        6,
    )
    payload = {
        "benchmark_id": benchmark_id,
        "policy_a": left_id,
        "policy_b": right_id,
        "mean_utility_a": mean_utility_a,
        "mean_utility_b": mean_utility_b,
        "mean_difference": round(mean_utility_a - mean_utility_b, 6),
        "sequential": evaluate_trace(records, alpha=alpha),
        "fixed_horizon": fixed_horizon_summary(records, alpha=alpha),
        "naive_peeking": naive_repeated_peeking(records, alpha=alpha),
    }
    if deadline_s is not None:
        payload["deadline_s"] = deadline_s
        payload["deadline_label"] = format_deadline_label(deadline_s)
    if reference_mode is not None:
        payload["reference_mode"] = reference_mode
        payload["reference_label"] = "no_limit"
    return payload


def run_evaluation(
    benchmarks_config_path: str,
    policies_config_path: str,
    out_dir: str,
    alpha: float = 0.05,
) -> dict[str, object]:
    benchmark_config = load_json(benchmarks_config_path)
    policy_config = load_json(policies_config_path)
    ensure_dir(out_dir)

    policies = build_policies(policy_config["policies"])
    policy_by_id = {policy.policy_id: policy for policy in policies}
    deadlines = [float(value) for value in benchmark_config["deadlines"]]

    all_prompt_runs: list[dict[str, object]] = []
    all_comparisons: list[dict[str, object]] = []
    utility_summary: list[dict[str, object]] = []
    reference_prompt_runs: list[dict[str, object]] = []
    reference_comparisons: list[dict[str, object]] = []
    reference_summary: list[dict[str, object]] = []

    for benchmark in benchmark_config["benchmarks"]:
        benchmark_path = resolve_path(benchmarks_config_path, benchmark["path"])
        examples = load_benchmark(benchmark_path)
        comparison_pairs = benchmark.get("comparison_pairs")
        if not comparison_pairs:
            comparison_pairs = [
                [left.policy_id, right.policy_id]
                for left, right in itertools.combinations(policies, 2)
            ]
        comparison_pairs = expand_comparison_pairs(
            comparison_pairs,
            include_reverse_pairs=bool(benchmark.get("include_reverse_pairs", True)),
        )

        reference_outcomes_by_policy: dict[str, list[dict[str, object]]] = {}
        for policy in policies:
            prompt_runs = []
            for example in examples:
                outcome = policy.run(example, float("inf"))
                payload = reference_outcome_payload(outcome, benchmark["id"])
                prompt_runs.append(payload)
                reference_prompt_runs.append(payload)
            reference_outcomes_by_policy[policy.policy_id] = prompt_runs
            reference_summary.append(
                summarize_runs(
                    benchmark_id=benchmark["id"],
                    policy_id=policy.policy_id,
                    prompt_runs=prompt_runs,
                    reference_mode="no_time_limit",
                )
            )
        for left_id, right_id in comparison_pairs:
            if left_id not in policy_by_id or right_id not in policy_by_id:
                raise ValueError(f"Unknown policy pair: {left_id}, {right_id}")
            reference_comparisons.append(
                compare_runs(
                    benchmark_id=benchmark["id"],
                    left_id=left_id,
                    right_id=right_id,
                    left_runs=reference_outcomes_by_policy[left_id],
                    right_runs=reference_outcomes_by_policy[right_id],
                    alpha=alpha,
                    reference_mode="no_time_limit",
                )
            )

        for deadline_s in deadlines:
            outcomes_by_policy: dict[str, list[dict[str, object]]] = {}
            for policy in policies:
                prompt_runs = []
                for example in examples:
                    outcome = policy.run(example, deadline_s)
                    payload = outcome_payload(outcome, benchmark["id"])
                    prompt_runs.append(payload)
                    all_prompt_runs.append(payload)
                outcomes_by_policy[policy.policy_id] = prompt_runs
                utility_summary.append(
                    summarize_runs(
                        benchmark_id=benchmark["id"],
                        policy_id=policy.policy_id,
                        prompt_runs=prompt_runs,
                        deadline_s=deadline_s,
                    )
                )
            for left_id, right_id in comparison_pairs:
                if left_id not in policy_by_id or right_id not in policy_by_id:
                    raise ValueError(f"Unknown policy pair: {left_id}, {right_id}")
                all_comparisons.append(
                    compare_runs(
                        benchmark_id=benchmark["id"],
                        left_id=left_id,
                        right_id=right_id,
                        left_runs=outcomes_by_policy[left_id],
                        right_runs=outcomes_by_policy[right_id],
                        alpha=alpha,
                        deadline_s=deadline_s,
                    )
                )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmarks_config_path": os.path.abspath(benchmarks_config_path),
        "policies_config_path": os.path.abspath(policies_config_path),
        "alpha": alpha,
        "prompt_run_count": len(all_prompt_runs),
        "comparison_count": len(all_comparisons),
        "reference_prompt_run_count": len(reference_prompt_runs),
        "reference_comparison_count": len(reference_comparisons),
    }
    write_json(os.path.join(out_dir, "manifest.json"), manifest)
    write_json(os.path.join(out_dir, "prompt_runs.json"), all_prompt_runs)
    write_json(os.path.join(out_dir, "utility_summary.json"), utility_summary)
    write_json(os.path.join(out_dir, "comparison_summaries.json"), all_comparisons)
    write_json(os.path.join(out_dir, "reference_prompt_runs.json"), reference_prompt_runs)
    write_json(os.path.join(out_dir, "reference_summary.json"), reference_summary)
    write_json(os.path.join(out_dir, "reference_comparison_summaries.json"), reference_comparisons)
    return {
        "manifest": manifest,
        "prompt_runs": all_prompt_runs,
        "utility_summary": utility_summary,
        "comparison_summaries": all_comparisons,
        "reference_prompt_runs": reference_prompt_runs,
        "reference_summary": reference_summary,
        "reference_comparison_summaries": reference_comparisons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmarks", required=True)
    parser.add_argument("--policies", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()
    result = run_evaluation(
        benchmarks_config_path=args.benchmarks,
        policies_config_path=args.policies,
        out_dir=args.out,
        alpha=args.alpha,
    )
    print(
        "Wrote",
        result["manifest"]["prompt_run_count"],
        "prompt runs and",
        result["manifest"]["comparison_count"],
        "comparisons to",
        args.out,
    )


if __name__ == "__main__":
    main()
