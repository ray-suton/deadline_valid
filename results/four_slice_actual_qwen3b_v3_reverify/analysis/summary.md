# Results Summary

Results directory: `results/four_slice_actual_qwen3b_v3_reverify`

## Leaders By Deadline

| Benchmark | Deadline | Highest observed policy | Highest observed utility | Runner-up | Margin |
| --- | ---: | --- | ---: | --- | ---: |
| knowledge_arc_actual_qwen3b_v2 | 0.1 | self_consistency_3 | 0.425000 | budget_branch | 0.008333 |
| knowledge_arc_actual_qwen3b_v2 | 0.15 | budget_branch | 0.441667 | greedy | 0.008334 |
| knowledge_arc_actual_qwen3b_v2 | 0.2 | budget_branch | 0.450000 | greedy | 0.008333 |
| language_cola_actual_qwen3b_v2 | 0.1 | greedy | 0.108333 | budget_branch | 0.008333 |
| language_cola_actual_qwen3b_v2 | 0.15 | self_consistency_3 | 0.241667 | greedy | 0.008334 |
| language_cola_actual_qwen3b_v2 | 0.2 | self_consistency_3 | 0.250000 | greedy | 0.016667 |
| math_gsm8k_actual_qwen3b_v2 | 0.1 | self_consistency_3 | 0.050000 | budget_branch | 0.016667 |
| math_gsm8k_actual_qwen3b_v2 | 0.15 | self_consistency_3 | 0.058333 | budget_branch | 0.008333 |
| math_gsm8k_actual_qwen3b_v2 | 0.2 | self_consistency_3 | 0.058333 | budget_branch | 0.008333 |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.1 | budget_branch | 0.283333 | greedy | 0.025000 |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.15 | budget_branch | 0.275000 | greedy | 0.016667 |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.2 | budget_branch | 0.275000 | greedy | 0.016667 |

## No-Time-Limit Reference

| Benchmark | Highest observed no-limit policy | No-limit utility | Runner-up | Margin |
| --- | --- | ---: | --- | ---: |
| knowledge_arc_actual_qwen3b_v2 | budget_branch | 0.875000 | greedy | 0.008333 |
| language_cola_actual_qwen3b_v2 | greedy | 0.500000 | self_consistency_3 | 0.008333 |
| math_gsm8k_actual_qwen3b_v2 | budget_branch | 0.108333 | self_consistency_3 | 0.008333 |
| reasoning_bbh_exact_actual_qwen3b_v2 | budget_branch | 0.508333 | greedy | 0.025000 |

## Difficulty Leaderboard

| Benchmark | Difficulty | Deadline | Highest observed policy | Highest observed utility | Runner-up | Margin |
| --- | --- | ---: | --- | ---: | --- | ---: |
| knowledge_arc_actual_qwen3b_v2 | medium | 0.1 | self_consistency_3 | 0.425000 | budget_branch | 0.008333 |
| knowledge_arc_actual_qwen3b_v2 | medium | 0.15 | budget_branch | 0.441667 | greedy | 0.008334 |
| knowledge_arc_actual_qwen3b_v2 | medium | 0.2 | budget_branch | 0.450000 | greedy | 0.008333 |
| language_cola_actual_qwen3b_v2 | medium | 0.1 | greedy | 0.108333 | budget_branch | 0.008333 |
| language_cola_actual_qwen3b_v2 | medium | 0.15 | self_consistency_3 | 0.241667 | greedy | 0.008334 |
| language_cola_actual_qwen3b_v2 | medium | 0.2 | self_consistency_3 | 0.250000 | greedy | 0.016667 |
| math_gsm8k_actual_qwen3b_v2 | medium | 0.1 | self_consistency_3 | 0.050000 | budget_branch | 0.016667 |
| math_gsm8k_actual_qwen3b_v2 | medium | 0.15 | self_consistency_3 | 0.058333 | budget_branch | 0.008333 |
| math_gsm8k_actual_qwen3b_v2 | medium | 0.2 | self_consistency_3 | 0.058333 | budget_branch | 0.008333 |
| reasoning_bbh_exact_actual_qwen3b_v2 | medium | 0.1 | budget_branch | 0.283333 | greedy | 0.025000 |
| reasoning_bbh_exact_actual_qwen3b_v2 | medium | 0.15 | budget_branch | 0.275000 | greedy | 0.016667 |
| reasoning_bbh_exact_actual_qwen3b_v2 | medium | 0.2 | budget_branch | 0.275000 | greedy | 0.016667 |

## Sequential Decisions

No directed comparisons crossed the sequential rejection threshold.

## Close Calls

| Benchmark | Deadline | Comparison | Mean diff | Fixed reject |
| --- | ---: | --- | ---: | --- |
| math_gsm8k_actual_qwen3b_v2 | 0.1 | greedy vs self_consistency_3 | -0.016667 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.1 | self_consistency_3 vs greedy | 0.016667 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.1 | self_consistency_3 vs budget_branch | 0.016667 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.1 | budget_branch vs self_consistency_3 | -0.016667 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.15 | greedy vs self_consistency_3 | -0.025000 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.15 | self_consistency_3 vs greedy | 0.025000 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.15 | self_consistency_3 vs budget_branch | 0.008333 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.15 | budget_branch vs self_consistency_3 | -0.008333 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.2 | greedy vs self_consistency_3 | -0.025000 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.2 | self_consistency_3 vs greedy | 0.025000 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.2 | self_consistency_3 vs budget_branch | 0.008333 | False |
| math_gsm8k_actual_qwen3b_v2 | 0.2 | budget_branch vs self_consistency_3 | -0.008333 | False |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.1 | greedy vs budget_branch | -0.025000 | False |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.1 | budget_branch vs greedy | 0.025000 | False |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.15 | greedy vs budget_branch | -0.016667 | False |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.15 | budget_branch vs greedy | 0.016667 | False |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.2 | greedy vs budget_branch | -0.016667 | False |
| reasoning_bbh_exact_actual_qwen3b_v2 | 0.2 | budget_branch vs greedy | 0.016667 | False |
| knowledge_arc_actual_qwen3b_v2 | 0.1 | self_consistency_3 vs budget_branch | 0.008333 | False |
| knowledge_arc_actual_qwen3b_v2 | 0.1 | budget_branch vs self_consistency_3 | -0.008333 | False |
| knowledge_arc_actual_qwen3b_v2 | 0.15 | self_consistency_3 vs budget_branch | -0.008334 | False |
| knowledge_arc_actual_qwen3b_v2 | 0.15 | budget_branch vs self_consistency_3 | 0.008334 | False |
| knowledge_arc_actual_qwen3b_v2 | 0.2 | self_consistency_3 vs budget_branch | -0.016667 | False |
| knowledge_arc_actual_qwen3b_v2 | 0.2 | budget_branch vs self_consistency_3 | 0.016667 | False |
| language_cola_actual_qwen3b_v2 | 0.1 | greedy vs self_consistency_3 | 0.008333 | False |
| language_cola_actual_qwen3b_v2 | 0.1 | self_consistency_3 vs greedy | -0.008333 | False |
| language_cola_actual_qwen3b_v2 | 0.15 | greedy vs self_consistency_3 | -0.008334 | False |
| language_cola_actual_qwen3b_v2 | 0.15 | self_consistency_3 vs greedy | 0.008334 | False |
| language_cola_actual_qwen3b_v2 | 0.2 | greedy vs self_consistency_3 | -0.016667 | False |
| language_cola_actual_qwen3b_v2 | 0.2 | self_consistency_3 vs greedy | 0.016667 | False |
