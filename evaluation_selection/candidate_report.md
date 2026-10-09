# 477 AI Evaluation Candidate Report

## Dataset Summary

이 보고서는 사람이 선택할 후보 목록이다. 최종 5개 선정, 위험 순위 정답, 모델 학습을 수행하지 않았다.

검토 방법: 전체 118개 XML 및 파일 목록 조사 → annotation 기반 표본 21개 → Swoon 대체 시점 9개 추가 → 총 30개 영상의 사건 전후 9장과 시간순 24장 검토. 전체 영상 연속 재생 또는 전체 프레임 검토는 수행하지 않았다. 점수는 정성적 선정 판단이며 AI Hub 정답이 아니다.

경로: Windows 실제 경로 D:/projects/477 (요청한 /mnt/d/projects/477에 대응). ZIP의 absolute_archive_path::member는 원본 locator이며 실제 디코딩 파일 경로를 별도로 표시한다.

| Event | 총 영상 | Annotation | 평균 XML duration | 실제 영상 메타데이터 확인 |
|---|---:|---:|---:|---:|
| fight | 54 | 54 XML | 310.68s | 6 |
| swoon | 20 | 20 XML | 300.65s | 20 |
| trespass | 44 | 44 XML | 303.20s | 44 |

XML은 MP4와 동일 stem이며 event/starttime+duration, object별 action/frame start/end 및 keyframe/keypoint를 제공한다. bbox와 제한구역 좌표는 없다. 4K/30 FPS는 모든 XML 및 70개 실제 영상 메타데이터에서 확인했다.

## Review priorities

아래 Top 3는 검토 순서 제안이며 최종 선정이 아니다. C는 평범한 이동과 맥락 판단을 우선하고, 담장 넘기 T06/T08은 명확한 비교 표본이다. B에는 명확성이 상대적으로 높은 4개와 차량 가림 조건부 2개가 포함된다. D는 A/C와 일부 영상을 공유하며 독립 샘플 수로 중복 계산하면 안 된다.

- Scenario A Top 3: F01, F02, F05
- Scenario B Top 3: S14, S16, S06
- Scenario C Top 3: T05, T02, T01
- Scenario D Top 3: D05, D04, D06
- Scenario E Top 3: R01, R02, R03

## Scenario A — Clear Fight

Fight 후보 6개는 녹색 스튜디오 배경이다. 신체 충돌 동작을 평가할 수 있으나 실제 현장 CCTV의 배경·자연스러운 위험 맥락에 대한 대표성은 낮다.

### Candidate F01
- Source review ID: F01
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-2/435-2_cam01_fight01_place09_night_spring.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-2/435-2_cam01_fight01_place09_night_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\435-2\435-2_cam01_fight01_place09_night_spring.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-2/435-2_cam01_fight01_place09_night_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\435-2\435-2_cam01_fight01_place09_night_spring.xml](<D:/projects/477/evaluation_selection/tmp/fight/435-2/435-2_cam01_fight01_place09_night_spring.xml>)
- Duration: 312.612s (영상); 312.600s (XML). FPS: 30.0.
- Event interval: 121.5–248.7s (XML, 127.2s).
- Selection reason: 대치→반복 접촉→일부 인물의 바닥 자세가 보이는 전후 흐름으로 Fight 기본 이해를 검토한다.
- Status: review_candidate
- Source actions: falldown, pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [4, 4], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 02:09–03:32 접촉과 자세 변화가 보인다. |
| event_clarity | 4 | 밀기와 가격에 대응하는 동작 및 XML punching/pushing이 일치한다. |
| temporal_value | 5 | 대치와 바닥 자세까지 순서에 따라 의미가 달라진다. |
| visual_quality | 4 | 인물은 식별되며 순간적으로 몸이 겹친다. |
| reasoning_value | 4 | 4명 중 접촉하는 인물과 주변 인물을 구분해야 한다. |
| demo_suitability | 4 | 초기 약 35초 구간에 대치와 접촉이 함께 보인다. |
| ambiguity | 2 | 행동은 비교적 명확하나 스튜디오 연기에서 의도를 단정할 수 없다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F01.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F01.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F01_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F01_temporal.jpg>)
![F01](D:/projects/477/evaluation_selection/contact_sheets/F01.jpg)

### Candidate F02
- Source review ID: F02
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-3/435-3_cam02_fight01_place09_night_summer.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-3/435-3_cam02_fight01_place09_night_summer.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\435-3\435-3_cam02_fight01_place09_night_summer.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-3/435-3_cam02_fight01_place09_night_summer.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\435-3\435-3_cam02_fight01_place09_night_summer.xml](<D:/projects/477/evaluation_selection/tmp/fight/435-3/435-3_cam02_fight01_place09_night_summer.xml>)
- Duration: 302.936s (영상); 302.900s (XML). FPS: 30.0.
- Event interval: 131.9–246.3s (XML, 114.4s).
- Selection reason: 두 쌍의 인물이 있는 장면에서 접촉 주체와 행동 진행을 구분하는 데 유용하다.
- Status: review_candidate
- Source actions: falldown, pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [4, 4], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 02:13 이후 두 인물의 팔 접촉과 밀기가 보인다. |
| event_clarity | 4 | 순차 장면의 접촉이 XML punching/pushing과 대응한다. |
| temporal_value | 5 | 대치→접촉→구도 변화가 이어진다. |
| visual_quality | 4 | 녹색 배경과 밝은 의상으로 사람을 구분할 수 있다. |
| reasoning_value | 4 | 사건 참여자와 관찰자를 시간에 따라 구분해야 한다. |
| demo_suitability | 4 | 02:07 이후 35초 구간을 제안한다. |
| ambiguity | 2 | 접촉 의도에는 연출의 애매함이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F02.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F02.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F02_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F02_temporal.jpg>)
![F02](D:/projects/477/evaluation_selection/contact_sheets/F02.jpg)

