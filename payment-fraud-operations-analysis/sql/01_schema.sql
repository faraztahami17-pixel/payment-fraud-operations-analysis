-- 01_schema.sql — Staging + clean model. Idempotent. Run after ingest.
IF DB_ID('FraudOps') IS NULL CREATE DATABASE FraudOps;
GO
USE FraudOps;
GO

-- Staging already created by ingest.py; ensure clean fact
IF OBJECT_ID('dbo.fact_transactions','U') IS NOT NULL DROP TABLE dbo.fact_transactions;
GO
CREATE TABLE dbo.fact_transactions(
    transaction_id BIGINT NOT NULL PRIMARY KEY,
    simulation_step INT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(20,2) NOT NULL,
    origin_account VARCHAR(30),
    destination_account VARCHAR(30),
    origin_balance_before DECIMAL(20,2),
    origin_balance_after DECIMAL(20,2),
    destination_balance_before DECIMAL(20,2),
    destination_balance_after DECIMAL(20,2),
    is_fraud BIT NOT NULL,
    existing_flag BIT NOT NULL,
    simulation_day INT NOT NULL,
    hour_in_simulated_day INT NOT NULL,
    amount_band VARCHAR(30) NOT NULL,
    destination_is_merchant BIT NOT NULL
);
GO
IF OBJECT_ID('dbo.transaction_rule_results','U') IS NOT NULL DROP TABLE dbo.transaction_rule_results;
GO
CREATE TABLE dbo.transaction_rule_results(
    transaction_id BIGINT NOT NULL PRIMARY KEY,
    rule_large_amount BIT NOT NULL,
    rule_transfer_threshold BIT NOT NULL,
    rule_destination_activity BIT NOT NULL,
    alert_flag BIT NOT NULL,
    priority_score INT NOT NULL,
    primary_reason VARCHAR(100),
    rule_version VARCHAR(30) NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES dbo.fact_transactions(transaction_id)
);
GO
-- Indexes for analysis
CREATE INDEX IX_fact_step_type ON dbo.fact_transactions(simulation_step, transaction_type);
CREATE INDEX IX_fact_amount ON dbo.fact_transactions(amount);
GO
