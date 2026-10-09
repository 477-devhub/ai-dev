# Dedup report — 477-triage-normal-v1 candidate pool

| Stage | Count |
|---|---|
| Candidate windows before dedup | 709 (pre-event 519, post-event 62, event 128) |
| Removed: same source video as 477-reasoning-v1 | 30 |
| Removed: too few frames / black or unusable | 0 |
| Identical-hash duplicates (person-free windows; identical 4-frame perceptual dHash in the same view; not byte-identical media) | 2 |
| Near duplicates (person-free windows, all 4 frame dHash within 6 bits) | 114 |
| Kept after dedup | 563 |
| Same-scene groups (visual camera views) | 20 |
| Physical split groups (views + shared staged takes) | 9 |
| Sent to human review (scene caps + diversity selection) | 115 |

**Why the scene count is small.**
- Hundreds of windows come from very few backgrounds.
- AI Hub 171 repeats the same staged camera view across takes (e.g. 710-2…710-6), seasons and cameras.
- A window is therefore never counted as an independent sample. The independent units are the 20 camera views, and for leakage the 9 split groups.

**Scene identity is visual, not header-based.** It uses median-background edge-map correlation. Header `place`/`cam` labels were wrong for identity:
- swoon `cam01` and `cam02` are two different physical places (day overhead and night garage);
- `710-3_cam01_..._summer` matches the night view.

## Per camera view

| scene_group | split_group | categories | cameras | takes | source_videos | windows_after_dedup | sent_to_review | related_to_reasoning_v1 |
|---|---|---|---|---|---|---|---|---|
| SCN_01 | SPG_01 | trespass01 | cam01 | 6 | 12 | 47 | 11 | True |
| SCN_02 | SPG_01 | trespass01 | cam02 | 6 | 12 | 92 | 11 | True |
| SCN_03 | SPG_02 | trespass03 | cam01 | 5 | 10 | 50 | 11 | True |
| SCN_04 | SPG_02 | trespass03 | cam02 | 5 | 10 | 67 | 11 | True |
| SCN_05 | SPG_03 | fight01 | cam01 | 5 | 15 | 61 | 11 | True |
| SCN_06 | SPG_03 | fight01 | cam02 | 5 | 15 | 66 | 11 | True |
| SCN_07 | SPG_03 | fight01 | cam03 | 5 | 15 | 66 | 8 | True |
| SCN_08 | SPG_04 | fight01 | cam01 | 1 | 3 | 7 | 4 | False |
| SCN_09 | SPG_04 | fight01 | cam02 | 1 | 3 | 6 | 5 | False |
| SCN_10 | SPG_04 | fight01 | cam03 | 1 | 3 | 6 | 2 | False |
| SCN_11 | SPG_05 | swoon01 | cam01 | 5 | 9 | 23 | 11 | True |
| SCN_12 | SPG_05 | swoon01 | cam01,cam02 | 5 | 11 | 64 | 11 | True |
| SCN_13 | SPG_06 | fight_mv | c1 | 2 | 2 | 2 | 2 | False |
| SCN_14 | SPG_06 | fight_mv | c2 | 2 | 2 | 2 | 2 | False |
| SCN_15 | SPG_07 | fight_mv | c1 | 1 | 1 | 1 | 1 | False |
| SCN_16 | SPG_07 | fight_mv | c2 | 1 | 1 | 1 | 1 | False |
| SCN_17 | SPG_08 | fight_mv | c1 | 1 | 1 | 1 | 1 | False |
| SCN_18 | SPG_08 | fight_mv | c2 | 1 | 1 | 1 | 1 | False |
| SCN_19 | SPG_09 | fight_mv | c1 | 1 | 1 | 0 | 0 | True |
| SCN_20 | SPG_09 | fight_mv | c2 | 1 | 1 | 0 | 0 | True |
