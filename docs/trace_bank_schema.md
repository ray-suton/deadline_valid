# Trace-Bank Schema

## Purpose

The trace bank is the frozen experimental substrate for the replay study.

It is not just a dataset of prompts. It is the full replayable record needed to compare policies under deadlines:

- the prompt and gold answer
- prompt metadata such as slice and difficulty
- one or more pre-collected model traces
- per-trace latency, confidence, and decoding metadata
- enough raw information to audit answer extraction

## Why We Need A Schema

Without a schema, the project can quietly mix incompatible traces, missing fields, duplicate prompt ids, and ambiguous answer formats. That would make the replay less trustworthy and could turn the experiment into an extraction-noise benchmark instead of a policy benchmark.

The schema is the contract. The validator enforces the contract before the main run.

## Current Compatibility Constraint

The current evaluator in `src/utility.py` and `src/policies.py` expects each trace to expose:

- one canonical answer string
- one latency
- one confidence

So the upgraded schema keeps the current `trace.answer` field as the canonical extracted answer used by the evaluator, even when richer fields such as `raw_output` and `extracted_answer` are added.

## Record Shape

Each JSONL line represents one prompt.

Required now:

- `id`
- `prompt`
- `answer`
- `traces`

Recommended upgraded shape:

```json
{
  "id": "gsm8k_0001",
  "prompt": "A train travels ... What is the final distance?",
  "answer": "72",
  "metadata": {
    "slice_id": "math_word_problems",
    "difficulty": "medium",
    "answer_type": "integer",
    "source_dataset": "gsm8k",
    "source_split": "train_subset_v1",
    "provenance_note": "curated frozen subset for replay study"
  },
  "traces": {
    "greedy": {
      "answer": "72",
      "raw_output": "The final answer is 72.",
      "extracted_answer": "72",
      "extraction_status": "ok",
      "latency_s": 0.91,
      "confidence": 0.77,
      "model_id": "gpt-4.1-2025-04-14",
      "token_count_prompt": 138,
      "token_count_completion": 41,
      "decode_config": {
        "temperature": 0.0,
        "max_output_tokens": 256
      }
    },
    "sample_1": {
      "answer": "71",
      "raw_output": "I think the answer is 71.",
      "extracted_answer": "71",
      "extraction_status": "ok",
      "latency_s": 1.14,
      "confidence": 0.61,
      "model_id": "gpt-4.1-2025-04-14",
      "token_count_prompt": 138,
      "token_count_completion": 58,
      "decode_config": {
        "temperature": 0.8,
        "max_output_tokens": 256
      }
    }
  }
}
```

## Prompt-Level Fields

### Required

- `id`: unique prompt identifier across the validated bundle
- `prompt`: the exact prompt text given to the model
- `answer`: the gold canonical answer string
- `traces`: map from trace name to trace payload

### Upgraded Metadata

- `slice_id`: benchmark slice name such as `math_word_problems`
- `difficulty`: coarse bucket such as `easy`, `medium`, `hard`
- `answer_type`: one of `integer`, `decimal`, `string`, `boolean`, `categorical`, `multiple_choice`
- `source_dataset`: original dataset family
- `source_split`: exact subset or curation split
- `provenance_note`: short note on origin or filtering

## Trace-Level Fields

### Required Now

- `answer`: canonical extracted answer used by the current evaluator
- `latency_s`: end-to-end latency for that trace
- `confidence`: confidence-like score already used by the current policies

### Upgraded Fields

- `raw_output`: full raw model text before extraction
- `extracted_answer`: raw extracted span before final normalization
- `extraction_status`: `ok`, `failed`, `ambiguous`, or `missing`
- `model_id`: exact snapshot or versioned model name
- `token_count_prompt`: prompt token count
- `token_count_completion`: completion token count
- `decode_config`: decoding settings such as temperature and max output tokens

## What The Validator Does

The validator in `scripts/validate_trace_bank.py` checks:

- valid JSONL structure
- required prompt and trace fields
- unique prompt ids
- non-negative finite latencies
- confidence values in `[0, 1]`
- optional upgraded fields when `--require-upgrade-fields` is used
- multiple-choice answer consistency when `answer_type` is `multiple_choice`

## Why MCQ Is Optional Until Extraction Is Robust

Multiple-choice tasks look simple because the gold answer is only `A`, `B`, `C`, or `D`. In practice, model outputs are often verbose:

- `I think the best answer is B because ...`
- `Final answer: (C)`
- `B, though A is tempting`

The current evaluator only sees the final canonical `trace.answer`. If extraction is not robust, the project can end up measuring parser brittleness instead of policy quality.

For the first workshop submission, MCQ should stay optional unless:

- the extractor maps common response forms reliably to one option label
- ambiguous outputs are marked explicitly
- the validator enforces canonical option outputs in the frozen trace bank

## Practical Rule

For the fastest path to a credible submission:

- prefer exact-answer math and exact-answer reasoning first
- include MCQ only after option extraction is tested and stable
