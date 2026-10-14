"""
develop_thresholds.py — Learn screening thresholds on DEVELOPMENT partition only.
- Splits by whole simulation steps: earliest 60% dev, next 20% val, final 20% test
- Computes Rule1: 99.5th percentile of amount per transaction_type on dev
- Computes Rule3: recipient activity thresholds (p99.5 of per-dest-step counts/values) on dev
- Writes config/rules.json thresholds (frozen before test evaluation)
"""
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config import load_rules, save_rules
from src.db import sqlserver_engine as engine

def get_partitions(eng):
    with eng.connect() as c:
        mn=c.execute(text("SELECT MIN(step) FROM dbo.stg_paysim_raw")).scalar()
        mx=c.execute(text("SELECT MAX(step) FROM dbo.stg_paysim_raw")).scalar()
        total=mx-mn+1
        dev_end=mn+int(total*0.6)-1
        val_end=dev_end+int(total*0.2)
        return (mn,dev_end),(dev_end+1,val_end),(val_end+1,mx)

def main():
    eng=engine()
    (d0,d1),(v0,v1),(t0,t1)=get_partitions(eng)
    print(f"Partitions dev [{d0},{d1}] val [{v0},{v1}] test [{t0},{t1}]")
    # Rule1 thresholds per type on dev
    q=f"SELECT type, amount FROM dbo.stg_paysim_raw WHERE step BETWEEN {d0} AND {d1}"
    df=pd.read_sql(q, eng)
    pct=df.groupby("type")["amount"].quantile(0.995).to_dict()
    # Rule3: dest activity on dev
    q2=f"SELECT nameDest, step, COUNT(*) cnt, SUM(amount) tot FROM dbo.stg_paysim_raw WHERE step BETWEEN {d0} AND {d1} GROUP BY nameDest, step"
    df2=pd.read_sql(q2, eng)
    cnt_thr=float(df2["cnt"].quantile(0.995)) if not df2.empty else 0
    val_thr=float(df2["tot"].quantile(0.995)) if not df2.empty else 0
    cfg = load_rules()
    for k, v in pct.items():
        cfg["rule1_large_for_type"]["thresholds"][k] = float(v)
    cfg["rule3_destination_activity"]["thresholds"]["max_count_threshold"] = cnt_thr
    cfg["rule3_destination_activity"]["thresholds"]["max_value_threshold"] = val_thr
    cfg["evaluation_partitions"] = {"development": [d0, d1], "validation": [v0, v1], "test": [t0, t1]}
    save_rules(cfg)
    print("Wrote thresholds to config/rules.json")
    print(json.dumps(cfg, indent=2))

if __name__=="__main__":
    main()
