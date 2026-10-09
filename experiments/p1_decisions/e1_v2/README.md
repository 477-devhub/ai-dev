# 477 AI E1 — Compact CV State v2 구현 결과

2026-10-09, Asia/Seoul. 범위: 내부 모델 입력 직렬화만. E2 API 실험, Threshold 선택, Router, 백엔드 연결 및 P4 변경은 수행하지 않았다.

`compact-decision-state-v2`와 별도 Serializer를 구현했다. 기존 Canonical 결과의 sample index와 per-frame posture를 재사용하므로 Detector/Tracker/StateBuilder 변경이나 CV 재실행이 필요 없다. 모델의 Suppression·Recall 개선은 측정하지 않았으며 주장하지 않는다.

## 실제 코드 분석과 조사 문서의 차이

기준: `planning/stage1_router_v2_research/report.md` 및 P0 `state_builder.py`, `feature_extractor.py`, `sparse_tracker.py`, P1 `compact_serializer.py`, `p1_pipeline.py`, 양쪽 Schema를 직접 검토했다. 기존 조사 결과의 GT·예측 수치는 Feature 선택이나 Threshold 설정에 사용하지 않았다. 이번 계측에서는 Frozen Calibration/Test·GT·P1/P4 예측 파일을 읽지 않았다.

* Clip 기준 Visibility는 **새 원천 정보가 아니다**. Canonical `detection.visible_fraction_of_clip = observed_frames / camera.frame_count`가 이미 있고 v1에서 빠진다. v2는 observation index로 같은 의미의 값을 재계산한다.
* Canonical/v1 `visible_fraction = observed_frames / (last_frame_index - first_frame_index + 1)`이다. 단일 관측 Track도 1이 될 수 있다. 영상 전체 Coverage나 실제 시간 점유율이 아니다.
* Canonical `duration_sec`는 마지막 sample 시각에 `1/30`초를 더한 값이다. 원본 영상 파일의 정확한 종료 시각을 보장하지 않는다. v2 마지막 관측 나이는 **마지막 sample 시각 기준**이며 duration을 사용하지 않는다.
* v1 `final_posture`는 마지막 **known** 자세를 선택한다. `Standing→Low→Unknown`의 Unknown 끝부분을 드러내지 못한다. v2는 마지막 관측 자세, 마지막 known 자세/시각, 마지막 sample의 관측 여부를 분리한다.
* v1 `_longest_low_run`은 observation Timeline에서 low label만 연속되면 sample 누락을 지나서도 시간차를 누적한다. Canonical `post_transition_low_posture_sec`도 standing이 나오기 전 unknown을 기간에 포함한다. v2는 이 두 입력 필드를 제거하고 인접 sample 양끝의 low 관측 span 및 전체 runs를 제공한다.
* Canonical `_vertical_transition`은 known 관측 중 standing→low 후보를 시간 window에서 찾고 `(downward_change, -duration)` 최대를 선택한다. 이는 인접 sample의 전환이나 연속 fall을 뜻하지 않는다. v2에서도 strongest transition은 보존하며 runs·gap과 함께 해석해야 한다. 변화 confidence는 양끝 posture confidence의 최소값에 링크 affinity factor를 곱한다.
* Canonical `_quality`의 `dropout or 0`은 unavailable dropout을 손실 0처럼 종합 점수에 넣는다. v2는 구성 요소가 불완전하면 `cv_reliability=null`, label=`unknown`을 내보낸다. 새 신뢰도 공식이나 Threshold는 만들지 않았다.
* `prediction_adapter.uncertainties`의 `pose_visibility or 1`은 0/null의 경고를 생략하는 **출력 설명 코드**다. 입력 Serializer나 Router 결정식이 아니다. E1의 입력 변경 범위를 지키고 v1 재현성을 보존하기 위해 이 기존 코드는 그대로 두었다. v2 자체는 visibility=0을 보존하고 null을 정상 값으로 바꾸지 않는다. Downward measurement 또는 basis가 unavailable인 transition/fragment 값에도 normal measurement reliability를 부여하지 않고 limited/unavailable로 표시한다.