### Candidate F03
- Source review ID: F03
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-4/435-4_cam03_fight01_place09_night_winter.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-4/435-4_cam03_fight01_place09_night_winter.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\435-4\435-4_cam03_fight01_place09_night_winter.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-4/435-4_cam03_fight01_place09_night_winter.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\435-4\435-4_cam03_fight01_place09_night_winter.xml](<D:/projects/477/evaluation_selection/tmp/fight/435-4/435-4_cam03_fight01_place09_night_winter.xml>)
- Duration: 309.576s (영상); 309.600s (XML). FPS: 30.0.
- Event interval: 139.5–255.9s (XML, 116.4s).
- Selection reason: 전경 인물의 부분 잘림과 후경 싸움의 거리 차이가 있는 비교 후보이며 D에서도 사용한다.
- Status: review_candidate
- Source actions: falldown, pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [3, 4], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 02:20 후경 접촉은 보이지만 전경 인물은 잘린다. |
| event_clarity | 4 | 후경 신체 충돌이 XML과 대응한다. |
| temporal_value | 4 | 대치와 접촉 이후 두 쌍의 위치가 달라진다. |
| visual_quality | 3 | 카메라 가까운 몸 일부가 프레임 밖에 있다. |
| reasoning_value | 4 | 가까운 사람보다 후경 사건을 주목해야 한다. |
| demo_suitability | 3 | 전체 구도 설명이 필요하여 발표에서는 후순위다. |
| ambiguity | 3 | 후경 거리와 전경 잘림 때문에 순간 해석이 어렵다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F03.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F03.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F03_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F03_temporal.jpg>)
![F03](D:/projects/477/evaluation_selection/contact_sheets/F03.jpg)

### Candidate F04
- Source review ID: F04
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-5/435-5_cam01_fight01_place09_night_spring.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-5/435-5_cam01_fight01_place09_night_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\435-5\435-5_cam01_fight01_place09_night_spring.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-5/435-5_cam01_fight01_place09_night_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\435-5\435-5_cam01_fight01_place09_night_spring.xml](<D:/projects/477/evaluation_selection/tmp/fight/435-5/435-5_cam01_fight01_place09_night_spring.xml>)
- Duration: 315.782s (영상); 315.800s (XML). FPS: 30.0.
- Event interval: 138.8–293.5s (XML, 154.7s).
- Selection reason: 반복 접촉은 보이나 XML 종료 직후에도 접촉이 있어 경계 재검토가 필요한 후보다.
- Status: boundary_review_required
- Source actions: falldown, pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [2, 3], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 02:33 및 03:26 신체 접촉이 보인다. |
| event_clarity | 4 | 반복되는 밀기와 가격 동작이 보인다. |
| temporal_value | 4 | 긴 반복 행동의 전후를 비교할 수 있다. |
| visual_quality | 4 | 두 인물이 비교적 분리되지만 접촉 시 겹친다. |
| reasoning_value | 3 | XML 경계와 화면의 지속 행동을 구분해야 한다. |
| demo_suitability | 3 | 전체 사건이 길고 종료 경계가 불명확하여 후순위다. |
| ambiguity | 3 | 04:59에도 접촉이 보여 종료 판단이 애매하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F04.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F04.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F04_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F04_temporal.jpg>)
![F04](D:/projects/477/evaluation_selection/contact_sheets/F04.jpg)

### Candidate F05
- Source review ID: F05
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-6/435-6_cam02_fight01_place09_night_winter.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-6/435-6_cam02_fight01_place09_night_winter.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\435-6\435-6_cam02_fight01_place09_night_winter.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-6/435-6_cam02_fight01_place09_night_winter.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\435-6\435-6_cam02_fight01_place09_night_winter.xml](<D:/projects/477/evaluation_selection/tmp/fight/435-6/435-6_cam02_fight01_place09_night_winter.xml>)
- Duration: 302.536s (영상); 302.500s (XML). FPS: 30.0.
- Event interval: 54.2–249.3s (XML, 195.1s).
- Selection reason: 초기 두 명의 대치가 접촉으로 변하고 이후 추가 인물이 등장하는 단계가 보인다.
- Status: review_candidate
- Source actions: falldown, kicking, pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [2, 4], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 00:56–01:26 팔 접촉이 보인다. |
| event_clarity | 4 | punching/pushing 및 이후 kicking XML이 존재한다. |
| temporal_value | 5 | 두 명에서 여러 명으로 사건이 진행한다. |
| visual_quality | 4 | 초기 인물은 잘 분리되고 이후 겹침이 증가한다. |
| reasoning_value | 4 | 인원 변화와 접촉 확대를 설명할 수 있다. |
| demo_suitability | 4 | 00:49 이후 초기 충돌 35초가 발표에 적합하다. |
| ambiguity | 2 | 초기 충돌은 명확하나 연출 의도는 확정할 수 없다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F05.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F05.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F05_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F05_temporal.jpg>)
![F05](D:/projects/477/evaluation_selection/contact_sheets/F05.jpg)

