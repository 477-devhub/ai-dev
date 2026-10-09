# common-adapter-v2

common-adapter-v2 is a deterministic consistency layer that sits between a decision model's frozen-v1-style decision and the final 477
prediction. It fixes one contradiction that P1-v1 and P2-v1 shared: `is_incident=false` together with `event_type="possible fall"` or `"possible conflict"`.

**It is not calibration.** It leaves all of these unchanged: thresholds, probabilities, category answers, risk, confidence, human_review,
priority, attention order and same_incident. The only prediction field it may change is `event_type`.

| Rule | Condition | is_incident | event_type |
|---|---|---|---|
| R1 | p(incident) < 0.5 | false | `no clear incident` |
| R2 | p(incident) ≥ 0.5, incident-like raw category | true | mapped raw category (P1 event_type_map) |
| R2b | p(incident) ≥ 0.5, raw category `no_clear_incident` | true | `uncertain` |
| R3 | p(incident) ≥ 0.5, category refused/invalid | true | `uncertain (category decision refused)` |
| R4 | p(incident) refused/invalid | false | `uncertain (incident decision unavailable)` |

The threshold is 0.5 and is shared by every model. That is the same value P1-v1 and P2-v1 used. The raw category answer is kept in
`runtime_config.common_adapter_v2.assessments[*].raw_decision` (incident_probability, incident_category,
incident_category_confidence), so the raw answer and the final presentation are stored separately.

## Commands
```bash
PY=../p3_gpt61_sol_state/.venv/Scripts/python.exe
$PY scripts/normalize_p1_p2.py     # offline, 0 API calls; first proves the v1 prediction rebuilds byte-exactly from raw_api
$PY scripts/validate_normalized.py # only *.event_type may differ; protected fields checked; validate_prediction --result x14
$PY scripts/freeze_adapter.py      # freeze/common_adapter_v2_freeze.json (refuses to overwrite)
```

Outputs are written to `normalized/p1/`, `normalized/p2/` (result-schema JSON) and `logs/`. The P1-v1 and P2-v1 files under `benchmark_v1/results/` remain the
official raw experiment records. They are not modified.
