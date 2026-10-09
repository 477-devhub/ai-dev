"""Step 3 — generic CV discovery features per sampled frame (brief section 46/47).

Allowed use: diversify candidate mining (person count, motion, close pair, low posture, darkness).
NOT used: any P0 rule-engine output, P0-P4 prediction, cascade threshold or evaluator result.
The pretrained yolo26n-pose weights are read (not modified) from experiments/p0_cv_only/models.

Run with the P0 venv interpreter (has ultralytics + CUDA torch):
  ../../experiments/p0_cv_only/.venv/Scripts/python.exe cv_features.py
Writes _work/features/<source_id>.json
"""
from __future__ import annotations

import json

import cv2
import numpy as np

from _common import ROOT, WORK, POOL, assert_writable, read_json

WEIGHTS = ROOT / "experiments" / "p0_cv_only" / "models" / "yolo26n-pose.pt"
FRAMES = WORK / "frames"
FEATS = WORK / "features"
CONF = 0.25          # same generic detection floor as the shared cheap CV layer
IMGSZ = 960


def frame_people(res) -> list[dict]:
    out = []
    if res.boxes is None or len(res.boxes) == 0:
        return out
    xyxy = res.boxes.xyxy.cpu().numpy()
    conf = res.boxes.conf.cpu().numpy()
    kp = res.keypoints.data.cpu().numpy() if res.keypoints is not None else None
    for i, (b, c) in enumerate(zip(xyxy, conf)):
        x1, y1, x2, y2 = map(float, b)
        w, h = x2 - x1, y2 - y1
        item = {"box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)], "conf": round(float(c), 3),
                "aspect_hw": round(h / max(w, 1e-6), 3)}
        if kp is not None:
            k = kp[i]
            vis = k[:, 2] > 0.5
            # torso verticality: shoulders (5,6) vs hips (11,12); small |dy| relative to |dx| = horizontal torso
            if vis[[5, 6, 11, 12]].all():
                sh, hp = k[[5, 6], :2].mean(0), k[[11, 12], :2].mean(0)
                d = hp - sh
                item["torso_vertical"] = round(float(abs(d[1]) / (np.hypot(*d) + 1e-6)), 3)
        out.append(item)
    return out


def main() -> None:
    from ultralytics import YOLO
    model = YOLO(str(WEIGHTS))
    srcs = read_json(POOL / "candidate_sources.json")["sources"]
    for i, s in enumerate(srcs):
        out = assert_writable(FEATS / f"{s['source_id']}.json")
        fj = FRAMES / s["source_id"] / "frames.json"
        if out.exists() or not fj.exists():
            continue
        frames = json.load(open(fj))["frames"]
        rows, prev = [], None
        for f in frames:
            img = cv2.imread(str(FRAMES / s["source_id"] / f["file"]))
            g = cv2.cvtColor(cv2.resize(img, (160, 90)), cv2.COLOR_BGR2GRAY).astype(np.float32)
            motion = float(np.abs(g - prev).mean()) if prev is not None else 0.0
            prev = g
            res = model.predict(img, imgsz=IMGSZ, conf=CONF, verbose=False)[0]
            rows.append({"t": f["t"], "brightness": round(float(g.mean()), 1), "motion": round(motion, 2),
                         "people": frame_people(res)})
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump({"source_id": s["source_id"], "frame_width": 960, "detector": "yolo26n-pose (pretrained)",
                   "conf": CONF, "imgsz": IMGSZ, "frames": rows}, open(out, "w"))
        print(f"[{i+1}/{len(srcs)}] {s['source_id']} frames={len(rows)}", flush=True)


if __name__ == "__main__":
    main()
