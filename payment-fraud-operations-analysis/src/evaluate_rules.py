"""
evaluate_rules.py — Honest evaluation on validation vs test.
Computes confusion, precision/recall/FPR/alert-rate/reviews-per-fraud/fraud-value-recall per rule/partition.
Also capacity scenarios 100/250/500 per simulated day.
"""
from pathlib import Path

import pandas as pd

from src.config import load_rules
from src.db import sqlserver_engine as engine
from src.metrics import confusion_metrics as metrics

def evaluate_partition(eng,label,lo,hi):
    q=f"SELECT r.rule_large_amount,r.rule_transfer_threshold,r.rule_destination_activity,r.alert_flag,s.isFraud,s.amount FROM dbo.stg_paysim_raw s JOIN dbo.transaction_rule_results r ON r.transaction_id=s.transaction_id WHERE s.step BETWEEN {lo} AND {hi}"
    df=pd.read_sql(q, eng)
    if df.empty: return []
    fvtot=float(df.loc[df.isFraud==1,"amount"].sum())
    rows=[]
    def score(col):
        tp=int(((df[col]==1)&(df.isFraud==1)).sum()); fp=int(((df[col]==1)&(df.isFraud==0)).sum())
        fn=int(((df[col]==0)&(df.isFraud==1)).sum()); tn=int(((df[col]==0)&(df.isFraud==0)).sum())
        fvtp=float(df.loc[(df[col]==1)&(df.isFraud==1),"amount"].sum())
        prec,rec,fpr,ar,rpf,fvr=metrics(tp,fp,fn,tn,fvtp,fvtot)
        return dict(partition=label, rule=col, alerts=tp+fp, tp=tp, fp=fp, fn=fn, tn=tn, precision=prec, recall=rec, fpr=fpr, alert_rate=ar, reviews_per_fraud=rpf, fraud_value_recall=fvr)
    for c in ["rule_large_amount","rule_transfer_threshold","rule_destination_activity","alert_flag"]:
        rows.append(score(c))
    base=pd.read_sql(f"SELECT isFraud,isFlaggedFraud,amount FROM dbo.stg_paysim_raw WHERE step BETWEEN {lo} AND {hi}", eng)
    tp=int(((base.isFlaggedFraud==1)&(base.isFraud==1)).sum()); fp=int(((base.isFlaggedFraud==1)&(base.isFraud==0)).sum())
    fn=int(((base.isFlaggedFraud==0)&(base.isFraud==1)).sum()); tn=int(((base.isFlaggedFraud==0)&(base.isFraud==0)).sum())
    fvtp=float(base.loc[(base.isFlaggedFraud==1)&(base.isFraud==1),"amount"].sum())
    fv=float(base.loc[base.isFraud==1,"amount"].sum())
    prec,rec,fpr,ar,rpf,fvr=metrics(tp,fp,fn,tn,fvtp,fv)
    rows.append(dict(partition=label, rule="existing_flag", alerts=tp+fp, tp=tp, fp=fp, fn=fn, tn=tn, precision=prec, recall=rec, fpr=fpr, alert_rate=ar, reviews_per_fraud=rpf, fraud_value_recall=fvr))
    return rows

def capacity_eval(eng,lo,hi,budgets=[100,250,500]):
    q=f"SELECT r.priority_score,s.amount,s.isFraud,s.step FROM dbo.transaction_rule_results r JOIN dbo.stg_paysim_raw s ON s.transaction_id=r.transaction_id WHERE r.alert_flag=1 AND s.step BETWEEN {lo} AND {hi}"
    df=pd.read_sql(q, eng)
    out=[]
    for b in budgets:
        if df.empty:
            out.append(dict(budget=b,tp=0,fp=0,prec=None,rec=None)); continue
        df2=df.sort_values(["step","priority_score","amount"], ascending=[True,False,False])
        picked=df2.groupby("step").head(b)
        tp=int((picked.isFraud==1).sum()); fp=int((picked.isFraud==0).sum())
        total=pd.read_sql(f"SELECT COUNT(*) c FROM dbo.stg_paysim_raw WHERE isFraud=1 AND step BETWEEN {lo} AND {hi}", eng).iloc[0]["c"]
        prec=tp/(tp+fp) if (tp+fp)>0 else None
        rec=tp/total if total else None
        out.append(dict(budget=b,tp=tp,fp=fp,prec=prec,rec=rec))
    return out

def main():
    eng = engine()
    cfg = load_rules()
    parts = cfg["evaluation_partitions"]
    results=[]
    for name in ["development","validation","test"]:
        v=parts.get(name)
        if not isinstance(v, list): continue
        lo,hi=v[0],v[1]
        results.extend(evaluate_partition(eng,name,lo,hi))
        if name in ("validation","test"):
            for r in capacity_eval(eng,lo,hi):
                results.append(dict(partition=name, rule=f"capacity_{r['budget']}_per_day", alerts=r["tp"]+r["fp"], tp=r["tp"], fp=r["fp"], fn=None, tn=None, precision=r["prec"], recall=r["rec"], fpr=None, alert_rate=None, reviews_per_fraud=None, fraud_value_recall=None))
    df=pd.DataFrame(results); Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/processed/rule_performance.csv", index=False)
    print(df.to_string())
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/findings.md").write_text("# Findings (scaffold — replace with computed values)\n\nSee data/processed/rule_performance.csv. Invariants: TP+FP+FN+TN = evaluated count; TP+FN = fraud count.\n")

if __name__=="__main__":
    main()
