# Automatic evaluation summary (auto-eval-v1)

Generated 2026-10-07T23:49:00+09:00. One evaluator, identical rules for P0, P1, P2. These are automatic diagnostic metrics, **not** the 0-8 human rubric and **not** % accuracy (5 cases / 7 conditions).

## Rules

- Category: prediction `event_type` text -> normalized category (same regex table for every pipeline) vs `normalized_event_target`. ITEM_04 is counted per camera (9 assessments total).
- Incident decision: scored only where a human-verified incident-presence anchor exists (ITEM_01, ITEM_04/CAM_01); others `not_scored`.
- Temporal: only ITEM_03 has a human-verified clip-relative transition (gate crossing ~29-30 s, +/-1 s); all others `requires_human_audit`.
- Attention: CAM_01 > CAM_02 > CAM_03 is a **477 project-defined reference**, not AI Hub ground truth.
- Internal contradiction: (fall/conflict category & is_incident=false) or (no_clear_incident & is_incident=true) or (confidence < 0.4 & no human review).
- Overclaim: keyword screening per sentence; sentences with negation cues are skipped (counted separately). Suspected only.

## Per pipeline

| Metric | P0 | P1 | P2 |
|---|---|---|---|
| category_match | 5/9 | 2/9 | 5/9 |
| incident_decision_scored | 0/2 | 2/2 | 0/2 |
| incident_decision_not_scored | 7 | 7 | 7 |
| attention_top1_correct | True | True | True |
| attention_full_order_correct | True | True | True |
| same_incident_correct | True | True | False |
| AB_A_B_category_correct | [False, False, False] | [False, False, False] | [False, False, True] |
| AB_uncertainty_improved | False | True | True |
| temporal_hit_ITEM_03 | False | True | True |
| internal_contradiction_count | 2 | 2 | 4 |
| suspected_overclaim_count | 0 | 0 | 0 |
| very_low_confidence_count | 0 | 0 | 3 |
| human_review_required_count | 4/9 | 9/9 | 5/9 |

## Per assessment (predicted category; ✓ = matches normalized target)

| Assessment | Expected | P0 | P1 | P2 |
|---|---|---|---|---|
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ (inc=false, conf=0.744) | possible_fall_or_person_down ✓ (inc=true, conf=0.925) | possible_fall_or_person_down ✓ (inc=false, conf=0.6587) |
| ITEM_02 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ (inc=false, conf=0.804) | possible_fall_or_person_down ✗ (inc=false, conf=0.685) | possible_scene_or_boundary_entry ✓ (inc=false, conf=0.584) |
| ITEM_03 | possible_scene_or_boundary_entry (ambiguous) | possible_scene_or_boundary_entry ✓ (inc=false, conf=0.782) | possible_fall_or_person_down ✗ (inc=false, conf=0.705) | no_clear_incident ✗ (inc=false, conf=0.5242) |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ (inc=false, conf=0.738) | possible_fall_or_person_down ✓ (inc=true, conf=0.96) | possible_fall_or_person_down ✓ (inc=false, conf=0.6964) |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident ✗ (inc=false, conf=0.51) | no_clear_incident ✗ (inc=false, conf=0.65) | possible_physical_conflict ✓ (inc=false, conf=0.4455) |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | possible_scene_or_boundary_entry ✓ (inc=false, conf=0.898) | no_clear_incident ✗ (inc=false, conf=0.44) | no_clear_incident ✗ (inc=false, conf=0.454) |
| ITEM_05 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ (inc=false, conf=0.627) | possible_fall_or_person_down ✗ (inc=true, conf=0.44) | no_clear_incident ✗ (inc=false, conf=0.38) |
| ITEM_06 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ (inc=false, conf=0.806) | possible_fall_or_person_down ✗ (inc=true, conf=0.625) | possible_physical_conflict ✓ (inc=false, conf=0.3727) |
| ITEM_07 | possible_physical_conflict | possible_scene_or_boundary_entry ✗ (inc=false, conf=0.779) | possible_fall_or_person_down ✗ (inc=true, conf=0.805) | no_clear_incident ✗ (inc=false, conf=0.3917) |

## Attention (ITEM_04)

| Pipeline | Order | Top-1 | Full order |
|---|---|---|---|
| P0 | CAM_01 > CAM_02 > CAM_03 | True | True |
| P1 | CAM_01 > CAM_02 > CAM_03 | True | True |
| P2 | CAM_01 > CAM_02 > CAM_03 | True | True |

## Multi-camera (ITEM_05 A / ITEM_06 B / ITEM_07 AB)

| Pipeline | same_incident (ref true) | camera count ok | 2nd-view info present | AB / A / B category correct | AB conf - best single | AB uncertainty improved |
|---|---|---|---|---|---|---|
| P0 | True (✓) | True | True | False / False / False | -0.027 | False |
| P1 | True (✓) | True | True | False / False / False | 0.18 | True |
| P2 | False (✗) | True | True | False / False / True | 0.0117 | True |

Multi-view Increment (0-8 rubric) is not auto-generated.

## Calibration against existing human grading (reviewer_01, P0/P1)

- decisive comparisons: 13, OPPOSITE: 3, partial (human=1): 5
- ranking auto vs human agree: True
- verdict: **BORDERLINE: below the opposite-case threshold but close to it; diagnostic use only, not an official quality metric**
- rule: agree: match&human=2 or mismatch&human=0; OPPOSITE: match&human=0 or mismatch&human=2; human=1 is partial. Verdict threshold: OPPOSITE > 25% of decisive comparisons => not official.

| Pipeline | Assessment | Auto category match | Human event (0-2) | Relation |
|---|---|---|---|---|
| P0 | ITEM_01 | True | 1 | partial (human 1) |
| P0 | ITEM_02 | True | 0 | OPPOSITE |
| P0 | ITEM_03 | True | 2 | agree |
| P0 | ITEM_04/CAM_01 | True | 1 | partial (human 1) |
| P0 | ITEM_04/CAM_02 | False | 0 | agree |
| P0 | ITEM_04/CAM_03 | True | 0 | OPPOSITE |
| P0 | ITEM_05 | False | 0 | agree |
| P0 | ITEM_06 | False | 0 | agree |
| P0 | ITEM_07 | False | 0 | agree |
| P1 | ITEM_01 | True | 2 | agree |
| P1 | ITEM_02 | False | 0 | agree |
| P1 | ITEM_03 | False | 0 | agree |
| P1 | ITEM_04/CAM_01 | True | 2 | agree |
| P1 | ITEM_04/CAM_02 | False | 0 | agree |
| P1 | ITEM_04/CAM_03 | False | 1 | partial (human 1) |
| P1 | ITEM_05 | False | 1 | partial (human 1) |
| P1 | ITEM_06 | False | 1 | partial (human 1) |
| P1 | ITEM_07 | False | 2 | OPPOSITE |

Auto category match is never converted into a human score.

## Note on evidence/temporal fields

P1 and P2 observations, temporal summaries and uncertainties come from the same deterministic templates over the same frozen compact state, so evidence and temporal metrics are model-independent between P1 and P2; only decision fields (category, is_incident, risk, confidence, review flag, ranking, multi-camera decisions) differ.
