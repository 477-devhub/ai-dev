"""Step 7 — one 4x4 contact sheet per queued candidate (16 evenly spaced frames, relative timestamps).

Frames come from the keyframe cache, restricted to the clip's actual [start, end). Sheets show only
candidate id + relative time: no source label, no suggestion, no model output (reduces anchoring).
"""
from __future__ import annotations

import json

import cv2
import numpy as np

from _common import REVIEW, WORK, assert_writable, read_csv, read_json

TILE_W, TILE_H, N = 480, 270, 16


def main() -> None:
    queue = read_csv(REVIEW / "human_review_queue.csv")
    clips = read_json(REVIEW / "clips" / "clip_manifest.json")["clips"]
    for q in queue:
        cid, sid = q["candidate_id"], q["source_video_id"]
        c = clips[cid]
        a, b = c["actual_start_sec"], c["actual_end_sec"]
        fr = [f for f in json.load(open(WORK / "frames" / sid / "frames.json"))["frames"] if a - 1e-3 <= f["t"] < b]
        idx = np.linspace(0, len(fr) - 1, min(N, len(fr))).astype(int)
        tiles = []
        for i in idx:
            im = cv2.resize(cv2.imread(str(WORK / "frames" / sid / fr[i]["file"])), (TILE_W, TILE_H))
            label = f"t={fr[i]['t'] - a:5.1f}s"
            cv2.rectangle(im, (0, 0), (118, 24), (0, 0, 0), -1)
            cv2.putText(im, label, (5, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(im)
        while len(tiles) < N:
            tiles.append(np.zeros((TILE_H, TILE_W, 3), np.uint8))
        grid = np.vstack([np.hstack(tiles[r * 4:(r + 1) * 4]) for r in range(4)])
        head = np.full((36, grid.shape[1], 3), 32, np.uint8)
        cv2.putText(head, f"{cid}   clip {b - a:.1f}s   (if the sheet is insufficient, watch review/clips/{cid}.mp4)",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        out = assert_writable(REVIEW / "contact_sheets" / f"{cid}.jpg")
        cv2.imwrite(str(out), np.vstack([head, grid]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("contact sheets:", len(queue))


if __name__ == "__main__":
    main()
