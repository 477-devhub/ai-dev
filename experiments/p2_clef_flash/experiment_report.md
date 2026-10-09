# P2 Clef-Flash — Experiment Report (p2-v1)

**Status: COMPLETE.** 7/7 benchmark requests succeeded. 0 retries. 0 missing or invalid answers.

## 1. Question
Same frames, same CV, same canonical CV state, same compact state and same decision semantics. How does Cloudflare
Clef-Flash compare with the OpenAI Decisions API (gpt-6-luna) on cost, latency and decision quality?

## 2. Cloudflare
| | |
|---|---|
| Endpoint | `POST https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/cloudflare/clef-flash` (direct REST; no AI Gateway) |
| Model / selector | `@cf/cloudflare/clef-flash` / `"model": "clef-flash"`. The response reports `model: "clef-flash"` |
| Schema | Verified live via `GET /ai/models/schema?model=@cf/cloudflare/clef-flash` (HTTP 200) and saved in `logs/cloudflare_schema_snapshot*.json`. Required fields: model, state, questions. 1–64 questions. Types: noul / choice (2–255 options) / score (2–10 levels). Answers: `{noul}`, `{choice, probabilities{}, confidence}`, `{score, legend, probabilities{index}, confidence}`. No refusal type. Usage: input_tokens, output_tokens |
| Context window | 65,536 tokens (catalog) |
| Pricing | $0.09 per 1M input tokens (8,182 neurons/M). No output-token price. Free allocation: 10,000 neurons/day; above that, $0.011 per 1k neurons. Source: developers.cloudflare.com/workers-ai/platform/pricing, cross-checked against the live catalog `price=0.09`. Checked 2026-10-07 |
| Plan state | Not observable through the API token; recorded as unknown. Total P2 usage ≈ 281 neurons (benchmark + smoke test), far below the 10k/day free allocation |

## 3. Synthetic smoke test (`logs/smoke_test.json`)
- Used a neutral `synthetic-smoke-v1` state. No benchmark item was used.
- Each answer type parsed: noul (p=0.968), choice, and score (probability keys `'0'..'4'`).
- Usage: 418 input tokens, 0 output tokens. Latency: 698 ms.
- Error handling: an invalid request (`questions: {}`) returned HTTP 400 and was not retried.
- Credential leakage: none. Result: PASS.

## 4. Fairness
- Compact state: `compact-decision-state-v1`. All P1 freeze hashes were unchanged (11 files + 7 states), verified at freeze, at run start and after evaluation.
- The `state` P2 sent is **byte-identical** to the P1 Decisions input for all 7 items: same SHA256 as the P1 `raw_api` request.
- Semantic question parity: `semantic_questions()` equals P1 `build_questions` (extracted from the frozen P1 source) for all 7 items: 7/7/7/22/7/7/10 questions with the same ids, order, instruction strings, choices and levels. The only translation was predicate→noul, plus the Clef `criteria` wire format.
- Adapter: P1 `decision_adapter.py` was executed from its frozen bytes. Templates are P1 `prediction_adapter.py` with five provider-name string substitutions and no logic change. Category/is_incident reconciliation is **not** fixed (P1-v1 behaviour kept; deferred to common-adapter-v2).
- Semantic changes after seeing benchmark output: **none**. P2 was frozen at `freeze/p2_freeze.json` before any benchmark request.
- No P1 output, label, GT or grading was sent to Clef (`logs/leakage_audit.json` PASS).

## 5. P2 per item
Risk values are normalized 0–1 (score/(levels-1)). Costs are theoretical: input tokens × $0.09/M. Output tokens were 0 for every item.

