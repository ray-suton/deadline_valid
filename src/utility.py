from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceCandidate:
    answer: str
    latency_s: float
    confidence: float


@dataclass(frozen=True)
class PromptExample:
    prompt_id: str
    prompt: str
    answer: str
    traces: dict[str, TraceCandidate]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyOutcome:
    prompt_id: str
    policy_id: str
    deadline_s: float
    predicted_answer: str | None
    correct: bool
    finished: bool
    latency_s: float | None
    utility: int
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["deadline_s"] = round(self.deadline_s, 6)
        if self.latency_s is not None:
            payload["latency_s"] = round(self.latency_s, 6)
        return payload


def normalize_answer(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def is_correct(predicted_answer: str | None, target_answer: str) -> bool:
    return bool(predicted_answer) and normalize_answer(predicted_answer) == normalize_answer(
        target_answer
    )


def deadline_utility(correct: bool, finished: bool) -> int:
    return int(correct and finished)


def format_deadline_label(value: float) -> str:
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, payload: Any) -> None:
    parent = os.path.dirname(path)
    if parent:
        ensure_dir(parent)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def resolve_path(base_file: str, maybe_relative_path: str) -> str:
    if os.path.isabs(maybe_relative_path):
        return maybe_relative_path
    return os.path.normpath(os.path.join(os.path.dirname(base_file), maybe_relative_path))


def load_benchmark(path: str) -> list[PromptExample]:
    examples: list[PromptExample] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            raw = json.loads(line)
            traces = {
                name: TraceCandidate(
                    answer=trace["answer"],
                    latency_s=float(trace["latency_s"]),
                    confidence=float(trace["confidence"]),
                )
                for name, trace in raw["traces"].items()
            }
            examples.append(
                PromptExample(
                    prompt_id=raw["id"],
                    prompt=raw["prompt"],
                    answer=raw["answer"],
                    traces=traces,
                    metadata=raw.get("metadata", {}),
                )
            )
    return examples
