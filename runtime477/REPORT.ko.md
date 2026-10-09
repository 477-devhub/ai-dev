# 477 실시간 관제 MVP 구현·실측 보고서

작성일: 2026-10-09 KST. **전체 준비 상태: PARTIALLY_READY**.

후속 작업에서 iframe을 제거하고 기존 Figma 기반 React 관제 UI에 직접 연결했다.
새 UI의 실제 9영상 검증 및 최신 측정은 [UI 직접 연결 보고서](reports/REACT_UI_INTEGRATION.ko.md)를 참조한다.
아래 수치는 앞선 standalone UI 실행 결과이며 새 UI 실행과 구분한다.

9개 실제 영상의 1× 재생, 실제 CV 후보 발행, 브라우저 표시, 실제 P1→P4 비동기 분석과 동일 Candidate 갱신을 실행했다.
다만 관측된 후보는 CAM_04의 움직임 2건이며, 사람 주석 T0와 위험 사건별 탐지율은 확보하지 않았다.
**Time-to-First-Alert(T3−T0)는 NOT MEASURED이다. 5초 목표 달성을 주장하지 않는다.**
측정한 것은 후보 생성 이후의 T3−T1이며, 마지막 CPU 제한 실행에서 55.05ms / 111.53ms였다.

## A. Repository Audit와 실제 구조

| 조사 대상 | 실제 구현 확인 / 이번 처리 |
|---|---|
| P0/CV | experiments/p0_cv_only 및 backend frozen_v1에 YOLO26n-pose, SparseTracker, CameraFeatureExtractor 존재. 변경하지 않음 |
| Decoder | backend cascade_worker.prepare는 ffprobe 전체 show_frames → uniform64 select → native RGB decode → lossless WebP/roundtrip. 파일 기반 batch |
| YOLO/Pose | 기존 Full CV imgsz1280/batch16, 카메라 작업마다 별도 subprocess에서 load/warmup. 동시 카메라별 상주 GPU 복제 구조라기보다 **job마다 재초기화** |
| Tracking/State | sparse tracker, canonical cv-state-v1 및 compact v1/v2 구현 확인. E1 v2와 E2/E2.1 연구는 수정하지 않음 |
| P1 | 실제 DecisionsClient / GPT-6 Luna / original questions 존재. 새 worker가 기존 serializer/client 사용 |
| P4 | 실제 GPT-6.1 Sol Responses Vision 존재. native uniform64 protocol 유지 |
| Backend queue | AnalysisJobService 실제 bounded queue와 HTTP job API 존재. 단, 결과 전 초기 후보 경로는 없었음 |
| 기존 UI | 9-camera grid, scripted scenario, 분석 cycle 존재. 실시간 CV로 생성한 첫 후보 전달 구조는 별도 구현 필요 |
| 데이터 구조 | ModelInput/ModelAssessment/Incident 존재. 사용자 예시 CandidateEvent/VLMAssessment라는 이름 그대로는 없으므로 새 후보 ledger를 기존 contract와 분리 |
| 기존 직렬 의존성 | prepare→CV→P1→P4 결과 뒤 Incident 생성. HTTP 요청은 비동기지만 첫 관제 표시는 cascade 결과에 의존 |
| 새 UI 연결 | 새 FastAPI/WebSocket/Attention Queue를 구현하고 기존 React에 `?mode=live-replay` iframe 진입점 추가. 기존 Incident 저장소로 병합하지 않음 |
| RTSP / 477대 | 이번 구현·검증 대상 아님 |

아키텍처 다이어그램과 전체 실행 순서는 [README](README.md)에 있다.
문서 중 과거에 “미구현”이라 남아 있는 SDK/adapter 설명과 실제 코드가 다른 부분은 실제 adapter 코드를 기준으로 판단했다.

### 223초의 확인된 근거

`mock_cctv/live-verification-stats.json`에 완료된 4개 작업의 합산 평균 **222.990초**가 있다.
이번 실행으로 재현한 동일 입력 benchmark가 아니라 **기존 로그**다. Queue wait 및 T0→T3가 아니다.