| Item | p(incident) → is_incident | Category (conf) | Severity | Human review (p) | Latency ms | Input tokens | Theoretical cost |
|---|---|---|---|---|---|---|---|
| ITEM_01 | 0.48 → false | possible_fall_or_person_down (0.80) | 0.45 | true (0.78) | 664 | 2,627 | $0.0002364 |
| ITEM_02 | 0.16 → false | possible_scene_or_boundary_entry (0.32) | 0.15 | false (0.24) | 283 | 2,878 | $0.0002590 |
| ITEM_03 | 0.16 → false | no_clear_incident (0.21) | 0.17 | false (0.18) | 479 | 2,889 | $0.0002600 |
| ITEM_04 | per camera: 0.44 / 0.26 / 0.27 → all false | CAM_01 fall (0.84), CAM_02 physical conflict (0.15), CAM_03 no_clear (0.18) | 0.42 / 0.25 / 0.19 | true / false / false | 621 | 9,778 | $0.0008800 |
| ITEM_05 | 0.30 → false | no_clear_incident (0.06) | 0.18 | true (0.32; low confidence 0.38) | 480 | 3,359 | $0.0003023 |
| ITEM_06 | 0.38 → false | possible_physical_conflict (0.12) | 0.22 | true (0.40; low confidence 0.37) | 410 | 4,731 | $0.0004258 |
| ITEM_07 | 0.31 → false | no_clear_incident (0.10) | 0.20 | true (0.32; low confidence 0.39) | 544 | 7,670 | $0.0006903 |

- **ITEM_04 attention:** order CAM_01 > CAM_02 > CAM_03. Top-1 and full order both match the 477 project reference. CAM_01 and CAM_02 priority scores are close (0.468 vs 0.460). The supplementary attention_first answer was CAM_01 (confidence 0.26).
- **ITEM_07:** same_incident p=0.44 → false (reference true). second_view_adds p=0.78 → true. multiview_value = 0.61.

## 6. Cost and latency
- Theoretical external API cost: $0.0030539 for 7 items, or $0.0004363 per candidate. P1 (gpt-6-luna, $0.10/M): $0.0033161, or $0.0004737 per candidate. P2 is about 8% cheaper per candidate.
- Actual billed cost: unknown per request (`actual_billed_cost_usd = null`). It is very likely $0 because usage was ~281 neurons against a 10k/day free allocation.
- Decision API latency for P2, one call per item: median 480 ms (min 283, max 664). P1: median 1146 ms (min 225, max 1848). These are single primary calls made at different times. They are not a controlled repeated benchmark.
- Timings cover the cached state only (frozen compact state). They are not end-to-end, so `latency_ms` in the results is null.
- Token counts come from different tokenizers (P1 33,161 vs P2 33,932) and are not used as an efficiency comparison.

## 7. Automatic evaluation (`evaluation/auto_eval_summary.md`)
One evaluator, with the same rules for P0, P1 and P2. The output is diagnostic counts, not % accuracy and not human rubric scores.

| | P0 | P1 | P2 |
|---|---|---|---|
| Category match (9 assessments) | 5/9 | 2/9 | 5/9 |
| Incident decision (HV anchor only) | 0/2 | 2/2 | 0/2 |
| Attention top-1 / full order | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ |
| same_incident (reference true) | ✓ | ✓ | ✗ |
| AB / A / B category correct | ✗/✗/✗ | ✗/✗/✗ | ✗/✗/✓ |
| ITEM_03 temporal hit | ✗ | ✓ | ✓ |
| Internal contradictions | 2 | 2 | 4 |
| Suspected overclaims | 0 | 0 | 0 |
| Very low confidence | 0 | 0 | 3 |

**Calibration against reviewer_01 (P0/P1):** 3 of 13 decisive comparisons were OPPOSITE (23%) and 5 were partial. That is **borderline**, so the auto category metric is diagnostic only and not an official quality metric. The P0 5/9 is inflated because P0 labels almost every clip "person movement / scene entry", which happens to match on the entry items. The human reviewer scored P0 ITEM_02 and ITEM_04/CAM_03 as 0 even though the category matched.

