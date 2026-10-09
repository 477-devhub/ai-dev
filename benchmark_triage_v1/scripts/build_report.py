"""Step 16 — generate candidate_pool/dedup_report.md, reports/diversity_report.md, reports/leakage_report.md
and reports/dataset_report.md from the current state (works before and after human review).
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict

from _common import BENCH, MANIFESTS, POOL, PRIVATE, REPORTS, REVIEW, assert_writable, read_csv, read_json

HN_GROUPS = {"crouch/recover": ["HN01", "HN09"], "sit/lie or on ground": ["HN02", "HN14"], "normal entry": ["HN04", "HN05"],
             "running": ["HN03"], "close pair": ["HN06"], "brief contact": ["HN07", "HN13"], "object pickup": ["HN08"],
             "occlusion": ["HN10"], "darkness": ["HN11"], "crowd": ["HN12"], "visual noise": ["HN15"]}


def write(path, text):
    p = assert_writable(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def table(rows, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join(out)


def main() -> None:
    if (PRIVATE / "triage_labels.json").exists() and read_json(PRIVATE / "triage_labels.json").get("human_gt_policy") == "priority_minimal_v1":
        from _priority_gt import write_reports
        write_reports()
        return
    srcs = read_json(POOL / "candidate_sources.json")["sources"]
    pool = read_csv(POOL / "candidates.csv")
    queue = read_csv(REVIEW / "human_review_queue.csv")
    scenes = read_json(MANIFESTS / "scene_manifest.json")
    sg = scenes["scene_groups"]
    status = read_json(REVIEW / "review_status.json") if (REVIEW / "review_status.json").exists() else {}
    clips = read_json(REVIEW / "clips" / "clip_manifest.json")["clips"] if (REVIEW / "clips" / "clip_manifest.json").exists() else {}
    built = (PRIVATE / "triage_labels.json").exists()
    gt = read_json(PRIVATE / "triage_labels.json") if built else None
    val = read_json(REPORTS / "validation.json") if (REPORTS / "validation.json").exists() else {"checks": {}}
    frozen = (BENCH / "BENCHMARK_LOCK.json").exists()

    st = Counter(r["pool_status"].split(":")[0] + (":" + r["pool_status"].split(":")[1] if ":" in r["pool_status"] else "") for r in pool)
    removed = Counter(r["pool_status"].split(":")[1] for r in pool if r["pool_status"].startswith("removed"))
    exact = sum(1 for r in pool if r["pool_status"].startswith("removed:exact"))
    near = sum(1 for r in pool if r["pool_status"].startswith("removed:near"))
    kept = [r for r in pool if r["pool_status"].startswith("kept")]
    kind = Counter(r["window_kind"] for r in pool)

    # ---------------------------------------------------------------- dedup report
    per_view_pool = Counter(r["scene_group_id"] for r in kept)
    per_view_q = Counter(q["scene_group_id"] for q in queue)
    view_rows = [{"scene_group": v, "split_group": d["split_group_id"], "categories": ",".join(d["categories"]),
                  "cameras": ",".join(d["cameras"]), "takes": len(d["takes"]), "source_videos": d["n_sources"],
                  "windows_after_dedup": per_view_pool.get(v, 0), "sent_to_review": per_view_q.get(v, 0),
                  "related_to_reasoning_v1": d["related_to_reasoning_v1"] or d["split_group_related_to_reasoning_v1"]}
                 for v, d in sorted(sg.items())]
    write(POOL / "dedup_report.md", f"""# Dedup report — 477-triage-normal-v1 candidate pool

| Stage | Count |
|---|---|
| Candidate windows before dedup | {len(pool)} (pre-event {kind['pre_event']}, post-event {kind['post_event']}, event {kind['event']}) |
| Removed: same source video as 477-reasoning-v1 | {removed.get('same_source_video_as_reasoning_v1', 0)} |
| Removed: too few frames / black or unusable | {removed.get('too_few_frames', 0) + removed.get('black_or_unusable', 0)} |
| Identical-hash duplicates (person-free windows; identical 4-frame perceptual dHash in the same view; not byte-identical media) | {exact} |
| Near duplicates (person-free windows, all 4 frame dHash within 6 bits) | {near} |
| Kept after dedup | {len(kept)} |
| Same-scene groups (visual camera views) | {len(sg)} |
| Physical split groups (views + shared staged takes) | {len(scenes['split_groups'])} |
| Sent to human review (scene caps + diversity selection) | {len(queue)} |

