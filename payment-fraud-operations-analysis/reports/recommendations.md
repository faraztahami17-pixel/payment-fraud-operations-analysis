# Recommendations

| Finding | Recommendation | Check |
|---|---|---|
| Baseline misses 99%+ | Pilot combined R2+R1+R3 | Recall test vs baseline |
| Alert rate near 2%, many FPs | Tighten R1 or require 2-rule agreement | Precision and alerts/day |
| R3 flags busy legit recipients | Segment recipients | FPR by segment |
| Stable dev to test | Monitor drift | Precision/recall by day |

No prevented-loss claim; no auto-block. Scores are triage priorities, not fraud probabilities.
