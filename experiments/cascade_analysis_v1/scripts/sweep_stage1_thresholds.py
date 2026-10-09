"""Step 3 — grid sweep of Stage-1 3-way triage policies over the frozen assessments.

Writes analysis/threshold_sweep.csv (all policies x thresholds, Pareto + lexicographic marks)
and analysis/comparator_sweep.csv (P2 / P3 probabilities used as the Stage-1 score, policy 1 only).
"""
from __future__ import annotations

import statistics
from collections import defaultdict

from _common import config, load_analysis_csv, read_json, write_csv

TRUE = {"True", "true", "1"}
DANGER_SETS = None  # filled from config


def route(row: dict, policy: str, tn: float, td: float, cn: float | None, score_col: str = "p1_p_incident") -> str:
    p = float(row[score_col])
    if p >= td:
        return "DANGER"
    gate_ok = True
    if policy == "P2_prob_conf":
        gate_ok = float(row["p1_confidence"]) >= cn
    elif policy == "P3_safety_full":
        gate_ok = row["rep_sensitive_any"] not in TRUE
    elif policy == "P3_safety_noboundary":
        gate_ok = row["rep_sensitive_noboundary"] not in TRUE
    if p <= tn and gate_ok:
        return "NORMAL"
    return "SUSPICIOUS"


def evaluate(rows: list[dict], routes: dict[str, str], p4_latency_ms: dict[str, float], n_items: int) -> dict:
    sets = {name: {r["assessment"] for r in rows if r["reference_tier"] in tiers} for name, tiers in DANGER_SETS.items()}
    final = {}
    for r in rows:
        s = routes[r["assessment"]]
        final[r["assessment"]] = s if s != "SUSPICIOUS" else r["p4_decision"]
    m = {
        "stage1_normal": sum(v == "NORMAL" for v in routes.values()),
        "stage1_danger": sum(v == "DANGER" for v in routes.values()),
        "stage1_suspicious": sum(v == "SUSPICIOUS" for v in routes.values()),
    }
    items_A = {r["item"] for r in rows if routes[r["assessment"]] == "SUSPICIOUS"}
    items_B = {r["item"] for r in rows if routes[r["assessment"]] != "NORMAL"}
    m["p4_calls_policyA"], m["p4_calls_policyB"] = len(items_A), len(items_B)
    m["escalation_rate_policyA"] = round(len(items_A) / n_items, 4)
    m["escalation_rate_policyB"] = round(len(items_B) / n_items, 4)
    m["suspicious_rate_assessments"] = round(m["stage1_suspicious"] / len(rows), 4)
    for name, S in sets.items():
        tag = name.replace("D_", "")
        m[f"danger_to_normal_{tag}"] = sum(routes[a] == "NORMAL" for a in S)
        m[f"danger_direct_{tag}"] = sum(routes[a] == "DANGER" for a in S)
        m[f"danger_recovered_p4_{tag}"] = sum(routes[a] == "SUSPICIOUS" and final[a] == "DANGER" for a in S)
        m[f"final_miss_{tag}"] = sum(final[a] == "NORMAL" for a in S)
        m[f"n_{tag}"] = len(S)
    amb = [r["assessment"] for r in rows if r["reference_tier"] == "ambiguous"]
    m["ambiguous_routes"] = ";".join(f"{a}:{routes[a]}->{final[a]}" for a in amb)
    m["human_queue"] = sum(v == "DANGER" for v in final.values())
    m["operator_review_reduction_diagnostic"] = round(1 - m["human_queue"] / len(rows), 4)
    by_item = defaultdict(float)
    for r in rows:
        by_item[r["item"]] = (float(r["p1_item_cost_usd"]), float(r["p4_item_cost_usd"]))
    p1_total = sum(v[0] for v in by_item.values())
    m["cost_per_candidate_policyA"] = round((p1_total + sum(by_item[i][1] for i in items_A)) / n_items, 6)
    m["cost_per_candidate_policyB"] = round((p1_total + sum(by_item[i][1] for i in items_B)) / n_items, 6)
    delayed = [p4_latency_ms[r["item"]] for r in rows
               if r["assessment"] in sets["D_conservative"] and routes[r["assessment"]] == "SUSPICIOUS"]
    m["conservative_dangers_waiting_on_p4"] = len(delayed)
    m["median_p4_wait_s_for_those"] = round(statistics.median(delayed) / 1000, 1) if delayed else 0.0
    return m


