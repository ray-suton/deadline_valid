# Deadline-Valid Replay Reproducibility Package

This repository contains the reproducibility surface for the Accepted ICML Hypothesis Testing Workshop Paper:

**Deadline-Valid Replay: Anytime-Valid Testing for LLM Inference Policies**

The package is intentionally replay-based. It includes the frozen trace-bank
inputs, policy and testing code, generated analysis outputs, and a repeated
verification run. It does not include manuscript source, manuscript PDFs, or
camera-ready assets, and it does not require live model calls to reproduce the
reported replay analysis.

## Contents

- `configs/`: replay benchmark and policy configuration.
- `data/benchmarks/`: frozen Qwen2.5-3B trace-bank slices used in the replay.
- `src/`: policy replay, utility, fixed-horizon, and e-process code.
- `scripts/`: analysis, simulation, and trace validation scripts.
- `results/four_slice_actual_qwen3b_v3/`: main replay experiment outputs.
- `results/four_slice_actual_qwen3b_v3_reverify/`: repeated verification run.
- `results/power_sim_v1/`: prompt-budget and optional-stopping simulation outputs.
- `docs/`: experiment data schema documentation.
- `tests/`: focused unit and replay tests.
- `validation/`: trace-bank validation summary for the packaged frozen traces.

## Quick Verification

Run the focused test suite:

```bash
python -m unittest \
  tests.test_pipeline \
  tests.test_policies \
  tests.test_sequential_test \
  tests.test_simulation \
  tests.test_trace_bank_validator \
  tests.test_utility -v
```

Validate the packaged frozen trace bank:

```bash
python scripts/validate_trace_bank.py --require-upgrade-fields --json \
  data/benchmarks/math_gsm8k_actual_qwen3b_v2.jsonl \
  data/benchmarks/reasoning_bbh_exact_actual_qwen3b_v2.jsonl \
  data/benchmarks/knowledge_arc_actual_qwen3b_v2.jsonl \
  data/benchmarks/language_cola_actual_qwen3b_v2.jsonl
```

Expected validation summary:

```json
{
  "ok": true,
  "validated_files": 4,
  "prompt_count": 480,
  "trace_count": 2400
}
```

## Reproduce Replay Outputs

Run the deterministic replay experiment:

```bash
python -m src.run_eval \
  --benchmarks configs/benchmarks_four_slice_actual_qwen3b_v3.json \
  --policies configs/policies.json \
  --out results/four_slice_actual_qwen3b_v3_reproduced
```

Generate analysis summaries:

```bash
python scripts/analyze_results.py \
  --results-dir results/four_slice_actual_qwen3b_v3_reproduced
```

## Scope

Empirical claims are scoped to the included frozen Qwen2.5-3B trace bank, the
four task slices, and the evaluated deadline grid. This package supports
replaying and verifying the reported methodology-first case study. It is not a
manuscript archive, live-serving benchmark, or universal ranking of inference
policies.
