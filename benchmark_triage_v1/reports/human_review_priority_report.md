# Human review priority report

```yaml
Original candidates: 115
Priority candidates: 43
Unique scene groups: 18
Independent-from-reasoning-v1 count: 16
Related count: 27
Per-scene max: 3
Requested target: 55
Feasible scene-capped maximum: 43
P1/P4 outputs accessed: NO
Human labels generated: NO
```

The requested 50–60 candidates cannot be reached under the scene cap: 11 scenes have at least 3 candidates, 3 scenes have 2, and 4 scenes have 1; 11×3 + 3×2 + 4×1 = 43. The cap takes precedence; no new candidates or scenes were invented.

This is a priority subset for human video review, not a labeled or final benchmark. Only humans assign CLEAR_NORMAL / HARD_NEGATIVE_NORMAL / ANCHORED_DANGER / AMBIGUOUS / EXCLUDE.

## Method and data boundary

Inputs: review/human_review_queue.csv and candidate_pool/candidates.csv only. Selection receives only explicit allowlisted metadata. No media, predictions, evaluation, cascade results, private ground truth, or human label values are inspected. Source label is copied as opaque review context, excluded from selection and hidden by the priority UI. All ten human-input fields are blank. Original queue and reviewer2 queue are untouched.

Quality eligibility: n_frames > 0 and pool_status=kept:sent_to_review. Uses existing duplicate filtering; no new image comparison or content judgment. Independence requires all three reasoning-v1 source/view/split relations to be false. Reserve independent candidates first (scene cap applies), ensure one source event candidate per available event scene, then fill using scene floor 2 and lexicographic score: missing scene event, new rare tags (sum floor(1000/tag availability)), new within-scene tags, new source, new dataset/take session, SHA256('477:candidate_id') tie break. No stochastic tie break. Every selection reason records score components. scene_group_rank is selected order within scene followed by excluded IDs sorted ascending; it is a selection rank, not a quality or danger rank.


## Candidates per scene group

| Group | Original | Priority |
|---|---:|---:|
| SCN_01 | 11 | 3 |
| SCN_02 | 11 | 3 |
| SCN_03 | 11 | 3 |
| SCN_04 | 11 | 3 |
| SCN_05 | 11 | 3 |
| SCN_06 | 11 | 3 |
| SCN_07 | 8 | 3 |
| SCN_08 | 4 | 3 |
| SCN_09 | 5 | 3 |
| SCN_10 | 2 | 2 |
| SCN_11 | 11 | 3 |
| SCN_12 | 11 | 3 |
| SCN_13 | 2 | 2 |
| SCN_14 | 2 | 2 |
| SCN_15 | 1 | 1 |
| SCN_16 | 1 | 1 |
| SCN_17 | 1 | 1 |
| SCN_18 | 1 | 1 |

## Coverage by source type

| Group | Original | Priority |
|---|---:|---:|
| aihub_171_abnormal_cctv | 107 | 35 |
| aihub_71953_multiview_cctv | 8 | 8 |

## Source categories

| Group | Original | Priority |
|---|---:|---:|
| fight01 | 41 | 17 |
| fight_mv | 8 | 8 |
| swoon01 | 22 | 6 |
| trespass01 | 22 | 6 |
| trespass03 | 22 | 6 |

## Camera

| Group | Original | Priority |
|---|---:|---:|
| c1 | 4 | 4 |
| c2 | 4 | 4 |
| cam01 | 49 | 15 |
| cam02 | 48 | 15 |
| cam03 | 10 | 5 |

## Actor/session proxy (split group)

| Group | Original | Priority |
|---|---:|---:|
| SPG_01 | 22 | 6 |
| SPG_02 | 22 | 6 |
| SPG_03 | 30 | 9 |
| SPG_04 | 11 | 8 |
| SPG_05 | 22 | 6 |
| SPG_06 | 4 | 4 |
| SPG_07 | 2 | 2 |
| SPG_08 | 2 | 2 |

## Recording session (take ID)