def pareto_marks(results: list[dict], keys: list[str]) -> None:
    vecs = [tuple(r[k] for k in keys) for r in results]
    for i, r in enumerate(results):
        v = vecs[i]
        r["pareto"] = not any(all(w[j] <= v[j] for j in range(len(keys))) and w != v for w in vecs)
    order = sorted(range(len(results)), key=lambda i: vecs[i])
    best = vecs[order[0]]
    for i, r in enumerate(results):
        r["lexicographic_best"] = vecs[i] == best


def main() -> None:
    global DANGER_SETS
    cfg = config()
    DANGER_SETS = {k: v for k, v in cfg["danger_sets"].items() if not k.startswith("_")}
    rows = load_analysis_csv("stage1_assessments_base.csv")
    p4 = read_json(cfg["inputs"]["run_summaries"]["P4"])["items"]
    p4_lat = {k: v["latency"]["full_pipeline_ms"] for k, v in p4.items()}
    n_items = len({r["item"] for r in rows})
    g = cfg["grid"]

    results = []
    for policy in ["P1_prob", "P2_prob_conf", "P3_safety_full", "P3_safety_noboundary"]:
        for tn in g["T_normal"]:
            for td in g["T_danger"]:
                for cn in (g["C_normal"] if policy == "P2_prob_conf" else [None]):
                    routes = {r["assessment"]: route(r, policy, tn, td, cn) for r in rows}
                    m = evaluate(rows, routes, p4_lat, n_items)
                    notes = []
                    if m["stage1_normal"] == 0:
                        notes.append("no Stage-1 NORMAL on this positive-only set; suppression benefit unmeasurable")
                    if td > 1:
                        notes.append("T_danger disabled (all non-NORMAL -> P4)")
                    results.append({"policy": policy, "T_normal": tn, "T_danger": td,
                                    "C_normal": "" if cn is None else cn, **m, "notes": "; ".join(notes)})
    keys = cfg["lexicographic_objective"]
    pareto_marks(results, keys)
    write_csv("threshold_sweep.csv", results)

    # supplementary: P2 / P3 probability as the Stage-1 score (policy 1 only)
    comp = []
    for model, col in [("P1", "p1_p_incident"), ("P2", "p2_p_incident"), ("P3", "p3_p_incident")]:
        for tn in g["T_normal"]:
            routes = {r["assessment"]: route(r, "P1_prob", tn, 1.01, None, col) for r in rows}
            m = evaluate(rows, routes, p4_lat, n_items)
            comp.append({"stage1_model": model, "T_normal": tn, "stage1_normal": m["stage1_normal"],
                         "danger_to_normal_anchor": m["danger_to_normal_anchor"],
                         "danger_to_normal_hv": m["danger_to_normal_hv"],
                         "danger_to_normal_conservative": m["danger_to_normal_conservative"],
                         "ambiguous_routes": m["ambiguous_routes"]})
    write_csv("comparator_sweep.csv", comp)

    print(f"rows={len(results)} pareto={sum(r['pareto'] for r in results)} lexbest={sum(r['lexicographic_best'] for r in results)}")
    for policy in ["P1_prob", "P2_prob_conf", "P3_safety_full", "P3_safety_noboundary"]:
        safe = [r for r in results if r["policy"] == policy and r["danger_to_normal_conservative"] == 0]
        print(policy, "max safe T_normal (conservative set):", max(r["T_normal"] for r in safe),
              "| any anchor D->N in grid:", any(r["danger_to_normal_anchor"] for r in results if r["policy"] == policy))
    for r in results:
        if r["lexicographic_best"]:
            print("LEX", r["policy"], r["T_normal"], r["T_danger"], r["C_normal"], r["p4_calls_policyA"], r["cost_per_candidate_policyA"])


if __name__ == "__main__":
    main()
