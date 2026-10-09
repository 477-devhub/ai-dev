# 477 AI E2 — Safe-to-Suppress Factorial Ablation

2026-10-09 (Asia/Seoul). **Harness 구현 및 Offline 검증 완료. 독립 Human-labeled Development GT가 없어 실제 모델 성능 검증은 NOT EVALUATED.** Decisions API/P4 호출0회, 실제 API 비용0달러다. 개선되지 않았다는 결과도, 개선되었다는 결과도 아직 없다.

## 구현과 사용법

이 폴더의 신규 파일만 사용한다. 기존 `P1Pipeline`, E1 Serializer/Schema 및 v1 기본 경로를 수정하지 않았다. 네 Arm에서 동일 Canonical과 동일 모델/endpoint/공통 질문을 사용한다.

| Arm | Compact | Questions |
|---|---|---|
| A | v1 | Original 7개 (single) |
| B | v1 | Original 7개 + safe predicate 1개 |
| C | v2 | Original 7개 |
| D | v2 | Original 7개 + safe predicate 1개 |

`prepare_arms()`는 E1 `prepare_compact()`를 이용해 각 버전의 Schema 검사·text·digest를 생성한다. A/B input hash 동일, C/D input hash 동일, A/C prompt hash 동일, B/D prompt hash 동일, 추가 전 Original 질문 내용이 정확히 동일한지 검사한다. Input에는 Human GT, 출처 이름/원본 dataset label, group, reviewer, 정답 설명을 전달하지 않는다. GT는 Manifest와 평가기에서만 사용한다.

단일 카메라 외에 attention(Original22→25, camera별 safe predicate), multi-camera(Original10→11) 입력/Answer parsing도 Offline 검증했다. Shadow Suppression은 attention의 모든 camera assessment가 guard를 만족해야 하며 Candidate 전체 단위 집계다. 실험의 실제 신규 Development 데이터는 아직 없다.

기존 P1의 `DecisionsClient.decide()`와 `build_questions()`를 재사용한다. E2 wrapper는 `decide()`의 로컬 함수 globals 복사본에서만 application retry를0으로 설정하고 SDK retry0도 유지한다. **원본 retry2 설정은 변경하지 않는다.** Timeout 후 재시도는 서버 처리와 중복 과금을 구분할 수 없기 때문이다. 네 Arm 공통 설정은 GPT-6 Luna, `/v1/decisions`, text only, connect10초/read120초, 별도 reasoning/tier 파라미터 없음이다. P4 관련 모듈을 import하거나 호출하지 않는다.

```powershell
# Repository root: D:/projects/477
$e2Python = 'experiments/p1_decisions/.venv/Scripts/python.exe'
& $e2Python experiments/stage1_safe_suppress_e2/scripts/preflight.py
& $e2Python experiments/stage1_safe_suppress_e2/scripts/run_e2.py audit
& $e2Python experiments/stage1_safe_suppress_e2/scripts/offline_validate.py
& $e2Python experiments/stage1_safe_suppress_e2/scripts/run_e2.py prepare --run pilot_ready_v2 --max-candidates 2
& $e2Python experiments/stage1_safe_suppress_e2/scripts/run_e2.py pilot --run pilot_ready_v2 --max-candidates 2
& $e2Python experiments/stage1_safe_suppress_e2/scripts/run_e2.py analyze --run pilot_ready_v2
```

Default Manifest는 빈 Development 파일이다. 현재 `pilot` 실행은 GT Gate에서 중단하고 API client를 생성하지 않는다. 새 Human GT와 Canonical이 준비되면 새 Manifest 경로를 `--manifest`로 지정하고 새 `--run` 이름을 사용한다. 실제 Pilot 시작 전 `plan.json`에 입력/질문 hash, 후보, exclusion registry hash, cost plan, protected hashes가 저장된다. 처음에는2 candidates ×4 arms 이하를 권장하며 `--max-candidates`로 확장한다. 후보별 Arm 순서는 Candidate hash로 회전하여 모든 A가 먼저 실행되는 순서 효과를 줄인다. 반복 stochastic 실험/무작위 block 실험은 이번에 수행하지 않았다.

