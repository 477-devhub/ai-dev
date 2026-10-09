"""Step 2 — one row per routed assessment: reference tier, frozen P1 signals, generic
representation-sensitive flags (from the frozen compact state P1 actually saw), the frozen
P4 decision, and P2/P3 probabilities as supplementary comparators.

Writes analysis/stage1_assessments_base.csv (signals only; routing is added by simulate_cascade.py).
"""
from __future__ import annotations

import json

from _common import ANALYSIS, config, per_assessment, read_json, write_csv


def flags_for(state: dict, key: str, task: str, d: dict) -> dict:
    cams = [c for c in state["cameras"] if key == "_" or c["camera"] == key]
    boundary = any(
        c["scene"].get("boundary_semantics_available") is False
        and (c["scene"].get("person_entry_observed") or c["scene"].get("large_spatial_transition_observed")
             or bool(c["scene"].get("boundary_crossing")))
        for c in cams
    )
    has_interaction = any(len(c.get("interactions") or []) > 0 for c in cams)
    p, cat = d["p_incident"], d["category"]
    disagree = (p < 0.5 and cat != "no_clear_incident") or (p >= 0.5 and cat == "no_clear_incident") or cat == "uncertain"
    return {
        "F_boundary": boundary,
        "F_multicam": task == "multi_camera",
        "F_interaction_lowconf": has_interaction and d["category_confidence"] < 0.70,
        "F_disagree": disagree,
        "F_lowconf": d["confidence"] < 0.60 or d["category_confidence"] < 0.50,
        "F_refusal": len(d["refused_questions"]) > 0,
        "has_interaction_record": has_interaction,
        "cv_reliability_labels": "|".join(c["quality"]["cv_reliability_label"] for c in cams),
    }


def main() -> None:
    cfg = config()
    inp = cfg["inputs"]
    inv = json.load(open(ANALYSIS / "existing_results_inventory.json", encoding="utf-8"))
    runs = {p: read_json(inp["run_summaries"][p]) for p in ["P1", "P2", "P3", "P4"]}

    rows = []
    for a in inv["assessments"]:
        item, key = a["item"], a["decision_key"]
        state = read_json(f"{inp['p1_compact_state_dir']}/{item}.json")
        dec = {p: per_assessment(runs[p]["items"][item]["decision_summary"]) for p in runs}
        d1, d4 = dec["P1"][key], dec["P4"][key]
        fl = flags_for(state, key, a["task"], d1)
        rows.append({
            "assessment": a["assessment"], "item": item, "task": a["task"], "asset": a["asset"],
            "reference_tier": a["tier"], "reference_provenance": a["tier_provenance"],
            "p1_p_incident": d1["p_incident"], "p1_category": d1["category"],
            "p1_category_confidence": d1["category_confidence"], "p1_confidence": d1["confidence"],
            "p1_severity": d1["risk"]["severity"], "p1_imminence": d1["risk"]["imminence"],
            "p1_exposure": d1["risk"]["exposure"], "p1_persistence": d1["risk"]["persistence"],
            "p1_priority": d1["priority_score"], "p1_p_human_review": d1["p_human_review"],
            "p1_human_review": d1["human_review_required"], "p1_refused": len(d1["refused_questions"]),
            **fl,
            "rep_sensitive_any": any(fl[k] for k in ["F_boundary", "F_multicam", "F_interaction_lowconf", "F_disagree", "F_lowconf", "F_refusal"]),
            "rep_sensitive_noboundary": any(fl[k] for k in ["F_multicam", "F_interaction_lowconf", "F_disagree", "F_lowconf", "F_refusal"]),
            "p4_p_incident": d4["p_incident"], "p4_category": d4["category"], "p4_is_incident": d4["is_incident"],
            "p4_decision": "DANGER" if d4["is_incident"] else "NORMAL",
            "p2_p_incident": dec["P2"][key]["p_incident"], "p3_p_incident": dec["P3"][key]["p_incident"],
            "p1_item_cost_usd": runs["P1"]["items"][item]["external_api_cost_usd"],
            "p4_item_cost_usd": runs["P4"]["items"][item]["external_api_cost_usd"],
        })
    write_csv("stage1_assessments_base.csv", rows)
    for r in rows:
        print(f"{r['assessment']:<15} {r['reference_tier']:<29} p1={r['p1_p_incident']:.2f} {r['p1_category']:<33} "
              f"conf={r['p1_confidence']:.2f} catc={r['p1_category_confidence']:.2f} "
              f"B={int(r['F_boundary'])} M={int(r['F_multicam'])} I={int(r['F_interaction_lowconf'])} "
              f"D={int(r['F_disagree'])} L={int(r['F_lowconf'])} p4={r['p4_p_incident']:.2f}")


if __name__ == "__main__":
    main()
