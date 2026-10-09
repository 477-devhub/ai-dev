# Initial transport failure

The first sandboxed P4 request for P001_SRC01 failed with APIConnectionError on all three transport attempts (retry_count=2). No HTTP response, prediction, or valid model result was received. Those records and logs are preserved in transport_failure_01/. The user-authorized evaluation was relaunched with approved network access and unchanged locked scripts, model settings, prompts, taxonomy projection and routing thresholds.

Execution statistics in analysis/summary.json describe the successful evaluation run. They exclude this initial failed connection sequence; read this note alongside the summary. API-failure fallback predictions were not generated.
