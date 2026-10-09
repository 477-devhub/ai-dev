# P4 GPT-6.1 Sol Vision — Experiment Report (p4-v1)

**Status: COMPLETE.** 7/7 primary requests succeeded, with 0 retries, 0 refusals and 0 incomplete responses. P4 is a
*strong direct-vision upper-bound condition within 477-reasoning-v1*. It is not an absolute theoretical maximum.

## 1. Config
| | |
|---|---|
| Model / endpoint | gpt-6.1-sol, `POST /v1/responses`, official SDK openai 3.26.0 (same as P3) |
| Reasoning effort / tier | `high` (echoed on every call); default tier, no service_tier sent, returned `default` |
| Tools / store | none / `store=false` |
| Input | One user message: generic visual prompt plus 64 × (frame label `F### \| CAM_## \| t=…s`, image). No CV state, compact state or item id (verified in `logs/request_text_ITEM_XX.txt`) |
| Frames | `iter_model_frames` (uniform_total64_v1): 64 / 64 / 64 / 22+21+21 / 64 / 64 / 32+32. No extra frames, no whole-video upload |
| Transport | Lossless WebP (Pillow q50/m2), in memory. Round trip: 448/448 frames bit-exact, and the run-time encoded bytes are identical to the pre-freeze verification. No image files written; base64 never stored |
| Detail | `high` for every image |
| Structured Outputs | json_schema `strict: true`. `frame_ref` enums are restricted per request and per camera. Evidence: 1–6 items per assessment |
| Probabilities | `model_generated_estimate` (not native decision probabilities) |
| Adapter | Frozen P1 decision adapter (0.5 thresholds, 0.35/0.30/0.20/0.15 priority), then frozen common-adapter-v2 |
| Pricing | Checked 2026-10-08. Standard rates per 1M tokens: input $2, cached $0.10, cache write $2.50, output $10 |

## 2. Gates before freeze
- **Synthetic smoke (shapes):** all three schema shapes returned HTTP 200 with 6 images at detail=high. Strict output passed, frame_ref evidence resolved, and usage including reasoning tokens was parsed. Effort was high, no tools were returned, and tier was `default`. Latency was 16.9 s / 30.1 s / 18.3 s. Refusal, incomplete and parse-failure classification passed, and cross-camera frame_ref rejection passed offline.
- **Transport verification:** 7 items × 64 frames, lossless 448/448. The allocation is correct.
- **Preflight:** base64 payloads are 102–157 MB (19–29% of the 512 MB limit), with 64 images per item (limit 1,500). The token estimate was ~162k against the 1.05M context and the 272k long-context threshold.

## 3. Results per item (final = common-adapter-v2)
| Item | p(inc) | Raw category (conf) | Final event_type | Sev | Review | Full / API s | In / cache-write | Out (reasoning) | Cost |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 0.99 | fall (0.99) | possible fall or person-down event | 0.65 | T | 75.6 / 58.9 | 159,233 / 159,230 | 882 (357) | $0.4069 |
| 02 | 0.98 | boundary entry (0.99) | possible scene or boundary entry … | 0.30 | T | 84.0 / 65.5 | 159,233 / 159,230 | 1,003 (473) | $0.4081 |
| 03 | 0.84 | boundary entry (0.97) | possible scene or boundary entry … | 0.10 | T | 85.1 / 67.6 | 159,233 / 159,230 | 1,095 (584) | $0.4090 |
| 04 | 0.99 / 0.85 / 0.98 | fall / conflict / entry | fall / conflict / entry | 0.75 / 0.50 / 0.25 | T/T/T | 108.1 / 87.7 | 159,969 / 159,966 | 2,662 (1,034) | $0.4265 |
| 05 | 0.94 | conflict (0.90) | possible physical conflict | 0.50 | T | 96.9 / 80.2 | 159,233 / 159,230 | 1,650 (1,034) | $0.4146 |
| 06 | 0.99 | conflict (0.99) | possible physical conflict | 0.85 | T | 76.9 / 61.8 | 159,233 / 159,230 | 1,328 (735) | $0.4114 |
| 07 | 0.99 | conflict (0.98) | possible physical conflict | 0.80 | T | 95.3 / 77.3 | 159,639 / 159,636 | 2,026 (1,034) | $0.4194 |