| 기존 단계 | 평균 | 전체에서 차지하는 비율 |
|---|---:|---:|
| 영상 준비 | 54.232초 | 24.3% |
| Full CV | 70.541초 | 31.6% |
| P1 worker/API 포함 | 4.164초 | 1.9% |
| P4 worker/API 포함 | 94.043초 | 42.2% |
| mapping | 0.010초 | <0.1% |

따라서 P1만 빠르게 해서는 해결되지 않는다. 가장 큰 단일 단계는 P4이며, 준비+Full CV도 124.773초다.
**기존 로그는 decode와 encode를 나누지 않았으므로 54초 전부를 decode라고 주장할 수 없다.**
Full CV 70초도 순수 GPU forward latency가 아니며 프로세스 시작·load·warmup·특성 추출이 포함된다.

새 런타임에서 동일 **64/native/lossless** 프로토콜을 관측 완료 구간에 적용해 측정한 1건의 준비 상세는 다음과 같다.

| 새 background 준비 상세 | 실측 |
|---|---:|
| 전체 PTS 탐색 | 6.517초 |
| selected RGB decode | 7.354초 |
| 64 lossless WebP encode + roundtrip 검증 | 53.432초 |
| wrapper 포함 준비 합계 | 68.329초 |
| Full CV wrapper | 29.069초 |
| 그 안의 detector warmup | 10.821초 |

이 1건에서는 decode보다 lossless encode/검증이 훨씬 느렸다. 원본·구간·CPU worker 수가 기존 로그와 다르므로
과거 54.232초의 정확한 내부 구성으로 소급하지 않는다. CPU 제한은 Fast Alert 지연을 보호하기 위한 선택으로,
AI 준비 총시간은 오히려 길어졌다. 64프레임 생성은 첫 후보의 선행 조건에서 제거했다.

## B. 실제 구현 범위

`runtime477/` 아래에 새 런타임을 추가했다. Frozen 파일·GT·split·질문·routing lock·E1/E2는 변경하지 않았다.

- 카메라별 독립 decoder, 공통 재생 epoch, 실제 재생 프레임의 latest-slot CV sampling.
- 모델 1개를 공유하는 9-camera GPU batch. 640 input / 목표 2 sampling FPS / 2회 연속 신호.
- 움직임 변화 및 가로 형태 person bbox proxy. 폭행·범죄·의료 상태 확정 없음.
- Candidate ID, 최초/최근 관측, signal/zone별 merge, 짧은 무관측 구간 이후 새 ID.
- WebSocket 전체 snapshot, 9개 프레임, Preview/Attention Queue, 원본 영상과 실제 P4 인용 이미지.
- P1/P4 개별 bounded queue/worker 1개씩, timeout, process tree 회수, 동일 ID 재제출 방지, retry 0.
- P1 NORMAL은 shadow 상태로 유지. Fast Alert와 Stage 1 decision contract 분리.
- 실패·적체·AI 비활성화는 사람 검토. Human generation 이후 늦은 결과는 stale audit.
- T1/T2/T3/T4/T5, frame PTS, batch latency, CPU/GPU 표본, queue와 merge 측정.
- 파일 기반 저장 결과 모드와 Human T0 오프라인 결합 도구. 저장 결과 모드의 전체 실제 시연은 미검증.

새 런타임의 P1은 **검토 완료된 Fast CV compact-only state**를 바로 사용하는 최적화가 아니다.
관측 완료 구간에 기존 Full CV/compact v1을 background로 적용한다. 이 부분의 시간은 아직 크다.
P4 축소 입력의 안전성 비교는 수행하지 않았고 64프레임을 유지했다.

## C. 실제 9개 영상 결과

