"""Step 6 — figures, generated tables, and a final integrity re-check of every frozen input.

Writes figures/escalation_vs_cost.png, figures/escalation_vs_danger_miss.png, figures/cascade_flow.png,
analysis/report_tables.md, analysis/integrity_check.json.
The narrative cascade_report.md is written by hand from these outputs.
"""
from __future__ import annotations

import json
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["text.parse_math"] = False  # labels contain literal "$" amounts
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from _common import ANALYSIS, FIGURES, ROOT, load_analysis_csv, sha256, write_json  # noqa: E402

INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dc"
SERIES = {"P1_prob": ("#2a78d6", "o"), "P2_prob_conf": ("#eb6834", "s"),
          "P3_safety_full": ("#1baf7a", "^"), "P3_safety_noboundary": ("#eda100", "D")}


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_cost(inv, summary):
    p1, p4 = inv["cost"]["P1"]["mean_per_candidate"], inv["cost"]["P4"]["mean_per_candidate"]
    xs = [i / 100 for i in range(0, 101)]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    ax.plot([x * 100 for x in xs], [p1 + x * p4 for x in xs], color="#2a78d6", lw=2)
    lines = []
    for r in (0.01, 0.05, 0.10, 0.20, 0.50, 1.00):
        y = p1 + r * p4
        ax.plot(r * 100, y, "o", ms=6, color="#2a78d6", mec="white", mew=1.5)
        lines.append(f"{int(r*100):>3}%   ${y:.4f}/cand   ${y*1000*30:>7,.0f}/mo @1k/day")
    ax.text(0.02, 0.97, "Escalation  cost/candidate  monthly (scenario)\n" + "\n".join(lines), transform=ax.transAxes,
            va="top", ha="left", fontsize=7.5, color=INK, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=GRID))
    for s in summary:
        if s["candidate"] in ("balanced", "safety_first"):
            r = float(s["escalation_rate_policyA"])
            ax.plot(r * 100, p1 + r * p4, "o", ms=9, mfc="none", mec="#eb6834", mew=1.5)
            ax.annotate(f"{s['candidate']} (in-sample,\npositive-only — not a forecast)", (r * 100, p1 + r * p4),
                        textcoords="offset points", xytext=(-175, -4 if s["candidate"] == "balanced" else -18), fontsize=7.5, color=MUTED)
    ax.set_xlabel("P4 escalation rate (% of candidates)", color=INK, fontsize=9)
    ax.set_ylabel("Expected API cost per candidate (USD)", color=INK, fontsize=9)
    ax.set_title(f"API cost is set almost entirely by P4 escalation rate\nP1 ${p1:.6f} + rate × P4 ${p4:.4f} (observed frozen means)",
                 fontsize=10, color=INK, loc="left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(FIGURES / "escalation_vs_cost.png")
    plt.close(fig)


def fig_miss(sweep):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), dpi=150, sharey=True)
    for ax, (col, title) in zip(axes, [("danger_to_normal_conservative", "Conservative set (8 source-positive, non-ambiguous)"),
                                       ("danger_to_normal_anchor", "Human-anchored set (2 assessments, 1 unique video)")]):
        offsets = {"P1_prob": -0.6, "P2_prob_conf": -0.2, "P3_safety_full": 0.2, "P3_safety_noboundary": 0.6}
        for pol, (c, m) in SERIES.items():
            pts = Counter((round(float(r["escalation_rate_policyA"]) * 100, 1), int(r[col])) for r in sweep if r["policy"] == pol)
            ax.scatter([x + offsets[pol] * 1.5 for x, _ in pts], [y + offsets[pol] * 0.15 for _, y in pts],
                       s=[28 + 4 * n ** 0.5 for n in pts.values()], color=c, marker=m, edgecolors="white", linewidths=1, label=pol)
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        ax.set_xlabel("P4 escalation rate, policy A (% of 7 items)", fontsize=9, color=INK)
        _style(ax)
    for ax in axes:
        ax.set_yticks([0, 1, 2, 3])
    axes[0].set_ylabel("Danger→Normal at Stage 1 (count)", fontsize=9, color=INK)
    axes[0].legend(fontsize=7.5, frameon=False, loc="upper right")
    fig.suptitle("Escalation vs Danger→Normal across the threshold grid (700 settings). Positive-only data: lower escalation\n"
                 "is bought only by direct-DANGER of high-p positives or by suppressing positives. Benign-scene effect unmeasured.",
                 fontsize=9, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(FIGURES / "escalation_vs_danger_miss.png")
    plt.close(fig)


def fig_flow(summary):
    b = next(s for s in summary if s["candidate"] == "balanced")
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")

    def box(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=fc, ec=MUTED, lw=1))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8, color=INK)

    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.2))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.5, label, fontsize=7.5, color=MUTED, ha="center")

    box(1, 25, 14, 10, "Stage 0\nCheap CV candidate\n(P0 state)", "#f4f3ee")
    box(21, 25, 16, 10, "Stage 1  P1 Decisions\np, conf, generic flags\n~$0.0005 · ~1 s", "#cde2fb")
    box(45, 47, 18, 9, f"NORMAL → suppress\n{b['stage1_normal']} / 9 here (no negatives\nexist to suppress)", "#f4f3ee")
    box(44, 26, 18, 9, f"SUSPICIOUS → P4\n{b['stage1_suspicious']} / 9 here", "#fde3d6")
    box(45, 4, 18, 9, f"DANGER (p ≥ 0.75)\n{b['stage1_danger']} / 9 → human now", "#fbe5b3")
    box(65.5, 26, 18, 9, "Stage 2  P4 Sol Vision\n~$0.41 · ~85 s\nnot an oracle", "#cde2fb")
    box(87, 18, 12, 20, f"Human\nAttention Queue\n{b['human_queue']} / 9\n(final decision)", "#d6f0e5")
    arrow(15, 30, 21, 30)
    arrow(37, 32, 45, 51); arrow(37, 30, 45, 30); arrow(37, 28, 45, 8)
    arrow(62.5, 30, 65.5, 30)
    arrow(83.5, 30, 87, 30)
    ax.text(85, 40, "P4 DANGER\n6 / 6", fontsize=7.5, color=MUTED, ha="center")
    arrow(63, 8, 87, 22, "immediate")
    ax.text(76, 20, "P4 NORMAL → suppress\n(0 here; never observed)", fontsize=7.5, color=MUTED, ha="center")
    ax.text(1, 57, "Proposed 'balanced' cascade on 477-reasoning-v1 (9 source-positive assessments, retrospective, 0 API calls)",
            fontsize=9.5, color=INK)
    ax.text(1, 1, "Counts are in-sample on a positive-only set: they show routing, not workload reduction.", fontsize=7.5, color=MUTED)
    fig.savefig(FIGURES / "cascade_flow.png", bbox_inches="tight")
    plt.close(fig)


