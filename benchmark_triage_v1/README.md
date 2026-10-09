# 477-triage-normal-v1

This is an independent benchmark for the **NORMAL branch** of the 477 two-stage cascade. It asks one question: which screens can Stage 1 safely say an operator does *not* need to see?

It is separate from `477-reasoning-v1`, which is positive-only and diagnostic. **No P0–P4 / LLM / VLM API was called to build it.**

**Current protocol: priority human GT.** A person reviewed 43 priority candidates: 13 CLEAR_NORMAL, 11 HARD_NEGATIVE_NORMAL, 13 ANCHORED_DANGER and 6 AMBIGUOUS. The remaining 72 candidates remain unreviewed and are excluded. No additional video review is required. See `reports/priority_gt_report.md` for build, split and technical readiness. Freeze still follows class-count and split approval.

## Priority protocol (current)

Only `candidate_id` and `review_label` are required human GT. Confidence, summaries, subtype and timestamps are optional and never used for primary inclusion, splitting or scoring. Existing human labels are immutable. Blank reviewer metadata may be filled with `reviewer_01` under the user's confirmed single-reviewer provenance. Missing confidence is never replaced with HIGH.

```bash
python benchmark_triage_v1/scripts/finalize_priority_gt.py
python benchmark_triage_v1/scripts/validate_human_labels.py --priority
python benchmark_triage_v1/scripts/build_benchmark.py --priority
python benchmark_triage_v1/scripts/validate_benchmark.py
python benchmark_triage_v1/scripts/build_report.py
```

Primary: all 37 human CLEAR_NORMAL / HARD_NEGATIVE_NORMAL / ANCHORED_DANGER items. Challenge: 6 AMBIGUOUS items in a separate public manifest and private GT array, outside the primary metric denominator. The builder ignores confidence and keeps every eligible priority label. It applies a combined max 3 per scene and splits by physical site/actor/take groups, guaranteeing no scene leakage. `review/priority_review_manifest.json` registers selected IDs and the immutable label digest. `review_status.json` identifies its validation scope.

Public manifests contain model inputs only. Human labels and derived binary/operator references stay in private GT. Review the compact class/split summary in `reports/priority_gt_report.md`, approve class counts and split in `review/approvals.json`, then run `freeze_benchmark.py`. Approval is manifest review, not another video review. The default non-priority validator/build path below remains the legacy full-queue protocol.

## Principles
- **Selection never uses model results.** No P0–P4 prediction, P1 failure, P4 result, cascade threshold or evaluator output is read by any script. Candidates come from:
  - source timing,
  - visual scene identity,
  - generic CV discovery features (person count, motion, low posture, close pair, speed, brightness),
  - seed 477.
- **The scene is the unit, not the clip.**
  - `scene_group_id` is the camera view (background); at most 3 final clips per view.
  - `split_group_id` is the camera views plus staged takes (same site, actors or session). It is the calibration/test split unit and never spans both splits.
- **Source labels are not GT.** AI Hub `swoon` / `fight` / `trespass` only located candidates. Final labels (`CLEAR_NORMAL`, `HARD_NEGATIVE_NORMAL`, `ANCHORED_DANGER`, `AMBIGUOUS`) are human-only.
- **Pre-event ≠ normal.** Pre-event windows keep a ≥5 s buffer from every annotated action and still require human verification.
- **No re-encode.** Clips are stream-copied from a keyframe of the original source. Source and clip SHA-256 values are recorded in `review/clips/clip_manifest.json`.
- **Read-only inputs.** `benchmark_v1/`, `experiments/*` and the raw data are only read. ZIP members are copied into `_work/source_cache/`, a working cache that is not part of the benchmark.

## Layout
| Path | Content |
|---|---|
| `candidate_pool/candidate_sources.json` | Every local source video, its annotation, usable regions, reasoning-v1 relation and license note |
| `candidate_pool/candidates.csv` | Every generated 35 s window with features, filter and dedup status |
| `candidate_pool/dedup_report.md` | Counts before and after dedup; per-view table |
| `manifests/scene_manifest.json` | Camera views, split groups, visually reassigned sources |
| `manifests/source_manifest.json` | Per-source scene and split assignment |
| `manifests/split_manifest.json` | Written by `build_benchmark.py` after review |
| `review/human_review_queue.csv` | **The file the reviewer fills** |
| `review/human_review_queue_reviewer2.csv` | Optional independent second review |
| `review/human_review_guide.md` | Label definitions, confidence policy, allowed vocabulary |
| `review/contact_sheets/`, `review/clips/` | 16-frame sheet and exact clip per candidate |
| `review/review.html` + `scripts/serve_review.py` | Local review UI that saves into the CSV |
| `private_ground_truth/triage_labels.json` | Evaluator-only GT, with `must_surface_to_operator` (after review) |
| `public_manifest.json`, `media/` | Model-visible items: generic ids, `uniform_total64_v1` frame schedule (after review) |
| `reports/` | Dataset, diversity, leakage and validation reports |

## Pipeline
```
scripts/discover_sources.py        source inventory (+ ZIP members -> _work/source_cache)
scripts/sample_frames.py [k/n]     keyframes (~1 fps) -> _work/frames
scripts/cv_features.py             (P0 venv python) generic person/pose/motion features -> _work/features
scripts/build_candidate_pool.py    windows, scene grouping, dedup, review-queue selection
scripts/extract_windows.py         stream-copy clips for review
scripts/build_contact_sheets.py    4x4 sheets
scripts/build_report.py            reports
----------------------------- HUMAN REVIEW (review/human_review_queue.csv) -----------------------------
scripts/validate_human_labels.py   label policy check, reviewer agreement -> review/review_status.json
scripts/build_benchmark.py         HIGH-confidence primary set, max 3/scene, scene-level calibration/test split
scripts/validate_benchmark.py      section-51 checks -> reports/validation.json
(write review/approvals.json)      class-count + split approval by a person
scripts/freeze_benchmark.py        BENCHMARK_LOCK.json (refuses unless every lock condition holds)
```

## How to review
```bash
python scripts/serve_review.py
```
Open the printed URL and follow `review/human_review_guide.md`. A second reviewer runs:
```bash
python scripts/serve_review.py --reviewer2
```
Then run:
```bash
python scripts/validate_human_labels.py
```

After freeze, nothing may change. Any fix becomes `477-triage-normal-v2`.
