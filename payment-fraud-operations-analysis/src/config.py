"""config.py — load frozen rule thresholds and partitions."""
from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_rules(path: Path | None = None) -> dict:
    p = path or (repo_root() / "config" / "rules.json")
    return json.loads(p.read_text(encoding="utf-8"))


def save_rules(cfg: dict, path: Path | None = None) -> None:
    p = path or (repo_root() / "config" / "rules.json")
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
