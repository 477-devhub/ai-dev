# cascade_analysis_v1 — Two-Stage Triage retrospective simulation

This is a retrospective simulation of a P1 (gpt-6-luna Decisions) Stage 1 with NORMAL / SUSPICIOUS / DANGER outputs, followed by a P4 (GPT-6.1 Sol Vision) Stage 2. It runs over the **frozen** P0–P4 outputs of `477-reasoning-v1`.

- **0 API calls.** Nothing outside this directory is written.
- **Integrity check.** Frozen inputs are hashed at the start and re-hashed at the end (`analysis/integrity_check.json`).

Read **`cascade_report.md`** first.

## Run (system Python 3.13, matplotlib)

Run these from `scripts/`, in order:

```bash
python inspect_existing_results.py
```

```bash
python build_triage_table.py
```

```bash
python sweep_stage1_thresholds.py
```

```bash
python simulate_cascade.py
```

```bash
python estimate_cost.py
```

```bash
python build_report.py
```

| Script | Output |
|---|---|
| `inspect_existing_results.py` | `analysis/existing_results_inventory.json` (reference tiers, signal ranges, costs, normal-data scan), `analysis/input_manifest.json` |
| `build_triage_table.py` | `analysis/stage1_assessments_base.csv` (P1 signals, generic flags, P4 decision, P2/P3 comparators) |
| `sweep_stage1_thresholds.py` | `analysis/threshold_sweep.csv` (4 policies × grid = 700 settings; Pareto and lexicographic marks), `analysis/comparator_sweep.csv` |
| `simulate_cascade.py` | `analysis/cascade_simulation.csv`, `analysis/cascade_summary.csv`, `analysis/stage1_assessments.csv` |
| `estimate_cost.py` | `analysis/cost_scenarios.csv` |
| `build_report.py` | `figures/*.png`, `analysis/report_tables.md`, `analysis/integrity_check.json` |

All rules, flags, grids and reference tiers are in `configs/cascade_analysis_v1.json`.

`analysis/normal_data_gap.md` and `cascade_report.md` are hand-written from the generated outputs.

## Rules followed
- **Danger reference.** Uses human-anchored tiers from `normalized_ground_truth_v1`, not AI Hub labels. Source-positive labels appear only as a conservative *constraint* set.
- **P4 is not ground truth.** P4 is treated as a Stage 2 model.
- **Uncalibrated thresholds.** Thresholds are in-sample routing variables, not calibrated or general optima.
- **Not blind.** The implementer had seen P0–P4 outputs and GT before writing any rule; this is disclosed in the config.

## Re-use on the normal extension
Once `477-triage-normal-v1` exists with frozen P1 and P4 outputs and human tiers (including `clear_normal` and `hard_negative`):
1. Point `configs/cascade_analysis_v1.json` at it.
2. Add the negative tiers to the reference-tier logic.
3. Re-run unchanged.

The metrics in report §1 that are currently "unmeasurable" become computable.
