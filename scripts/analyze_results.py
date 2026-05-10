from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.utility import ensure_dir, format_deadline_label, load_benchmark, load_json, normalize_answer, resolve_path

UTILITY_SUMMARY_FIELDNAMES = [
    "benchmark_id",
    "policy_id",
    "deadline_s",
    "deadline_label",
    "mean_utility",
    "prompt_count",
    "mean_latency_s",
]

COMPARISON_FIELDNAMES = [
    "benchmark_id",
    "deadline_s",
    "policy_a",
    "policy_b",
    "mean_utility_a",
    "mean_utility_b",
    "mean_difference",
    "final_e_value",
    "seq_decision",
    "seq_stop_step",
    "fixed_p_value",
    "fixed_reject",
    "naive_stop_step",
    "naive_final_p_value",
]

REFERENCE_COMPARISON_FIELDNAMES = [
    "benchmark_id",
    "reference_mode",
    "reference_label",
    *COMPARISON_FIELDNAMES[2:],
]

DECISION_FIELDNAMES = [
    "benchmark_id",
    "deadline_s",
    "policy_a",
    "policy_b",
    "mean_difference",
    "seq_decision",
    "seq_stop_step",
    "fixed_reject",
    "naive_stop_step",
]

REFERENCE_DECISION_FIELDNAMES = [
    "benchmark_id",
    "reference_label",
    *DECISION_FIELDNAMES[2:],
]

REFERENCE_SUMMARY_FIELDNAMES = [
    "benchmark_id",
    "policy_id",
    "reference_mode",
    "reference_label",
    "mean_utility",
    "prompt_count",
    "mean_latency_s",
]

DIFFICULTY_UTILITY_FIELDNAMES = [
    "benchmark_id",
    "difficulty",
    "policy_id",
    "deadline_s",
    "deadline_label",
    "mean_utility",
    "prompt_count",
    "mean_latency_s",
]

DIFFICULTY_LEADERBOARD_FIELDNAMES = [
    "benchmark_id",
    "difficulty",
    "deadline_s",
    "deadline_label",
    "best_policy",
    "best_mean_utility",
    "runner_up_policy",
    "runner_up_mean_utility",
    "margin",
]

REFERENCE_METADATA_FIELDS = ("reference_mode", "reference_label")


