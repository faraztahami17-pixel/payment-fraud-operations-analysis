# Metric Dictionary
| Metric | Definition |
|---|---|
| Total transactions | COUNT rows |
| Total transaction value | SUM amount (local units) |
| Fraud-labeled transactions | COUNT isFraud=1 |
| Fraud rate | fraud / total |
| Fraud-labeled value | SUM amount where isFraud=1 (not realized loss) |
| Alert rate | alerts / total |
| Precision | TP / (TP+FP) |
| Recall | TP / (TP+FN) |
| FPR | FP / (FP+TN) |
| Missed fraud | FN |
| Reviews per detected fraud | alerts / TP |
| Fraud-value recall | fraud value alerted / total fraud value (multiple legs may be counted) |
Consistent terms: fraud-labeled value, flagged transaction value, screening priority (not fraud probability unless calibrated).
