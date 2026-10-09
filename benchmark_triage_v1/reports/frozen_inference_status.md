# Frozen inference execution status

Freeze: COMPLETE. All 74 benchmark lock hashes and technical validations pass.
Explicit external-transmission authorization: recorded in experiments/triage_frozen_v1/external_api_authorization.json.

Execution is continuing through a single background workflow. The initial P4 runner and CV runner are reused; model outputs are not discarded or rerun. The workflow starts P1 as CV states become available, waits for both calibration model runs, locks the routing policy using calibration only, then starts test inference and performs one final test evaluation. A technical failure stops advancement and is recorded in workflow_status.json; no fake output or automatic repeat inference is created.

Current status snapshot:

{
  "updated_at": "2026-10-09T09:42:24+09:00",
  "stage": "calibration",
  "state": "RUNNING",
  "expected": 15,
  "completed": {
    "p1": 11,
    "p4": 3
  },
  "test_evaluation_completed": false,
  "routing_policy_locked": false,
  "post_test_retuning": false
}

Live status: experiments/triage_frozen_v1/workflow_status.json
Logs: experiments/triage_frozen_v1/logs/
Final policy: experiments/triage_frozen_v1/routing_policy_lock.json (created only after calibration)
Final test report: experiments/triage_frozen_v1/analysis/final_test_evaluation.json (one evaluation only)
Final cascade report: experiments/triage_frozen_v1/analysis/cascade_report.md

The conservative danger threshold range and disabled direct-danger bypass were declared before predictions. The test set has not been used for threshold selection. No human label was changed.
