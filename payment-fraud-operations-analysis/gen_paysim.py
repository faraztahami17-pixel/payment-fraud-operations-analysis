"""PaySim-faithful synthetic CSV for local runs (no Kaggle download needed).

Default 636,262 rows = 10% of the 6.36M spec. Fraud ~0.13%, only in
TRANSFER / CASH_OUT. See docs/data_dictionary.md for limitations.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
TYPE_PROBS = [0.22, 0.22, 0.06, 0.28, 0.22]

CHUNK = 250_000


def generate(rows: int, out: Path, seed: int = 42) -> Path:
    rng = np.random.default_rng(seed)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_fraud = max(10, int(rows * 0.00129))
    fraud_types = rng.choice(["TRANSFER", "CASH_OUT"], size=n_fraud, p=[0.55, 0.45])
    fraud_idx = set(rng.choice(rows, size=n_fraud, replace=False))

    all_types = rng.choice(TYPES, size=rows, p=TYPE_PROBS)
    for idx, ft in zip(fraud_idx, fraud_types):
        all_types[idx] = ft
    if out.exists():
        out.unlink()

    for start in range(0, rows, CHUNK):
        end = min(start + CHUNK, rows)
        n = end - start
        ct = all_types[start:end]
        steps = rng.integers(1, 745, size=n)

        amounts = np.empty(n)
        for t in TYPES:
            m = (ct == t).sum()
            if m == 0:
                continue
            if t in ("TRANSFER", "CASH_OUT"):
                base = rng.lognormal(10.5, 1.2, size=m)
            elif t == "PAYMENT":
                base = rng.lognormal(8.5, 0.9, size=m)
            elif t == "CASH_IN":
                base = rng.lognormal(9.5, 1.0, size=m)
            else:
                base = rng.lognormal(8.0, 0.8, size=m)
            amounts[ct == t] = np.clip(base, 1, 1_500_000)
        for i, g in enumerate(range(start, end)):
            if g in fraud_idx:
                amounts[i] = float(np.clip(rng.lognormal(12.2, 0.7), 50000, 10_000_000))

        name_orig = [f"C{rng.integers(1_000_000_000, 9_999_999_999)}" for _ in range(n)]
        name_dest, ob_o, nb_o, ob_d, nb_d, is_fr, is_fl = [], [], [], [], [], [], []
        for i in range(n):
            t = ct[i]
            is_mer = (t in ("PAYMENT", "DEBIT") and rng.random() < 0.7) or rng.random() < 0.05
            dest = f"M{rng.integers(1_000_000_000, 9_999_999_999)}" if is_mer else f"C{rng.integers(1_000_000_000, 9_999_999_999)}"
            name_dest.append(dest)
            amt = amounts[i]
            ob_org = float(rng.integers(0, 2_000_000)) if rng.random() > 0.1 else 0.0
            fraud = 1 if (start + i) in fraud_idx else 0
            is_fr.append(fraud)
            if fraud == 1:
                # canceled fraud: balances frozen (publisher warning — never use for screening)
                nb_org = ob_org
                ob_dest = 0.0 if is_mer else float(rng.integers(0, 2_000_000))
                nb_dest = ob_dest
            else:
                nb_org = max(0, ob_org - amt) if t in ("TRANSFER", "CASH_OUT", "PAYMENT") else ob_org + amt * 0.95
                ob_dest = 0.0 if is_mer else float(rng.integers(0, 2_000_000))
                nb_dest = ob_dest + amt if not is_mer else 0.0
            ob_o.append(round(ob_org, 2))
            nb_o.append(round(nb_org, 2))
            ob_d.append(round(ob_dest, 2))
            nb_d.append(round(nb_dest, 2))
            flagged = 1 if (t == "TRANSFER" and amt > 200000 and (
                (fraud == 1 and rng.random() < 0.015) or rng.random() < 0.00002)) else 0
            is_fl.append(flagged)

        pd.DataFrame({
            "step": steps, "type": ct, "amount": np.round(amounts, 2),
            "nameOrig": name_orig, "oldbalanceOrg": ob_o, "newbalanceOrig": nb_o,
            "nameDest": name_dest, "oldbalanceDest": ob_d, "newbalanceDest": nb_d,
            "isFraud": is_fr, "isFlaggedFraud": is_fl,
        }).to_csv(out, mode="w" if start == 0 else "a", header=(start == 0), index=False)
        print(f"chunk {start}-{end} written")

    flagged_total = pd.read_csv(out, usecols=["isFlaggedFraud"])["isFlaggedFraud"].sum()
    print(f"Done {out} fraud={n_fraud} flagged={flagged_total}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=636262)
    ap.add_argument("--out", default="data/raw/PS_20174392719_1491204439457_log.csv")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    generate(a.rows, Path(a.out), a.seed)
