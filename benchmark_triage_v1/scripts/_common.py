"""Shared helpers for 477-triage-normal-v1 construction.

Rules enforced here:
- Source roots (benchmark_v1, experiments/*, data/, downloads/) are only ever opened for reading.
- Every write goes under benchmark_triage_v1/.
- No model (P0-P4) prediction, threshold or evaluator output is read by any script.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # D:/projects/477
BENCH = Path(__file__).resolve().parents[1]           # D:/projects/477/benchmark_triage_v1
POOL = BENCH / "candidate_pool"
REVIEW = BENCH / "review"
MANIFESTS = BENCH / "manifests"
REPORTS = BENCH / "reports"
PRIVATE = BENCH / "private_ground_truth"
MEDIA = BENCH / "media"
WORK = BENCH / "_work"                                  # source cache / review clips; not part of the frozen benchmark

SEED = 477
WINDOW_SEC = 35.0
EVENT_BUFFER_SEC = 5.0          # brief section 18: exclude event_start-5 .. event_end+5
REVIEW_GUARD_SEC = 10.0         # extra margin used when ranking pre-event windows (annotation times are not trusted)

BENCHMARK_ID = "477-triage-normal-v1"

READ_ONLY_ROOTS = [ROOT / p for p in ["benchmark_v1", "experiments", "data", "downloads", "evaluation_selection",
                                      "organized_data", "human_grading"]]


def assert_writable(path: Path) -> Path:
    path = Path(path).resolve()
    if BENCH.resolve() not in path.parents and path != BENCH.resolve():
        raise PermissionError(f"refusing to write outside benchmark_triage_v1: {path}")
    return path


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj) -> Path:
    path = assert_writable(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> Path:
    path = assert_writable(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for r in rows:
            fields += [k for k in r if k not in fields]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def ffprobe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                          "-show_entries", "stream=width,height,r_frame_rate,nb_read_packets,codec_name:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    d = json.loads(out.stdout)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"], "fps": float(num) / float(den), "codec": s["codec_name"],
            "frames": int(s.get("nb_read_packets", 0)), "duration": float(d["format"]["duration"])}


def ffprobe_fast(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height,r_frame_rate,codec_name:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    d = json.loads(out.stdout)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"], "fps": float(num) / float(den), "codec": s["codec_name"],
            "duration": float(d["format"]["duration"])}
