from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_ANSWER_TYPES = {
    "integer",
    "decimal",
    "string",
    "boolean",
    "categorical",
    "multiple_choice",
}

ALLOWED_EXTRACTION_STATUSES = {
    "ok",
    "failed",
    "ambiguous",
    "missing",
}

UPGRADE_METADATA_FIELDS = {
    "slice_id",
    "difficulty",
    "answer_type",
    "source_dataset",
    "source_split",
    "provenance_note",
}

UPGRADE_TRACE_FIELDS = {
    "model_id",
    "raw_output",
    "extracted_answer",
    "extraction_status",
    "token_count_prompt",
    "token_count_completion",
    "decode_config",
}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    line: int
    message: str


class TraceBankValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__(f"Trace-bank validation failed with {len(issues)} issue(s)")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _canonical_option(value: str) -> str:
    candidate = value.strip().upper()
    if candidate.startswith("(") and candidate.endswith(")") and len(candidate) == 3:
        candidate = candidate[1]
    if candidate.startswith("OPTION "):
        candidate = candidate[len("OPTION ") :].strip()
    return candidate


def _append_issue(issues: list[ValidationIssue], path: str, line: int, message: str) -> None:
    issues.append(ValidationIssue(path=path, line=line, message=message))


def _validate_trace(
    *,
    trace_name: str,
    trace: Any,
    path: str,
    line: int,
    issues: list[ValidationIssue],
    answer_type: str | None,
    mcq_options: set[str] | None,
    require_upgrade_fields: bool,
) -> None:
    if not isinstance(trace, dict):
        _append_issue(issues, path, line, f"trace `{trace_name}` must be an object")
        return

    if "answer" not in trace:
        _append_issue(issues, path, line, f"trace `{trace_name}` is missing `answer`")
    elif not isinstance(trace["answer"], str):
        _append_issue(issues, path, line, f"trace `{trace_name}` field `answer` must be a string")

    latency = trace.get("latency_s")
    if latency is None:
        _append_issue(issues, path, line, f"trace `{trace_name}` is missing `latency_s`")
    elif not _is_finite_number(latency) or float(latency) < 0:
        _append_issue(issues, path, line, f"trace `{trace_name}` field `latency_s` must be a non-negative finite number")

    confidence = trace.get("confidence")
    if confidence is None:
        _append_issue(issues, path, line, f"trace `{trace_name}` is missing `confidence`")
    elif not _is_finite_number(confidence) or not 0.0 <= float(confidence) <= 1.0:
        _append_issue(issues, path, line, f"trace `{trace_name}` field `confidence` must be between 0 and 1")

    if require_upgrade_fields:
        for field_name in sorted(UPGRADE_TRACE_FIELDS):
            if field_name not in trace:
                _append_issue(issues, path, line, f"trace `{trace_name}` is missing upgrade field `{field_name}`")

    extraction_status = trace.get("extraction_status")
    if extraction_status is not None and extraction_status not in ALLOWED_EXTRACTION_STATUSES:
        _append_issue(
            issues,
            path,
            line,
            f"trace `{trace_name}` field `extraction_status` must be one of {sorted(ALLOWED_EXTRACTION_STATUSES)}",
        )

    if extraction_status == "ok" and not _is_non_empty_string(trace.get("answer")):
        _append_issue(issues, path, line, f"trace `{trace_name}` has extraction_status `ok` but no canonical `answer`")

    for token_field in ("token_count_prompt", "token_count_completion"):
        if token_field in trace:
            token_value = trace[token_field]
            if not isinstance(token_value, int) or token_value < 0:
                _append_issue(issues, path, line, f"trace `{trace_name}` field `{token_field}` must be a non-negative integer")

    if "decode_config" in trace and not isinstance(trace["decode_config"], dict):
        _append_issue(issues, path, line, f"trace `{trace_name}` field `decode_config` must be an object")

    if answer_type == "multiple_choice" and mcq_options is not None and isinstance(trace.get("answer"), str):
        canonical = _canonical_option(trace["answer"])
        if canonical and canonical not in mcq_options:
            _append_issue(
                issues,
                path,
                line,
                f"trace `{trace_name}` has canonical answer `{trace['answer']}` outside allowed options {sorted(mcq_options)}",
            )


