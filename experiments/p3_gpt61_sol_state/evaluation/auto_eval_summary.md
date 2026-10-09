# Automatic evaluation summary — P0 / P1 / P2 / P3

Generated 2026-10-08T00:20:57+09:00. The P2 evaluator (auto-eval-v1) is reused unchanged with the same normalized_ground_truth_v1. Diagnostic counts only (x/N), not % accuracy, not human rubric scores. "v1 raw" = official raw experiment records; "adapter-v2" = common-adapter-v2 presentation (event_type = "no clear incident" when p(incident) < 0.5).

| Metric | P0 | P1-v1 raw | P2-v1 raw | P1 (adapter-v2) | P2 (adapter-v2) | P3 (adapter-v2) |
|---|---|---|---|---|---|---|
| category_match | 5/9 | 2/9 | 5/9 | 2/9 | 0/9 | 4/9 |
| incident_decision_scored | 0/2 | 2/2 | 0/2 | 2/2 | 0/2 | 2/2 |
| incident_decision_not_scored | 7 | 7 | 7 | 7 | 7 | 7 |
| attention_top1_correct | True | True | True | True | True | True |
| attention_full_order_correct | True | True | True | True | True | False |
| same_incident_correct | True | True | False | True | False | False |
| AB_A_B_category_correct | [False, False, False] | [False, False, False] | [False, False, True] | [False, False, False] | [False, False, False] | [True, False, True] |
| AB_uncertainty_improved | False | True | True | True | True | True |
| temporal_hit_ITEM_03 | False | True | True | True | True | True |
| internal_contradiction_count | 2 | 2 | 4 | 0 | 0 | 0 |
| suspected_overclaim_count | 0 | 0 | 0 | 0 | 0 | 0 |
| very_low_confidence_count | 0 | 0 | 3 | 0 | 3 | 0 |
| human_review_required_count | 4/9 | 9/9 | 5/9 | 9/9 | 5/9 | 8/9 |
| raw category match (model category answer, before adapter) | n/a | 2/9 | 5/9 | 2/9 | 5/9 | 4/9 |

## Per assessment (final event category; raw category in brackets)

| Assessment | Expected | P0 | P1 (v2) | P2 (v2) | P3 (v2) |
|---|---|---|---|---|---|
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ p=- | possible_fall_or_person_down ✓ [possible_fall_or_person_down] p=0.85 | no_clear_incident ✗ [possible_fall_or_person_down] p=0.479 | possible_fall_or_person_down ✓ [possible_fall_or_person_down] p=0.97 |
| ITEM_02 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ p=- | no_clear_incident ✗ [possible_fall_or_person_down] p=0.35 | no_clear_incident ✗ [possible_scene_or_boundary_entry] p=0.1552 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.58 |
| ITEM_03 | possible_scene_or_boundary_entry (ambiguous) | possible_scene_or_boundary_entry ✓ p=- | no_clear_incident ✗ [possible_fall_or_person_down] p=0.3 | no_clear_incident ✗ [no_clear_incident] p=0.164 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.7 |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ p=- | possible_fall_or_person_down ✓ [possible_fall_or_person_down] p=0.92 | no_clear_incident ✗ [possible_fall_or_person_down] p=0.4431 | possible_fall_or_person_down ✓ [possible_fall_or_person_down] p=0.97 |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident ✗ p=- | no_clear_incident ✗ [no_clear_incident] p=0.21 | no_clear_incident ✗ [possible_physical_conflict] p=0.2605 | no_clear_incident ✗ [no_clear_incident] p=0.14 |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ p=- | no_clear_incident ✗ [no_clear_incident] p=0.4 | no_clear_incident ✗ [no_clear_incident] p=0.2694 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.51 |
| ITEM_05 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ p=- | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.59 | no_clear_incident ✗ [no_clear_incident] p=0.2977 | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.64 |
| ITEM_06 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ p=- | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.72 | no_clear_incident ✗ [possible_physical_conflict] p=0.3788 | possible_physical_conflict ✓ [possible_physical_conflict] p=0.74 |
| ITEM_07 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ p=- | possible_fall_or_person_down ✗ [possible_fall_or_person_down] p=0.79 | no_clear_incident ✗ [no_clear_incident] p=0.3145 | possible_physical_conflict ✓ [possible_physical_conflict] p=0.84 |

## Attention / multi-camera

| Pipeline | Attention order | top1 | full | same_incident | AB/A/B final category | AB conf - best single |
|---|---|---|---|---|---|---|
| P0 | CAM_01 > CAM_02 > CAM_03 | True | True | True | False/False/False | -0.027 |
| P1-v1 raw | CAM_01 > CAM_02 > CAM_03 | True | True | True | False/False/False | 0.18 |
| P2-v1 raw | CAM_01 > CAM_02 > CAM_03 | True | True | False | False/False/True | 0.0117 |
| P1 (adapter-v2) | CAM_01 > CAM_02 > CAM_03 | True | True | True | False/False/False | 0.18 |
| P2 (adapter-v2) | CAM_01 > CAM_02 > CAM_03 | True | True | False | False/False/False | 0.0117 |
| P3 (adapter-v2) | CAM_01 > CAM_03 > CAM_02 | True | False | False | True/False/True | 0.03 |

Calibration vs reviewer_01 (P0/P1-v1 only, unchanged): BORDERLINE: below the opposite-case threshold but close to it; diagnostic use only, not an official quality metric (OPPOSITE 3/13, partial 5).

Note: P1/P2/P3 observations, temporal summaries and uncertainties come from the same deterministic templates over the same frozen state; evidence/temporal metrics do not distinguish the decision models.