### Candidate F06
- Source review ID: F06
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::439-1/439-1_cam01_fight01_place03_day_spring.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::439-1/439-1_cam01_fight01_place03_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\439-1\439-1_cam01_fight01_place03_day_spring.mp4](<D:/projects/477/evaluation_selection/tmp/fight/439-1/439-1_cam01_fight01_place03_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\439-1\439-1_cam01_fight01_place03_day_spring.xml](<D:/projects/477/evaluation_selection/tmp/fight/439-1/439-1_cam01_fight01_place03_day_spring.xml>)
- Duration: 319.519s (영상); 319.500s (XML). FPS: 30.0.
- Event interval: 11.1–253.7s (XML, 242.6s).
- Selection reason: 두 인물의 접근과 반복 접촉이 있으나 화면 내 사람 크기가 작아 보조 후보다.
- Status: review_candidate
- Source actions: pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [2, 2], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 00:43 이후 접촉을 볼 수 있으나 인물이 작다. |
| event_clarity | 4 | 시간순 팔 동작과 XML punching/pushing이 대응한다. |
| temporal_value | 4 | 접근→접촉→이탈이 보인다. |
| visual_quality | 3 | 높은 시점의 넓은 구도에서 신체 세부가 작다. |
| reasoning_value | 3 | 팔 접촉과 단순 접근을 구분해야 한다. |
| demo_suitability | 3 | 큰 발표 화면 또는 확대 검토가 필요하다. |
| ambiguity | 3 | 단일 작은 프레임의 팔 동작은 장난처럼 해석될 수 있다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F06.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F06_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F06_temporal.jpg>)
![F06](D:/projects/477/evaluation_selection/contact_sheets/F06.jpg)


## Scenario B — Clear Swoon

S02/S04는 차량 가림 때문에 조건부 후순위이다. 표본 수를 채우려고 완전히 명확한 사례라고 표시하지 않았다. 누운 상태는 관찰할 수 있지만 의학적 실신 원인이나 의식 상태를 확정할 수 없다.

### Candidate S06
- Source review ID: S06
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-2/710-2_cam01_swoon01_place01_day_summer.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-2/710-2_cam01_swoon01_place01_day_summer.xml>)
- Duration: 297.597s (영상); 297.600s (XML). FPS: 30.0.
- Event interval: 248.3–264.6s (XML, 16.3s).
- Selection reason: 04:11 보행에서 04:13–04:14 넘어짐을 거쳐 04:17 이후 바닥 자세가 유지된다.
- Status: review_candidate
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": true, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 04:11 보행에서 04:13–04:14 넘어짐을 거쳐 04:17 이후 바닥 자세가 유지된다. |
| event_clarity | 4 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 4 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 4 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 2 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S06.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S06_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S06_temporal.jpg>)
![S06](D:/projects/477/evaluation_selection/contact_sheets/S06.jpg)

### Candidate S14
- Source review ID: S14
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-4/710-4_cam01_swoon01_place01_day_summer.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-4/710-4_cam01_swoon01_place01_day_summer.xml>)
- Duration: 315.782s (영상); 315.800s (XML). FPS: 30.0.
- Event interval: 230.6–247.4s (XML, 16.8s).
- Selection reason: 03:50 보행→03:53 넘어짐→04:18까지 누운 자세가 확인된다.
- Status: review_candidate
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": true, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 03:50 보행→03:53 넘어짐→04:18까지 누운 자세가 확인된다. |
| event_clarity | 4 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 4 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 4 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 2 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S14.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S14.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S14_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S14_temporal.jpg>)
![S14](D:/projects/477/evaluation_selection/contact_sheets/S14.jpg)

### Candidate S15
- Source review ID: S15
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_summer.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_summer.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-5/710-5_cam01_swoon01_place01_day_summer.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_summer.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-5/710-5_cam01_swoon01_place01_day_summer.xml>)
- Duration: 303.503s (영상); 303.500s (XML). FPS: 30.0.
- Event interval: 244.2–279.0s (XML, 34.8s).
- Selection reason: 04:22 보행에서 04:27 앉는 듯한 중간 자세를 거쳐 04:32 이후 눕는다.
- Status: review_candidate
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": true, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 04:22 보행에서 04:27 앉는 듯한 중간 자세를 거쳐 04:32 이후 눕는다. |
| event_clarity | 4 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 3 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 4 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 3 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S15.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S15.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S15_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S15_temporal.jpg>)
![S15](D:/projects/477/evaluation_selection/contact_sheets/S15.jpg)

### Candidate S16
- Source review ID: S16
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-6/710-6_cam01_swoon01_place01_day_summer.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-6/710-6_cam01_swoon01_place01_day_summer.xml>)
- Duration: 304.504s (영상); 304.500s (XML). FPS: 30.0.
- Event interval: 243.0–258.9s (XML, 15.9s).
- Selection reason: 04:01 보행에서 04:04–04:07 넘어지고 이후 바닥 자세가 유지된다.
- Status: review_candidate
- Source actions: falldown
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": true, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 04:01 보행에서 04:04–04:07 넘어지고 이후 바닥 자세가 유지된다. |
| event_clarity | 4 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 4 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 4 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 2 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S16.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S16.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S16_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S16_temporal.jpg>)
![S16](D:/projects/477/evaluation_selection/contact_sheets/S16.jpg)

### Candidate S02
- Source review ID: S02
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-3\710-3_cam01_swoon01_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-3\710-3_cam01_swoon01_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-3\710-3_cam01_swoon01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-3/710-3_cam01_swoon01_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-3\710-3_cam01_swoon01_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-3/710-3_cam01_swoon01_place01_day_spring.xml>)
- Duration: 302.169s (영상); 302.200s (XML). FPS: 30.0.
- Event interval: 267.0–286.3s (XML, 19.3s).
- Selection reason: 04:31 보행→04:34 넘어짐은 보이나 몸 일부가 차량에 가려진다.
- Status: conditional_occlusion
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": null, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 04:31 보행→04:34 넘어짐은 보이나 몸 일부가 차량에 가려진다. |
| event_clarity | 3 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 3 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 2 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 3 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S02.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S02.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S02_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S02_temporal.jpg>)
![S02](D:/projects/477/evaluation_selection/contact_sheets/S02.jpg)

