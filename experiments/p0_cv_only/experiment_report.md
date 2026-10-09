# P0 CV-only Experiment — Shared Cheap CV + CV-only Baseline (P0-v1)

Run date: 2026-10-07 · run_id `p0_cv_only-v1` · benchmark `477-reasoning-v1` (frozen, unchanged)

This report contains no human grading and no comparison with private ground truth. `human_grading` is `null` in all results.

## 1. Environment

| | |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| Python | 3.12.6 (isolated venv `experiments/p0_cv_only/.venv`; global Anaconda 3.13 env left untouched) |
| PyTorch | 2.14.1+cu126, CUDA 12.6, cuDNN 9.10 |
| GPU | NVIDIA GeForce RTX 3050 4GB Laptop GPU (driver 576.57) |
| CPU / RAM | 13th Gen Intel Core i7-1360P (12C/16T) / 15.7 GB |
| OpenCV / Ultralytics | 5.0.0.93 / 8.4.52 |
| ffmpeg | 8.0 (gyan.dev full build), used only via the benchmark loader |
| Power | **On battery (unplugged) for all timed runs.** This inflates latency and makes it noisy (see §10). |

Why a venv: the global env had a CPU-only torch and no torchvision, so Ultralytics could not import. A venv avoided any destructive global upgrade. Full record: `logs/environment.json`.

## 2. CV model

- **YOLO26n-pose** (`yolo26n-pose.pt`, Ultralytics assets v8.4.0). It is pretrained COCO person + 17-keypoint pose, used as-is with no training or fine-tuning.
- Weights SHA256 `eb3bb8268828aeaf515cec23a4bfafd793944a86fe9af94ba7823609c14522a9`, 7.88 MB (7,878,574 bytes).
- Device: cuda:0. Precision: FP16. Input size: 1280 (letterboxed). conf 0.25, IoU 0.7, max_det 50, batch 16.
- **Why this model:** it was priority 1 in the plan, and it was available and compatible with the installed Ultralytics. One nano network gives person boxes and keypoints in a single pass, which is cheaper and simpler than a separate detector plus pose model. The input size of 1280 (rather than 640) was chosen *a priori* because these are 1920×1080 CCTV frames where people are small. VRAM peak was 470 MB.

## 3. Canonical input protocol

- All frames come from `benchmark_v1/scripts/load_model_input.py::iter_model_frames` (`uniform_total64_v1`). The pipeline adds no sampling of its own.
- Frame allocation: 64 frames for single items, 22+21+21 for attention (ITEM_04), 32+32 for AB (ITEM_07).
- `CanonicalFrameSource` enforces the protocol:
  - it asserts each timestamp matches the loader schedule;
  - it asserts exactly 64 frames are used in total;
  - it hashes the exact RGB bytes per camera (`frame_fingerprint_sha256`).
- Every state records frame numbers, and `validate_states.py` checks them against the canonical schedule.
- Runtime access audit (Python audit hooks, all 7 items × 4 runs):
  - 0 private or label paths were opened.
  - 0 MP4 files were opened directly by Python.
  - The only subprocesses were the loader's `ffmpeg -vf select='eq(n,…)'` decodes.

## 4. Canonical CV State (`cv-state-v1`)

- Schema: `schemas/canonical_cv_state.schema.json` (draft 2020-12, `additionalProperties:false` throughout, nullable fields declared explicitly). SHA256 `445feea6…`.
- CV config: `configs/cv_state_v1.yaml` (SHA256 `efe509eb…`). This file holds only generic observation parameters.
- The state contains observations only. `validation.py` rejects event keys such as `fight_detected`, `fall_detected`, `event_type`, `is_incident`, `physical_contact`.

Structure per camera:

- `sampling`: timestamps, median and max interval, plus an explicit sparse-sampling note.
- `frames[]`: for each detection, the normalized bbox, confidence, normalized COCO-17 keypoints, sparse-link affinity/ambiguity, and posture proxies.
- `detection_summary`.
- `tracks[]`: reliability, detection, geometry, motion, posture, `vertical_transition`, `low_motion`.
- `pairwise_interactions[]`.
- `scene_observations`.
- `quality`.
- `cross_camera`: present only for 2-camera items.

`generator` records the model hash, CV config hash, CV code hash, `external_api_calls: 0` and `llm_or_vlm_used: false`.

