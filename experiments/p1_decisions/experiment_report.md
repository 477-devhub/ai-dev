# P0.5 / P1 Experiment Report — CV State → OpenAI Decisions API (gpt-6-luna)

Run date: 2026-10-07 · run_id `p1_decisions-v1` · model_id `p1_decisions:gpt-6-luna@v1-decisions` · benchmark `477-reasoning-v1` (frozen, unchanged)

**No human quality grading yet.** `human_grading` is `null` in all 7 results. Nothing in this report compares outputs with private ground truth.

## 1. Setup

| | |
|---|---|
| Python | 3.12.6 (isolated venv `experiments/p1_decisions/.venv`). P0 venv and global Anaconda were untouched. |
| OpenAI SDK | `openai` 3.26.0, using the native `client.decisions.create` (called via `.with_raw_response`). No raw-HTTPS fallback was needed. |
| HTTP client | httpx2 2.13.1 |
| Model / endpoint | `gpt-6-luna` / `POST /v1/decisions`. Every response reported model `gpt-6-luna`. |
| Input | Text only: a generic preamble plus the compact state as canonical JSON. No images. |
| Timeouts | Connect 10 s, read 120 s. |
| Retries | At most 2, only for network errors, 429 and 5xx. Backoff is 1 s·2ⁿ plus 0–0.25 s jitter. 4xx responses are never retried. Actual retries: 0. |
| API key | Read from the environment or `experiments/.env` only. A scan of all 49 artifact files (including results) found no key. |

**SDK structure (checked from the installed SDK):**
- Questions are `predicate`, `choice` (value + description) or `score` (ordered `levels`).
- Answers come back in question order as `predicate{probability}`, `choice{choice, confidence, probabilities}`, `score{score, confidence, probabilities}` or `refusal{name}`.
- Usage fields: `input_tokens`, `input_tokens_details{cached_tokens, cache_write_tokens}`, `output_tokens`, `output_tokens_details{reasoning_tokens}` and `total_tokens`.
- No `compute_units` field exists, so it is recorded as `null`.

