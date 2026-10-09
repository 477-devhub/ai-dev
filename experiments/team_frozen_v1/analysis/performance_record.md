# Team benchmark: frozen P1/P4 separate experiment

AI-reviewed demo reference; not human gold. Six unique videos reused across 12 items.

Original frozen prompts/models/adapters maintained. Team common prompt was not used: not eligible for the common-prompt leaderboard.
Each source is run independently using exactly its allocated frames. No synchronization/identity assumptions. No threshold refit.
Frozen taxonomy cannot separately encode gate entry or loitering. Fixed projection was locked before inference.

| Model | Six single-source primary | All 28 occurrences (descriptive only) |
|---|---:|---:|
| p1 | 2/6 (33.3%) | 9/28 (32.1%) |
| p4 | 5/6 (83.3%) | 22/28 (78.6%) |
| cascade | 5/6 (83.3%) | 22/28 (78.6%) |

## Execution
{
  "p1": {
    "success": 28,
    "retry_count": 0,
    "api_error_fallback_count": 0,
    "refusal_jobs": 0,
    "estimated_api_cost_usd": 0.0082115,
    "measured_full_harness_ms_sum": 127092.41
  },
  "p4": {
    "success": 28,
    "retry_count": 0,
    "api_error_fallback_count": 0,
    "refusal_jobs": 0,
    "estimated_api_cost_usd": 5.162378,
    "measured_full_harness_ms_sum": 1539040.72
  }
}

Cascade is an offline replay of the prior locked policy; P4 actually executed all 28 source jobs. No measured routing savings are claimed.
P1 has no frame-specific evidence references; none were fabricated. Object detection scores were not measured in this run.
No normal controls: normal false-alarm rate, unnecessary-call rate and routing savings effectiveness are unmeasurable.
Prior human-GT final Test outputs and thresholds remain unchanged. No human labels were generated.

## Routing replay against reviewed call-need reference

| Group | Would invoke P4 | Required calls missed | Final operator queue |
|---|---:|---:|---:|
| single_source_primary | 6/6 | 0/6 | 6 |
| all_occurrences | 28/28 | 0/28 | 27 |

Call-need reference is not a binary danger/normal label. Operator queue size is a count, not a human-GT recall score.

## API execution and cost

| Model | Successful requests | Median API seconds | Estimated USD |
|---|---:|---:|---:|
| p1 | 28 | 0.29 | 0.008212 |
| p4 | 28 | 44.59 | 5.162378 |

Cost uses actual API token usage and frozen historical pricing, not invoice actual. API timing excludes CV and image preparation.

## Transport incident

Initial sandboxed P4 connection failed before any HTTP response or prediction (3 transport attempts). Records are retained in transport_failure_01. After approved network access, the evaluation succeeded. Successful-run retry counts exclude that initial connection sequence; no fallback prediction was generated.

Prior human-GT benchmark (74 frozen files), final Test report and policy hashes were verified unchanged; see prior_freeze_verification.json.
