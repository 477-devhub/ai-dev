# P0 → P4 comparison (477-reasoning-v1)

Same canonical frames for every pipeline. P1–P3: same cheap CV → byte-identical compact state → different decision model. P4: GPT-6.1 Sol sees the 64 canonical frames directly (no CV state). P1–P4 final predictions via frozen common-adapter-v2; P1/P2-v1 raw records unchanged. Diagnostic counts only (x/N): **not % accuracy** (5 cases / 7 conditions).

## Overview

| | P0 Cheap CV rules | P1 Decisions (gpt-6-luna) | P2 Clef-Flash | P3 Sol State | P4 Sol Vision |
|---|---|---|---|---|---|
| Final category match (9) | 5/9 | 2/9 | 0/9 | 4/9 | 9/9 |
| Raw category answer match (9) | n/a | 2/9 | 5/9 | 4/9 | 9/9 |
| Anchored incidents (2) | 0/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| Attention top-1 / full | True / True | True / True | True / True | True / False | True / True |
| same_incident (ref true) | True | True | False | False | True |
| AB / A / B final category | False/False/False | False/False/False | False/False/False | True/False/True | True/True/True |
| ITEM_03 temporal hit | False | True | True | True | True |
| Internal contradictions | 2 | 0 | 0 | 0 | 0 |
| Suspected overclaims | 0 | 0 | 0 | 0 | 0 |
| Human review required | 4/9 | 9/9 | 5/9 | 8/9 | 9/9 |
| External API cost / candidate | $0 (no external API) | $0.000474 | $0.000436 | $0.010897 | $0.413697 |

## P3 (State) vs P4 (Vision) — same model, effort, taxonomy, risk semantics, priority formula and adapter

| Capability | P3 State | P4 Vision |
|---|---|---|
| Fall (ITEM_01, ITEM_04/CAM_01) | 2/2 | 2/2 |
| Boundary / Entry (ITEM_02, ITEM_04/CAM_03) final / raw | 0/2 / 0/2 | 2/2 / 2/2 |
| Ambiguous Entry (ITEM_03) | possible_fall_or_person_down p=0.70 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.84 → possible_scene_or_boundary_entry ✓ |
| Conflict (CAM_02, ITEM_05, ITEM_06, ITEM_07) final / raw | 2/4 / 2/4 | 4/4 / 4/4 |
| Attention Top-1 | True | True |
| Attention Full Order | False (CAM_01 > CAM_03 > CAM_02) | True (CAM_01 > CAM_02 > CAM_03) |
| Same Incident (ref true) | p=0.38 → False | p=0.94 → True |
| Second-view value | adds p=0.46 → False; value 0.27 | adds p=0.99 → True; value 0.80 |
| Cost / candidate | $0.0109 | $0.4137 |
| Latency median (min–max) | 11.0 s (9.7–26.0) cached-state decision path | 85.1 s (75.6–108.1) full visual path |

### Ablation detail (raw category, p(incident) → final category)

| Assessment | Expected | P3 State | P4 Vision |
|---|---|---|---|
| ITEM_02 | possible_scene_or_boundary_entry | possible_fall_or_person_down p=0.58 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.98 → possible_scene_or_boundary_entry ✓ |
| ITEM_03 | possible_scene_or_boundary_entry | possible_fall_or_person_down p=0.70 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.84 → possible_scene_or_boundary_entry ✓ |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | possible_fall_or_person_down p=0.51 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.98 → possible_scene_or_boundary_entry ✓ |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident p=0.14 → no_clear_incident ✗ | possible_physical_conflict p=0.85 → possible_physical_conflict ✓ |
| ITEM_05 | possible_physical_conflict | possible_fall_or_person_down p=0.64 → possible_fall_or_person_down ✗ | possible_physical_conflict p=0.94 → possible_physical_conflict ✓ |
| ITEM_06 | possible_physical_conflict | possible_physical_conflict p=0.74 → possible_physical_conflict ✓ | possible_physical_conflict p=0.99 → possible_physical_conflict ✓ |
| ITEM_07 | possible_physical_conflict | possible_physical_conflict p=0.84 → possible_physical_conflict ✓ | possible_physical_conflict p=0.99 → possible_physical_conflict ✓ |
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down p=0.97 → possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.99 → possible_fall_or_person_down ✓ |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down p=0.97 → possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.99 → possible_fall_or_person_down ✓ |

