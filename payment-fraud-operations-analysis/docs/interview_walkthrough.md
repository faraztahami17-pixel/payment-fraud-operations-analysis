# Interview Walkthrough

## 60-second version

"Analyzed 636k synthetic mobile-money transactions as a fraud-ops triage
problem — which transactions should analysts review first. The existing
`isFlaggedFraud` flag catches almost nothing (0% recall in test), so I built
3 transparent rules — large-for-type at the dev 99.5th percentile, TRANSFER
over 200k, and end-of-hour recipient activity — with thresholds frozen on dev
before ever touching test. Combined they catch 32% of test fraud at 2%
precision, 52 reviews per hit. Full reproduction is `python run.py`."

## 3-minute version

1. **Business goal** — limited review capacity, so the deliverable is a
   prioritized queue, not a classifier. Every number is workload-aware:
   precision, recall, reviews-per-fraud, fraud-value recall, capacity
   scenarios 100/250/500 per simulated day.
2. **Data limits** — synthetic PaySim; `step` is a simulation hour, not a
   calendar date; amount is local units; fraud-labeled value is not realized
   loss; the 4 balance columns are excluded from all screening per the
   publisher warning (canceled fraud leaves balances frozen — using them
   would be leakage).
3. **Ingestion** — 250k-row chunks, `transaction_id` = row number, bad rows
   quarantined, reconciliation `read = staged + quarantined`.
4. **Rules** — R1/R2/R3 with weights 40/30/30, priority bands High 70+ /
   Medium 40–69 / Low 1–39. Deterministic queue order score → amount → id.
   R3 is end-of-hour monitoring, not instant pre-transaction screening.
5. **Evaluation honesty** — chronological split by whole steps (dev 1–446,
   val 447–594, test 595–744), never splitting a step; thresholds learned on
   dev, frozen before test; invariants TP+FP+FN+TN = total checked in tests.
6. **Power BI** — 3 pages (overview, control effectiveness, review queue),
   DAX in `powerbi/measures.dax`, `is_fraud` hidden from the ops queue page.
7. **Trade-offs** — tighten R1 or require 2-rule agreement to cut the ~2%
   alert rate; segment R3 recipients; monitor drift dev→test.

## Q&A cheat sheet

- *Why exclude balances?* Publisher documents canceled fraud txs — balances
  freeze, so they leak the label. Enforced by test + config.
- *Why is R3 end-of-hour?* Same-hour row order is not event time; the signal
  is only valid as a retrospective hourly rollup.
- *Reviews-per-fraud?* Alerts ÷ true positives — here ~52, i.e. an analyst
  reviews 52 alerts per fraud found. The capacity analysis shows the same
  recall under 100/250/500-per-day budgets because sample volume fits.
- *Why not Isolation Forest as primary?* Ran as an optional comparison
  (notebook 02) at the same 2,954 budget: recall 13% vs rules 32%. Kept
  rules as primary because ops needs explainable reasons.