대표 최종 실측: `179ce01b94f24f538e0c7caf01b5b8f4`.
원자료: [마지막 실행 metrics](reports/run4-bounded-cpu.json), [후보별 T1~T5](reports/final-candidates.json).
브라우저 검수 화면: [9-camera wall](reports/live-wall.png), [원본 및 P4 근거](reports/evidence-ui.png).
GPU: RTX 3050 Laptop 4GB, Fast CV Torch 2.14.1+cu126. 사전 재생본은 원본의 640×360 파생본이며 실제 움직이는 프레임에 추론했다.

| 카메라 | 실제 decode frame | 재생 종료 PTS | CV 표본 | 결과 |
|---|---:|---:|---:|---|
| CAM_01 | 929 | 30.933s | 62 | ENDED |
| CAM_02 | 918 | 30.567s | 62 | ENDED |
| CAM_03 | 935 | 31.133s | 63 | ENDED |
| CAM_04 | 1,050 | 34.967s | 70 | ENDED |
| CAM_05 | 897 | 29.867s | 60 | ENDED |
| CAM_06 | 921 | 30.667s | 62 | ENDED |
| CAM_07 | 908 | 30.233s | 61 | ENDED |
| CAM_08 | 915 | 30.467s | 61 | ENDED |
| CAM_09 | 915 | 30.467s | 61 | ENDED |
| 합계 | **8,388** | 최대 약 35초 | **562** | **9/9 완료** |

각 카메라의 decode는 약 30fps, CV는 약 2.00~2.03fps였다.
첫 프레임을 0초로 계산하므로 `frame_count / last_frame_elapsed`는 명목 30fps보다 소폭 높게 나온다.
전체 세션 길이를 분모로 한 aggregate decode는 239.87fps, aggregate CV는 16.07fps다.
짧은 영상부터 종료되므로 전체 세션 합산 FPS는 9×30 / 9×2보다 작다.
웹 브라우저의 원본 30fps 렌더링을 입증한 결과는 아니다. JPEG 전송과 UI 표시는 의도적으로 낮은 FPS다.

## D. Performance Report

| Metric | Old Pipeline | New Pipeline: 마지막 실제 실행 |
|---|---|---|
| Time-to-First-Alert T3−T0 | N/A | **NOT MEASURED — Human T0 없음** |
| 후보 생성→Frontend T3−T1 | N/A | **평균/p50 83.29ms; p95/max 111.53ms; n=2** |
| Backend→Frontend T3−T2 | N/A | p50 82.26ms / p95,max 110.76ms |
| Fast CV inference batch latency | N/A | 평균 90.09 / p50 76.26 / p95 219.93 / max 254.67ms |
| 영상 PTS→CV observation | N/A | p50 104.40 / p95 255.66 / max 565.78ms; T0 지표 아님 |
| P1 latency | 기존 worker 포함 평균 4.164s, n=4 | 실제 API 1.135s / worker 포함 3.537s, n=1 |
| P4 latency | 기존 worker 포함 평균 94.043s, n=4 | 실제 API 50.963s / worker 포함 55.239s, n=1 |
| 9-camera FPS | N/A | 카메라별 decode 약 30, CV 약 2; 세션 aggregate 239.87 / 16.07 |
| decode frame drop | N/A | container frame count 대비 0/8,388 = **0%** |
| 한 source-frame interval 이상 늦은 decode | N/A | **0.227%**; drop과 다름 |
| decode 지연 | N/A | p50 .63 / p95 1.35 / max 144.20ms |
| queue length / peak waiting backlog | 기존 스냅샷 queued 3 | 완료 시 0/0, waiting peak P1 1 / P4 1 |
| deduplication | N/A | 14번 연속 trigger 중 12번 merge: **85.71%**, 고유 후보 2 |
| GPU memory | 기존 해당 로그 N/A | 장치 전체 1초 표본 peak **881 MiB**, Fast worker PyTorch peak allocation **100.96 MiB** |
| CPU/GPU utilization | N/A | 장치/호스트 전체 표본 peak **93.7% / 97%** |
| Fast model cold start | N/A | **15.56s**; 실제 재생 시작 전이며 T3−T1에 포함하지 않음 |

