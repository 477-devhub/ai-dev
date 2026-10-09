# 477 AI — Two-Stage Triage / Cascade Analysis v1

**Status: COMPLETE (retrospective).** This analysis made **0 API calls**, modified **0 frozen artifacts** (`analysis/integrity_check.json`: 74 frozen inputs hashed at the start and re-hashed at the end, PASS; P3/P4 frozen result files also match their own results manifests) and left benchmark_v1 untouched.

All results are in-sample and diagnostic. The data has 9 assessments, 6 unique clips and 5 unique incidents, and **no normal negatives**.

> **Headline.** The existing P0–P4 evidence supports the *shape* of the cascade. A cheap P1 Stage 1 should not hard-suppress, should escalate uncertain or representation-sensitive cases to P4 Vision, and should send high-confidence cases straight to a human.
>
> It **cannot** support any number for workload reduction, safe-normal precision, real escalation rate or monthly cost. The benchmark has nothing that should be suppressed. Every reduction in the human queue measurable here is a missed positive.

---

## 1. Can current data answer this?

| | Count | Source |
|---|---|---|
| Clear normal negatives | **0** | `existing_results_inventory.json` |
| Hard normal negatives | **0** | |
| Confirmed / anchored danger | **2 assessments = 1 unique video** (ITEM_01 and ITEM_04/CAM_01 are both ASSET_01) | GT `incident_presence_anchor` |
| HV-observed event, danger not anchored | 2 (ITEM_02 and ITEM_04/CAM_03 = ASSET_02, wall crossing) | GT `human_verified_observation` |
| Ambiguous | 1 (ITEM_03, neutral gate entry) | GT `ambiguous_case` |
| Source-label only (diagnostic) | 4 (ITEM_04/CAM_02 F01 fight; ITEM_05, 06, 07 = one SET05 fight) | `not_scored` |

| Question | Answer |
|---|---|
| Can we estimate real Normal precision? | **No.** There are zero negatives. |
| Can we estimate real workload reduction? | **No.** With positives only, the human queue shrinks only by missing positives. |
| Can we estimate real escalation rate? | **No.** The escalation rate depends on the P1 score distribution of *benign* traffic, which was never observed. |
| Can we observe Danger→Normal? | Yes, but only as a raw count for 2 anchors from one video. A **conservative constraint set** (8 non-ambiguous source-positives) is used as a safety *constraint* only, never as accuracy truth. |
| Can we judge P4's suppression ability? | **No.** P4 answered DANGER on 9/9 and was never observed saying NORMAL. |

Other limitations:
- **In-sample tuning.** Thresholds and flags were defined after P0–P4 outputs and GT had been seen. Flags use only the generic conditions from the brief and round-number defaults (0.5 / 0.6 / 0.7), with no per-item tuning. Even so, nothing here is blind.
- **Uncalibrated scores.** P1 probabilities are uncalibrated routing variables.
- **Uncontrolled latency.** Latencies are the observed P1 cached-state path (about 1 s, excluding CV) and the P4 full visual path (about 85 s).

## 2. Stage 1 — P1 triage signals (frozen P1 output and compact state)

| Signal | Range over 9 positives | Usable as a router? |
|---|---|---|
| p(incident) | 0.21 – 0.92 | Yes. This is the main axis. Lowest positives: ITEM_04/CAM_02 fight 0.21, ITEM_03 0.30, ITEM_02 0.35, ITEM_04/CAM_03 0.40 |
| Category confidence | 0.28 – 1.00 | Partly. Low on the cases P1 got wrong (0.28 / 0.29 / 0.51 / 0.53) |
| Overall (adapter) confidence | 0.44 – 0.96 | Partly. It includes max(p, 1−p), so it rises mechanically as p falls, which partly cancels its value as a NORMAL gate |
| Risk (severity, imminence, exposure, persistence) | priority 0.34 – 0.72 | Tracks p; adds no independent separation on this data |
| human_review | **9/9 true** (p_review 0.74 – 0.95) | **No** (see below) |
| Uncertainty entries | Deterministic text from the CV state. "Boundary semantics unavailable" appears in **9/9** | No, not selective |
| Representation-sensitive flags (compact state) | see below | Yes, without the boundary flag |

**Why human_review is not selective.**
- The frozen question is "review because of *either* risk *or* uncertainty". It is an OR of the two things every candidate has.
- The compact state always carries unknown boundary and authorization fields, plus limited-reliability proxies. Under the frozen policy text these count as uncertainty.
- So the flag cannot separate cases. Routing on it equals "P4 on everything" (`p1_human_review` row: 7/7 calls).