### Candidate S04
- Source review ID: S04
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-5/710-5_cam01_swoon01_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-5\710-5_cam01_swoon01_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-5/710-5_cam01_swoon01_place01_day_spring.xml>)
- Duration: 294.761s (영상); 294.800s (XML). FPS: 30.0.
- Event interval: 250.8–267.6s (XML, 16.8s).
- Selection reason: 04:13 이후 넘어지는 과정은 보이나 바닥 자세 대부분이 차량 뒤에 가려진다.
- Status: conditional_occlusion
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": null, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 04:13 이후 넘어지는 과정은 보이나 바닥 자세 대부분이 차량 뒤에 가려진다. |
| event_clarity | 3 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 3 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 2 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 3 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S04.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S04.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S04_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S04_temporal.jpg>)
![S04](D:/projects/477/evaluation_selection/contact_sheets/S04.jpg)


## Scenario C — Temporal Trespass

### Candidate T01
- Source review ID: T01
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-1\146-1_cam01_trespass03_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-1\146-1_cam01_trespass03_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-1\146-1_cam01_trespass03_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-1/146-1_cam01_trespass03_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-1\146-1_cam01_trespass03_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-1/146-1_cam01_trespass03_place01_day_spring.xml>)
- Duration: 301.234s (영상); 301.200s (XML). FPS: 30.0.
- Event interval: 245.5–287.0s (XML, 41.5s).
- Selection reason: 대문 주변의 짧은 조작과 왕복 이동이 보이지만 무단 진입은 영상만으로 확정할 수 없다.
- Status: review_candidate
- Source actions: pulling, walking
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 3], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 대문 주변의 짧은 조작과 왕복 이동이 보이지만 무단 진입은 영상만으로 확정할 수 없다. |
| event_clarity | 3 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 3 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 4 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T01.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T01.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T01_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T01_temporal.jpg>)
![T01](D:/projects/477/evaluation_selection/contact_sheets/T01.jpg)

### Candidate T02
- Source review ID: T02
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-2\146-2_cam01_trespass03_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-2\146-2_cam01_trespass03_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-2\146-2_cam01_trespass03_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-2/146-2_cam01_trespass03_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-2\146-2_cam01_trespass03_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-2/146-2_cam01_trespass03_place01_day_spring.xml>)
- Duration: 304.805s (영상); 304.800s (XML). FPS: 30.0.
- Event interval: 214.8–288.6s (XML, 73.8s).
- Selection reason: 03:40 대문 접근→03:55 이후 낮은 자세 유지→04:43 문 주변 변화가 보인다.
- Status: review_candidate
- Source actions: pulling, walking
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 2], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 03:40 대문 접근→03:55 이후 낮은 자세 유지→04:43 문 주변 변화가 보인다. |
| event_clarity | 3 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 3 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 4 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T02.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T02.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T02_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T02_temporal.jpg>)
![T02](D:/projects/477/evaluation_selection/contact_sheets/T02.jpg)

### Candidate T03
- Source review ID: T03
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-3/146-3_cam01_trespass03_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-3/146-3_cam01_trespass03_place01_day_spring.xml>)
- Duration: 304.304s (영상); 304.300s (XML). FPS: 30.0.
- Event interval: 218.1–288.3s (XML, 70.2s).
- Selection reason: 대문 옆 정지·조작과 일반 통행이 섞여 단일 프레임은 평범한 보행처럼 보인다.
- Status: review_candidate
- Source actions: pulling, walking
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 2], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 대문 옆 정지·조작과 일반 통행이 섞여 단일 프레임은 평범한 보행처럼 보인다. |
| event_clarity | 2 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 2 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 5 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T03.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T03.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T03_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T03_temporal.jpg>)
![T03](D:/projects/477/evaluation_selection/contact_sheets/T03.jpg)

### Candidate T04
- Source review ID: T04
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-4\146-4_cam01_trespass03_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-4\146-4_cam01_trespass03_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-4\146-4_cam01_trespass03_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-4/146-4_cam01_trespass03_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-4\146-4_cam01_trespass03_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-4/146-4_cam01_trespass03_place01_day_spring.xml>)
- Duration: 297.631s (영상); 297.600s (XML). FPS: 30.0.
- Event interval: 212.9–275.4s (XML, 62.5s).
- Selection reason: 여러 번 대문 부근 접근과 이탈이 반복되어 이동 궤적을 비교해야 한다.
- Status: review_candidate
- Source actions: pulling, walking
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 3], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 여러 번 대문 부근 접근과 이탈이 반복되어 이동 궤적을 비교해야 한다. |
| event_clarity | 3 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 3 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 4 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T04.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T04.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T04_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T04_temporal.jpg>)
![T04](D:/projects/477/evaluation_selection/contact_sheets/T04.jpg)

### Candidate T05
- Source review ID: T05
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-5\146-5_cam01_trespass03_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-5\146-5_cam01_trespass03_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-5\146-5_cam01_trespass03_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-5/146-5_cam01_trespass03_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-5\146-5_cam01_trespass03_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-5/146-5_cam01_trespass03_place01_day_spring.xml>)
- Duration: 302.803s (영상); 302.800s (XML). FPS: 30.0.
- Event interval: 280.4–288.2s (XML, 7.8s).
- Selection reason: 04:40 대문으로 접근하여 04:43–04:46 문 경계를 넘어 사라지는 과정이 보인다.
- Status: review_candidate
- Source actions: pulling, walking
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 2], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": true, "restricted_area_status": "not_provided_by_annotation", "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 04:40 대문으로 접근하여 04:43–04:46 문 경계를 넘어 사라지는 과정이 보인다. |
| event_clarity | 4 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 4 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 3 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T05.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T05.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T05_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T05_temporal.jpg>)
![T05](D:/projects/477/evaluation_selection/contact_sheets/T05.jpg)