Unknown is `null`, never `false`. Examples:
- `boundary_crossing: null` with `boundary_crossing_reliability: "unavailable"`.
- `scene_semantics.zones: null`.
- Transition flags are `null` when a track has fewer than 3 known postures.

`identity_link_confirmed` and `sync_confirmed` are always `false`.

All 7 states were generated, and `validate_states.py` passes for all 7. Across separate process runs the states were byte-identical except for the `generator` code hash, and within each run all 3 repeats were identical.

Caching: per-camera states can be cached under a key of (frame-bytes SHA256, model SHA256, precision, CV config SHA256, CV code SHA256). Across items the canonical frame sets never coincide: ITEM_01 uses 64 frames of its asset while ITEM_04 CAM_01 uses 22, so no reuse was possible. The cache was disabled for all timed runs.

## 5. Sparse tracking strategy

Each camera is processed independently, with no cross-camera identity.

Each frame's detections are matched to active tracks (gap ≤ 3.0 s) by a deterministic Hungarian assignment (SciPy, with a greedy fallback). The affinity combines five weighted terms:

| Term | Weight |
|---|---|
| Timestamp-gated centre distance (body heights per *actual* Δt) | 0.35 |
| HSV-histogram similarity | 0.25 |
| bbox IoU | 0.15 |
| Size similarity | 0.15 |
| Pose-shape similarity | 0.10 |

How uncertain links are handled:
- Links below affinity 0.40 are refused, and the detection starts a new track.
- If the best and second-best affinities differ by less than 0.10, the link is flagged `ambiguous`.
- Fragments are never merged. Plausible continuations are recorded as `fragment_links` with `identity_confirmed: false`.

Each track carries `association_confidence`, `observed_frames`, `visible_fraction`, `max_gap_sec`, `ambiguous_links`, `reliability_score` and a `reliability_label`. The label is `low` if a track has fewer than 3 observations.

No ByteTrack/BoT-SORT, Kalman filter or optical flow is used.

## 6. Feature definitions (key ones)

Units:
- `fh` = frame heights.
- `bh` = body heights, using the reference standing height: the tallest upright sample of that track within ±6 s, otherwise the track's p90 height.
- Every rate = displacement / actual timestamp difference.

**Posture (per detection):** these features are computed only when at least 6 keypoints have confidence ≥ 0.5.
- `torso_angle_deg` (hip→shoulder vs. vertical), `body_orientation_angle_deg` (keypoint PCA axis), hip and shoulder height in the bbox, `leg_extension_ratio`, `body_height_ratio`, aspect ratio.
- `upright_score`, `horizontal_score` and `crouched_score` are each in 0–1.
- Labels: `standing | crouched | low_posture | horizontal | unknown`. The label is `unknown` if confidence < 0.40.
- A bbox-only fallback allows only `horizontal` (aspect < 0.75, confidence 0.45).

**Motion (per track):**
- normalized and body-height speed (mean/max), total and net displacement, `direction_change_count` (>90°), `stationary_fraction`.
- `low_motion`: low-motion fraction, longest low-motion run, `post_transition_low_motion_sec`, `post_transition_low_posture_sec`. All are explicitly defined as "low sampled displacement", not a claim of motionlessness.

**Vertical transition:** the strongest standing→{crouched, low_posture, horizontal} pair within 4 s. It reports:
- `max_downward_change` in bh, using a hip drop when hips are visible, otherwise a bbox-top drop;
- start, end and duration;
- confidence = min of the two posture confidences × link reliability;
- `temporal_resolution_sec`.

**Pairwise (for tracks co-observed in at least 2 frames):**
- centre distance in bh (min/mean plus the full `distance_series`), approach rate, rapid-approach score;
- close fraction and duration (< 1.0 bh), bbox overlap, approach-event count;
- relative motion (overall, when close, max);
- arm extension toward the other person, rapid sampled limb motion;
- `contact_proxy` {score, terms, basis, note}.

**Scene:**
- entry types: present at start, edge entry, appears mid-frame;
- exit types: present at end, edge exit, disappears mid-frame;
- large spatial transitions (≥ 0.35 fh), occlusion candidates, fragment links.

**Quality:**
- brightness, contrast, sharpness, dark-frame fraction;
- mean person bbox area, small-person fraction, pose visibility;
- detection dropout, track fragmentation, occlusion proxy;
- `overall_cv_reliability` with a label.

