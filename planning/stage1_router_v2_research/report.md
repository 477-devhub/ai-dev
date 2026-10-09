# 477 AI — Stage 1 Safe-to-Suppress Router v2 사전 조사

조사일: 2026-10-09, Asia/Seoul. 기준 저장소: `D:\projects\477`; 보조 계약 확인: `D:\projects\477_team_benchmark_v1`.

**결론: 당장의 0건 Suppression은 모든 Test 입력이 고정 `p_incident ≤ 0.01` 조건을 실패한 결과다. 그러나 해결책을 Threshold 완화로 좁힐 근거는 없다. 기존 Calibration에서 0.01→0.025→0.05로 바꿔도 Suppression은 2건 그대로였고, 그 2건은 모두 사람이 검출되지 않은 화면이었다. 사람이 있는 정상 상황을 설명할 정보와, 그 정보를 안전한 제거 판단으로 연결하는 질문·정책의 결합이 우선 병목이다.**

P1 + P4 조합은 유지한다. 우선 새 Development 데이터에서 동일 P1의 Safe-to-Suppress 질문과 최소 관측 정보 보강을 분리 실험하고, 이후 별도 Calibration과 독립 Safety Test를 거쳐야 한다. 검증된 NORMAL만 제거하고, 위험 신호는 즉시 Human, 해소되지 않은 불확실성은 P4로 보내는 Hybrid Router를 추천한다. 향상률은 아직 측정되지 않았다.

이번 작업은 기존 파일의 읽기와 기존 결과의 고정 정책 진단만 수행했다. Production 코드, 기존 Prompt, Threshold, Benchmark, Frozen Test를 수정하지 않았고 모델 API를 호출하지 않았다. 새 파일은 이 조사 디렉터리의 보고서, 읽기 전용 진단 스크립트, 진단 JSON뿐이다. Frozen Test의 대체 Threshold 평가·Prompt 평가·정책 선택은 수행하지 않았다.

근거 표시는 **[확인]**=코드/저장 결과로 확인, **[해석]**=확인된 패턴의 설명, **[가설]**=새 실험으로 검증할 개선 효과, **[미확인]**=현재 자료로 확인할 수 없는 내용이다. Test의 추가 집계는 기존 고정 조건의 원인 진단이며 새로운 최종 평가 결과로 취급하지 않는다. 이번 조사로 Test 특성을 보았으므로 향후 모델 선택·튜닝·안전성 주장에는 새 Test가 필요하다.

## 1) Current Architecture Audit

### 1.1 실제 실행 구조와 운영 설계의 차이

```text
현재 Frozen triage 실험
이미 선정된 37개 단일 카메라 clip
  ├─ 64장 고정 프레임 → Cheap CV → Canonical CV State
  │                         → Compact State → P1 typed answers → decision 저장
  └─ 동일 64장 → P4 Direct Vision → decision 저장

Calibration 15개 결과 → 라우팅 정책 잠금
Test 22개 결과 → 고정 can_suppress 검사 → 나머지 P4 저장 결과 사용
```

**[확인] 이 저장소에서 검증된 것은 후보 선정 이후의 실험 Pipeline이다.** 운영 RTSP 입력, Stage 0의 실제 Candidate 생성·발생률·재알림 억제, 백엔드 큐 연결, 라이브 P1→P4 조건부 호출은 확인되지 않았다. 설계 문서도 기존 Benchmark가 Candidate Detector 자체를 평가하지 않는다고 명시한다. [실험 계획](</D:/projects/477/477_AI_Cost-Accuracy_Experiment_Plan_P0-P4_v2.md:35>)

Frozen worker는 CV 생성 시 `rule_engine_executed: false`를 기록한다. P0의 `RuleEngine`은 CV-only 비교 실험의 판단기이며, 현재 Frozen triage에서 P1의 Safety Override로 연결되어 있지 않다. [worker.cv](</D:/projects/477/experiments/triage_frozen_v1/scripts/worker.py:7>), [RuleEngine.assess_camera](</D:/projects/477/experiments/p0_cv_only/src/rule_engine.py:22>)

P1과 P4는 Calibration/Test 각각 모든 후보에서 실행되었다. `routed_to_p4`는 사후 정책상 호출 수이며 실제 절약된 API 호출 수가 아니다. Calibration은 정책상 13/15이지만 실제 P4 추론은 15건, Test는 정책상·실제 모두 22건이다. 이 실험은 조건부 Cascade의 효과를 저장 결과로 계산한 것이며 실시간 지연·실제 호출 절감 실험은 아니다. [worker.models](</D:/projects/477/experiments/triage_frozen_v1/scripts/worker.py:39>), [analyze.evaluate](</D:/projects/477/experiments/triage_frozen_v1/scripts/analyze.py:20>)

| 항목 | 운영 설계/기대 | 실제 구현/검증 범위 |
|---|---|---|
| Stage 0 | Cheap CV Candidate Filter | 미리 선택된 clip 전체에 CV; Candidate Recall·발생률 미측정 |
| Stage 1 | NORMAL/SUSPICIOUS/DANGER Router | P1은 확률·category·risk·review를 반환; 최종 Router는 분석 스크립트의 Suppress/그 외 P4 |
| Safety Rules | 명확한 위험은 Override | Frozen triage에 P0 RuleEngine 미연결; Suppress 가드만 존재 |
| DANGER 즉시 Human | P4를 기다리지 않음 | 직접 위험 분기 disabled; 높은 P1 점수도 P4로 전달 |
| P4 호출 | SUSPICIOUS에만 호출 | 모든 clip에서 추론, 사후 라우팅 시뮬레이션 |
| 오류 | P4 또는 Human으로 Fail-safe | worker는 오류에서 batch 중단·실패 기록; 실제 큐 전송 미구현 |
| 출력 계약 | Output Contract v1 | 현재 실험 prediction/result와 별개; 제시된 Router envelope 구현 없음 |

기존 설계의 High Risk 즉시 Queue 및 P1 오류 시 P0 유지 원칙과 실제 batch 실패 처리는 구분해야 한다. [안전 라우팅/실패 설계](</D:/projects/477/477_AI_Cost-Accuracy_Experiment_Plan_P0-P4_v2.md:1082>)

### 1.2 핵심 코드 위치

| 책임 | 파일·함수·위치 | 실제 동작 |
|---|---|---|
| Shared CV State 생성 | [state_builder.py:50](</D:/projects/477/experiments/p0_cv_only/src/state_builder.py:50>) `StateBuilder.build`; `._camera_state`:100 | decode → person/pose → sparse association → per-camera features → cross-camera summary |
| 검출/pose | [pose_detector.py:66](</D:/projects/477/experiments/p0_cv_only/src/pose_detector.py:66>) `PoseDetector.detect`; [CV config](</D:/projects/477/experiments/p0_cv_only/configs/cv_state_v1.yaml:7>) | YOLO26n-pose 한 모델; imgsz1280, conf0.25, batch16; CUDA FP16 가능 |
| Tracking | [sparse_tracker.py:105](</D:/projects/477/experiments/p0_cv_only/src/sparse_tracker.py:105>) `SparseTracker.run` | 실제 시간 간격, 위치/IoU/크기/pose/HSV affinity; Hungarian, scipy 없으면 greedy; fragment를 합치지 않음 |
| CV Feature | [feature_extractor.py:204](</D:/projects/477/experiments/p0_cv_only/src/feature_extractor.py:204>) `_track_features`; posture:294, transition:326, pairwise:442, scene:551, quality:604 | 좌표·confidence·자세 timeline·motion·근접 proxy·entry/exit·quality |
| 원본/Compact Schema | [Canonical Schema](</D:/projects/477/experiments/p0_cv_only/schemas/canonical_cv_state.schema.json>), [Compact Schema](</D:/projects/477/experiments/p1_decisions/schemas/compact_decision_state.schema.json>) | `cv-state-v1` → `compact-decision-state-v1` |
| Compact 직렬화 | [compact_serializer.py:25](</D:/projects/477/experiments/p1_decisions/src/compact_serializer.py:25>) `serialize`; `.camera`:61, `.track`:102, `.interactions`:160, `.scene`:188 | 결정론적 JSON, 최대6 tracks/4 pairs/4 fragment links, 소수3자리; 메타데이터/P0 판단 제거 |
| 입력·질문 생성 | [p1_pipeline.py:36](</D:/projects/477/experiments/p1_decisions/src/p1_pipeline.py:36>) `prepare`; [decisions_client.py:26](</D:/projects/477/experiments/p1_decisions/src/decisions_client.py:26>) `build_questions` | preamble+Compact JSON, 질문별 scope/instructions/policy; Compact Schema 검사 |
| P1 API | [decisions_client.py:67](</D:/projects/477/experiments/p1_decisions/src/decisions_client.py:67>) `DecisionsClient.decide` | `gpt-6-luna`, `/v1/decisions`, text only, 기본1 request/item |
| P1 의미 변환 | [decision_adapter.py:21](</D:/projects/477/experiments/p1_decisions/src/decision_adapter.py:21>) `assessment` | p_incident·risk·priority·confidence·review 계산 |
| 설명/기존 prediction | [prediction_adapter.py:99](</D:/projects/477/experiments/p1_decisions/src/prediction_adapter.py:99>) `single_prediction` | 관측·reason·uncertainties는 CV/답변의 결정론적 템플릿; P1 자유 생성 설명 아님 |
| Frozen Suppress | [analyze.py:9](</D:/projects/477/experiments/triage_frozen_v1/scripts/analyze.py:9>) `can_suppress` | p≤T + no review + no refusal + no_clear_incident + confidence≥.90 |
| Calibration/잠금 | [analyze.py:36](</D:/projects/477/experiments/triage_frozen_v1/scripts/analyze.py:36>) `calibrate`; `test`:67 | Calibration만 선택; 정책 잠금 및 해시, Test 최종 평가 이미 존재하면 재실행 거부 |
| P4 분석/변환 | [p4_pipeline.py:44](</D:/projects/477/experiments/p4_gpt61_sol_vision/src/p4_pipeline.py:44>) `prepare`; `adapt`:65 | 64 원본 RGB→lossless WebP/roundtrip 확인; strict JSON schema, frame_ref 근거; P1 adapter+common adapter 사용 |
| P4 호출/실패 | [openai_client.py:53](</D:/projects/477/experiments/p4_gpt61_sol_vision/src/openai_client.py:53>) `ResponsesClient.decide`; `classify`:26 | GPT-6.1 Sol, Responses high reasoning; refusal/incomplete/parse_failure 구분 |
| 최종 Human 여부 | [analyze.py:15](</D:/projects/477/experiments/triage_frozen_v1/scripts/analyze.py:15>) `surface_p4` | P4 `is_incident OR human_review_required OR refused_questions` |

