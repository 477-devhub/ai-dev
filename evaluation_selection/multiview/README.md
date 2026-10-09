# 477 AI Multi-camera Candidate Selection

기존 single-camera 결과를 보존한 별도 확장이다. 최종 pair 선정, 학습, VLM API 성능 실험은 수행하지 않았다. 로컬 데이터가 10 MP4 / 5 JSON / 5 사건뿐이라 15–20개 예비 후보를 만들 수 없었다. annotation을 모두 읽고 공식 videos 배열로 연결한 다섯 pair를 먼저 shortlist한 뒤 확인에 필요한 10개 member만 추출했다. 이번 제한된 ZIP에서는 결과적으로 영상 member 전부가 필요했지만 무조건 전체 ZIP 해제로 시작하지 않았다.

## Data locations

- Project: `/mnt/d/projects/477` ↔ Windows `D:/projects/477`.
- Source: `D:/projects/477/downloads/multiview_fight/21.다각도_CCTV_생활안전_데이터/3.개방데이터/2.데이터(NIA)/Validation/01.원천데이터/VS_싸움_신체적충돌을동반한싸움.zip`.
- Labels: same Validation directory, `02.라벨링데이터/VL_싸움_신체적충돌을동반한싸움.zip`.
- Outputs only: `D:/projects/477/evaluation_selection/multiview/`.
- Existing reports read first: parent candidate_report.md, candidates.csv, candidates.json, dataset_structure.md; SHA256 unchanged checks saved.
- Dataset key 71953 supplied by user; local annotations are the factual source, no external source inferred.

## Run

Python with OpenCV, numpy and Pillow is required. Existing runtime used: `D:/Users/suncastle/anaconda3/python.exe`. No installation was performed. Work inside this multiview directory:

```bash
python scripts/inspect_multiview_dataset.py
# inspect is the same read-only source scan as build_inventory; run either once
python scripts/build_multiview_inventory.py
python scripts/select_multiview_candidates.py
python scripts/extract_multiview_contact_sheets.py
python scripts/build_multiview_report.py
python scripts/load_model_input.py MV05 multi_ab
```

First inspect/build writes dataset_structure.md and initial inventories; inspect these before candidate selection. No selection logic runs inside the structure scan. Extraction capacity is checked with shutil.disk_usage (Windows equivalent of df -h); WSL/df access unavailable. ZIP members are copied through zipfile streams, never modifying sources. Existing extracted files are reused by size and verified by source member CRC during report verification. Temporary files are not automatically deleted. Source ZIP SHA256 uses streaming hashing. Normal script runs write only inside this directory, including Python cache.

## Outputs and privacy

- dataset_structure.md; multiview_inventory.csv/json: full source association and decoder metadata; **PRIVATE** because labels/evidence included.
- annotation_shortlist_private.json: annotation-first all-five shortlist, source actions/descriptions.
- review_decisions_private.json: frozen qualitative visual review and all nine 1–5 scores/reasons. Re-running rebuilds the same selection from these documented decisions; it does not automatically rejudge video quality. Any source change requires a new human visual review and new decisions.
- multiview_candidates.csv/json; multiview_candidate_report.md: five candidates, Top 3, clips, scores and limitations; **PRIVATE**.
- multiview_eval_manifest.json: model_input plus ground_truth_private and selection_review_private. Never serialize this entire object to a model.
- model_input_only.json: allowlisted media locators, fixed generic prompt and three conditions. load_model_input.py loads only this file, produces local paths for opening media with generic CAM A/B display labels, and makes no API calls. Paths/source filenames are locators, not prompt text.
- contact_sheets/: 25 JPEG, 9-frame camera sheets and 9-column paired sheets, plus full-duration 1 Hz temporal review for each camera. **PRIVATE: annotation-based sampling and EVENT labels leak answers.** Never use these sheets for model input.
- integration_recommendation.md: existing scenarios comparison and optional replacement opinion; no parent files changed.
- source_zip_snapshot.json, existing_result_snapshot.json, validation_summary.json: protection and verification records.
- capacity_check.json, temporary_files.json: extraction size and all ten removable-after-human-approval local temporary copies. Do not delete originals or these files automatically.
- No derived evaluation clips were created. Recommended 15–35 second bounds are private review proposals only.

## Selection and experiment

Prefer complementary/occlusion-recovering views, then temporal and participant evidence. Gain = .35 complementarity + .25 occlusion_recovery + .20 participant_clarity_gain + .20 view_difference, 1–5; heuristic for ordering, not AI Hub ground truth or performance metric. MV05/MV02/MV01 are priorities; MV03/MV04 are lower-gain comparisons, not falsely promoted as strong gains. Two annotated people per view does not mean there are only two background people.

Future conditions: single_a, single_b, multi_ab. Use identical predeclared generic prompt and pixels only. No event class, caption, question/answer, CoT, source description, bbox/object information, scores or annotation-selected timestamps may enter input. The current model_input proposes full source videos, or predeclared uniform sampling; neither uses private clip bounds. If clips are later adopted, predeclare cropping consistently and acknowledge oracle temporal localization. Compare AB with both singles, especially the stronger one, and control total frame/token budget. No medical injury/severity/risk/priority/confidence ground truth was invented.

## Limitations

Official incident_id/pair_id and frame sync mapping are absent. Pair identity is supported by two-video co-listing in one source JSON and visually consistent scene/clothing/actions; cross-camera track identity is not officially continuous. Coarse timestamps disagree with evidence-start differences. estimated_time_offset is B evidence onset minus A evidence onset in media seconds, not a verified sync offset. Pair sheets show independently normalized evidence phases, not synchronized real moments.

Evidence prose tracking ranges are not exact action boundaries. Source frame index base is undocumented; some sparse keyframes fall just outside prose ranges and some endpoints reach beyond zero-based last frames. Source facts are preserved, decoder seeks only are clamped. Some MV04/MV05 boundary frames are black; proposed clip bounds omit confirmed edge black frames. Source face blur is retained. Many clips end near the evidence end, so 5–10 seconds of aftermath is unavailable. Review uses 1 Hz temporal frames and nine anchors, not continuous playback; short motion can be missed. A person must verify the original video before final selection. Five incidents are a small convenience sample and cannot establish product/model performance generalization.
