# P3 — Compact Decision State → GPT-6.1 Sol (text-only state reasoning)

This experiment changes only the decision model, relative to P1/P2. It is not a vision experiment: no image or audio is ever sent. That comparison is P4.

```
P1 compact_states/ITEM_XX.json (frozen bytes, read-only; byte-identical P1/P2 input text)
  -> Responses API  POST /v1/responses   model gpt-6.1-sol, reasoning.effort=high, no tools, store=false,
     instructions = configs/p3_prompt_v1.txt + decision definitions rendered from frozen P1 decisions_questions_v1.json
     text.format  = json_schema strict (schemas/p3_decision_output.schema.json)
  -> raw_decision_adapter (canonical raw record, probability_source = model_generated_estimate)
  -> frozen P1 decision_adapter.py + P1 templates (provider-name substitutions only)
  -> frozen common-adapter-v2
  -> benchmark_v1/results/p3_gpt61_sol_state/run_ITEM_XX.json
```

## Commands
```bash
cd D:/projects/477/experiments/p3_gpt61_sol_state
.venv/Scripts/python.exe scripts/offline_adapter_test.py   # no API
.venv/Scripts/python.exe scripts/smoke_test_p3.py          # synthetic neutral states only
.venv/Scripts/python.exe scripts/freeze_p3.py
.venv/Scripts/python.exe scripts/run_p3.py --all
.venv/Scripts/python.exe scripts/leakage_audit.py
.venv/Scripts/python.exe scripts/freeze_results.py
# evaluator only, after the result freeze (reuses experiments/p2_clef_flash/scripts/run_auto_eval.py unchanged):
.venv/Scripts/python.exe scripts/run_auto_eval.py
.venv/Scripts/python.exe scripts/compare_p1_p2_p3.py
```
The API key comes from `OPENAI_API_KEY` or `experiments/.env` and is never written. The model path is audited at runtime: opening private GT,
grading files, P1/P2 results or raw outputs, normalized outputs or evaluation files fails the run.