## Per assessment (all pipelines)

| Assessment | Expected | P0 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.85 → possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.48 → no_clear_incident ✗ | possible_fall_or_person_down p=0.97 → possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.99 → possible_fall_or_person_down ✓ |
| ITEM_02 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ | possible_fall_or_person_down p=0.35 → no_clear_incident ✗ | possible_scene_or_boundary_entry p=0.16 → no_clear_incident ✗ | possible_fall_or_person_down p=0.58 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.98 → possible_scene_or_boundary_entry ✓ |
| ITEM_03 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ | possible_fall_or_person_down p=0.30 → no_clear_incident ✗ | no_clear_incident p=0.16 → no_clear_incident ✗ | possible_fall_or_person_down p=0.70 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.84 → possible_scene_or_boundary_entry ✓ |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.92 → possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.44 → no_clear_incident ✗ | possible_fall_or_person_down p=0.97 → possible_fall_or_person_down ✓ | possible_fall_or_person_down p=0.99 → possible_fall_or_person_down ✓ |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident ✗ | no_clear_incident p=0.21 → no_clear_incident ✗ | possible_physical_conflict p=0.26 → no_clear_incident ✗ | no_clear_incident p=0.14 → no_clear_incident ✗ | possible_physical_conflict p=0.85 → possible_physical_conflict ✓ |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ | no_clear_incident p=0.40 → no_clear_incident ✗ | no_clear_incident p=0.27 → no_clear_incident ✗ | possible_fall_or_person_down p=0.51 → possible_fall_or_person_down ✗ | possible_scene_or_boundary_entry p=0.98 → possible_scene_or_boundary_entry ✓ |
| ITEM_05 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ | possible_fall_or_person_down p=0.59 → possible_fall_or_person_down ✗ | no_clear_incident p=0.30 → no_clear_incident ✗ | possible_fall_or_person_down p=0.64 → possible_fall_or_person_down ✗ | possible_physical_conflict p=0.94 → possible_physical_conflict ✓ |
| ITEM_06 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ | possible_fall_or_person_down p=0.72 → possible_fall_or_person_down ✗ | possible_physical_conflict p=0.38 → no_clear_incident ✗ | possible_physical_conflict p=0.74 → possible_physical_conflict ✓ | possible_physical_conflict p=0.99 → possible_physical_conflict ✓ |
| ITEM_07 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ | possible_fall_or_person_down p=0.79 → possible_fall_or_person_down ✗ | no_clear_incident p=0.31 → no_clear_incident ✗ | possible_physical_conflict p=0.84 → possible_physical_conflict ✓ | possible_physical_conflict p=0.99 → possible_physical_conflict ✓ |

## API cost per candidate

| Pipeline | External API cost / candidate | 7-item total |
|---|---|---|
| P0 Cheap CV rules | $0 (no external API; local CV compute not costed) | $0 |
| P1 Decisions (gpt-6-luna) | $0.000474 | $0.003316 |
| P2 Clef-Flash | $0.000436 | $0.003054 |
| P3 Sol State | $0.010897 | $0.076282 |
| P4 Sol Vision | $0.413697 | $2.895882 |

Theoretical cost from provider-reported usage × official rates (P2 actual billing likely $0 under the free Neuron allocation). A higher-quality pipeline is not declared the winner on quality alone: 477 targets the Accuracy × Cost × Latency trade-off.

## Observed primary latency (NOT a controlled comparison)

| Pipeline | Median (min–max) | Path measured |
|---|---|---|
| P1 Decisions (gpt-6-luna) | 1.15 s (0.23–1.85) | cached-state decision path (state → API → adapter) |
| P2 Clef-Flash | 0.48 s (0.28–0.66) | cached-state decision path (state → API → adapter) |
| P3 Sol State | 10.98 s (9.70–25.97) | cached-state decision path (state → API → adapter) |
| P4 Sol Vision | 85.09 s (75.57–108.11) | full visual path: frame decode → encode → upload → provider → adapter → validation |

- **P4 primary latency = full visual path; P1/P2/P3 primary latency = cached-state decision path.**
- **Final fair latency comparison pending controlled benchmark (controlled_latency_v1).**
- P4 stage medians: frame decode 2.9 s, image encode 11.5 s, round-trip verify 1.4 s, API (upload + provider) 67.6 s, adapter 2 ms.
