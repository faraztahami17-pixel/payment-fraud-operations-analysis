-- 02_data_quality.sql — Run after ingest, before clean transform
USE FraudOps; GO
-- Row reconciliation
SELECT (SELECT COUNT_BIG(*) FROM dbo.stg_paysim_raw) AS staged,
       (SELECT COUNT_BIG(*) FROM dbo.quarantine_paysim) AS quarantined,
       (SELECT COUNT_BIG(*) FROM dbo.stg_paysim_raw)+(SELECT COUNT_BIG(*) FROM dbo.quarantine_paysim) AS total_accounted;
-- Uniqueness
SELECT COUNT_BIG(*) - COUNT(DISTINCT transaction_id) AS duplicate_transaction_id FROM dbo.stg_paysim_raw;
-- Binary labels
SELECT COUNT(*) AS invalid_isFraud FROM dbo.stg_paysim_raw WHERE isFraud NOT IN (0,1);
SELECT COUNT(*) AS invalid_isFlagged FROM dbo.stg_paysim_raw WHERE isFlaggedFraud NOT IN (0,1);
-- Type domain
SELECT type, COUNT_BIG(*) c FROM dbo.stg_paysim_raw GROUP BY type ORDER BY c DESC;
SELECT COUNT(*) AS unknown_types FROM dbo.stg_paysim_raw WHERE type NOT IN ('CASH_IN','CASH_OUT','DEBIT','PAYMENT','TRANSFER');
-- Amounts
SELECT COUNT(*) AS negative_amounts FROM dbo.stg_paysim_raw WHERE amount < 0;
SELECT COUNT(*) AS zero_amounts FROM dbo.stg_paysim_raw WHERE amount = 0;
SELECT COUNT(*) AS null_amounts FROM dbo.stg_paysim_raw WHERE amount IS NULL;
-- Missing IDs
SELECT COUNT(*) AS missing_origin FROM dbo.stg_paysim_raw WHERE nameOrig IS NULL;
SELECT COUNT(*) AS missing_dest FROM dbo.stg_paysim_raw WHERE nameDest IS NULL;
-- Repeated rows (report only)
SELECT type, amount, nameOrig, nameDest, step, COUNT(*) c FROM dbo.stg_paysim_raw
GROUP BY type, amount, nameOrig, nameDest, step HAVING COUNT(*)>1 ORDER BY c DESC;
