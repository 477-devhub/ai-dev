"""Step 1 — inventory the frozen P0-P4 artifacts, reference tiers and normal-data availability.

Read-only. Writes analysis/existing_results_inventory.json and analysis/input_manifest.json.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from _common import ROOT, config, per_assessment, read_csv, read_json, read_log, sha256, write_json

PIPELINES = ["P1", "P2", "P3", "P4"]


def assessment_ids(scen_item: dict) -> list[tuple[str, str, str]]:
    """(assessment_id, decision_key, asset) per routed unit."""
    item, task, cams = scen_item["item_id"], scen_item["task"], scen_item["cameras"]
    if task == "attention":
        return [(f"{item}/{c['camera']}", c["camera"], c["asset"]) for c in cams]
    assets = "+".join(c["asset"] for c in cams)
    return [(item, "_", assets)]


def reference_tier(gt_item: dict, camera: str | None) -> tuple[str, str]:
    node = gt_item["per_camera"][camera] if camera and "per_camera" in gt_item else gt_item
    if gt_item.get("ambiguous_case"):
        return "ambiguous", "ambiguous_case=true"
    anchor = node.get("incident_presence_anchor", {})
    if anchor.get("value") is True:
        return "anchored_danger", anchor.get("provenance", "")
    hvo = node.get("human_verified_observation") or {}
    if any(v is True for v in hvo.values()):
        return "hv_event_unanchored", "human_verified_observation: " + ", ".join(k for k, v in hvo.items() if v is True)
    return "diagnostic_source_label_only", f"source label '{node.get('source_label', gt_item.get('source_label'))}' only; anchor not_scored"


def main() -> None:
    cfg = config()
    inp = cfg["inputs"]
    gt = read_json(inp["ground_truth"])["items"]
    scen = read_json(inp["scenarios"])["items"]
    runs = {p: read_json(inp["run_summaries"][p]) for p in PIPELINES}

    # ---- assessments + reference tiers -------------------------------------------------
    rows, asset_to_tier = [], {}
    for it in scen:
        for aid, key, asset in assessment_ids(it):
            cam = key if key != "_" else None
            tier, prov = reference_tier(gt[it["item_id"]], cam)
            rows.append({"assessment": aid, "item": it["item_id"], "task": it["task"], "decision_key": key,
                         "asset": asset, "tier": tier, "tier_provenance": prov})
            if tier in ("anchored_danger", "hv_event_unanchored"):
                asset_to_tier.setdefault(asset, (tier, aid))
    # identical-asset inheritance (e.g. ITEM_04/CAM_03 is ASSET_02 = ITEM_02)
    for r in rows:
        if r["tier"] == "diagnostic_source_label_only" and r["asset"] in asset_to_tier:
            t, src = asset_to_tier[r["asset"]]
            if t == "hv_event_unanchored":
                r["tier"] = t
                r["tier_provenance"] = f"inherited: byte-identical asset {r['asset']} of {src} (GT itself marks not_scored)"

    tier_counts = Counter(r["tier"] for r in rows)
    unique_assets = sorted({a for r in rows for a in r["asset"].split("+")})
    anchored_assets = sorted({r["asset"] for r in rows if r["tier"] == "anchored_danger"})

    # ---- P1 signal inventory -----------------------------------------------------------
    p1 = runs["P1"]["items"]
    sig = defaultdict(list)
    for it in scen:
        dec = per_assessment(p1[it["item_id"]]["decision_summary"])
        for k, d in dec.items():
            sig["p_incident"].append(d["p_incident"])
            sig["category_confidence"].append(d["category_confidence"])
            sig["confidence"].append(d["confidence"])
            sig["p_human_review"].append(d["p_human_review"])
            sig["human_review_required"].append(d["human_review_required"])
            sig["priority_score"].append(d["priority_score"])
            sig["category"].append(d["category"])
            sig["refused"].append(len(d["refused_questions"]))
    signal_summary = {
        k: ({"min": min(v), "max": max(v), "median": statistics.median(v)}
            if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v) else dict(Counter(map(str, v))))
        for k, v in sig.items()
    }

    # ---- cost + latency (from frozen run summaries) -----------------------------------
    cost, latency = {}, {}
    for p in PIPELINES:
        items = runs[p]["items"]
        c = {k: v["external_api_cost_usd"] for k, v in items.items()}
        cost[p] = {"per_item": c, "mean_per_candidate": sum(c.values()) / len(c), "total": sum(c.values())}
        lat = []
        for v in items.values():
            L = v.get("latency", {})
            ms = L.get("full_pipeline_ms") or L.get("cached_state_pipeline_latency_ms") or L.get("cached_state_pipeline_ms")
            if ms is not None:
                lat.append(ms)
        latency[p] = {"median_ms": statistics.median(lat) if lat else None,
                      "definition": next(iter(items.values())).get("latency", {}).get("definition")}

    # ---- frozen-results integrity check (manifests that list sha256) ------------------
    integrity = {}
    for p, rel in inp["frozen_result_manifests"].items():
        man = read_json(rel)
        ok = {f: sha256(ROOT / "benchmark_v1" / f) == h for f, h in man["sha256"].items() if (ROOT / "benchmark_v1" / f).exists()}
        integrity[p] = {"files_checked": len(ok), "all_match": all(ok.values()), "mismatch": [f for f, v in ok.items() if not v]}

    # ---- normal / benign data search ---------------------------------------------------
    ns = cfg["normal_source_scan"]
    inv = read_csv(inp["dataset_inventory"])
    by_type = defaultdict(lambda: {"videos": 0, "videos_with_window": 0, "windows": 0, "source_ids": set(), "local_files": 0})
    for r in inv:
        try:
            start = float(r["event_start"])
        except (TypeError, ValueError):
            continue
        b = by_type[r["event_type"]]
        b["videos"] += 1
        n = max(0, math.floor((start - ns["pre_event_guard_sec"]) / ns["window_sec"]))
        if n:
            b["videos_with_window"] += 1
            b["windows"] += n
            b["source_ids"].add(r["filename"].split("_cam")[0])
        vp = r["video_path"]
        if "::" not in vp and Path(vp).exists():
            b["local_files"] += 1
    normal_scan = {
        "explicit_normal_class_in_project": False,
        "searched": ["downloads/fight (AI Hub 171 fight)", "data/recovered (AI Hub 171 swoon, trespass)",
                     "downloads/multiview_fight (AI Hub 71953 fight, 5 events x 2 views)",
                     "evaluation_selection/*", "organized_data/*", "benchmark_v1 (read only)"],
        "finding": "All downloaded sources are abnormal-scenario categories (fight / swoon / trespass). No normal/benign class was downloaded.",
        "pre_event_windows": {k: {**{kk: vv for kk, vv in v.items() if kk != "source_ids"}, "unique_source_ids": len(v["source_ids"])}
                              for k, v in by_type.items()},
        "pre_event_rule": f"floor((event_start - {ns['pre_event_guard_sec']}s guard) / {ns['window_sec']}s) per video",
        "caveat": ns["note"],
    }

    out = {
        "analysis_version": cfg["analysis_version"],
        "api_calls_made": 0,
        "assessments": rows,
        "assessment_count": len(rows),
        "item_count": len(scen),
        "tier_counts": dict(tier_counts),
        "clear_normal_negatives": 0,
        "hard_normal_negatives": 0,
        "every_assessment_source_positive": True,
        "unique_media_assets": unique_assets,
        "anchored_danger_unique_assets": anchored_assets,
        "independence_note": "ITEM_04/CAM_01 reuses ASSET_01 (ITEM_01) and ITEM_04/CAM_03 reuses ASSET_02 (ITEM_02); ITEM_05/06/07 are views of one SET05 incident. 9 assessments = 6 unique clips = 5 unique incidents; the 2 fall anchors are ONE video sampled two ways.",
        "p1_signal_summary": signal_summary,
        "cost": cost,
        "latency": latency,
        "frozen_result_integrity": integrity,
        "normal_data_scan": normal_scan,
    }
    write_json("existing_results_inventory.json", out)
    files = read_log()
    # every frozen artifact the later steps read, plus the frozen per-pipeline results and benchmark lock
    for pattern in ["experiments/p1_decisions/compact_states/*.json", "experiments/p1_decisions/raw_api/ITEM_*.json",
                    "experiments/common_adapter_v2/normalized/p1/*.json", "experiments/p4_gpt61_sol_vision/raw_api/ITEM_*.json",
                    "benchmark_v1/results/p*/*.json", "benchmark_v1/BENCHMARK_LOCK.json"]:
        for p in sorted(ROOT.glob(pattern)):
            files[str(p.relative_to(ROOT)).replace("\\", "/")] = sha256(p)
    write_json("input_manifest.json", {"note": "sha256 of frozen inputs at analysis start; re-checked by build_report.py", "files": files})
    print(f"assessments={len(rows)} tiers={dict(tier_counts)} unique_assets={len(unique_assets)}")
    print("P1 mean cost", cost["P1"]["mean_per_candidate"], "P4 mean cost", cost["P4"]["mean_per_candidate"])
    print("integrity", integrity)
    print("normal scan", normal_scan["pre_event_windows"])


if __name__ == "__main__":
    main()
