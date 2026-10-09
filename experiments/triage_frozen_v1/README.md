# Frozen triage P1/P4 evaluation

The benchmark is frozen unchanged. The harness and search plan were locked before any predictions.

1. Run calibration: python experiments/triage_frozen_v1/scripts/run_stage.py --stage calibration
2. This creates routing_policy_lock.json from calibration only.
3. Run test: python experiments/triage_frozen_v1/scripts/run_stage.py --stage test
4. The final 22-item evaluation is written once to analysis/final_test_evaluation.json. Never retune after test.

Original pinned per-model venvs are used. Existing frozen P1/P4 prompts and adapters are loaded unchanged. Original experiment outputs are not overwritten. Public model input is separated from evaluator-only analysis/. Failed attempts are recorded and block silent reruns.

T_danger is not fit against three calibration dangers: direct-danger bypass disabled, conservative range 0.90–1.0, fixed 1.0. T_normal grid is predeclared as 0 / 0.01 / 0.025 / 0.05 with strict normal/uncertainty guards. All-to-P4 is the fallback. Challenge 6 is excluded from the primary run.

The initial harness lock was preserved before a pre-inference test-fixture correction. Only nullable mock probabilities and workspace-local test temporary directories changed; no production code, model, prompt, protocol or benchmark changed.
