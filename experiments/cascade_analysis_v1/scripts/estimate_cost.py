"""Step 5 — API cost scenarios from frozen observed P1 / P4 costs.

expected_cost_per_candidate = P1 + escalation_rate * P4   (Policy A; for Policy B, escalation_rate
already includes direct-DANGER background verification).
Volumes are scenario inputs, not a measured arrival rate.

Writes analysis/cost_scenarios.csv (long form, column `table` distinguishes sections).
"""
from __future__ import annotations

import json

from _common import ANALYSIS, config, load_analysis_csv, write_csv

BUDGET_EXAMPLES = [50, 100, 300, 1000, 3000]  # USD / month, illustrative inputs only — not an affordability judgement


def main() -> None:
    cfg = config()
    cs = cfg["cost_scenarios"]
    inv = json.load(open(ANALYSIS / "existing_results_inventory.json", encoding="utf-8"))
    p1 = inv["cost"]["P1"]["mean_per_candidate"]
    p4 = inv["cost"]["P4"]["mean_per_candidate"]
    single = [i for i, a in ((r["item"], r["task"]) for r in inv["assessments"]) if a == "single"]
    p1_single = sum(inv["cost"]["P1"]["per_item"][i] for i in single) / len(single)
    p4_single = sum(inv["cost"]["P4"]["per_item"][i] for i in single) / len(single)
    days = cs["days_per_month"]

    out = []
    for unit, c1, c4 in [("observed_mean_7_items", p1, p4), ("single_camera_items_only", p1_single, p4_single)]:
        for r in cs["escalation_rates"]:
            per = c1 + r * c4
            row = {"table": "by_escalation_rate", "cost_unit": unit, "escalation_rate": r,
                   "p1_usd": round(c1, 7), "p4_usd": round(c4, 6), "expected_cost_per_candidate_usd": round(per, 6)}
            for n in cs["candidates_per_day"]:
                row[f"daily_usd_{n}_per_day"] = round(per * n, 2)
                row[f"monthly_usd_{n}_per_day"] = round(per * n * days, 2)
            out.append(row)

    # in-sample routed rates of named candidates (diagnostic only — positive-only benchmark)
    for s in load_analysis_csv("cascade_summary.csv"):
        for pol in ("A", "B"):
            r = float(s[f"escalation_rate_policy{pol}"])
            per = p1 + r * p4
            row = {"table": "named_candidate_in_sample_DIAGNOSTIC", "cost_unit": f"{s['candidate']}/policy{pol}",
                   "escalation_rate": r, "p1_usd": round(p1, 7), "p4_usd": round(p4, 6),
                   "expected_cost_per_candidate_usd": round(per, 6),
                   "observed_item_weighted_cost_per_candidate_usd": s[f"cost_per_candidate_policy{pol}"]}
            for n in cs["candidates_per_day"]:
                row[f"daily_usd_{n}_per_day"] = round(per * n, 2)
                row[f"monthly_usd_{n}_per_day"] = round(per * n * days, 2)
            out.append(row)

    # inverse: max escalation rate allowed by a monthly budget
    for b in BUDGET_EXAMPLES:
        row = {"table": "max_escalation_for_monthly_budget", "cost_unit": f"budget_usd_{b}", "p1_usd": round(p1, 7), "p4_usd": round(p4, 6)}
        for n in cs["candidates_per_day"]:
            r = (b / (days * n) - p1) / p4
            row[f"max_escalation_rate_{n}_per_day"] = round(max(r, 0.0), 4) if r < 1 else ">=1.0 (all candidates)"
        out.append(row)

    fields = []
    for r in out:
        fields += [k for k in r if k not in fields]
    write_csv("cost_scenarios.csv", out, fields)
    print(f"P1={p1:.7f} P4={p4:.6f} single-cam P1={p1_single:.7f} P4={p4_single:.6f}")
    for r in out:
        if r["table"] == "by_escalation_rate" and r["cost_unit"] == "observed_mean_7_items":
            print(r["escalation_rate"], r["expected_cost_per_candidate_usd"], [r[f"monthly_usd_{n}_per_day"] for n in cs["candidates_per_day"]])
    for r in out:
        if r["table"] == "max_escalation_for_monthly_budget":
            print(r["cost_unit"], [r[f"max_escalation_rate_{n}_per_day"] for n in cs["candidates_per_day"]])


if __name__ == "__main__":
    main()