def write_csv(path: str, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def build_comparison_row(
    comparison: dict[str, object],
    extra_fields: tuple[str, ...] = (),
    include_deadline: bool = True,
) -> dict[str, object]:
    row = {
        "benchmark_id": comparison["benchmark_id"],
        "policy_a": comparison["policy_a"],
        "policy_b": comparison["policy_b"],
        "mean_utility_a": comparison["mean_utility_a"],
        "mean_utility_b": comparison["mean_utility_b"],
        "mean_difference": comparison["mean_difference"],
        "final_e_value": comparison["sequential"]["final_e_value"],
        "seq_decision": comparison["sequential"]["decision"],
        "seq_stop_step": comparison["sequential"]["stop_step"],
        "fixed_p_value": comparison["fixed_horizon"]["p_value"],
        "fixed_reject": comparison["fixed_horizon"]["reject_null"],
        "naive_stop_step": comparison["naive_peeking"]["stop_step"],
        "naive_final_p_value": comparison["naive_peeking"]["final_p_value"],
    }
    if include_deadline:
        row["deadline_s"] = comparison["deadline_s"]
    for field in extra_fields:
        row[field] = comparison[field]
    return row


def svg_line_chart(
    path: str,
    title: str,
    series: dict[str, list[tuple[float, float]]],
    x_label: str,
    y_label: str,
) -> None:
    width = 720
    height = 420
    left = 70
    right = 20
    top = 50
    bottom = 55
    plot_width = width - left - right
    plot_height = height - top - bottom

    x_values = [x for points in series.values() for x, _ in points]
    y_values = [y for points in series.values() for _, y in points]
    min_x = min(x_values)
    max_x = max(x_values)
    min_y = min(0.0, min(y_values))
    max_y = max(1.0, max(y_values))

    def scale_x(x: float) -> float:
        if max_x == min_x:
            return left + plot_width / 2.0
        return left + ((x - min_x) / (max_x - min_x)) * plot_width

    def scale_y(y: float) -> float:
        if max_y == min_y:
            return top + plot_height / 2.0
        return top + plot_height - ((y - min_y) / (max_y - min_y)) * plot_height

    colors = ["#0b6e4f", "#b5651d", "#1d4ed8", "#b91c1c"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-size="20" font-family="monospace">{title}</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222"/>',
        f'<text x="{width / 2}" y="{height - 12}" text-anchor="middle" font-size="14" font-family="monospace">{x_label}</text>',
        f'<text x="18" y="{height / 2}" text-anchor="middle" transform="rotate(-90 18 {height / 2})" font-size="14" font-family="monospace">{y_label}</text>',
    ]
    for tick in range(5):
        y_value = min_y + ((max_y - min_y) * tick / 4.0)
        y = scale_y(y_value)
        parts.append(f'<line x1="{left - 5}" y1="{y}" x2="{left}" y2="{y}" stroke="#222"/>')
        parts.append(
            f'<text x="{left - 10}" y="{y + 4}" text-anchor="end" font-size="11" font-family="monospace">{y_value:.2f}</text>'
        )
    for tick, x_value in enumerate(sorted(set(x_values))):
        x = scale_x(x_value)
        parts.append(f'<line x1="{x}" y1="{top + plot_height}" x2="{x}" y2="{top + plot_height + 5}" stroke="#222"/>')
        parts.append(
            f'<text x="{x}" y="{top + plot_height + 20}" text-anchor="middle" font-size="11" font-family="monospace">{x_value:.1f}</text>'
        )
    for index, (label, points) in enumerate(series.items()):
        color = colors[index % len(colors)]
        ordered = sorted(points)
        polyline = " ".join(f"{scale_x(x):.1f},{scale_y(y):.1f}" for x, y in ordered)
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{polyline}"/>')
        for x, y in ordered:
            parts.append(f'<circle cx="{scale_x(x):.1f}" cy="{scale_y(y):.1f}" r="4" fill="{color}"/>')
        legend_y = top + 18 * index
        parts.append(f'<rect x="{width - 175}" y="{legend_y - 10}" width="10" height="10" fill="{color}"/>')
        parts.append(
            f'<text x="{width - 160}" y="{legend_y}" font-size="12" font-family="monospace">{label}</text>'
        )
    parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(parts))