**Why the scene count is small.**
- Hundreds of windows come from very few backgrounds.
- AI Hub 171 repeats the same staged camera view across takes (e.g. 710-2…710-6), seasons and cameras.
- A window is therefore never counted as an independent sample. The independent units are the {len(sg)} camera views, and for leakage the {len(scenes['split_groups'])} split groups.

**Scene identity is visual, not header-based.** It uses median-background edge-map correlation. Header `place`/`cam` labels were wrong for identity:
- swoon `cam01` and `cam02` are two different physical places (day overhead and night garage);
- `710-3_cam01_..._summer` matches the night view.

## Per camera view

{table(view_rows, list(view_rows[0].keys()))}
""")

    # ---------------------------------------------------------------- diversity (candidates or final)
    def hint_cat(h):
        for name, codes in HN_GROUPS.items():
            if any(h.startswith(c) for c in codes):
                return name
        return None

    qhint = Counter()
    for q in queue:
        for h in q["discovery_hints"].split("|"):
            c = hint_cat(h)
            if c:
                qhint[c] += 1
    qtype = Counter(q["suggested_candidate_type"] for q in queue)
    dur = [c["clip_meta"]["duration"] for c in clips.values()]
    src_by_id = {s["source_id"]: s for s in srcs}
    final_txt = "Not built yet (requires completed human review)."
    if built:
        prim = gt["primary"]
        lab = Counter(l["triage_label"] for l in prim)
        hn = Counter(t for l in prim if l["hard_negative_type"] for t in l["hard_negative_type"])
        dg = Counter(l["danger_type"] for l in prim if l["danger_type"])
        cps = Counter(l["scene_group_id"] for l in prim)
        final_txt = (f"Classes: {dict(lab)}\n\nUnique scene groups: {len(cps)}; max clips per scene: {max(cps.values())}\n\n"
                     f"Hard-negative types: {dict(hn)}\n\nDanger types: {dict(dg)}\n\n"
                     f"Scene groups per class: " + str({k: len({l['scene_group_id'] for l in prim if l['triage_label'] == k}) for k in lab}))
    tod = Counter((src_by_id[q["source_video_id"]].get("time_of_day") or "n/a") for q in queue)
    write(REPORTS / "diversity_report.md", f"""# Diversity report — 477-triage-normal-v1

## Final benchmark
{final_txt}

## Review queue (candidates, NOT labels)

| | |
|---|---|
| Candidates in queue | {len(queue)} |
| Unique source videos | {len({q['source_video_id'] for q in queue})} |
| Unique scene groups (camera views) | {len({q['scene_group_id'] for q in queue})} |
| Unique split groups (physical sites + staged takes) | {len({q['split_group_id'] for q in queue})} |
| Max candidates per scene group | {max(per_view_q.values())} |
| Suggested types (hints only) | {dict(qtype)} |
| Discovery-hint categories (CV hints only; a candidate can carry several) | {dict(qhint)} |
| Source time-of-day header | {dict(tod)} |
| Clip duration (s) | min {min(dur) if dur else 'n/a'}, median {round(statistics.median(dur), 2) if dur else 'n/a'}, max {max(dur) if dur else 'n/a'} |

## Camera / background diversity

| Scene group | Categories | Cameras | Takes | Related to reasoning-v1 |
|---|---|---|---|---|
""" + "\n".join(f"| {v} | {','.join(d['categories'])} | {','.join(d['cameras'])} | {len(d['takes'])} | {d['related_to_reasoning_v1'] or d['split_group_related_to_reasoning_v1']} |" for v, d in sorted(sg.items())) + """

**Known diversity limits of the local data.** These are real, not fixable by selection:
- **AI Hub 171 fight** is a green-screen studio, not real CCTV backgrounds.
- **AI Hub 171 swoon and trespass** are staged scenes at a handful of streets; the same actors repeat across takes.
- **AI Hub 71953** clips are about 30 s and are the fight event itself, so they provide no normal footage.
- **No indoor real-world, crowd, transit or commercial scenes** exist locally.
""")

    # ---------------------------------------------------------------- leakage
    v1_src = [s for s in srcs if s["used_in_reasoning_v1"]]
    q_same_src = [q for q in queue if src_by_id[q["source_video_id"]]["used_in_reasoning_v1"]]
    q_same_view = [q for q in queue if sg[q["scene_group_id"]]["related_to_reasoning_v1"]]
    q_same_split = [q for q in queue if sg[q["scene_group_id"]]["split_group_related_to_reasoning_v1"]]
    final_leak = ""
    if built:
        prim = gt["primary"]
        test = [l for l in prim if l["split"] == "test"]
        final_leak = f"""
