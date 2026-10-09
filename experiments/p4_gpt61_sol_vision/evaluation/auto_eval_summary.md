# Automatic evaluation summary — P0 … P4

Generated 2026-10-08T01:06:45+09:00. P2 evaluator (auto-eval-v1) reused unchanged; same normalized_ground_truth_v1. Diagnostic counts (x/N) only — not % accuracy, not human rubric scores.

| Metric | P0 | P1-v1 raw | P2-v1 raw | P1 (v2) | P2 (v2) | P3 state (v2) | P4 vision (v2) |
|---|---|---|---|---|---|---|---|
| category_match | 5/9 | 2/9 | 5/9 | 2/9 | 0/9 | 4/9 | 9/9 |
| incident_decision_scored | 0/2 | 2/2 | 0/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| incident_decision_not_scored | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| attention_top1_correct | True | True | True | True | True | True | True |
| attention_full_order_correct | True | True | True | True | True | False | True |
| same_incident_correct | True | True | False | True | False | False | True |
| AB_A_B_category_correct | [False, False, False] | [False, False, False] | [False, False, True] | [False, False, False] | [False, False, False] | [True, False, True] | [True, True, True] |
| AB_uncertainty_improved | False | True | True | True | True | True | False |
| temporal_hit_ITEM_03 | False | True | True | True | True | True | True |
| internal_contradiction_count | 2 | 2 | 4 | 0 | 0 | 0 | 0 |
| suspected_overclaim_count | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| very_low_confidence_count | 0 | 0 | 3 | 0 | 3 | 0 | 0 |
| human_review_required_count | 4/9 | 9/9 | 5/9 | 9/9 | 5/9 | 8/9 | 9/9 |
| raw category answer match | n/a | 2/9 | 5/9 | 2/9 | 5/9 | 4/9 | 9/9 |

## Per assessment (final category ✓/✗; [raw category]; p(incident))

| Assessment | Expected | P0 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ | possible_fall_or_person_down ✓ [possible_fall_or_person_down] 0.85 | no_clear_incident ✗ [possible_fall_or_person_down] 0.48 | possible_fall_or_person_down ✓ [possible_fall_or_person_down] 0.97 | possible_fall_or_person_down ✓ [possible_fall_or_person_down] 0.99 |
| ITEM_02 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ | no_clear_incident ✗ [possible_fall_or_person_down] 0.35 | no_clear_incident ✗ [possible_scene_or_boundary_entry] 0.16 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.58 | possible_scene_or_boundary_entry ✓ [possible_scene_or_boundary_entry] 0.98 |
| ITEM_03 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ | no_clear_incident ✗ [possible_fall_or_person_down] 0.30 | no_clear_incident ✗ [no_clear_incident] 0.16 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.70 | possible_scene_or_boundary_entry ✓ [possible_scene_or_boundary_entry] 0.84 |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ | possible_fall_or_person_down ✓ [possible_fall_or_person_down] 0.92 | no_clear_incident ✗ [possible_fall_or_person_down] 0.44 | possible_fall_or_person_down ✓ [possible_fall_or_person_down] 0.97 | possible_fall_or_person_down ✓ [possible_fall_or_person_down] 0.99 |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident ✗ | no_clear_incident ✗ [no_clear_incident] 0.21 | no_clear_incident ✗ [possible_physical_conflict] 0.26 | no_clear_incident ✗ [no_clear_incident] 0.14 | possible_physical_conflict ✓ [possible_physical_conflict] 0.85 |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ | no_clear_incident ✗ [no_clear_incident] 0.40 | no_clear_incident ✗ [no_clear_incident] 0.27 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.51 | possible_scene_or_boundary_entry ✓ [possible_scene_or_boundary_entry] 0.98 |
| ITEM_05 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.59 | no_clear_incident ✗ [no_clear_incident] 0.30 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.64 | possible_physical_conflict ✓ [possible_physical_conflict] 0.94 |
| ITEM_06 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.72 | no_clear_incident ✗ [possible_physical_conflict] 0.38 | possible_physical_conflict ✓ [possible_physical_conflict] 0.74 | possible_physical_conflict ✓ [possible_physical_conflict] 0.99 |
| ITEM_07 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ | possible_fall_or_person_down ✗ [possible_fall_or_person_down] 0.79 | no_clear_incident ✗ [no_clear_incident] 0.31 | possible_physical_conflict ✓ [possible_physical_conflict] 0.84 | possible_physical_conflict ✓ [possible_physical_conflict] 0.99 |

## Attention / multi-camera

| Pipeline | Order | top1 | full | same_incident | AB/A/B final category |
|---|---|---|---|---|---|
| P0 | CAM_01 > CAM_02 > CAM_03 | True | True | True | False/False/False |
| P1-v1 raw | CAM_01 > CAM_02 > CAM_03 | True | True | True | False/False/False |
| P2-v1 raw | CAM_01 > CAM_02 > CAM_03 | True | True | False | False/False/True |
| P1 (v2) | CAM_01 > CAM_02 > CAM_03 | True | True | True | False/False/False |
| P2 (v2) | CAM_01 > CAM_02 > CAM_03 | True | True | False | False/False/False |
| P3 state (v2) | CAM_01 > CAM_03 > CAM_02 | True | False | False | True/False/True |
| P4 vision (v2) | CAM_01 > CAM_02 > CAM_03 | True | True | True | True/True/True |

Calibration vs reviewer_01 (P0/P1-v1 only): BORDERLINE: below the opposite-case threshold but close to it; diagnostic use only, not an official quality metric (OPPOSITE 3/13).

Note: P1–P3 evidence/temporal text is template-generated from the same CV state; P4 evidence/temporal/uncertainty/reason text is model-generated from frames, so temporal_hit and overclaim screening are more informative for P4 than for P1–P3.
