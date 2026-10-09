# P1 — CV State → OpenAI Decisions API (gpt-6-luna)

P1 interprets the **same** P0 Canonical CV observations (`cv-state-v1`) with the OpenAI Decisions API instead of
deterministic rules. Text only (no images). One request per item. P0 conclusions are never sent.

```
P0 states/ITEM_XX.json (cv-state-v1, cached; CV not re-run)
  -> CompactSerializer  (configs/compact_state_v1.yaml)       -> compact_states/ITEM_XX.json (compact-decision-state-v1)
  -> Decisions API      (configs/decisions_questions_v1.json)  -> raw_api/ITEM_XX.json
  -> DecisionAdapter + template PredictionAdapter              -> benchmark_v1/results/p1_decisions/run_ITEM_XX.json
```

## Setup
The API key is read only from the environment or `experiments/.env` (`OPENAI_API_KEY=...`). It is never written anywhere.

## Commands
```bash
cd D:/projects/477/benchmark_v1 && python scripts/validate_benchmark.py
cd D:/projects/477/experiments/p1_decisions
.venv/Scripts/python.exe scripts/build_compact_states.py
.venv/Scripts/python.exe scripts/validate_compact_states.py
.venv/Scripts/python.exe scripts/smoke_test_decisions.py --item ITEM_01   # P0.5 integration only
.venv/Scripts/python.exe scripts/freeze_p1.py                             # refuses to overwrite an existing freeze
.venv/Scripts/python.exe scripts/run_p1.py --all                          # refuses to run if frozen files changed
.venv/Scripts/python.exe scripts/leakage_audit.py
cd D:/projects/477/benchmark_v1 && python scripts/validate_prediction.py results/p1_decisions/run_ITEM_01.json --result
```
`scripts/offline_adapter_test.py` exercises every task type and the refusal path with synthetic answers (no API call).

## Reuse in P2/P3
`src/compact_serializer.py` + `configs/compact_state_v1.yaml` + `schemas/compact_decision_state.schema.json` are frozen
(`freeze/p1_freeze.json`). Send `CompactSerializer.model_input_text(compact)` as the model's evidence.
