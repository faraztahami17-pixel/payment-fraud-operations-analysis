"""
ingest.py — Chunked ingestion PaySim CSV -> SQL Server staging.
Reads PS_20174392719_1491204439457_log.csv in chunks, creates
transaction_id = CSV row number, quarantines bad rows, logs counts.
See full spec in docs/. Usage: python src/ingest.py --csv data/raw/... --chunksize 250000
"""
import argparse
import json
import logging
import sys
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db import sqlserver_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

REQUIRED_COLS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig",
    "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud", "isFlaggedFraud",
]
ALLOWED_TYPES = {"CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"}


def ensure_staging(engine) -> None:
    ddl = """
    IF OBJECT_ID('dbo.stg_paysim_raw','U') IS NULL
    CREATE TABLE dbo.stg_paysim_raw(transaction_id BIGINT PRIMARY KEY, step INT NOT NULL, type VARCHAR(20) NOT NULL, amount DECIMAL(20,2) NOT NULL, nameOrig VARCHAR(30), nameDest VARCHAR(30), oldbalanceOrg DECIMAL(20,2), newbalanceOrig DECIMAL(20,2), oldbalanceDest DECIMAL(20,2), newbalanceDest DECIMAL(20,2), isFraud BIT NOT NULL, isFlaggedFraud BIT NOT NULL, load_batch UNIQUEIDENTIFIER NULL, source_row_number BIGINT NOT NULL);
    IF OBJECT_ID('dbo.quarantine_paysim','U') IS NULL CREATE TABLE dbo.quarantine_paysim(source_row_number BIGINT PRIMARY KEY, reason VARCHAR(200), raw_json NVARCHAR(MAX));
    IF OBJECT_ID('dbo.load_log','U') IS NULL CREATE TABLE dbo.load_log(batch_id UNIQUEIDENTIFIER PRIMARY KEY, started_at DATETIME2 DEFAULT SYSUTCDATETIME(), csv_path NVARCHAR(500), chunk_size INT, rows_read BIGINT, rows_staged BIGINT, rows_quarantined BIGINT);
    """
    with engine.begin() as c:
        for stmt in ddl.split(";"):
            s = stmt.strip()
            if s:
                c.execute(text(s))

def validate_chunk(chunk: pd.DataFrame):
    issues=[]
    missing=[c for c in REQUIRED_COLS if c not in chunk.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")
    chunk["amount"]=pd.to_numeric(chunk["amount"], errors="coerce")
    neg=(chunk["amount"]<0).sum()
    if neg: issues.append(f"{neg} negative amounts")
    zero=(chunk["amount"]==0).sum()
    if zero: issues.append(f"{zero} zero amounts (report, not auto-remove)")
    for col in ["isFraud","isFlaggedFraud"]:
        bad=~chunk[col].isin([0,1,0.0,1.0,"0","1"])
        if bad.any(): issues.append(f"{bad.sum()} invalid {col}")
    unknown=set(chunk["type"].dropna().unique())-ALLOWED_TYPES
    if unknown: issues.append(f"unknown types {unknown}")
    return issues

def ingest(csv_path: Path, chunksize: int, truncate: bool) -> int:
    engine = sqlserver_engine()
    ensure_staging(engine)
    batch_id = str(uuid.uuid4())
    if truncate:
        with engine.begin() as c:
            c.execute(text("DELETE FROM dbo.stg_paysim_raw"))
            c.execute(text("DELETE FROM dbo.quarantine_paysim"))
        log.info("Truncated staging + quarantine")
    total_read = total_staged = total_quarantined = 0
    row_offset = 0
    with engine.begin() as c:
        c.execute(
            text("INSERT INTO dbo.load_log(batch_id,csv_path,chunk_size,rows_read,rows_staged,rows_quarantined) VALUES (:b,:p,:cs,0,0,0)"),
            {"b": batch_id, "p": str(csv_path), "cs": chunksize},
        )
    for chunk in pd.read_csv(csv_path, chunksize=chunksize):
        chunk.insert(0, "transaction_id", range(row_offset + 1, row_offset + len(chunk) + 1))
        chunk["source_row_number"] = range(row_offset + 1, row_offset + len(chunk) + 1)
        row_offset += len(chunk)
        total_read += len(chunk)

        issues = validate_chunk(chunk)
        if issues:
            log.warning("Chunk %s: %s", row_offset, "; ".join(issues))

        mask = chunk["amount"].isna() | chunk["nameOrig"].isna() | chunk["nameDest"].isna()
        to_q, to_stage = chunk[mask], chunk[~mask].copy()

        if not to_q.empty:
            with engine.begin() as c:
                for _, r in to_q.iterrows():
                    c.execute(
                        text("INSERT INTO dbo.quarantine_paysim(source_row_number,reason,raw_json) VALUES (:n,:r,:j)"),
                        {"n": int(r["source_row_number"]), "r": "amount NaN or missing account ID", "j": r.to_json()},
                    )
            total_quarantined += len(to_q)

        if not to_stage.empty:
            cols = [
                "transaction_id", "step", "type", "amount", "nameOrig", "nameDest",
                "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest",
                "isFraud", "isFlaggedFraud", "source_row_number",
            ]
            to_stage = to_stage[cols]
            to_stage["isFraud"] = to_stage["isFraud"].astype(int)
            to_stage["isFlaggedFraud"] = to_stage["isFlaggedFraud"].astype(int)
            to_stage["load_batch"] = batch_id
            to_stage.to_sql("stg_paysim_raw", engine, if_exists="append", index=False, method="multi", chunksize=10000)
            total_staged += len(to_stage)

        log.info("Progress read=%s staged=%s quarantined=%s", total_read, total_staged, total_quarantined)

    with engine.begin() as c:
        c.execute(
            text("UPDATE dbo.load_log SET rows_read=:r,rows_staged=:s,rows_quarantined=:q WHERE batch_id=:b"),
            {"r": total_read, "s": total_staged, "q": total_quarantined, "b": batch_id},
        )
    log.info("Done. Reconciliation OK? %s", total_read == total_staged + total_quarantined)

    out = Path("data/processed/ingest_summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"csv": str(csv_path), "rows_read": int(total_read), "rows_staged": int(total_staged),
         "rows_quarantined": int(total_quarantined), "batch_id": batch_id}, indent=2,
    ))
    return total_read

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/raw/PS_20174392719_1491204439457_log.csv")
    ap.add_argument("--chunksize", type=int, default=250000)
    ap.add_argument("--truncate", action="store_true")
    args=ap.parse_args()
    p=Path(args.csv)
    if not p.exists():
        log.error(f"CSV not found: {p}. Download from https://www.kaggle.com/datasets/ealaxi/paysim1 and place in data/raw/")
        sys.exit(1)
    ingest(p, args.chunksize, args.truncate)