**Cross-camera:** each clip is mapped to a normalized phase (16 bins). There is no absolute time matching. Computed values:
- person-count, temporal-pattern, motion-peak, posture-transition and incident-signature similarity;
- visibility drop and complementarity;
- `same_incident_similarity_score` (a weighted mean of the available similarities).

## 7. Rule definitions (`configs/p0_v1.yaml`, frozen)

- SHA256 `0f0d25d993786a2614a907efc9481478e1158526cc8570bab6519bc5dbe597a7`.
- Frozen before any prediction existed (`logs/p0_v1_freeze.json`, 17:01 KST). The hash is unchanged at the end of the run.

| Rule | Condition (all thresholds in YAML) | event_type |
|---|---|---|
| fall-like | `upright_to_low_transition` AND conf ≥ 0.45 AND downward ≥ 0.25 bh AND (post low motion ≥ 2 s OR post low posture ≥ 2 s); a fragment-link variant applies ×0.6 confidence | `possible fall` |
| conflict-like | ≥ 2 persons, pair reliability ≥ 0.4, close ≥ 1.5 s and ≥ 30 % of co-observed samples, contact proxy ≥ 0.5, and ≥ 2 of 4 cues (relative motion when close ≥ 0.5 bh/s, ≥ 2 approaches, limb score ≥ 0.5, arm extension ≥ 0.3) | `possible physical conflict` |
| low posture | ≥ 5 known postures, ≥ 60 % low/horizontal, ≥ 5 s, track not used by an incident rule | `low or horizontal posture observed (onset not observed)` |
| movement | edge entry, mid-frame appearance or large transition (track ≥ 3 obs) | `person movement / scene entry observed` |
| fallback | no persons / CV reliability < 0.5 / otherwise | `no person detected…` / `uncertain` / `no incident-like pattern detected` |

**Risk components (each 0–1, deterministic):**
- `severity`: a base value by pattern, plus bonuses for prolonged low motion or for the contact proxy.
- `imminence`: whether the proxy is still present in the last 25 % of the clip.
- `exposure`: (involved + 0.5 × other visible persons) / 4.
- `persistence`: proxy duration / time from onset to clip end.

**Priority:** `priority = 0.35·sev + 0.30·imm + 0.20·exp + 0.15·pers`. Confidence is separate and is **never** multiplied into risk or priority.

**Attention tie-break:** priority desc → severity desc → confidence desc → input camera order.

**Multi-camera:**
- `same_incident` = `same_incident_similarity_score` ≥ 0.60, and each camera has a track with ≥ 3 observations.
- Risk is the element-wise maximum across cameras.

**Explanations:** CV evidence templates only. Diagnosis, intent, authorization and identity are never asserted.

## 8. Reliability handling

- Every claim carries track and camera reliability.
- Low-confidence posture becomes `unknown`.
- Negative claims ("no incident-like pattern") become `uncertain` when CV reliability is < 0.5.
- `human_review_required` is true for incident patterns, low-posture patterns, uncertain results and any confidence < 0.6.
- Uncertainty lists always state:
  - the sampling interval;
  - that scene/boundary semantics are unavailable;
  - for multi-camera items, that there is no sync and no identity link.

## 9. Items processed (P0 predictions; not graded)

| Item | P0 output |
|---|---|
| ITEM_01 | `low or horizontal posture observed (onset not observed)`, is_incident false, sev 0.40 / imm 0.50 / exp 0.25 / pers 1.00, conf 0.74 |
| ITEM_02 | `person movement / scene entry observed`, is_incident false, conf 0.80 |
| ITEM_03 | `person movement / scene entry observed`, is_incident false, conf 0.78 |
| ITEM_04 | Attention queue: CAM_01 (low/horizontal posture, priority 0.49) > CAM_02 (no incident-like pattern) > CAM_03 (movement) |
| ITEM_05 | `person movement / scene entry observed`, conf 0.63 |
| ITEM_06 | `person movement / scene entry observed`, conf 0.81 |
| ITEM_07 | `person movement / scene entry observed`, same_incident **true** (similarity 0.601 vs threshold 0.60), visibility complementarity 1.00 |

None of the 7 outputs fired a `possible fall` or `possible physical conflict` rule.

## 10. Latency

All timed runs were on battery power. Treat the absolute values as an upper/noisy bound and re-measure on AC power before any cost comparison.

**Steady state** (model loaded and warmed up). Each run covers canonical decode, CV inference, tracking/features, state build, rules and serialization. Each item was run 3 times; result `latency_ms` = the per-item median.

