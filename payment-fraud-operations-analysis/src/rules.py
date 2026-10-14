"""
rules.py — pure, testable screening logic.

No DB, no I/O. All thresholds come from config/rules.json frozen on dev.
Balances and is_fraud are never read here (leakage guard).
"""
from __future__ import annotations

import pandas as pd


def apply_rules(df: pd.DataFrame, r1_thresholds: dict, r2_amount: float, r3_cnt: float, r3_val: float) -> pd.DataFrame:
    """
    df must contain: transaction_id, transaction_type (or type), amount, destination_account (or nameDest), simulation_step (or step)
    Returns df with rule columns added. Normalizes column names internally.
    """
    # normalize names so both SQL Server (type/nameDest/step) and DuckDB (transaction_type/...) work
    col_type = "transaction_type" if "transaction_type" in df.columns else "type"
    col_dest = "destination_account" if "destination_account" in df.columns else "nameDest"
    col_step = "simulation_step" if "simulation_step" in df.columns else "step"

    out = df.copy()

    out["rule_large_amount"] = out.apply(
        lambda r: 1 if r["amount"] > r1_thresholds.get(r[col_type], float("inf")) else 0, axis=1
    )
    out["rule_transfer_threshold"] = ((out[col_type] == "TRANSFER") & (out["amount"] > r2_amount)).astype(int)

    grp = out.groupby([col_dest, col_step], as_index=False).agg(cnt=("transaction_id", "count"), tot=("amount", "sum"))
    grp["flag_activity"] = ((grp["cnt"] > r3_cnt) | (grp["tot"] > r3_val)).astype(int)
    out = out.merge(grp[[col_dest, col_step, "flag_activity"]], on=[col_dest, col_step], how="left")
    out["rule_destination_activity"] = out["flag_activity"].fillna(0).astype(int)

    out["alert_flag"] = (out["rule_large_amount"] | out["rule_transfer_threshold"] | out["rule_destination_activity"]).astype(int)
    out["priority_score"] = out["rule_large_amount"] * 40 + out["rule_transfer_threshold"] * 30 + out["rule_destination_activity"] * 30

    def reason(r):
        parts = []
        if r["rule_large_amount"]:
            parts.append("Unusually large for type")
        if r["rule_transfer_threshold"]:
            parts.append("Large transfer benchmark")
        if r["rule_destination_activity"]:
            parts.append("Elevated recipient activity (end-of-hour)")
        return "; ".join(parts) if parts else None

    out["primary_reason"] = out.apply(reason, axis=1)
    return out