### 1.3 Score, 질문, 가드의 의미

단일 카메라의 현재 P1은 7개 독립 질문을 같은 request에 넣는다. `incident` predicate, `incident_category` choice, severity/imminence/exposure/persistence score 네 개, `human_review` predicate다. attention은 22개, multi-camera는 10개다. Frozen triage 37개는 모두 single이므로 7개 질문이다. [질문 정의](</D:/projects/477/experiments/p1_decisions/configs/decisions_questions_v1.json:12>)

```text
p_incident = incident predicate의 probability 원값
is_incident = p_incident >= 0.5
risk_axis = clip(score / (levels - 1), 0, 1)  # 현재 5 levels
priority = .35*severity + .30*imminence + .20*exposure + .15*persistence
confidence = mean(category.confidence, max(p_incident, 1-p_incident))
             # 둘 중 하나만 있으면 절반; 모두 없으면 0
human_review_required = p_human_review 미확인 또는 >=.5
                        OR 필수 질문 누락/refusal
                        OR adapter confidence <.4

Frozen NORMAL = p_incident <= .01
                AND human_review_required == false
                AND refused_questions가 비어 있음
                AND category == no_clear_incident
                AND adapter confidence >= .90
그 외 = P4로 전달; 직접 DANGER는 비활성
```

**[확인] Suppress에 쓰이는 Incident Score는 priority_score가 아닌 p_incident다.** priority와 네 risk axis는 Frozen Suppress식에 직접 들어가지 않는다. confidence는 CV reliability와 별개이고, 운영 위험에 보정된 확률이 아니다. p_incident가 낮을수록 `max(p,1-p)`는 높아지므로 confidence≥.90은 독립적인 안전 보증도 아니다. [adapter 설정](</D:/projects/477/experiments/p1_decisions/configs/decisions_questions_v1.json:122>)

`calibrate`는 가드/Prompt/확률을 학습·보정하지 않는다. 이미 계산된 p_incident의 T_normal 후보 0/.01/.025/.05에서 관측 Danger suppression=0을 만족하면서 정상 제거가 가장 많고 T가 가장 낮은 정책을 선택한다. T_danger는1.0으로 기록되지만 direct branch가 꺼져 있어 실제 라우팅에 쓰이지 않는다. **Calibration이라는 이름은 현재 Threshold 선택을 뜻하며, reliability curve/Platt/isotonic 등의 Score Calibration은 구현되지 않았다.** [정책 잠금](</D:/projects/477/experiments/triage_frozen_v1/routing_policy_lock.json>)

`no_clear_incident`는 “현재 CV가 확실한 사건을 보여주지 않음”이라는 해석에 가까우며 “제거해도 안전함”과 동치가 아니다. 현재 `human_review`는 위험과 불확실성 모두에 대해 관제사 검토를 질문하므로 P4 검토가 필요한 상황과 즉시 Human이 필요한 상황을 구분하지 못한다.

### 1.4 Safety Rules의 실제 위치

과거 `cascade_analysis_v1`에는 F_boundary/F_multicam/F_interaction_lowconf/F_disagree/F_lowconf/F_refusal을 사용하는 사후 Hybrid 정책이 있다. 예컨대 boundary semantics가 없고 entry/large movement가 있으면 NORMAL을 막는다. 하지만 이는 7-item reasoning 자료를 이미 본 상태의 in-sample 분석이며 Frozen triage의 실행 정책이 아니다. [flags_for](</D:/projects/477/experiments/cascade_analysis_v1/scripts/build_triage_table.py:14>), [route](</D:/projects/477/experiments/cascade_analysis_v1/scripts/sweep_stage1_thresholds.py:16>), [분석 설정/한계](</D:/projects/477/experiments/cascade_analysis_v1/configs/cascade_analysis_v1.json>)

따라서 **“Boundary Safety Rule이 Frozen Test Normal 전부를 P4로 보냈다”는 설명은 코드와 일치하지 않는다.** Frozen에는 category/review/confidence/refusal 가드가 적용된다. category와 review는 P1 답변에서 나오며 명시적인 CV Rule Override가 아니다.

### 1.5 오류와 Structured Output

P1: SDK typed answers → adapter → 기존 prediction Schema 검사. 질문 누락/refusal은 unknown 및 review=true로 처리하고 refused risk에는 Schema 수치 요구 때문에0.5를 넣는다. 이0.5는 추정 위험도가 아니다. 네 score confidence는 저장되지만 aggregate confidence 계산에 사용하지 않는다. `index_answers`는 name별 dictionary로 만들기 때문에 중복 name을 명시적으로 거부하지 않는다. answer name/type/개수/유한 수치 검증을 Router에서 보강할 여지가 있다.

P1 client는 connect10초/read120초, network·429·5xx에 최대2회 재시도; 4xx는 재시도하지 않는다. 완료 실패는 `FAILED`, worker는 batch를 중단한다. client에서 다루지 않는 serialization/adapter 예외도 큐로 전환하는 상위 운영 wrapper가 확인되지 않았다. 37건 결과에 실제 refusal/retry는0건이며, 실제 failure 상황의 Human 전송은 검증되지 않았다.

P4는 strict JSON Schema와 실제 제공된 frame_ref 검증을 수행한다. refusal/incomplete/schema/transport 실패는 결과를 만들어내지 않고 실패한다. `surface_p4`의 refusal 처리는 decision record가 존재하는 경우이며, transport failure나 top-level refusal로 result가 없는 경우까지 자동 Human 큐에 넣는 운영 코드가 아니다. [P4 실패 정책](</D:/projects/477/experiments/p4_gpt61_sol_vision/configs/p4_v1.json>)

정상 처리 실패를 NORMAL로 만드는 경로는 이번에 확인되지 않았다. 다만 “실패했으므로 후보가 관제사에게 실제 전달됐다”는 보장은 아직 없다. v2는 P1 실패→P4, P4 실패/대기 deadline 초과→Human의 명시적 실행 경로와 누락 방지 저장/큐 재시도가 필요하다.

### 1.6 비용·Latency 계측

초기 reasoning 7-item 비용은 평균 `$0.00047373/item`이다. 이 자료의 API latency1.146초는 **중앙값**이며 반올림 표 기준 평균은 약1.063초다. 사용자가 제시한1.15초를 전체 CCTV E2E 평균으로 쓰면 안 된다. 원본 P1의 `latency_ms`는 null이며 cached-state serializer+API+adapter 시간이 별도로 기록된다. [초기 측정](</D:/projects/477/experiments/p1_decisions/experiment_report.md:174>)

새 triage harness는 원본 `.run()` 대신 prepare/decide/adapt를 직접 호출하여 usage/api_timing/full_harness_ms를 저장한다. 원본 runtime_config 비용·Latency breakdown과 envelope가 다르다. full_harness는 준비→예측 검사까지이고 CV는 별도 작업이므로 P1 full_harness에도 CV가 포함되지 않는다. [worker:105](</D:/projects/477/experiments/triage_frozen_v1/scripts/worker.py:105>)

| 기존 저장 결과 집계 | Calibration15 | Test22 |
|---|---:|---:|
| P1 평균 input tokens | 3,380.07 | 3,056.64 |
| P1 평균 API 비용 | $0.00033801 | $0.00030566 |
| P1 평균 API 마지막 시도 | 0.570초 | 0.504초 |
| P1 평균 API retries 포함 | 0.580초 | 0.508초 |
| P1 평균 full harness | 1.337초 | 1.267초 |
| CV 단계별 시간 합 평균 | 28.412초 | 17.040초 |
| P4 평균 API 마지막 시도 | 93.307초 | 59.796초 |
| P4 평균 full harness | 153.742초 | 94.423초 |
| P4 평균 provider usage 기반 비용 | $0.487186 | $0.458287 |