- **ITEM_04:** order CAM_01 > CAM_02 > CAM_03, priorities 0.763 / 0.633 / 0.303. The supplementary attention_first answer was CAM_01 (0.98).
- **ITEM_07:** same_incident p=0.94 → true. second_view_adds p=0.99 → true. multiview_value 0.80.
- **Evidence examples (model text):**
  - ITEM_02: "crouched atop the brick wall" at 7.2 s, then "upright in the narrow green passage on the opposite side of the wall" at 8.3 s.
  - ITEM_03: gate opened and crossed at about 28–31 s. Its uncertainties state that purpose and authorization cannot be determined.

## 4. P3 → P4 ablation (same model / effort / semantics / adapter; input = CV state vs frames)
| Capability | P3 State | P4 Vision |
|---|---|---|
| Fall (ITEM_01, ITEM_04/CAM_01) | 2/2 | 2/2 |
| Boundary / Entry (ITEM_02, ITEM_04/CAM_03) | 0/2 (fall p 0.58, 0.51) | 2/2 (entry p 0.98, 0.98) |
| Ambiguous Entry (ITEM_03) | fall p 0.70 ✗ | entry p 0.84 ✓ (authorization/intent left unknown) |
| Conflict (CAM_02, ITEM_05, ITEM_06, ITEM_07) | 2/4 | 4/4 |
| Attention Top-1 / Full order | ✓ / ✗ (CAM_01 > CAM_03 > CAM_02) | ✓ / ✓ |
| Same incident (ref true) | p 0.38 → false | p 0.94 → true |
| Second view adds / multiview value | p 0.46 → false / 0.27 | p 0.99 → true / 0.80 |
| API cost / candidate | $0.0109 | $0.4137 (~38×) |
| Primary latency median | 11.0 s (cached-state decision path) | 85.1 s (full visual path) |

**Does this support the compact-state information-bottleneck hypothesis?** Within this diagnostic set: **yes, as strong but small-sample evidence.**

The model, effort, semantics and adapter were held fixed. With frames instead of the compact state, P4 correctly named every boundary/entry case (3/3, including ambiguous ITEM_03) where P3 said "fall". It also recovered the two conflict views P3 missed (CAM_02 and the foliage-limited A view), and both multi-camera judgments.

This is consistent with the compact CV state having lost scene and boundary semantics (walls, gates, crossing) and interaction detail. The decision model was not the binding limit for these cases.

**Caveats:**
- These are 3 entry and 4 conflict assessments from 5 cases; no generalization is claimed.
- The P4 entry-category definition names visible walls, gates and doorways, while P3's said "boundary semantics are not known". That wording matches what each modality can actually observe, but it is a prompt co-variable.
- P4 probabilities are model-generated estimates.

## 5. Cost and latency
| Pipeline | External API cost / candidate |
|---|---|
| P0 Cheap CV rules | $0 (no external API; local CV compute not costed) |
| P1 Decisions (gpt-6-luna) | $0.000474 |
| P2 Clef-Flash | $0.000436 (actual billing likely $0, free allocation) |
| P3 Sol State | $0.010897 |
| P4 Sol Vision | $0.413697 (7-item total $2.8959) |

- **Image tokens:** about 2,450 tokens per 1920×1080 frame at detail=high, inferred from provider usage (159,233 input tokens for 64 frames plus ~2k text tokens; consistent with the 2,040-patch × 1.2 preflight estimate).
- **Cache-write billing:** the provider reported almost all input as `cache_write_tokens` (automatic prompt caching), so it was billed at $2.50/M instead of $2/M. Cost follows that provider usage. At the plain input rate the cost would be about $0.33 per candidate.

**P4 latency medians:**

