"""Step 11-13 — select the final benchmark from HUMAN-labelled candidates, split by scene, write manifests.

Refuses to run unless validate_human_labels.py reports human_review_complete.
Selection uses only human labels, human confidence, scene identity and the fixed seed (477).
No model output is read.

Primary set   : HIGH-confidence CLEAR_NORMAL / HARD_NEGATIVE_NORMAL / ANCHORED_DANGER
Challenge set : MEDIUM-confidence labels of those classes (kept separate; never used for calibration)
Ambiguous set : AMBIGUOUS (kept separate)
LOW / EXCLUDE : dropped

Writes media/TRIAGE_XXX.mp4, public_manifest.json, private_ground_truth/triage_labels.json,
manifests/split_manifest.json, reports/proposed_selection.md.
"""
from __future__ import annotations

import itertools
import random
import shutil
import sys
import argparse
from collections import Counter, defaultdict

from _common import (BENCH, BENCHMARK_ID, MANIFESTS, MEDIA, PRIVATE, REPORTS, REVIEW, SEED, assert_writable, read_csv,
                     read_json, sha256, write_json)

PRIMARY = ["ANCHORED_DANGER", "HARD_NEGATIVE_NORMAL", "CLEAR_NORMAL"]
TARGET = {"CLEAR_NORMAL": 30, "HARD_NEGATIVE_NORMAL": 40, "ANCHORED_DANGER": 10 ** 6}
MAX_PER_SCENE = 3
CALIB_FRACTION = 0.40


def round_half_up(x: float) -> int:
    return int(x + 0.5)


def schedule64(frame_count: int, fps: float) -> list[dict]:
    n = 64
    idx = [round_half_up(j * (frame_count - 1) / (n - 1)) for j in range(n)]
    return [{"j": j, "frame_index": i, "t_sec": round(i / fps, 4)} for j, i in enumerate(idx)]


def select(rows: list[dict]) -> list[dict]:
    rnd = random.Random(SEED)
    pools = defaultdict(list)
    for r in rows:
        pools[r["review_label"]].append(r)
    for v in pools.values():
        rnd.shuffle(v)
    per_scene, chosen = Counter(), []
    progress = True
    while progress:
        progress = False
        for lab in PRIMARY:                                   # scarcest-first round robin
            if sum(c["review_label"] == lab for c in chosen) >= TARGET[lab]:
                continue
            cands = [r for r in pools[lab] if per_scene[r["scene_group_id"]] < MAX_PER_SCENE]
            if not cands:
                continue
            m = min(per_scene[r["scene_group_id"]] for r in cands)   # spread across scenes
            r = next(r for r in cands if per_scene[r["scene_group_id"]] == m)
            pools[lab].remove(r)
            chosen.append(r)
            per_scene[r["scene_group_id"]] += 1
            progress = True
    return chosen


