# 477 AI Multi-camera Candidate Report

## Dataset Structure

- Total videos: 10 MP4, actual 30 FPS, 1920×1080, approximately 30–32 seconds each.
- Total annotations: 5 JSON. Total valid pairs: 5. All five reviewed; five retained including two lower-gain comparisons.
- Event class (private): 신체적 충돌을 동반한 싸움.
- Pairing rule: one source JSON explicitly co-lists c1/c2 files, each resolves uniquely. No explicit official incident_id/pair_id. MV IDs are local, annotation stems are locators.
- Synchronization: no official sync. Coarse recording clocks disagree with evidence onset differences. Neither establishes exact frame correspondence.
- Review: full-duration 1 Hz decoded temporal sheets + nine evidence-centered keyframes per camera. This is not continuous playback; brief contact between samples can be missed. Human final video verification remains necessary.
- EVENT/BEFORE/AFTER means position relative to evidence tracking range, not official exact action boundaries. Source 0/1-based indexing is unspecified; decoder frame numbers are zero based.
- All reports, inventories and contact sheets contain private answer hints: never send to the evaluated model. Use model_input_only.json. No VLM API experiment run.

## Top Candidates

1. MV05 — Gain 4.80/5 — 나무 뒤로 사라진 사건을 다른 카메라에서 계속 관찰할 수 있는 가림 복원 사례다.
2. MV02 — Gain 4.45/5 — 차량 및 신체 겹침을 반대 시점이 보완한다.
3. MV01 — Gain 3.75/5 — 골목 반대 방향에서 본 신체 접촉·팔/다리 동작을 비교하기 좋다.

Gain = 0.35×complementarity + 0.25×occlusion_recovery + 0.20×participant_clarity_gain + 0.20×view_difference. Candidate-ordering heuristic only, not measured performance or source ground truth. Scores 1–5; ambiguity 1=clear, 5=ambiguous (more constrained view). No final pair selected.

---

## MV05

### Source

Pair ID: MV05; source locator: ph_e2069; role: priority_candidate.

CAM A (c1):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2069\ph_e2069_c1.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2069/ph_e2069_c1.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2069/ph_e2069.json`
- duration: 30.633s; FPS 30; 1920×1080; 74,834,701 bytes.
- event support estimate: 8.900–30.467s; tracking range [267, 914]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 1.900–30.600s (28.700s).
- near-black boundary frames: [918].

CAM B (c2):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2069\ph_e2069_c2.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2069/ph_e2069_c2.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2069/ph_e2069.json`
- duration: 31.833s; FPS 30; 1920×1080; 75,412,559 bytes.
- event support estimate: 9.333–30.733s; tracking range [280, 922]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 2.333–31.800s (29.467s).
- near-black boundary frames: [954].

Estimated B media time − A: +0.433s from evidence onset; coarse-clock alternative +3.0s. Neither proves sync.

### What CAM A shows

두 사람이 공원 통로에서 도로 쪽으로 이동한다. 접촉 이후 수목/수관 뒤에 가려 약 18~29초에는 참여자와 동작을 읽기 어렵다.

### What CAM B shows

도로의 노란 표시 부근에서 접근·신체 접촉을 볼 수 있다. 약 20~26초에 검은 옷 사람이 낮게 쓰러진 자세를 보이고 흰 옷 사람이 주변에 있으며 약 29~31초에 이동한다.

### Why multi-view helps

CAM A에서 인물이 보이지 않는 동안 CAM B는 도로 위 자세 변화와 이후 이동을 보여준다. 화면에서 사라짐과 사건 종료를 구별하는 근거를 제공한다.

### Limitations

의학적 실신, 부상 정도, 의도는 영상으로 확정할 수 없다. CAM B 단독도 매우 명확하므로 AB가 B보다 나은지는 별도 평가가 필요하다. 일부 마지막 프레임은 검은 화면이다.

5–10 seconds after the event is not guaranteed by these short source clips. No missing context synthesized. Pair sheet columns align independent event-support phases, not the same real moment.

### Scores