## Canonical Feature 전체 범위와 선택

전체 Schema 경로, 타입, Nullable과 v1/v2 필드 참조는 [field_reference.md](field_reference.md)에 있다. v2 신규 필드는 JSON Schema에 `description`, `x-canonical-source`, `x-units`, `x-summary`로 원천·단위·계산법도 명시했다.

| Canonical Feature Group | 원천 / 계산의 의미 | v1 | v2 |
|---|---|---|---|
| generator / input metadata | 모델·코드 해시, input fingerprint, item id, 샘플 프로토콜 | task만 전달 | 동일; 메타데이터와 label-like 정보 제외 |
| camera / sampling | image_size, frame_count, duration, timestamps, median/max interval | 크기·timestamps 제외 | timestamps 추가; index 기반 runs 해석 |
| frames | index/time/frame number, count, image stats, detection bbox/keypoints/confidence/link/posture geometry | raw frame/detection 제외 | 원천으로 재사용; bbox/keypoints 원문은 전달하지 않음 |
| detection_summary | count min/max/median/mean, fraction, total detections, mean confidence | min/max/median/fraction | 기본 요약 유지; Track mean confidence 추가 |
| tracks.detection / reliability | 첫/끝 관측, 관측 수, span/clip visibility, detection confidence, association affinity, max gap, ambiguous count, reliability | clip fraction·detection/association confidence·max gap 누락 | clip/span 명시, gap/leading/tail, detection/association confidence, fragment 후보 수 |
| tracks.observations | `[frame_index,det_index]` | 제외 | 샘플 Coverage 및 posture 재구성의 근거 |
| tracks.geometry | 평균 bbox/center/reference height, center_path, area change, vertical position change | 대부분 제외 | 원문 제외; 이동량은 기존 motion 요약 유지 |
| tracks.motion | normalized/bh speed mean/max, total/net displacement, direction changes, stationary fraction | bh mean/max/net/direction/stationary | 유지; gap을 건너뛰는 sampled displacement임을 명시 |
| tracks.posture | known/pose count/fraction, low fraction, 각 geometry score/angle 평균, count와 confidence Timeline | initial/final known, distribution, longest low run | distribution·initial 유지, runs/basis/min confidence, unknown/회복/마지막 관측 상태 추가 |
| vertical_transition / low_motion | upright→low/horizontal, 최대 drop/basis/time/confidence; 시간 가중 low motion / post transition 기간 | strongest transition, 일부 기간 | strongest 유지; 잘못 연속성으로 읽기 쉬운 low posture 기간 교체 |
| pairwise_interactions | co-observation, distance series/min/mean, approach/rate/events, proximity, overlap, relative motion, arm/limb/contact proxy | 일부 scalar와 limited proxy | co Coverage, 인접 close span, 거리 변화율, relative motion mean 및 contact proxy 측정 항 수 추가 |
| scene_observations | entry/exit/large movement, occlusion 후보, fragment 링크, boundary/ROI unavailable | 대부분 요약; links cap4 | 기본 유지; 전체 대비 제외 집계 추가 |
| quality | brightness/contrast/sharpness, dark/small fraction, pose visibility/dropout/fragmentation/occlusion, aggregate | 일부 scalar | 영상 통계 추가; aggregate completeness 명시 |
| cross_camera | phase count/activity/low curves, similarities, visibility complement/drop, signature | 기초 similarity/phase count만; signature 제외 | 동일; 동기화·동일인 미확인 유지 |

### Temporal / Motion / Quality 공식

P0 SparseTracker는 실제 timestamp delta로 distance gate를 계산하고 motion/IoU/size/pose/HSV affinity를 가중 평균한다. 사용 불가능한 affinity 항은 가중치 합에서 제외한다. Hungarian assignment(Scipy 없으면 deterministic greedy) 후 낮은 affinity 링크는 거절하고 rival affinity margin이 작으면 ambiguous로 표시한다. Fragment는 병합하지 않는다.

