# 477 Blind Human Grading Pack (System A / System B)

7 benchmark conditions × 2 systems = **14 blinded assessments**, each graded by a human reviewer on four 0/1/2
metrics (Event, Temporal, Evidence, Uncertainty; total 0–8) while watching the actual CCTV video.

**No scores were generated automatically.** No judge model, no keyword auto-flags, no imputation.
All scores are entered by human reviewers.

## For reviewers

1. Start the local UI (from this folder):
   ```bash
   python scripts/serve_grading.py
   ```
   Open the printed URL (default `http://127.0.0.1:4770/review/review.html`). If 4770 is busy, the next free port is used.
2. Enter your Reviewer ID (e.g. `reviewer_01`). A second reviewer uses `?reviewer=reviewer_02` or enters that ID.
   Each ID has its own browser autosave, and reviewers never see each other's grades.
3. For each ITEM, do the following:
   - Watch the video(s).
   - Read the **Reviewer Reference**. The green box is OBSERVABLE REFERENCE; the orange box is MUST REMAIN UNCERTAIN.
   - Grade **System A** and submit, then grade **System B** and submit. This is sequential: B opens only after A is submitted.
4. Autosave runs on every change (browser localStorage), and each submit is also saved to `grades/<reviewer_id>.json`.
   You can also use **Export grading JSON** and save the file into `grades/`.
   **Import JSON** resumes your own file on another browser.
5. Read `grading_guide.md` first. It covers the general 0/1/2 rubric with minimum conditions, 1-point cases, 0-point cases and boundary cases.
6. The per-item anchors are in `grading_reference.md`, also shown under "자세한 기준 펼치기" in the UI.

**Do not open:** `reveal_map_private.json`, `config/`, `scripts/`, `output/`, other reviewers' `grades/` files.
Do not try to identify the systems.

## Blinding

- A/B assignment uses a fixed seed (`config/build_config.json`, seed 4772026), set per item.
  - It does not depend on prediction content.
  - The mapping exists only in `reveal_map_private.json`.
  - The server never serves that file, and the UI never requests it.
- Blinded files (`cases/ITEM_XX/system_A|B.json`) keep only the `prediction` object.
  - Pipeline, model, run and runtime metadata are removed.
  - System-identifying phrases inside prediction text were replaced with `[system description redacted]` / `[system]`. Every replacement is logged in the private map. **No other wording was changed.**
  - Residual risk: the two systems write in different styles (for example, one mentions rule thresholds, the other mentions typed answers). Reviewers are asked not to guess.
- Videos are streamed read-only from `benchmark_v1/media` via `/video/ITEM_XX/CAM_0Y`.
  - The browser sees only generic camera labels, never file names or paths.
  - No copies or re-encoding.

## Reviewer reference provenance

The reference content is derived only from `benchmark_v1/private_ground_truth/set01–05.json`, written in `config/case_guides.yaml`. Every statement is tagged:
- `HV`: human-verified observation.
- `PR`: project reference / expected uncertainty.
- `CS`: SET03 clip-selection record.
- `SA`: AI Hub source annotation (context only, not the grading answer).
- `DER`: approximate clip-time conversion of SA/CS times.

No facts beyond those files were added. Model inputs never contained this material.

## After grading (operator)

```bash
python scripts/validate_grades.py grades/reviewer_01.json [grades/reviewer_02.json]
python scripts/reveal_results.py --grades grades/reviewer_01.json
python scripts/reveal_results.py --grades grades/reviewer_02.json      # optional second reviewer
```

`reveal_results.py` refuses to run until the grade file is complete and valid. It then writes:
- `output/<reviewer>_revealed.json`
- `output/summary.md` and `output/summary.csv`, containing:
  - the per-item and per-metric table;
  - the main five-case summary (ITEM_01–04, 07);
  - SET04 Top-1 / Full Order;
  - SET05 Multi-view Increment = ITEM_07 − max(ITEM_05, ITEM_06);
  - the ITEM_07 qualitative checks;
  - the confirmed flags.
- With two reviewers, also:
  - exact agreement and mean absolute difference per metric;
  - `output/adjudication_needed.md`, which lists every disagreement with both notes and the relevant anchor.

Disagreements are never averaged into a final score; reviewers re-watch the video and reach a consensus. Results are reported as rubric totals, never as "% accuracy".

## Rebuilding

```bash
python scripts/build_grading_pack.py
```

The build is deterministic. It validates the benchmark before and after, hashes the result files before and after (they are never modified), and checks that no identifying tokens remain in the blinded files.

## Files

| Path | Purpose |
|---|---|
| `grading_guide.md` | General 0/1/2 rubric (①②③④ per metric), procedure, SET04/SET05 rules |
| `grading_reference.md` | Per-ITEM reviewer reference + ITEM × metric 0/1/2 anchors + tips |
| `review/review.html` (+`app.js`, `style.css`, `data/rubric.json`) | Reviewer UI |
| `cases/ITEM_XX/` | `system_A.json`, `system_B.json` (blinded predictions), `reference.json` |
| `blind_manifest.json` | Items, cameras, video routes, case-file hashes (no identities) |
| `reveal_map_private.json` | **Private** A/B → system map, result-file SHA256, redaction log, build integrity record |
| `grades/` | Reviewer grade files |
| `output/` | Generated after reveal only |