| Metric | Score | Selection reason |
|---|---:|---|
| cam_a_event_visibility | 2 | 수관이 접촉 이후 주요 구간을 가린다. |
| cam_b_event_visibility | 5 | 도로 쪽 카메라는 접촉·낮은 자세·이후 이동을 잘 보여준다. |
| view_difference | 5 | 공원 통로와 도로를 크게 다른 방향에서 본다. |
| complementarity | 5 | 가려진 동안의 사건 진행과 이후 이동을 추가한다. |
| occlusion_recovery | 5 | 수목 때문에 사라진 참여자와 자세를 반대 시점이 복원한다. |
| temporal_value | 5 | 사라짐 이후에도 사건이 진행됨을 순서로 확인한다. |
| participant_clarity_gain | 4 | 가려진 두 사람의 위치와 자세를 도로 시점에서 보완한다. |
| demo_suitability | 5 | 가려진 화면과 진행되는 사건의 대비가 직관적이다. |
| single_view_ambiguity | 5 | CAM A 단독에서는 사건 종료와 가림을 구별하기 매우 어렵다. |
| Multi-view gain (heuristic) | 4.80 | Ranking only |

### Suggested evaluation

CAM A only: A pixels + fixed generic prompt; assess observable interaction, evidence and uncertainty.

CAM B only: B pixels + identical prompt; essential strong single-view baseline.

CAM A + B: both pixel streams + identical prompt. Require camera-attributed evidence and no assumed sync. Compare with BOTH singles; AB better than A alone does not prove gain beyond B. Predeclare frame/token budgets and matched-total-budget sensitivity. Private clip suggestions above are not the current model-input schedule.

### Contact sheets

- CAM A: [MV05_cam_a.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV05_cam_a.jpg)
- CAM A full-duration 1 Hz: [MV05_cam_a_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV05_cam_a_temporal.jpg)
- CAM B: [MV05_cam_b.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV05_cam_b.jpg)
- CAM B full-duration 1 Hz: [MV05_cam_b_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV05_cam_b_temporal.jpg)
- Pair: [MV05_pair.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV05_pair.jpg)

---

## MV02

### Source

Pair ID: MV02; source locator: ph_e2044; role: priority_candidate.

CAM A (c1):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2044\ph_e2044_c1.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2044/ph_e2044_c1.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2044/ph_e2044.json`
- duration: 30.633s; FPS 30; 1920×1080; 72,442,413 bytes.
- event support estimate: 12.233–30.233s; tracking range [367, 907]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 5.233–30.633s (25.400s).
- near-black boundary frames: [].

CAM B (c2):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2044\ph_e2044_c2.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2044/ph_e2044_c2.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2044/ph_e2044.json`
- duration: 30.967s; FPS 30; 1920×1080; 73,151,531 bytes.
- event support estimate: 12.767–30.967s; tracking range [383, 929]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 5.767–30.967s (25.200s).
- near-black boundary frames: [].

Estimated B media time − A: +0.533s from evidence onset; coarse-clock alternative -1.0s. Neither proves sync.

### What CAM A shows

주차 차량과 이동하는 흰색 차량이 있는 골목에서 참여자가 멀고 일부 몸이 가려진다. 가까이 붙는 동작만으로 접촉의 형태를 판단하기 어렵다.

### What CAM B shows

약 13~27초에 팔을 뻗거나 몸을 붙이는 동작, 두 사람의 분리와 재접근이 상대적으로 잘 보인다.

### Why multi-view helps

CAM A에서 차량·몸 겹침으로 빠진 신체 동작을 CAM B로 확인한다. 배경 이동과 두 사람의 관계를 함께 설명할 수 있다.

### Limitations

차량의 가림은 구간에 따라 변한다. CAM B 단독 대비 실제 추가 성능은 아직 검증하지 않았다. 마지막까지 접촉이 이어져 사건 이후 맥락이 부족하다.

5–10 seconds after the event is not guaranteed by these short source clips. No missing context synthesized. Pair sheet columns align independent event-support phases, not the same real moment.

### Scores

| Metric | Score | Selection reason |
|---|---:|---|
| cam_a_event_visibility | 2 | 거리와 차량 때문에 몸 접촉을 읽기 어렵다. |
| cam_b_event_visibility | 4 | CAM B에서는 팔 동작과 재접근이 상대적으로 선명하다. |
| view_difference | 5 | 서로 반대 방향에서 차량과 인물의 배치를 본다. |
| complementarity | 4 | CAM A의 가려진 접촉 정보를 CAM B가 추가한다. |
| occlusion_recovery | 5 | 차량 및 인물 겹침의 상당 부분을 반대 시점에서 확인한다. |
| temporal_value | 4 | 접근·접촉·분리·재접근의 순서가 유용하다. |
| participant_clarity_gain | 4 | 두 몸이 겹칠 때 각 사람의 위치와 자세를 보완한다. |
| demo_suitability | 5 | 차량 가림과 다른 시점의 접촉을 비교하기 쉽다. |
| single_view_ambiguity | 4 | CAM A 단독에서는 가까이 서 있음과 접촉을 구분하기 어렵다. |
| Multi-view gain (heuristic) | 4.45 | Ranking only |