Track association confidence는 연결된 affinity 평균이다. Canonical reliability는 `association × span visibility × min(1, observations/min_reliable_observations) × ambiguity penalty`이고 관측 2개 미만이면 null이다. identity가 맞을 확률로 보정된 값이 아니다. v2는 association unavailable이면 reliability도 null/unknown으로 내보낸다. 기존 Track 선택의 null→0은 **정렬 점수에만** 적용되며 측정값을 0으로 출력하는 동작과 구분한다.

Motion은 관측 center displacement / 실제 시간차다. `fh`는 영상 높이, `bh`는 근처 upright bbox 높이의 reference 또는 Track bbox height P90에서 나온 reference height다. `stationary_fraction`은 속도가 기존 low-motion threshold보다 작은 interval의 **개수 비율**, `low_motion_fraction`은 **시간 가중 비율**이다. Gap을 사이에 둔 endpoint displacement도 포함하므로 작은 값이 중간의 무동작을 입증하지 않는다. 기존 motion 기간은 그대로 보존하고 이 제한을 `evidence_semantics`에 명시했다.

Pair distance는 center 간 2D 거리 / 두 reference height 평균이다. Canonical close duration은 양끝 close=true인 co-observed interval 중 tracker max_gap 이하인 시간차의 합으로, 중간 미관측 sample을 포함할 수 있다. v2 close span은 **sample index까지 인접**한 양끝 close 관측만 합한다. 실제 접촉 시간은 계산하지 않는다. 새 distance change rate는 인접 pair의 거리 변화 합 / 시간차 합이며 양수=멀어짐, 음수=가까워짐이다. 상대 motion은 두 center velocity 벡터 차이 norm의 Canonical 평균을 재사용한다.

Contact proxy는 bbox overlap 기반 항 / wrist-over-box 항 / relative-motion 항을 사용하고, unavailable 항은 가중치에서 빠진다. v2는 3개 중 측정 가능한 항 개수를 보존하여 일부 항만으로 계산된 score를 구분한다. Arm extension은 2D shoulder/wrist geometry, rapid limb는 torso 기준 sparse wrist displacement로 aliasing과 saturation 한계가 있다. 모두 limited proxy이며 충돌·폭행·의도·동일인 확정 Feature를 만들지 않았다.

Camera dropout은 관측 2개 이상 Track의 `1 - mean(span visible_fraction)`이다. 전체 영상의 검출 실패율이 아니다. Fragmentation은 multi-observation Track 수 / sample person count P90에서 만든 proxy이고 occlusion은 bbox overlap과 mid-frame disappearance 후보의 혼합이다. 작은 person bbox 비율 및 어두운 frame 비율은 기존 설정을 쓴다. v2는 이 Threshold를 바꾸지 않는다. Brightness=grayscale 평균, contrast=grayscale 표준편차, sharpness=Laplacian variance다.

## v2 주요 필드 / Unknown 의미