**Representation-sensitive flags.** These are defined generically in `configs/cascade_analysis_v1.json` and computed from the frozen compact state P1 actually saw.

| Flag | Fires on | Comment |
|---|---|---|
| F_boundary (boundary semantics unavailable AND entry or large transition) | **9/9** | The P0 CV stack never provides boundary semantics, so this flag fires on any scene with a person. It is non-selective by construction. It only becomes useful once per-camera boundary or ROI configuration exists. |
| F_disagree (p < 0.5 but category ≠ no_clear_incident, or the reverse) | ITEM_02, ITEM_03 | P1 says "fall" at p 0.30–0.35. Its internal disagreement marks the entry cases. |
| F_interaction_lowconf (interaction record AND category confidence < 0.70) | ITEM_04/CAM_02, ITEM_05, ITEM_06 | The conflict views P1 mislabelled. |
| F_lowconf (confidence < 0.60 or category confidence < 0.50) | ITEM_04/CAM_03, ITEM_05 | |
| F_multicam | ITEM_07 | |
| Any flag without F_boundary | **7/9**: every positive except the two fall-anchor assessments | Covers all 4 low-p positives in-sample. Its fire rate on benign scenes is **unknown** and probably high (crowds and close pairs produce interaction records). |

## 3. Retrospective routing (per assessment)

The two proposed candidates are shown. The full long-form table is in `analysis/cascade_simulation.csv`, and the base signals are in `analysis/stage1_assessments.csv`.

| Assessment | Reference | P1 p / category | Flags (no boundary) | **Balanced** S1 → P4 → final | **Safety-first** S1 → final | P1 binary 0.5 (current single stage) |
|---|---|---|---|---|---|---|
| ITEM_01 | anchored | 0.85 / fall | — | **DANGER** → human (1.0 s) | SUSP → P4 DANGER (77 s) | DANGER |
| ITEM_04/CAM_01 | anchored (same video) | 0.92 / fall | — | **DANGER** (1.2 s) | **DANGER** (1.2 s) | DANGER |
| ITEM_02 | HV wall crossing | 0.35 / fall | disagree | SUSP → P4 DANGER (entry) (84 s) | SUSP → DANGER | **NORMAL ✗** |
| ITEM_04/CAM_03 | HV wall crossing (same video) | 0.40 / none | lowconf | SUSP → P4 DANGER (entry) (109 s) | SUSP → DANGER | **NORMAL ✗** |
| ITEM_03 | ambiguous | 0.30 / fall | disagree | SUSP → P4 DANGER (entry) (85 s) | SUSP → DANGER | NORMAL (not scored) |
| ITEM_04/CAM_02 | source-label fight | 0.21 / none | interaction | SUSP → P4 DANGER (conflict) (109 s) | SUSP → DANGER | **NORMAL ✗** |
| ITEM_05 | source-label fight | 0.59 / fall | interaction, lowconf | SUSP → P4 DANGER (conflict) (98 s) | SUSP → DANGER | DANGER (category wrong) |
| ITEM_06 | source-label fight | 0.72 / fall | interaction | SUSP → P4 DANGER (conflict) (79 s) | SUSP → DANGER | DANGER (category wrong) |
| ITEM_07 | source-label fight | 0.79 / fall | multicam | **DANGER** with P1 category "fall" (wrong) (1.9 s) | SUSP → DANGER | DANGER (category wrong) |

Time-to-attention is observed and uncontrolled: P1 cached-state latency plus, for SUSPICIOUS cases, the P4 full-path latency. CV extraction time is excluded.

**Readings from this table:**
1. **The current single-stage P1 at 0.5 would hide 3 must-surface views**, including both views of the human-verified wall crossing, and would suppress ITEM_03. A cascade fixes all of them in-sample.
2. **P4 recovered every escalated case and corrected the category every time.** This is consistent with the P3→P4 ablation. P4 is still not an oracle: it has never been tested on a benign clip.
3. **Direct DANGER shows P1's category, which can be wrong** (ITEM_07: "fall" for a fight). Under Policy B, background P4 verification is what fixes the label.
4. **The escalation path costs about 80–110 s of operator delay.** For a real incident in the SUSPICIOUS band, the safety cost of escalation is latency, not money.

## 4. Threshold sweep (`analysis/threshold_sweep.csv`, 700 settings)