def validate_trace_bank(
    paths: list[str],
    *,
    require_upgrade_fields: bool = False,
) -> dict[str, int]:
    issues: list[ValidationIssue] = []
    seen_prompt_ids: set[str] = set()
    prompt_count = 0
    trace_count = 0

    for raw_path in paths:
        path = str(Path(raw_path))
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    _append_issue(issues, path, line_number, f"invalid JSON: {exc}")
                    continue

                if not isinstance(record, dict):
                    _append_issue(issues, path, line_number, "each JSONL line must be an object")
                    continue

                prompt_id = record.get("id")
                if not _is_non_empty_string(prompt_id):
                    _append_issue(issues, path, line_number, "field `id` must be a non-empty string")
                    prompt_id = None
                elif prompt_id in seen_prompt_ids:
                    _append_issue(issues, path, line_number, f"duplicate prompt id `{prompt_id}`")
                else:
                    seen_prompt_ids.add(prompt_id)

                if not _is_non_empty_string(record.get("prompt")):
                    _append_issue(issues, path, line_number, "field `prompt` must be a non-empty string")

                if not isinstance(record.get("answer"), str):
                    _append_issue(issues, path, line_number, "field `answer` must be a string")

                metadata = record.get("metadata", {})
                if not isinstance(metadata, dict):
                    _append_issue(issues, path, line_number, "field `metadata` must be an object when present")
                    metadata = {}

                if require_upgrade_fields:
                    for field_name in sorted(UPGRADE_METADATA_FIELDS):
                        if field_name not in metadata:
                            _append_issue(issues, path, line_number, f"metadata is missing upgrade field `{field_name}`")

                answer_type = metadata.get("answer_type")
                if answer_type is not None and answer_type not in ALLOWED_ANSWER_TYPES:
                    _append_issue(
                        issues,
                        path,
                        line_number,
                        f"metadata `answer_type` must be one of {sorted(ALLOWED_ANSWER_TYPES)}",
                    )
                    answer_type = None

                mcq_options: set[str] | None = None
                if answer_type == "multiple_choice":
                    options = metadata.get("options")
                    if not isinstance(options, list) or not options or not all(_is_non_empty_string(option) for option in options):
                        _append_issue(issues, path, line_number, "multiple_choice prompts must provide non-empty string `metadata.options`")
                    else:
                        mcq_options = {_canonical_option(option) for option in options}
                        gold_answer = record.get("answer", "")
                        if _canonical_option(gold_answer) not in mcq_options:
                            _append_issue(
                                issues,
                                path,
                                line_number,
                                f"gold answer `{gold_answer}` is outside allowed options {sorted(mcq_options)}",
                            )

                traces = record.get("traces")
                if not isinstance(traces, dict) or not traces:
                    _append_issue(issues, path, line_number, "field `traces` must be a non-empty object")
                    continue

                prompt_count += 1
                trace_count += len(traces)
                for trace_name, trace in traces.items():
                    _validate_trace(
                        trace_name=str(trace_name),
                        trace=trace,
                        path=path,
                        line=line_number,
                        issues=issues,
                        answer_type=answer_type,
                        mcq_options=mcq_options,
                        require_upgrade_fields=require_upgrade_fields,
                    )

    if issues:
        raise TraceBankValidationError(issues)

    return {
        "validated_files": len(paths),
        "prompt_count": prompt_count,
        "trace_count": trace_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--require-upgrade-fields", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        summary = validate_trace_bank(
            args.paths,
            require_upgrade_fields=args.require_upgrade_fields,
        )
    except TraceBankValidationError as exc:
        if args.json:
            payload = {
                "ok": False,
                "issues": [
                    {"path": issue.path, "line": issue.line, "message": issue.message}
                    for issue in exc.issues
                ],
            }
            print(json.dumps(payload, indent=2))
        else:
            for issue in exc.issues:
                print(f"{issue.path}:{issue.line}: {issue.message}")
        raise SystemExit(1) from exc

    if args.json:
        print(json.dumps({"ok": True, **summary}, indent=2))
    else:
        print(
            "Validated",
            summary["prompt_count"],
            "prompts and",
            summary["trace_count"],
            "traces across",
            summary["validated_files"],
            "file(s).",
        )


if __name__ == "__main__":
    main()
