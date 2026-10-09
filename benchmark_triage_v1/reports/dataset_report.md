# 477-TRIAGE-NORMAL-V1 DATASET REPORT

Human reviewed: 43 / 43 priority

Primary:
- CLEAR_NORMAL: 13
- HARD_NEGATIVE_NORMAL: 11
- ANCHORED_DANGER: 13

Challenge:
- AMBIGUOUS: 6

Additional human review required: NO

Only candidate_id and review_label are required human GT. Auxiliary fields are OPTIONAL / NOT USED FOR SCORING. No human label was modified, inferred or generated; 72 unreviewed labels remain blank. reviewer_01 was filled only where blank, with backups, following the user's confirmed reviewer provenance.

Human labels were manually assigned, but per-item confidence was not collected consistently.

No confidence, summary, subtype or item timestamp was fabricated. Existing optional values were retained; only populated optional fields are exported to private GT.

Batch provenance timestamp: 2026-10-09T07:49:42.043965+09:00 (priority CSV modification time before metadata update, not per-candidate time).

## Class counts and split for approval

| Split | CLEAR_NORMAL | HARD_NEGATIVE_NORMAL | ANCHORED_DANGER | Total |
|---|---:|---:|---:|---:|
| calibration | 7 | 5 | 3 | 15 |
| test | 6 | 6 | 10 | 22 |

Primary: 37; challenge: 6; primary scenes: 18; all priority scenes: 18; scene leakage: 0.

Independent test scenes (9): SCN_08, SCN_09, SCN_10, SCN_13, SCN_14, SCN_15, SCN_16, SCN_17, SCN_18.

Related scenes (9): SCN_01, SCN_02, SCN_03, SCN_04, SCN_05, SCN_06, SCN_07, SCN_11, SCN_12.

## Split policy and trade-offs

Exhaustive deterministic split search over existing split_group_id groups, which keeps shared site/actor/take groups together and guarantees scene separation. Priority order: all classes present in both splits, closest sample count to 40% calibration, related scenes in calibration and independent scenes in test, class fraction balance, sorted group tie break. Human confidence is never used.

Selected split groups: `{"SPG_01": "calibration", "SPG_02": "calibration", "SPG_03": "calibration", "SPG_04": "test", "SPG_05": "test", "SPG_06": "test", "SPG_07": "test", "SPG_08": "test"}`.

Related groups in test: ['SPG_05']. All 16 independent primary candidates can be kept in test, but that alone yields only 43.2% of primary. Reaching about 60% test while keeping each physical group intact requires related candidates in test; these are flagged. Test is not wholly independent of reasoning-v1.

## Auxiliary warnings only

- review_confidence: 1
- observable_summary: 21
- normal_subtype: 30
- hard_negative_type_if_any: 32
- danger_type_if_any: 30
- ambiguous_reason: 40
- reviewed_at: 0
- applicable_subtype_missing: 3

## Validation and freeze readiness

Technical readiness: YES. See validation.json for label validity, ID membership, label snapshot integrity, media hashes, public/private separation, derived mapping and scene cap. Missing auxiliary data does not block freeze.

Frozen after explicit user approval of the generated class counts and split manifest. No additional video review is required. See freeze_completion_report.md.

Freeze is complete. Run frozen P1 + frozen P4 once on the primary set under the calibration-only protocol, then perform one final test evaluation. No P1/P4 output was accessed during this finalization.

## Files

public_manifest.json contains only 37 primary model inputs. challenge_public_manifest.json contains only 6 ambiguous model inputs and must not enter the primary denominator. private_ground_truth/triage_labels.json holds the human GT for both. review/priority_review_manifest.json registers the 43 human-reviewed IDs and label digest.
