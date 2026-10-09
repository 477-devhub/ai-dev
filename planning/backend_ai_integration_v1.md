# 현재 AI 모델의 백엔드 연결 계획

작성: 2026-10-09. 대상: `D:/projects/477`의 현재 AI 구현 → `D:/projects/477-backend`.
범위: 기존 모델을 실제 영상 입력부터 사건 저장·프론트 표시까지 연결하는 개발용 v1.
이번 요청에서는 계획만 작성하며 모델 호출·코드 변경·배포는 실행하지 않는다.

## 목표와 범위

현재 Cheap CV → P1 → 필요 시 P4를 백엔드의 비동기 분석 작업으로 연결한다.
모델·질문·점수 정의·프롬프트·기존 라우팅 임계값은 버전을 고정한다.
Stage1 router v2 연구, 새로운 학습/데이터 수집, 임계값 튜닝은 별도 작업이다.

1차 입력은 등록된 MP4와 명시적인 분석 구간이다. 카메라별 분석을 먼저 완성한다.
RTSP/HLS 라이브 입력, 477대 동시 처리, 영구 DB, 자동 다중 카메라 사건 병합은 후속 범위다.
여러 카메라의 영상은 각각 분석할 수 있지만 같은 사건이라고 자동 묶지 않는다.

## 확인된 현재 상태

| 구성 | 확인한 구현 | 연결에서 맡을 역할 |
|---|---|---|
| Cheap CV | `experiments/p0_cv_only/src/pose_detector.py`, `sparse_tracker.py`, `feature_extractor.py`, `state_builder.py`; YOLO26n-pose 가중치 존재 | 실제 프레임으로 canonical CV state 생성. 백엔드의 HOG 관측 어댑터와 구분 |
| P1 | `experiments/p1_decisions/src/compact_serializer.py`, `decisions_client.py`, `decision_adapter.py` | CV state를 compact로 변환하고 현재 Decisions 모델에 질문하여 Stage1 판정 |
| P4 | `experiments/p4_gpt61_sol_vision/src/frame_loader.py`, `visual_prompt_builder.py`, `openai_client.py`, `p4_pipeline.py` | 실제 프레임에서 정밀 판정·위험축·프레임 근거·설명 생성 |
| 결과 정합성 | `experiments/common_adapter_v2` | incident 여부와 사건명 모순 정리. 보정/calibration이 아님 |
| 기존 라우팅 | `experiments/triage_frozen_v1/routing_policy_lock.json` | `T_normal=.01`, review 없음, refusal 없음, `no_clear_incident`, confidence≥.90 조건. 직접 danger 분기 비활성 |
| 백엔드 실행 | `app/models/base.py`, `execution.py`, `registry.py`, `app/main.py` | ModelAdapter → execute → ingest_model_input |
| 사건·프론트 | `app/services/incidents.py`, `policy.py`, 기존 API/WS | 결과 저장, 위험도·순위, 상세/근거 영상, ACK/복구, snapshot push |

현재 cascade 결과는 P1과 P4를 모두 실행한 뒤의 offline replay다.
실제 조건부 P4 호출과 작업 큐는 이번 연동에서 구현해야 한다.
기존 triage Test22건은 Stage1 제외0건, P4 전달22건이다. 현재 P1의 비용 절감 효과를 전제하지 않는다.
팀 영상 결과는 AI reference 기준이며 human GT 정확도나 정상 오탐 검증으로 사용하지 않는다.

## 실행 흐름

```text
등록된 camera + clip_ref + start_ms/end_ms
  → 분석 job 생성, 중복 조회
  → 고정 프레임 준비 + 실제 PTS/frame_id + resolver 등록
  → Cheap CV worker → canonical CV state
  → P1 compact + 질문 → raw decision
  → 고정 Stage1 policy 판정/기록
  → P4 visual worker (필요한 후보)
  → common-adapter-v2 + BackendAssessmentMapper
  → execute 검증
  → apply_assessment → Incident / Review / Suppressed
  → 기존 snapshot/WS → 프론트 사건 카드·상세·근거 영상
```

기본 검증 모드에서는 Stage1 policy를 shadow로 기록하고 전부 P4로 전달한다.
이는 운영 연결 검증용 모드이며 기존 frozen cascade와 같은 실행 정책이라고 표시하지 않는다.
연동 검증 완료 후 명시적인 `frozen_cascade_v1` 모드에서 기존 Stage1 gate를 활성화한다.
두 모드는 구분해 기록하며 같은 결과/비용 지표로 합치지 않는다.

