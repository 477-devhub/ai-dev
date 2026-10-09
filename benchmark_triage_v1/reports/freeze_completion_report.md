# Benchmark freeze complete

User approved the existing class counts and split in this chat on 2026-10-09 (Asia/Seoul).

- Human labels: CLEAR_NORMAL 13, HARD_NEGATIVE_NORMAL 11, ANCHORED_DANGER 13, AMBIGUOUS 6.
- Primary: 37; calibration: 15 (7 / 5 / 3); test: 22 (6 / 6 / 10); separate challenge: 6.
- Frozen files: 74. Label, media, public/private separation and scene leakage checks: PASS.
- Scene/site-actor group leakage: 0. Additional human review: NO.
- All human labels and existing confidence/summary/timestamp values are preserved.

## Evaluation protocol

Routing policy and thresholds use only calibration data. Test predictions cannot be generated before the calibration-selected routing policy is locked. Test 22 is evaluated once; no threshold adjustment after viewing test metrics. Ambiguous challenge is excluded from primary metrics and calibration.

Calibration contains only 3 danger examples. T_danger is not finely optimized. The inference harness predeclares a conservative 0.90–1.0 range and fixes T_danger=1.0 with the direct-danger bypass disabled, sending high/uncertain scores to P4. Only the conservative normal-suppression threshold is compared on calibration with uncertainty guards; all-to-P4 is the fallback. Zero observed misses on 3 calibration dangers is not a safety guarantee.

## Frozen model execution

Existing frozen P1-v1, P4-v1 and common-adapter-v2 files passed their hash checks. The old runners are bound to the 7-item reasoning-v1 benchmark; a separate harness connects only this benchmark's public pixels/CV inputs and writes only experiments/triage_frozen_v1 outputs. Frozen prompts, models, transports and decision adapters are unchanged. The new result envelope supports TRIAGE IDs without changing the original reasoning-v1 schemas. P1 uses generic CV observations only; P4 uses 64 canonical native-resolution frames and the original lossless WebP transport. Model workers reject reads of GT/review/evaluator directories.

Completed model outputs are reused on resume; existing attempts cannot silently be repeated. Test workers print completion status only. Calibration and test GT are stored in separate evaluator-only files.

## Validation command

python experiments/triage_frozen_v1/scripts/verify_benchmark_lock.py

The original frozen validator CLI has a formatting bug when a valid lock produces a list-valued detail. Its underlying checks pass; the new wrapper runs those unchanged checks and reports them without editing any frozen script.