**Where Danger→Normal starts.** Policy 1 (probability only):
- Anchored danger: Danger→Normal is **0 for every setting in the grid**. The anchors sit at p 0.85 and 0.92, and the grid goes no higher than T_normal 0.45. This is **uninformative**, not reassuring: it reflects one easy video.
- Conservative set:
  - T_normal ≥ 0.25 suppresses ITEM_04/CAM_02 (fight, p 0.21).
  - T_normal ≥ 0.30 also suppresses ITEM_03 (ambiguous).
  - T_normal ≥ 0.35 suppresses ITEM_02 (HV wall crossing).
  - T_normal ≥ 0.40 suppresses ITEM_04/CAM_03.
- **In-sample safe region for P1 probability alone: T_normal < 0.21.** That boundary sits on a single fight view, so it has zero margin.
- With the generic flags (`P3_safety_noboundary`), Danger→Normal stays at 0 up to T_normal 0.45, because every low-p positive carries at least one flag.
- Comparators, probability only:
  - P2 Clef-Flash: suppresses positives from T_normal 0.20, and an anchor at 0.45. Its scores are compressed, with a maximum of 0.48.
  - P3 Sol State: its lowest positive is CAM_02 at 0.14.
  - **P1 is the most usable Stage 1 score of the three state-based models.**

**Best safety-first candidates.** All have Danger→Normal = 0 on the anchored set *and* the conservative set:

| | Safety-first | Balanced |
|---|---|---|
| Policy | P3_safety_noboundary (probability plus generic flags; boundary flag dropped as non-selective) | same |
| T_normal | 0.10 (range: anything < 0.21) | 0.15 (range: anything < 0.21) |
| T_danger | 0.90 | 0.75 (range 0.75–0.90; see sensitivity) |
| Additional gates | NORMAL only if no flag | same |
| Danger→Normal (anchor / HV / conservative) | 0 / 0 / 0 | 0 / 0 / 0 |
| Danger direct (anchor) | 1 | 2 |
| Danger recovered by P4 (anchor) | 1 | 0 |
| P4 calls, Policy A (items) | 7 / 7 | 5 / 7 |
| Escalation rate, Policy A, in-sample | 100% | 71% |
| Human queue | 9 / 9 (all positives, as it should be) | 9 / 9 |
| Cost per candidate, Policy A / B | $0.414 / $0.414 | $0.296 / $0.414 |
| Conservative positives waiting on P4 | 7 (median 95 s) | 5 (median 97 s) |

T_danger sensitivity (`analysis/report_tables.md`), with T_normal 0.15 and the flag gate, Danger→Normal 0 throughout:

| T_danger | 0.55 | 0.60–0.70 | 0.75 | 0.80–0.85 | 0.90 | ≥ 0.95 |
|---|---|---|---|---|---|---|
| P4 items (of 7) | 3 | 4 | 5 | 6 | 7 | 7 |

Lowering T_danger reduces P4 calls on this data *only* because every case is positive. On real traffic, lower T_danger moves benign cases into the human queue with P1's often-wrong category. That false-alert load is unmeasured.

## 5. Pareto candidates

Pareto filtering is over (anchor D→N, conservative D→N, conservative final miss, P4 calls, human queue, cost). It yields 16 non-dominated settings (`report_tables.md`). They are degenerate:
- On positive-only data, *human queue* and *danger miss* are the same axis: a smaller queue means a positive was missed.
- So settings that miss 1–3 positives are "non-dominated" only because they are cheaper.

Restricted to Danger→Normal = 0:

| Candidate | What it is | Why none dominates |
|---|---|---|
| **Safety-first** (T_n 0.10, T_d 0.90, flag gate) | Almost everything goes to P4; NORMAL is nearly impossible | Lowest reliance on P1's score; highest cost and P4 latency |
| **Balanced** (T_n 0.15, T_d 0.75, flag gate) | High-p cases go direct to a human; flagged or mid-p cases go to P4 | Cheaper and faster for high-p cases; trusts P1 at ≥ 0.75 (in-sample 3/3 positive, 1/3 wrong category) |
| ~~Cost-first~~ | **Not proposed** | See below |

**Rejected: the in-sample lexicographic optimum** (`lexbest_overfit`: probability + confidence, C_normal 0.70, T_normal 0.30, T_danger 0.55):
- It reaches 2/7 P4 calls ($0.120 per candidate) with conservative Danger→Normal 0. That works only because C = 0.70 falls exactly between ITEM_02's confidence (0.685, kept) and ITEM_03's (0.705, suppressed).
- It suppresses the ambiguous ITEM_03.
- It sends 5 cases direct to DANGER at p ≥ 0.55 with no data on benign false alerts.

This is the textbook overfit that the brief's §32 warns about.

