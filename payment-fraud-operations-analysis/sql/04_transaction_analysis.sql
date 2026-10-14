-- 04_transaction_analysis.sql — 8+ analytical queries (business questions 1-8)
USE FraudOps; GO
-- Overall KPIs
SELECT COUNT_BIG(*) AS total_transactions, SUM(amount) AS total_transaction_value,
  SUM(CAST(is_fraud AS BIGINT)) AS fraud_transactions,
  100.0*SUM(CAST(is_fraud AS BIGINT))/NULLIF(COUNT_BIG(*),0) AS fraud_rate_pct,
  SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END) AS fraud_labeled_value
FROM dbo.fact_transactions;
GO
-- Fraud by transaction type (show counts alongside rates)
SELECT transaction_type, COUNT_BIG(*) AS transaction_count, SUM(amount) AS transaction_value,
  SUM(CAST(is_fraud AS BIGINT)) AS fraud_count,
  100.0*SUM(CAST(is_fraud AS BIGINT))/NULLIF(COUNT_BIG(*),0) AS fraud_rate_pct,
  SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END) AS fraud_labeled_value
FROM dbo.fact_transactions GROUP BY transaction_type ORDER BY fraud_rate_pct DESC;
GO
-- Count & value by simulation day
SELECT simulation_day, COUNT_BIG(*) AS tx_count, SUM(amount) AS tx_value,
  SUM(CAST(is_fraud AS BIGINT)) AS fraud_count FROM dbo.fact_transactions GROUP BY simulation_day ORDER BY simulation_day;
GO
-- Fraud rate by amount band
SELECT amount_band, COUNT_BIG(*) AS tx_count, SUM(CAST(is_fraud AS BIGINT)) AS fraud_count,
  100.0*SUM(CAST(is_fraud AS BIGINT))/NULLIF(COUNT_BIG(*),0) AS fraud_rate_pct,
  SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END) AS fraud_labeled_value
FROM dbo.fact_transactions GROUP BY amount_band ORDER BY MIN(amount);
GO
-- Volume by simulation step
SELECT simulation_step, COUNT_BIG(*) AS tx_count, SUM(amount) AS tx_value FROM dbo.fact_transactions GROUP BY simulation_step ORDER BY simulation_step;
GO
-- Destination activity: top recipients by incoming count/value (hourly rollup done in rule dev)
SELECT TOP 50 destination_account, COUNT_BIG(*) AS incoming_count, SUM(amount) AS incoming_value,
  SUM(CAST(is_fraud AS BIGINT)) AS fraud_count FROM dbo.fact_transactions GROUP BY destination_account ORDER BY incoming_count DESC;
GO
-- High-value legitimate transactions
SELECT TOP 100 * FROM dbo.fact_transactions WHERE is_fraud=0 ORDER BY amount DESC;
GO
-- Fraud-labeled missed by baseline flag (for diagnostic review)
SELECT TOP 200 * FROM dbo.fact_transactions WHERE is_fraud=1 AND existing_flag=0 ORDER BY amount DESC;
GO
