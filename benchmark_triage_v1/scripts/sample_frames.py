"""Step 2 — one decode pass per source video: keyframes (~1 fps on these sources) at 960 px width.

These frames are a working cache (_work/frames/<source_id>/) used for scene grouping, near-duplicate
hashing, CV discovery features and contact sheets. Keyframe timestamps are recorded exactly
(frames.json per source) so every derived timestamp is traceable.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _common import POOL, ROOT, WORK, assert_writable, read_json

FRAMES = WORK / "frames"


def sample(src: dict) -> None:
    out_dir = assert_writable(FRAMES / src["source_id"])
    done = out_dir / "frames.json"
    if done.exists():
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    video = ROOT / src["local_read_path"]
    # keyframes only (GOP ~1 s on AI Hub 171; 71953 clips are short and decoded fully at 1 fps)
    if src["dataset"] == "aihub_171_abnormal_cctv":
        vf, pre = "scale=960:-2,showinfo", ["-skip_frame", "nokey"]
    else:
        vf, pre = "fps=1,scale=960:-2,showinfo", []
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", *pre, "-i", str(video), "-vf", vf,
           "-vsync", "vfr", "-q:v", "3", str(out_dir / "f%05d.jpg")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(p.stderr[-2000:])
    ts = [float(line.split("pts_time:")[1].split()[0]) for line in p.stderr.splitlines() if "pts_time:" in line]
    files = sorted(out_dir.glob("f*.jpg"))
    assert len(files) == len(ts), (src["source_id"], len(files), len(ts))
    json.dump({"source_id": src["source_id"], "frames": [{"file": f.name, "t": round(t, 3)} for f, t in zip(files, ts)]},
              open(done, "w"), indent=1)


def main() -> None:
    srcs = read_json(POOL / "candidate_sources.json")["sources"]
    k, n = (map(int, sys.argv[1].split("/")) if len(sys.argv) > 1 else (0, 1))   # optional shard "k/n"
    for i, s in enumerate(srcs):
        if i % n != k:
            continue
        sample(s)
        print(f"[{i+1}/{len(srcs)}] {s['source_id']}", flush=True)


if __name__ == "__main__":
    main()
