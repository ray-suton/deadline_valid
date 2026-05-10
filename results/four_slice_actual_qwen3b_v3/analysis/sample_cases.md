# Sample Cases

## 1. math_gsm8k_actual_qwen3b_v2 / gsm8k_0007

Prompt:

`Max plans to watch two movies this weekend. The first movie is 1 hour and 30 minutes long while the second movie is 2 hours and 5 minutes long. How many minutes will it take Max to watch the two movies? Output only the final numeric answer.`

Gold answer:

`215`

Displayed deadline: `0.1`

| Policy | Deadline output | Utility | Finished | Latency | No-limit output | No-limit utility | Notes |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| budget_branch | 245 | 0 | True | 0.077731 | 245 | 0 | fallback_skipped |
| greedy | 245 | 0 | True | 0.077731 | 245 | 0 |  |
| selective_abstain | <none> | 0 | True | 0.077731 | <none> | 0 | abstain |
| self_consistency_3 | 215 | 1 | True | 0.094803 | 155 | 0 | vote_count=1 |

## 2. math_gsm8k_actual_qwen3b_v2 / gsm8k_0043

Prompt:

`Diane gave a number train a starting value of 20. This starting value plus half the number was divided by 5 and the resulting value was multiplied by the starting value minus 12. What was the final value of the number train? Output only the final numeric answer.`

Gold answer:

`48`

Displayed deadline: `0.1`

| Policy | Deadline output | Utility | Finished | Latency | No-limit output | No-limit utility | Notes |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| budget_branch | 48 | 1 | True | 0.061459 | 48 | 1 | fallback_skipped |
| greedy | 48 | 1 | True | 0.061459 | 48 | 1 |  |
| selective_abstain | <none> | 0 | True | 0.061459 | <none> | 0 | abstain |
| self_consistency_3 | 64 | 0 | True | 0.063107 | 64 | 0 | vote_count=1 |

## 3. reasoning_bbh_exact_actual_qwen3b_v2 / object_counting_0000

Prompt:

`I have a flute, a piano, a trombone, four stoves, a violin, an accordion, a clarinet, a drum, two lamps, and a trumpet. How many musical instruments do I have?`

Gold answer:

`8`

Displayed deadline: `0.1`

| Policy | Deadline output | Utility | Finished | Latency | No-limit output | No-limit utility | Notes |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| budget_branch | 8 | 1 | True | 0.092419 | 8 | 1 | fallback_used |
| greedy | 6 | 0 | True | 0.043936 | 6 | 0 |  |
| selective_abstain | <none> | 0 | True | 0.043936 | <none> | 0 | abstain |
| self_consistency_3 | 6 | 0 | True | 0.096404 | 6 | 0 | vote_count=2 |

## 4. reasoning_bbh_exact_actual_qwen3b_v2 / object_counting_0008

Prompt:

`I have a yam, a cauliflower, a garlic, two lettuce heads, a head of broccoli, a potato, a stalk of celery, and an onion. How many vegetables do I have?`

Gold answer:

`9`

Displayed deadline: `0.1`

| Policy | Deadline output | Utility | Finished | Latency | No-limit output | No-limit utility | Notes |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| budget_branch | 9 | 1 | True | 0.077869 | 9 | 1 | fallback_used |
| greedy | 8 | 0 | True | 0.038742 | 8 | 0 |  |
| selective_abstain | <none> | 0 | True | 0.038742 | <none> | 0 | abstain |
| self_consistency_3 | 8 | 0 | True | 0.079122 | 9 | 1 | vote_count=2 |

## 5. reasoning_bbh_exact_actual_qwen3b_v2 / object_counting_0016

Prompt:

`I have a microwave, a table, a fridge, a stove, an oven, a toaster, a couch, and four cars. How many objects do I have?`

Gold answer:

`11`

Displayed deadline: `0.1`

| Policy | Deadline output | Utility | Finished | Latency | No-limit output | No-limit utility | Notes |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| budget_branch | 11 | 1 | True | 0.056618 | 12 | 0 | fallback_skipped |
| greedy | 11 | 1 | True | 0.056618 | 11 | 1 |  |
| selective_abstain | <none> | 0 | True | 0.056618 | <none> | 0 | abstain |
| self_consistency_3 | 10 | 0 | True | 0.057422 | 12 | 0 | vote_count=1 |

