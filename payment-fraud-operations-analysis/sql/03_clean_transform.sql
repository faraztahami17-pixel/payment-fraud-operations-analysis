-- 03_clean_transform.sql — Staging -> fact_transactions (no deduplication without investigation)
USE FraudOps; GO
-- Amount bands (configurable; local currency units unspecified)
-- Keep balances only for retrospective diagnostics, never for screening features.

TRUNCATE TABLE dbo.fact_transactions;
INSERT INTO dbo.fact_transactions(
  transaction_id, simulation_step, transaction_type, amount,
  origin_account, destination_account,
  origin_balance_before, origin_balance_after, destination_balance_before, destination_balance_after,
  is_fraud, existing_flag, simulation_day, hour_in_simulated_day, amount_band, destination_is_merchant
)
SELECT
  s.transaction_id,
  s.step AS simulation_step,
  s.type AS transaction_type,
  s.amount,
  s.nameOrig AS origin_account,
  s.nameDest AS destination_account,
  s.oldbalanceOrg AS origin_balance_before,
  s.newbalanceOrig AS origin_balance_after,
  s.oldbalanceDest AS destination_balance_before,
  s.newbalanceDest AS destination_balance_after,
  CAST(s.isFraud AS BIT) AS is_fraud,
  CAST(s.isFlaggedFraud AS BIT) AS existing_flag,
  FLOOR((s.step - 1)/24)+1 AS simulation_day,
  (s.step - 1) % 24 AS hour_in_simulated_day,
  CASE
    WHEN s.amount < 10000 THEN '0-10k'
    WHEN s.amount < 50000 THEN '10k-50k'
    WHEN s.amount < 100000 THEN '50k-100k'
    WHEN s.amount < 200000 THEN '100k-200k'
    WHEN s.amount < 500000 THEN '200k-500k'
    ELSE '500k+'
  END AS amount_band,
  CASE WHEN s.nameDest LIKE 'M%' THEN 1 ELSE 0 END AS destination_is_merchant
FROM dbo.stg_paysim_raw s;
GO
SELECT COUNT_BIG(*) AS fact_rows, COUNT(DISTINCT transaction_id) AS distinct_ids FROM dbo.fact_transactions;
GO