Fast CV batch 수치는 카메라별 표본에 동일 batch 시간을 기록한 가중 분포다. 단일 프레임당 독립 처리시간이나 562개 독립 batch가 아니다.
장치 전체 utilization/memory는 다른 프로세스의 영향이 있을 수 있고 1초 표본이므로 순간 절대 peak를 보장하지 않는다.
T3는 브라우저 clock offset 보정 후 두 번의 animation frame을 거친 ACK다. 마지막 두 표본의 clock RTT/2는 각각 0.5ms였다.
샘플 수 2 및 API 1회로 일반적인 p95 SLO를 추정할 수 없다.

첫 후보: 영상 3.00초에 생성, T3−T1 **55.05ms**, T4−T1 **103.24초**, T5−T1 **158.56초**.
두 번째 후보: 영상 25.00초에 생성, T3−T1 **111.53ms**.
실측 실행은 비용·작업 수를 제한하기 위해 `--max-ai-jobs 1`로 실행했다. 두 번째는 `QUEUE_BACKPRESSURE`로 사람 검토에 남았다.
첫 작업의 **실제 background preparation 중 새 후보 전달**을 확인했다. P4 API 실행 중 새로운 영상 이벤트가 발생하는 장시간 연속 replay는 이번 실제 영상 길이에서 검증하지 못했다.
해당 비차단 worker 성질은 별도 synthetic timeout 테스트로 검증했으며 실제 P4 부하 실험과 구분한다.

### 실패·이전 실행도 보존

| 실행 | T3−T1 p50 / max | 주의사항 |
|---|---|---|
| [1: Fast only](reports/run1-fast-only.json) | 90.10 / 106.09ms | API 비활성. batch shape 변경 시 CV max 2.123s 발견 |
| [2: 실제 AI 연결](reports/run2-mapping-failure.json) | 189.35 / 221.70ms | P1 실제 응답 후 새 mapper의 risk_axes 누락으로 fallback. 수정·회귀 테스트 추가 |
| [3: P1/P4 완료](reports/run3-ui-delay.json) | **7,580.75 / 15,055.84ms** | 두 번째 브라우저 ACK 지연. 삭제하거나 성공 표본에서 숨기지 않음 |
| [4: background CPU 제한](reports/run4-bounded-cpu.json) | 83.29 / 111.53ms | 2-thread lossless encode 및 낮은 process priority. P1/P4 실제 완료 |

3번의 T1→T2는 짧았고 지연은 T2→T3 구간이었다. CPU 경쟁·브라우저 paint/visibility 중 어느 하나가 유일 원인인지
확정할 tracing은 없다. CPU 제한 후 짧아진 1회 결과만으로 15초 tail이 영구 제거되었다고 주장하지 않는다.
최종 UI에는 동일 후보 카드의 불필요한 재생성을 줄이는 변경도 추가했지만 위 4번 latency 표본 이후의 변경이다.

## E. 테스트와 Demo Readiness

| 검증 | 실제 결과 |
|---|---|
| 신규 runtime HTTP/WS, clock ACK, dedup, 상태, Human stale 보호, queue, P1/P4 failure, recorded 모드 API 차단 | **11 passed** |
| 재사용 backend cascade/execution/audit 회귀 | **29 passed** |
| backend Frozen 계약 해시 | **Frozen contracts match** |
| 기존 frontend build | PASS |
| 기존 frontend unit tests | PASS (실제 실행 출력에 포함된 local/API/highlight/monitoring suite) |
| 실제 9 MP4 완주 | 9/9, 8,388 frames |
| 실제 P1→P4→동일 Candidate 갱신 | 완료 2회, 마지막 1회 API latency 위 표 |
| camera failure isolation | [실제 영상 8개 + 의도적 누락 1개](reports/camera-isolation.json): 오류 1, 나머지 8개 완료 |
| 브라우저 원본/Keyframe 열기 | 실제 UI에서 확인 |
| Human T0 및 위험 사건별 recall / false-positive rate | **미검증** |
| RTSP / 477 cameras / 장시간 soak / reconnect replay resume / 분산 DB | **미구현·미검증** |

