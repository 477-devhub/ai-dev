"""Step 6 — cut each queued candidate window from its source WITHOUT re-encoding.

The cut starts on the keyframe at/just before the requested start (keyframe pts are known exactly
from _work/frames/<src>/frames.json), and the video stream is copied bit-for-bit (-c:v copy, audio
dropped). Actual start/end, source SHA-256 and clip SHA-256 are recorded.

Writes review/clips/CAND_XXXX.mp4 and review/clips/clip_manifest.json.
"""
from __future__ import annotations

import json
import subprocess

from _common import (POOL, REVIEW, ROOT, WINDOW_SEC, WORK, assert_writable, ffprobe, read_csv, read_json, sha256,
                     write_json)

CLIPS = REVIEW / "clips"


def keyframe_at_or_before(src_id: str, t: float) -> float:
    fr = json.load(open(WORK / "frames" / src_id / "frames.json"))["frames"]
    ks = [f["t"] for f in fr if f["t"] <= t + 1e-3]
    return ks[-1] if ks else 0.0


def main() -> None:
    srcs = {s["source_id"]: s for s in read_json(POOL / "candidate_sources.json")["sources"]}
    queue = read_csv(REVIEW / "human_review_queue.csv")
    man_path = CLIPS / "clip_manifest.json"
    manifest = read_json(man_path) if man_path.exists() else {"clips": {}, "source_sha256": {}}
    for i, q in enumerate(queue):
        cid, sid = q["candidate_id"], q["source_video_id"]
        out = assert_writable(CLIPS / f"{cid}.mp4")
        if cid in manifest["clips"] and out.exists():
            continue
        s = srcs[sid]
        src_path = ROOT / s["local_read_path"]
        if sid not in manifest["source_sha256"]:
            manifest["source_sha256"][sid] = sha256(src_path)
        req_start, req_end = float(q["start_sec"]), float(q["end_sec"])
        is_mv = s["dataset"] != "aihub_171_abnormal_cctv"
        start = 0.0 if is_mv else keyframe_at_or_before(sid, req_start)
        dur = (s["video"]["duration"] if is_mv else (req_end - start))
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{start:.3f}", "-i", str(src_path),
               "-t", f"{dur:.3f}", "-map", "0:v:0", "-c:v", "copy", "-an", "-map_metadata", "-1",
               "-avoid_negative_ts", "make_zero", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        meta = ffprobe(out)
        manifest["clips"][cid] = {
            "candidate_id": cid, "source_video_id": sid, "source_path": s["original_path"],
            "source_sha256": manifest["source_sha256"][sid],
            "requested_window_sec": [req_start, req_end], "actual_start_sec": round(start, 3),
            "actual_end_sec": round(start + meta["duration"], 3),
            "start_shift_to_keyframe_sec": round(req_start - start, 3),
            "clip_sha256": sha256(out), "clip_meta": meta,
            "method": "stream copy (-c:v copy) from keyframe; no re-encode; audio removed; metadata stripped",
            "window_exception": (f"source clip shorter than {WINDOW_SEC:.0f}s; whole clip used" if is_mv and meta["duration"] < WINDOW_SEC - 0.5 else None),
        }
        write_json(man_path, manifest)
        print(f"[{i+1}/{len(queue)}] {cid} {sid} {start:.2f}+{meta['duration']:.2f}s frames={meta['frames']}", flush=True)


if __name__ == "__main__":
    main()
