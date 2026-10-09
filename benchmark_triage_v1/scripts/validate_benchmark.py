"""Step 14 — validate 477-triage-normal-v1 (brief section 51).

Runs in two modes automatically:
  - before build: validates the candidate pool / review pack only (reports NOT_BUILT for benchmark checks)
  - after build : full benchmark checks; after freeze also checks BENCHMARK_LOCK hashes.
Writes reports/validation.json. Exit 0 only if every applicable check passes.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from _common import BENCH, MANIFESTS, PRIVATE, REVIEW, read_csv, read_json, sha256, write_json

PRIVATE_KEYS = {"triage_label", "danger_type", "hard_negative_type", "human_verified_observation", "review_confidence",
                "source_label", "must_surface_to_operator", "normal_subtype", "source_video_id", "scene_group_id",
                "split", "review_candidate_id", "review_label", "reference_binary", "reviewer", "reviewed_at",
                "observable_summary", "ambiguous_reason", "related_to_reasoning_benchmark"}


def main() -> int:
    gt_path = PRIVATE / "triage_labels.json"
    if gt_path.exists() and read_json(gt_path).get("human_gt_policy") == "priority_minimal_v1":
        from _priority_gt import validate_built
        result = validate_built()
        for name, check in result["checks"].items():
            if name == "benchmark_lock_hashes_valid" and check["detail"].startswith("NOT_FROZEN"):
                print("INFO benchmark_lock_hashes_valid: NOT_FROZEN; technical readiness is checked separately")
                continue
            print(("PASS " if check["pass"] else "FAIL ") + name,
                  "" if check["pass"] else check["detail"])
        return 0 if result["ready_to_freeze"] else 1
    checks: dict[str, dict] = {}

    def chk(name, ok, detail=""):
        checks[name] = {"pass": bool(ok), "detail": detail}

    # ---------------- review pack ----------------
    q = read_csv(REVIEW / "human_review_queue.csv")
    clips = read_json(REVIEW / "clips" / "clip_manifest.json")["clips"]
    ids = [r["candidate_id"] for r in q]
    chk("review_unique_candidate_ids", len(ids) == len(set(ids)))
    missing = [c for c in ids if not (BENCH / "review" / "clips" / f"{c}.mp4").exists() or not (BENCH / "review" / "contact_sheets" / f"{c}.jpg").exists()]
    chk("review_media_and_sheets_exist", not missing, missing[:10])
    bad = [c for c in ids if c in clips and sha256(BENCH / "review" / "clips" / f"{c}.mp4") != clips[c]["clip_sha256"]]
    chk("review_clip_sha256", not bad, bad)
    hashes = Counter(v["clip_sha256"] for v in clips.values())
    chk("review_no_duplicate_exact_media", all(n == 1 for n in hashes.values()))
    src = {s["source_id"]: s for s in read_json(MANIFESTS / "source_manifest.json")["sources"]}
    v1 = [r["candidate_id"] for r in q if src[r["source_video_id"]]["used_in_reasoning_v1"]]
    chk("review_no_reasoning_v1_source_video", not v1, v1)
    per_scene = Counter(r["scene_group_id"] for r in q)
    checks["info_review_candidates_per_scene"] = {"pass": True, "detail": dict(per_scene)}

    # ---------------- benchmark (if built) ----------------
    pub_p, gt_p = BENCH / "public_manifest.json", PRIVATE / "triage_labels.json"
    if not pub_p.exists() or not gt_p.exists():
        checks["benchmark_built"] = {"pass": False, "detail": "NOT_BUILT (requires completed human review)"}
    else:
        pub, gt = read_json(pub_p), read_json(gt_p)
        items = pub["items"]
        prim = gt["primary"]
        chk("benchmark_built", True)
        miss = [i["item_id"] for i in items for c in i["cameras"] if not (BENCH / c["media"]).exists()]
        chk("all_media_exists", not miss, miss)
        badh = [i["item_id"] for i in items for c in i["cameras"] if (BENCH / c["media"]).exists() and sha256(BENCH / c["media"]) != c["sha256"]]
        chk("media_sha256_matches", not badh, badh)
        tids = [i["item_id"] for i in items]
        chk("no_duplicate_candidate_ids", len(tids) == len(set(tids)))
        chk("no_duplicate_exact_media", len({c["sha256"] for i in items for c in i["cameras"]}) == len(items))
        sp = {}
        leak = []
        for l in prim:
            sp.setdefault(l["split_group_id"], set()).add(l["split"])
        leak = [g for g, s in sp.items() if len(s) > 1]
        sc = {}
        for l in prim:
            sc.setdefault(l["scene_group_id"], set()).add(l["split"])
        leak += [g for g, s in sc.items() if len(s) > 1]
        chk("scene_group_split_leakage_zero", not leak, leak)
        chk("every_primary_sample_has_human_label", all(l["triage_label"] and l["reviewer"] and l["reviewed_at"] for l in prim))
        chk("review_confidence_policy_primary_HIGH_only", all(l["review_confidence"] == "HIGH" for l in prim))
        okm = all((l["must_surface_to_operator"] is True) == (l["triage_label"] == "ANCHORED_DANGER") for l in prim) and \
              all(a["must_surface_to_operator"] is None for a in gt.get("ambiguous", []))
        chk("must_surface_to_operator_valid", okm)
        txt = json.dumps(pub)
        leaked = [k for k in PRIVATE_KEYS if f'"{k}"' in txt]
        src_leak = any(s in txt for s in src)                          # no source ids in public manifest
        chk("no_private_gt_in_public_manifest", not leaked and not src_leak, leaked)
        fs_ok = all(len(c["frame_schedule_uniform_total64_v1"]) == 64 and
                    all(0 <= f["frame_index"] < c["frame_count"] for f in c["frame_schedule_uniform_total64_v1"]) and
                    [f["frame_index"] for f in c["frame_schedule_uniform_total64_v1"]] == sorted(f["frame_index"] for f in c["frame_schedule_uniform_total64_v1"])
                    for i in items for c in i["cameras"])
        chk("frame_schedules_valid", fs_ok)
        per = Counter(l["scene_group_id"] for l in prim)
        chk("max_3_clips_per_scene", max(per.values()) <= 3, dict(per))
        chk("public_and_private_item_sets_match", {l["candidate_id"] for l in prim} == set(tids))
        checks["info_class_counts"] = {"pass": True, "detail": {s: dict(Counter(l["triage_label"] for l in prim if l["split"] == s))
                                                                for s in ("calibration", "test")}}
        lock_p = BENCH / "BENCHMARK_LOCK.json"
        if lock_p.exists():
            lock = read_json(lock_p)
            badl = [f for f, h in lock["sha256"].items() if not (BENCH / f).exists() or sha256(BENCH / f) != h]
            chk("benchmark_lock_hashes_valid", not badl, badl)
        else:
            checks["benchmark_lock_hashes_valid"] = {"pass": False, "detail": "NOT_FROZEN"}

    hard = {k: v for k, v in checks.items() if not k.startswith("info_")}
    out = {"checks": checks, "all_pass": all(v["pass"] for v in hard.values())}
    write_json(BENCH / "reports" / "validation.json", out)
    for k, v in checks.items():
        print(("PASS " if v["pass"] else "FAIL ") + k, "" if v["pass"] else v["detail"])
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
