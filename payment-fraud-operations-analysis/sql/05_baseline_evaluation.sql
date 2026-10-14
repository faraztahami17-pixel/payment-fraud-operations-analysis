-- 05_baseline_evaluation.sql — Evaluate existing_flag (isFlaggedFraud)
USE FraudOps; GO
SELECT
  SUM(CASE WHEN existing_flag=1 AND is_fraud=1 THEN 1 ELSE 0 END) AS true_positive,
  SUM(CASE WHEN existing_flag=1 AND is_fraud=0 THEN 1 ELSE 0 END) AS false_positive,
  SUM(CASE WHEN existing_flag=0 AND is_fraud=1 THEN 1 ELSE 0 END) AS false_negative,
  SUM(CASE WHEN existing_flag=0 AND is_fraud=0 THEN 1 ELSE 0 END) AS true_negative
FROM dbo.fact_transactions;
GO
-- Invariant: TP+FP+FN+TN = total
SELECT SUM(CASE WHEN existing_flag=1 AND is_fraud=1 THEN 1 ELSE 0 END)
     + SUM(CASE WHEN existing_flag=1 AND is_fraud=0 THEN 1 ELSE 0 END)
     + SUM(CASE WHEN existing_flag=0 AND is_fraud=1 THEN 1 ELSE 0 END)
     + SUM(CASE WHEN existing_flag=0 AND is_fraud=0 THEN 1 ELSE 0 END) AS total_check,
     COUNT_BIG(*) AS fact_count FROM dbo.fact_transactions;
GO
-- Baseline by type
SELECT transaction_type,
  SUM(CASE WHEN existing_flag=1 AND is_fraud=1 THEN 1 ELSE 0 END) AS tp,
  SUM(CASE WHEN existing_flag=1 AND is_fraud=0 THEN 1 ELSE 0 END) AS fp,
  SUM(CASE WHEN existing_flag=0 AND is_fraud=1 THEN 1 ELSE 0 END) AS fn
FROM dbo.fact_transactions GROUP BY transaction_type ORDER BY tp DESC;
GO
-- Derived metrics (handle zero denominators)
WITH m AS (
  SELECT
    SUM(CASE WHEN existing_flag=1 AND is_fraud=1 THEN 1.0 ELSE 0 END) AS tp,
    SUM(CASE WHEN existing_flag=1 AND is_fraud=0 THEN 1.0 ELSE 0 END) AS fp,
    SUM(CASE WHEN existing_flag=0 AND is_fraud=1 THEN 1.0 ELSE 0 END) AS fn,
    SUM(CASE WHEN existing_flag=0 AND is_fraud=0 THEN 1.0 ELSE 0 END) AS tn
  FROM dbo.fact_transactions
)
SELECT tp,fp,fn,tn,
  CASE WHEN tp+fp>0 THEN tp/(tp+fp) END AS precision,
  CASE WHEN tp+fn>0 THEN tp/(tp+fn) END AS recall,
  CASE WHEN fp+tn>0 THEN fp/(fp+tn) END AS false_positive_rate,
  CASE WHEN tp+fp>0 THEN (tp+fp)/NULLIF(tp,0) END AS reviews_per_detected_fraud
FROM m;
GO