## Final benchmark
| | All primary | Test split |
|---|---|---|
| Exact window overlap with reasoning-v1 | 0 | 0 |
| Same source video | {sum(1 for l in prim if src_by_id[l['source_video_id']]['used_in_reasoning_v1'])} | {sum(1 for l in test if src_by_id[l['source_video_id']]['used_in_reasoning_v1'])} |
| Same scene view as reasoning-v1 | {sum(1 for l in prim if sg[l['scene_group_id']]['related_to_reasoning_v1'])} | {sum(1 for l in test if sg[l['scene_group_id']]['related_to_reasoning_v1'])} |
| Same split group (site/actors) as reasoning-v1 | {sum(1 for l in prim if sg[l['scene_group_id']]['split_group_related_to_reasoning_v1'])} | {sum(1 for l in test if sg[l['scene_group_id']]['split_group_related_to_reasoning_v1'])} |
| Calibration/test scene leakage | {'0' if val['checks'].get('scene_group_split_leakage_zero', {}).get('pass') else 'CHECK FAILED'} | |
"""
    write(REPORTS / "leakage_report.md", f"""# Leakage / overlap report — 477-triage-normal-v1 vs 477-reasoning-v1

477-reasoning-v1 drew its clips from these {len(v1_src)} source videos: {', '.join(s['source_id'] for s in v1_src)}.

**Policy:**
- Every window of those source videos is removed from the pool, so there is no exact or same-video overlap.
- Same scene view and same site/actors cannot be fully avoided with local data. These are flagged as `related_to_reasoning_benchmark`.

## Review queue
| | Count |
|---|---|
| Exact window overlap | 0 (whole source videos excluded) |
| Same source video | {len(q_same_src)} |
| Same scene view (same background) | {len(q_same_view)} |
| Same split group (same site, staged takes or actors) | {len(q_same_split)} |
| Fully independent of reasoning-v1 | {len(queue) - len(q_same_split)} |
{final_leak}
**Model-result independence.** No P0–P4 prediction, cascade threshold or evaluator output was read by any script (see the docstrings in `scripts/`). The CV features used for discovery are generic person, motion and posture measurements from the pretrained detector weights. They are not the P0 rule engine.

**Implementer exposure.** The implementer has seen 477-reasoning-v1 clips and GT. Candidates were chosen by fixed rules and seed 477, never by eye.
""")

    # ---------------------------------------------------------------- dataset report
    rs = status.get("label_counts", {})
    complete = status.get("human_review_complete", False)
    overall = "COMPLETE" if frozen else ("NEEDS HUMAN REVIEW" if not complete else "PARTIAL")
    vck = val.get("checks", {})
    vf = lambda k: ("PASS" if vck.get(k, {}).get("pass") else ("NOT BUILT" if not built else "FAIL"))
    datasets = Counter(s["dataset"] for s in srcs)
    fin = Counter(l["triage_label"] for l in gt["primary"]) if built else Counter()
    spl = Counter(l["split"] for l in gt["primary"]) if built else Counter()
    write(REPORTS / "dataset_report.md", f"""# 477-TRIAGE-NORMAL-V1 DATASET REPORT

## Status
**{overall}**

## SOURCE INVENTORY
| | |
|---|---|
| AI Hub sources | AI Hub 171 abnormal-behavior CCTV: {datasets['aihub_171_abnormal_cctv']} videos (swoon 20, trespass 44, fight 54 in green-screen studio). AI Hub 71953 multi-view: {datasets['aihub_71953_multiview_cctv']} videos (5 fight events × 2 views) |
| Other sources | none (no normal/benign dataset exists locally) |
| Total source videos | {len(srcs)} |
| Unique scene groups (camera views) | {len(sg)} |
| Physical split groups | {len(scenes['split_groups'])} |

## CANDIDATE MINING
| | |
|---|---|
| Candidates before dedup | {len(pool)} |
| After exact dedup (and reasoning-v1 source removal / quality) | {len(pool) - sum(removed.values()) + near} |
| After near-dup and scene grouping | {len(kept)} windows in {len(per_view_pool)} scene groups |
| Sent to human review | {len(queue)} |