Stage0의 운영 후보 생성기는 아직 검증되지 않았다. 1차에는 분석 요청으로 들어온 모든
영상 구간을 처리하며 CV 점수만으로 입력을 사전 제거하지 않는다.
P1 실패는 P4로 전달하고, CV/P4 실패나 최종 deadline 초과는 검토 사건으로 저장한다.

## 어디에 어떻게 붙일 것인가

아래 파일명은 구현 시 제안이다. 실험 저장소는 동결된 기준으로 유지한다.
백엔드로 필요한 코드·설정·라이선스/출처만 명시적으로 가져오며 benchmark 데이터·GT·전체 venv는 옮기지 않는다.
`sys.path` 수정, Windows PID polling, benchmark item_id 로더를 운영 코드에 사용하지 않는다.

| 백엔드 경로 | 추가/변경 내용 |
|---|---|
| `app/models/adapters/cv_features/*` | detector/tracker/extractor를 일반 입력 프레임 기반으로 분리. canonical state schema와 설정 고정. CV는 관측 생성 담당 |
| `app/models/adapters/p1_decisions/*` | serializer, 질문 설정, 현재 client와 decision parser를 패키지화. benchmark 로더 대신 전달된 state 수신 |
| `app/models/adapters/p4_vision/*` | 실제 프레임·resolver를 받는 visual client/구조화 출력/근거 검증. benchmark loader 의존 제거 |
| `app/models/adapters/cascade_v1.py` | `ModelAdapter.evaluate(ModelInput)` 구현. CV/P1/P4 호출·단계별 deadline·fallback. SDK/요청 직렬화는 adapters 내부 |
| `app/models/adapters/assessment_mapper.py` | 실험 decision/visual → 백엔드 `ModelAssessment` 변환. raw/normalized/backend 세 결과 구분 보관 |
| `app/models/registry.py`, `app/config.py` | 명시적인 `cascade_v1` 등록. 모델/가중치 경로, 입력 프로필, 단계별 시간/동시성/모드 설정 |
| `app/main.py`, `app/models/media.py` | 작업별 prepared resolver를 모델 실행에도 전달하고 사건 근거 제공까지 같은 프레임 사용. 수명·해제 정책 추가 |
| `app/services/analysis_jobs.py`, `app/api/analysis.py` | 분석 요청/조회, bounded queue, job 상태, idempotency, 완료/실패 저장. 모델 호출 중 API 상태 lock을 잡지 않음 |
| `app/services/policy.py`, `incidents.py` | Stage1 route와 최종 사건 정책을 분리. 검토/제외/복구를 기존 저장 경로에 연결 |
| `app/schemas/model.py`, `app/api/contracts.py` | 필요한 내부 routing/job metadata를 typed contract로 추가. 기존 프론트 필드 의미 유지, 변경 시 계약 검사/동결 |
| `docs/*`, `handoffs/*`, `.env.example`, `pyproject.toml` | 재현 가능한 설치·실행 안내, 의존성 확인, 설정 예제, API 계약/프론트 handoff |

백엔드 HOG `local_cv`는 그대로 별도 이름으로 유지한다. 이번 Cheap CV를 동일한
구현처럼 취급하지 않고 `cascade_v1`의 관측 생성기로 연결한다.
P0 rule engine은 최종 판정 주 경로에 넣지 않는다. P2/P3는 비교 모델로 보존한다.

## 핵심 계약 차이와 해결

### 1. 영상 입력 프로필

백엔드 sampler는 기본4장/640×360이고 현재 최대16장 제한이 있다.
현재 모델의 기본 프로토콜은 `uniform_total64_v1`; 팀 실험의 source별10..64장은
해당 bundle에서 배정된 별도 프로필이다. 일반 신규 입력에는 이를 임의 적용하지 않는다.

별도 `ai_frozen_v1` 프로필로 기존 frame loader의 sampling·색공간·해상도·순서·WebP 전송을
재현한다. 단순히 기존 sampler의 frame_count만64로 바꾸지 않는다.
고정 영상의 원본 loader와 새 loader가 RGB hash/시간/순서를 재현하는지 확인한다.
재현 불가능한 구간은 오류/지원 범위로 기록하고 frozen-v1과 동일하다고 주장하지 않는다.
모델 입력 timestamp는 필요한 상대 시간을 쓰되 backend 근거 시간은 source video 기준 ms로
변환하고 offset을 보존한다. 실제 PTS를 사용하며 frame 번호로 시간을 추측하지 않는다.

### 2. 결과 형식과 의미

