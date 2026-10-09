# 477-reasoning-v1

**Stage 2 — AI Reasoning / Attention Orchestration Benchmark.** Candidate events are already selected. This package tests visual/temporal understanding, risk reasoning, uncertainty, attention and multi-camera evidence. It does not test detector recall/FPR or end-to-end deployment performance. Five human-approved cases, seven execution conditions; no candidate replacement. No external API, CV model or LLM run was performed. Results directories are empty.

## Frozen cases

SET01 S14: normal movement → fall → ground posture, 225.6–260.6s.
SET02 T06: outside wall → wall crossing → inside movement, 252.8–287.8s.
SET03 T03: **256.0–291.0s, 35 seconds**, the minimum allowed 35–45s length. Gate-side looking/direction changes, moving away, final approach, opening/entry (~285–286s) and inside position follow continuously. The initial approach around 212s cannot fit with actual entry in a 45s clip; the final re-approach is included. Head/direction changes are visible; criminal intent and authorization are not established. Selection was made from source pixel inspection, not the XML label. Source selection notes and review crops are private; evaluation is uncropped full frame.
SET04 R01: hypothetical concurrent independent alerts. CAM_01=S14, CAM_02=F01, CAM_03=T06. Reference order **S14 > F01 > T06** is **477 project-defined human reference**, not AI Hub ground truth. No numerical risk targets. Recording simultaneity is not claimed.
SET05 MV05/ph_e2069: whole CAM A/c1 and CAM B/c2 source durations, including short last black frames. No official precise synchronization. Compare A, B and AB; key increment is AB minus best single, not AB minus A alone.

| Encoded media | Source range | Actual duration |
|---|---|---|
| set01_swoon.mp4 | 225.600–260.600s | 35.000000s |
| set02_trespass.mp4 | 252.800–287.800s | 35.000000s |
| set03_ambiguous.mp4 | 256.000–291.000s | 35.000000s |
| set04_cam_b_fight.mp4 | 116.500–151.500s | 35.000000s |
| set05_cam_a.mp4 | 0.000–30.633s | 30.633008s |
| set05_cam_b.mp4 | 0.000–31.833s | 31.833333s |

## Media and privacy

Six source clips encoded once with libx264 CRF 18, medium, Lanczos 1920×1080, CFR 30 FPS, yuv420p, no audio, metadata stripped. Four original single-camera sources were 3840×2160 at 30000/1001 FPS, so scaling and FPS normalization are deliberate. MV05 originals were H.264 1080p/30 FPS; whole temporal clips retained under the same encoding recipe. All conditions and pipelines reuse the exact same output bytes. Encoder version/command, original metadata, source ranges and hashes are private provenance.

Requested descriptive media names are human-facing only. SET04 CAM A/C are byte-identical hardlinks (copy fallback) of SET01/02, never re-encoded. Six additional asset_01.mp4…asset_06.mp4 aliases are also hardlinks/copy fallback. **Only opaque aliases in public_manifest.json are allowed for harness loading; upload display names are generic CAM_01, CAM_02, CAM_03.** Do not send directory listings, descriptive filenames, README, BENCHMARK_LOCK.json or private_ground_truth to models.

model_input/scenarios.json contains only opaque item/asset IDs, generic camera IDs, neutral task and frozen sampling protocol. prompt_v1.txt is English and common to both pipelines. There is no event class list or same-incident answer in it. Observation time is clip-relative for each camera, never annotation time or synchronized absolute time.

Source labels/XML/captions/answers/CoT, source filenames/IDs, evidence frame annotations, expected ranking, clip rationale and grading references live under private_ground_truth only. Each set JSON explicitly separates source_ground_truth, human_verified_observation and project_defined_reference. The standalone load_model_input.py has no private-data imports or paths; it reads only public artifacts and evaluation media. The combined benchmark folder is for evaluators, not a model upload bundle.

## Fixed fair input protocol

Primary protocol **uniform_total64_v1**: exactly 64 decoded RGB frames per item, allocated equally among cameras with remainder to manifest order. Uniform frame selection includes clip endpoints: round-half-up(j*(N-1)/(K-1)). Single A/B receive 64 frames; AB receives 32 per view. Attention receives 22/21/21. Timestamps are selected output-frame number divided by 30. Thus both pipelines see identical pixels and timeline, and multi-view does not get twice the total frame budget. This matched-budget comparison has lower per-camera temporal density in multi-view; interpret missing detail accordingly. Native-video transport or a per-camera budget is a different protocol requiring an explicit new version/experiment definition, not a silent replacement.