### Suggested evaluation

CAM A only: A pixels + fixed generic prompt; assess observable interaction, evidence and uncertainty.

CAM B only: B pixels + identical prompt; essential strong single-view baseline.

CAM A + B: both pixel streams + identical prompt. Require camera-attributed evidence and no assumed sync. Compare with BOTH singles; AB better than A alone does not prove gain beyond B. Predeclare frame/token budgets and matched-total-budget sensitivity. Private clip suggestions above are not the current model-input schedule.

### Contact sheets

- CAM A: [MV02_cam_a.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV02_cam_a.jpg)
- CAM A full-duration 1 Hz: [MV02_cam_a_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV02_cam_a_temporal.jpg)
- CAM B: [MV02_cam_b.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV02_cam_b.jpg)
- CAM B full-duration 1 Hz: [MV02_cam_b_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV02_cam_b_temporal.jpg)
- Pair: [MV02_pair.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV02_pair.jpg)

---

## MV01

### Source

Pair ID: MV01; source locator: ph_e2038; role: priority_candidate.

CAM A (c1):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2038\ph_e2038_c1.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2038/ph_e2038_c1.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2038/ph_e2038.json`
- duration: 30.600s; FPS 30; 1920×1080; 72,261,694 bytes.
- event support estimate: 17.433–30.567s; tracking range [523, 917]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 10.433–30.600s (20.167s).
- near-black boundary frames: [].

CAM B (c2):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2038\ph_e2038_c2.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2038/ph_e2038_c2.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2038/ph_e2038.json`
- duration: 30.967s; FPS 30; 1920×1080; 73,156,545 bytes.
- event support estimate: 18.067–30.967s; tracking range [542, 929]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 11.067–30.967s (19.900s).
- near-black boundary frames: [].

Estimated B media time − A: +0.633s from evidence onset; coarse-clock alternative +1.0s. Neither proves sync.

### What CAM A shows

멀리 있는 두 사람의 몸이 겹친다. 약 24~26초의 몸 굽힘은 한쪽 화면만으로 자세 변화의 성격을 구별하기 어렵다.

### What CAM B shows

더 큰 인물과 다른 방향의 팔·다리 움직임을 볼 수 있다. 약 25초에 두 사람의 자세와 접촉을 구별하기 쉽다.

### Why multi-view helps

한쪽에서 겹친 팔다리와 몸 굽힘을 반대 시점으로 교차 확인할 수 있다.

### Limitations

CAM B만으로도 사건이 비교적 명확하다. 넘어짐이라는 caption 표현을 영상만으로 단정하지 않는다. 사건 후 충분한 여유 구간이 없다.

5–10 seconds after the event is not guaranteed by these short source clips. No missing context synthesized. Pair sheet columns align independent event-support phases, not the same real moment.

### Scores

| Metric | Score | Selection reason |
|---|---:|---|
| cam_a_event_visibility | 3 | 거리와 몸 겹침이 팔다리 판단을 제한한다. |
| cam_b_event_visibility | 4 | 반대 시점에서 팔과 다리 움직임이 더 크고 잘 보인다. |
| view_difference | 5 | 같은 골목을 반대 방향으로 관찰한다. |
| complementarity | 4 | 겹친 팔다리를 교차 확인할 수 있다. |
| occlusion_recovery | 3 | 일부 몸 겹침을 반대 시점으로 보완한다. |
| temporal_value | 4 | 접근부터 연속 접촉까지 흐름을 확인한다. |
| participant_clarity_gain | 3 | 두 참여자의 자세를 보완하지만 참여자 수는 양쪽에서 읽힌다. |
| demo_suitability | 4 | 크기 차이와 자세 해석을 발표에서 비교하기 좋다. |
| single_view_ambiguity | 4 | CAM A의 몸 굽힘과 겹침만으로는 동작 성격이 애매하다. |
| Multi-view gain (heuristic) | 3.75 | Ranking only |

### Suggested evaluation

CAM A only: A pixels + fixed generic prompt; assess observable interaction, evidence and uncertainty.

CAM B only: B pixels + identical prompt; essential strong single-view baseline.

CAM A + B: both pixel streams + identical prompt. Require camera-attributed evidence and no assumed sync. Compare with BOTH singles; AB better than A alone does not prove gain beyond B. Predeclare frame/token budgets and matched-total-budget sensitivity. Private clip suggestions above are not the current model-input schedule.

