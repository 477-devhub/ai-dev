# P1 vs P2 — OpenAI Decisions API (gpt-6-luna) vs Cloudflare Clef-Flash

Same canonical frames, same cheap CV, same cv-state-v1, **byte-identical compact-decision-state-v1 input**, same semantic questions, same frozen adapter. Only the decision model differs. One primary request per item for both. Automatic metrics are diagnostic counts (x/N), not % accuracy and not human rubric scores.

## Headline

| Axis | P1 (gpt-6-luna) | P2 (Clef-Flash) |
|---|---|---|
| Event category match (9 assessments) | 2/9 | 5/9 |
| Incident decision (HV-anchored only) | 2/2 | 0/2 |
| Attention order (ref CAM_01>CAM_02>CAM_03) | CAM_01 > CAM_02 > CAM_03 (top1 True, full True) | CAM_01 > CAM_02 > CAM_03 (top1 True, full True) |
| same_incident (ref true) | True | False |
| AB / A / B category correct | False / False / False | False / False / True |
| Internal contradictions | 2 | 4 |
| Suspected overclaims | 0 | 0 |
| Very low confidence (<0.4) | 0 | 3 |
| Human review required | 9/9 | 5/9 |
| Decision API latency median (min–max), ms | 1146 (225–1848) | 480 (283–664) |
| Theoretical external API cost, 7 items | $0.0033161 | $0.0030539 |
| Mean cost per candidate (item) | $0.0004737 | $0.0004363 |
| Input tokens, 7 items (provider tokenizer; not comparable) | 33161 | 33932 |
| Retries | 0 | 0 |

P1/P2 agree on category in 3/9 assessments and on is_incident in 4/9.

Latency: single primary call per item on each provider, measured at different times from the same client; not a controlled repeated benchmark. Cost: published input-token rates × provider-reported input tokens (P1 $0.10/M, P2 $0.09/M); actual P2 billing may be $0 under the Workers AI daily free Neuron allocation.

## Per assessment

| Assessment | Expected | P1 category (conf) | P2 category (conf) | P1 p(inc) → is_incident | P2 p(inc) → is_incident | P1 sev / imm | P2 sev / imm | P1 review | P2 review |
|---|---|---|---|---|---|---|---|---|---|
| ITEM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ (1.00) | possible_fall_or_person_down ✓ (0.80) | 0.85 → True | 0.48 → False | 0.71 / 0.88 | 0.45 / 0.54 | True | True |
| ITEM_02 | possible_scene_or_boundary_entry | possible_fall_or_person_down ✗ (0.72) | possible_scene_or_boundary_entry ✓ (0.32) | 0.35 → False | 0.16 → False | 0.35 / 0.38 | 0.15 / 0.32 | True | False |
| ITEM_03 | possible_scene_or_boundary_entry | possible_fall_or_person_down ✗ (0.71) | no_clear_incident ✗ (0.21) | 0.30 → False | 0.16 → False | 0.31 / 0.36 | 0.17 / 0.31 | True | False |
| ITEM_04/CAM_01 | possible_fall_or_person_down | possible_fall_or_person_down ✓ (1.00) | possible_fall_or_person_down ✓ (0.84) | 0.92 → True | 0.44 → False | 0.72 / 0.93 | 0.42 / 0.49 | True | True |
| ITEM_04/CAM_02 | possible_physical_conflict | no_clear_incident ✗ (0.51) | possible_physical_conflict ✓ (0.15) | 0.21 → False | 0.26 → False | 0.33 / 0.42 | 0.25 / 0.40 | True | False |
| ITEM_04/CAM_03 | possible_scene_or_boundary_entry | no_clear_incident ✗ (0.28) | no_clear_incident ✗ (0.18) | 0.40 → False | 0.27 → False | 0.39 / 0.36 | 0.19 / 0.24 | True | False |
| ITEM_05 | possible_physical_conflict | possible_fall_or_person_down ✗ (0.29) | no_clear_incident ✗ (0.06) | 0.59 → True | 0.30 → False | 0.42 / 0.52 | 0.18 / 0.40 | True | True |
| ITEM_06 | possible_physical_conflict | possible_fall_or_person_down ✗ (0.53) | possible_physical_conflict ✓ (0.12) | 0.72 → True | 0.38 → False | 0.47 / 0.53 | 0.22 / 0.50 | True | True |
| ITEM_07 | possible_physical_conflict | possible_fall_or_person_down ✗ (0.82) | no_clear_incident ✗ (0.10) | 0.79 → True | 0.31 → False | 0.53 / 0.66 | 0.20 / 0.46 | True | True |

## Per request (latency / tokens / cost)

| Item | P1 ms | P2 ms | P1 input tokens | P2 input tokens | P1 cost USD | P2 cost USD |
|---|---|---|---|---|---|---|
| ITEM_01 | 948 | 664 | 2589 | 2627 | 0.0002589 | 0.0002364 |
| ITEM_02 | 369 | 283 | 2828 | 2878 | 0.0002828 | 0.0002590 |
| ITEM_03 | 225 | 479 | 2834 | 2889 | 0.0002834 | 0.0002600 |
| ITEM_04 | 1146 | 621 | 9571 | 9778 | 0.0009571 | 0.0008800 |
| ITEM_05 | 1310 | 480 | 3297 | 3359 | 0.0003297 | 0.0003023 |
| ITEM_06 | 1598 | 410 | 4521 | 4731 | 0.0004521 | 0.0004258 |
| ITEM_07 | 1848 | 544 | 7521 | 7670 | 0.0007521 | 0.0006903 |

## Notes

- The frozen P1-v1 adapter has no category/is_incident reconciliation; both runs keep it (fix deferred to common-adapter-v2 for both).
- Evidence/temporal/uncertainty text is template-generated from the same compact state, so it is identical in structure for P1 and P2.
- Calibration of the auto event-category metric vs reviewer_01 is borderline (see auto_eval_summary.md); treat quality rows as diagnostic.
