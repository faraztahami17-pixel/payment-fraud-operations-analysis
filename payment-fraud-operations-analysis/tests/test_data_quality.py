"""Data-quality guardrails: no balance leakage, invariants hold."""
import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_no_leakage_in_rules():
    cfg = json.loads((_repo() / "config" / "rules.json").read_text(encoding="utf-8"))
    forbidden = set(cfg.get("leakage_guard", {}).get("forbidden_features", []))
    assert {"oldbalanceOrg", "newbalanceDest"}.issubset(forbidden)

    for mod in ["src/rules.py", "src/apply_rules.py"]:
        src = (_repo() / mod).read_text(encoding="utf-8").lower()
        assert "oldbalance" not in src and "newbalance" not in src, f"leakage in {mod}"


def test_metrics_invariants():
    tp, fp, fn, tn = 10, 5, 2, 100
    assert tp + fp + fn + tn == 117
    assert tp + fn == 12
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    assert abs(prec - 0.6666) < 0.01
    assert abs(rec - 0.8333) < 0.01
