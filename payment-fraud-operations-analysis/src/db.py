"""db.py — single place for database connections.

SQL Server is the primary target (spec). DuckDB is the portable fallback
for reviewers without SQL Server — same schema, same invariants.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def sqlserver_url() -> str:
    server = os.getenv("MSSQL_SERVER", r"localhost\SQLEXPRESS")
    db = os.getenv("MSSQL_DATABASE", "FraudOps")
    driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server").replace(" ", "+")
    trusted = os.getenv("MSSQL_TRUSTED_CONNECTION", "yes").lower() in ("yes", "true", "1")
    uid = os.getenv("MSSQL_UID")
    pwd = os.getenv("MSSQL_PWD")
    if trusted:
        return f"mssql+pyodbc://@{server}/{db}?driver={driver}&Trusted_Connection=yes&TrustServerCertificate=yes"
    if not uid or not pwd:
        raise RuntimeError("Set MSSQL_UID/MSSQL_PWD or enable Trusted_Connection")
    return f"mssql+pyodbc://{uid}:{pwd}@{server}/{db}?driver={driver}&TrustServerCertificate=yes"


def sqlserver_engine():
    from sqlalchemy import create_engine

    return create_engine(sqlserver_url(), fast_executemany=True)


def duckdb_path(repo_root: Path | None = None) -> Path:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "data" / "processed" / "fraudops.duckdb"


def duckdb_connect(repo_root: Path | None = None):
    import duckdb

    p = duckdb_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(p))
