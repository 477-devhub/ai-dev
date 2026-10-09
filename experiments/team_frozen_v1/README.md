# Frozen P1/P4 on team benchmark inputs

Separate experiment using original frozen P1/P4 prompts, adapters and model settings.
This does not use the team common prompt and is not a common-prompt leaderboard submission.
Each of 28 source occurrences is assessed independently with its original allocated images;
the 12 item bundles each retain exactly 64 frames, 768 total. No added images or padding.
CV transport validation follows actual per-source frame counts (10..64); frozen computation is unchanged.

AI-reviewed demo reference is isolated in analysis/reference, never read by inference workers.
Six single-video problems are the primary descriptive result; repeated bundles are reported separately.
Original human-GT triage Test and routing policy remain immutable. No threshold fitting on team data.
Cascade is offline replay; both P1 and P4 execute all source occurrences to record baseline performance.
P1 has no frame-grounded citations. Gate-entry/loitering cannot be separately expressed in the frozen taxonomy.
No person labels are generated. No normal-control false-alarm or routing-saving claims are supported.

Prepare: python scripts/prepare.py
Run: python scripts/workflow.py (original pinned per-model environments launched automatically)
Read: workflow_status.json; analysis/report.md; analysis/summary.json; analysis/per_item.csv; analysis/per_source.csv.