| Group | Original | Priority |
|---|---:|---:|
| 145-1 | 4 | 1 |
| 145-2 | 6 | 2 |
| 145-3 | 3 | 1 |
| 145-4 | 3 | 0 |
| 145-5 | 4 | 2 |
| 145-6 | 2 | 0 |
| 146-1 | 8 | 2 |
| 146-2 | 3 | 1 |
| 146-3 | 1 | 0 |
| 146-4 | 5 | 2 |
| 146-5 | 5 | 1 |
| 435-2 | 4 | 1 |
| 435-3 | 12 | 2 |
| 435-4 | 6 | 3 |
| 435-5 | 3 | 2 |
| 435-6 | 5 | 1 |
| 439-1 | 11 | 8 |
| 710-2 | 4 | 2 |
| 710-3 | 5 | 1 |
| 710-4 | 3 | 1 |
| 710-5 | 3 | 1 |
| 710-6 | 7 | 1 |
| ph_e2038 | 2 | 2 |
| ph_e2044 | 2 | 2 |
| ph_e2047 | 2 | 2 |
| ph_e2058 | 2 | 2 |

## Window kind

| Group | Original | Priority |
|---|---:|---:|
| event | 38 | 20 |
| post_event | 18 | 5 |
| pre_event | 59 | 18 |

## Coverage by discovery hint

| Group | Original | Priority |
|---|---:|---:|
| (no hint) | 12 | 3 |
| HN01_HN09_low_then_upright | 19 | 7 |
| HN02_HN14_low_posture_sustained | 9 | 4 |
| HN03_fast_movement | 7 | 4 |
| HN06_HN07_close_pair | 38 | 13 |
| HN11_dark | 6 | 2 |
| HN12_multiple_people | 14 | 3 |
| HN15_visual_motion_no_person | 1 | 1 |
| empty_scene | 11 | 4 |
| source_event_window | 38 | 20 |

## Diversity tags (proxies, not labels)

| Group | Original | Priority |
|---|---:|---:|
| boundary_event_candidate | 12 | 4 |
| clear_low_motion_proxy | 75 | 22 |
| close_pair_hint | 38 | 13 |
| conflict_event_candidate | 20 | 14 |
| crouch_recover_proxy | 19 | 7 |
| crowd_proxy | 14 | 3 |
| darkness_low_visibility_hint | 6 | 2 |
| empty_scene_hint | 11 | 4 |
| entry_gate_source_context_proxy | 32 | 8 |
| fall_event_candidate | 6 | 2 |
| person_present_unspecified | 66 | 19 |
| running_proxy | 7 | 4 |
| sit_lie_posture_proxy | 9 | 4 |
| visual_noise_proxy | 1 | 1 |

## Event-candidate coverage

Source category + window_kind=event only; no source_label or danger inference.

| Type | Original | Priority | Unique priority scenes |
|---|---:|---:|---:|
| fall | 6 | 2 | 2 |
| conflict | 20 | 14 | 10 |
| boundary | 12 | 4 | 4 |

## Candidates excluded from priority review

Count: 72. Excluded candidates remain in the original queue; exclusion here is not a human EXCLUDE label.

- independent_scene_cap: 3
- related_scene_cap_representative_only: 69

Candidate-level decisions for all 115 candidates: human_review_priority_selection_audit.csv.

## Potential diversity limitations

- 19 independent candidates available; 16 retained. Three repeat candidates exceed caps in SCN_08/SCN_09.
- Walking has no explicit discovery hint: person_present_unspecified is only person presence, not walking.
- Entry/gate uses pre/post-event source context only; normal entry and gate presence are unverified.
- Brief contact has no independent hint: HN06_HN07_close_pair is a shared proximity proxy, not contact evidence.
- Low motion, recovery, sit/lie, running, crowd and visual noise tags are discovery proxies only.
- Fall events exist in two scenes only; darkness in one scene and visual-noise hint in one candidate.
- Cameras within a split group may share site/actors; 18 scenes are not 18 independent sites. Only two datasets and five source categories are available; actors have no explicit IDs. Selection uses take and split-group proxies and cannot guarantee actor diversity.

## Start reduced human review

```sh
python benchmark_triage_v1/scripts/serve_review.py --priority
```
Default and --reviewer2 modes keep their existing queues. --priority saves human edits only to the priority CSV with backups; it does not synchronize labels into the original queue. The builder refuses to overwrite a priority queue to preserve later human edits.

## Validation

Original and reviewer2 queues were SHA256-identical before and after generation. Reversing input order produces identical selected IDs and order. All original columns and selection metadata were verified, all human fields are blank, all 18 scenes and every existing discovery hint are represented, and independence/scene-cap counts pass. CLI help exposes mutually exclusive --priority/--reviewer2. The priority GET handler was tested directly: exactly 43 rows, source labels hidden, review labels blank. An HTTP loopback integration attempt was blocked by Windows socket permissions (WinError 10013); no browser or video was opened, and no save/label operation was performed.

