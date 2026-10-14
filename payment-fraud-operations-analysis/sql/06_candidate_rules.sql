-- 06_candidate_rules.sql — Candidate rule logic (Python is authoritative; SQL shown for audit)
-- Thresholds below are EXAMPLE placeholders; real values come from config/rules.json after develop_thresholds.py.
-- Rule1: amount > dev 99.5th percentile per type
-- Rule2: TRANSFER and amount > 200000
-- Rule3: end-of-hour dest activity (count/value > dev p99.5 per dest-step)
USE FraudOps; GO

-- Inspect thresholds learned on dev (example values, replace after Python run)
-- SELECT * FROM OPENROWSET(BULK 'config/rules.json', SINGLE_CLOB) ... -- or load via Python

-- Example SQL application (replace thresholds):
/*
WITH thresholds AS (
  SELECT 'CASH_IN' AS transaction_type, 150000.00 AS thr UNION ALL
  SELECT 'CASH_OUT', 180000 UNION ALL SELECT 'DEBIT', 80000 UNION ALL SELECT 'PAYMENT', 90000 UNION ALL SELECT 'TRANSFER', 120000
),
dest_activity AS (
  SELECT destination_account, simulation_step, COUNT(*) AS cnt, SUM(amount) AS tot
  FROM dbo.fact_transactions WHERE simulation_step BETWEEN @dev_lo AND @dev_hi
  GROUP BY destination_account, simulation_step
),
dest_thr AS (SELECT 15 AS cnt_thr, 500000 AS val_thr),
scored AS (
  SELECT f.transaction_id,
    CASE WHEN f.amount > t.thr THEN 1 ELSE 0 END AS rule_large_amount,
    CASE WHEN f.transaction_type='TRANSFER' AND f.amount>200000 THEN 1 ELSE 0 END AS rule_transfer_threshold,
    CASE WHEN da.cnt > (SELECT cnt_thr FROM dest_thr) OR da.tot > (SELECT val_thr FROM dest_thr) THEN 1 ELSE 0 END AS rule_destination_activity
  FROM dbo.fact_transactions f
  LEFT JOIN thresholds t ON t.transaction_type=f.transaction_type
  LEFT JOIN dest_activity da ON da.destination_account=f.destination_account AND da.simulation_step=f.simulation_step
)
SELECT transaction_id,
  rule_large_amount, rule_transfer_threshold, rule_destination_activity,
  CASE WHEN rule_large_amount=1 OR rule_transfer_threshold=1 OR rule_destination_activity=1 THEN 1 ELSE 0 END AS alert_flag,
  rule_large_amount*40 + rule_transfer_threshold*30 + rule_destination_activity*30 AS priority_score
FROM scored;
*/

-- After Python apply_rules.py, verify one-to-one join:
SELECT COUNT(*) AS fact_cnt FROM dbo.fact_transactions;
SELECT COUNT(*) AS rule_cnt FROM dbo.transaction_rule_results;
SELECT COUNT(*) AS orphan_fact FROM dbo.fact_transactions f LEFT JOIN dbo.transaction_rule_results r ON r.transaction_id=f.transaction_id WHERE r.transaction_id IS NULL;
SELECT COUNT(*) AS orphan_rule FROM dbo.transaction_rule_results r LEFT JOIN dbo.fact_transactions f ON f.transaction_id=r.transaction_id WHERE f.transaction_id IS NULL;

-- Rule coverage
SELECT rule_large_amount, rule_transfer_threshold, rule_destination_activity, COUNT(*) AS cnt
FROM dbo.transaction_rule_results GROUP BY rule_large_amount, rule_transfer_threshold, rule_destination_activity ORDER BY cnt DESC;
