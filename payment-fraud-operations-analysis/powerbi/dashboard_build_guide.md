# Power BI Dashboard Build Guide — 3 Pages

Model: Import vw_FactMonitoring as FactMonitoring, vw_DailyMonitoring as DailyMonitoring, vw_ReviewQueue as ReviewQueue, plus Dim tables if desired. Relationship: FactMonitoring[simulation_day] -> DailyMonitoring[simulation_day] (1: many not needed; keep Fact as central). Do NOT fabricate calendar dates for step.

## Page 1 — Transaction & Fraud Overview
Cards: Total Transactions, Total Transaction Value, Fraud Transactions, Fraud Rate, Fraud-Labeled Value (use measures.dax)
Visuals: Bar - transaction count by type; Bar - fraud rate by type (show counts alongside rates); Line - tx volume by simulation_day; Bar - fraud-labeled value by amount_band; Line - fraud count & tx count over simulation_step
Slicers: simulation_day, transaction_type, amount_band, priority_band (evaluation_partition from config)

## Page 2 — Control Effectiveness
Cards: Alert count, Precision, Recall, False Positives, Missed Fraud (False Negatives)
Visuals: Table rule-performance comparison (existing_flag vs each rule vs combined); 2x2 confusion matrix (matrix visual with alert_flag rows, is_fraud columns); Bar - alert volume per simulated day; Scatter - precision vs recall by rule; Bar - fraud-value recall under capacity 100/250/500 (from rule_performance.csv)
Show evaluation partition clearly; test results must not be mixed with dev.

## Page 3 — Review Queue & Operational Anomalies
Table visual bound to ReviewQueue: Transaction ID, Simulation step, Type, Amount, Origin, Destination, Priority score, Priority band, Rule reasons, Suggested review action
- Sort by priority_score desc, amount desc, transaction_id asc (deterministic)
- Conditional formatting on priority_band
- Do NOT expose is_fraud in operational queue; keep retrospective eval on separate page with is_fraud visible for reporting
- Add drillthrough to transaction detail page

Formatting: Amount = decimal 2 places, no currency symbol (local units unspecified). Fraud Rate/Precision/Recall as % with 2 decimals. Leave undefined ratios blank.
Export screenshots to reports/screenshots/.
.pbix goes in powerbi/ after you build it — do not claim AI generated it.