**Cost-first is not proposed.** With zero negatives, its constraint ("danger miss stays at 0 while P4 is minimized") can only be met by raising direct DANGER. The cost of that (false alerts) is unmeasurable.

## 6. Cost

Observed frozen means, re-read from `logs/run_summary.json`:
- **P1:** $0.0004737 per candidate (single-camera items $0.000321).
- **P4:** $0.413697 per candidate (single-camera items $0.409997; 64 frames at detail=high, billed as cache-write).

**Expected cost per candidate = P1 + escalation × P4** (Policy A; under Policy B, escalation includes direct-DANGER verification):

| P4 escalation | $/candidate | 100/day: daily / monthly | 500/day | 1,000/day | 5,000/day |
|---|---|---|---|---|---|
| 0% (P1 only) | 0.00047 | $0.05 / $1.42 | $0.24 / $7.11 | $0.47 / $14.21 | $2.37 / $71.06 |
| 1% | 0.00461 | $0.46 / $13.83 | $2.31 / $69.16 | $4.61 / $138.32 | $23.05 / $691.61 |
| 5% | 0.02116 | $2.12 / $63.48 | $10.58 / $317.38 | $21.16 / $634.76 | $105.79 / $3,173.79 |
| 10% | 0.04184 | $4.18 / $125.53 | $20.92 / $627.65 | $41.84 / $1,255.30 | $209.22 / $6,276.52 |
| 20% | 0.08321 | $8.32 / $249.64 | $41.61 / $1,248.20 | $83.21 / $2,496.40 | $416.07 / $12,481.98 |
| 50% | 0.20732 | $20.73 / $621.97 | $103.66 / $3,109.84 | $207.32 / $6,219.67 | $1,036.61 / $31,098.37 |
| 100% | 0.41417 | $41.42 / $1,242.51 | $207.09 / $6,212.57 | $414.17 / $12,425.13 | $2,070.86 / $62,125.67 |

All of the above is **scenario analysis**. No arrival rate has been measured. Costs are 30-day months.

- **P1 is negligible.** At 1,000 candidates per day, P1 alone is about $14/month; each 1% of P4 escalation adds about $124/month. **The escalation rate *is* the bill.**
- **Budget inverse.** `max_escalation = (B / (30·N) − P1) / P4`. Example: B = $300/month at 1,000 candidates/day allows about 2.3% escalation. The full table is in `cost_scenarios.csv` (`max_escalation_for_monthly_budget`). No affordability judgement is made; plug in the real budget.
- **Unmeasured lever.** P4's cost is driven by 64 frames × about 2,450 image tokens at detail=high. A cheaper Stage 2 (fewer frames, an event-window crop, lower detail) would shift the whole curve. It needs its own test.

## 7. Operator value