## 8. P1 vs P2 (`evaluation/p1_vs_p2.md`, `.csv`)
- **Categories:** P2 matched 5/9 and P1 matched 2/9. P1 maps almost everything to fall/person-down. P2 differentiates more, but its category confidences are often near-uniform (0.12–0.32 on ITEM_02, ITEM_04/CAM_02 and ITEM_06).
- **Incident decisions:** P2 p(incident) is below 0.5 on **every** assessment, including both human-verified falls (0.48 and 0.44). P2 therefore gets 0/2 on the anchored incident decisions, while P1 gets 2/2. P2's risk scores are also compressed: severity is at most 0.45, versus P1's 0.72.
- **Ranking:** both pipelines produced the reference order.
- **Multi-camera:** P1 said same_incident = true (correct). P2 said false (p=0.44). Both answered second_view_adds = true.
- **Contradictions:** P1 had 2 (fall category with is_incident=false on ITEM_02 and ITEM_03). P2 had 4 (fall or conflict category with is_incident=false on ITEM_01, CAM_01, CAM_02 and ITEM_06). Both come from the same unreconciled frozen adapter, so the fix belongs in common-adapter-v2.
- **Human review:** P1 required review on 9/9 assessments. P2 required it on 5/9 and skipped review on ITEM_02, ITEM_03, CAM_02 and CAM_03.
- **Overclaims:** 0 suspected for both. The evidence and uncertainty text comes from the same templates.
- **Cost:** P2 is about 8% cheaper on theoretical cost, and likely $0 actual cost under the free allocation. **Latency:** P2 was faster in this single-call run (median 480 vs 1146 ms). This is not controlled.
- **Overall:** P2 is cheaper and (in this run) faster. Decision quality is mixed. P2 separates categories better, but it under-calls incidents (p<0.5 on the verified falls), rejects same_incident, and is less willing to request human review. Neither model dominates. A controlled latency benchmark and common-adapter-v2 are the next steps.

## 9. Human audit queue (`evaluation/human_audit_queue.md`)
- 25 flagged assessments. 9 are P2 rows.
- **4 need full-video review** (P2 only): ITEM_03 (ambiguous; no_clear_incident), ITEM_04/CAM_03, ITEM_05 and ITEM_07 (category mismatch, very low confidence).
- The other 5 P2 rows need a text or decision check only (adapter contradictions or P1/P2 disagreement). P0/P1 rows already have reviewer_01 grades.

## 10. Validation and process
- Prediction schema: 7/7 `validate_prediction.py --result` PASS.
- Benchmark integrity: `validate_benchmark.py` passed before the run, after the run, after the result freeze and after the evaluator.
- Leakage audit: PASS. Runtime access audit: 0 forbidden paths opened. Credentials: none found in 55 files.
- GT accessed before result freeze: **no** for every program. Order in `logs/process_audit_log.jsonl`: run_p2_end → leakage_audit → p2_results_frozen → build_auto_ground_truth.

## 11. Disclosures
- The leakage audit ran three times. Run 1 FAILed on a false positive: the deny-list matched the ITEM_07 question *id* `same_incident`, a frozen P1 question name. The audit-only fix excludes question ids. Run 2 did not apply the edit. Run 3 passed. No model-path file changed (P2 freeze hashes are unchanged).
- The `schema_inspected`, `smoke_test_pass` and `p2_frozen` process-log events were appended just before `run_p2`. Their real times are recorded in the artifacts themselves (`logs/smoke_test.json` `at`, `freeze/p2_freeze.json` `frozen_at`).
- While surveying the project, before writing any P2 code, the implementer (Claude) opened `private_ground_truth/set01.json` and listed the `human_grading` directory. No P2 model-path code or config uses this. All P2 semantics come from frozen P1 files, and nothing was tuned.
- `run_auto_eval.py` was re-run once. The fix was a markdown table formatting change and a "borderline" verdict tier, added before the calibration ratio was interpreted. Predictions were untouched (hash-verified before and after).