def analyze_results(results_dir: str) -> dict[str, object]:
    manifest = load_json(os.path.join(results_dir, "manifest.json"))
    utility_summary = load_json(os.path.join(results_dir, "utility_summary.json"))
    comparisons = load_json(os.path.join(results_dir, "comparison_summaries.json"))
    prompt_runs = load_json(os.path.join(results_dir, "prompt_runs.json"))
    reference_summary = optional_load_json(os.path.join(results_dir, "reference_summary.json"))
    reference_comparisons = optional_load_json(
        os.path.join(results_dir, "reference_comparison_summaries.json")
    )
    reference_prompt_runs = optional_load_json(os.path.join(results_dir, "reference_prompt_runs.json"))
    analysis_dir = os.path.join(results_dir, "analysis")
    ensure_dir(analysis_dir)

    write_csv(
        os.path.join(analysis_dir, "utility_summary.csv"),
        utility_summary,
        UTILITY_SUMMARY_FIELDNAMES,
    )

    comparison_rows = [build_comparison_row(comparison) for comparison in comparisons]
    write_csv(
        os.path.join(analysis_dir, "comparison_summary.csv"),
        comparison_rows,
        COMPARISON_FIELDNAMES,
    )

    leaderboard_rows = build_leaderboard_rows(utility_summary)
    write_csv(
        os.path.join(analysis_dir, "leaderboard.csv"),
        leaderboard_rows,
        [
            "benchmark_id",
            "deadline_s",
            "best_policy",
            "best_mean_utility",
            "runner_up_policy",
            "runner_up_mean_utility",
            "margin",
        ],
    )

    prompt_lookup = load_prompt_lookup(manifest)
    difficulty_utility_rows = build_difficulty_utility_rows(prompt_runs, prompt_lookup)
    write_csv(
        os.path.join(analysis_dir, "difficulty_utility_summary.csv"),
        difficulty_utility_rows,
        DIFFICULTY_UTILITY_FIELDNAMES,
    )
    difficulty_leaderboard_rows = build_difficulty_leaderboard_rows(difficulty_utility_rows)
    write_csv(
        os.path.join(analysis_dir, "difficulty_leaderboard.csv"),
        difficulty_leaderboard_rows,
        DIFFICULTY_LEADERBOARD_FIELDNAMES,
    )

    decision_rows = build_decision_rows(comparison_rows)
    write_csv(
        os.path.join(analysis_dir, "decision_summary.csv"),
        decision_rows,
        DECISION_FIELDNAMES,
    )

    reference_rows = build_reference_rows(reference_summary)
    if reference_summary:
        write_csv(
            os.path.join(analysis_dir, "no_time_limit_summary.csv"),
            reference_summary,
            REFERENCE_SUMMARY_FIELDNAMES,
        )
    reference_decision_rows: list[dict[str, object]] = []
    if reference_comparisons:
        reference_comparison_rows = [
            build_comparison_row(
                comparison,
                extra_fields=REFERENCE_METADATA_FIELDS,
                include_deadline=False,
            )
            for comparison in reference_comparisons
        ]
        write_csv(
            os.path.join(analysis_dir, "no_time_limit_comparison_summary.csv"),
            reference_comparison_rows,
            REFERENCE_COMPARISON_FIELDNAMES,
        )
        reference_decision_rows = build_decision_rows(
            reference_comparison_rows,
            extra_fields=("reference_label",),
            include_deadline=False,
        )
        write_csv(
            os.path.join(analysis_dir, "no_time_limit_decision_summary.csv"),
            reference_decision_rows,
            REFERENCE_DECISION_FIELDNAMES,
        )

    utility_series: dict[str, list[tuple[float, float]]] = {}
    for row in utility_summary:
        utility_series.setdefault(row["policy_id"], []).append((row["deadline_s"], row["mean_utility"]))
    svg_line_chart(
        os.path.join(analysis_dir, "utility_by_deadline.svg"),
        title="Mean Deadline Utility",
        series=utility_series,
        x_label="deadline_s",
        y_label="mean_utility",
    )

    if comparisons:
        first = comparisons[0]
        evidence_series = {
            f"{first['policy_a']} vs {first['policy_b']}": [
                (float(step["step"]), float(step["e_value"])) for step in first["sequential"]["trace"]
            ]
        }
        svg_line_chart(
            os.path.join(analysis_dir, "evidence_trace.svg"),
            title="Sequential Evidence Trace",
            series=evidence_series,
            x_label="prompt_index",
            y_label="e_value",
        )

    write_markdown(
        os.path.join(analysis_dir, "summary.md"),
        render_summary_markdown(
            results_dir=results_dir,
            leaderboard_rows=leaderboard_rows,
            decision_rows=decision_rows,
            reference_rows=reference_rows,
            difficulty_leaderboard_rows=difficulty_leaderboard_rows,
        ),
    )

    sample_cases = build_sample_cases(
        prompt_runs=prompt_runs,
        reference_prompt_runs=reference_prompt_runs,
        prompt_lookup=prompt_lookup,
        max_cases=5,
    )
    write_markdown(
        os.path.join(analysis_dir, "sample_cases.md"),
        render_sample_cases_markdown(sample_cases),
    )

    summary = {
        "analysis_dir": analysis_dir,
        "utility_row_count": len(utility_summary),
        "comparison_row_count": len(comparison_rows),
        "leaderboard_row_count": len(leaderboard_rows),
        "decision_row_count": len(decision_rows),
        "reference_row_count": len(reference_rows),
        "difficulty_utility_row_count": len(difficulty_utility_rows),
        "difficulty_leaderboard_row_count": len(difficulty_leaderboard_rows),
        "sample_case_count": len(sample_cases),
    }
    return summary


