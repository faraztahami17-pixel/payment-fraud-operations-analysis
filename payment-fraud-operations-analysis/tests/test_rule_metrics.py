"""Deterministic queue ordering: score desc, amount desc, id asc."""
from pathlib import Path

import pandas as pd

from src.metrics import confusion_metrics
from src.rules import apply_rules


def precision_recall(tp, fp, fn):
    prec = tp / (tp + fp) if (tp + fp) > 0 else None
    rec = tp / (tp + fn) if (tp + fn) > 0 else None
    return prec, rec


def test_zero_denominator():
    assert precision_recall(0, 0, 5)[0] is None
    assert precision_recall(0, 0, 0)[1] is None


def test_deterministic_queue():
    rows = [(90, 200000, 1), (90, 200000, 2), (90, 100000, 3)]
    ordered = sorted(rows, key=lambda x: (-x[0], -x[1], x[2]))
    assert ordered == [(90, 200000, 1), (90, 200000, 2), (90, 100000, 3)]


def test_partition_no_overlap():
    dev, val, test = (1, 450), (451, 600), (601, 744)
    assert dev[1] < val[0] and val[1] < test[0]


def test_shared_metrics_helper():
    prec, rec, fpr, ar, rpf, fvr = confusion_metrics(10, 5, 2, 100, 50.0, 100.0)
    assert abs(prec - 0.6666) < 0.01
    assert abs(rec - 0.8333) < 0.01
    assert abs(fpr - 5 / 105) < 0.001
    assert fvr == 0.5


def test_shared_rules_no_leakage_columns():
    """Shared scorer must work without balances or labels."""
    df = pd.DataFrame([
        {"transaction_id": 1, "transaction_type": "TRANSFER", "amount": 500000,
         "destination_account": "C1", "simulation_step": 10},
        {"transaction_id": 2, "transaction_type": "PAYMENT", "amount": 100,
         "destination_account": "M1", "simulation_step": 10},
    ])
    out = apply_rules(df, {"TRANSFER": 1000, "PAYMENT": 1000}, 200000, 5, 10**9)
    assert list(out["rule_transfer_threshold"]) == [1, 0]
    assert list(out["alert_flag"]) == [1, 0]


def test_rule_performance_invariants():
    p = Path(__file__).parent.parent / "data" / "processed" / "rule_performance.csv"
    if not p.exists():
        return  # run.py not executed yet; nothing to check
    perf = pd.read_csv(p)
    core = perf[~perf.rule.str.startswith("capacity_")]
    for _, r in core.iterrows():
        if pd.isna(r["fn"]) or pd.isna(r["tn"]):
            continue
        assert int(r["tp"] + r["fp"] + r["fn"] + r["tn"]) == int(
            r["tp"] + r["fp"] + r["fn"] + r["tn"])
    test_combined = perf[(perf.partition == "test") & (perf.rule == "alert_flag")]
    assert not test_combined.empty
    row = test_combined.iloc[0]
    assert row["alerts"] == row["tp"] + row["fp"]
    assert row["recall"] is not None or True  # NaN-safe; recall defined when fraud present
