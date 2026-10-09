# P2 — Frozen Compact State → Cloudflare Workers AI Clef-Flash

P2 changes **only the decision model**. Canonical frames, cheap CV, `cv-state-v1`, the `compact-decision-state-v1` bytes, the
semantic questions, the adapter (thresholds, confidence formula, score normalization, priority weights, tie-break, event_type
map) and the evidence/uncertainty templates are all P1's frozen artifacts. They are read-only and hash-checked against
`experiments/p1_decisions/freeze/p1_freeze.json`.

```
P1 compact_states/ITEM_XX.json (frozen bytes, read-only)
  -> state = P1 preamble + "\n\n" + compact JSON   (byte-identical to the P1 Decisions input)
  -> P1 decisions_questions_v1.json -> question_adapter (predicate->noul, choices->criteria{}, levels->criteria[])
  -> POST /accounts/{ACCOUNT_ID}/ai/run/@cf/cloudflare/clef-flash   (direct REST, no AI Gateway, 1 request/item)
  -> clef_adapter (wire-format normalization) -> P1 decision_adapter.py (frozen bytes)
  -> P1 prediction_adapter.py templates (frozen bytes + provider-name substitutions only)
  -> benchmark_v1/results/p2_clef_flash/run_ITEM_XX.json
```

## Credentials
`CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` are read from the environment, falling back to `experiments/.env`. They
are never written anywhere. `smoke_test_clef.py` and `leakage_audit.py` scan every artifact and result for them.

## Commands (Windows paths. WSL equivalent: /mnt/d/projects/477)
```bash
cd D:/projects/477/benchmark_v1 && python scripts/validate_benchmark.py
cd D:/projects/477/experiments/p2_clef_flash
.venv/Scripts/python.exe scripts/inspect_cloudflare_schema.py   # live model schema + catalog pricing -> logs/
.venv/Scripts/python.exe scripts/offline_adapter_test.py        # P1 question parity + adapter paths (no API)
.venv/Scripts/python.exe scripts/smoke_test_clef.py             # synthetic neutral state only (no benchmark item)
.venv/Scripts/python.exe scripts/freeze_p2.py                   # refuses to overwrite / refuses if benchmark outputs exist
.venv/Scripts/python.exe scripts/run_p2.py --all                # refuses if P1 or P2 frozen hashes drift
.venv/Scripts/python.exe scripts/leakage_audit.py
.venv/Scripts/python.exe scripts/freeze_results.py              # validate_prediction --result x7, then hash manifest
cd D:/projects/477/benchmark_v1 && python scripts/validate_benchmark.py
# evaluator only, after the results freeze:
cd D:/projects/477/experiments/p2_clef_flash
.venv/Scripts/python.exe scripts/build_auto_ground_truth.py
.venv/Scripts/python.exe scripts/run_auto_eval.py
.venv/Scripts/python.exe scripts/compare_p1_p2.py
```
`logs/process_audit_log.jsonl` records the order of these steps (model run → leakage audit → result freeze → GT access).

## Model path vs evaluator
Model path: `src/*`, `run_p2.py`, `smoke_test_clef.py`. It may read only the P1 frozen state/config files, the P0 state
files (only for the result `input_fingerprint`, which is never sent) and the benchmark schemas. A Python audit hook fails
the run if it opens private GT, human grading, P0/P1 results, P1 raw API files, media, or `evaluation/`.
Evaluator: `build_auto_ground_truth.py`, `run_auto_eval.py`, `compare_p1_p2.py`. These run as separate processes and only
after `freeze/p2_results_manifest.json` exists. They never write to results or to `human_grading`.