def optional_load_json(path: str) -> list[dict[str, object]]:
    if not os.path.exists(path):
        return []
    return load_json(path)


def build_leaderboard_rows(utility_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, float], list[dict[str, object]]] = {}
    for row in utility_summary:
        key = (str(row["benchmark_id"]), float(row["deadline_s"]))
        grouped.setdefault(key, []).append(row)

    leaderboard_rows: list[dict[str, object]] = []
    for (benchmark_id, deadline_s), rows in sorted(grouped.items()):
        ordered = sorted(
            rows,
            key=lambda row: (-float(row["mean_utility"]), str(row["policy_id"])),
        )
        best = ordered[0]
        best_value = float(best["mean_utility"])
        tied_best = [row for row in ordered if float(row["mean_utility"]) == best_value]
        next_distinct = next(
            (row for row in ordered if float(row["mean_utility"]) < best_value),
            None,
        )
        leaderboard_rows.append(
            {
                "benchmark_id": benchmark_id,
                "deadline_s": deadline_s,
                "best_policy": ",".join(str(row["policy_id"]) for row in tied_best),
                "best_mean_utility": best["mean_utility"],
                "runner_up_policy": next_distinct["policy_id"] if next_distinct else "",
                "runner_up_mean_utility": next_distinct["mean_utility"] if next_distinct else best["mean_utility"],
                "margin": round(
                    best_value
                    - float(next_distinct["mean_utility"] if next_distinct else best["mean_utility"]),
                    6,
                ),
            }
        )
    return leaderboard_rows


def build_decision_rows(
    comparison_rows: list[dict[str, object]],
    extra_fields: tuple[str, ...] = (),
    include_deadline: bool = True,
) -> list[dict[str, object]]:
    decision_rows: list[dict[str, object]] = []
    for row in comparison_rows:
        decision_row = {
            "benchmark_id": row["benchmark_id"],
            "policy_a": row["policy_a"],
            "policy_b": row["policy_b"],
            "mean_difference": row["mean_difference"],
            "seq_decision": row["seq_decision"],
            "seq_stop_step": row["seq_stop_step"],
            "fixed_reject": row["fixed_reject"],
            "naive_stop_step": row["naive_stop_step"],
        }
        if include_deadline:
            decision_row["deadline_s"] = row["deadline_s"]
        for field in extra_fields:
            decision_row[field] = row[field]
        decision_rows.append(decision_row)
    return decision_rows