## HUMAN REVIEW
| | |
|---|---|
| Reviewed | {status.get('labelled', 0)} |
| Pending | {status.get('pending', len(queue))} |
| Excluded | {rs.get('EXCLUDE', 0)} |
| Clear Normal | {rs.get('CLEAR_NORMAL', 0)} |
| Hard Negative | {rs.get('HARD_NEGATIVE_NORMAL', 0)} |
| Anchored Danger | {rs.get('ANCHORED_DANGER', 0)} |
| Ambiguous | {rs.get('AMBIGUOUS', 0)} |

## DIVERSITY
See `reports/diversity_report.md`. Candidate level: {len({q['scene_group_id'] for q in queue})} scene groups and {len({q['split_group_id'] for q in queue})} split groups in the queue. Final-level counts appear after review.

## LEAKAGE / OVERLAP
| | |
|---|---|
| Overlap with 477-reasoning-v1: exact | 0 |
| Same source | 0 |
| Same scene (queue) | {len(q_same_view)} |
| Same site/actors (queue) | {len(q_same_split)} |
| Calibration/test scene leakage | {'0' if built and vck.get('scene_group_split_leakage_zero', {}).get('pass') else 'not built'} |

## FINAL BENCHMARK
| | |
|---|---|
| Total | {sum(fin.values()) if built else 'not built'} |
| Calibration | {spl.get('calibration', '-')} |
| Test | {spl.get('test', '-')} |
| CLEAR_NORMAL | {fin.get('CLEAR_NORMAL', '-')} |
| HARD_NEGATIVE_NORMAL | {fin.get('HARD_NEGATIVE_NORMAL', '-')} |
| ANCHORED_DANGER | {fin.get('ANCHORED_DANGER', '-')} |

## VALIDATION
| | |
|---|---|
| Media hashes | {vf('media_sha256_matches')} (review clips: {'PASS' if vck.get('review_clip_sha256', {}).get('pass') else 'n/a'}) |
| GT completeness | {vf('every_primary_sample_has_human_label')} |
| Private/public separation | {vf('no_private_gt_in_public_manifest')} |
| Scene leakage | {vf('scene_group_split_leakage_zero')} |
| Benchmark lock | {'FROZEN' if frozen else 'NOT FROZEN'} |

## READY FOR P1/P4 RUN?
**{'YES' if frozen else 'NO'}**
""" + ("" if frozen else f"""
## What is still required (if NO)
1. **Human review of {status.get('pending', len(queue))} candidates.**
   - Run `python scripts/serve_review.py` (or edit `review/human_review_queue.csv`) following `review/human_review_guide.md`.
   - Event candidates and every candidate showing low posture, close pairs or wall/gate activity must be judged from the clip, not the sheet.
2. **Optional second review** of the {len(read_csv(REVIEW / 'human_review_queue_reviewer2.csv'))} rows in `review/human_review_queue_reviewer2.csv`: all event candidates plus 20 others. It must be done by a different person.
3. `python scripts/validate_human_labels.py` must report COMPLETE.
4. `python scripts/build_benchmark.py`, then `validate_benchmark.py` and `build_report.py`.
5. A person approves class counts and the split in `review/approvals.json` (from `approvals_TEMPLATE.json`). Then run `freeze_benchmark.py`.

## Capacity ceiling of the local data (read before approving class counts)
- **Total ceiling.** With max 3 clips per scene group and {len({q['scene_group_id'] for q in queue})} scene groups in the queue, the final benchmark can hold **at most {3 * len({q['scene_group_id'] for q in queue})} clips in total**. That is below the ~90 target *before* any candidate is rejected.
- **Normals.** Normal candidates exist in {len({q['scene_group_id'] for q in queue if q['window_kind'] != 'event'})} scene groups. Danger candidates exist in {len({q['scene_group_id'] for q in queue if q['window_kind'] == 'event'})}.
- **Independence.** {len(queue) - len(q_same_split)} of {len(queue)} queued candidates are fully independent of 477-reasoning-v1 sites and actors. The rest share a site or actors with it (no exact or same-video overlap).
- **Expectation.** A smaller benchmark, roughly 15–25 clear normal, 15–25 hard negative and 10–15 anchored danger, is the realistic outcome. The brief allows this: "억지 balance 금지".
- **Closing the gap.** Reaching ~90 independent clips needs new source data: a benign/normal CCTV dataset, or AI Hub categories with real street, indoor or crowd footage. No amount of further mining of these sources will do it.
"""))
    print("reports written; status", overall)


if __name__ == "__main__":
    main()
