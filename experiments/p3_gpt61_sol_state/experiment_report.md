# P3 GPT-6.1 Sol State Reasoning — Experiment Report (p3-v1)

**Status: COMPLETE.** 7/7 primary requests succeeded. Retries: 0. Refusals: 0. Incomplete outputs: 0.

## 1. Config
| | |
|---|---|
| Model / endpoint | `gpt-6.1-sol` via `POST /v1/responses` (official SDK openai 3.26.0, `client.responses.with_raw_response.create`) |
| Reasoning effort | `high`; the response echoed `high` on every call |
| Input | Text only. `instructions` = frozen prompt + P1 decision definitions; `input` = compact state. No images, audio or tools; `store=false` |
| Structured Outputs | `text.format` json_schema with `strict: true`. One schema per task type; attention uses `$defs/$ref` and an object keyed by camera, so each camera appears exactly once |
| Compact state | `compact-decision-state-v1`. Bytes are identical to the P1 input and the P2 state on all 7 items (SHA256-verified post-run). The state was not modified |
| Probability source | `model_generated_estimate`. P1 used native Decisions API probabilities and P2 native Clef probabilities; P3's are LLM estimates and are not assumed to be calibrated |
| Adapter | Frozen P1 decision adapter (thresholds 0.5, confidence formula, priority weights 0.35/0.30/0.20/0.15) followed by the frozen common-adapter-v2 |
| Pricing | Checked 2026-10-08 at developers.openai.com/api/docs/models/gpt-6.1-sol. Standard tier: $2 input, $0.10 cached input, $2.50 cache write, $10 output (reasoning included) per 1M tokens |

## 2. Synthetic smoke test (`logs/smoke_test.json`)
The test sent three neutral synthetic states, one for each of the single, attention and multi_camera schema shapes. All checks passed:
- HTTP 200.
- Strict output was parsed and validated against the schema.
- Usage was parsed, including cached and reasoning tokens.
- Effort was `high` and no tools were returned.
- Latency was 14.0 s, 24.2 s and 20.9 s.

The multi_camera call needed one transient retry. Refusal, incomplete and parse-failure classification was verified on synthetic bodies. The refusal path through the adapters was verified offline.

## 3. Per item (final = common-adapter-v2)
| Item | p(incident) | Raw category (conf) | Final event_type | Sev | Review (p) | Latency ms | In (cached / cache-write) | Out (reasoning) | Cost |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 0.97 | fall/person-down (0.98) | possible fall or person-down event | 0.65 | true (0.99) | 9,705 | 1,922 (1,195 / 724) | 281 (194) | $0.004746 |
| 02 | 0.58 | fall/person-down (0.60) | possible fall or person-down event | 0.45 | true (0.68) | 14,550 | 2,161 (1,195 / 963) | 542 (455) | $0.007953 |
| 03 | 0.70 | fall/person-down (0.80) | possible fall or person-down event | 0.50 | true (0.84) | 10,947 | 2,167 (1,195 / 969) | 444 (297) | $0.006988 |
| 04 | 0.97 / 0.14 / 0.51 | CAM_01 fall (0.97) / CAM_02 no_clear (0.87) / CAM_03 fall (0.62) | fall / no clear incident / fall | 0.75 / 0.15 / 0.40 | T / F / T | 25,011 | 5,040 (1,504 / 3,533) | 1,224 (752) | $0.021229 |
| 05 | 0.64 | fall/person-down (0.70) | possible fall or person-down event | 0.50 | true (0.78) | 9,784 | 2,630 (1,195 / 1,432) | 318 (231) | $0.006886 |
| 06 | 0.74 | physical conflict (0.71) | possible physical conflict | 0.50 | true (0.86) | 10,983 | 3,854 (1,195 / 2,656) | 350 (264) | $0.010266 |
| 07 | 0.84 | physical conflict (0.67) | possible physical conflict | 0.56 | true (0.94) | 25,965 | 6,231 (1,475 / 4,753) | 618 (413) | $0.018216 |

- **ITEM_04:** order CAM_01 > CAM_03 > CAM_02, with priorities 0.756 / 0.302 / 0.247. Top-1 matches the reference but the full order does not. The supplementary attention_first answer was CAM_01 (0.98).
- **ITEM_07:** same_incident p=0.38 → false (reference true). second_view_adds p=0.46 → false. multiview_value 0.27.

## 4. Cost and observed primary latency
| | P1 | P2 | P3 |
|---|---|---|---|
| Mean theoretical cost / candidate | $0.000474 | $0.000436 | $0.010897 (~23× P1) |
| Total, 7 items | $0.003316 | $0.003054 | $0.076282 |
| Primary latency median (min–max) | 1,146 ms (225–1,848) | 480 ms (283–664) | 10,983 ms (9,705–25,965) |

The latency figures come from one call per item, made at different times. **This is not a controlled repeated latency benchmark.** The timings cover the cached state only, not end-to-end. No winner is declared from cost.

