# common-adapter-v2 — report

**Status:** COMPLETE. Frozen at `freeze/common_adapter_v2_freeze.json`:
- `config/adapter_v2.json`: `dd04161724a92874f242a93560877dd3ea44485773a35815c67dec81fcb1f8e9`
- `src/common_adapter_v2.py`: `4f274d6d91d178083a2c7c7bf78f507cb8112bba085d78f971d7137e7c1a11de`

## What was done
- Normalized P1-v1 and P2-v1 offline from their stored `raw_api` answers. No API calls were repeated.
- First, the frozen P1 decision adapter and templates rebuilt each v1 prediction. All 14 rebuilds were byte-identical to the stored v1 result (`offline_rebuild_equals_v1=true`).
- The v2 rule was then applied to the stored v1 prediction.

## Changes
| | P1 | P2 |
|---|---|---|
| event_type changed | 2 (ITEM_02, ITEM_03: fall → no clear incident) | 5 (ITEM_01, ITEM_02, ITEM_04/CAM_01, ITEM_04/CAM_02, ITEM_06 → no clear incident) |
| Internal contradictions (auto evaluator) | 2 → 0 | 4 → 0 |
| Raw categories preserved | yes | yes |
| Risk / human_review / priority / attention order / same_incident changed | no | no |

`validate_normalized.py` passed all 14 files. The only changed paths are `*.event_type`. All 14 files pass benchmark `validate_prediction --result`. The v1 results and raw_api
files are byte-unchanged.

## Interpretation note
For P2, applying v2 lowers the *final* event-category match from 5/9 to 0/9 (raw-category match stays 5/9). This is because every P2
p(incident) is below 0.5, so every final event_type becomes `no clear incident`. The P2 category signal is still available in the raw category field.
Reports should therefore show both the raw category answer and the final presentation.
