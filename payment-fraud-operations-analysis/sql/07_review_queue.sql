-- 07_review_queue.sql — Prioritized review queue (deterministic ordering)
USE FraudOps; GO

-- Queue 1: Operational queue (NO is_fraud column) — what analysts see
SELECT TOP 500
  f.transaction_id, f.simulation_step, f.simulation_day, f.transaction_type, f.amount,
  f.origin_account, f.destination_account, r.priority_score,
  CASE WHEN r.priority_score>=70 THEN 'High' WHEN r.priority_score>=40 THEN 'Medium' WHEN r.priority_score>=1 THEN 'Low' ELSE 'No alert' END AS priority_band,
  r.primary_reason,
  CASE
    WHEN r.rule_large_amount=1 THEN 'Review unusually large transaction.'
    WHEN r.rule_destination_activity=1 THEN 'Inspect elevated recipient activity.'
    ELSE 'Verify transaction context before escalation.'
  END AS suggested_review_action
FROM dbo.fact_transactions f
JOIN dbo.transaction_rule_results r ON r.transaction_id=f.transaction_id
WHERE r.alert_flag=1
ORDER BY r.priority_score DESC, f.amount DESC, f.transaction_id ASC;
GO

-- Queue 2: Retrospective evaluation (for reporting only, is_fraud visible)
SELECT TOP 500
  f.transaction_id, f.simulation_step, f.transaction_type, f.amount, f.is_fraud, r.priority_score, r.primary_reason
FROM dbo.fact_transactions f
JOIN dbo.transaction_rule_results r ON r.transaction_id=f.transaction_id
WHERE r.alert_flag=1
ORDER BY r.priority_score DESC, f.amount DESC, f.transaction_id ASC;
GO

-- Capacity scenario: top N per simulated day (example 250/day) — retrospective daily prioritization
DECLARE @budget INT = 250;
WITH ranked AS (
  SELECT f.simulation_day, f.transaction_id, r.priority_score, f.amount, f.is_fraud,
    ROW_NUMBER() OVER (PARTITION BY f.simulation_day ORDER BY r.priority_score DESC, f.amount DESC, f.transaction_id ASC) AS rn
  FROM dbo.fact_transactions f JOIN dbo.transaction_rule_results r ON r.transaction_id=f.transaction_id
  WHERE r.alert_flag=1
)
SELECT simulation_day, COUNT(*) AS picked, SUM(CASE WHEN is_fraud=1 THEN 1 ELSE 0 END) AS fraud_found
FROM ranked WHERE rn <= @budget GROUP BY simulation_day ORDER BY simulation_day;
GO