def build_reference_rows(reference_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in reference_summary:
        grouped.setdefault(str(row["benchmark_id"]), []).append(row)

    rows: list[dict[str, object]] = []
    for benchmark_id, benchmark_rows in sorted(grouped.items()):
        ordered = sorted(
            benchmark_rows,
            key=lambda row: (-float(row["mean_utility"]), str(row["policy_id"])),
        )
        best = ordered[0]
        next_distinct = next(
            (row for row in ordered if float(row["mean_utility"]) < float(best["mean_utility"])),
            None,
        )
        rows.append(
            {
                "benchmark_id": benchmark_id,
                "best_policy": best["policy_id"],
                "best_mean_utility": best["mean_utility"],
                "runner_up_policy": next_distinct["policy_id"] if next_distinct else "",
                "runner_up_mean_utility": next_distinct["mean_utility"] if next_distinct else best["mean_utility"],
                "margin": round(
                    float(best["mean_utility"])
                    - float(next_distinct["mean_utility"] if next_distinct else best["mean_utility"]),
                    6,
                ),
            }
        )
    return rows


def summarize_group(
    *,
    benchmark_id: str,
    policy_id: str,
    rows: list[dict[str, object]],
    difficulty: str,
    deadline_s: float,
) -> dict[str, object]:
    latency_values = [float(row["latency_s"]) for row in rows if row["latency_s"] is not None]
    return {
        "benchmark_id": benchmark_id,
        "difficulty": difficulty,
        "policy_id": policy_id,
        "deadline_s": deadline_s,
        "deadline_label": format_deadline_label(deadline_s),
        "mean_utility": round(sum(int(row["utility"]) for row in rows) / len(rows), 6),
        "prompt_count": len(rows),
        "mean_latency_s": round(sum(latency_values) / max(1, len(latency_values)), 6),
    }


def build_difficulty_utility_rows(
    prompt_runs: list[dict[str, object]],
    prompt_lookup: dict[tuple[str, str], dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, float, str], list[dict[str, object]]] = defaultdict(list)
    for row in prompt_runs:
        key = (str(row["benchmark_id"]), str(row["prompt_id"]))
        metadata = prompt_lookup.get(key, {}).get("metadata", {})
        difficulty = "unknown"
        if isinstance(metadata, dict):
            difficulty = str(metadata.get("difficulty", "unknown"))
        group_key = (
            str(row["benchmark_id"]),
            difficulty,
            float(row["deadline_s"]),
            str(row["policy_id"]),
        )
        grouped[group_key].append(row)

    difficulty_rows: list[dict[str, object]] = []
    for (benchmark_id, difficulty, deadline_s, policy_id), rows in sorted(grouped.items()):
        difficulty_rows.append(
            summarize_group(
                benchmark_id=benchmark_id,
                difficulty=difficulty,
                deadline_s=deadline_s,
                policy_id=policy_id,
                rows=rows,
            )
        )
    return difficulty_rows


def build_difficulty_leaderboard_rows(
    difficulty_utility_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, float], list[dict[str, object]]] = defaultdict(list)
    for row in difficulty_utility_rows:
        grouped[(str(row["benchmark_id"]), str(row["difficulty"]), float(row["deadline_s"]))].append(row)

    leaderboard_rows: list[dict[str, object]] = []
    for (benchmark_id, difficulty, deadline_s), rows in sorted(grouped.items()):
        ordered = sorted(
            rows,
            key=lambda row: (-float(row["mean_utility"]), str(row["policy_id"])),
        )
        best = ordered[0]
        best_value = float(best["mean_utility"])
        tied_best = [row for row in ordered if float(row["mean_utility"]) == best_value]
        next_distinct = next(
            (row for row in ordered if float(row["mean_utility"]) < best_value),
            None,
        )
        leaderboard_rows.append(
            {
                "benchmark_id": benchmark_id,
                "difficulty": difficulty,
                "deadline_s": deadline_s,
                "deadline_label": format_deadline_label(deadline_s),
                "best_policy": ",".join(str(row["policy_id"]) for row in tied_best),
                "best_mean_utility": best["mean_utility"],
                "runner_up_policy": next_distinct["policy_id"] if next_distinct else "",
                "runner_up_mean_utility": next_distinct["mean_utility"] if next_distinct else best["mean_utility"],
                "margin": round(
                    best_value
                    - float(next_distinct["mean_utility"] if next_distinct else best["mean_utility"]),
                    6,
                ),
            }
        )
    return leaderboard_rows


def load_prompt_lookup(manifest: dict[str, object]) -> dict[tuple[str, str], dict[str, object]]:
    benchmark_config_path = str(manifest["benchmarks_config_path"])
    benchmark_config = load_json(benchmark_config_path)
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for benchmark in benchmark_config["benchmarks"]:
        benchmark_path = resolve_path(benchmark_config_path, benchmark["path"])
        for example in load_benchmark(benchmark_path):
            lookup[(str(benchmark["id"]), example.prompt_id)] = {
                "prompt": example.prompt,
                "answer": example.answer,
                "metadata": example.metadata,
            }
    return lookup