- **Work removed from the human (in principle).**
  - Watching all screens is replaced by reviewing a queue.
  - Benign candidates confidently suppressed at Stage 1 or Stage 2 never reach the operator.
  - Stage 2 attaches visual evidence and a corrected category (P4 fixed all 7 of P1's wrong or missing labels here).
- **What still requires a human.**
  - Every DANGER, and every case P4 could not resolve.
  - All judgments of authorization, intent and medical state, which both models are designed to leave unknown.
- **Can current data quantify the reduction?** **No.** The diagnostic `operator_review_reduction` is 0 for every safe setting, which is correct for a positive-only set. Any non-zero value came from missed positives.
- **Benchmark needed.** `477-triage-normal-v1` (see §8), plus a real candidate log from a pilot site for the benign:incident ratio.

## 8. Normal data gap (detail in `analysis/normal_data_gap.md`)

- **Is a new normal/benign set needed?** **Yes. This is the gating item.**
- **What exists in the project.** No normal class was downloaded. The only in-project source is the pre-event portion of the AI Hub 171 videos: 506 nominal 35 s windows, but only **21 unique scenes**, staged, and needing human verification. Use them for hard negatives.
- **Recommended `477-triage-normal-v1`** (~90 clips):
  - 30 clear normals.
  - 40 hard negatives: crouch then recover, sitting down, normal running, normal doorway or gate entry, close pairs, brief contact, object pickup, occlusion or darkness, crowd flow.
  - ≥ 20 new human-anchored dangers from distinct scenes.
  - At most 3 clips per scene. Labels frozen before any run.
- **Estimated run cost.** About $0.04 for P1 and about $37 for P4 on all clips.

## 9. Final architecture recommendation (hypothesis to test, not a validated design)

| Stage | What runs | Rule |
|---|---|---|
| Stage 0 | Cheap CV candidate filter (P0 state) | Unchanged. Its recall upstream of Stage 1 is still unmeasured. |
| Stage 1 | P1 Decisions (gpt-6-luna) on the compact state | **3-way triage**, see the routing logic below |
| Stage 2 | P4 GPT-6.1 Sol Vision on SUSPICIOUS cases (and, under Policy B, background on DANGER cases) | DANGER → queue; NORMAL → suppress *only once validated on negatives*; refusal or error → human |
| Human | Attention Queue | Final decision. DANGER from Stage 1 is shown immediately and never waits for P4. |

**Recommended routing logic** (`P3_safety_noboundary`, starting point = Balanced):

```
if p_incident >= T_danger (start 0.75–0.90):                 DANGER  -> human now (+ P4 background if Policy B)
elif p_incident <= T_normal (start < 0.21, e.g. 0.10–0.15)
     and not any(F_disagree, F_interaction_lowconf,
                 F_lowconf, F_multicam, F_refusal):           NORMAL  -> suppress (log for audit sampling)
else:                                                         SUSPICIOUS -> P4
do NOT use: human_review (9/9 true), F_boundary (9/9 true until per-camera boundary/ROI config exists)
```

Operational notes:
- **Policy B (P4 background on DANGER) is recommended** for at least the first deployment. P1's direct-DANGER categories were wrong on 3 of the 5 assessments with p ≥ 0.55 in-sample. P4 verification gives the operator a correct label at about 85 s, without delaying the alert.
- **Audit sampling.** Randomly sample a small share of Stage 1 NORMAL decisions for human audit. Otherwise Danger→Normal is unobservable in production.

## 10. Main conclusion

**Does the existing P0–P4 evidence support a NORMAL / SUSPICIOUS / DANGER → Strong Vision on SUSPICIOUS architecture?**

**Partially: the routing logic is supported; the economics and the NORMAL branch are not.**

| SUPPORTED BY DATA (in-sample, 9 assessments) | HYPOTHESIS / NEEDS MORE DATA |
|---|---|
| A single P1 binary threshold (0.5) hides 3 must-surface views (2 of them a human-verified wall crossing). A SUSPICIOUS band plus P4 recovers all of them. | That any T_normal suppresses meaningful benign traffic (zero negatives) |
| P1 is the best Stage 1 score among the state models (lowest positive 0.21 vs P2's compressed range and P3's 0.14) | Safe-Normal Precision and the false-normal rate on hard negatives |
| P4 Vision is the right Stage 2 for boundary/entry and interaction cases that compact state misses (P3→P4 ablation; P4 has the right category on all 7 assessments where P1's was wrong) | P4's ability to say NORMAL (never observed); P4 is not an oracle |
| P1 human_review is not a usable router (9/9 true, by construction) | The fire rate of the generic flags on benign scenes, i.e. whether the flag gate keeps escalation low |
| The boundary flag is non-selective until boundary or ROI configuration exists (9/9) | Real escalation rate, operator workload reduction and monthly cost |
| Cost is linear in the P4 escalation rate; P1 cost is negligible ($14/month at 1,000/day) | Danger→Normal rate (only 1 anchored video exists) |
| Direct DANGER from P1 often carries a wrong category, so background P4 has value | Time-to-attention under controlled latency (P0 CV time excluded here) |

**Minimum next experiment:**
1. Build `477-triage-normal-v1` (~90 human-verified clips: 30 clear normal, 40 hard negative, ≥ 20 new anchored dangers; at most 3 per scene).
2. Run frozen P1 and P4 once on it (about $37), with no prompt changes.
3. Re-run this exact analysis unchanged (`scripts/` + `configs/`) to measure Safe-Normal Precision, escalation rate on benign scenes, P4 NORMAL behavior and the flag fire rate.
4. In parallel, obtain a real Stage 0 candidate log (arrivals per camera per day, benign:incident ratio) from a pilot site to turn §6 from scenarios into a forecast.

---
**Files:**
- `analysis/stage1_assessments.csv`: signals, flags, reference and routing.
- `analysis/threshold_sweep.csv`: 700 settings, Pareto and lexicographic marks.
- `analysis/cascade_simulation.csv` and `analysis/cascade_summary.csv`: named candidates.
- `analysis/cost_scenarios.csv`.
- `analysis/comparator_sweep.csv`: P2/P3 as Stage 1.
- `analysis/normal_data_gap.md`.
- `analysis/report_tables.md`: generated tables.
- `analysis/integrity_check.json`.
- `figures/escalation_vs_cost.png`, `figures/escalation_vs_danger_miss.png`, `figures/cascade_flow.png`.