| 모델 결과 | 백엔드 연결 규칙 |
|---|---|
| severity/imminence/exposure/persistence | 유효한 측정 답만 `risk_axes` 0..1에 연결. risk는 서버 가중식으로 계산, confidence는 곱하지 않음 |
| score refusal/missing | frozen raw decision은 그대로 보관하되 backend 해당 축은 null. 실험 adapter의 대체값0.5를 실제 측정으로 저장하지 않음 |
| confidence/human_review | 검증 후 연결. 계약 오류/미측정/근거 오류에는 review 강제 |
| possible fall/person-down | `collapse`로 UI 분류하되 설명에 의심/가능성을 보존. 확정 사건으로 서술하지 않음 |
| possible physical conflict | `conflict`, 의심 상태 보존 |
| possible scene/boundary entry | 경계 위반 의미가 확인되지 않으면 `uncertain` + review. 단순 scene entry를 침입 확정으로 변환하지 않음 |
| no clear incident | 이것만으로 명시적 normal로 변환하지 않음. 별도 typed routing 판정과 gate 검증을 거쳐 처리 |
| P4 frame_ref/description | 입력 frame_id에 연결하고 근거 text·timestamp·frame_url 전달 |
| temporal_summary/reason/uncertainties | `ai_opinion`, `uncertainty_reason` 및 상세 설명으로 전달. timeline은 검증된 시간 근거만 사용 |
| usage/timing/retries/request_id | 분석 이력에 단계별 저장. 사건 요약 metadata와 실제 pipeline 통계로 연결 |

현재 `ModelAssessment`에 `p_incident`/Stage1 route가 없고, 백엔드 suppression에는
normal/confidence≥.90/risk<20이 필요하다. 실험 gate와 백엔드 gate는 같은 조건이 아니다.
따라서 raw decision을 `normal`로 바꿔 기존 policy를 통과시키는 방법은 사용하지 않는다.

제안: versioned 내부 `RoutingAssessment`에 stage, policy_version, disposition,
p_incident, guard 결과를 담는다. frozen gate가 선택한 SUPPRESS는 별도 정상 제외 기록으로
저장하고 모델 판정/제외 이유/근거 미제공 여부를 보존한다. 기존 위험도/실패 불변식은 유지한다.
P4의 최종 no-clear 결과도 자동 normal 대신 초기에는 review로 표면화하고, 최종 제외 정책은
별도 의미와 테스트를 명시한 뒤 활성화한다. frozen offline `surface_p4()`와 이 연동 정책의 차이를 기록한다.
초기 연동은 offline operator queue 수와 동일하다는 목표보다 실제 결과의 누락 없는 전달을 우선한다.

P1에는 frame citation이 없으므로 P1 근거 frame_id를 만들어 넣지 않는다.
P4 근거 문구는 현재 backend make_incident의 고정 `Referenced observation`을 대체할
typed evidence 설명 경로로 전달한다. 추정 bbox/동일인 정보는 만들지 않는다.

### 3. 비동기 실행과 실패

현재 backend 기본 timeout은5초, P4 실험 client read/write timeout은900초이고 retries도 있다.
전체 adapter를5초 wait_for로 감싸서는 현재 파이프라인이 정상 연결되지 않는다.
HTTP는202를 즉시 반환하고 실제 분석은 큐에서 수행한다.
단계별 deadline과 전체 deadline을 별도로 설정하고 실제 샘플 시간으로 초기 값을 확정한다.

CV는 장기 실행 bounded process worker로 detector를 warmup하며 처음에는 동시성1로 시작한다.
동기 SDK는 검증된 비동기 client로 전환하거나 bounded 별도 worker에서 실행한다.
worker를 분리하더라도 backend 공통 execute를 통해 최종 출력·근거·실패를 검증한다.
outer cancellation만으로 과금 요청/스레드가 종료됐다고 가정하지 않는다.
취소·late completion·재시도·중복 요청을 추적하고 완료 후 늦은 결과가 검토 사건을 덮어쓰지 않게 한다.

이미 accepted된 입력과 운영자가 ACK한 사건은 재추론하지 않는다.
job idempotency와 기존 sample ledger를 함께 사용한다. 서버 재시작 내구성은 메모리 v1에서
보장되지 않으며 재시작 후 자동 재호출을 기본으로 하지 않는다.
큐가 가득 찬 경우 접수 성공으로 응답하지 않고 명시적인 오류를 반환한다.

## 제안 분석 API

```json
POST /api/analysis/jobs
Idempotency-Key: <new-request-key>
{
  "camera_id": "CAM_02",
  "clip_ref": "ASSET_0002",
  "start_ms": 0,
  "end_ms": 30000
}
```