**PARTIALLY_READY**인 이유:

1. Fast Alert와 async AI를 보여주는 로컬 기술 데모는 가능하다.
2. 9개 영상에서 생성된 후보는 모두 CAM_04의 motion proxy였다. P4가 본 첫 약 5초 구간은 일반 차량 통행으로 설명됐다.
   다른 영상의 위험 사건을 제때 검출한다는 증거는 없다. 두 후보를 실제 위험 2건으로 발표하면 안 된다.
3. T0 미주석이므로 5초 이하 Time-to-First-Alert와 누락률은 알 수 없다. 이전 실행의 15초 표시 지연도 남아 있다.
4. 새 queue/UI는 실제 동작하지만 기존 Incident 시스템으로의 정식 병합·영구 job recovery는 후속 작업이다.
5. 저장 결과 모드는 분리되어 있으나 실제 end-to-end 실행은 하지 않았다. Direct DANGER는 검증되지 않아 비활성이다.

## F. 발표에서 사용할 수 있는 문장

- “9개 실제 MP4를 공통 1배속 시간축에서 끝까지 처리하고, 재생 중인 프레임으로 후보를 생성했습니다.”
- “최종 측정의 두 후보에서 탐지 후 브라우저 표시까지 55ms와 112ms가 걸렸습니다. 영상의 최초 이상 징후부터의 시간은 아직 측정하지 않았습니다.”
- “같은 실행에서 P1 API는 1.14초, P4 API는 50.96초였으며 첫 후보 표시는 이 결과를 기다리지 않았습니다.”
- “AI 실패나 큐 적체가 있어도 후보를 남기고, 최종 판단은 사람이 하도록 구현했습니다.”
- “이 수치는 9개 파일 재생 환경의 소수 표본입니다. RTSP, 477대 확장성과 위험 사건 탐지율은 아직 검증하지 않았습니다.”
- “다음 단계는 Human T0/사건별 recall 검증, 작은 사람·자세 변화 후보 검출 개선, P4 근거를 보존하는 프레임 준비 최적화입니다.”

“9대의 모든 위험을 5초 안에 검출했다”, “실제 477 CCTV 실시간 운영 가능”, “P4 51초가 모든 상황에서 보장된다”는 문장은 사용할 근거가 없다.

## 변경 파일

| 경로 | 목적 |
|---|---|
| runtime477/config.json | Fast CV / queue / mode 설정 |
| runtime477/detection.py | 관측 기반 후보 신호와 short window |
| runtime477/stream_worker.py | 독립 9 decoder, resident GPU model, JSON IPC |
| runtime477/state.py | Candidate, merge, Human generation, append audit |
| runtime477/ai.py | P1/P4 queue, 기존 execution/adapter bridge, shadow 정책 |
| runtime477/prepare_worker.py, media.py | 64/native/lossless 근거 준비 및 CPU·timeout 제한 |
| runtime477/server.py, ui.html | 실제 후보 API/WS와 9-camera UI·표시 ACK·근거 보기 |
| runtime477/run.py, requirements.txt | 실행 entry/dependencies |
| runtime477/annotate.py | Human T0와 wall-clock의 사후 결합 |
| runtime477/tests/*, verify_camera_isolation.py | 회귀 및 실제 카메라 격리 검증 |
| runtime477/README.md, REPORT.ko.md, reports/* | 실행 설명, 실측 보고서·원자료 사본 |
| ../477-frontend/src/LiveReplay.tsx, src/main.tsx | 기존 React에서 명시적인 live-replay 진입점 |

프론트 저장소의 다른 기존 수정 파일은 이 작업의 변경 목록에 포함하지 않았다. Commit/push는 하지 않았다.
원본 영상, 기존 Frozen benchmark 결과, E1 Compact v2, E2 harness, E2.1 연구 파일은 그대로 보존했다.