| Item | median ms | min | max | CV inference median ms |
|---|---|---|---|---|
| ITEM_01 | 8433 | 7605 | 8508 | 6188 |
| ITEM_02 | 8970 | 8752 | 9018 | 6273 |
| ITEM_03 | 8665 | 8029 | 9020 | 6162 |
| ITEM_04 | 7583 | 7267 | 15632 | 2428 |
| ITEM_05 | 4189 | 4141 | 4267 | 2637 |
| ITEM_06 | 4003 | 3922 | 4041 | 2571 |
| ITEM_07 | 5531 | 5438 | 5672 | 2794 |

Summary of the primary run:
- Median of the item medians: 7583 ms. Range across all runs: 3922–15632 ms.
- Model load: 996 ms (388 ms in the first run).
- Warm-up: 36.0 s. `cold_start_total_ms`: 98.9 s. This is dominated by first-time CUDA/cuDNN kernel loading and DLL import on battery. The model download is excluded.

**Separate latency run** (`debug/reports/latency_report.json`):
- Item medians ranged 4.5–11.5 s (median 6.6 s), with mean GPU utilization only 3–19 %.

Interpretation:
- The pipeline is CPU/decode-bound: ffmpeg decode plus Ultralytics CPU preprocessing of 1920×1080 frames. GPU compute is not the bottleneck.
- ~5–16 frames/s.
- Tracking + features take 20–110 ms per item. The rule engine takes < 1.1 ms.
- The same code varied by about 2× between runs (ITEM_05: 8.1 s in the first run vs 4.2 s in the final run), consistent with battery power throttling.

## 11. External API cost

- External API calls: 0. `external_api_cost_usd = 0`. `input_tokens` and `output_tokens` are `null`.
- `estimated_cost_usd` = `null` in the result JSON. That field denotes total cost, and the local GPU/CPU energy and hardware amortization were deliberately not converted to dollars.

## 12. Prediction validation

- `validate_prediction.py … --result`: **7/7 PASS**. 0 failed.
- `validate_benchmark.py`: PASS before and after every run. No frozen file was changed.

**Schema constraint:** `result.schema.json` only allows `pipeline ∈ {vlm_only, cv_llm}`, and the frozen schema may not be edited. P0 results therefore use `pipeline: "cv_llm"`. P0 is still identifiable:
- `run_id` = `p0_cv_only-v1`;
- `model_id` = `p0_cv_only:yolo26n-pose@ultralytics-8.4.52+rules-p0_v1`;
- `runtime_config.pipeline_actual` = `p0_cv_only`, and `llm_or_vlm_used` = false.

`score_results.py` was **not** run: it reads `private_ground_truth/set04.json`, and grading is pending human review anyway.

## 13. Known limitations

**Posture.**
- Standing→low/horizontal changes *were* captured in the state:
  - ITEM_01 T01: standing until ~6.1 s, horizontal from 8.3 s to 35.0 s (50 horizontal labels);
  - ITEM_04 CAM_01: transition 6.7→8.3 s.
- The fall-like rule still did not fire:
  - ITEM_01: the hip-based downward change was 0.19 bh, below T2 = 0.25. In this camera view the person lies with an inverted torso (~160°), so the hip drops less than the bbox top does.
  - ITEM_04 CAM_01: transition confidence was 0.43, below T1 = 0.45. Its first horizontal samples had a weak score of 0.50, and the sampling interval was 1.67 s.
- Both items fell through to the low-posture rule. Its configured label says "(onset not observed)", which is **inaccurate** for these two items because an onset was observed.
- Per the protocol, the frozen thresholds, feature definitions and label were not changed.
- Candidate P0-v2 changes:
  - use max(hip, bbox-top/head drop);
  - relabel the low-posture pattern by whether a sub-threshold onset exists.

**Interaction.**
- Proximity and relative motion are measurable:
  - ITEM_06: a pair at 0.001 bh minimum distance, 71 % close, limb score 1.0;
  - ITEM_07 CAM_02: 94 % close over 16.4 s.
- The contact proxy stayed at 0.32–0.43, below 0.5. Its bbox term is diluted by all co-observed samples, and relative centre motion of grappling people is small at ~0.5 s sampling.
- Static standing groups (ITEM_04 CAM_02, four people in two close pairs) also look "close". Proximity alone is correctly not enough.
- Sampled limb speed is aliasing-prone.

