# P0 — Shared Cheap CV + CV-only Baseline

P0 of the 477 AI Cost–Accuracy Experiment: **no LLM/VLM/external API**. Pretrained YOLO26n-pose +
deterministic rules over a reusable **Canonical CV State** (`cv-state-v1`) that P1/P2/P3 will consume unchanged.

```
canonical frames (load_model_input.iter_model_frames, uniform_total64_v1)
  -> PoseDetector (yolo26n-pose, FP16, imgsz 1280)        src/pose_detector.py
  -> SparseTracker (timestamp-aware Hungarian, per camera) src/sparse_tracker.py
  -> CameraFeatureExtractor + cross-camera comparison      src/feature_extractor.py, src/state_builder.py
  => Canonical CV State  (schemas/canonical_cv_state.schema.json, configs/cv_state_v1.yaml)
  -> P0 RuleEngine (configs/p0_v1.yaml, frozen)            src/rule_engine.py
  -> prediction.schema.json adapter                        src/prediction_adapter.py
```

## Commands (Windows; use the experiment venv)

```bash
cd D:/projects/477/benchmark_v1 && python scripts/validate_benchmark.py
cd D:/projects/477/experiments/p0_cv_only
.venv/Scripts/python.exe scripts/inspect_environment.py
.venv/Scripts/python.exe scripts/smoke_test.py --item ITEM_01
.venv/Scripts/python.exe scripts/run_p0.py --all          # 3 timed repeats/item, states, results, overlays
.venv/Scripts/python.exe scripts/validate_states.py
.venv/Scripts/python.exe scripts/benchmark_latency.py
.venv/Scripts/python.exe scripts/leakage_audit.py
cd D:/projects/477/benchmark_v1 && python scripts/validate_prediction.py results/p0_cv_only/run_ITEM_01.json --result
```

(WSL: replace `D:/` with `/mnt/d/`; the venv is a Windows venv, so recreate it from `requirements.txt` there.)

## Outputs
- `states/ITEM_XX.json` — Canonical CV State per item (`states/_camera_cache/` only if caching is enabled).
- `benchmark_v1/results/p0_cv_only/run_ITEM_XX.json` — result JSON (benchmark result schema).
- `runtime_config.json`, `logs/` (environment, run summary, frozen rule hash, first-run archive),
  `debug/overlays/ITEM_XX/` (track/pose/posture overlays + contact sheets), `debug/reports/` (smoke, latency, leakage).

## Using the state in P1/P2/P3
Feed `cameras[*]` (+ `cross_camera`) to the decision model. Do **not** send `input.item_id` or
`input.benchmark_input_fingerprint` as prompt content (harness metadata only). Unknown values are `null`, never `false`.
See `experiment_report.md` for field definitions and reliability guidance.