### Contact sheets

- CAM A: [MV01_cam_a.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV01_cam_a.jpg)
- CAM A full-duration 1 Hz: [MV01_cam_a_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV01_cam_a_temporal.jpg)
- CAM B: [MV01_cam_b.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV01_cam_b.jpg)
- CAM B full-duration 1 Hz: [MV01_cam_b_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV01_cam_b_temporal.jpg)
- Pair: [MV01_pair.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV01_pair.jpg)

---

## MV03

### Source

Pair ID: MV03; source locator: ph_e2047; role: lower_gain_comparison.

CAM A (c1):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2047\ph_e2047_c1.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2047/ph_e2047_c1.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2047/ph_e2047.json`
- duration: 30.967s; FPS 30; 1920×1080; 77,831,245 bytes.
- event support estimate: 12.300–25.900s; tracking range [369, 777]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 5.300–30.967s (25.667s).
- near-black boundary frames: [].

CAM B (c2):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2047\ph_e2047_c2.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2047/ph_e2047_c2.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2047/ph_e2047.json`
- duration: 30.900s; FPS 30; 1920×1080; 78,353,565 bytes.
- event support estimate: 10.000–26.433s; tracking range [300, 793]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 3.000–30.900s (27.900s).
- near-black boundary frames: [].

Estimated B media time − A: -2.300s from evidence onset; coarse-clock alternative +2.0s. Neither proves sync.

### What CAM A shows

흰 옷과 검은 옷의 두 사람이 골목에서 접근하고 약 12~23초에 팔·다리를 움직이며 접촉한 뒤 떨어진다.

### What CAM B shows

반대 방향에서 몸 겹침과 다리·팔 움직임을 볼 수 있다. 약 10~26초의 진행과 이후 이동을 확인한다.

### Why multi-view helps

서로 다른 신체 방향을 확인하지만 양쪽 모두 이미 사건이 잘 보여 증분 정보는 제한적이다.

### Limitations

single-view에서는 애매하지만 multi-view에서는 명확이라는 대표 스토리에 약하다. 기록 시각과 evidence 시작 차이가 크게 맞지 않아 동기화 추정에 특히 주의한다.

5–10 seconds after the event is not guaranteed by these short source clips. No missing context synthesized. Pair sheet columns align independent event-support phases, not the same real moment.

### Scores

| Metric | Score | Selection reason |
|---|---:|---|
| cam_a_event_visibility | 4 | 양쪽 참여자와 신체 동작이 비교적 크게 보인다. |
| cam_b_event_visibility | 4 | 반대 시점에서도 신체 접촉과 분리가 보인다. |
| view_difference | 4 | 반대 방향으로 앞뒤와 팔다리를 관찰한다. |
| complementarity | 3 | 추가 각도는 있으나 사건 분류는 단독에서도 쉽다. |
| occlusion_recovery | 3 | 국소 몸 겹침만 보완하고 큰 가림은 적다. |
| temporal_value | 4 | 접근·접촉·이탈이 있어 시간 흐름이 유용하다. |
| participant_clarity_gain | 3 | 이미 양쪽에서 두 참여자를 구별하기 쉽다. |
| demo_suitability | 4 | 싸움 시연은 명확하지만 multi-view 증분 스토리는 약하다. |
| single_view_ambiguity | 2 | 불확실성이 낮은 단독 시점 비교군이다. |
| Multi-view gain (heuristic) | 3.20 | Ranking only |

### Suggested evaluation

CAM A only: A pixels + fixed generic prompt; assess observable interaction, evidence and uncertainty.

CAM B only: B pixels + identical prompt; essential strong single-view baseline.

CAM A + B: both pixel streams + identical prompt. Require camera-attributed evidence and no assumed sync. Compare with BOTH singles; AB better than A alone does not prove gain beyond B. Predeclare frame/token budgets and matched-total-budget sensitivity. Private clip suggestions above are not the current model-input schedule.

### Contact sheets

- CAM A: [MV03_cam_a.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV03_cam_a.jpg)
- CAM A full-duration 1 Hz: [MV03_cam_a_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV03_cam_a_temporal.jpg)
- CAM B: [MV03_cam_b.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV03_cam_b.jpg)
- CAM B full-duration 1 Hz: [MV03_cam_b_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV03_cam_b_temporal.jpg)
- Pair: [MV03_pair.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV03_pair.jpg)

---

## MV04

### Source

Pair ID: MV04; source locator: ph_e2058; role: lower_gain_comparison.