**Boundary semantics.**
- Generic CV cannot represent a wall, gate or authorization. ITEM_02/03 reduce to "person movement / scene entry observed".
- This is an inherent P0 limitation and was accepted, not patched with ROIs.

**Sparse tracking.**
- Single-person scenes stay a single track: ITEM_01 has 1 track over 57 detections with 0 fragmentation.
- Crowded or occluded scenes fragment:
  - ITEM_07 CAM_01: fragmentation 1.0, 6 tracks, reliability 0.53;
  - ITEM_05: 0.67.
- At 1.67 s intervals (ITEM_04) association weakens further.
- Fragment links are recorded but never merged.

**Multi-camera.**
- Low-level visibility complementarity is expressible: CAM_01 visibility drops in phases 0.44–1.0 while CAM_02 still has persons (complementarity 1.0).
- `same_incident = true` sits exactly at the threshold (0.601 vs 0.60), and the person-count similarity was 0.00. Treat it as weak evidence.

**Data quality.**
- The final AB frames are black, which correctly shows as 0 persons.

**Explanation fix after the first run (decision-neutral).** In the first run, the low-posture evidence template claimed "no standing-to-low transition was observed" even when one was observed below the thresholds. That is a false statement. Only the template was corrected:
- It now states whether a sub-threshold transition was observed (with values), whether none was observed, or whether there were too few samples.
- `event_type`, `is_incident`, risk values, confidence, review flags, attention order, `same_incident` and all CV states were verified **identical** to the first run. Only the text changed, for ITEM_01 and ITEM_04.
- The first-run outputs are preserved in `logs/first_run_archive/`.

## 14. Features likely useful for P1/P2/P3

- Per-detection posture proxies plus keypoints, and the posture timeline per track. These make transitions clearly visible.
- `vertical_transition` together with `low_motion.post_transition_low_posture_sec`. On ITEM_01 these give 26 s of low/horizontal posture after the transition.
- Pairwise `distance_series`, close duration and arm-extension, which show sustained close interaction.
- `fragment_links`, `occlusion_candidates`, the per-track reliability block, and `quality.overall_cv_reliability` for calibrating trust.
- `cross_camera.phase_curves` and the visibility complementarity phases.

## 15. Features that failed or were unreliable

- `contact_proxy.score`: diluted, and it never exceeded 0.65 in practice.
- `rapid_limb_motion_score`: saturates at 1.0 under sparse sampling.
- The hip-based `max_downward_change` under steep or overhead views.
- `post_transition_low_motion_sec`: it breaks on the first post-transition movement sample (0.0 s on ITEM_01).
- `same_incident_similarity_score`: a marginal decision.
- `person_count_similarity` when one view is mostly empty.

## 16. Leakage audit

Command: `scripts/leakage_audit.py` → `debug/reports/leakage_audit.json`. Verdict: **PASS**.

- **Static scan:** forbidden terms appear only in deny-lists, docstrings and a CLI default (`--item ITEM_01`). There are 0 conditional branches on item, asset or source IDs or on labels. `item_id` is used only to load frames and to tag outputs. The rule engine never reads it.
- **Runtime audit:** all 7 items PASS. No private, annotation, README or lock paths were opened. No direct MP4 reads. Only canonical ffmpeg decodes.
- **No source labels, XML, candidate_report or private references were used.** No thresholds were set from benchmark answers.

**Disclosure:** while orienting, the implementer read `benchmark_v1/README.md`. Its "Condition mapping (evaluator only)" section describes the source scenarios. This material was not used in any code path. The CV design, thresholds and rules are generic, and they were frozen before any prediction was produced. The private ground-truth directory was never opened.

## 17. Reproducibility record

| Artifact | SHA256 |
|---|---|
| models/yolo26n-pose.pt | eb3bb8268828aeaf515cec23a4bfafd793944a86fe9af94ba7823609c14522a9 |
| configs/p0_v1.yaml | 0f0d25d993786a2614a907efc9481478e1158526cc8570bab6519bc5dbe597a7 |
| configs/cv_state_v1.yaml | efe509eb7a2b803416d4eb7f4dbe927fb0995189a256264057f8c759d144d173 |
| schemas/canonical_cv_state.schema.json | 445feea651d695bb7d98d8b4c5010aa17fcca692b325034bdc77933a9bf23c81 |

Full runtime record: `runtime_config.json`, plus `runtime_config` inside each result JSON (per-item latency stats, stage medians, compute record, state SHA256, frame-bytes fingerprint, access audit).