| 필드 | 타입 / Nullable | 의미·단위 / 계산 |
|---|---|---|
| `coverage.clip_sample_fraction` | number, non-null | 전체 sample 대비 할당 관측 비율; 실제 시간 Coverage 아님 |
| `coverage.span_sample_fraction` | number/null | 첫~끝 sample 범위 대비 관측 비율; 관측 없음 null |
| `missing_inside_span_samples`, `max_missing_run_samples` | integer, non-null | 내부 누락 수 / clip 전체 최대 누락 run; 후자는 leading/tail 포함 |
| `max_gap_bracket_sec` | number/null | 내부 누락을 둘러싼 관측 시간차 최대; 누락 없으면 0초 |
| `max_observation_interval_sec` | number/null | 모든 연속 관측 시간차 최대; 2개 미만 null |
| `leading_unobserved_samples`, `tail_unobserved_samples` | integer, non-null | 첫 관측 전 / 마지막 관측 후 미관측 sample 수 |
| `last_sample_age_sec` | number/null | 마지막 sample 기준 마지막 관측 나이(초); 관측 없음 null |
| `temporal.runs` | tuple array, non-null | `[start_index,end_index,posture,min_confidence,bases]`; 시간은 sampling timestamps와 연결; 모든 변화/gap 보존 |
| `low_observed_samples`, `unknown_posture_samples` | integer, non-null | low 계열 자세 관측 / unresolved 자세 관측 수 |
| `low_adjacent_span_sec`, `longest_low_adjacent_span_sec` | number/null | 인접 sample의 low 계열 관측 시간차 합 / 최대 run span(초); gap/unknown 단절 |
| `last_observed_posture` | enum/null | 마지막 검출의 자세, unknown 포함 |
| `last_known_posture`, `last_known_posture_sec` | enum/null, number/null | 마지막 resolved 자세와 그 시각; 최신 상태 보장 아님 |
| `last_sample_posture` | enum, non-null | 마지막 sample에서 관측한 자세 또는 `not_observed` |
| `low_to_standing_observations` | tuple array, non-null | `[last_low_sec,standing_sec,missed_samples,unknown_samples_between]`; []는 회복 관측 없음 |
| `mean_detection_confidence`, `association_confidence` | number/null | Canonical 평균 detection score / link affinity; 0 보존 |
| `fragment_link_candidates` | integer, non-null | 해당 track과 연결되는 전체 fragment 후보 수; 동일인 확정 아님 |
| `quality.aggregate_inputs_complete` | boolean | 주요 종합 신뢰도 구성 항이 모두 non-null인지; 낮은 측정값 0은 available |
| `quality.mean_brightness/contrast/sharpness` | number/null | Canonical 영상 통계 직접 전달; 단위는 위 공식 참조 |
| `interaction.coverage` | object | 관측 index 교집합으로 산출한 pair sample Coverage |
| `close_adjacent_span_sec` | number/null | 인접 sample 양끝 close의 시간차 합(초), 접촉 기간 아님 |
| `distance_change_bh_per_sec` | number/null | 인접 co-observed pair 거리 변화율; 인접 interval 없음 null |
| `relative_motion_mean_bh_per_sec` | number/null | 기존 Canonical 상대 velocity 차이 norm 평균 |
| `contact_proxy_terms_available` | integer 0..3 | contact proxy 구성 항 중 측정 가능한 개수 |
| `selection_coverage.*` | integer, non-null | 원본/포함/제외 track/pair/link 개수와 제외된 low/transition/unknown/close/fragment posture 관측 수 |

`null`은 measurement unavailable, `unknown`은 검출되었으나 자세 미해결, `not_observed`는 그 sample에 할당된 검출이 없음을 뜻한다. `low_confidence`는 **원본 posture basis**를 그대로 보존한다. Known standing/low도 자동 자세 proxy이며 incident Normal/Abnormal 판정과 같지 않다. 임의로 `Observed Normal` 또는 `Observed Abnormal` 사건 label을 부여하지 않았다.

Runs는 동일 자세 및 인접 sample에서만 합친다. 최소 confidence는 일부 sample confidence가 null이면 null이고 basis는 정렬된 고유 목록이다. 하나의 low sample은 관측 수 1이지만 span은 0초다. `0초`는 실제 low 사건의 기간이 0이라는 의미가 아니다. Unknown·gap 이후 standing이 관측되면 회복 관측을 기록하되 중간 unknown/미관측 수를 함께 남긴다. 그 앞의 low 관측도 삭제하지 않는다.

### Selection / Truncation