| Stage | Median |
|---|---|
| Frame decode | 2.9 s |
| Image encode (16 threads) | 11.5 s |
| Round-trip verification | 1.4 s |
| Base64 | 0.6 s |
| API (upload + provider) | 67.6 s (provider processing header about 48 s) |
| Adapter | 2 ms |
| **Full path** | **85.1 s (75.6–108.1)** |

**P4 primary latency is the full visual path. P1/P2/P3 primary latency is the cached-state decision path. A fair latency comparison is pending controlled_latency_v1.**

## 6. Auto diagnostics (P2 evaluator reused unchanged; same normalized_ground_truth_v1)
| | P0 | P1 (v2) | P2 (v2) | P3 | P4 |
|---|---|---|---|---|---|
| Category (9) | 5/9 | 2/9 | 0/9 (raw 5/9) | 4/9 | 9/9 |
| Anchored incidents | 0/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| Attention top-1 / full | ✓/✓ | ✓/✓ | ✓/✓ | ✓/✗ | ✓/✓ |
| same_incident | ✓ | ✓ | ✗ | ✗ | ✓ |
| Contradictions | 2 | 0 | 0 | 0 | 0 |
| Suspected overclaims | 0 | 0 | 0 | 0 | 0 |
| Human review | 4/9 | 9/9 | 5/9 | 8/9 | 9/9 |

These are diagnostic counts, not accuracy. The auto category metric is still borderline against reviewer_01 (3/13 opposite cases).

## 7. Human audit (`evaluation/human_audit_queue.md`)
5 P4 assessments were flagged:
- **1 needs full-video review:** ITEM_03 (ambiguous case).
- **4 need a text check only:** ITEM_02, ITEM_04/CAM_02, ITEM_04/CAM_03 and ITEM_05, all flagged for P3/P4 disagreement.

There were no suspected overclaims, cross-camera identity assertions or very-low-confidence flags. P4's evidence text is model-generated, and wording such as "kicks" and "striking-like movements" (ITEM_06) describes actions, not intent. A human spot check is still advisable before any presentation use.

## 8. Validation
- **Prediction schema:** 7/7 `validate_prediction --result` PASS.
- **Frame refs and camera attribution:** strict per-camera enums plus runtime checks found 0 violations. Timestamps come from deterministic lookup of the frame table.
- **Benchmark integrity:** `validate_benchmark.py` passed before P4, after transport verification, after the freeze, after the run, after the result freeze and after evaluation.
- **Leakage:** PASS (see disclosure). Model-path runtime access found 0 forbidden opens; no CV or compact state was sent; no item ids or labels appear in the request text; no API key was found in 74 files.
- **GT accessed before result freeze:** **no.** Order: p4_frozen → run → leakage_audit → p4_results_frozen → run_auto_eval.
- **Frozen artifacts:** P1/P2/P3/common-adapter-v2 freezes show no drift, and the benchmark is unchanged.

## 9. Disclosures
- **Leakage audit, run 1 FAILed on audit-script false positives only:**
  - (a) The source-id deny pattern `F01` matched inside frame refs F010–F019. Source ids are now word-bounded.
  - (b) The frame-allocation assertion in the local-only `verify_frame_transport.py` was reported as item-specific branching.
  - The audit was revised (r2) and run 2 passed. No model-path file changed.
- **Pre-freeze fix:** `src/access_audit.py` had a backslash dropped by a shell heredoc (SyntaxError). It was restored before any API call.
- **Process log:** the pre-freeze gate events (smoke, transport, preflight, validations) were appended just before `p4_frozen`. Their artifacts carry their own timestamps.
- **Encoder choice:** the lossless WebP effort (q50/m2) was chosen from local timing on canonical frames before any benchmark API call. This is a transport-efficiency choice; all candidate settings were lossless.
- **Frozen label:** the frozen common event_type map labels entry as "…(boundary semantics unknown)". That label is accurate for the state pipelines but not for P4. It is kept unchanged for comparability.
- **Prior GT exposure:** the implementer has seen benchmark GT in earlier phases. P4 semantics come from frozen P1 definitions plus the specified generic prompt, and nothing was tuned after outputs.