**Score semantics.** From the [Decisions guide](https://developers.openai.com/api/docs/guides/decisions): "a probability-weighted average of the level indices", where indices start at 0.

## 2. P0.5 integration result — PASS

The test used ITEM_01 only: 7 questions in 1 request.

All checks passed (`logs/p0_5_smoke.json`):
- authentication and request (HTTP 200);
- model returned `gpt-6-luna`;
- 7 of 7 answers returned, in order;
- predicate 2/2, choice 1/1 and score 4/4 parsed;
- usage captured (2,589 input tokens, 0 output tokens);
- prediction and result valid against the benchmark schemas;
- raw response saved;
- compact state SHA256 unchanged;
- no forbidden path opened;
- no API key in any artifact;
- benchmark validation passed before and after.

**Refusal path:** `scripts/offline_adapter_test.py` injects synthetic refusals for the single, attention and multi task types. The pipeline turns each into an unknown decision, lowers confidence, forces human review and adds an uncertainty entry. All checks passed. No real refusal occurred.

**Integration fix during P0.5:** in attempt 1 the API checks all passed. The smoke script's benchmark-validator subprocess used a bare `python`, which on Windows resolved to an interpreter without `jsonschema`. The benchmark itself validated PASS when run directly. The fix was harness-only (`sys.executable`). The attempt-1 raw response is kept as `raw_api/p0_5_ITEM_01_attempt1_harness_validator_bug.json`.

**Semantic changes after seeing smoke results: none.** The smoke answers were stored but not inspected before the freeze.

## 3. Compact Decision State design (`compact-decision-state-v1`)

The serializer is deterministic: it maps `cv-state-v1` to compact JSON (`src/compact_serializer.py`, `configs/compact_state_v1.yaml`, `schemas/compact_decision_state.schema.json`).

**Removed from the model input:**
- `item_id`, all fingerprints and the `generator` block;
- paths and file names;
- every P0 rule output (`event_type`, `is_incident`, `risk`, `confidence`, attention order, `same_incident`, explanations);
- P0 aggregate `same_incident_similarity_score` and `incident_signature_*`.

A forbidden-key check fails the build if any of these keys appear.

**Per camera:**
- sampling: count and intervals;
- quality: CV reliability with label, pose visibility, fragmentation, occlusion, dropout, small-person fraction and dark-frame fraction;
- people counts;
- at most 6 tracks;
- at most 4 interactions;
- scene: entry, exit, large transition, occlusion count, at most 4 fragment links, and `boundary_semantics_available: false`, `boundary_crossing: null`, `authorization_known: false`.

**Track summary:**
- reliability, `visible_fraction` and ambiguous links;
- first and last seen times;
- initial and final known posture, and the posture distribution;
- strongest vertical transition (from, to, times, `downward_change_bh`, confidence);
- longest low-posture run and post-transition low-posture seconds;
- motion: speeds in bh/s, net displacement, stationary and low-motion fractions, large-transition flag;
- appearance: entry and exit types.

**Selection rules** (generic quality scores, fixed in config):
- Tracks: `observed_frames × reliability × visible_fraction`, keeping tracks with ≥ 2 observations.
- Interactions: `close_fraction × co_observed_frames × pair_reliability`; both tracks must be included.

**Limited-reliability flags** (`{"value", "reliability": "limited", "note"}`):
- `contact_proxy`, noted as "heuristic visual proxy, not confirmed contact";
- rapid limb motion and arm extension;
- hip-based downward change;
- cross-camera person-count, temporal, motion-peak and posture-transition similarity.

**Cross-camera fields** (base observations only):
- `sync_confirmed: false` and `identity_link_confirmed: false`;
- the four similarities, each flagged limited;
- visibility complementarity, drop flags and low-visibility phases;
- per-phase person counts.

**Determinism and encoding:**
- Canonical JSON: UTF-8, sorted keys, compact separators, floats rounded to 3 decimals, no negative zero, no NaN.
- A rebuild produced byte-identical output, and `validate_compact_states.py` re-serializes and compares the bytes.
- Validation: 7 of 7 PASS (schema, forbidden keys and text, determinism, SHA256 manifest).

### State compression

| Item | P0 state bytes | Compact bytes | Reduction | Local token estimate* | Actual API input_tokens** |
|---|---|---|---|---|---|
| ITEM_01 | 226,814 | 1,964 | 99.13 % | 720 | 2,589 |
| ITEM_02 | 116,132 | 2,782 | 97.60 % | 959 | 2,828 |
| ITEM_03 | 247,172 | 2,805 | 98.87 % | 965 | 2,834 |
| ITEM_04 | 462,185 | 11,832 | 97.44 % | 3,529 | 9,571 |
| ITEM_05 | 155,803 | 4,390 | 97.18 % | 1,428 | 3,297 |
| ITEM_06 | 471,395 | 8,666 | 98.16 % | 2,652 | 4,521 |
| ITEM_07 | 358,727 | 15,713 | 95.62 % | 4,749 | 7,521 |
| **Mean** | 291,175 | 6,879 | 97.64 % (total) | 2,143 | 4,737 |

\* tiktoken o200k estimate of the preamble plus compact JSON only.

\*\* The authoritative count; it includes the question instructions. The 7-question set alone adds about 1.9k tokens per assessment.

## 4. Decision question definitions (`decisions-v1`, `configs/decisions_questions_v1.json`)

Every instruction is formed as scope + question + the full policy text:
- Use only the supplied CV observations.
- No medical diagnosis, criminal intent, authorization, identity, or weapons without supplied support.
- Null means unknown.
- Limited-reliability proxies count as uncertain evidence.
- Confidence and risk are separate concepts.

**Per assessment (7 questions):**

| Key | Type | Definition |
|---|---|---|
| `incident` | predicate | — |
| `incident_category` | choice | `no_clear_incident`, `possible_fall_or_person_down`, `possible_physical_conflict`, `possible_scene_or_boundary_entry`, `other_safety_relevant`, `uncertain` |
| `severity` | score, 5 levels | none / minor / moderate / serious / critical |
| `imminence` | score, 5 levels | none / low / moderate / high / immediate |
| `exposure` | score, 5 levels | none / one / two / small_group / many |
| `persistence` | score, 5 levels | none / momentary / short / sustained / ongoing |
| `human_review` | predicate | — |

**Attention (ITEM_04):** 7 per-camera questions × 3 cameras with camera scope, plus `attention_first` (choice of CAM_01, CAM_02, CAM_03 or `no_clear_priority`), for 22 questions.

**Multi-camera (ITEM_07):** the 7 questions over joint scope, plus `same_incident` (predicate), `second_view_adds` (predicate) and `multiview_value` (score, 5 levels), for 10 questions.

**Frozen adapter mapping:**
- Scores: `score/(levels−1)`, giving a value in [0, 1].
- `is_incident`: p(incident) ≥ 0.5.
- `confidence`: mean of the category confidence and max(p, 1−p) of the incident answer. It is halved if either answer is refused.
- `human_review_required`: p(review) ≥ 0.5, or any refusal, or confidence < 0.4.
- Priority: 0.35·severity + 0.30·imminence + 0.20·exposure + 0.15·persistence, the same weights as P0.
- Attention tie-break: priority, then severity, then confidence, then input order. `attention_first` is supplementary only.
- `same_incident`: p ≥ 0.5.
- A refused score is reported as 0.5 and flagged in the uncertainties.
- The `event_type` text map is fixed in the config.

**Evidence, uncertainties and temporal summary** are deterministic templates over compact-state fields (CV → Evidence, Decisions → Decision, Template → Explanation). The model generates no free text, and there is no second model call.

## 5. Freeze

`freeze/p1_freeze.json` (SHA256 `9a2733e2…`) was written after the P0.5 PASS and before the primary run. `run_p1.py` checks every frozen hash before it runs.

| File | SHA256 |
|---|---|
| schemas/compact_decision_state.schema.json | 2e408fd80f6a0eba9725d97b6b87a02cca9b3dc308b01a24946117c118a31774 |
| configs/compact_state_v1.yaml | 137dbf6375975f8f9d5f55cac8fe00772bdd43b44347802a1c489ea88ec47f44 |
| configs/decisions_questions_v1.json | 2e8f9967d83ae500acc07055648a913a0454789a9fa9d4d6ee956dd9cc3b47d4 |
| src/compact_serializer.py | b667538b6d81d3530489b0b2287877dcdf1fe26b0ebb9eaeca692ff593a14533 |
| src/decision_adapter.py | c6d951fa1689787d00e1a1a2f8a9cf38b4895baad273379f7a4d5c23161b712e |
| src/prediction_adapter.py | e222cc878b6f7f33b9b431c73a002f5dc896cea5567fdf55df36e9c9a80f3ead |
| src/decisions_client.py | e77d66ea957136a7a67a02461ee50629603e62a894740f560083754660659496 |
| src/p1_pipeline.py | 6164c44ce2493fdc7af5c63070dde6941466d13a9073bd17c5f21b04787d2ca7 |
| src/cost.py, state_loader.py, utils.py | see freeze file |

Nothing was changed after the P1 outputs were produced.

## 6. P1 primary run — API usage, latency, cost

There was 1 request per item: 7 succeeded, 0 failed, 0 refusals and 0 retries.

| Item | Questions | input_tokens | cached | output | reasoning | Decision API latency ms | openai-processing-ms | Cost USD |
|---|---|---|---|---|---|---|---|---|
| ITEM_01 | 7 | 2,589 | 0 | 0 | 0 | 948 | 252 | 0.0002589 |
| ITEM_02 | 7 | 2,828 | 0 | 0 | 0 | 369 | 290 | 0.0002828 |
| ITEM_03 | 7 | 2,834 | 0 | 0 | 0 | 225 | 158 | 0.0002834 |
| ITEM_04 | 22 | 9,571 | 0 | 0 | 0 | 1,146 | 1,085 | 0.0009571 |
| ITEM_05 | 7 | 3,297 | 0 | 0 | 0 | 1,310 | 1,037 | 0.0003297 |
| ITEM_06 | 7 | 4,521 | 0 | 0 | 0 | 1,598 | 1,474 | 0.0004521 |
| ITEM_07 | 10 | 7,521 | 0 | 0 | 0 | 1,848 | 1,777 | 0.0007521 |

Totals:
- 33,161 input tokens.
- **7-item external API cost: $0.0033161. Mean per candidate item: $0.00047373.**
- Decision API latency: median 1,146 ms, min 225 ms, max 1,848 ms.

The P0.5 smoke calls (2 × 2,589 tokens = $0.0005178) are not part of the primary run.

**Pricing:**
- Applied rate, from the [Decisions guide](https://developers.openai.com/api/docs/guides/decisions): "input costs $0.10 per 1M tokens. You pay only for input tokens: there are no cache-read, cache-write, or output-token charges."
- The [gpt-6-luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna) lists chat-endpoint Standard rates: input $0.10, cached $0.01, cache write $0.125, output $0.50 per 1M. The Decisions-specific rule was applied instead.
- Because every request reported 0 cached, 0 cache-write and 0 output tokens, the computed cost is the same under either reading.
- Service tier: standard (default). Pricing checked: 2026-10-07.
- No regional premium. The long-context surcharge (> 272K tokens) does not apply.

**Latency scope:** these timings are **cached-state only**. P0 CV states were reused and the CV was not re-run, so they are not full end-to-end figures. Accordingly:
- result `latency_ms` = `null`;
- the breakdown is in `runtime_config.latency`: `serializer_latency_ms` (0.2–3 ms), `decision_api_latency_ms`, `adapter_latency_ms` (< 2 ms) and `cached_state_pipeline_latency_ms`.

`estimated_cost_usd` = `null`, because local CV compute cost is unmeasured. `runtime_config.external_api_cost_usd` holds the API cost.

## 7. P1 outputs (recorded, not graded)

| Item | p(incident) → is_incident | Category (conf) | Sev / Imm / Exp / Pers | Confidence | Human review |
|---|---|---|---|---|---|
| ITEM_01 | 0.85 → true | possible_fall_or_person_down (1.00) | 0.71 / 0.88 / 0.25 / 0.99 | 0.93 | true (0.95) |
| ITEM_02 | 0.35 → false | possible_fall_or_person_down (0.72) | 0.35 / 0.38 / 0.34 / 0.45 | 0.69 | true (0.79) |
| ITEM_03 | 0.30 → false | possible_fall_or_person_down (0.71) | 0.31 / 0.36 / 0.28 / 0.48 | 0.71 | true (0.82) |
| ITEM_04 CAM_01 | 0.92 | possible_fall_or_person_down (1.00) | priority 0.724 | 0.96 | true |
| ITEM_04 CAM_02 | 0.21 | no_clear_incident (0.51) | priority 0.446 | 0.65 | true |
| ITEM_04 CAM_03 | 0.40 | no_clear_incident (0.28) | priority 0.362 | 0.44 | true |
| ITEM_05 | 0.59 → true | possible_fall_or_person_down (0.29) | 0.42 / 0.52 / 0.49 / 0.48 | 0.44 | true (0.85) |
| ITEM_06 | 0.72 → true | possible_fall_or_person_down (0.53) | 0.47 / 0.53 / 0.61 / 0.52 | 0.63 | true (0.92) |
| ITEM_07 (AB) | 0.79 → true | possible_fall_or_person_down (0.82) | 0.53 / 0.66 / 0.59 / 0.53 | 0.81 | true (0.94) |

**ITEM_04:**
- Attention order by priority formula: CAM_01 > CAM_02 > CAM_03.
- Supplementary `attention_first` = CAM_01 (conf 0.85).

**ITEM_07:**
- p(same_incident) 0.71 → `same_incident` true.
- p(second view adds) 0.85.
- `multiview_value` 0.26 (0–1).

**Determinism:** the three ITEM_01 calls (2 smoke attempts and the primary run) returned identical answers.

## 8. Validation

- Compact states: 7/7 PASS.
- Result JSON with the official `validate_prediction.py … --result`: **7/7 PASS**, 0 failed.
- `validate_benchmark.py`: PASS before and after the smoke test and the primary run. Frozen benchmark files changed: 0.
- P0 is unchanged: the config and schema hashes match the P0 report (`0f0d25d9…`, `efe509eb…`, `445feea6…`), and P0 source and state files were not modified.
- `score_results.py` was not run: it reads private ground truth, and grading is pending human review.

## 9. Leakage audit — PASS (`logs/leakage_audit.json`)

- **No item-specific branching.** Code mentions of forbidden terms are only deny-lists or allowlist definitions.
- **Model inputs are clean.** For all 7 items, the sent input SHA256 equals the frozen compact state plus preamble. No item or asset IDs, source labels, P0 decision fields (`event_type`, `is_incident`, `risk`, `attention_queue`, `same_incident`, similarity aggregates) or expected ranking appear.
- **Runtime access audit (Python audit hook):** no `private_ground_truth`, README, BENCHMARK_LOCK, annotation, candidate report, contact sheet, media, P0 debug or P0 results path was opened during any API run. Inputs pass through the allowlist in `src/utils.py`.
- **No API key** in 49 artifact files.

**Disclosure:** the implementer saw the benchmark README during the earlier P0 session. Nothing from it is used in P1 code, configs, questions or inputs.

## 10. Known limitations (objective; no ground-truth comparison)

**Category skew.** `possible_fall_or_person_down` was the chosen category in 7 of 9 assessments, including two where p(incident) < 0.5 (ITEM_02, ITEM_03). In those two the `event_type` text names a fall-like category while `is_incident` is false. The choice argmax and the predicate are independent questions, and the frozen adapter does not reconcile them. Any change belongs in p1-v2.

**Internal tension in ITEM_07.** p(second view adds) is 0.85 while the `multiview_value` score is 0.26.

**Low category confidence.** ITEM_05 (0.29) and ITEM_04 CAM_03 (0.28) have low category confidence. ITEM_05's overall confidence is 0.44, and human review was requested.

**Human review is always true.** It was true for all 9 assessments (p 0.74–0.95). The predicate gives no selectivity on this set.

**Inherited limitations.** P1 can only reason over what P0's CV observed: sparse 64-frame sampling, no boundary semantics, contact and limb proxies of limited reliability, and track fragmentation in crowded clips. It cannot recover information P0 failed to extract.

**Timing scope.** Latency is cached-state only. Full frames → CV → state → Decisions timing still needs a controlled AC-power run. There is a single primary call per item, with no latency repeats by design.

**Small sample.** 7 conditions on 5 cases is a diagnostic set, not a performance estimate.

## 11. Artifacts

- Inputs and configs: `compact_states/` (with `manifest.json`), `configs/`, `schemas/compact_decision_state.schema.json`, `freeze/p1_freeze.json`.
- API and run records: `raw_api/` (P0.5 attempts and ITEM_01…07, with no headers or key), `logs/` (smoke, run summary, leakage audit), `runtime_config.json`.
- Results: `benchmark_v1/results/p1_decisions/run_ITEM_01…07.json`.