### Candidate T06
- Source review ID: T06
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-3/145-3_cam01_trespass01_place01_day_summer.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-3/145-3_cam01_trespass01_place01_day_summer.xml>)
- Duration: 297.564s (영상); 297.600s (XML). FPS: 30.0.
- Event interval: 257.8–263.0s (XML, 5.2s).
- Selection reason: 04:18–04:23 담장 외측에서 내측으로 넘어가 이동하는 순서가 보인다.
- Status: review_candidate
- Source actions: climbwall
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 2], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": true, "restricted_area_status": "not_provided_by_annotation", "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 04:18–04:23 담장 외측에서 내측으로 넘어가 이동하는 순서가 보인다. |
| event_clarity | 5 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 4 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 5 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 2 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T06.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T06_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T06_temporal.jpg>)
![T06](D:/projects/477/evaluation_selection/contact_sheets/T06.jpg)

### Candidate T08
- Source review ID: T08
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-4/145-4_cam01_trespass01_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-4/145-4_cam01_trespass01_place01_day_spring.xml>)
- Duration: 295.796s (영상); 295.800s (XML). FPS: 30.0.
- Event interval: 261.3–264.1s (XML, 2.8s).
- Selection reason: 04:21–04:24 접근 후 담장을 넘어 내측으로 내려가며 단일 보행 이미지와 비교하기 좋다.
- Status: review_candidate
- Source actions: climbwall, running
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 3], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": true, "restricted_area_status": "not_provided_by_annotation", "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 4 | 04:21–04:24 접근 후 담장을 넘어 내측으로 내려가며 단일 보행 이미지와 비교하기 좋다. |
| event_clarity | 5 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 4 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 5 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 2 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T08.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T08.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T08_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T08_temporal.jpg>)
![T08](D:/projects/477/evaluation_selection/contact_sheets/T08.jpg)


## Scenario D — Ambiguous Cases

정상/비사건 negative 영상을 새로 만든 것이 아니다. 모두 source positive label이 있는 hard positive이며, false-positive rate 자체를 계산하려면 별도 정상 영상이 필요하다.

### Candidate D01
- Source review ID: F03
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-4/435-4_cam03_fight01_place09_night_winter.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-4/435-4_cam03_fight01_place09_night_winter.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\435-4\435-4_cam03_fight01_place09_night_winter.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-4/435-4_cam03_fight01_place09_night_winter.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\435-4\435-4_cam03_fight01_place09_night_winter.xml](<D:/projects/477/evaluation_selection/tmp/fight/435-4/435-4_cam03_fight01_place09_night_winter.xml>)
- Duration: 309.576s (영상); 309.600s (XML). FPS: 30.0.
- Event interval: 139.5–255.9s (XML, 116.4s).
- Selection reason: 전경 인물의 부분 잘림과 후경 싸움의 거리 차이가 있는 비교 후보이며 D에서도 사용한다.
- Status: review_candidate
- Source actions: falldown, pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [3, 4], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 02:20 후경 접촉은 보이지만 전경 인물은 잘린다. |
| event_clarity | 4 | 후경 신체 충돌이 XML과 대응한다. |
| temporal_value | 4 | 대치와 접촉 이후 두 쌍의 위치가 달라진다. |
| visual_quality | 3 | 카메라 가까운 몸 일부가 프레임 밖에 있다. |
| reasoning_value | 4 | 가까운 사람보다 후경 사건을 주목해야 한다. |
| demo_suitability | 3 | 전체 구도 설명이 필요하여 발표에서는 후순위다. |
| ambiguity | 3 | 후경 거리와 전경 잘림 때문에 순간 해석이 어렵다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F03.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F03.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F03_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F03_temporal.jpg>)
![D01](D:/projects/477/evaluation_selection/contact_sheets/F03.jpg)

### Candidate D02
- Source review ID: F06
- Video (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::439-1/439-1_cam01_fight01_place03_day_spring.mp4`
- Annotation (원본): `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::439-1/439-1_cam01_fight01_place03_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\evaluation_selection\tmp\fight\439-1\439-1_cam01_fight01_place03_day_spring.mp4](<D:/projects/477/evaluation_selection/tmp/fight/439-1/439-1_cam01_fight01_place03_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\evaluation_selection\tmp\fight\439-1\439-1_cam01_fight01_place03_day_spring.xml](<D:/projects/477/evaluation_selection/tmp/fight/439-1/439-1_cam01_fight01_place03_day_spring.xml>)
- Duration: 319.519s (영상); 319.500s (XML). FPS: 30.0.
- Event interval: 11.1–253.7s (XML, 242.6s).
- Selection reason: 두 인물의 접근과 반복 접촉이 있으나 화면 내 사람 크기가 작아 보조 후보다.
- Status: review_candidate
- Source actions: pulling, punching, pushing
- Sampled observations: {"visible_persons_range_in_sampled_frames": [2, 2], "physical_contact_observed": true, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 00:43 이후 접촉을 볼 수 있으나 인물이 작다. |
| event_clarity | 4 | 시간순 팔 동작과 XML punching/pushing이 대응한다. |
| temporal_value | 4 | 접근→접촉→이탈이 보인다. |
| visual_quality | 3 | 높은 시점의 넓은 구도에서 신체 세부가 작다. |
| reasoning_value | 3 | 팔 접촉과 단순 접근을 구분해야 한다. |
| demo_suitability | 3 | 큰 발표 화면 또는 확대 검토가 필요하다. |
| ambiguity | 3 | 단일 작은 프레임의 팔 동작은 장난처럼 해석될 수 있다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\F06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F06.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\F06_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F06_temporal.jpg>)
![D02](D:/projects/477/evaluation_selection/contact_sheets/F06.jpg)