## 질문 Config의 정확한 차이

`configs/original.json`은 기존 `decisions_questions_v1.json`의 byte copy다. `configs/original_plus_safe.json`은 같은 모든 질문/공통 policy/scope/adapter를 보존하고 version을 바꾼 뒤 `e2_safe_question` 한 개만 추가했다. Runtime validator가 이 두 변경 이외의 차이를 거부한다.

추가 질문은 `type=predicate`, `name=safe_to_suppress`다. SDK가 지원하는 응답은 `probability`이며 별도의 predicate confidence·free text·custom JSON 출력은 요청하지 않는다. 다음은 새 instructions 원문이다. 실제 전송 시 기존 scope와 공통 policy가 동일하게 앞뒤에 붙는다.

> Do the supplied CV observations provide sufficient direct evidence to dismiss this candidate from further operator or strong-vision review, with no unresolved safety-relevant signal? This is an evidence-sufficiency question, not the complement of incident probability. Assess actual sampled coverage, observation gaps and clip tail, posture changes and subsequent observations, detection and association quality, omitted tracks/interactions, and any scene semantics essential to interpret the candidate. Missing detections do not establish absence. Unknown or unavailable measurements do not establish normality. No persons detected with insufficient image or detection quality, low posture followed by unknown or lost observation, unresolved close interactions, boundary/authorization-dependent events, or omitted potentially relevant observations do not provide affirmative evidence for dismissal. Observed recovery does not erase a prior safety-relevant event. Proximity, low motion and contact proxies do not confirm assault, collision, intent or medical condition. If the required evidence is unavailable or insufficient, do not treat a lack of explicit incident evidence as evidence of safe dismissal. Use only the supplied observations; do not rely on answers to other questions.