def split(chosen: list[dict], related: set[str]) -> dict[str, str]:
    groups = sorted({r["split_group_id"] for r in chosen})
    cls = {g: Counter(r["review_label"] for r in chosen if r["split_group_id"] == g) for g in groups}
    total = Counter(r["review_label"] for r in chosen)
    best = None
    for bits in itertools.product([0, 1], repeat=len(groups)):        # 1 = calibration
        cal = Counter()
        for g, b in zip(groups, bits):
            if b:
                cal += cls[g]
        n_cal = sum(cal.values())
        if not (0 < n_cal < len(chosen)):
            continue
        missing = sum(1 for lab in PRIMARY if total[lab] and (cal[lab] == 0 or cal[lab] == total[lab]))
        dev = abs(n_cal / len(chosen) - CALIB_FRACTION) + sum(abs(cal[l] / total[l] - CALIB_FRACTION) for l in PRIMARY if total[l])
        related_in_test = sum(cls[g].total() for g, b in zip(groups, bits) if not b and g in related) / len(chosen)
        key = (missing, round(dev + 0.25 * related_in_test, 6), bits)
        if best is None or key < best[0]:
            best = (key, bits)
    return {g: ("calibration" if b else "test") for g, b in zip(groups, best[1])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority", action="store_true", help="use minimal human GT; ignore confidence")
    args = ap.parse_args()
    if args.priority:
        from _priority_gt import build_priority
        return build_priority()
    status = read_json(REVIEW / "review_status.json") if (REVIEW / "review_status.json").exists() else {}
    if status.get("scope") == "priority_minimal_v1":
        print("REFUSED: priority GT is active; use build_benchmark.py --priority to preserve its protocol")
        return 1
    if not status.get("human_review_complete"):
        print("REFUSED: human review is not complete (run validate_human_labels.py; see review/review_status.json)")
        return 1
    q = read_csv(REVIEW / "human_review_queue.csv")
    clips = read_json(REVIEW / "clips" / "clip_manifest.json")["clips"]
    scenes = read_json(MANIFESTS / "scene_manifest.json")["scene_groups"]
    related = {v["split_group_id"] for v in scenes.values() if v["related_to_reasoning_v1"] or v["split_group_related_to_reasoning_v1"]}

    primary = [r for r in q if r["review_label"] in PRIMARY and r["review_confidence"] == "HIGH"]
    challenge = [r for r in q if r["review_label"] in PRIMARY and r["review_confidence"] == "MEDIUM"]
    ambiguous = [r for r in q if r["review_label"] == "AMBIGUOUS"]
    chosen = select(primary)
    chosen.sort(key=lambda r: r["candidate_id"])
    split_of_group = split(chosen, related)

    rnd = random.Random(SEED)
    order = chosen[:]
    rnd.shuffle(order)                                               # public ids carry no class/scene order
    labels, public = [], []
    for k, r in enumerate(order, 1):
        tid = f"TRIAGE_{k:03d}"
        c = clips[r["candidate_id"]]
        dst = assert_writable(MEDIA / f"{tid.lower()}.mp4")
        MEDIA.mkdir(exist_ok=True)
        shutil.copyfile(BENCH / r["review_clip"], dst)
        h = sha256(dst)
        assert h == c["clip_sha256"], f"clip hash drift for {r['candidate_id']}"
        meta = c["clip_meta"]
        public.append({"item_id": tid, "task": "single", "cameras": [{"camera": "CAM_01", "media": f"media/{tid.lower()}.mp4",
                       "sha256": h, "duration_sec": meta["duration"], "fps": round(meta["fps"], 5), "frame_count": meta["frames"],
                       "width": meta["width"], "height": meta["height"],
                       "frame_schedule_uniform_total64_v1": schedule64(meta["frames"], meta["fps"])}]})
        lab = r["review_label"]
        labels.append({
            "candidate_id": tid, "review_candidate_id": r["candidate_id"], "split": split_of_group[r["split_group_id"]],
            "triage_label": lab, "human_verified_observation": r["observable_summary"],
            "danger_type": r["danger_type_if_any"] or None if lab == "ANCHORED_DANGER" else None,
            "hard_negative_type": [t for t in r["hard_negative_type_if_any"].split("|") if t] if lab == "HARD_NEGATIVE_NORMAL" else None,
            "normal_subtype": r["normal_subtype"] or None if lab == "CLEAR_NORMAL" else None,
            "review_confidence": r["review_confidence"], "reviewer": r["reviewer"], "reviewed_at": r["reviewed_at"],
            "must_surface_to_operator": lab == "ANCHORED_DANGER",
            "scene_group_id": r["scene_group_id"], "split_group_id": r["split_group_id"],
            "source_video_id": r["source_video_id"], "source_label": r["source_label"],
            "source_window_sec": [c["actual_start_sec"], c["actual_end_sec"]], "source_sha256": c["source_sha256"],
            "window_kind": r["window_kind"], "related_to_reasoning_benchmark": r["related_to_reasoning_benchmark"] in ("True", "true", True),
        })

    write_json(BENCH / "public_manifest.json", {
        "benchmark_version": BENCHMARK_ID, "frame_protocol": "uniform_total64_v1 (round-half-up(j*(frame_count-1)/63), j=0..63)",
        "model_input_policy": "pixels, generic camera id, neutral relative times only", "items": public})
    side = lambda rows, kind: [{"review_candidate_id": r["candidate_id"], "triage_label": r["review_label"], "set": kind,
                                "review_confidence": r["review_confidence"], "observable_summary": r["observable_summary"],
                                "ambiguous_reason": r.get("ambiguous_reason"),
                                "must_surface_to_operator": None if r["review_label"] == "AMBIGUOUS" else r["review_label"] == "ANCHORED_DANGER"}
                               for r in rows]
    write_json(PRIVATE / "triage_labels.json", {
        "benchmark_version": BENCHMARK_ID, "access": "evaluator only; never read by any model-execution path",
        "primary": labels, "challenge_medium_confidence": side(challenge, "challenge"), "ambiguous": side(ambiguous, "ambiguous")})
    write_json(MANIFESTS / "split_manifest.json", {
        "unit": "split_group_id (scene views + staged takes); a split group never spans both splits",
        "calibration_fraction_target": CALIB_FRACTION, "split_groups": split_of_group,
        "counts": {s: dict(Counter(l["triage_label"] for l in labels if l["split"] == s)) for s in ("calibration", "test")},
        "related_to_reasoning_v1_groups_in_test": sorted(g for g, s in split_of_group.items() if s == "test" and g in related),
        "finalized": False, "finalize_by": "human approval in review/approvals.json, then freeze_benchmark.py"})
    print("selected", Counter(l["triage_label"] for l in labels), "split", Counter(l["split"] for l in labels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