기존 제한 **Tracks6 / Pairs4 / Fragment links4**와 선택 규칙을 유지했다. Track은 최소2관측 후 `observed_frames × reliability × span_visibility`, 동률은 작은 track 번호다. Pair는 양쪽 Track 포함 및 최소2 co-observation 후 `close_fraction × co_observed_frames × reliability`, 동률은 작은 minimum distance 및 pair id다. Fragment 링크는 기존 순서에서 양쪽 Track 포함인 것만 cap4를 적용한다.

새 `selection_coverage`는 min-observation filter, endpoint filter, cap으로 제외된 것을 모두 집계한다. 제외된 Track의 low/standing→low/unknown 관측, 제외 Pair의 close sample, 제외 Fragment의 posture change 개수는 전체 Canonical을 대상으로 계산한다. **Hazard evidence의 존재 가능성을 나타내는 관측 집계이며 위험 또는 NORMAL 결정식이 아니다.** Track나 Pair 상세가 빠졌다는 한계는 여전히 남는다.

## Before / After 예시

같은 synthetic Canonical 입력을 두 Serializer에 넣었다. 기존 unlabeled Canonical은 구조 template로만 활용했고, 예시의 관측은 인위적으로 구성했다. Synthetic에서 motion/transition 측정을 하지 않은 값은 null이다. 실제 detector가 이 영상을 처리했다는 의미가 아니다.

64 samples(0~63초) 중 61/62/63초만 Track을 관측한 경우:

| 근거 | Compact v1 | Compact v2 |
|---|---|---|
| Coverage | visible_fraction=1 | clip_sample_fraction=.047, span_sample_fraction=1, leading_unobserved_samples=61 |
| A: standing→horizontal→standing | final_posture=standing; 회복 시각 목록 없음 | last_sample_posture=standing; recovery=`[[62,63,0,0]]`; low_observed_samples=1 |
| B: standing→horizontal→unknown | final_posture=horizontal (known만 선택) | last_observed/last_sample_posture=unknown; last_known=horizontal at62s; recovery=[] |
| dropout unavailable | 종합 reliability=.85/high를 그대로 전달 | aggregate_inputs_complete=false; reliability=null/unknown |
| 연속성 | low run의 sample 누락을 구분하지 않음 | runs가 누락 index에서 분리되고 gap/tail 숫자를 함께 전달 |

전체 출력: [recovery.canonical.json](recovery.canonical.json), [recovery.v1.json](recovery.v1.json), [recovery.v2.json](recovery.v2.json), [unknown_tail.canonical.json](unknown_tail.canonical.json), [unknown_tail.v1.json](unknown_tail.v1.json), [unknown_tail.v2.json](unknown_tail.v2.json).

## 사용 방법 / E2 Handoff

```powershell
python experiments/p1_decisions/scripts/build_compact_version.py --input experiments/p0_cv_only/states/ITEM_01.json --version v2 --output experiments/p1_decisions/e1_v2/local.v2.json
python experiments/p1_decisions/scripts/build_compact_version.py --input experiments/p0_cv_only/states/ITEM_01.json --version v1 --output experiments/p1_decisions/e1_v2/local.v1.json
python -m unittest discover -s experiments/p1_decisions/tests -v
python experiments/p1_decisions/scripts/compare_compact_v2.py
python experiments/p1_decisions/scripts/document_compact_v2.py
```

CLI는 P1의 기존 Canonical read allowlist를 지키며 출력은 E1 폴더 아래에만 쓴다. 새 Development Canonical은 E2의 실험 harness가 직접 읽어 아래 함수를 사용할 수 있다. 기존 Frozen allowlist를 E1에서 확대하지 않았다.

```python
from compact_versions import prepare_compact

a = prepare_compact(canonical_state, version='v1')
c = prepare_compact(canonical_state, version='v2')
# returns compact, input_text, compact_sha256; both validate their own JSON Schema
# same Canonical input; no client import / API calls / decisions here
```

