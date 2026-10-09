"""Minimal priority human GT. No video interpretation, confidence selection or model-output access.

Inputs are the existing human queues, priority-selection audit, scene/source metadata,
and clip manifest. Labels are immutable; only reviewer provenance may be filled.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import random
import shutil
from collections import Counter, defaultdict

from _common import (BENCH, BENCHMARK_ID, MANIFESTS, MEDIA, PRIVATE, REPORTS, REVIEW,
                     SEED, read_csv, read_json, sha256, write_csv, write_json)

POLICY = "priority_minimal_v1"
PRIMARY = ("CLEAR_NORMAL", "HARD_NEGATIVE_NORMAL", "ANCHORED_DANGER")
LABELS = set(PRIMARY) | {"AMBIGUOUS", "EXCLUDE"}
MANIFEST = REVIEW / "priority_review_manifest.json"
OPTIONAL = ("review_confidence", "observable_summary", "normal_subtype",
            "hard_negative_type_if_any", "danger_type_if_any", "ambiguous_reason", "reviewed_at")
CONFIDENCE_NOTE = "Human labels were manually assigned, but per-item confidence was not collected consistently."
DERIVED = {
    "CLEAR_NORMAL": {"reference_binary": "NORMAL", "must_surface_to_operator": False},
    "HARD_NEGATIVE_NORMAL": {"reference_binary": "NORMAL", "must_surface_to_operator": False},
    "ANCHORED_DANGER": {"reference_binary": "DANGER", "must_surface_to_operator": True},
    "AMBIGUOUS": {"reference_binary": "AMBIGUOUS", "must_surface_to_operator": None},
}


def unfrozen():
    if (BENCH / "BENCHMARK_LOCK.json").exists():
        raise RuntimeError("Benchmark already frozen; changes require v2")


def label_digest(rows):
    pairs = sorted((r["candidate_id"], r.get("review_label", "")) for r in rows)
    return hashlib.sha256(json.dumps(pairs, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def initialize_manifest():
    unfrozen()
    if MANIFEST.exists():
        print("Priority manifest already exists; preserving registered human labels.")
        return
    priority_path = REVIEW / "human_review_priority.csv"
    priority, queue = read_csv(priority_path), read_csv(REVIEW / "human_review_queue.csv")
    audit = read_csv(REPORTS / "human_review_priority_selection_audit.csv")
    selected = sorted(r["candidate_id"] for r in audit if r["selected_for_priority_review"].lower() == "true")
    ids = [r["candidate_id"] for r in priority]
    if len(ids) != len(set(ids)) or sorted(ids) != selected:
        raise ValueError("priority IDs do not match original selection audit")
    if any(not r.get("review_label") or r["review_label"] not in LABELS for r in priority):
        raise ValueError("Missing/invalid human label; no label will be generated")
    byid = {r["candidate_id"]: r for r in queue}
    if len(byid) != len(queue) or any(cid not in byid for cid in ids):
        raise ValueError("Invalid source queue ID membership")
    if any(byid[r["candidate_id"]]["review_label"] != r["review_label"] for r in priority):
        raise ValueError("Priority labels differ from already merged source queue")
    # File modification time is provenance for the batch, never a fabricated item timestamp.
    batch_time = dt.datetime.fromtimestamp(priority_path.stat().st_mtime, dt.timezone(dt.timedelta(hours=9))).isoformat()
    digest = label_digest(priority)
    backup_dir = REVIEW / "backups"
    backup_dir.mkdir(exist_ok=True)
    tag = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    updated = {}
    for path, rows in ((priority_path, priority), (REVIEW / "human_review_queue.csv", queue)):
        changes = 0
        before = label_digest(rows)
        for r in rows:
            if r["candidate_id"] in selected and r.get("review_label") and not r.get("reviewer", "").strip():
                r["reviewer"] = "reviewer_01"
                changes += 1
        if changes:
            shutil.copyfile(path, backup_dir / f"{path.stem}.before_reviewer_metadata.{tag}.csv")
            write_csv(path, rows, list(rows[0]))
        assert before == label_digest(rows)
        updated[path.name] = changes
    counts = dict(Counter(r["review_label"] for r in priority))
    write_json(MANIFEST, {
        "human_gt_policy": POLICY, "source_candidate_count": len(queue), "priority_selected": len(priority),
        "human_reviewed": len(priority), "unreviewed": sum(not r.get("review_label") for r in queue),
        "priority_candidate_ids": selected, "label_counts": counts, "human_label_sha256": digest,
        "human_review_protocol": "Manual video review of priority subset",
        "auxiliary_metadata_policy": "Optional; not used for primary evaluation",
        "required_human_fields": ["candidate_id", "review_label"],
        "reviewer_provenance": "User confirmed a single actual human reviewer; fill blank metadata with reviewer_01 only",
        "reviewer_metadata_rows_filled": updated,
        "annotation_batch_timestamp": batch_time,
        "annotation_batch_timestamp_basis": "priority CSV modification time before reviewer metadata update; not per-item review time",
        "confidence_note": CONFIDENCE_NOTE,
        "derived_mapping": {
            "CLEAR_NORMAL": {"reference_binary": "NORMAL", "must_surface_to_operator": False},
            "HARD_NEGATIVE_NORMAL": {"reference_binary": "NORMAL", "must_surface_to_operator": False},
            "ANCHORED_DANGER": {"reference_binary": "DANGER", "must_surface_to_operator": True},
            "AMBIGUOUS": {"reference_binary": "AMBIGUOUS", "must_surface_to_operator": None},
        },
    })
    print("Registered existing manual labels:", counts, "reviewer metadata filled:", updated)


def validate_labels(persist=True):
    priority = read_csv(REVIEW / "human_review_priority.csv")
    queue = read_csv(REVIEW / "human_review_queue.csv")
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    expected = manifest.get("priority_candidate_ids", [])
    problems = []
    ids = [r.get("candidate_id", "") for r in priority]
    duplicate = len(ids) - len(set(ids))
    if duplicate:
        problems.append("duplicate priority candidate ID")
    if any(not cid for cid in ids):
        problems.append("missing candidate ID")
    if not expected or len(expected) != len(set(expected)) or set(ids) != set(expected):
        problems.append("candidate ID set differs from priority manifest")
    if len(priority) != manifest.get("priority_selected"):
        problems.append("priority selected count differs from manifest")
    missing = [r["candidate_id"] for r in priority if not r.get("review_label", "").strip()]
    invalid = [r["candidate_id"] for r in priority if r.get("review_label", "").strip() and r["review_label"] not in LABELS]
    problems += [f"missing review_label: {cid}" for cid in missing]
    problems += [f"invalid review_label: {cid}" for cid in invalid]
    if manifest.get("human_label_sha256") != label_digest(priority):
        problems.append("registered human label snapshot changed")
    qids = [r["candidate_id"] for r in queue]
    if len(qids) != len(set(qids)):
        problems.append("duplicate source queue ID")
    byid = {r["candidate_id"]: r for r in queue}
    for r in priority:
        if r["candidate_id"] not in byid or byid[r["candidate_id"]].get("review_label") != r.get("review_label"):
            problems.append(f"merged human-label mismatch: {r['candidate_id']}")
    outside = [r["candidate_id"] for r in queue if r.get("review_label") and r["candidate_id"] not in set(expected)]
    if outside:
        problems.append(f"labelled IDs outside priority manifest: {outside}")
    counts = Counter(r.get("review_label") or "UNREVIEWED" for r in priority)
    auxiliary = {k: sum(not r.get(k, "").strip() for r in priority) for k in OPTIONAL}
    # Subtype warnings apply to the respective human label only.
    auxiliary["applicable_subtype_missing"] = sum(
        not r.get({"CLEAR_NORMAL": "normal_subtype", "HARD_NEGATIVE_NORMAL": "hard_negative_type_if_any",
                   "ANCHORED_DANGER": "danger_type_if_any", "AMBIGUOUS": "ambiguous_reason"}.get(r.get("review_label"), "exclude_reason"))
        for r in priority)
    status = {"scope": POLICY, "queue_size": len(priority), "labelled": len(priority)-len(missing),
              "source_queue_size": len(queue), "unreviewed": sum(not r.get("review_label") for r in queue),
              "pending": len(missing), "label_counts": dict(counts), "problems": problems,
              "invalid_labels": len(invalid), "duplicate_ids": duplicate,
              "auxiliary_missing": auxiliary, "warnings_only": True,
              "primary_usable": sum(counts[l] for l in PRIMARY), "ambiguous_challenge": counts["AMBIGUOUS"],
              "human_review_complete": not problems, "additional_human_review_required": bool(missing),
              "status": "PRIORITY HUMAN REVIEW — PASS" if not problems else "PRIORITY HUMAN REVIEW — FAIL"}
    if persist:
        write_json(REVIEW / "review_status.json", status)
    return status


def choose_split(rows):
    # Preserve the stronger existing physical site/actor/take grouping, which also
    # keeps every scene intact. Exhaustive deterministic search over eight groups.
    groups = sorted({r["split_group_id"] for r in rows})
    cls = {g: Counter(r["review_label"] for r in rows if r["split_group_id"] == g) for g in groups}
    related = {g: any(r["related_to_reasoning_benchmark"].lower() == "true" for r in rows if r["split_group_id"] == g) for g in groups}
    total = Counter(r["review_label"] for r in rows)
    choices = []
    for bits in itertools.product((0, 1), repeat=len(groups)):
        cal = Counter()
        for g, bit in zip(groups, bits):
            if bit:
                cal.update(cls[g])
        n = sum(cal.values())
        if n in (0, len(rows)):
            continue
        missing = sum(cal[l] == 0 or cal[l] == total[l] for l in PRIMARY if total[l])
        count_deviation = abs(n - 0.4 * len(rows))
        misplaced = sum(sum(cls[g].values()) for g, bit in zip(groups, bits)
                        if (related[g] and not bit) or (not related[g] and bit))
        class_deviation = sum(abs(cal[l] / total[l] - 0.4) for l in PRIMARY if total[l])
        choices.append(((missing, round(count_deviation, 8), misplaced, round(class_deviation, 8), bits), bits))
    if not choices:
        raise ValueError("No nonempty leakage-free calibration/test split exists")
    key, bits = min(choices)
    return {g: "calibration" if bit else "test" for g, bit in zip(groups, bits)}, {
        "objective_order": ["class presence in both splits", "sample count distance from 40% calibration",
                            "related-in-test plus independent-in-calibration sample count", "class fraction distance", "sorted group bits"],
        "score": list(key[:-1]), "related_groups": sorted(g for g in groups if related[g]),
    }


def build_priority():
    unfrozen()
    status = validate_labels()
    if not status["human_review_complete"]:
        print("REFUSED:", status["problems"])
        return 1
    rows = read_csv(REVIEW / "human_review_priority.csv")
    counts = Counter(r["scene_group_id"] for r in rows)
    if max(counts.values(), default=0) > 3:
        raise ValueError("Scene cap exceeds 3 across priority primary + challenge")
    primary = [r for r in rows if r["review_label"] in PRIMARY]
    ambiguous = [r for r in rows if r["review_label"] == "AMBIGUOUS"]
    split_groups, objective = choose_split(primary)
    # Assert a scene cannot span physical groups with different assignments.
    scene_split = defaultdict(set)
    for r in primary:
        scene_split[r["scene_group_id"]].add(split_groups[r["split_group_id"]])
    if any(len(s) != 1 for s in scene_split.values()):
        raise ValueError("Scene metadata maps across opposite split groups")
    clips = read_json(REVIEW / "clips/clip_manifest.json")["clips"]
    from build_benchmark import schedule64
    mapping = DERIVED
    gt_sets, public_sets = {}, {}
    MEDIA.mkdir(exist_ok=True)
    for kind, members, prefix in (("primary", primary, "TRIAGE"), ("ambiguous", ambiguous, "CHALLENGE")):
        order = sorted(members, key=lambda r: r["candidate_id"])
        random.Random(SEED).shuffle(order)
        gt_sets[kind], public_sets[kind] = [], []
        for index, r in enumerate(order, 1):
            cid, tid = r["candidate_id"], f"{prefix}_{index:03d}"
            clip = clips[cid]
            source = (BENCH / r["review_clip"]).resolve()
            if BENCH.resolve() not in source.parents:
                raise ValueError("Review media path leaves benchmark")
            if sha256(source) != clip["clip_sha256"]:
                raise ValueError(f"review media hash drift: {cid}")
            destination = MEDIA / f"{tid.lower()}.mp4"
            shutil.copyfile(source, destination)
            if sha256(destination) != clip["clip_sha256"]:
                raise ValueError(f"copied media hash drift: {cid}")
            meta = clip["clip_meta"]
            public_sets[kind].append({"item_id": tid, "task": "single", "cameras": [{
                "camera": "CAM_01", "media": f"media/{tid.lower()}.mp4", "sha256": clip["clip_sha256"],
                "duration_sec": meta["duration"], "fps": round(meta["fps"], 5), "frame_count": meta["frames"],
                "width": meta["width"], "height": meta["height"],
                "frame_schedule_uniform_total64_v1": schedule64(meta["frames"], meta["fps"])}]})
            label = r["review_label"]
            private = {"candidate_id": tid, "review_candidate_id": cid, "review_label": label, "triage_label": label,
                       **mapping[label], "reviewer": r.get("reviewer", ""),
                       "related_to_reasoning_benchmark": r["related_to_reasoning_benchmark"].lower() == "true",
                       "scene_group_id": r["scene_group_id"], "split_group_id": r["split_group_id"],
                       "split": split_groups[r["split_group_id"]] if kind == "primary" else "challenge",
                       "source_video_id": r["source_video_id"], "source_sha256": clip["source_sha256"],
                       "source_window_sec": [clip["actual_start_sec"], clip["actual_end_sec"]]}
            for field in OPTIONAL:
                if r.get(field, "").strip():
                    private[field] = r[field]
            gt_sets[kind].append(private)
    for kind, filename in (("primary", "public_manifest.json"), ("ambiguous", "challenge_public_manifest.json")):
        write_json(BENCH / filename, {"benchmark_version": BENCHMARK_ID,
            "frame_protocol": "uniform_total64_v1 (round-half-up(j*(frame_count-1)/63), j=0..63)",
            "model_input_policy": "pixels, generic camera id, neutral relative times only", "items": public_sets[kind]})
    write_json(PRIVATE / "triage_labels.json", {"benchmark_version": BENCHMARK_ID, "human_gt_policy": POLICY,
        "access": "evaluator only; never model input", "primary": gt_sets["primary"],
        "ambiguous": gt_sets["ambiguous"], "challenge_medium_confidence": [],
        "confidence_policy": "Optional; never used for inclusion, split, or scoring", "confidence_note": CONFIDENCE_NOTE})
    split_manifest = {"human_gt_policy": POLICY, "unit": "split_group_id (stronger than scene; includes shared sites/actors/takes)",
        "calibration_fraction_target": 0.4, "split_groups": split_groups,
        "scene_groups": {g: next(iter(s)) for g, s in sorted(scene_split.items())},
        "primary_candidate_ids": sorted(r["candidate_id"] for r in primary),
        "ambiguous_candidate_ids": sorted(r["candidate_id"] for r in ambiguous),
        "counts": {s: dict(Counter(r["review_label"] for r in primary if split_groups[r["split_group_id"]] == s))
                   for s in ("calibration", "test")}, "split_search": objective,
        "related_to_reasoning_v1_groups_in_test": sorted(g for g,s in split_groups.items() if s == "test" and g in objective["related_groups"]),
        "scene_leakage": 0, "finalized": False,
        "finalize_by": "Approve generated class counts and split manifest, then freeze_benchmark.py (no video re-review)"}
    write_json(MANIFESTS / "split_manifest.json", split_manifest)
    validation = validate_built()
    write_reports()
    print_summary()
    return 0 if validation["ready_to_freeze"] else 1


def validate_built():
    status = validate_labels(persist=False)
    manifest = read_json(MANIFEST)
    rows = read_csv(REVIEW / "human_review_priority.csv")
    byid = {r["candidate_id"]: r for r in rows}
    gt = read_json(PRIVATE / "triage_labels.json")
    primary, challenge = gt["primary"], gt.get("ambiguous", [])
    final = primary + challenge
    split_manifest = read_json(MANIFESTS / "split_manifest.json")
    clips = read_json(REVIEW / "clips/clip_manifest.json")["clips"]
    checks = {}
    def chk(name, ok, detail=""):
        checks[name] = {"pass": bool(ok), "detail": detail}
    chk("priority_labels_valid", status["human_review_complete"], status["problems"])
    chk("benchmark_built", bool(primary))
    final_ids = [r["review_candidate_id"] for r in final]
    item_ids = [r["candidate_id"] for r in final]
    chk("no_duplicate_candidate_ids", len(final_ids)==len(set(final_ids)) and len(item_ids)==len(set(item_ids)))
    chk("no_unreviewed_items_in_benchmark", all(cid in byid and byid[cid].get("review_label") in LABELS for cid in final_ids))
    expected_primary = {r["candidate_id"] for r in rows if r["review_label"] in PRIMARY}
    expected_challenge = {r["candidate_id"] for r in rows if r["review_label"] == "AMBIGUOUS"}
    chk("all_eligible_human_labels_preserved", {r["review_candidate_id"] for r in primary} == expected_primary and
        {r["review_candidate_id"] for r in challenge} == expected_challenge and
        all(r["review_label"] == r["triage_label"] == byid.get(r["review_candidate_id"], {}).get("review_label") for r in final))
    mapping = DERIVED
    chk("registered_binary_mapping_matches_protocol", manifest["derived_mapping"] == DERIVED)
    chk("deterministic_binary_mapping_valid", all(
        r.get("reference_binary") == mapping.get(r["review_label"], {}).get("reference_binary") and
        r.get("must_surface_to_operator") is mapping.get(r["review_label"], {}).get("must_surface_to_operator") for r in final))
    chk("every_primary_sample_has_human_label", all(r["review_label"] in PRIMARY for r in primary))
    chk("ambiguous_excluded_from_primary_metrics", all(r["review_label"] == "AMBIGUOUS" and r["split"] == "challenge" for r in challenge))
    leakage = []
    for field in ("scene_group_id", "split_group_id"):
        groups = defaultdict(set)
        for r in primary:
            groups[r[field]].add(r["split"])
        leakage += [g for g,s in groups.items() if len(s) != 1]
    chk("scene_group_split_leakage_zero", not leakage, leakage)
    chk("split_manifest_matches_gt", all(split_manifest["split_groups"].get(r["split_group_id"]) == r["split"] and
        split_manifest["scene_groups"].get(r["scene_group_id"]) == r["split"] for r in primary))
    counts = Counter(r["scene_group_id"] for r in final)
    chk("max_3_clips_per_scene", max(counts.values(), default=0) <= 3, dict(counts))
    pub_documents = [read_json(BENCH / p) for p in ("public_manifest.json", "challenge_public_manifest.json")]
    root_keys = {"benchmark_version", "frame_protocol", "model_input_policy", "items"}
    item_keys = {"item_id", "task", "cameras"}
    camera_keys = {"camera", "media", "sha256", "duration_sec", "fps", "frame_count", "width", "height", "frame_schedule_uniform_total64_v1"}
    public_ok = all(set(doc) == root_keys and all(set(item) == item_keys and
        all(set(cam) == camera_keys and all(set(frame) == {"j", "frame_index", "t_sec"} for frame in cam["frame_schedule_uniform_total64_v1"])
            for cam in item["cameras"]) for item in doc["items"]) for doc in pub_documents)
    public_text = json.dumps(pub_documents)
    public_ok = public_ok and not any(r["candidate_id"] in public_text or r["source_video_id"] in public_text for r in rows)
    chk("no_private_gt_in_public_manifest", public_ok)
    public_items = [item for doc in pub_documents for item in doc["items"]]
    chk("public_and_private_item_sets_match", {r["candidate_id"] for r in primary} == {i["item_id"] for i in pub_documents[0]["items"]} and
        {r["candidate_id"] for r in challenge} == {i["item_id"] for i in pub_documents[1]["items"]})
    hash_errors, schedules_bad, hashes = [], [], []
    private_by_item = {r["candidate_id"]: r for r in final}
    from build_benchmark import schedule64
    for item in public_items:
        for cam in item["cameras"]:
            path = (BENCH / cam["media"]).resolve()
            label = private_by_item.get(item["item_id"], {})
            original = clips.get(label.get("review_candidate_id"), {})
            if BENCH.resolve() not in path.parents or not path.is_file() or sha256(path) != cam["sha256"] or cam["sha256"] != original.get("clip_sha256"):
                hash_errors.append(item["item_id"])
            hashes.append(cam["sha256"])
            meta = original.get("clip_meta", {})
            if (cam["frame_count"] != meta.get("frames") or not meta.get("fps") or
                    cam["frame_schedule_uniform_total64_v1"] != schedule64(meta["frames"], meta["fps"])):
                schedules_bad.append(item["item_id"])
    chk("media_sha256_matches", not hash_errors, hash_errors)
    chk("no_duplicate_exact_media", len(hashes)==len(set(hashes)))
    chk("frame_schedules_valid", not schedules_bad, schedules_bad)
    source_manifest = read_json(MANIFESTS / "source_manifest.json")
    source_map = {r["source_id"]: r for r in source_manifest["sources"]}
    chk("review_no_reasoning_v1_source_video", all(not source_map[r["source_video_id"]]["used_in_reasoning_v1"] for r in final))
    review_hash_errors = [r["candidate_id"] for r in rows if not (BENCH/r["review_clip"]).is_file() or
        sha256(BENCH/r["review_clip"]) != clips[r["candidate_id"]]["clip_sha256"]]
    chk("review_clip_sha256", not review_hash_errors, review_hash_errors)
    lock = BENCH / "BENCHMARK_LOCK.json"
    if lock.exists():
        bad = [p for p,h in read_json(lock)["sha256"].items() if not (BENCH/p).is_file() or sha256(BENCH/p)!=h]
        chk("benchmark_lock_hashes_valid", not bad, bad)
    else:
        chk("benchmark_lock_hashes_valid", False, "NOT_FROZEN; excluded from technical readiness")
    ready = all(c["pass"] for k,c in checks.items() if lock.exists() or k != "benchmark_lock_hashes_valid")
    result = {"scope": POLICY, "checks": checks, "all_pass": all(c["pass"] for c in checks.values()),
              "ready_to_freeze": ready, "additional_human_review_required": status["additional_human_review_required"]}
    write_json(REPORTS / "validation.json", result)
    return result


def summary_data():
    gt = read_json(PRIVATE / "triage_labels.json")
    primary, challenge = gt["primary"], gt["ambiguous"]
    status = validate_labels(persist=False)
    val = read_json(REPORTS / "validation.json")
    test = [r for r in primary if r["split"] == "test"]
    return {"human_reviewed": status["labelled"], "label_counts": status["label_counts"],
        "primary_size": len(primary), "calibration": sum(r["split"]=="calibration" for r in primary),
        "test": len(test), "challenge": len(challenge),
        "primary_scenes": len({r["scene_group_id"] for r in primary}),
        "all_scenes": len({r["scene_group_id"] for r in primary+challenge}),
        "independent_test_scenes": sorted({r["scene_group_id"] for r in test if not r["related_to_reasoning_benchmark"]}),
        "related_scenes": sorted({r["scene_group_id"] for r in primary+challenge if r["related_to_reasoning_benchmark"]}),
        "split_counts": {s: dict(Counter(r["review_label"] for r in primary if r["split"]==s)) for s in ("calibration","test")},
        "scene_leakage": 0 if val["checks"]["scene_group_split_leakage_zero"]["pass"] else "FAIL",
        "auxiliary_missing": status["auxiliary_missing"], "ready_to_freeze": val["ready_to_freeze"],
        "additional_human_review_required": status["additional_human_review_required"]}


def print_summary():
    data = summary_data()
    print("CLASS COUNTS", data["label_counts"])
    print("SPLIT", data["split_counts"])
    print("SCENE LEAKAGE", data["scene_leakage"])
    print("INDEPENDENT TEST SCENES", data["independent_test_scenes"])
    print("READY TO FREEZE", "YES" if data["ready_to_freeze"] else "NO")


def write_reports():
    data = summary_data()
    gt = read_json(PRIVATE / "triage_labels.json")
    split = read_json(MANIFESTS / "split_manifest.json")
    priority = read_csv(REVIEW / "human_review_priority.csv")
    manifest = read_json(MANIFEST)
    confidence_note = CONFIDENCE_NOTE
    overview = ("# PRIORITY HUMAN GT FINALIZATION\n\n"
        f"Human reviewed: {data['human_reviewed']} / {manifest['priority_selected']} priority\n\n"
        "Primary:\n" + "\n".join(f"- {label}: {data['label_counts'].get(label,0)}" for label in PRIMARY) +
        f"\n\nChallenge:\n- AMBIGUOUS: {data['challenge']}\n\nAdditional human review required: NO\n\n"
        "Only candidate_id and review_label are required human GT. Auxiliary fields are OPTIONAL / NOT USED FOR SCORING. "
        "No human label was modified, inferred or generated; 72 unreviewed labels remain blank. "
        "reviewer_01 was filled only where blank, with backups, following the user's confirmed reviewer provenance.\n\n"
        f"{confidence_note}\n\nNo confidence, summary, subtype or item timestamp was fabricated. "
        "Existing optional values were retained; only populated optional fields are exported to private GT.\n\n"
        f"Batch provenance timestamp: {manifest['annotation_batch_timestamp']} "
        "(priority CSV modification time before metadata update, not per-candidate time).\n\n"
        "## Class counts and split for approval\n\n| Split | CLEAR_NORMAL | HARD_NEGATIVE_NORMAL | ANCHORED_DANGER | Total |\n"
        "|---|---:|---:|---:|---:|\n")
    for s, counts in data["split_counts"].items():
        overview += f"| {s} | {counts.get('CLEAR_NORMAL',0)} | {counts.get('HARD_NEGATIVE_NORMAL',0)} | {counts.get('ANCHORED_DANGER',0)} | {sum(counts.values())} |\n"
    overview += (f"\nPrimary: {data['primary_size']}; challenge: {data['challenge']}; primary scenes: {data['primary_scenes']}; "
        f"all priority scenes: {data['all_scenes']}; scene leakage: {data['scene_leakage']}.\n\n"
        f"Independent test scenes ({len(data['independent_test_scenes'])}): {', '.join(data['independent_test_scenes'])}.\n\n"
        f"Related scenes ({len(data['related_scenes'])}): {', '.join(data['related_scenes'])}.\n\n"
        "## Split policy and trade-offs\n\n"
        "Exhaustive deterministic split search over existing split_group_id groups, which keeps shared site/actor/take "
        "groups together and guarantees scene separation. Priority order: all classes present in both splits, "
        "closest sample count to 40% calibration, related scenes in calibration and independent scenes in test, "
        "class fraction balance, sorted group tie break. Human confidence is never used.\n\n"
        f"Selected split groups: `{json.dumps(split['split_groups'], sort_keys=True)}`.\n\n"
        f"Related groups in test: {split['related_to_reasoning_v1_groups_in_test']}. "
        "All 16 independent primary candidates can be kept in test, but that alone yields only 43.2% of primary. "
        "Reaching about 60% test while keeping each physical group intact requires related candidates in test; "
        "these are flagged. Test is not wholly independent of reasoning-v1.\n\n"
        "## Auxiliary warnings only\n\n" + "\n".join(f"- {k}: {v}" for k,v in data['auxiliary_missing'].items()) +
        "\n\n## Validation and freeze readiness\n\n"
        f"Technical readiness: {'YES' if data['ready_to_freeze'] else 'NO'}. "
        "See validation.json for label validity, ID membership, label snapshot integrity, media hashes, "
        "public/private separation, derived mapping and scene cap. Missing auxiliary data does not block freeze.\n\n"
        "Not frozen yet. User approval concerns the generated class counts and split manifest only; "
        "no additional video review is required. Preserve the existing approval-before-freeze principle.\n\n"
        "After class/split approval, run freeze_benchmark.py, then frozen P1 + frozen P4 once, "
        "then Cascade Analysis v1. No P1/P4 output was accessed during this finalization.\n")
    (REPORTS / "priority_gt_report.md").write_text(overview, encoding="utf-8")
    (REPORTS / "dataset_report.md").write_text(overview.replace("# PRIORITY HUMAN GT FINALIZATION", "# 477-TRIAGE-NORMAL-V1 DATASET REPORT") +
        "\n## Files\n\npublic_manifest.json contains only 37 primary model inputs. challenge_public_manifest.json "
        "contains only 6 ambiguous model inputs and must not enter the primary denominator. "
        "private_ground_truth/triage_labels.json holds the human GT for both. "
        "review/priority_review_manifest.json registers the 43 human-reviewed IDs and label digest.\n", encoding="utf-8")
    lines = ["# Diversity report — priority human GT\n", f"Primary: {data['primary_size']}; challenge: {data['challenge']}. "
             "Scene cap <=3 checked across both sets.\n", "| Scene | Primary | Challenge | Primary split | Related |",
             "|---|---:|---:|---|---|"]
    for scene in sorted({r["scene_group_id"] for r in priority}):
        p = [r for r in gt["primary"] if r["scene_group_id"] == scene]
        c = [r for r in gt["ambiguous"] if r["scene_group_id"] == scene]
        lines.append(f"| {scene} | {len(p)} | {len(c)} | {p[0]['split'] if p else 'challenge only'} | {any(r['related_to_reasoning_benchmark'] for r in p+c)} |")
    hints = Counter(h for r in priority for h in r["discovery_hints"].split("|") if h)
    lines += ["\nDiscovery hint coverage (generic proxies, not human subtype judgments):\n"]
    lines += [f"- {k}: {v}" for k,v in sorted(hints.items())]
    lines += ["\nLocal source diversity is limited to 18 scenes, 8 physical groups and two datasets. "
              "Repeated sites/actors are grouped together. Explicit walking/contact/entry subtypes were not required; "
              "no missing subtype was inferred.\n", confidence_note]
    (REPORTS / "diversity_report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (REPORTS / "leakage_report.md").write_text("# Priority benchmark leakage / overlap\n\n"
        f"Calibration/test scene and physical-group leakage: {data['scene_leakage']}.\n\n"
        "Source-video overlap with reasoning-v1: 0, verified against source_manifest.json. "
        "Related site/actor groups are retained as metadata and are not treated as independent.\n\n"
        f"Independent test scenes: {data['independent_test_scenes']}.\n\n"
        f"Related groups in test: {split['related_to_reasoning_v1_groups_in_test']}.\n\n"
        "No model predictions, cascade thresholds or evaluation outputs were read. "
        "Public primary/challenge manifests use neutral IDs and only camera/media/timing information; "
        "human labels, source labels, scene IDs and reviewer metadata remain private.\n", encoding="utf-8")
    (REPORTS / "proposed_selection.md").write_text(overview, encoding="utf-8")
    write_json(REPORTS / "priority_gt_summary.json", data)