같은 Request에 질문을 추가하면 incident/human_review/category 답도 변할 수 있으므로 별도로 저장·비교한다. Safe Question은 incident의 반환값에 의존하도록 설계하지 않았다. [공식 Decisions 가이드](https://developers.openai.com/api/docs/guides/decisions)와 [Python API Reference](https://developers.openai.com/api/reference/python/resources/decisions/methods/create)에서 지원 형식을 확인했고, 실제 P1 SDK3.26.0의 Typed Answer 정의도 확인했다. Default shell의 SDK2.48.0에는 Decisions types가 없으므로 **기존 P1 venv**를 사용한다. 환경을 업그레이드하거나 기존 dependency를 변경하지 않았다.

## Dataset 조사 및 Leakage Gate

[reports/dataset_audit.json](reports/dataset_audit.json)의 결과:

| 조사 항목 | 수 |
|---|---:|
| 기존 source manifest | 128 sources |
| 기존 candidate pool | 709 windows |
| 기존 review queue | 115 candidates |
| 기존 Human reviewed | 43 |
| Frozen primary / Challenge | 37 / 6 |
| E2에 적합한 신규 독립 Human GT | **0** |
| Clear / Hard Negative / Danger / Ambiguous 신규 GT | **0 / 0 / 0 / 0** |

기존 리뷰43개는 Frozen37 + Challenge6에 해당한다. SPG01~08은 기존 triage Calibration/Test Physical Group이며 SPG09는 reasoning에 사용된 다각도 촬영 그룹이다. 조사한 Pool709개는 모두 이9개 Group에 연결되어 제외한다. 전체20개 Scene·source ID·기존 clip hash·reasoning 원본 media hash/path·이전 Canonical hash를 exclusion registry에 저장한다. Calibration/Test 세부 GT나 모델 예측은 Feature/Prompt/Threshold 선택에 쓰지 않았다. 보호 파일의 **bytes hash**는 변경 확인 목적으로만 읽었다.

`evaluation_selection/review_decisions.json`은 Agent가 sample sequence/XML을 확인한 selection assessment이며 Human GT가 아니다. 원본 dataset action label, XML, 파일명, P4 출력도 새로운 Human GT로 인정하지 않는다. Team Frozen public `items.json`의12개 item도 기존 실험으로 확인했다. 그러나 그 공개 파일은 SRCxx generic ID이며 실제 원본 Scene/Physical mapping을 검증할 정보가 부족하다. **새 데이터의 Human independence evidence는 triage/reasoning/team 세 데이터셋을 모두 확인했음을 필수로 기록**해야 한다.

현재 조사는 구조화된 로컬 Pool/리뷰 자료 범위다. 모든 raw download의 모든 영상에 미사용 장면이 없다고 증명한 것은 아니다. 새 Source를 추가할 때 물리 장소·촬영 세션/배우·동일 사건이 겹치지 않는지 별도 확인이 필요하다. 선언된 metadata와 hash 검사는 사람의 잘못된 독립성 판단까지 해결하지 못한다.

준비된 자료:

* `data/development_manifest.json`: 신규 GT 없음이 명확한 빈 Manifest.
* `data/development_manifest.schema.json`: Human 원본 전체 재생 근거, reviewer/time/summary, source/scene/physical group, video/CV hashes, CV source link, 세 기존 dataset independence 확인 필수.
* `data/human_review_queue.csv`: 기존709개 **제외 감사 Queue**, GT/모델 score/원본 action 힌트 복사 없음.
* `data/new_human_review_queue.csv`: 신규 출처용 빈 등록 Queue.
* `data/labeling_protocol.md`: 사람의 원본 영상 재생·정상/Hard Negative/위험/불확실 라벨 정의·독립성 검증·불일치 처리.

유료 실행은 Manifest Schema, source/group/path/media hash overlap, Human provenance, CV/media hash link, Canonical Schema와 v1/v2 Schema를 통과한 후보만 허용한다. GT 누락이나 independence 미확인은 제외 사유로 남기고 Pilot을 억지로 실행하지 않는다.

## Parsing / Storage / Resume / Budget

`src/e2_answers.py`는 Original `DecisionAdapter` 전에 expected question name·type·duplicate·missing·refusal을 검사하고 finite/range 값, Choice distribution, Score labels/index/weighted mean 등을 확인한다. Invalid answer는 Adapter 입력에서 제거하고, 새 safe가 invalid/missing/refused이면 parsed complete=false다. 원래 DecisionAdapter의 score midpoint·confidence·review 의미는 유지한다. E1 v2를 기존 `PredictionAdapter`에 넣지 않으므로 제거된 v1 설명 필드에 의존하지 않는다.

Request별 Artifact에는 input text/compact, Canonical hash, compact digest, input/prompt/config/request hashes, requested/returned model, SDK/HTTP settings, 원본 client response body와 Typed Answers, 사용량, request id, timing, 실패 상태, parse issues, common decision와 safe shadow가 저장된다. JSON 비유한 값은 그대로 숫자로 저장할 수 없어 `invalid_nonfinite_number` 표식으로 보존하며 invalid 상태를 유지한다. 정답/label은 Model request에 들어가지 않는다.

`results/pilot_ledger.json`과 `pilot_request_cache/`는 **E2 전체 공유**다. 같은 Request hash는 새 Run 폴더에서도 다시 호출하지 않는다. Candidate/Arm별 slot Artifact를 별도로 저장하므로 서로 다른 Canonical metadata가 같은 모델 입력으로 직렬화되어도 각 후보 provenance를 보존한다. Cache hit의 usage/cost/timing은 원래 dispatch의 기록이며 새 dispatch 비용은0으로 별도 집계한다. 완료·refusal·invalid·실패 응답 모두 재사용하고, 응답 파일 없이 DISPATCHED 상태가 남으면 INDETERMINATE로 차단한다. Dispatch 전에 ledger를 atomic write하고 전체 Pilot 공통 exclusive lock을 잡는다. Ctrl+C 후 재개는 응답이 저장된 요청부터 cache를 사용한다. 프로세스 강제 종료로 stale `.pilot.lock`이 남으면 살아 있는 worker/원격 처리 여부를 확인한 뒤 사람이 복구해야 한다. **Ledger/cache를 지워 재시도하거나 unknown usage를0으로 처리하면 안 된다.** API가 invoice 차원의 exactly-once를 보장한다고 주장하지 않는다.

기본 예산 상한은2달러며 그보다 큰 설정은 거부한다. 요청별0.10달러를 먼저 예약하고 provider usage가 있으면 verified rate로 계산한 비용으로 대체한다. Failed/unknown usage는 예약액을 유지한다. 새 요청을 예약하면2달러를 넘을 경우 호출 전에 BUDGET_STOP한다. Request JSON은100,000bytes 이하로 제한하고 automatic retries는0이다. 초기2 candidate×4 arm의 최대 로컬 예약은0.80달러다. 실제 입력으로 추정한 비용과 예약 최대값은 plan에 따로 저장한다. 현재 신규 데이터0개의 plan은 요청0/추정0/예약0이다.

이는 **보수적인 로컬 비용 예약**이며 provider가 입력 Token을 hard cap하는 기능이나 invoice 지출 상한으로 오인하면 안 된다. 예외적으로 실제 usage가 예약을 넘으면 초과를 기록하고 다음 호출을 중단한다. 관련 분기도 테스트했다. [공식 Decisions 가격](https://developers.openai.com/api/docs/guides/decisions)에 따라 입력0.10달러/1M, long context multiplier를 별도 적용한다. 기본 regional premium이 없는 endpoint를 전제로 하며 별도 지역 과금 환경은 설정·사전 계측을 다시 고정해야 한다. Invoice는 확인하지 않았다.

## Offline 검증

[reports/offline_tests.json](reports/offline_tests.json)에 최신 테스트 결과와 보호 해시가 저장된다. E2 **36개 테스트가 모두 통과**했다. E2 테스트는 Synthetic response로만 수행하고, E1의21개 테스트를 별도 프로세스로 다시 실행했다. 모델 API는0회다.

검증 범위: A/B/C/D hash 공정성·Original 질문 보존·single/attention/multi-camera typed parsing·동일 DecisionAdapter 의미·Safe와 incident 비동치·missing/refusal/invalid/duplicate/nonfinite·raw 저장·cache resume·global cross-run 중복 방지·동시 lock·indeterminate·예산 중단/초과 기록·setting version 변경·Human provenance/overlap Gate·잘못된 write 경로 거부·평가 분모·불완전 paired 제외·SDK 설정 불일치 제외·0 miss의 confidence interval.

Mock 응답과 usage/latency는 `results/offline_demo_<codehash>/`에 mode=synthetic로 저장한다. [reports/offline_demo.json](reports/offline_demo.json)은 위치를 가리킨다. **이는 모델의 판단·비용·지연 측정값이 아니다.** Synthetic GT를 Development Manifest에 등록하지 않았다.

## 실제 Ablation 결과

[results/pilot_ready_v2/pilot_status.json](results/pilot_ready_v2/pilot_status.json): NO_ELIGIBLE_INDEPENDENT_HUMAN_GT. Actual Decisions0회, P4 0회.

| Arm | Normal Suppression | Danger False Suppression | Projected P4 Rate | 실제 API Cost | API Latency |
|---|---|---|---|---|---|
| A | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| B | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| C | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| D | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |

총 실제 지출0달러는 실험 미실행 결과이며 Arm별 모델 cost가0달러라는 측정값이 아니다. 모델의 false-positive/false-suppression, high-safe Danger, v2에 따른 판단 변화, 추가 질문의 과신 사례는 관측하지 못했다. 관측한 장애는 **독립 Human GT 부족**이다. SDK2.48.0 환경에 Decisions types가 없는 점도 확인하고 기존 P1 SDK3.26.0 환경을 사용하도록 해결했다.

## 평가기와 Shadow Policy

`src/e2_metrics.py`는 완전한 A/B/C/D paired 후보만 primary cohort에 넣는다. 한 Arm 실패 후보는 별도 목록·상태로 표시한다. 추가 all-candidate diagnostic에서는 failed/not-run은 escalation으로 간주한다. Ambiguous는 Normal 분모로 합치지 않고 별도 suppression count를 보고한다. N=0 비율은 null/NOT EVALUATED이고0으로 채우지 않는다.

계산 가능한 항목: Clear/Hard Negative 별도 정상 제거, Danger False Suppression, 사후 Projected P4 Rate, incident/review/confidence/safe score의 GT별 분포·Normal/Danger range overlap, answer issues, common question/category/review 변화, input/total usage·비용·API timing, Paired A↔B/A↔C/B↔D/C↔D delta, `(D−C)−(B−A)`의 State×Question interaction, v2 Feature Group bytes, high-safe Danger 및 shadow false-suppression 사례의 compact/raw 근거. Multi-camera/attention raw 답변은 모두 남고 score 요약은 candidate incident/review=max, safe=min으로 명시적 집계한다.

사전 고정한 진단 정책:

* `baseline_guard` (4개 Arm): 모든 expected 답변 complete, incident≤.01, no human review, no refusal, category=no_clear_incident, adapter confidence≥.90. 공개된 기존 비교 기준의 수치를 고정했으며 이번 데이터로 고르지 않았다.
* `safe_guard_095`, `safe_guard_099` (B/D만): 같은 guard에 safe≥.95 또는 .99 추가. A/C는 safe 질문이 없으므로 NOT APPLICABLE.

따라서 raw score 관계와 공통 baseline policy를 먼저 비교하고, 추가 safe guard는 제한된 진단값으로 따로 본다. 기존 Frozen Policy Lock은 수정하지 않는다. Safe guard를0.95/0.99 중 택하거나 운영 Threshold로 채택하지 않았다. 모델 probability/confidence는 안전 확률이 아니다. `Stage1 NORMAL`이라는 외부 결과를 생성하거나 운영 Suppress를 켜지 않는다.

Danger miss confidence interval은 candidate 단위 Wilson two-sided95%와 zero-miss일 때 exact one-sided95% upper bound를 출력한다. 예를 들어 위험10개에서 miss0이면 상한이 약25.9%라 운영 안전성의 증거가 아니다. 같은 Scene/Physical Group에 여러 후보가 있으면 독립성 가정이 깨져 이 구간은 과도하게 좁을 수 있다. 최종 검증에서 Group 단위 safety 평가가 필요하다.

## Token / Cost / Latency 분석

[reports/offline_input_costs.json](reports/offline_input_costs.json): 기존 unlabeled Canonical7개를 size 측정에만 사용했다. Frozen Calibration/Test 또는 신규 Human GT 실험이 아니다. `o200k_base` proxy tokenizer로 계측했고 API usage는 없다.

| 평균 로컬 추정 | A | B | C | D |
|---|---:|---:|---:|---:|
| Compact text + 동일 preamble tokens | 2,143.1 | 2,143.1 | 3,745.9 | 3,745.9 |
| JSON Request text tokens (questions 포함) | 4,014.3 | 4,431.1 | 5,643.4 | 6,060.3 |

새 Safe 질문은 request JSON token proxy 약416.9개를 추가하고, v2는 약1,629.1개를 추가한다. 이 JSON 표기는 실제 endpoint의 내부 질문 encoding/envelope와 다르므로 **실제 청구 Input Tokens가 아니다.** 지원 tokenizer cache가 없는 환경은 bytes/4 heuristic으로 fallback하고 방법을 저장한다. API 비용이나 모델 latency 증가 실측은 없다. 이전 E1의 CPU serialization 계측은 이번 API latency로 재해석하지 않는다.

v2 신규 Group 평균 bytes(독립 payload 표현, 서로 additive token 값으로 해석 금지): Coverage/Gap/Tail1,542.3, Posture Runs/Recovery/Unknown1,767.6, Detection/Tracking/Quality564.0, Interaction849.4, Selection/Omission491.0. Posture와 Coverage가 큰 Group이므로 후속 비용 Ablation 후보지만, **불필요하다고 결론 낼 성능 근거는 없다.** 전체 JSON overhead·공통 의미 설명·제거된 v1 필드 때문에 Group 합이 v1→v2 delta와 같지 않다.

새 질문의 추가 비용을 입력0.10달러/1M 가정으로 단순 추정하면 요청당 약0.00004169달러, v2의 추가량은 약0.00016291달러다. 실제 사용량/청구는 미확인이며 모델 cost 비교의 성공 결과로 보고하지 않는다.

## E3 Handoff

1. **Compact v2 실제 효과:** 미확인. 관측 근거 보존과 Schema 동작만 확인했다.
2. **Safe Question 실제 효과:** 미확인. 추가 Predicate 구현과 parse/cache 동작만 확인했다.
3. **가장 유망한 Arm:** 근거 부족으로 선정하지 않는다. D가 좋을 것이라는 가설과 비용 증가는 검증 대상이다.
4. **정상 제거를 방해하는 주된 요인:** 이번 실제 응답이 없어 순위를 정할 수 없다. Sparse gap/tail, low 이후 unknown, interaction meaning, quality, omissions, scene semantics가 가설 후보다.
5. **Safety Rule 보호 후보:** 미해결 standing→low, low 이후 미관측/Unknown, 낮거나 unavailable인 detection/association quality, ambiguous fragments, omitted low/interaction evidence, 중요한 경계 의미 미확인. 이 후보들은 E3 설계 가설이며 이번에 policy로 활성화하지 않았다.
6. **P4 Escalation 후보:** 미해결 위험/의미/품질·API 실패·missing/refusal/invalid·scene context 필요 상황. 실제 운영 mandatory rule은 별도 Calibration·safety 검증 이후 결정한다. 이미 명확한 위험의 Human immediate 분기는 E3에서 따로 설계한다.
7. **Router 입력·출력 구조:** 내부 입력은 schema/version·canonical/compact hash·common Decisions 값·safe shadow·parse issues·CV coverage/quality/temporal/selection evidence. 별도 versioned rule evaluation과 calibrated policy를 거쳐 기존 `NORMAL→SUPPRESS`, `SUSPICIOUS→ESCALATE_P4`, `DANGER→HUMAN_IMMEDIATE` 외부 envelope를 유지하는 설계를 권고한다. 이번 E2는 envelope/Backend Adapter를 생성하지 않았다.
8. **부족한 검증:** 실제 원본 Human-labeled independent Development, A/B/C/D API 응답, 실제 Usage/latency, Paired safety failure analysis, 추가 Calibration·Group 독립 Test, 실제 conditional cascade 호출 비용/E2E latency·오류 fallback·운영 queue 연결.

## 파일 목록과 보호 범위

| 신규 경로 | 목적 |
|---|---|
| `configs/original.json`, `original_plus_safe.json`, `experiment.json` | 정확한 질문 복사/추가 Predicate, Arm·budget·진단 정책 고정 |
| `src/e2_common.py`, `e2_inputs.py` | E2 한정 atomic write·hash, fair 입력·질문·token/feature bytes |
| `src/e2_answers.py`, `e2_metrics.py` | strict typed parsing·기존 Adapter 의미 유지, paired/shadow/CI/failure 분석 |
| `src/e2_dataset.py`, `e2_runner.py` | Human/leakage Gate, at-most-once cache·ledger·budget·client wrapper |
| `scripts/run_e2.py`, `offline_validate.py`, `preflight.py` | 실행·재개·분석 CLI, offline 증거 생성, SDK/key-presence 점검 |
| `tests/test_e2.py` | Synthetic response 기반 Offline 검증 |
| `data/*` | 빈 신규 Manifest/Schema, exclusion registry, 제외/신규 Review Queue, Human protocol |
| `reports/*`, `results/*` | 테스트·데이터 조사·로컬 비용 추정, Synthetic Artifact와 실제 미평가 status/plan |
| `README.md`, `requirements.txt` | 사용법·한국어 결과/한계/E3 인계, 기존 P1 환경 사용 명시 |

기존 파일 수정0개다. Frozen Benchmark/Human GT/Split/Results/Policy Lock, v1 질문/모델/API 설정·Schema/Serializer, E1 기준 구현, P4 Pipeline, Stage1 backend contract, CandidateEvent/VLMAssessment/Incident 및 백엔드 연동 작업 영역은 보존했다. 보호 hash 비교와 E1 regression도 통과했다. 기존 구현 버그는 E1의 출력 설명 renderer 호환성/Unknown 처리 한계를 인계하고 원본을 고치지 않았다.
