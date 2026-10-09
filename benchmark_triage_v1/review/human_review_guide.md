# 477-triage-normal-v1 — Human Review Guide

**Current priority protocol:** the 43 priority videos have already been manually reviewed. No additional video review or auxiliary annotation is required. Only `candidate_id` and `review_label` are required human GT. The 72 unreviewed candidates remain blank and are not included. Existing human labels must not be changed by AI or heuristics. `validate_human_labels.py --priority` applies this policy; the default validator retains the legacy full-queue policy.

You are building the **reference** that decides whether 477 AI may hide a screen from an operator.

- Your label is the ground truth.
- Nothing in this pack was labelled by a model.
- The `suggested_candidate_type` and `discovery_hints` columns come from simple metadata and motion rules. They are **hints for finding candidates, not answers**. Ignore them when you judge.
- `source_label` is the AI Hub scenario name for the *whole source video* (e.g. "swoon", "fight", "trespass"). Most windows were cut from *before* that event, so the label usually does **not** describe the window. Do not copy it.

## Files

| File | Purpose |
|---|---|
| `review/human_review_queue.csv` | One row per candidate. Fill the empty columns (see below). |
| `review/contact_sheets/CAND_XXXX.jpg` | 16 frames, evenly spaced, with time relative to the clip start |
| `review/clips/CAND_XXXX.mp4` | The exact clip (≈35 s, original resolution, no re-encode) |
| `review/human_review_queue_reviewer2.csv` | Optional independent second review (all event candidates + 20 others) |

**If the contact sheet is insufficient, review the full candidate video.** Always watch the full clip when:
- the sheet shows anyone low to the ground, two people close together, fast movement, or a person near a wall, gate or door;
- you are about to choose ANCHORED_DANGER or HARD_NEGATIVE_NORMAL;
- you are not at least MEDIUM-confident from the sheet alone.

Falls, conflicts, brief contact and boundary crossings depend on temporal context. A single frame is not enough.

## Labels (`review_label`)

| Label | Use when |
|---|---|
| `CLEAR_NORMAL` | No observable safety-relevant event; ordinary human activity (or an empty scene). You are confident it is benign. |
| `HARD_NEGATIVE_NORMAL` | Some observable motion or posture *could resemble* danger (crouching, sitting on the ground, running, close pair, brief contact, a person near a gate or wall, darkness…), but the **full temporal context shows benign behavior**. |
| `ANCHORED_DANGER` | A clear, observable, safety-relevant event that an operator should see. Describe it without inferring intent, diagnosis or authorization. |
| `AMBIGUOUS` | Reasonable reviewers could disagree, or the visual evidence is insufficient. Fill `ambiguous_reason`. |
| `EXCLUDE` | Unusable: the event leaks into a "normal" window, the clip is broken, black or frozen, it duplicates another candidate, or it is otherwise unusable. Fill `exclude_reason`. |

**Rules of thumb:**
- **An empty scene is CLEAR_NORMAL** (`normal_subtype = empty_scene`). It may be used, but at most a few. The benchmark needs scenes *with people*.
- **Pre-event windows are not automatically normal.** Staged actors may already be approaching, crouching near a wall, or starting to argue. If anything in the window is part of the incident build-up, choose `AMBIGUOUS` or `EXCLUDE` (`event_leakage`). Do not choose normal.
- **Event windows are not automatically danger.** Choose `ANCHORED_DANGER` only if *you* can see the event in this clip. A gate entry with no visible safety-relevant act is normally `HARD_NEGATIVE_NORMAL` (HN05) or `AMBIGUOUS`, not danger.
- **The green-screen studio clips** (AI Hub 171 fight) are not real CCTV scenes. Label what you see, and use the `observable_summary` to note "studio" if it matters.

## Confidence (`review_confidence`)

| Confidence | Meaning | Use in the benchmark |
|---|---|---|
| `HIGH` | You would bet on it; another careful reviewer would almost surely agree | Optional metadata; no selection/scoring effect |
| `MEDIUM` | Probably right, but some doubt | Optional metadata; no selection/scoring effect |
| `LOW` | A guess | Optional metadata; no selection/scoring effect |
| blank / `UNSPECIFIED` | Per-item confidence not collected | Allowed; never filled with HIGH |

Human labels were manually assigned, but per-item confidence was not collected consistently. Primary inclusion depends only on the human review label. AMBIGUOUS is the separate challenge set and never part of the primary denominator.

## Other columns

| Column | Required when | Allowed values |
|---|---|---|
| `observable_summary` | Optional | Observable facts if already collected; no machine summary is presented as human GT |
| `danger_type_if_any` | Optional | Existing human error-analysis metadata only |
| `hard_negative_type_if_any` | Optional | Existing human error-analysis metadata only |
| `normal_subtype` | Optional | Existing human error-analysis metadata only |
| `ambiguous_reason` | Optional | Existing free text only |
| `exclude_reason` | Optional | Existing exclusion context only |
| `reviewer` | Metadata | Blank labelled rows may use `reviewer_01` under the user's confirmed single-reviewer provenance; preserve existing values |
| `reviewed_at` | Optional | Preserve existing times; never fabricate per-item timestamps. Batch file modification time is recorded separately in the priority manifest |

### Words that must NOT appear in your summary (observable facts only)

These terms are forbidden and are rejected by the validator: *criminal, illegal, trespass(er), intruder, burglar, thief, attacker, victim, assault, fainted, unconscious, medical emergency, seizure, drunk, suspicious person*.

Use descriptions such as:
- "person climbs over a visible wall"
- "person goes from upright to the ground within ~1 s and stays low"
- "two people exchange repeated strikes or shoves"

## Second reviewer (optional but recommended)

`review/human_review_queue_reviewer2.csv` lists every event candidate plus 20 others.
- A second person fills it **without looking at the first reviewer's file**.
- Disagreements are flagged `adjudication_required` by `scripts/validate_human_labels.py` and must be resolved by discussion. They are never averaged.
- If there is no second reviewer, leave the file empty. Never fill it in on someone else's behalf.

## Finishing

1. Save the CSV (UTF-8; Excel "CSV UTF-8" is fine).
2. Run `python scripts/validate_human_labels.py`. It reports missing fields, forbidden words, policy violations and any reviewer disagreement.
3. When validation passes, record class-count approval in `review/approvals.json` (template in that file). Then `scripts/build_benchmark.py` can select, split and freeze.
