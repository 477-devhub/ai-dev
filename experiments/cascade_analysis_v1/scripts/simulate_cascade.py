"""Step 4 — per-assessment retrospective cascade routing for named candidate policies.

Candidates are chosen by principle (see cascade_report.md §5), not by in-sample optimum:
  safety_first     P3_safety_noboundary, T_normal 0.10, T_danger 0.90
  balanced         P3_safety_noboundary, T_normal 0.15, T_danger 0.75
  lexbest_overfit  P2_prob_conf C 0.70, T_normal 0.30, T_danger 0.55  (in-sample optimum; shown to be rejected)
References:
  all_to_p4        every candidate to P4 (T_normal 0, T_danger off)
  p1_binary_0.5    current single-stage P1 (p >= 0.5 -> alert, else suppress)
  p1_human_review  route on P1 human_review flag (true -> P4)

Writes analysis/cascade_simulation.csv (long form), analysis/cascade_summary.csv,
and analysis/stage1_assessments.csv (base signals + routing for the two proposed candidates).
"""
from __future__ import annotations

from _common import config, load_analysis_csv, read_json, write_csv
import sweep_stage1_thresholds as sw

CANDIDATES = [
    ("safety_first", "P3_safety_noboundary", 0.10, 0.90, None),
    ("balanced", "P3_safety_noboundary", 0.15, 0.75, None),
    ("lexbest_overfit", "P2_prob_conf", 0.30, 0.55, 0.70),
    ("all_to_p4", "P1_prob", 0.0, 1.01, None),
    ("p1_binary_0.5", "P1_prob", 0.4999, 0.5, None),
    ("p1_human_review", "human_review", None, None, None),
]


def main() -> None:
    cfg = config()
    sw.DANGER_SETS = {k: v for k, v in cfg["danger_sets"].items() if not k.startswith("_")}
    rows = load_analysis_csv("stage1_assessments_base.csv")
    runs = {p: read_json(cfg["inputs"]["run_summaries"][p])["items"] for p in ["P1", "P4"]}
    p1_lat = {k: v["latency"]["cached_state_pipeline_latency_ms"] for k, v in runs["P1"].items()}
    p4_lat = {k: v["latency"]["full_pipeline_ms"] for k, v in runs["P4"].items()}
    n_items = len({r["item"] for r in rows})

    long_rows, summary = [], []
    routing_cols = {}
    for name, policy, tn, td, cn in CANDIDATES:
        if policy == "human_review":
            routes = {r["assessment"]: ("SUSPICIOUS" if r["p1_human_review"] in sw.TRUE else "NORMAL") for r in rows}
        else:
            routes = {r["assessment"]: sw.route(r, policy, tn, td, cn) for r in rows}
        m = sw.evaluate(rows, routes, p4_lat, n_items)
        summary.append({"candidate": name, "policy": policy, "T_normal": tn, "T_danger": td, "C_normal": cn, **m})
        for r in rows:
            s1 = routes[r["assessment"]]
            final = s1 if s1 != "SUSPICIOUS" else r["p4_decision"]
            tta = None
            if final == "DANGER":
                tta = p1_lat[r["item"]] / 1000 + (p4_lat[r["item"]] / 1000 if s1 == "SUSPICIOUS" else 0)
            long_rows.append({
                "candidate": name, "assessment": r["assessment"], "reference_tier": r["reference_tier"],
                "p1_p_incident": r["p1_p_incident"], "p1_category": r["p1_category"], "p1_confidence": r["p1_confidence"],
                "rep_sensitive_noboundary": r["rep_sensitive_noboundary"],
                "stage1": s1,
                "p4_decision_if_escalated": r["p4_decision"] if s1 == "SUSPICIOUS" else "",
                "p4_category_if_escalated": r["p4_category"] if s1 == "SUSPICIOUS" else "",
                "final": final,
                "category_shown_to_operator": (r["p1_category"] if s1 == "DANGER" else r["p4_category"] if final == "DANGER" else ""),
                "time_to_attention_s_observed": "" if tta is None else round(tta, 1),
            })
            if name in ("safety_first", "balanced"):
                routing_cols.setdefault(r["assessment"], {})[f"stage1_{name}"] = s1
                routing_cols[r["assessment"]][f"p4_{name}"] = r["p4_decision"] if s1 == "SUSPICIOUS" else ""
                routing_cols[r["assessment"]][f"final_{name}"] = final

    write_csv("cascade_simulation.csv", long_rows)
    write_csv("cascade_summary.csv", summary)
    write_csv("stage1_assessments.csv", [{**r, **routing_cols[r["assessment"]]} for r in rows])
    for s in summary:
        print(f"{s['candidate']:<16} N/S/D={s['stage1_normal']}/{s['stage1_suspicious']}/{s['stage1_danger']} "
              f"D->N anchor/hv/cons={s['danger_to_normal_anchor']}/{s['danger_to_normal_hv']}/{s['danger_to_normal_conservative']} "
              f"P4 A/B={s['p4_calls_policyA']}/{s['p4_calls_policyB']} queue={s['human_queue']} "
              f"cost A/B={s['cost_per_candidate_policyA']}/{s['cost_per_candidate_policyB']} amb={s['ambiguous_routes']} "
              f"wait={s['conservative_dangers_waiting_on_p4']}@{s['median_p4_wait_s_for_those']}s")


if __name__ == "__main__":
    main()
