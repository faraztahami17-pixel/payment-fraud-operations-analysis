"""
apply_rules.py — Apply frozen screening rules to all rows, emit transaction_rule_results.
Uses config/rules.json (no is_fraud leakage, no balance columns).
Writes to dbo.transaction_rule_results via SQL for auditability, also CSV.
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config import load_rules
from src.db import sqlserver_engine as engine

def main():
    eng = engine()
    cfg = load_rules()
    r1 = cfg["rule1_large_for_type"]["thresholds"]
    r2_thr = cfg["rule2_large_transfer"]["amount_threshold"]
    r3c = cfg["rule3_destination_activity"]["thresholds"]["max_count_threshold"]
    r3v = cfg["rule3_destination_activity"]["thresholds"]["max_value_threshold"]
    version = cfg.get("version", "v0.1")

    # Load only columns needed for screening — no balances, no is_fraud.
    df = pd.read_sql("SELECT transaction_id, step, type, amount, nameDest FROM dbo.stg_paysim_raw", eng)

    from src.rules import apply_rules

    # Normalize column names for the shared helper
    df = df.rename(columns={"type": "transaction_type", "nameDest": "destination_account", "step": "simulation_step"})
    scored = apply_rules(df, r1, r2_thr, r3c, r3v)
    scored["rule_version"] = version
    out = scored[["transaction_id", "rule_large_amount", "rule_transfer_threshold",
                  "rule_destination_activity", "alert_flag", "priority_score", "primary_reason", "rule_version"]]
    # Write to SQL
    with eng.begin() as c:
        c.execute(text("IF OBJECT_ID('dbo.transaction_rule_results','U') IS NOT NULL DELETE FROM dbo.transaction_rule_results"))
    out.to_sql("transaction_rule_results", eng, if_exists="append", index=False, method="multi", chunksize=20000)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    out.to_parquet("data/processed/rule_results.parquet", index=False)
    print(f"Wrote {len(out)} rule results, alerts={out['alert_flag'].sum()}")

if __name__=="__main__":
    main()
