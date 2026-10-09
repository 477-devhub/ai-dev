"""Deterministic metadata-only priority selection. Never opens video or ground truth.

Only two input files are opened; selection uses explicit allowlisted projections.
Human fields are discarded without inspection. source_label is copied opaquely to
the deliverable, never passed to selection. Existing queues are never written.
Rebuilding refuses to overwrite an existing priority queue (possibly human-reviewed).
"""
from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
SEED, TARGET, CAP = 477, 55, 3
HUMAN_FIELDS = {
    "review_label", "review_confidence", "observable_summary", "danger_type_if_any",
    "hard_negative_type_if_any", "normal_subtype", "ambiguous_reason",
    "exclude_reason", "reviewer", "reviewed_at",
}
QUEUE_META = {
    "candidate_id", "scene_group_id", "split_group_id", "source_video_id",
    "start_sec", "end_sec", "window_kind", "discovery_hints",
    "related_to_reasoning_benchmark",
}
POOL_META = {
    "candidate_id", "dataset", "category", "camera", "take_id", "pool_status",
    "n_frames", "motion_mean", "person_frames_frac",
    "same_source_video_as_reasoning_v1", "same_scene_view_as_reasoning_v1",
    "same_split_group_as_reasoning_v1",
}
EXTRA = ["selected_for_priority_review", "selection_reason", "scene_group_rank", "diversity_tags"]
HINT_TAGS = {
    "empty_scene": "empty_scene_hint",
    "HN01_HN09_low_then_upright": "crouch_recover_proxy",
    "HN02_HN14_low_posture_sustained": "sit_lie_posture_proxy",
    "HN03_fast_movement": "running_proxy",
    "HN06_HN07_close_pair": "close_pair_hint",
    "HN11_dark": "darkness_low_visibility_hint",
    "HN12_multiple_people": "crowd_proxy",
    "HN15_visual_motion_no_person": "visual_noise_proxy",
}
EVENT_CATEGORY = {"swoon01": "fall", "fight01": "conflict", "fight_mv": "conflict",
                  "trespass01": "boundary", "trespass03": "boundary"}


def read_inputs():
    # csv.reader must tokenize the CSV; prohibited values are never interpreted,
    # displayed, inspected, or exposed to the selector.
    with (BENCH / "review/human_review_queue.csv").open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        fields = next(reader)
        indices = {k: fields.index(k) for k in QUEUE_META}
        candidates, copies = [], {}
        for cells in reader:
            meta = {k: cells[i] for k, i in indices.items()}
            candidates.append(meta)
            copies[meta["candidate_id"]] = {
                k: "" if k in HUMAN_FIELDS else cells[i] for i, k in enumerate(fields)
            }
    with (BENCH / "candidate_pool/candidates.csv").open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        indices = {k: header.index(k) for k in POOL_META}
        pool = {}
        for cells in reader:
            cid = cells[indices["candidate_id"]]
            if cid in copies:
                if cid in pool:
                    raise ValueError(f"duplicate pool id: {cid}")
                pool[cid] = {k: cells[i] for k, i in indices.items()}
    if len(copies) != len(candidates):
        raise ValueError("duplicate queue ids")
    for r in candidates:
        r.update(pool[r["candidate_id"]])
        r["independent"] = all(r[k].lower() == "false" for k in (
            "same_source_video_as_reasoning_v1", "same_scene_view_as_reasoning_v1",
            "same_split_group_as_reasoning_v1"))
        if r["independent"] != (r["related_to_reasoning_benchmark"].lower() == "false"):
            raise ValueError("reasoning relation metadata disagree")
        r["event"] = EVENT_CATEGORY.get(r["category"], "") if r["window_kind"] == "event" else ""
        hints = set(filter(None, r["discovery_hints"].split("|")))
        tags = {HINT_TAGS[h] for h in hints if h in HINT_TAGS}
        if r["event"]:
            tags.add(r["event"] + "_event_candidate")
        elif float(r["motion_mean"]) <= 6:
            tags.add("clear_low_motion_proxy")
        if not r["event"] and r["category"].startswith("trespass"):
            tags.add("entry_gate_source_context_proxy")
        if not r["event"] and float(r["person_frames_frac"]) > 0:
            tags.add("person_present_unspecified")
        r["tags"] = sorted(tags)
        r["quality_ok"] = int(r["n_frames"]) > 0 and r["pool_status"] == "kept:sent_to_review"
    return fields, candidates, copies


