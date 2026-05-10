# Power Simulation Summary

- Trials per grid point: 1000
- Tie rate: 0.35
- Alpha: 0.05
- Target power: 0.80

## Grid Results

| Win prob | Expected mean diff | Prompts | Sequential power | Fixed power | Median seq stop |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.55 | 0.065 | 40 | 0.065 | 0.105 | 17.00 |
| 0.55 | 0.065 | 80 | 0.097 | 0.156 | 26.00 |
| 0.55 | 0.065 | 120 | 0.104 | 0.188 | 36.50 |
| 0.55 | 0.065 | 160 | 0.118 | 0.253 | 52.00 |
| 0.60 | 0.130 | 40 | 0.122 | 0.216 | 21.00 |
| 0.60 | 0.130 | 80 | 0.223 | 0.387 | 34.00 |
| 0.60 | 0.130 | 120 | 0.275 | 0.517 | 49.00 |
| 0.60 | 0.130 | 160 | 0.332 | 0.596 | 63.00 |
| 0.65 | 0.195 | 40 | 0.242 | 0.371 | 20.50 |
| 0.65 | 0.195 | 80 | 0.415 | 0.653 | 37.00 |
| 0.65 | 0.195 | 120 | 0.604 | 0.828 | 54.00 |
| 0.65 | 0.195 | 160 | 0.688 | 0.915 | 62.00 |
| 0.70 | 0.260 | 40 | 0.397 | 0.583 | 20.00 |
| 0.70 | 0.260 | 80 | 0.676 | 0.879 | 34.50 |
| 0.70 | 0.260 | 120 | 0.876 | 0.972 | 47.00 |
| 0.70 | 0.260 | 160 | 0.941 | 0.998 | 52.00 |

## Prompt Budget Recommendations

- Win prob 0.55 (expected mean diff 0.065): no prompt budget in the current grid reached target power.
- Win prob 0.60 (expected mean diff 0.130): no prompt budget in the current grid reached target power.
- Win prob 0.65 (expected mean diff 0.195): no prompt budget in the current grid reached target power.
- Win prob 0.70 (expected mean diff 0.260): 120 prompts reaches target sequential power.