Original P1 question config와 `model_input_preamble`은 그대로다. `task`, `cameras[].camera`, text input 구조도 유지하므로 기존 `build_questions`에 같은 task/camera 목록을 전달할 수 있다. JSON 내부의 `evidence_semantics`는 새 관측 필드의 의미 설명이다. E2 A/B는 v1, C/D는 v2를 명시적으로 선택하고 질문 config만 실험별로 분리한다. **기존 `P1Pipeline`은 v1 default를 계속 사용한다.**

v2는 제거된 v1 필드가 있으므로 **기존 `P1Pipeline.adapt(v2, ...)` 및 v1 `prediction_adapter`를 그대로 호출하는 방식은 지원하지 않는다.** E2 판단 비교는 기존 `DecisionAdapter`의 typed answer 변환을 그대로 사용할 수 있다. 기존 benchmark explanation이 필요하면 같은 Canonical에서 생성한 v1을 그 설명 renderer에 별도로 전달하고, 이를 v2 evidence 설명으로 보고해서는 안 된다. v2용 관측 설명 renderer는 후속 harness 작업이다. 이번 E1에서 백엔드 출력·판단 contract 또는 기존 설명 코드를 수정하지 않았다.

권장 Ablation Group은 (1) clip/span/gap/tail coverage, (2) posture runs/recovery/unknown/basis, (3) detection/association/aggregate completeness 및 image stats, (4) interaction coverage/distance/contact-term completeness, (5) omission summaries다. 검증해야 할 가설은 관측 범위와 자세 회복의 구분이 Safe-to-Suppress 판단에 도움이 되는지, 비용에 비해 runs/basis 전체가 필요한지, 제외 요약이 정보 손실에 대한 과도한 확신을 줄이는지다. 현재 어느 Group의 성능 효과도 확인하지 않았다.

남은 Scene Semantics: gate/wall/ROI·restricted zone·authorization·camera calibration·깊이·인체 충돌/폭행 의도·정확한 의료 상태·cross-camera identity/sync가 없다. Co-movement와 Track의 시간별 bh speed trend는 이번에 새로 정의하지 않았다. Endpoint motion 및 distance trend만으로 의미 있는 동행/충돌을 판정하기 어렵고 reference-height 일관성·association 품질 검증이 더 필요하다. 새로운 learned action Feature를 추가하지 않았다.

Human annotation/추가 데이터 후보: 실제 자세 전환 및 회복 시각, Unknown/occlusion 구간, fragmented Track identity, 근접 vs 물리 contact 구분, low-confidence 자세의 실제 상태, 관측되지 않은 영상 마지막 구간, scene ROI/authorization, 카메라 시각 동기화. 새 Development에서 Feature/질문을 선택하고 별도 Calibration 및 독립 Test를 유지해야 한다. Frozen GT·예측으로 선택/튜닝하지 않는다.

## 검증 결과

[test_results.json](test_results.json): **21 tests, failures0, errors0, skipped0**. Canonical 샘플 7개의 원본 Schema와 v1/v2 출력 Schema 검사, 기존 저장 v1 JSON과 canonical JSON byte-identical 비교, input 불변성, deterministic digest/text, null/0/unknown/low-confidence basis, sample gap/clip span/leading/tail, low 계열 변화, recovery vs unknown, max6/4/4 및 min filter/누락 관측 집계, pair gap/distance/contact terms, empty camera Unknown, 잘못된 source reference/timestamp/pair alignment 거부를 검증했다.

실제 API 수락·모델 판단 성능·Suppression·실제 청구 token·API latency·full cascade latency는 검증하지 않았다. 7개 샘플은 기존 `p0_cv_only/states/ITEM_01..07.json`이며 Frozen triage Test 재평가가 아니다. Frozen GT·예측은 검증 입력으로 사용하지 않았다.

## Token / Serialization 영향

[comparison.json](comparison.json): 동일 Canonical 7개, 버전별 warmup10회와 serialize+canonical JSON+preamble 100회 측정. 다음 시간은 **샘플별 중앙값들의 평균**이며 I/O, Schema validation, CV, 모델 API, 네트워크/큐 대기를 제외한다.