def build_sample_cases(
    *,
    prompt_runs: list[dict[str, object]],
    reference_prompt_runs: list[dict[str, object]],
    prompt_lookup: dict[tuple[str, str], dict[str, object]],
    max_cases: int,
) -> list[dict[str, object]]:
    min_deadline_by_benchmark: dict[str, float] = {}
    for row in prompt_runs:
        benchmark_id = str(row["benchmark_id"])
        deadline_s = float(row["deadline_s"])
        min_deadline_by_benchmark[benchmark_id] = min(
            deadline_s,
            min_deadline_by_benchmark.get(benchmark_id, deadline_s),
        )

    grouped_runs: dict[tuple[str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in prompt_runs:
        benchmark_id = str(row["benchmark_id"])
        if float(row["deadline_s"]) == min_deadline_by_benchmark[benchmark_id]:
            grouped_runs[(benchmark_id, str(row["prompt_id"]))][str(row["policy_id"])] = row

    grouped_reference: dict[tuple[str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in reference_prompt_runs:
        grouped_reference[(str(row["benchmark_id"]), str(row["prompt_id"]))][
            str(row["policy_id"])
        ] = row

    scored_cases: list[tuple[tuple[int, int, int], tuple[str, str]]] = []
    for key, policy_runs in grouped_runs.items():
        utilities = {int(run["utility"]) for run in policy_runs.values()}
        predictions = {
            normalize_answer(run["predicted_answer"]) if run["predicted_answer"] is not None else "<none>"
            for run in policy_runs.values()
        }
        non_empty_predictions = sum(1 for prediction in predictions if prediction != "<none>")
        score = (len(utilities), len(predictions), non_empty_predictions)
        scored_cases.append((score, key))

    selected: list[dict[str, object]] = []
    for _, key in sorted(scored_cases, key=lambda item: item[0], reverse=True)[:max_cases]:
        benchmark_id, prompt_id = key
        selected.append(
            {
                "benchmark_id": benchmark_id,
                "prompt_id": prompt_id,
                "deadline_s": min_deadline_by_benchmark[benchmark_id],
                "prompt": prompt_lookup[key]["prompt"],
                "answer": prompt_lookup[key]["answer"],
                "policy_runs": grouped_runs[key],
                "reference_runs": grouped_reference.get(key, {}),
            }
        )
    return selected


def render_sample_cases_markdown(sample_cases: list[dict[str, object]]) -> str:
    lines = ["# Sample Cases", ""]
    if not sample_cases:
        lines.append("No sample cases were selected.")
        return "\n".join(lines) + "\n"

    for index, case in enumerate(sample_cases, start=1):
        lines.extend(
            [
                f"## {index}. {case['benchmark_id']} / {case['prompt_id']}",
                "",
                "Prompt:",
                "",
                f"`{case['prompt']}`",
                "",
                "Gold answer:",
                "",
                f"`{case['answer']}`",
                "",
                f"Displayed deadline: `{format_deadline_label(case['deadline_s'])}`",
                "",
                "| Policy | Deadline output | Utility | Finished | Latency | No-limit output | No-limit utility | Notes |",
                "| --- | --- | ---: | --- | ---: | --- | ---: | --- |",
            ]
        )
        for policy_id in sorted(case["policy_runs"]):
            run = case["policy_runs"][policy_id]
            reference_run = case["reference_runs"].get(policy_id, {})
            deadline_output = run["predicted_answer"] if run["predicted_answer"] is not None else "<none>"
            no_limit_output = (
                reference_run.get("predicted_answer")
                if reference_run.get("predicted_answer") is not None
                else "<none>"
            )
            notes = ""
            if run["details"].get("stage"):
                notes = str(run["details"]["stage"])
            elif run["details"].get("vote_count") is not None:
                notes = f"vote_count={run['details']['vote_count']}"
            lines.append(
                "| "
                f"{policy_id} | "
                f"{deadline_output} | "
                f"{int(run['utility'])} | "
                f"{run['finished']} | "
                f"{float(run['latency_s']) if run['latency_s'] is not None else ''} | "
                f"{no_limit_output} | "
                f"{int(reference_run['utility']) if reference_run else ''} | "
                f"{notes} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def render_summary_markdown(
    results_dir: str,
    leaderboard_rows: list[dict[str, object]],
    decision_rows: list[dict[str, object]],
    reference_rows: list[dict[str, object]],
    difficulty_leaderboard_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Results Summary",
        "",
        f"Results directory: `{results_dir}`",
        "",
        "## Leaders By Deadline",
        "",
        "| Benchmark | Deadline | Highest observed policy | Highest observed utility | Runner-up | Margin |",
        "| --- | ---: | --- | ---: | --- | ---: |",
    ]
    for row in leaderboard_rows:
        lines.append(
            "| "
            f"{row['benchmark_id']} | "
            f"{row.get('deadline_label', format_deadline_label(row['deadline_s']))} | "
            f"{row['best_policy']} | "
            f"{float(row['best_mean_utility']):.6f} | "
            f"{row['runner_up_policy']} | "
            f"{float(row['margin']):.6f} |"
        )

    lines.extend(["", "## No-Time-Limit Reference", ""])
    if reference_rows:
        lines.extend(
            [
                "| Benchmark | Highest observed no-limit policy | No-limit utility | Runner-up | Margin |",
                "| --- | --- | ---: | --- | ---: |",
            ]
        )
        for row in reference_rows:
            lines.append(
                "| "
                f"{row['benchmark_id']} | "
                f"{row['best_policy']} | "
                f"{float(row['best_mean_utility']):.6f} | "
                f"{row['runner_up_policy']} | "
                f"{float(row['margin']):.6f} |"
            )
    else:
        lines.append("No no-time-limit reference summary was available.")

    lines.extend(["", "## Difficulty Leaderboard", ""])
    if difficulty_leaderboard_rows:
        lines.extend(
            [
                "| Benchmark | Difficulty | Deadline | Highest observed policy | Highest observed utility | Runner-up | Margin |",
                "| --- | --- | ---: | --- | ---: | --- | ---: |",
            ]
        )
        for row in difficulty_leaderboard_rows:
            lines.append(
                "| "
                f"{row['benchmark_id']} | "
                f"{row['difficulty']} | "
                f"{row.get('deadline_label', format_deadline_label(row['deadline_s']))} | "
                f"{row['best_policy']} | "
                f"{float(row['best_mean_utility']):.6f} | "
                f"{row['runner_up_policy']} | "
                f"{float(row['margin']):.6f} |"
            )
    else:
        lines.append("No difficulty metadata was available for subgroup reporting.")

    rejecting = [row for row in decision_rows if row["seq_decision"] == "reject_null"]
    close_calls = [
        row
        for row in decision_rows
        if row["seq_decision"] != "reject_null" and abs(float(row["mean_difference"])) <= 0.06
    ]

    lines.extend(
        [
            "",
            "## Sequential Decisions",
            "",
        ]
    )
    if rejecting:
        lines.extend(
            [
                "| Benchmark | Deadline | Comparison | Mean diff | Stop step |",
                "| --- | ---: | --- | ---: | ---: |",
            ]
        )
        for row in rejecting:
            lines.append(
                "| "
                f"{row['benchmark_id']} | "
                f"{row.get('deadline_label', format_deadline_label(row['deadline_s']))} | "
                f"{row['policy_a']} > {row['policy_b']} | "
                f"{float(row['mean_difference']):.6f} | "
                f"{int(row['seq_stop_step']) if row['seq_stop_step'] not in (None, '') else ''} |"
            )
    else:
        lines.append("No directed comparisons crossed the sequential rejection threshold.")

    lines.extend(["", "## Close Calls", ""])
    if close_calls:
        lines.extend(
            [
                "| Benchmark | Deadline | Comparison | Mean diff | Fixed reject |",
                "| --- | ---: | --- | ---: | --- |",
            ]
        )
        for row in close_calls:
            lines.append(
                "| "
                f"{row['benchmark_id']} | "
                f"{row.get('deadline_label', format_deadline_label(row['deadline_s']))} | "
                f"{row['policy_a']} vs {row['policy_b']} | "
                f"{float(row['mean_difference']):.6f} | "
                f"{row['fixed_reject']} |"
            )
    else:
        lines.append("No near-tie comparisons met the current close-call filter.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    args = parser.parse_args()
    summary = analyze_results(args.results_dir)
    print(
        "Wrote analysis to",
        summary["analysis_dir"],
        "with",
        summary["utility_row_count"],
        "utility rows and",
        summary["comparison_row_count"],
        "comparison rows",
    )


if __name__ == "__main__":
    main()
