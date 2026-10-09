# Multi-view dataset structure

- Dataset key (user supplied): 71953. Local source ZIP: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip`.
- Label ZIP: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip`.
- Source MP4: 10; JSON: 5; valid linked pairs: 5. Two cameras per source JSON.
- ZIP layout: ph_eNNNN/ph_eNNNN_c1.mp4 and _c2.mp4; labels ph_eNNNN/ph_eNNNN.json.
- Pair association comes from the JSON videos array, not a filename-only inference. No explicit pair_id/incident_id field. MV IDs are local review IDs. Annotation stems are source locators.
- Event class: 신체적 충돌을 동반한 싸움. JSON videos has filename, dimensions (1920x1080), date/time, length, distribution, camera hardware model, angle, source and view. Camera hardware identifiers are not unique incident IDs. Source codes or/re are retained without guessing their meaning.
- Camera-specific caption.caption_text and caption.cot stage descriptions; common question and answer; camera-specific evidence_text, frame_id, obj_id, obj_bbox, obj_label. A question/answer pair exists, not a separate VQA list.
- FPS absent from source JSON. Numeric event_start/end absent; prose evidence frame range describes tracking consistency. Derived seconds require actual decoder FPS and remain event-support sampling estimates, not corrected official event times.
- obj_id strings jointly list people 1,2. Three sparse boxes per view correspond to evidence points; no continuous per-person bbox tracks supplied. Bounding-box axis convention is not explicitly defined. No independent keyframe images inside ZIP.
- No explicit sync offset/frame mapping. Coarse recording time differs by 1–3 sec; not a synchronization guarantee. Event onset difference will be stored separately from any visual correspondence estimate.
- All five local pairs are the shortlist: requested 15–20 cannot be produced from five incidents. No old candidates rerun or modified.
- Caption, CoT, answer, event class, evidence frame/object descriptions and annotation-selected sampling are private review data. Model loader must use only sanitized video/image media and a fixed generic prompt.

## Initial structure inconsistencies
- ph_e2038/ph_e2038.json c2: evidence keyframe outside prose tracking range
- ph_e2058/ph_e2058.json c1: evidence keyframe outside prose tracking range

Existing candidate_report.md, candidates.csv, candidates.json, dataset_structure.md read before this work; SHA256 snapshot stored separately for preservation verification.
## Decoder and review findings

- Ten videos: measured 30 FPS, 1920×1080. Final inventory contains durations, frame counts and file sizes.
- JSON pair associations visually consistent; no per-frame cross-camera identity or exact sync.
- Some evidence ends equal/exceed last zero-based frame. Source indexing convention unknown; only decode seeking clamped, annotation unchanged.
- MV04/MV05 have short boundary black frames. Private clip proposals avoid confirmed boundary black frames; originals and sheets retain them.
- Annotation-first shortlist has all five available incidents. Ten selected members extracted: 743,055,292 bytes. No derived clips generated.
- Review sampled full duration at 1 Hz plus evidence anchors; final human playback still required.
