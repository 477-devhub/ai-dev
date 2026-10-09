# P1 vs P2 vs P3 — same frames, CV, state and semantics; different decision model

All three decision models received the byte-identical compact-decision-state-v1 text and the same frozen P1 question semantics. Final predictions are compared through the frozen common-adapter-v2 (P1-v1/P2-v1 raw records unchanged). Automatic diagnostics only (x/N); not % accuracy, not human rubric scores.

| | P1 | P2 | P3 |
|---|---|---|---|
| Decision model | OpenAI Decisions API gpt-6-luna | Cloudflare Clef-Flash | GPT-6.1 Sol (Responses, high) |
| Probability source | native Decisions API probability | native Clef decision probability | model-generated structured estimate |

## Category behavior

| | P1 | P2 | P3 |
|---|---|---|---|
| Raw category answer match (9) | 2/9 | 5/9 | 4/9 |
| Final event category match (adapter-v2, 9) | 2/9 | 0/9 | 4/9 |
| Raw categories used | no_clear_incident×2, possible_fall_or_person_down×7 | no_clear_incident×4, possible_fall_or_person_down×2, possible_physical_conflict×2, possible_scene_or_boundary_entry×1 | no_clear_incident×1, possible_fall_or_person_down×6, possible_physical_conflict×2 |

## Incident detection

| | P1 | P2 | P3 |
|---|---|---|---|
| HV-anchored incident decisions (ITEM_01, ITEM_04/CAM_01) | 2/2 | 0/2 | 2/2 |
| p(incident) on anchored falls | 0.85, 0.92 | 0.48, 0.44 | 0.97, 0.97 |
| is_incident=true count (9) | 5 | 0 | 8 |
| p(incident) min / median / max | 0.21 / 0.59 / 0.92 | 0.16 / 0.30 / 0.48 | 0.14 / 0.70 / 0.97 |

## Risk score distributions (min / median / max over 9 assessments, 0-1)

| Risk | P1 | P2 | P3 |
|---|---|---|---|
| severity | 0.31 / 0.42 / 0.72 | 0.15 / 0.20 / 0.45 | 0.15 / 0.50 / 0.75 |
| imminence | 0.36 / 0.52 / 0.93 | 0.24 / 0.40 / 0.54 | 0.15 / 0.50 / 0.98 |
| exposure | 0.25 / 0.34 / 0.74 | 0.25 / 0.34 / 0.67 | 0.25 / 0.25 / 0.75 |
| persistence | 0.37 / 0.48 / 0.99 | 0.30 / 0.50 / 0.80 | 0.00 / 0.65 / 1.00 |
| priority | 0.34 / 0.47 / 0.72 | 0.24 / 0.41 / 0.49 | 0.25 / 0.52 / 0.76 |
| confidence | 0.44 / 0.69 / 0.96 | 0.37 / 0.45 / 0.70 | 0.56 / 0.75 / 0.97 |

## Attention ranking (ITEM_04; reference CAM_01 > CAM_02 > CAM_03, 477 project-defined)

| | P1 | P2 | P3 |
|---|---|---|---|
| Order | CAM_01 > CAM_02 > CAM_03 | CAM_01 > CAM_02 > CAM_03 | CAM_01 > CAM_03 > CAM_02 |
| Top-1 / full order | True / True | True / True | True / False |
| Priority CAM_01 / CAM_02 / CAM_03 | 0.724 / 0.446 / 0.362 | 0.468 / 0.460 / 0.243 | 0.756 / 0.247 / 0.302 |

## Multi-camera (ITEM_07; same-incident reference = true)

| | P1 | P2 | P3 |
|---|---|---|---|
| p(same_incident) → same_incident | 0.71 → True | 0.44 → False | 0.38 → False |
| p(second_view_adds) → second_view_adds | 0.85 → True | 0.78 → True | 0.46 → False |
| multiview_value (0-1) | 0.26 | 0.61 | 0.27 |
| AB / A / B final category correct | False / False / False | False / False / False | True / False / True |

## Consistency, review, overclaims

| | P1 | P2 | P3 |
|---|---|---|---|
| Internal contradictions: v1 raw → adapter-v2 | 2 → 0 | 4 → 0 | n/a → 0 |
| human_review_required | 9/9 | 5/9 | 8/9 |
| p(human_review) min / median / max | 0.74 / 0.85 / 0.95 | 0.18 / 0.32 / 0.78 | 0.27 / 0.84 / 0.99 |
| Very low confidence (<0.4) | 0 | 3 | 0 |
| Suspected overclaims | 0 | 0 | 0 |

## API cost and observed primary latency

| | P1 | P2 | P3 |
|---|---|---|---|
| Theoretical external API cost, 7 items | $0.003316 | $0.003054 | $0.076282 |
| Mean cost per candidate | $0.000474 | $0.000436 | $0.010897 |
| Primary latency median (min–max), ms | 1146 (225–1848) | 480 (283–664) | 10983 (9705–25965) |
| Input / output tokens, 7 items (provider tokenizers) | 33161 / 0 | 33932 / 0 | 24005 / 3777 |
| Retries | 0 | 0 | 0 |

Cost = provider-reported usage × official rates (P1 $0.10/M input; P2 $0.09/M input, actual billing likely $0 under the free Neuron allocation; P3 $2/M input, $0.10/M cached, $2.50/M cache write, $10/M output incl. reasoning). **Latency is one primary call per item at different times — NOT a controlled repeated latency benchmark** (planned after P4). No winner is declared from cost alone.

## Per assessment

| Assessment | Expected | P1 raw cat (p_inc) | P2 raw cat (p_inc) | P3 raw cat (p_inc) | P1 / P2 / P3 final event_type |
|---|---|---|---|---|---|
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down (0.85) | possible_fall_or_person_down (0.48) | possible_fall_or_person_down (0.97) | possible fall or person-down event / no clear incident / possible fall or person-down event |
| ITEM_02 | possible_scene_or_boundary_entry | possible_fall_or_person_down (0.35) | possible_scene_or_boundary_entry (0.16) | possible_fall_or_person_down (0.58) | no clear incident / no clear incident / possible fall or person-down event |
| ITEM_03 | possible_scene_or_boundary_entry | possible_fall_or_person_down (0.30) | no_clear_incident (0.16) | possible_fall_or_person_down (0.70) | no clear incident / no clear incident / possible fall or person-down event |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down (0.92) | possible_fall_or_person_down (0.44) | possible_fall_or_person_down (0.97) | possible fall or person-down event / no clear incident / possible fall or person-down event |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident (0.21) | possible_physical_conflict (0.26) | no_clear_incident (0.14) | no clear incident / no clear incident / no clear incident |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | no_clear_incident (0.40) | no_clear_incident (0.27) | possible_fall_or_person_down (0.51) | no clear incident / no clear incident / possible fall or person-down event |
| ITEM_05 | possible_physical_conflict | possible_fall_or_person_down (0.59) | no_clear_incident (0.30) | possible_fall_or_person_down (0.64) | possible fall or person-down event / no clear incident / possible fall or person-down event |
| ITEM_06 | possible_physical_conflict | possible_fall_or_person_down (0.72) | possible_physical_conflict (0.38) | possible_physical_conflict (0.74) | possible fall or person-down event / no clear incident / possible physical conflict |
| ITEM_07 | possible_physical_conflict | possible_fall_or_person_down (0.79) | no_clear_incident (0.31) | possible_physical_conflict (0.84) | possible fall or person-down event / no clear incident / possible physical conflict |