## 5. Auto diagnostics (P2 evaluator reused unchanged; same normalized_ground_truth_v1)
| | P0 | P1-v1 raw | P2-v1 raw | P1 v2 | P2 v2 | P3 v2 |
|---|---|---|---|---|---|---|
| Final category match (9) | 5/9 | 2/9 | 5/9 | 2/9 | 0/9 | 4/9 |
| Raw category answer match | — | 2/9 | 5/9 | 2/9 | 5/9 | 4/9 |
| HV incident anchors | 0/2 | 2/2 | 0/2 | 2/2 | 0/2 | 2/2 |
| Attention top-1 / full | ✓/✓ | ✓/✓ | ✓/✓ | ✓/✓ | ✓/✓ | ✓/✗ |
| same_incident | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ |
| Contradictions | 2 | 2 | 4 | 0 | 0 | 0 |
| Suspected overclaims | 0 | 0 | 0 | 0 | 0 | 0 |
| Human review | 4/9 | 9/9 | 5/9 | 9/9 | 5/9 | 8/9 |

The calibration of the auto category metric against reviewer_01 is still BORDERLINE: 3 of 13 decisive comparisons are opposite, so it is diagnostic only.

## 6. Answers to the P3 questions
- **A — ITEM_01 fall: yes.** p=0.97 with category fall (0.98). The same holds on ITEM_04/CAM_01. P1 also caught it; P2 missed it (p 0.48).
- **B — boundary entry (ITEM_02/03, ITEM_04/CAM_03): no.** P3 labels all three `possible_fall_or_person_down` at p 0.51–0.70. This is the same fall bias P1 showed. P2 named entry once (ITEM_02) but at p 0.16.
  - All three decision models, including the strong reasoner, fail to name boundary entry from this state. That is consistent with a **compact-state information bottleneck** for boundary/entry semantics: the state has no scene semantics, and a posture "transition" signal is present. P4 tests this directly.
- **C — conflict: partially.** P3 is the only model whose final output gets ITEM_06 (B view) and ITEM_07 (AB) as `possible_physical_conflict`. It misses ITEM_04/CAM_02 (no_clear_incident, 0.87) and ITEM_05 (A view, foliage-limited), where it says fall.
  - On the views where the CV state carries interaction evidence, the decision model's capacity matters: P1 called these fall, and P2 under-called.
- **D — multi-camera:** P3 is not more consistent than P1 here.
  - It gets the AB category right (unlike P1/P2).
  - It also says same_incident=false (p 0.38) and second_view_adds=false (p 0.46), with low multiview_value (0.27).
  - P3 treats sync_confirmed=false / identity_link_confirmed=false conservatively. The reference says same incident.

**Overall:** P3 combines P1's incident sensitivity with better conflict recognition. It has no contradictions and no very-low-confidence outputs. It is about 23× the cost and about 10× the observed latency of P1. The remaining failures are boundary entry, CAM_02 conflict, same_incident and the attention full order. The entry failures are shared by every decision model, which points to the representation rather than decision capacity. This is to be verified in P4 (GPT-6.1 Sol vision).

## 7. Human audit (`evaluation/human_audit_queue.md`)
- 6 P3 assessments were flagged.
- **5 need full video review:** ITEM_02, ITEM_03 (ambiguous), ITEM_04/CAM_02, ITEM_04/CAM_03 and ITEM_05.
- **1 needs a text check only:** ITEM_07 (P1/P2/P3 major disagreement).

## 8. Validation
- Prediction schema: 7/7 `validate_prediction --result` PASS.
- Benchmark integrity `validate_benchmark.py` PASSed at every checkpoint: before common-adapter, after common-adapter, before the P3 run, after the P3 run, after the result freeze and after the evaluator.
- Leakage audit: PASS on the first run.
  - State bytes equal P1 and P2 for all 7 items.
  - The instructions and schema equal the frozen rebuild.
  - There were no images or tools, and effort was high.
  - The runtime access audit found 0 forbidden opens.
  - No API key in 73 files.
- GT accessed before the result freeze: **no**. Order: run_p3_end → leakage_audit → p3_results_frozen → run_auto_eval.

## 9. Disclosures
- The implementer (Claude) has seen benchmark GT in earlier sessions (P2 evaluator construction). P3 semantics come only from frozen P1 definitions plus a generic prompt/schema written before any benchmark call. Nothing was tuned after seeing output.
- There was one pre-freeze integration fix: `common_adapter_bridge.py` now sets the module `__file__` before exec. No semantic change.
- Several process-log events (before the common-adapter step, the adapter freeze, the post-adapter validation, and smoke pass) were written into the P3 log at 00:16:46, just before `p3_frozen`. Their actual evidence is in the artifacts' own timestamps and outputs.
- The compare script was re-run once to fix a missing markdown table header. Results were untouched.