def md_table(rows, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join(out)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    inv = json.load(open(ANALYSIS / "existing_results_inventory.json", encoding="utf-8"))
    sweep = load_analysis_csv("threshold_sweep.csv")
    summary = load_analysis_csv("cascade_summary.csv")
    fig_cost(inv, summary)
    fig_miss(sweep)
    fig_flow(summary)

    # T_danger sensitivity for the balanced family (P3_safety_noboundary, T_normal 0.15)
    sens = [r for r in sweep if r["policy"] == "P3_safety_noboundary" and float(r["T_normal"]) == 0.15]
    tn_sens = [r for r in sweep if r["policy"] == "P1_prob" and float(r["T_danger"]) == 1.01]
    parts = [
        "# Generated tables (build_report.py)\n",
        "## Named candidates\n",
        md_table(summary, ["candidate", "policy", "T_normal", "T_danger", "C_normal", "stage1_normal", "stage1_suspicious",
                           "stage1_danger", "danger_to_normal_anchor", "danger_to_normal_hv", "danger_to_normal_conservative",
                           "final_miss_conservative", "p4_calls_policyA", "p4_calls_policyB", "human_queue",
                           "cost_per_candidate_policyA", "cost_per_candidate_policyB", "ambiguous_routes",
                           "conservative_dangers_waiting_on_p4", "median_p4_wait_s_for_those"]),
        "\n## T_danger sensitivity (P3_safety_noboundary, T_normal 0.15)\n",
        md_table(sens, ["T_danger", "stage1_danger", "stage1_suspicious", "p4_calls_policyA", "escalation_rate_policyA",
                        "danger_to_normal_conservative", "cost_per_candidate_policyA", "conservative_dangers_waiting_on_p4"]),
        "\n## T_normal sensitivity (P1_prob, T_danger off)\n",
        md_table(tn_sens, ["T_normal", "stage1_normal", "danger_to_normal_anchor", "danger_to_normal_hv",
                           "danger_to_normal_conservative", "ambiguous_routes"]),
        "\n## Pareto-non-dominated settings (lexicographic objective vector)\n",
        md_table([r for r in sweep if r["pareto"] == "True"], ["policy", "T_normal", "T_danger", "C_normal",
                 "danger_to_normal_anchor", "danger_to_normal_conservative", "final_miss_conservative",
                 "p4_calls_policyA", "human_queue", "cost_per_candidate_policyA", "ambiguous_routes"]),
    ]
    (ANALYSIS / "report_tables.md").write_text("\n".join(parts) + "\n", encoding="utf-8")

    manifest = json.load(open(ANALYSIS / "input_manifest.json", encoding="utf-8"))["files"]
    changed = [f for f, h in manifest.items() if sha256(ROOT / f) != h]
    write_json("integrity_check.json", {"inputs_rechecked": len(manifest), "changed": changed, "pass": not changed,
                                        "api_calls_made": 0})
    print("figures + tables written; integrity", "PASS" if not changed else f"FAIL {changed}")


if __name__ == "__main__":
    main()