CAM A (c1):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2058\ph_e2058_c1.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2058/ph_e2058_c1.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2058/ph_e2058.json`
- duration: 30.400s; FPS 30; 1920×1080; 73,210,703 bytes.
- event support estimate: 6.533–30.200s; tracking range [196, 906]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 0.133–30.333s (30.200s).
- near-black boundary frames: [0, 1, 2, 3, 910, 911].

CAM B (c2):
- video: `D:\projects\477\evaluation_selection\multiview\tmp\ph_e2058\ph_e2058_c2.mp4`
- original ZIP member: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\01.원천데이터\VS_싸움_신체적충돌을동반한싸움.zip::ph_e2058/ph_e2058_c2.mp4`
- annotation: `D:\projects\477\downloads\multiview_fight\21.다각도_CCTV_생활안전_데이터\3.개방데이터\2.데이터(NIA)\Validation\02.라벨링데이터\VL_싸움_신체적충돌을동반한싸움.zip::ph_e2058/ph_e2058.json`
- duration: 30.633s; FPS 30; 1920×1080; 72,400,336 bytes.
- event support estimate: 6.767–30.767s; tracking range [203, 923]; NOT exact official event bounds.
- people: 2 jointly annotated; sparse IDs ['1', '2']; not all background pedestrians.
- suggested clip (not generated): 0.000–30.567s (30.567s).
- near-black boundary frames: [917, 918].

Estimated B media time − A: +0.233s from evidence onset; coarse-clock alternative +2.0s. Neither proves sync.

### What CAM A shows

넓은 도로/골목 교차부에서 두 사람이 작게 보인다. 몸 움직임은 있으나 팔·손 접촉을 분명히 읽기 어렵다.

### What CAM B shows

다른 방향과 높이에서 같은 공간을 보지만 사람은 여전히 작고 주차 차량 주변의 자세를 세밀하게 구별하기 어렵다.

### Why multi-view helps

방향 정보는 추가되나 양쪽의 거리 제약이 남아 접촉·참여자 판단 향상이 작다.

### Limitations

카메라 구도가 동일한 pair는 아니다. 서로 다른 구도지만 유효 정보가 적다. 짧은 시작/끝 검은 화면이 있어 데모 구간 검토가 필요하다.

5–10 seconds after the event is not guaranteed by these short source clips. No missing context synthesized. Pair sheet columns align independent event-support phases, not the same real moment.

### Scores

| Metric | Score | Selection reason |
|---|---:|---|
| cam_a_event_visibility | 2 | 먼 거리의 작은 인물이라 접촉을 읽기 어렵다. |
| cam_b_event_visibility | 2 | 다른 시점도 사람 크기가 작아 세부 동작이 제한된다. |
| view_difference | 4 | 방향과 카메라 높이는 다르다. |
| complementarity | 2 | 다른 시점에서도 거리 제약이 남는다. |
| occlusion_recovery | 2 | 일부 위치 확인 외 신체 가림 복원은 제한적이다. |
| temporal_value | 3 | 움직임 순서는 보이나 접촉 세부는 제한된다. |
| participant_clarity_gain | 2 | 두 사람이 작아 참여자 자세 구별 향상이 적다. |
| demo_suitability | 2 | 멀리 있는 사람과 끝 검은 화면이 데모 직관성을 낮춘다. |
| single_view_ambiguity | 4 | 몸 움직임만으로 신체 충돌을 확신하기 어렵다. |
| Multi-view gain (heuristic) | 2.40 | Ranking only |

### Suggested evaluation

CAM A only: A pixels + fixed generic prompt; assess observable interaction, evidence and uncertainty.

CAM B only: B pixels + identical prompt; essential strong single-view baseline.

CAM A + B: both pixel streams + identical prompt. Require camera-attributed evidence and no assumed sync. Compare with BOTH singles; AB better than A alone does not prove gain beyond B. Predeclare frame/token budgets and matched-total-budget sensitivity. Private clip suggestions above are not the current model-input schedule.

### Contact sheets

- CAM A: [MV04_cam_a.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV04_cam_a.jpg)
- CAM A full-duration 1 Hz: [MV04_cam_a_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV04_cam_a_temporal.jpg)
- CAM B: [MV04_cam_b.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV04_cam_b.jpg)
- CAM B full-duration 1 Hz: [MV04_cam_b_temporal.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV04_cam_b_temporal.jpg)
- Pair: [MV04_pair.jpg](D:/projects/477/evaluation_selection/multiview/contact_sheets/MV04_pair.jpg)