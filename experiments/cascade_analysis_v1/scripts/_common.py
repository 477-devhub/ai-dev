"""Shared read-only helpers for cascade_analysis_v1.

Every input is opened read-only and recorded with its SHA-256 so that
build_report.py can confirm no frozen artifact changed during the analysis.
All writes go under cascade_analysis_v1/ only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # D:/projects/477
HERE = Path(__file__).resolve().parents[1]          # .../cascade_analysis_v1
ANALYSIS = HERE / "analysis"
FIGURES = HERE / "figures"
CONFIG_PATH = HERE / "configs" / "cascade_analysis_v1.json"

_READ_LOG: dict[str, str] = {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _abs(rel: str | Path) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else ROOT / p


def read_json(rel: str | Path):
    p = _abs(rel)
    _READ_LOG[str(p.relative_to(ROOT)).replace("\\", "/")] = sha256(p)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def read_csv(rel: str | Path) -> list[dict]:
    p = _abs(rel)
    _READ_LOG[str(p.relative_to(ROOT)).replace("\\", "/")] = sha256(p)
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_log() -> dict[str, str]:
    return dict(sorted(_READ_LOG.items()))


def config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def write_json(name: str, obj) -> Path:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    p = ANALYSIS / name
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return p


def write_csv(name: str, rows: list[dict], fields: list[str] | None = None) -> Path:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    p = ANALYSIS / name
    fields = fields or list(rows[0].keys())
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


def load_analysis_csv(name: str) -> list[dict]:
    with open(ANALYSIS / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def per_assessment(summary: dict) -> dict[str, dict]:
    """Flatten a run_summary decision_summary into {camera_or_'_': decision}."""
    if "per_camera" in summary:
        return dict(summary["per_camera"])
    return {"_": summary}