### Candidate D03
- Source review ID: S01
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-2/710-2_cam01_swoon01_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-2/710-2_cam01_swoon01_place01_day_spring.xml>)
- Duration: 299.633s (영상); 299.600s (XML). FPS: 30.0.
- Event interval: 235.2–255.6s (XML, 20.4s).
- Selection reason: 04:02–04:06 넘어짐 이후 몸이 차량 뒤에 가려져 상태 판단에 제한이 있다.
- Status: conditional_occlusion
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": null, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 2 | 04:02–04:06 넘어짐 이후 몸이 차량 뒤에 가려져 상태 판단에 제한이 있다. |
| event_clarity | 3 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 3 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 2 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 4 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S01.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S01.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S01_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S01_temporal.jpg>)
![D03](D:/projects/477/evaluation_selection/contact_sheets/S01.jpg)

### Candidate D04
- Source review ID: S03
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-4/710-4_cam01_swoon01_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-4/710-4_cam01_swoon01_place01_day_spring.xml>)
- Duration: 297.097s (영상); 297.100s (XML). FPS: 30.0.
- Event interval: 241.4–258.8s (XML, 17.4s).
- Selection reason: 04:04–04:06 낮아지는 자세 이후 차량 가림이 커서 앉기와 쓰러짐 구분에 시간이 필요하다.
- Status: conditional_occlusion
- Source actions: falldown, totter
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 1], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": null, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 2 | 04:04–04:06 낮아지는 자세 이후 차량 가림이 커서 앉기와 쓰러짐 구분에 시간이 필요하다. |
| event_clarity | 3 | 보행에서 바닥 자세로 변하는 흐름과 XML falldown이 대응한다. |
| temporal_value | 5 | 보행·자세 전환·낮은 움직임의 후속 장면을 함께 봐야 한다. |
| visual_quality | 3 | 차량이 신체 일부를 가리므로 완전한 자세 관찰에는 제한이 있다. |
| reasoning_value | 5 | 넘어짐과 누운 상태의 지속을 구분하되 의학적 실신 원인은 영상만으로 단정하지 않는다. |
| demo_suitability | 2 | 여름 시점은 전후 흐름을 보여주며 가림이 큰 봄 시점은 후순위다. |
| ambiguity | 4 | 짧은 정지 이미지의 낮은 자세는 앉기와 구분하기 어려우므로 시간순 확인이 필요하다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\S03.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S03.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\S03_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S03_temporal.jpg>)
![D04](D:/projects/477/evaluation_selection/contact_sheets/S03.jpg)

### Candidate D05
- Source review ID: T03
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-3/146-3_cam01_trespass03_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\146-3\146-3_cam01_trespass03_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/146-3/146-3_cam01_trespass03_place01_day_spring.xml>)
- Duration: 304.304s (영상); 304.300s (XML). FPS: 30.0.
- Event interval: 218.1–288.3s (XML, 70.2s).
- Selection reason: 대문 옆 정지·조작과 일반 통행이 섞여 단일 프레임은 평범한 보행처럼 보인다.
- Status: review_candidate
- Source actions: pulling, walking
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 2], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": null, "restricted_area_status": null, "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 3 | 대문 옆 정지·조작과 일반 통행이 섞여 단일 프레임은 평범한 보행처럼 보인다. |
| event_clarity | 2 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 4 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 2 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 5 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T03.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T03.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T03_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T03_temporal.jpg>)
![D05](D:/projects/477/evaluation_selection/contact_sheets/T03.jpg)