load_model_input.load_item returns harness-only media locators, expected fingerprint, generic prompt and task-specific schema. **iter_model_frames(item_id)** streams canonical frames in memory via ffmpeg, returning only RGB bytes, generic camera ID and neutral relative timestamp. It writes no frames and calls no models. The harness must actually send these canonical frames, not upload the whole MP4 and report a fictional 64-frame fingerprint. Paths and item IDs stay in harness metadata, not prompt text. CV+LLM may compute features from exactly these frames; no additional source frames, private answers or annotations may be introduced. Record CV checkpoints/configuration and LLM/model settings in runtime_config. Use the same text/schema, decoding, frame schedule and comparable generation settings. Input hashes and frame indices are mandatory in measured results. End-to-end reasoning latency/cost should include all CV and LLM stages, preprocessing and upload as declared in runtime_config; do not compare partially timed pipelines.

## Condition mapping (evaluator only)

- ITEM_01=SET01; ITEM_02=SET02; ITEM_03=SET03.
- ITEM_04=SET04, CAM_01/CAM_02/CAM_03 as above.
- ITEM_05=MV05_A/CAM_01; ITEM_06=MV05_B/CAM_02; ITEM_07=MV05_AB/both.

## Schemas and scoring

prediction.schema.json: single assessment, three-camera attention assessments/queue, or multi-camera assessment with same_incident, camera_evidence, cross_camera_summary and additional_information_from_second_view. Runtime validator selects the required shape by item, checks timestamps and camera attribution, and forces exactly three unique ranking cameras/ranks. event_type is free text: no label choices supplied. All risk components and confidence are predictions bounded 0–1, never numerical ground truth.

result.schema.json includes pipeline, run/model/config, exact input fingerprint, prediction, human_grading and nullable latency_ms/input_tokens/output_tokens/estimated_cost_usd. No fake result or prediction is provided. For a real future run, use null for unavailable usage/latency/cost rather than invented values. human_grading is null until a named reviewer assigns the four 0/1/2 scores (Event, Temporal, Evidence, Uncertainty); anchors are in private set files. A second reviewer/adjudication is advisable; values are project rubric, not official AI Hub metrics. Risk reasoning is inspected through reason/evidence and human notes, with no numerical risk target.

score_results.py validates actual results and their exact fingerprints before scoring. It does not invent semantic grades, use a judge model or fill missing grades with zero. Report scenario scores and x/5 with explicit coverage; never percent accuracy/generalization from these five cases. SET05 A/B are additional conditions; main five-case summary counts SET01–04 and SET05 AB. Attention Top-1 and full-order compare the private project reference. Multi-view Increment = AB rubric total (0–8) minus max(A total, B total); per-metric increments also reported. Scores remain null/pending until the three conditions are human-graded.

Six overclaim types: unsupported diagnosis, criminal intent, authorization, identity, weapon, cross-camera identity. Human flags require an exact output quote and visual-support explanation. Lightweight keyword screening adds **suspected** review flags only; it cannot establish unsupportedness, may miss paraphrases or confuse negation, and never counts as confirmed without human adjudication. No official severity/risk/priority/confidence ground truth was invented.

## Commands

From D:/projects/477/benchmark_v1 (WSL mapping /mnt/d/projects/477/benchmark_v1):

```bash
python scripts/validate_benchmark.py
python scripts/build_benchmark.py
# Frozen build only validates, never rewrites. Actual changes require a new benchmark_v2 package.
python scripts/load_model_input.py ITEM_07
# Future real predictions/results only:
python scripts/validate_prediction.py results/vlm_only/run_ITEM_01.json --result
python scripts/score_results.py results/vlm_only/run_*.json --output results/vlm_only/summary.json
```

On Windows use installed Python with jsonschema (currently D:/Users/suncastle/anaconda3/python.exe). ffmpeg/ffprobe must be on PATH; no packages or models installed here. PowerShell wildcard expansion for score_results is not guaranteed: pass explicit filenames or use Python/glob to enumerate; summary.json is an aggregate, not a result-schema input.

## Lock and protection

BENCHMARK_LOCK.json fixes SHA256, duration, frame count, encoding and all reusable/opaque media files; it also hashes prompt, schemas, scripts, private references and review artifacts. Validation fails for changed bytes, durations, hashes, missing files, private hints/public source filenames, model loader private imports/paths or invalid schema definitions. Results and Python cache are outside locked artifacts. Do not alter the lock to conceal changed media. Source video before/after hashes and previous selection artifact hashes were checked at freeze, original ZIPs/media/annotations were not edited. Runtime validation is portable and does not require original archive availability. Semantic leakage validation complements exact schema/key allowlists and hashes; it cannot audit an external uploader implementation or model provider hidden preprocessing.

All writes are under benchmark_v1. Storage checked before media encoding (>2 GiB headroom required). Original large source videos were not copied wholesale except temporal content needed for approved short clips. No automatic temp deletion. Private inspection images/caches are frozen audit material. Rebuilding on another ffmpeg/platform may not reproduce byte-identical encodes; the frozen hashed media are the authoritative identical inputs. Keep v1 read-only in comparison runs and create v2 for changes. These few selected/staged CCTV examples are a diagnostic benchmark, not deployment safety evidence.