신뢰된 asset 등록 경로로 연결된 token만 받는다. 사용자 임의 파일 경로/외부 URL은 받지 않는다.
응답202: job_id/status. 조회: `GET /api/analysis/jobs/{job_id}`.
상태: queued/preparing/cv/p1/p4/completed/failed; 결과에 incident_id 또는 suppressed_id,
review 여부, 단계 시간 포함. 실패한 추론도 가능한 경우 검토 사건 링크를 반환한다.
잘못된 카메라/영상 등록 요청 자체의 오류와 접수 후 모델 실패를 구분한다.
프론트는 기존 사건 WS/상세 API를 사용하며 분석 진행 상태만 추가로 표시한다.

## 구현 순서와 완료 기준

| 순서 | 작업 | 완료 기준 |
|---|---|---|
| 1 | 소스/설정/가중치 hash 고정, 입력/출력/route 계약 확정 | 원본 frozen 파일 변경0, 이식 범위·의존성·mapping 명시 |
| 2 | 동일 프레임 loader + CV state 생성기 이식 | 실제 영상에서 frame/time/hash와 CV state 일치 또는 허용 차이 명시, GT 미유입 |
| 3 | P4 단독 어댑터 → mapper → 기존 저장/WS 연결 | 실제 영상 새 추론이 카드·위험축·설명·실제 근거 이미지/영상으로 표시됨 |
| 4 | P1 serializer/client + shadow route 연결 | 동일 저장 raw answer의 decision/guard가 원본과 일치, P4 결과 경로 보존 |
| 5 | job API/큐/worker/deadline/fallback + 실조건 cascade | API 비차단, P1 실패→P4, P4 실패→review, 중복 호출 방지. SUPPRESS 시 P4 호출0 확인 |
| 6 | 실제 영상 통합 점검, 문서/설정/프론트 handoff | GET/WS/ACK/restore/근거 재생 동작, 실측 단계 시간·호출·usage 기록 |

3단계에서 P4부터 연결하면 전체 cascade 작업 완료 전에도 실제 모델 결과를 프론트에서
검토할 수 있다. 4~5단계가 끝나야 CV→P1→P4 연동 완료로 표시한다.
작업 규모 가정: 담당자1명, 현재 API 접근/가중치/실행 환경 사용 가능 시 약4~6 작업일.
환경 충돌·GPU 제약·동영상 입력 차이·프론트 계약 변경량에 따라 조정한다.

## 검증과 납품

- 저장된 raw answer/frames 기반 offline parity: 새 모델 호출 없이 serializer/adapter/mapper 검사.
- 계약 경계: 잘못된 frame_ref, 축 refusal, missing answer, NaN/범위 위반, 단위/offset 검사.
- 실행: timeout/refusal/network failure/CV failure/queue full/동시 중복/late completion 검사.
- 기존 서버 회귀: 전체 pytest 및 `scripts/check_contracts.py`; 계약 변경 시 재동결.
- 실제 입력 smoke: 등록 MP4 → 새 추론 → 사건 → WS → 상세/영상/근거 → ACK.
- route fixture: 실제 frozen gate를 만족하는 입력에서 P4 호출0, 그 외1, 오류에서 review 전달.
- 기존 frozen Test는 재추론/재튜닝하지 않고 새 연동 점검 샘플을 사용한다.

외부 호출을 수반하는 검증은 구현 후 영상 수·최대 호출/비용을 구체화해 실행 범위를 정한다.
현재 계획에는 유료 호출이나 새 provider capability 확인이 포함되지 않았다.
기존 API/model 명칭은 저장소에서 확인한 설정이며 실제 작업 시 SDK/API 접근 preflight가 필요하다.

납품물: cascade 어댑터와 작업 API, 실행 환경/설정, 모델·프롬프트·입력 profile provenance,
계약/프론트 안내, offline/실영상 검증 기록, 호출·시간·실패 로그.
기존 메모리 서버의 운영 한계는 그대로 문서화하며 production 준비 완료로 표시하지 않는다.

## 조사 근거

- backend: `AGENTS.md`, `docs/ownership.md`, `docs/model-contract.md`, `docs/api-contract.md`,
  `app/main.py`, `app/config.py`, `app/models/base.py`, `registry.py`, `adapters/ingestion.py`,
  `app/schemas/model.py`, `incident.py`, `app/services/policy.py`, `incidents.py`.
- AI: `experiments/p0_cv_only/README.md`, `src/*`; `experiments/p1_decisions/src/*`,
  `configs/decisions_questions_v1.json`; `experiments/p4_gpt61_sol_vision/src/*`, `configs/p4_v1.json`;
  `experiments/common_adapter_v2/README.md`.
- routing/results: `experiments/triage_frozen_v1/routing_policy_lock.json`, `scripts/analyze.py`,
  `analysis/cascade_report.md`; `experiments/team_frozen_v1/README.md`, `scripts/worker.py`,
  `analysis/report.md`; `planning/stage1_router_v2_research/report.md`.