| 평균 | v1 | v2 | 변화 |
|---|---:|---:|---:|
| compact JSON bytes | 6,878.9 | 12,076.4 | +5,197.6 (+75.6%) |
| JSON tokenizer tokens | 1,974.1 | 3,576.9 | +1,602.7 |
| input text tokenizer tokens (원래 preamble 포함) | 2,143.1 | 3,745.9 | +1,602.7 (+74.8%) |
| serialization ms | 0.2966 | 1.0449 | +0.7483ms |

`tiktoken 0.11.0 / o200k_base`의 실계측이다. 공개 vocabulary SHA256를 검증하여 Git에서 제외된 로컬 cache에 저장했다. **GPT-6 Luna / Decisions의 실제 billing tokenizer 및 요청 envelope와 질문 overhead는 확인하지 않았으므로 API Input Tokens는 추정치다.** Tokenizer 사전이 없고 다운로드할 수 없는 환경에서는 비교 스크립트가 bytes/4 heuristic으로 fallback하고 JSON에 방법을 명시한다.

저장소의 frozen Decisions 입력 요금 `$0.10 / 1M tokens`가 그대로라는 가정에서 평균 추가 비용은 약 **$0.00016027 / request**이다. 현재 요금 확인이나 실제 청구 측정값이 아니다. API 호출0회이고 latency 변화 역시 측정하지 않았다. CPU serialization 증가는 작지만 token 증가는 의미 있게 크다. 전체 64 sample을 무조건 풀어 보내는 대신 index runs와 최소 confidence/basis를 묶었고, bbox/keypoints/center_path 원문·frame별 detection을 제외했으며 객체 cap도 늘리지 않았다. 더 줄일 수 있는 Feature는 E2에서 판단 성능과 비용을 함께 검증해야 한다.

## 변경 파일 및 병렬 작업 경계

모든 E1 변경은 **새 파일**이다. 작업 시작 시 이미 존재했던 untracked `planning/`, `experiments/team_frozen_v1/`는 이 작업의 변경물이 아니다.

| 새 파일 | 목적 |
|---|---|
| `src/compact_serializer_v2.py` | v1 선택 로직을 재사용하는 v2 observation serializer |
| `src/compact_versions.py` | explicit v1/v2 offline 준비·Schema 검사·text/digest |
| `schemas/compact_decision_state_v2.schema.json` | standalone strict v2 Schema, 타입·null·원천·단위 설명 |
| `scripts/build_compact_version.py` | version 선택 CLI, E1 폴더 출력 제한 |
| `scripts/compare_compact_v2.py` | label-free token/bytes/serialization 비교 및 synthetic 예시 생성 |
| `scripts/document_compact_v2.py` | Canonical/v1/v2 전체 필드 목록·참조 생성 |
| `tests/test_compact_v2.py` | offline regression/evidence tests |
| `e1_v2/README.md`, `field_reference.md` | 설계·실제 코드 분석·필드 설명·한계·E2 인계 |
| `e1_v2/comparison.json`, `test_results.json` | 실행 검증 및 계측 결과 |
| `e1_v2/recovery.{canonical,v1,v2}.json`, `unknown_tail.{canonical,v1,v2}.json` | 동일 입력 Before/After 예시 6개 |
| `e1_v2/.gitignore` | tokenizer 사전 cache를 Git 변경물에서 제외 |

기존 v1 Schema/Serializer/config/preamble/P1 Pipeline/questions/model/API 설정·Threshold·Routing·P0·P4·Frozen Benchmark/Calibration/Test 및 백엔드 Output Contract 파일은 수정하지 않았다. `NORMAL→SUPPRESS`, `SUSPICIOUS→ESCALATE_P4`, `DANGER→HUMAN_IMMEDIATE`와 외부 필드 계약을 변경하거나 운영 적용하지 않았다. 백엔드-AI 연동 작업 영역에도 파일을 쓰지 않았다.