def select(candidates):
    eligible = [r for r in candidates if r["quality_ok"]]
    availability = Counter(r["scene_group_id"] for r in eligible)
    capacity = sum(min(CAP, n) for n in availability.values())
    limit = min(TARGET, capacity)
    tag_frequency = Counter(t for r in eligible for t in r["tags"])
    chosen, reasons = [], {}
    counts, tags = Counter(), Counter()

    def feasible(r):
        return r["candidate_id"] not in reasons and counts[r["scene_group_id"]] < CAP

    def score(r):
        scene = r["scene_group_id"]
        event_missing = bool(r["event"]) and not any(
            x["scene_group_id"] == scene and x["event"] for x in chosen)
        gain = sum(1000 // tag_frequency[t] for t in r["tags"] if not tags[t])
        local_tags = {t for x in chosen if x["scene_group_id"] == scene for t in x["tags"]}
        local_gain = len(set(r["tags"]) - local_tags)
        # Avoid repeating actor/session and exact source video whenever alternatives exist.
        source_new = not any(x["source_video_id"] == r["source_video_id"] for x in chosen)
        session_new = not any((x["dataset"], x["take_id"]) ==
                              (r["dataset"], r["take_id"]) for x in chosen)
        tie = hashlib.sha256(f"{SEED}:{r['candidate_id']}".encode()).hexdigest()
        return (int(event_missing), gain, local_gain, int(source_new), int(session_new), tie)

    def add(r, phase):
        s = score(r)
        reasons[r["candidate_id"]] = (
            f"{phase}; independent={r['independent']}; scene_event_gap={s[0]}; "
            f"rare_tag_gain={s[1]}; new_scene_tags={s[2]}; new_source={s[3]}; new_session={s[4]}")
        chosen.append(r)
        counts[r["scene_group_id"]] += 1
        tags.update(r["tags"])

    # All usable independent candidates are reserved first, subject only to scene cap.
    while options := [r for r in eligible if r["independent"] and feasible(r)]:
        if len(chosen) == limit:
            break
        add(max(options, key=score), "independent_reservation")
    # Source-metadata event coverage in every scene that has event candidates.
    for scene in sorted(availability):
        options = [r for r in eligible if r["scene_group_id"] == scene and r["event"] and feasible(r)]
        if options and len(chosen) < limit and not any(x["scene_group_id"] == scene and x["event"] for x in chosen):
            add(max(options, key=score), "source_event_scene_coverage")
    # Cover rare hints, then balance scenes and source/session representations.
    while len(chosen) < limit:
        options = [r for r in eligible if feasible(r)]
        if not options:
            break
        add(max(options, key=lambda r: (int(counts[r["scene_group_id"]] < 2), *score(r))),
            "hint_source_scene_diversity")
    return chosen, reasons, capacity


def table(title, rows):
    return [f"\n## {title}\n", "| Group | Original | Priority |", "|---|---:|---:|"] + [
        f"| {k} | {a} | {b} |" for k, a, b in rows]


def main():
    out = BENCH / "review/human_review_priority.csv"
    if out.exists():
        raise SystemExit("Refusing to overwrite existing priority queue; preserve human review work.")
    fields, candidates, copies = read_inputs()
    chosen, reasons, capacity = select(candidates)
    chosen_ids = {r["candidate_id"] for r in chosen}
    counts = Counter(r["scene_group_id"] for r in chosen)
    assert len(chosen_ids) == len(chosen) and max(counts.values()) <= CAP
    ranks, audit = {}, []
    excluded = Counter()
    for scene in sorted({r["scene_group_id"] for r in candidates}):
        members = [r for r in chosen if r["scene_group_id"] == scene]
        members += sorted((r for r in candidates if r["scene_group_id"] == scene and r["candidate_id"] not in chosen_ids),
                          key=lambda r: r["candidate_id"])
        for rank, r in enumerate(members, 1):
            cid = r["candidate_id"]
            ranks[cid] = rank
            if cid not in chosen_ids:
                reason = ("quality_or_prior_duplicate_filter" if not r["quality_ok"] else
                          "independent_scene_cap" if r["independent"] and counts[scene] == CAP else
                          "related_scene_cap_representative_only" if counts[scene] == CAP else "target_budget")
                reasons[cid] = reason
                excluded[reason] += 1
            audit.append({"candidate_id": cid, "scene_group_id": scene,
                          "selected_for_priority_review": str(cid in chosen_ids),
                          "selection_reason": reasons[cid], "scene_group_rank": rank,
                          "diversity_tags": "|".join(r["tags"])})
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields + EXTRA)
        writer.writeheader()
        for r in chosen:
            cid = r["candidate_id"]
            row = {**copies[cid], "selected_for_priority_review": "True", "selection_reason": reasons[cid],
                   "scene_group_rank": ranks[cid], "diversity_tags": "|".join(r["tags"])}
            assert all(row[k] == "" for k in HUMAN_FIELDS)
            writer.writerow(row)
    with (BENCH / "reports/human_review_priority_selection_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "scene_group_id"] + EXTRA)
        writer.writeheader()
        writer.writerows(audit)
    independent = sum(r["independent"] for r in chosen)
    report = ["# Human review priority report\n", "```yaml",
              f"Original candidates: {len(candidates)}", f"Priority candidates: {len(chosen)}",
              f"Unique scene groups: {len(counts)}", f"Independent-from-reasoning-v1 count: {independent}",
              f"Related count: {len(chosen) - independent}", f"Per-scene max: {max(counts.values())}",
              f"Requested target: {TARGET}", f"Feasible scene-capped maximum: {capacity}",
              "P1/P4 outputs accessed: NO", "Human labels generated: NO", "```\n",
              "The requested 50–60 candidates cannot be reached under the scene cap: "
              "11 scenes have at least 3 candidates, 3 scenes have 2, and 4 scenes have 1; "
              "11×3 + 3×2 + 4×1 = 43. The cap takes precedence; no new candidates or scenes were invented.\n",
              "This is a priority subset for human video review, not a labeled or final benchmark. "
              "Only humans assign CLEAR_NORMAL / HARD_NEGATIVE_NORMAL / ANCHORED_DANGER / AMBIGUOUS / EXCLUDE.\n",
              "## Method and data boundary\n",
              "Inputs: review/human_review_queue.csv and candidate_pool/candidates.csv only. "
              "Selection receives only explicit allowlisted metadata. No media, predictions, evaluation, "
              "cascade results, private ground truth, or human label values are inspected. Source label "
              "is copied as opaque review context, excluded from selection and hidden by the priority UI. "
              "All ten human-input fields are blank. Original queue and reviewer2 queue are untouched.\n",
              "Quality eligibility: n_frames > 0 and pool_status=kept:sent_to_review. "
              "Uses existing duplicate filtering; no new image comparison or content judgment. "
              "Independence requires all three reasoning-v1 source/view/split relations to be false. "
              "Reserve independent candidates first (scene cap applies), ensure one source event candidate "
              "per available event scene, then fill using scene floor 2 and lexicographic score: missing "
              "scene event, new rare tags (sum floor(1000/tag availability)), new within-scene tags, "
              "new source, new dataset/take session, SHA256('477:candidate_id') tie break. "
              "No stochastic tie break. Every selection reason records score components. "
              "scene_group_rank is selected order within scene followed by excluded IDs sorted ascending; "
              "it is a selection rank, not a quality or danger rank.\n"]
    def coverage(key):
        a, b = Counter(r[key] for r in candidates), Counter(r[key] for r in chosen)
        return [(k, a[k], b[k]) for k in sorted(a)]
    report += table("Candidates per scene group", coverage("scene_group_id"))
    for title, key in [("Coverage by source type", "dataset"), ("Source categories", "category"),
                       ("Camera", "camera"), ("Actor/session proxy (split group)", "split_group_id"),
                       ("Recording session (take ID)", "take_id"), ("Window kind", "window_kind")]:
        report += table(title, coverage(key))
    for title, get in [("Coverage by discovery hint", lambda r: list(filter(None, r["discovery_hints"].split("|"))) or ["(no hint)"]),
                       ("Diversity tags (proxies, not labels)", lambda r: r["tags"])]:
        a, b = Counter(t for r in candidates for t in get(r)), Counter(t for r in chosen for t in get(r))
        report += table(title, [(k, a[k], b[k]) for k in sorted(a)])
    report += ["\n## Event-candidate coverage\n", "Source category + window_kind=event only; no source_label or danger inference.\n",
               "| Type | Original | Priority | Unique priority scenes |", "|---|---:|---:|---:|"]
    for event in ("fall", "conflict", "boundary"):
        rows = [r for r in chosen if r["event"] == event]
        report.append(f"| {event} | {sum(r['event'] == event for r in candidates)} | {len(rows)} | {len({r['scene_group_id'] for r in rows})} |")
    report += ["\n## Candidates excluded from priority review\n", f"Count: {len(candidates) - len(chosen)}. "
               "Excluded candidates remain in the original queue; exclusion here is not a human EXCLUDE label.\n"]
    report += [f"- {k}: {v}" for k, v in sorted(excluded.items())]
    report += ["\nCandidate-level decisions for all 115 candidates: human_review_priority_selection_audit.csv.\n",
               "## Potential diversity limitations\n",
               "- 19 independent candidates available; 16 retained. Three repeat candidates exceed caps in SCN_08/SCN_09.\n"
               "- Walking has no explicit discovery hint: person_present_unspecified is only person presence, not walking.\n"
               "- Entry/gate uses pre/post-event source context only; normal entry and gate presence are unverified.\n"
               "- Brief contact has no independent hint: HN06_HN07_close_pair is a shared proximity proxy, not contact evidence.\n"
               "- Low motion, recovery, sit/lie, running, crowd and visual noise tags are discovery proxies only.\n"
               "- Fall events exist in two scenes only; darkness in one scene and visual-noise hint in one candidate.\n"
               "- Cameras within a split group may share site/actors; 18 scenes are not 18 independent sites. "
               "Only two datasets and five source categories are available; actors have no explicit IDs. "
               "Selection uses take and split-group proxies and cannot guarantee actor diversity.\n",
               "## Start reduced human review\n", "```sh",
               "python benchmark_triage_v1/scripts/serve_review.py --priority", "```",
               "Default and --reviewer2 modes keep their existing queues. --priority saves human edits only "
               "to the priority CSV with backups; it does not synchronize labels into the original queue. "
               "The builder refuses to overwrite a priority queue to preserve later human edits.\n"]
    (BENCH / "reports/human_review_priority_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Original={len(candidates)} Selected={len(chosen)} Scenes={len(counts)} "
          f"Independent={independent} Related={len(chosen)-independent} Capacity={capacity}")


if __name__ == "__main__":
    main()
