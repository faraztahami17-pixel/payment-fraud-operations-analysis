-- 08_powerbi_views.sql — Lightweight views for Power BI import
USE FraudOps; GO

IF OBJECT_ID('dbo.vw_FactMonitoring','V') IS NOT NULL DROP VIEW dbo.vw_FactMonitoring;
GO
CREATE VIEW dbo.vw_FactMonitoring AS
SELECT
  f.transaction_id, f.simulation_step, f.simulation_day, f.hour_in_simulated_day,
  f.transaction_type, f.amount, f.amount_band, f.destination_is_merchant,
  f.origin_account, f.destination_account,
  f.is_fraud, f.existing_flag,
  r.rule_large_amount, r.rule_transfer_threshold, r.rule_destination_activity,
  r.alert_flag, r.priority_score, r.primary_reason, r.rule_version,
  CASE WHEN r.priority_score>=70 THEN 'High' WHEN r.priority_score>=40 THEN 'Medium' WHEN r.priority_score>=1 THEN 'Low' ELSE 'None' END AS priority_band
FROM dbo.fact_transactions f
LEFT JOIN dbo.transaction_rule_results r ON r.transaction_id=f.transaction_id;
GO

IF OBJECT_ID('dbo.vw_DailyMonitoring','V') IS NOT NULL DROP VIEW dbo.vw_DailyMonitoring;
GO
CREATE VIEW dbo.vw_DailyMonitoring AS
SELECT simulation_day,
  COUNT_BIG(*) AS tx_count, SUM(amount) AS tx_value,
  SUM(CAST(is_fraud AS BIGINT)) AS fraud_count,
  SUM(CASE WHEN existing_flag=1 THEN 1 ELSE 0 END) AS existing_alerts
FROM dbo.fact_transactions GROUP BY simulation_day;
GO

-- RulePerformance view materialized via Python evaluate; also compute on-the-fly for Power BI
IF OBJECT_ID('dbo.vw_RulePerformance','V') IS NOT NULL DROP VIEW dbo.vw_RulePerformance;
GO
CREATE VIEW dbo.vw_RulePerformance AS
SELECT 'all' AS evaluation_partition, alert_flag, is_fraud, COUNT_BIG(*) AS cnt
FROM dbo.vw_FactMonitoring GROUP BY alert_flag, is_fraud;
GO

IF OBJECT_ID('dbo.vw_ReviewQueue','V') IS NOT NULL DROP VIEW dbo.vw_ReviewQueue;
GO
CREATE VIEW dbo.vw_ReviewQueue AS
SELECT transaction_id, simulation_step, transaction_type, amount, origin_account, destination_account, priority_score, priority_band, primary_reason
FROM dbo.vw_FactMonitoring WHERE alert_flag=1;
GO