Test P1 full_harness p95=3.019초, API retries 포함 p95=.680초; P4 full_harness p95=190.674초. p95는22개에 대한 nearest-rank 기술통계다. CV 값은 decode/inference/tracking/features 등의 합이며 arrival→출력 wall-clock SLA가 아니다. 순차 가정에서 Test CV+P1은 약18.306초지만 streaming overlap·warmup·큐 지연·관측 window 누적 시간까지 측정한 실시간 수치는 아니다. P4 full_harness에는 영상 준비 비용도 크다. 즉시 Human 분기는 의미가 크지만 현재 측정으로 라이브 즉시성을 입증할 수는 없다.

P1 비용은 input tokens×$0.10/1M, output/cache 요금은 Decisions 규칙상 별도 청구하지 않는다. P4는 frozen standard rate input$2/cache-read$.1/cache-write$2.5/output$10 per1M, >272k input이면 multiplier 적용한다. [P1 cost 함수](</D:/projects/477/experiments/p1_decisions/src/cost.py>), [P4 cost 함수](</D:/projects/477/experiments/p4_gpt61_sol_vision/src/cost.py>)

이번37개 P4 usage에는 cached_tokens=0, cache_write_tokens=input_tokens가 기록돼 있다. 따라서 모든 input을$2로 계산하면 과소 산정된다. Test 평균은178,863.55 input,1,112.95 output이고 이 입력이 모두 cache-write여서 `$0.458287`이다. 모두272k 미만이다. 이는 provider usage×공식/고정 가격의 계산값이며 invoice 실청구 확인값은 아니다. 실패·retry 과금과 로컬 GPU/서버 비용도 포함하지 않는다. 공식 가격 확인: [Decisions](https://developers.openai.com/api/docs/guides/decisions), [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

## 2) Bottleneck Analysis

### 2.1 고정 정책 진단

다음 집계는 T_normal=.01 및 기존 모든 가드를 그대로 적용한 진단이다. 각 실패 가드 수는 **중복 집계**라 합이 전체 후보 수와 같을 필요가 없다. 세부 수치는 [audit_metrics.json](</D:/projects/477/planning/stage1_router_v2_research/audit_metrics.json>)의 `splits.*.groups`에 있다.

| Split/유형 | n | p_incident 최소/중앙/최대 | score 실패 | review 실패 | category 실패 | conf 실패 | refusal 실패 | Stage1 Suppress |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Calibration Clear | 7 | .00/.07/.66 | 5 | 3 | 5 | 5 | 0 | 2 |
| Calibration Hard Negative | 5 | .16/.45/.71 | 5 | 5 | 5 | 5 | 0 | 0 |
| Calibration Danger | 3 | .20/.63/.68 | 3 | 3 | 3 | 3 | 0 | 0 |
| Test Clear | 6 | .05/.085/.66 | 6 | 2 | 4 | 5 | 0 | 0 |
| Test Hard Negative | 6 | .14/.21/.23 | 6 | 5 | 6 | 6 | 0 | 0 |
| Test Danger | 10 | .17/.635/.74 | 10 | 10 | 10 | 10 | 0 | 0 |

**[확인] Test에서 score 조건만 통과하고 나머지 가드 때문에 막힌 후보는0건이다.** 즉 Test Suppression0의 충분한 직접 원인은 score cutoff다. 가드도 다수 정상에서 실패하므로 cutoff를 바꾸면 해결된다는 의미는 아니다. Test에서 대체 cutoff를 계산하거나 고르지 않았다.

Calibration에서 Suppress된 TRIAGE_017/023은 사람 검출0·tracks0·CV reliability=null/unknown이었다. 영상 brightness/sharpness는 Canonical에 존재하지만 Compact에는 dark fraction 외 해당 수치가 전달되지 않는다. 정상 label인 두 사례의 성공은 관측된 사실이며, **무검출=실제 사람 부재를 검증한 것**은 아니다. Test에는 무검출 후보가0건이다. [Calibration 결과/근거](</D:/projects/477/experiments/triage_frozen_v1/analysis/calibration_gt.json>), [원본 CV 예](</D:/projects/477/experiments/triage_frozen_v1/cv_states/TRIAGE_017.json>)

기존 Calibration 후보 결과는 T=.01/.025/.05 모두 정상2건 제거, Danger0건 제거, P4 13/15이다. 추가 Threshold 실험 없이 기존 파일만 확인한 결과다. [calibration_candidates](</D:/projects/477/experiments/triage_frozen_v1/analysis/calibration_candidates.json>)

### 2.2 요청된 여덟 원인 구분

| 원인 후보 | 확인된 사실 | 판단/한계 |
|---|---|---|
| 1. Normal/Danger score 비분리 | Calibration HN .16–.71과 Danger .20–.68이 겹친다. Clear에도 .66이 있다 | **확인된 현상.** 단일 전역 점수만으로 안전 제거를 최적화하기 어렵다. 어느 Feature/질문이 원인인지는 ablation 필요 |
| 2. T_normal=.01 보수적 | Test 모든 score>.01, Calibration grid 완화에도 제거2건 유지 | **직접 차단 원인.** 안전성을 근거 없이 완화할 수 없고 현재 범위에서는 완화 효과도 미확인 |
| 3. Scene semantics 누락 | boundary_semantics=false, crossing=null, authorization_known=false 고정; ROI/문·gate 미구현 | **구조적 결손 확인.** Calibration Clear3/7이 scene-entry category. 경계 통과 Danger의 의미를 복원하지 못하는 사례도 있음 |
| 4. Safety Rule 과잉 Escalation | Frozen에서 P0 RuleEngine 미실행; 과거 F_boundary 정책은 별도 in-sample 분석 | **그 Rule을 0건의 원인으로 지목할 수 없음.** 현재 review/category/confidence 가드는 실제 차단하지만 독립 원인 효과는 미측정 |
| 5. Score Calibration 불일치 | 확률 보정 없음; review/category/incident 답이 일부 불일치; confidence는 산술식 | **미보정 상태 확인.** 실제 위험확률과의 miscalibration 크기는 현재 n으로 추정 불가 |
| 6. Prompt 목적 불일치 | “operator should surface”, “most safety-relevant”, “risk or uncertainty”; safe_to_suppress 질문 없음 | **목적 차이 확인.** 일상 entry·근접·crouch를 과도하게 의미화할 수 있다는 가설은 Dev에서 검증 |
| 7. Clear/HN 차이 | Calibration 제거 Clear2/7, HN0/5; Test 양쪽0; HN은 주로 conflict/down category | **확인.** 사람이 있는 Clear와 HN을 나눠 평가해야 한다. HN을 한 종류의 normal로 다루면 병목이 가려짐 |
| 8. 신뢰도/누락 처리 | null unknown 지침 있음; Canonical confidence/좌표 등 Compact 누락; 코드에 null을 낙관값으로 취급하는 경로 존재 | **코드 위험 확인.** 이것이 실제 0건을 유발한 양은 미확인; 안전 강화는 Suppress를 더 줄일 수도 있음 |

정상·위험의 의미 혼동을 보여주는 **Calibration** 예시:

- TRIAGE_015: Human Clear Normal, p=.06, entry category, p_review=.51. 일반 이동/entry와 의미 있는 경계 통과를 구분할 Camera Context가 없다.
- TRIAGE_001: Human HN, p=.16, conflict category, p_review=.71; 근접·장난을 구분할 의미가 약하다. Canonical CV quality는.8265이므로 단순히 CV reliability가 낮아서만 생긴 현상이 아니다.
- TRIAGE_007: Human 경계 통과 Danger인데 P1 category는 person-down, p=.63. 내려가는 자세와 담장 통과 의미가 혼동된다.
- TRIAGE_036: Human 경계 통과 Danger, p=.20으로 낮으나 review=true가 보호한다. p_incident 단독으로 NORMAL 판단을 확대하면 보호 근거를 잃을 수 있다.

이 예시는 모델 능력의 일반적 결론이나 새 Prompt의 few-shot 예제로 사용하기 위한 것이 아니다. 재사용하려면 새 Dev 역할을 명시해야 하며 Frozen Test 사례는 Prompt에 넣지 않는다.

### 2.3 압축·품질 처리의 구체적 한계

**[확인] 이미 풍부한 Cheap CV 결과가 존재한다.** person count, pose transition, pair distance, motion, persistence, tracking/quality를 새 모델로 다시 얻을 필요가 없다. 하지만 Compact는 원본 정보 일부를 잃는다.

1. 자세는 initial/final/distribution/strongest downward transition으로 압축된다. 낮아진 뒤 회복한 시점·마지막 관측과 clip 끝의 거리·후반 위험 여부를 명확하게 표현하지 못한다. `final_posture`는 **마지막 known posture**라 후반 unknown이 있어도 standing일 수 있다. 회복이 있었다는 이유만으로 이전 위험을 제거해서는 안 된다.
2. track `visible_fraction`의 분모는 첫~마지막 관측 span이다. clip 전체에서의 coverage가 아니다. 짧게 등장한 두 sample track도1.0일 수 있다. 원본 `visible_fraction_of_clip`·max_gap·mean detection confidence는 Compact에 빠진다.
3. `_longest_low_run`은 known observation timeline만 순회하며 시간 gap으로 run을 끊지 않는다. 미검출 gap 사이의 낮은 자세를 지속으로 볼 수 있다. `_vertical_transition`은 최대4초 내 standing→low 관측쌍을 비교하지만 연속 관측 검증 자체는 아니다. [compact low run](</D:/projects/477/experiments/p1_decisions/src/compact_serializer.py:148>), [transition](</D:/projects/477/experiments/p0_cv_only/src/feature_extractor.py:326>)
4. 최대6 track 초과 후보는37개에서0건이므로 **6-track cap은 현재 0건의 설명이 아니다.** 다만 1관측 track은 Calibration8/Test10개가 선택 대상에서 빠지고, 원본 pair>4인 clip은 Calibration5/Test1개다. 실제 유효 pair 누락 여부·중요도는 Dev에서 원본/Compact 대응으로 확인해야 한다. absence 판단은 생략된 대상에 대한 coverage summary 없이 하면 위험하다.
5. `_quality`는 `(dropout or 0)`으로 dropout=null을 aggregate reliability에서 손실0으로 취급한다. Test에는 dropout unknown인 clip이1개 있다. 알려진 dropout=0과 unavailable은 구분해야 한다. `prediction_adapter.uncertainties`의 `(pose_visibility or 1)`은0/null을 높은 가시성처럼 경고 생략에 쓰지만 **이 설명 함수가 review를 계산하는 것은 아니다.** 따라서 바로 Suppress0의 원인으로 연결하지 않는다. [quality:640](</D:/projects/477/experiments/p0_cv_only/src/feature_extractor.py:640>), [uncertainties:65](</D:/projects/477/experiments/p1_decisions/src/prediction_adapter.py:65>)

### 2.4 최종 지표를 Stage 1 성능과 분리

| 고정 지표 | Calibration | Test |
|---|---:|---:|
| Stage1 Safe Normal Suppression | 2/12=16.7% | 0/12=0% |
| Stage1 Danger False Suppression | 0/3 | 0/10 |
| Stage1 제거/전체 | 2/15=13.3% | 0/22=0% |
| 정책상 P4 Escalation | 13/15=86.7% | 22/22=100% |
| 최종 Danger Surface Recall | 3/3 | 10/10 |
| 최종 Normal Suppression | 9/12=75% | 10/12=83.3% |
| 최종 Operator Queue Reduction | 1−6/15=60% | 1−12/22=45.5% |

Test 최종 Normal 제거는 Clear5/6와 HN5/6으로 **모두 P4에서** 일어났다. P4가 Human에게 남긴 Normal은 각1건이다. Calibration의 P4 surface는 Clear0/7, HN3/5다. P4는 정확한 oracle이 아니며 Normal의 위험/uncertainty surface를 False Alarm과 운영 정책상 필요 검토로 분리 검수할 필요가 있다.

## 3) Improvement Opportunities

### 3.1 Compact CV State Feature 검토

Runtime은 **추가 비용**의 정성 추정이다. L=기존 결과에 선형 집계/몇 개 필드 추가, M=pair 연산·polygon 교차·추가 수동 context 관리. 현재 벤치마크에서 추가 ms를 측정하지 않았으므로 고정 수치를 약속하지 않는다. 모든 추가 필드는 내부 `compact-v2`로 version/hash 관리하고 외부 Output Contract는 유지한다.

| Feature | 현재 구현 | 기존 자료 계산/추가 모델 | Runtime/난이도 | 기대 이익 [가설] | False Suppression Risk/보호 |
|---|---|---|---|---|---|
| Person Count | 원본·Compact min/max/median, 존재비율 | 즉시 가능, 모델 불필요; camera-time count curve도 생성 가능 | L/낮음 | 단독 보행·안정적 인원과 갑작스런 dropout 구분 | count0은 미검출일 수 있음; coverage/quality 확인 없이 safe 금지 |
| Bounding Box/Spatial Relation | 원본 bbox/path, Compact pair distance·overlap; 실제 위치/path는 제외 | Canonical frame bbox/center_path 재사용 | L~M/중간 | ROI 안 일반 이동, 경계 접근, 경로 교차·동행 구분 | 2D perspective·occlusion; 위치는 물리 거리/접촉 확증 아님 |
| Posture Transition | downward strongest, distribution, initial/final | 원본 timeline에서 짧은 phase·회복 시점·후반 unknown 산출; 모델 불필요 | L/중간 | 지속 person-down과 brief crouch의 차이 설명 | 회복해도 위험이 사라진다고 단정 금지; 이전 위험과 onset 별도 유지 |
| Motion/Speed/Direction | mean/max speed, net displacement, direction count | 원본 path에서 displacement vector·coarse phases·signed ROI approach 추가 | L/낮음~중간 | 일반 보행, 동행, 반복 approach, 불규칙 motion 비교 | bbox jitter·track switch; low speed=안전 아님 |
| Close Contact/Interaction | pair close duration/relative motion/contact·arm·limb proxy | 기존 distance_series/경로로 parallel co-motion·gap-aware phases, ratio support 추가 | M/중간 | 단순 근접/동행과 접근·충돌 proxy 분리 | 손 접촉·위협/장난 의미는 CV만으로 확정 불가; 애매하면 P4 |
| Temporal Persistence | longest low/low motion/close duration; P1 persistence score | observed_duration/gap/continuous evidence·post-peak 회복 집계 | L/중간 | 순간 오검출에 의한 escalation 감소 가능 | 샘플 사이 미관측을 연속 관측으로 채우면 위험; gap을 unknown 처리 |
| Multi-camera Relation | 원본 normalized phase; Compact similarity limited, sync/id=false | 현 데이터는 비교 proxy만 가능; 실제 sync/topology metadata 필요 | M/높음 | 추후 coverage 보완·같은 사건 중복 큐 개선 | 정상 시점이 다른 위험 시점 지울 수 있음; 현재 joint safe 판단에 쓰지 않음 |
| Camera ROI | 미구현 | bbox/path+새 수동 camera polygon, 모델 불필요 | L~M/중간 | 일상 walkway와 관심 경계 구분 | ROI 밖 위험 배제 금지; camera 이동/해상도/context 변경 감지 |
| Restricted Area | semantics unavailable | 사전 수동 area/policy 등록 필요; 현재 clip만으로 권한 복원 불가 | L/중간 | 경계 접근 여부를 구체화 | 미확인 권한을 authorized로 추론 금지; 위험 경계 교차는 사람 검토 |
| Door/Gate/Boundary Crossing | generic entry/exit만 있고 crossing=null | 수동 segment/polygon과 footpoint/path 교차로 가능; 문 자체 객체 검출은 선택 사항 | L~M/중간 | frame entry와 실제 boundary crossing 구분 | 방향/가림/추적 gap에서 crossing 불확실; gate 통과 자체를 무조건 위법/안전으로 분류하지 않음 |
| CV Detection Confidence | 원본 frame/track/camera confidence; Compact 미포함 | mean/low quantile/low-conf 비율 재사용 | L/낮음 | 양호한 관측과 detector dropout 위험 분리 | 모델 confidence는 Recall 보증 아님; 높은 detector conf도 semantic safe 아님 |
| Tracking Reliability | Compact rel/visible_fraction/ambiguous/fragmentation 있음 | max_gap/association_conf/clip coverage/recent support 추가 가능 | L/낮음 | 짧은 track의 과대 신뢰·마지막 관측 후 gap 구분 | association score 미보정; 안전 predicate의 충분조건으로 단독 사용 금지 |
| Missing/Low-quality Observation | null, dark/small/pose/occlusion/dropout 일부 | Canonical brightness/contrast/sharpness·frame count·unknown fractions·staleness 추가 가능 | L/낮음 | 실패와 true absence 구분, confidence 낙관 경로 방지 | 품질 강화는 Suppress를 줄일 수 있음; 안전성 기여와 비용 목표를 따로 평가 |
| Serialization Coverage | included/total tracks만 부분 구현 | omitted track/pair count, supporting frames, omitted-risk summary 산출 | L/중간 | 압축으로 신호가 빠진 후보에서 강제 abstain | 생략된 track이 risk-free라고 추론 금지; raw all-track hazard scan 병행 |

**우선순위:** 새 모델 없이 관측 quality/coverage와 짧은 시간 흐름을 보존하고, 필요한 camera만 수동 context를 붙인다. Multicam identity/ReID·추가 action model·door detector는 첫 개선 범위에서 제외한다. 현재37개는 단일 카메라이므로 Multicam 개선 효과를 이 자료로 주장할 수 없다.

### 3.2 Decisions API 지원과 현재 구현의 차이

공식 문서에서 확인한 Decisions 기능은 predicate/choice/score, 같은 입력의 여러 질문, choice/score probability distribution·confidence, 질문별 refusal이다. 현재 P1은 이 세 타입을 사용하지만 Safe-to-Suppress 질문은 없다. predicate는 probability를 주며 독립 confidence는 제공하지 않는다. score는 level index의 probability-weighted mean이므로 운영 위험확률과 다르다. [Decisions guide](https://developers.openai.com/api/docs/guides/decisions)

API에서 직접 `choice`의 허용값을 NORMAL/SUSPICIOUS/DANGER로 정의하는 것은 가능하다. 또는 `safe_to_suppress` predicate와 관측 충분성·위험 유형 질문을 함께 요청할 수 있다. 그러나 모델이 **임의 Output Contract JSON·자유 reason text**를 Decisions에서 생성한다고 가정하지 않는다. 최종 JSON 및 reason_codes는 로컬 policy/adapter가 만든다. 두 질문을 같은 request에 넣는 경우 서로의 답을 참조하는 순차 추론을 요구하지 않고 각각 동일 evidence에 대해 평가한다. [API reference](https://developers.openai.com/api/reference/resources/decisions/methods/create)

공식 가이드 기준 지원 모델은 gpt-6-luna이고 현재 P1도 그 모델이다. 모델 교체·fine-tuning·임의 response_format/json_schema·tools·temperature/seed 조절·무료 추가 질문·confidence의 자동 운영 보정은 이번 개선의 전제로 삼지 않는다. beta 및 실제 account 접근 권한은 기존 성공 기록 이상의 새 실행 검증을 하지 않았다.

권장 질문 방향은 “위험 사건이 있는가?”와 “관측이 충분하고 알려진 위험 신호가 남지 않아 제거해도 되는가?”를 분리하는 것이다. suppression predicate는 **강한 정상 관측 근거와 관련 위험의 배제 가능성**을 묻는다. 단순히 p_incident를1−p로 뒤집지 않는다. general operator review 대신 “P4로 확인해야 할 unresolved evidence”와 “즉시 Human을 요구하는 위험”의 목적도 분리한다.

질문/설명/field 수가 늘면 input tokens와 처리시간이 늘 수 있다. 예를 들어 실제 usage가400 input tokens 증가하면 P1 비용은 약$0.00004/호출 늘어난다. Prompt 축약으로 줄일 수 있지만 검증 전 가드를 삭제해서 비용을 줄이지 않는다. **질문 수 변화와 Latency의 비례 관계는 미확인**이며 동일 Dev 입력에서 기록해야 한다.

### 3.3 우선 개선 후보

| 순서/개선 대상 | 현재 문제·개선 방법 | 기대 효과/근거 | 위험 | 필요한 데이터 | 난이도/비용 영향 | 검증 |
|---|---|---|---|---|---|---|
| P0: 측정/실패 wrapper | 현 실험 Router와 운영 라우팅 분리; branch·실제 call·fallback·latency trace 기록, invalid result는 suppress 금지 | 오류 후보 누락 방지·원인별 비용 파악; 구현 부재 확인 | 추가 저장/queue 중복 | 합성 timeout/refusal/schema failure + 실제 trace | 낮음~중간; API 추가 없음, 로컬 저장 증가 | 모든 invalid route에서 SUPPRESS0; P4 실패 Human delivery·idempotency 검증 |
| P1: 최소 State 보존 | clip coverage/recent gaps/det conf/quality·짧은 posture phases·omitted summaries 보강 | 기존 CV에 정보 존재, 재추론 비용 없음 | 압축 증가, 일부 safety gate로 escalation 증가 | 별도 Dev의 원본 CV↔Compact와 사람 관측 tag | 낮음~중간; CPU·tokens 소폭 증가 예상 | field별 ablation, gap/빈 화면/dropout stress; 안전 개선과 Suppress 효과 분리 |
| P1: Safe Suppress 질문/정책 | 동일 P1에서 safe predicate와 유형별 evidence/uncertainty; category 정의에서 generic entry≠위험을 명확화 | 현재7질문에 safe 목적 없음; Clear entry 및 HN 혼동 확인 | wording으로 자신감만 올리고 관측 한계 숨길 위험 | 새 Dev Clear/HN/Danger/ambiguous, 특히 의미가 다른 유사 CV pair | 낮음; request1개 유지, tokens 변화 측정 | state 고정 Prompt ablation, calibration curve·Danger FS·subgroup 평가 |
| P2: Camera Context | ROI/ordinary paths/boundary/direction/context version을 수동 등록, geometry summary 추가 | 현재 경계 semantics 부재, entry Clear 및 boundary Danger 혼동 | context stale/잘못된 ROI·권한 추정 | 새 카메라별 수동 geometry, context 감수; unlabeled와 labeled 분리 | 중간; annotation 비용, 런타임 geometry 저렴 | held-out cameras, context off/on, 이동/역방향/occlusion stress |
| P2: Hybrid safety checks | raw CV all tracks에 위험 veto/관측 부족 checks, 신뢰 가능한 위험은 P1 우회 Human | cap/short track·실패 신호를 P1 낙관 판단으로 덮지 않음 | 근접·low posture만으로 danger면 Human 과증가 | 검증된 위험 subtype + HN paired examples | 중간; P1/P4 호출 일부 감소 가능, 미측정 | rule precision/recall·Human normal rate·time-to-human·safe suppression 공동평가 |
| P3: Calibration | 새로운 Calibration에서 routing score threshold·category별 abstention 선택, 필요시 간단 calibration | 현재 p가 미보정·nD3 | overfit, 여러 policy 검색의 선택 편향 | 독립 calibration 위험 유형/scene 충분수 | 중간; 로컬 학습 저렴, 추가 labeled data 비용 | group holdout, reliability/Brier·risk-coverage, 독립 Test1회 |

새 Combined Router는 초기에는 얇은 deterministic policy로 유지한다. score+CV feature를 학습한 supervised router는 별도 후보로만 두며, n=37로 복잡한 classifier를 학습하거나 실측 이익 없이 도입하지 않는다.

### 3.4 Hybrid 순서 비교

아래 효과는 조건부 설계 비교이며 측정된 성능 순위가 아니다. 모든 구조에서 Rule 단독 NORMAL을 허용하지 않는다.

| 구조 | Danger Miss Risk | Safe Normal/P4 절감 가능성 | Stage1 API 비용/Latency | 복잡도/Explainability |
|---|---|---|---|---|
| Rules→P1→Final Policy | 알려진 위험 먼저 보호; 최종 재검사 필요 | 정상 설명은 P1 담당; rule 과잉은 절감 제한 | 전부 P1이면 비용 동일; 위험 Human은 즉시 발행 가능 | 중간; 단계 원인 명확 |
| P1→Safety Override | P1 낙관 답을 veto 가능; P1 지연 뒤에 위험 발견 | 가장 적은 기존 변경; 안전 veto가 많으면 P4 유지 | 모두 P1, 위험도 P1 대기 | 낮음~중간; 최종 override 로그 용이 |
| Rules 선별+P1 선택 호출 | 신뢰된 위험 Human, 처리 불가 P4 우회; 누락/오분기 점검 중요 | 명확한 처리 불가 후보의 P1 비용 절약; **그 자체는 P4 rate를 낮추지 않음** | skip된 부분 비용/지연 감소 | 중간; rule branch별 recall·queue 측정 필요 |
| P1 score+CV Combined | risk constraint 없이 점수 합치면 unsafe; hard veto 필요 | 관측 충분성이 있는 정상에서 절감 가능 | P1 호출량 동일, feature 계산 소폭 | deterministic이면 중간; learned면 높고 데이터 요구 큼 |

**추천은 “Rules 선별 + P1 Safe Suppression + Final hard veto”의 한 가지 구조다.** 기존 P1 client/typed response/P4 경로를 유지하면서, 높은 우선순위 위험과 명백한 처리 불가를 먼저 분리하고, 정상은 P1과 evidence gates가 함께 결정한다.

## 4) Recommended Stage 1 Router v2

### 4.1 내부 설계

```text
Canonical CV State + versioned Camera Context
  ↓
관측 validity/coverage 및 all-track deterministic hazard 검사
  ├─ 검증된 강한 위험 신호 → DANGER/HUMAN_IMMEDIATE (P1/P4 대기 없음)
  ├─ 입력 불량/관련 evidence 부족 → SUSPICIOUS/ESCALATE_P4 (P1 생략 가능)
  └─ 그 외 → Compact-v2 → 기존 P1 Decisions API 1회
                   ↓
           답변 validity + Safe-to-Suppress + 위험/uncertainty 판단
                   ↓
           Final policy: hazard veto > uncertainty > safe suppression
              ├─ 검증된 immediate-danger → DANGER/HUMAN_IMMEDIATE
              ├─ 모든 suppression 조건 충족 → NORMAL/SUPPRESS
              └─ 그 외/오류/refusal → SUSPICIOUS/ESCALATE_P4

P4 incident/관련 unresolved uncertainty/Error/Refusal/대기 deadline 초과 → Human Queue
P4의 검증된 NORMAL → 최종 Suppress
```

현재 관측 proxy만으로 “강한 위험”을 확정할 수 있다고 주장하지 않는다. 예시 후보는 **신뢰되는 standing→horizontal 변화 + 관측이 유지된 장시간 low/low-motion**, 또는 **검수된 물리적 boundary 교차 + 정해진 관제 정책**이다. 지속시간·confidence cutoff는 여기서 정하지 않고 새 Dev/Calibration에만 맞춘다. 단순 근접, running, crouch, contact proxy 하나는 immediate danger 충분조건으로 쓰지 않는다. 의료 진단·범죄·권한 추정을 하지 않는다. Rule에는 `requires_review` 의미를 부여하고 사람이 최종 확인한다.

배포 전 검증을 통과하지 않은 rule/모델 immediate-danger branch는 shadow 로그만 낸다. 관측 부재나 기존 review=true를 무시해 NORMAL을 늘리는 정책은 채택하지 않는다. 위험이 해소되지 않은 후보는 P4로 보내고, 실제 P4 서비스도 unavailable이면 Human으로 넘긴다. Stage1의 처리 deadline/후단 대기 deadline은 관제 SLA로 정해야 하며 기존120/900초 client timeout을 곧바로 운영 SLA로 쓰지 않는다.

### 4.2 P1의 최소 변경 경로

1. 기존 gpt-6-luna/Decisions client·usage logging·P4 GPT-6.1 Sol Direct Vision 유지.
2. 내부 입력에 coverage/quality/짧은 phase만 추가한 `compact-v2` 후보를 만든다. Context는 따로 ablation.
3. Dev 실험에서 기존7문항에 `safe_to_suppress` predicate 한 개를 **shadow 추가**하여 task alignment 이득부터 측정한다. 질문은 관측 충분성, 정상 관측 근거, 중요한 미해결 위험을 포함한다. Predicate의 수치를 직접 operational safety probability로 간주하지 않는다.
4. 다음 Dev arm에서 category와 review 질문을 Safe Router 목적에 맞게 분리/정의한다. 기존 `category == no_clear_incident` 가드를 그대로 유지한 채 safe 질문만 더하면 가드 실패 후보는 계속 막힌다. 따라서 shadow arm과 실제 policy arm을 구분하고, 어떤 수정으로 개선됐는지 기록한다.
5. category별 concern 및 unresolved evidence는 predicate/choice typed answers 또는 deterministic feature gate로 구현한다. 즉시 Human 위험과 P4로 해소할 불확실성을 구분한다. confidence가 높아도 관련 관측 부족이나 hard veto가 있으면 Suppress 금지.
6. 최종 suppression은 `valid answers ∧ sufficient relevant observation ∧ no unresolved hazard ∧ safe_score passes calibrated threshold ∧ policy applicability`의 교집합으로 한다. `p_incident`는 유지하여 보조 veto/비교에 사용하되, 새 Dev에서 확인 없이 기존 score gate를 완화하지 않는다.

독립 질문 모두의 확률을 단순 곱해 joint safety confidence로 만들지 않는다. 답변 상관과 detector miss를 반영하지 못하기 때문이다. category score가 낮다고 불확실성 자체가 해소됐다고 보지 않는다. API choice를 Router 결과로 직접 사용해도 마지막 local override를 거친다.

정상 허용 범위는 context/quality가 검증된 일상 이동·안정적 관측 등 새 데이터가 뒷받침하는 범위부터 시작한다. HN·미확인 boundary·multicam·unsupported camera는 evidence가 부족하면 계속 P4다. “카메라에 ROI가 없다”는 이유만으로 모든 후보를 escalate하거나, 반대로 gate가 등록되지 않았다고 boundary 위험을 부정하지 않는다. 관련 위험 배제가 필요한 후보인지와 context 적용 범위를 명시적으로 검사한다.

### 4.3 Output Contract v1 유지 및 기존 Schema 정합성

제시된7필드와3조합을 유지하고 reason_codes는 deterministic local mapping으로 생성한다. 아래는 설계 예시이며 실제 예측/성능 결과가 아니다.

```json
{
  "schema_version": "1.0",
  "candidate_id": "cand_001",
  "camera_id": "cam_07",
  "decision": "SUSPICIOUS",
  "action": "ESCALATE_P4",
  "reason_codes": ["CLOSE_CONTACT", "UNCERTAIN_INTERACTION"],
  "router_version": "stage1-v2"
}
```

NORMAL→SUPPRESS, SUSPICIOUS→ESCALATE_P4, DANGER→HUMAN_IMMEDIATE만 출력한다. 내부 score/features/answer status/policy hashes/fallback trace/질문과 context version은 candidate_id로 연결한 audit record에 저장한다. 출력 필드 추가가 필요하지 않다. `router_version`은 재현 가능한 policy manifest와 연결하고 동일 값 아래 다른 thresholds/prompts를 배포하지 않는다.

**[확인] 조사한 두 workspace에서 CandidateEvent/VLMAssessment/Incident라는 실제 타입/Schema 정의는 발견되지 않았다.** 따라서 해당 백엔드 타입과 정합성이 검증됐다고 말할 수 없다. 현재 확인 가능한 Schema는 다음과 다르다.

| 현재 Schema/계약 | Router envelope와 차이 | 하위 호환 방법 |
|---|---|---|
| `benchmark_v1/schemas/prediction.schema.json` | event_type/is_incident/risk/confidence/observations/review, additionalProperties=false; camera CAM_01~03 enum | Router object를 prediction 안에 끼우지 않고 별도 message/record로 생성; 기존 assessment 보존 |
| `benchmark_v1/schemas/result.schema.json` | reasoning 실험 model/run/item ID·pipeline enum 제한 | 새 Router의 live candidate_id를 별도로 유지; legacy benchmark exporter로 변환, schema를 수정하지 않음 |
| Frozen triage result | TRIAGE ID를 지원하려고 새 envelope 사용, Router decision/action 아님 | raw decision 및 route 결과를 별도 저장; benchmark 결과 덮어쓰기 금지 |
| Team Benchmark VLM contract | source_id SRC01~06, canonical event_type, risk_axes/evidence_refs/needs_human_review | stage output exporter로만 매핑. **event_type normal ≠ router SUPPRESS**, `is_incident=false`도 NORMAL로 자동 변환 금지 |
| Team Clef contract | invoke_vlm Boolean, 현재 모든6영상 호출 필요 | 3-action Router 정보를 Boolean만으로 보존 불가. 비교용 export와 실제 운영 메시지 분리 |

근거: [prediction schema](</D:/projects/477/benchmark_v1/schemas/prediction.schema.json:16>), [팀 제출 계약](</D:/projects/477_team_benchmark_v1/TEAM_CONTRACT.md>), [팀 VLM Schema](</D:/projects/477_team_benchmark_v1/schemas/vlm_output.schema.json>)

camera_id/candidate_id는 runtime registry가 부여하고 model에 식별자를 판단 근거로 전달하지 않는다. CAM_01→실제 camera mapping을 명시해야 한다. multi-camera는 향후 camera별 routing envelope와 공통 incident correlation을 별도 처리하고 하나의 NORMAL이 다른 위험 view를 제거하지 않게 한다. 현재 단일 카메라 기준 Contract 변경은 불가피하지 않다. 실제 backend 정의가 제공되면 adapter boundary에서 정합성 검증을 추가한다.

reason_codes의 합의된 enum 범위는 저장소에서 발견되지 않았다. 예컨대 `OBSERVATION_INSUFFICIENT`, `P1_REFUSAL`, `P1_UNAVAILABLE`, `SAFE_NORMAL_EVIDENCE`, `VERIFIED_PERSON_DOWN_SIGNAL` 등을 사용하려면 기존 수신자 허용목록을 확인해야 한다. 구조는 유지하되 enum이 닫혀 있다면 기존 code로 매핑하고 자세한 이유는 audit record에 보존한다. P4 failure는 Stage1의 이전 SUSPICIOUS 결과를 DANGER로 덮어써 incident 확증처럼 보이게 하지 않고 후단 Human attention 이벤트로 전달한다.

## 5) Experiment Roadmap

### 5.1 Benchmark 진단과 새로운 분리 원칙

**[확인] Calibration/Test의 scene_group_id, split_group_id, source_video_id, source_sha256 교집합은 모두0**이다. split unit은 단순 clip이 아니라 shared site/actors/takes를 묶는 physical group이다. 선언된 manifest 수준에서는 직접 source/scene leakage가 확인되지 않았다. 하지만 데이터 규모는18 scenes/8 physical groups/2 datasets에 제한되며 이전 reasoning 실험과 관련 site/actor 그룹은 남아 있다. Test의 SPG_05 포함6개 후보는 related로 표시되어 있다. “이전 실험과 완전히 독립”이라는 해석은 부적절하다. [leakage 보고](</D:/projects/477/benchmark_triage_v1/reports/leakage_report.md>), [priority GT 보고](</D:/projects/477/benchmark_triage_v1/reports/priority_gt_report.md>), [diversity](</D:/projects/477/benchmark_triage_v1/reports/diversity_report.md>)

Calibration Danger3개는 optional subtype상 boundary crossing2/conflict1이고 person-down이 없다. Test Danger10개는 conflict8/person-down2이고 boundary crossing이 없다. **Cal/Test 위험 유형 coverage 불균형**이다. subtype은 optional human metadata이며 미기입 값을 추정해 채우지 않았다. 이것이 class labeling 오류나 모델의 unseen-category 성능을 확정하는 것은 아니다.

Human GT는 수동43개(Primary37+Ambiguous6), auxiliary confidence/subtype는 일관되게 수집되지 않았다. 일부 subtype coverage는 CV discovery hint이지 Human subtype 정답이 아니다. Ambiguous6개는 primary denominator/threshold fitting에서 제외되어 있고 이 Frozen run에서 모델 추론도 하지 않았다. 현재 Normal은 staged abnormal source의 전후 정상 구간·제한된 공개 데이터 중심이므로 실제 관제 Candidate 분포를 대표한다고 가정하지 않는다.

새 데이터는 기존 파일을 수정하는 `v1 업데이트`가 아니라 독립 디렉터리의 `477-stage1-router-dev-v2` 및 별도 safety-test version으로 구성한다. 기존 Test22개와 source·scene·related physical groups는 새 선택용 Dev/Calibration 및 새 독립 Test에서 재사용하지 않는다. 초기 reasoning/test에서 이미 본 유사 actors/sites도 분리한다. 기존 Calibration15개는 역사적 diagnostic reference로 남기고 선택용 데이터의 중심으로 삼지 않는다.

권장 초기 수집 계획(확정 수량·성능 보증 아님):

- Dev 탐색: 약300 clips, Clear100/HN100/Danger100, 별도 Ambiguous·failure stress. 실제 Stage0 통과 후보에서 채집하고 알려진 위험 source도 보강한다. 가능한 한 독립 camera/day/incident group을 늘린다.
- Calibration: Dev와 source/physical group이 다른 약200 clips, Normal100/Danger100을 시작점으로 삼되 danger subtype별 충분수 없으면 해당 scope Suppress 활성화 금지.
- 독립 Safety Test: 위험 False Suppression 한계를 정한 뒤 아래 sample target에 맞춰 확보; 비용·Normal suppression 평가용 Normal과 실제 arrival distribution shadow 자료도 별도 수집한다.

Dev는 positive/negative와 유사 CV지만 뜻이 다른 쌍을 포함한다. normal walking/entry, brief crouch→standing, sitting/stretch, greetings/play/contact, crowd co-motion, cleaning/work, reflections/shadows, detector jitter, dark/occluded/small-person, empty scene+missed person, true fall/down, genuine conflict, boundary crossing, track fragmentation, incident onset/end 포함 및 과거 위험 후 회복을 다룬다. 각 예에는 candidate-level must-surface와 “Stage1이 제거해도 되는가”에 필요한 observable tags·관측 충분성·불확실성·시간 구간을 수집한다. benign이어도 Stage1 입력으로 해소 불가능한 경우 abstain을 허용한다.

두 reviewer와 disagreement adjudication을 추천한다. 단순 source label로 Danger를 대체하지 않는다. 카메라 ROI/정책은 모델 결과·GT를 보기 전에 별도로 annotation하고, 사건 subtype나 outcome을 context에 넣지 않는다. 같은 사건 여러 view/겹치는 시간 window는 한 group에 넣는다. near-duplicate 영상·crop·계절만 다른 staged take도 가능한 physical group으로 묶는다.

### 5.2 통계적 안전성 해석

IID 독립 Danger에서 miss0건일 때 한쪽95% Clopper–Pearson 상한은 `1−0.05^(1/n)`이다. n3→63.16%, n10→25.89%. 즉 Test0/10 miss가 위험 제거율이 매우 낮다고 통계적으로 보장하지 않는다. Calibration과 Test를 단순 합친0/13도 독립 최종 Test가 아니며, 설명상 IID 상한은20.58%에 불과하다.

목표 danger false suppression 상한ε에 대해 miss0 가정의 최소 독립 위험 수는 `ceil(log(.05)/log(1−ε))`이다: ε1%→299,0.5%→598,0.1%→2,995. **이는 배포 안전 인증이나 수집하면 자동 달성되는 수가 아니다.** 실제 clip은 scene/incident 군집으로 상관되어 유효 표본 수가 작고, category/camera별로 별도 coverage가 필요하다. 동일 사건의 여러 clip을 독립299건으로 세지 않는다. danger FS와 최종 danger miss 각각 보고하고 group-bootstrap 구간·scene/incident-level failure도 병기한다.

Independent Test는 policy/model/input version·threshold·scope·success criteria를 잠근 후 한 번만 평가한다. 실패 사례를 개선에 쓰면 그 Test는 다음 버전의 Dev로 재분류하고 새 Test를 마련한다. Test 중간 결과를 보고 수량이나 Threshold를 바꾸지 않는다. Group-aware 실험으로 안전성 한계를 판단해야 한다.

### 5.3 평가 지표 정의

| 지표 | 정의/주의 |
|---|---|
| Stage1 Safe Normal Suppression Rate | GT Normal 중 Stage1 SUPPRESS / 전체 GT Normal; Clear/HN 각각과 source/group별 병기 |
| Stage1 Danger False Suppression Rate | GT Danger 중 Stage1 SUPPRESS / 전체 GT Danger; count 및 한쪽95% upper bound |
| P4 Escalation Rate | 실제 P4에 dispatch된 후보 / 모든 Stage0 후보; skip/실패/재시도 request 별도 |
| Danger Surface Recall | GT Danger 중 실제 Human Queue delivery 성공 / 전체 GT Danger; Stage1/P4/fallback별 분리 |
| Operator Queue Reduction | 1−최종 Human 후보 수/전체 후보; 중복 묶음 전·후와 normal Human 부담 병기 |
| Cost per Candidate | 모든 P1/P4 시도 usage 기반 API 비용 + 별도 로컬 비용 / 모든 후보; 실패/usage unknown은0으로 취급 금지 |
| Estimated Monthly Operating Cost | cameras×post-filter candidate rate×days 및 branch별 실제 cost; 인프라/관제 인건비 별도 |
| Stage1 Latency | Compact ready→routing commit의 mean/p50/p95/p99; CV/queue/API/adapter 분해; API timing과 분리 |
| 추가 보호 지표 | time-to-human, P4 wait, unavailable/refusal/fallback delivery, actual request savings, stale context·quality subgroup 실패 |

P4 rate는 Normal 제거 외에 immediate Human 증가로도 낮아질 수 있다. 따라서 human_immediate_rate 및 **Normal을 직접 Human으로 올린 비율**을 함께 보며 비용만 좋아지고 관제 부담은 악화되는 정책을 채택하지 않는다. 전체 weighted rate는 benchmark class 비율이 아닌 실제 candidate arrival mixture로 다시 계산한다.

### 5.4 작은 실험 순서와 Go/No-Go

아래 수치 기준은 **향후 Dev에서 사용할 제안 기준**이며 성능 예측이나 현재 Frozen Test에 맞춘 수치가 아니다. 안전 boundε·time-to-human SLA·비용 예산은 실험 전에 관제 운영 목표로 잠근다.

| 실험 | Hypothesis / 변경 사항 | 필요한 데이터 | Evaluation Metric | Success / Failure / 다음 단계 조건 |
|---|---|---|---|---|
| E0 Current Baseline Audit | 실제 코드·locked 결과·가드·timing·calls를 구분하면 병목이 드러남; 기존 파일 read-only | 현재 artifacts | 고정 gate counts, lock hashes, 실제 vs 정책 calls | **이번 조사 완료.** drift0, Test retuning0. 운영 queue 코드 부재는 후속 구현 요구로 남김 |
| E1 New Dev & CV Evidence Audit | 기존 Cheap CV 관측을 정확히 보존하면 semantic/quality 부족을 분리 가능; 재사용 가능한 fields만 분석 | 새 Dev300 계획, human tags, 원본/Compact 대응 | coverage omissions, tag concordance, unknown/quality subgroups | 안전 claim을 뒷받침하는 관측 태그 확보, group split/label adjudication 완료 전 선택 실험 금지 |
| E2 Task/State 분리 Ablation — 첫 성능 실험 | safe 질문이 기존 incident 질문보다 제거 판단에 적합; state 보강 효과와 분리 | 동일 새 Dev, P1 동일 모델, 최소 arms: original/original+safe-shadow/최소state+original/최소state+safe-policy | 8핵심지표, clear/HN, risk-coverage, semantic ambiguity, tokens | Dev Danger FS 관측0 및 추가 normal 제거가 여러 독립 group에서 나타남. 예: original 대비 Safe Normal +10%p 및 P4 −5%p를 탐색 gate로 사전 선언 가능. confidence만 증가/실패가 정상화되면 실패. 합격은 안전성 입증 아님 |
| E3 Camera Context | entry와 boundary/ROI 차이가 제거·위험 해석을 돕는다; 최선의 Dev arm에서 context off/on | 새 context-annotated cameras, boundary Danger/HN/일상 entry | boundary Danger FS, subgroup suppression, annotation time, tokens | held-out camera에서도 이득, boundary misses0·stale context invalid에서 suppress0. 해당 type 수 부족/권한 추론 의존하면 해당 scope 보류 |
| E4 Hybrid Safety/Fallback | 검증된 hazard 조기 분기와 quality abstain이 위험 delivery를 유지하면서 지연 줄임 | Dev danger/HN, synthetic missing/refusal/timeout/out-of-range/duplicate-answer, queue harness | danger surface/time-to-human, Normal Human rate, P1 call fraction, fallback delivery | invalid→SUPPRESS0; verified hazard 즉시 delivery·idempotency; P4 실패/누락도 Human. Human normal burden이 비용 절감 때문에 급증하면 실패 |
| E5 Router Calibration & Freeze | 적은 policy family를 독립 calibration에서 맞추면 overfit 줄일 수 있음 | 별도 Calibration, 위험 subtype 충분수; Dev 선택 완료 | risk bound/coverage, reliability/Brier, per-category FS, cost/latency | predeclaredε/coverage를 충족하지 못하면 threshold 완화 금지·scope 축소·추가 data. prompt/context/rules/adapter/threshold/contract hash freeze 후 Test |
| E6 Independent Safety Test | 잠긴 v2가 독립 scene/camera에서 위험 보존과 normal 제거를 재현 | 새로운 blind Test, 위험수는ε 기반, Normal·HN·Ambiguous 포함 | 8핵심지표+group uncertainty | 사전 안전 upper bound 충족, danger delivery SLA·필수 category coverage 충족, normal/P4 감소 재현. miss/coverage 부족/비용만 개선이면 운영 suppress 승격 금지; 같은 Test 재튜닝 금지 |
| E7 Real Cascade Cost/Latency Shadow | 사후 simulated saving이 실제 호출/월비용·시간 절감으로 이어짐 | 동일 새로운 후보 stream, AC/고정 하드웨어, representative camera rates | 실제 P4 requests, Stage1 p95/p99, peak backlog, per-attempt cost, operator queue | 실제 비용/latency budget 충족 및 정상 증가로 queue 부하가 악화되지 않음. 처음 shadow는 candidate를 실제 제거하지 않고 기존 관제 경로 유지; 별도 운영 검증 후 승격 |

P1/P4 유료 추론이 필요한 E2 이후는 **이번 조사에서 실행하지 않았다.** 후속 실행은 데이터/arms/예산을 구체화한 별도 작업으로 진행한다. 시험마다 P4 전수 reference가 꼭 필요한지 구분하고, true cascade의 비용 비교에는 routed items만 실제 호출하는 경로를 별도로 측정한다.

### 5.5 공정한 비교

새 Dev에서 original frozen P1 policy와 v2를 **같은 입력·후보·labels·하드웨어·P4 version**에서 비교한다. feature 변경과 prompt 변경은 factorial/단계별로 분리하고 branch 정책도 기록한다. P4 full-reference를 모두 추론하는 offline paired 평가와 actual conditional-call 운영 평가를 구분한다. P4 결과를 GT로 사용하지 않는다.

기존 Test22개의 최종 지표는 역사적 frozen baseline으로 그대로 보존한다. 새 데이터의 v2 수치를 이전22건과 단순 차감해 개선율이라고 하지 않는다. 별도 허용된 신규 Benchmark에서 original-v1과 v2 paired 비교를 계획하고, 잠금 전 반복은 Dev/Calibration에만 허용한다. 새 final Test에서도 반복 호출해서 마음에 드는 답을 고르지 않으며 API snapshot/SDK/service tier·질문 hash·raw output/usage·실패도 남긴다.

### 5.6 월 운영비 모델과 감도 분석

```text
M = Cameras × Candidates_per_camera_per_day_after_Stage0 × Days
q1 = P1 호출 후보 비율
r4 = 실제 P4 전달 후보 비율
API_month = M × (q1 × mean_P1_cost + r4 × mean_P4_cost)
            + billed_retry_and_failed_attempt_cost
Operating_month = API_month + Local_CV_compute + server/storage/network + 기타 운영비

# Token식 (1M tokens 기준, short context)
P1 = input_tokens × .10 / 1e6
P4 = ((input - cached - cache_write)×2 + cached×.1 + cache_write×2.5
      + output_tokens×10) / 1e6
# image tokens는 input에, reasoning tokens는 output에 포함; 중복 가산 금지
```

아래는 q1=1,30일, Test22개의 평균 P1/P4 비용을 가정한 **API 비용 시나리오**다. 실제 Camera 수·발생률 측정도, 달성된 escalation rate도 아니다. 같은 P4 mean을 사용하는 sensitivity이고 suppress된 input complexity에 따라 routed 평균 비용은 달라질 수 있다.

| Cameras | 후보/camera/day | 월 후보/P1 호출 | P4 rate100% (calls; USD) | P4 rate50% (calls; USD) | P4 rate25% (calls; USD) |
|---:|---:|---:|---|---|---|
| 50 | 2 | 3,000 | 3,000; $1,375.78 | 1,500; $688.35 | 750; $344.63 |
| 100 | 10 | 30,000 | 30,000; $13,757.78 | 15,000; $6,883.47 | 7,500; $3,446.32 |
| 500 | 20 | 300,000 | 300,000; $137,577.77 | 150,000; $68,834.74 | 75,000; $34,463.22 |

100-camera/10-candidate 가정에서 P1 월 비용은약$9.17이고 P4가 거의 전체를 차지한다. P1 usage400 tokens 증가 가정이면 월$1.20 추가다. 단순 기대값상 P4-only 대비 P1 비용 회수에 필요한 회피율은 `P1/P4≈0.0667%`지만 이는 안전 기준이나 실측 절감 증거가 아니다. 현재 Test의 실제 회피율은0%다. P4 skipped rate에는 직접 Human을 올린 후보도 포함하므로 Safe Normal의 이득과 구분한다.

GPU/decoder 상시 비용, CPU inference fallback, peak concurrency, 긴 관측 window, 실패 요청 과금, image detail/해상도/context tier, cache-write/read mix·regional premium, 과도한 재알림 중복은 따로 측정해야 한다. 높은 Camera 수를 월 단순 평균으로만 수용 가능하다고 판단하지 않는다. Stage0 candidate frequency가 현재 미측정이므로 월비용은 실측 운영 예측이 아니다.

## 6) Final Recommendation

1. **가장 큰 병목은 어디인가?** 직접 0건을 만든 것은 T_normal=.01과 score 분포다. 개선 관점의 우선 병목은 **사람이 있는 정상 상황을 설명하는 CV State·Camera Semantics와 P1의 incident/review 중심 목적의 불일치**다. Safety Rules가 Frozen 모든 후보를 escalation시켰다는 근거는 없다. CV State와 P1 reasoning 각각의 인과 기여율은 아직 미측정이며 새 Dev ablation으로 분리해야 한다.
2. **개발 비용이 가장 적은 유망 방법은?** 기존 Cheap CV 결과에서 coverage·detection confidence·recent gaps·짧은 posture phases를 보존하고 같은 P1에 safe predicate를 넣어 task alignment를 실험하는 방법이다. 새 모델이 필요 없다. 일반 entry와 미확인 boundary를 구분할 수동 Context가 다음 우선이다. 이득은 가설이며 Threshold 완화만으로 해결된다는 근거는 없다.
3. **P1 구조를 최대한 유지할 수 있는가?** 가능하다. model/endpoint/client/request1회/typed answers/P4 경로/외부 Contract v1을 유지하고 내부 Compact·질문·local policy·failure wrapper만 versioned로 발전시킬 수 있다. 기존 prediction Schema에 Router fields를 섞을 필요가 없다.
4. **P4 rate 감소를 위해 가장 먼저 할 성능 실험은?** 새 Human-labeled Dev 준비(E1) 후 **E2의 Task/State 분리 ablation**이다. original-v1, safe-shadow, 최소State 보강, safe-policy를 같은 데이터에서 비교한다. 현재 Test Threshold 재탐색이나 즉시 broad NORMAL rule 배포는 하지 않는다.
5. **현재 데이터로 충분한가?** 코드 병목 진단에는 충분하지만 튜닝·운영 안전성 입증에는 부족하다. 특히 Calibration Danger3, boundary Danger 없는 Test, 제한된 site/actors, 실제 Stage0 후보 분포 부재를 해결하는 새 Normal/HN/Danger/Ambiguous와 별도 Calibration·독립 Safety Test가 필요하다.

첫 후속 작업의 완료 기준은 “새 Dev에서 어떤 정상 유형을 어떤 관측 근거로 안전하게 제거할 수 있는지, 그리고 어떤 유형은 계속 P4여야 하는지”를 식별하는 것이다. **P1+P4는 유지하고, 안전한 제거의 증거를 먼저 늘린 뒤 정책을 보정한다.**

### 조사 재현과 변경 범위

진단은 [audit_artifacts.py](</D:/projects/477/planning/stage1_router_v2_research/audit_artifacts.py>)를 `python -B`로 실행하여 재현할 수 있다. 이 스크립트는 외부 호출/모델 import/기존 평가 실행 없이 고정 .01 정책·저장 usage/timing·lock hashes를 읽고 자신의 디렉터리 JSON만 쓴다.

무결성 검사: HARNESS lock30, Benchmark lock74, P1 freeze11, P4 freeze16, common adapter freeze2개의 각 지정 항목이 모두 일치했다(중복 포함133검사). 기존 final report/policy SHA 일치, Test22×2 모델 결과 SHA drift0. 파일의 lock 검증은 데이터/실행 재현성의 근거이지 모델 안전성의 근거는 아니다. 기존 team_frozen_v1의 사용자 미추적 파일은 수정하지 않았다.