### Candidate D06
- Source review ID: T07
- Video (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-1\145-1_cam02_trespass01_place01_day_spring.mp4`
- Annotation (원본): `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-1\145-1_cam02_trespass01_place01_day_spring.xml`
- Video (재생 가능한 절대경로): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-1\145-1_cam02_trespass01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-1/145-1_cam02_trespass01_place01_day_spring.mp4>)
- Annotation (실제 파일): [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-1\145-1_cam02_trespass01_place01_day_spring.xml](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-1/145-1_cam02_trespass01_place01_day_spring.xml>)
- Duration: 302.469s (영상); 302.500s (XML). FPS: 30.0.
- Event interval: 245.6–247.0s (XML, 1.4s).
- Selection reason: 약 1.4초 담장 넘기가 후경에서 발생하여 짧은 행동과 촬영 거리의 영향을 검토한다.
- Status: review_candidate
- Source actions: climbwall
- Sampled observations: {"visible_persons_range_in_sampled_frames": [1, 3], "physical_contact_observed": false, "remains_motionless_in_sampled_frames": false, "boundary_entry_visible": true, "restricted_area_status": "not_provided_by_annotation", "basis": "9-frame event sheet and 24-frame ordered temporal sheet; observations are not continuous measurements"}
- Scores:

| 기준 | 점수 | 이유 |
|---|---:|---|
| event_visibility | 2 | 약 1.4초 담장 넘기가 후경에서 발생하여 짧은 행동과 촬영 거리의 영향을 검토한다. |
| event_clarity | 3 | XML trespass label은 존재하며 출입 권한은 제공되지 않는다. |
| temporal_value | 5 | 접근 위치와 이동 전후를 비교해야 경계 통과 또는 조작을 이해한다. |
| visual_quality | 3 | 주간 주택가 구도는 식별 가능하나 사람은 화면 일부를 차지한다. |
| reasoning_value | 5 | 정상 출입 가능성과 관찰된 이동을 분리하여 설명해야 한다. |
| demo_suitability | 2 | 담장 넘기 표본은 짧게 보여주기 좋고 대문 조작 표본은 맥락 설명이 필요하다. |
| ambiguity | 4 | 접근 권한과 제한구역 정보가 없어 불법성 판단에는 불확실성이 남는다. |

- Contact sheet (9장): [D:\projects\477\evaluation_selection\contact_sheets\T07.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T07.jpg>)
- Temporal sheet (24장): [D:\projects\477\evaluation_selection\contact_sheets\T07_temporal.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T07_temporal.jpg>)
![D06](D:/projects/477/evaluation_selection/contact_sheets/T07.jpg)

## Scenario E — Attention Ranking

원본 약 5분 전체는 동시 재생에 길다. 각 CAM의 아래 35초 구간을 seek해서 동시에 시작하는 가상 테스트를 제안한다. 재생 구간은 평가 제안이며 annotation을 수정한 정답 구간이 아니다. 파일 자르기/복사/동시 촬영 여부를 주장하지 않는다. Fight 구간은 긴 사건의 일부만 포함한다. 위험 우선순위 정답은 미정이다. 제한구역의 법적/운영상 지위는 annotation에 없으며 시각적 경계 통과만 기록한다.

### Combination R01

#### CAM A = swoon (S14)
- Video: [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-4/710-4_cam01_swoon01_place01_day_summer.mp4>)
- Source: `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.mp4`
- Annotation: `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-4\710-4_cam01_swoon01_place01_day_summer.xml`
- Duration: 315.782s; XML event duration: 16.8s.
- Suggested playback: 225.6–260.6s (35.0s).
- Visible persons (sampled min–max): [1, 1]; XML population: 1.
- Physical contact: False; low movement after fall: True; boundary entry visible: None.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\S14.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S14.jpg>)

#### CAM B = fight (F01)
- Video: [D:\projects\477\evaluation_selection\tmp\fight\435-2\435-2_cam01_fight01_place09_night_spring.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-2/435-2_cam01_fight01_place09_night_spring.mp4>)
- Source: `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-2/435-2_cam01_fight01_place09_night_spring.mp4`
- Annotation: `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-2/435-2_cam01_fight01_place09_night_spring.xml`
- Duration: 312.612s; XML event duration: 127.2s.
- Suggested playback: 116.5–151.5s (35.0s).
- Visible persons (sampled min–max): [4, 4]; XML population: 2.
- Physical contact: True; low movement after fall: False; boundary entry visible: None.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\F01.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F01.jpg>)

#### CAM C = trespass (T06)
- Video: [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-3/145-3_cam01_trespass01_place01_day_summer.mp4>)
- Source: `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.mp4`
- Annotation: `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.xml`
- Duration: 297.564s; XML event duration: 5.2s.
- Suggested playback: 252.8–287.8s (35.0s).
- Visible persons (sampled min–max): [1, 2]; XML population: 1.
- Physical contact: False; low movement after fall: False; boundary entry visible: True.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\T06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T06.jpg>)

Reason this combination is useful: 쓰러진 뒤 자세 지속, 여러 인물의 접촉, 담장 통과를 비교하며 서로 다른 관찰 근거로 우선 확인을 설명할 수 있다.

### Combination R02

#### CAM A = swoon (S06)
- Video: [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-2/710-2_cam01_swoon01_place01_day_summer.mp4>)
- Source: `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.mp4`
- Annotation: `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-2\710-2_cam01_swoon01_place01_day_summer.xml`
- Duration: 297.597s; XML event duration: 16.3s.
- Suggested playback: 243.3–278.3s (35.0s).
- Visible persons (sampled min–max): [1, 1]; XML population: 1.
- Physical contact: False; low movement after fall: True; boundary entry visible: None.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\S06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S06.jpg>)

#### CAM B = fight (F02)
- Video: [D:\projects\477\evaluation_selection\tmp\fight\435-3\435-3_cam02_fight01_place09_night_summer.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-3/435-3_cam02_fight01_place09_night_summer.mp4>)
- Source: `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-3/435-3_cam02_fight01_place09_night_summer.mp4`
- Annotation: `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-3/435-3_cam02_fight01_place09_night_summer.xml`
- Duration: 302.936s; XML event duration: 114.4s.
- Suggested playback: 126.9–161.9s (35.0s).
- Visible persons (sampled min–max): [4, 4]; XML population: 2.
- Physical contact: True; low movement after fall: False; boundary entry visible: None.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\F02.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F02.jpg>)

#### CAM C = trespass (T08)
- Video: [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-4/145-4_cam01_trespass01_place01_day_spring.mp4>)
- Source: `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.mp4`
- Annotation: `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-4\145-4_cam01_trespass01_place01_day_spring.xml`
- Duration: 295.796s; XML event duration: 2.8s.
- Suggested playback: 256.3–291.3s (35.0s).
- Visible persons (sampled min–max): [1, 3]; XML population: 1.
- Physical contact: False; low movement after fall: False; boundary entry visible: True.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\T08.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T08.jpg>)

Reason this combination is useful: 짧은 담장 통과와 반복 신체 접촉, 바닥 자세 지속의 서로 다른 시간 특성을 비교한다.

### Combination R03

#### CAM A = swoon (S16)
- Video: [D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted/710-6/710-6_cam01_swoon01_place01_day_summer.mp4>)
- Source: `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.mp4`
- Annotation: `D:\projects\477\data\recovered\19.이상행동CCTV\05.실신(swoon)\실외\extracted\710-6\710-6_cam01_swoon01_place01_day_summer.xml`
- Duration: 304.504s; XML event duration: 15.9s.
- Suggested playback: 238.0–273.0s (35.0s).
- Visible persons (sampled min–max): [1, 1]; XML population: 1.
- Physical contact: False; low movement after fall: True; boundary entry visible: None.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\S16.jpg](<D:/projects/477/evaluation_selection/contact_sheets/S16.jpg>)

#### CAM B = fight (F05)
- Video: [D:\projects\477\evaluation_selection\tmp\fight\435-6\435-6_cam02_fight01_place09_night_winter.mp4](<D:/projects/477/evaluation_selection/tmp/fight/435-6/435-6_cam02_fight01_place09_night_winter.mp4>)
- Source: `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-6/435-6_cam02_fight01_place09_night_winter.mp4`
- Annotation: `D:\projects\477\downloads\fight\19.이상행동CCTV\02.싸움(fight)\실내(원본)\insidedoor_04.zip::435-6/435-6_cam02_fight01_place09_night_winter.xml`
- Duration: 302.536s; XML event duration: 195.1s.
- Suggested playback: 49.2–84.2s (35.0s).
- Visible persons (sampled min–max): [2, 4]; XML population: 2.
- Physical contact: True; low movement after fall: False; boundary entry visible: None.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\F05.jpg](<D:/projects/477/evaluation_selection/contact_sheets/F05.jpg>)

#### CAM C = trespass (T06)
- Video: [D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.mp4](<D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted/145-3/145-3_cam01_trespass01_place01_day_summer.mp4>)
- Source: `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.mp4`
- Annotation: `D:\projects\477\data\recovered\19.이상행동CCTV\07.침입(trespass)\실외\extracted\145-3\145-3_cam01_trespass01_place01_day_summer.xml`
- Duration: 297.564s; XML event duration: 5.2s.
- Suggested playback: 252.8–287.8s (35.0s).
- Visible persons (sampled min–max): [1, 2]; XML population: 1.
- Physical contact: False; low movement after fall: False; boundary entry visible: True.
- Contact sheet: [D:\projects\477\evaluation_selection\contact_sheets\T06.jpg](<D:/projects/477/evaluation_selection/contact_sheets/T06.jpg>)

Reason this combination is useful: 초기 두 사람 충돌과 이후 확대 가능성을 쓰러짐 및 담장 통과와 비교하며 R01과 일부 영상을 공유하는 대안이다.

## Data issues and limitations

- Swoon의 S07–S13은 XML/filename 주간과 실제 야간 영상이 불일치한다. 사건 구간에서도 일치하는 쓰러짐을 확인하지 못해 후보에서 제외했다. 원인을 복구 오류로 단정하지 않으며 원본 pairing 재검증이 필요하다.
- Swoon 11개 XML/영상 길이 차이; 세부 목록은 data_issues.json 및 dataset_structure.md 참조. 시간 오프셋을 임의 보정하지 않았다.
- F04 XML 종료 뒤에도 접촉이 관찰된다. Fight 여러 시점은 XML 시작 전 제스처도 있다. XML 이벤트 경계와 관찰 경계는 별개다.
- Frame 번호는 디코더 0-based이며 source XML의 indexing convention은 확인되지 않았다. seek 결과 실제 frame을 기록하며 한 프레임 수준 양자화로 경계 시점이 BEFORE/AFTER로 표시될 수 있다.
- XML population은 실제 보이는 사람 수와 다를 수 있다. 예: Fight 4명이 보이는 표본의 object/참여자는 일부 인물만 포함한다.
- motionless는 시간순 표본에서 자세 변화가 작다는 관찰이며 지속적 완전 무동작 측정이 아니다.
- 카메라·계절·source ID 간 상관성이 크다. 미래 모델 비교 시 동일 sampling/FPS/ROI/프롬프트 및 재생 구간을 고정하고 related ID를 분리 평가 데이터로 섞지 않아야 한다.
- 전체 Fight ZIP 54개 중 영상 검토는 6개에 한정된다. 후보는 전수 품질 순위가 아니다.

## Temporary extraction and storage

임시 파일을 자동 삭제하지 않았다. 아래 파일은 ZIP에서 재생성할 수 있지만 삭제 전에 사용자가 확인해야 한다. 삭제하면 현재 Fight 로컬 재생 경로가 없어지며 contact sheet/원본 ZIP locator는 남는다.

- `D:\projects\477\evaluation_selection\tmp\fight\435-2\435-2_cam01_fight01_place09_night_spring.mp4` — 382,316,090 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-2\435-2_cam01_fight01_place09_night_spring.xml` — 3,960 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-3\435-3_cam02_fight01_place09_night_summer.mp4` — 378,675,871 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-3\435-3_cam02_fight01_place09_night_summer.xml` — 4,073 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-4\435-4_cam03_fight01_place09_night_winter.mp4` — 366,330,899 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-4\435-4_cam03_fight01_place09_night_winter.xml` — 4,720 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-5\435-5_cam01_fight01_place09_night_spring.mp4` — 394,462,992 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-5\435-5_cam01_fight01_place09_night_spring.xml` — 4,805 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-6\435-6_cam02_fight01_place09_night_winter.mp4` — 377,634,785 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\435-6\435-6_cam02_fight01_place09_night_winter.xml` — 5,227 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\439-1\439-1_cam01_fight01_place03_day_spring.mp4` — 359,710,289 bytes
- `D:\projects\477\evaluation_selection\tmp\fight\439-1\439-1_cam01_fight01_place03_day_spring.xml` — 3,498 bytes

- Fight extracted bytes: 2,259,157,209.
- Temporary listing: [D:\projects\477\evaluation_selection\temporary_files.json](<D:/projects/477/evaluation_selection/temporary_files.json>).
- 현재 총 용량은 storage_summary.json에서 확인할 수 있다.
