# Figma 기반 관제 UI 직접 연결 검증

2026-10-09. 런타임 instance `129cec1941dd4d74915703daabf2770d`.

**직접 연결 기능: READY. 전체 위험 탐지 MVP: PARTIALLY_READY.**
기존 보고서의 탐지 커버리지/T0/RTSP 제약은 그대로다.

## 구현

iframe을 제거하고 Figma `50:2` 화면의 기존 React Header, 로고, 색상 토큰,
3×3 카메라 벽, 우측 요약·후보 카드, 상세 화면 레이아웃에 런타임 데이터를 직접 연결했다.
위험 점수를 만들어 넣지 않고 초기 후보/사람 검토/AI 추정/관제사 처리 상태를 표시한다.
상단 실측 모드·시작 버튼과 Preview 분리는 새 기능에 맞춰 추가했다. Figma 전체 화면의 픽셀 동일성을 주장하지 않는다.

- `/runtime/ws`: 최신 실제 JPEG, camera state, Candidate ID, P1/P4 결과
- `/runtime/api/start`: 9 MP4 공통 1× 시작
- `/runtime/api/candidates/{id}/displayed`: 화면 노출 후 T3 ACK
- `/runtime/api/candidates/{id}/human`: 확인/종결 및 audit
- `/runtime/original/{camera}`, `/runtime/evidence/{id}/{frame}`: 원본 영상과 근거
- 기존 8000 API와 연구/실험 코드는 유지. 새 후보의 상태 소유자는 runtime ledger이며 Incident DB 자동 복제는 미구현.

## 실제 검증

| 항목 | 결과 |
|---|---|
| 9개 실제 MP4 | 9/9 완료, 총 8,388 decoded frames |
| 1× 재생 | 각 영상 29.9~35.0초 실제 경과, 공통 시작 시간축 |
| Decode FPS 합계 | 239.86 (서로 다른 종료 길이를 포함한 전체 구간 평균) |
| CV FPS 합계 | 16.07 |
| Frame drop rate | 0% (컨테이너 frame count 대비; 의도적 CV/화면 subsampling 별도) |
| 후보 | 2개, CAM_04 MOTION_CHANGE; 위험 2건이라는 뜻이 아님 |
| Candidate→React UI, T3−T1 | 135.30ms / 270.44ms |
| T3−T1 평균/p50 | 202.87ms, n=2 |
| T3−T1 p95/max | 270.44ms, 소표본 |
| 시계 정렬 불확실성 | 최대 9.15ms (최소 RTT 방식) |
| Time-to-First-Alert T3−T0 | NOT MEASURED — Human T0 미주석 |
| Fast CV batch | 평균 107.11 / p95 211.97 / max 241.96ms |
| GPU 할당 peak | 100.96MiB (PyTorch); nvidia-smi peak는 저장 JSON 참조 |

첫 후보의 실제 P1 API 2.176초, P4 API 56.130초를 확인했다.
이는 API 시간이며 영상 준비·Full CV·대기를 포함한 후보→최종 결과 시간과 다르다.
원본 MP4 duration 35초, readyState 4, 실제 P4 F001/F032/F064 근거 이미지 로딩을 확인했다.
첫 후보의 P4 완료 결과가 같은 ID로 사람 검토로 갱신됐고, UI의 `확인 완료` 클릭이 서버에 기록되어 처리 기록으로 이동했다.
두 번째 후보도 첫 후보 처리와 무관하게 남아 분석을 완료했고, `AI_DANGER_ESTIMATE`로 사람 확인 대기열에 표시됐다.
두 작업 모두 완료했다. P1 API 평균 1.379초/max 2.176초, P4 API 평균 66.064초/max 75.999초(n=2).
첫 후보의 관제사 확인 기록은 그대로 유지됐다. AI 위험 추정의 정확성을 검증한 것은 아니다.
최신 API 분포·상태는 동봉 JSON 참조.

브라우저 DOM에서 iframe 0개, 카메라 9개, 로딩된 실제 프레임 9개, 로고 자산 정상 로딩을 확인했다.
페이지 재진입 후 서버 후보 상태 복원도 확인했다.
`npm run build` 성공, `node scripts/test-local.mjs` **28/28 통과**(새 runtime 정책 회귀 테스트 4개 포함).
오류/normal/Human 우선 분기와 revision 회귀는 단위 테스트 결과이며 실제 API 오류를 이번 실행에서 강제 주입한 것은 아니다.

## 실행 및 산출물

서버: `D:/projects/477`에서 `python -m runtime477.run --ai --max-ai-jobs 3 --port 8011`.
프론트: `D:/projects/477-frontend`에서 `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174`.
접속: http://127.0.0.1:5174/?mode=live-replay . 현재 실행은 재생 완료 상태이며, 재시연 시 서버 재시작이 필요하다.
API 없이 실제 CV만 시연하려면 `--ai` 생략.

변경 파일: frontend `src/LiveReplay.tsx`, `src/runtime/{model.ts,useRuntime.ts,runtime.css}`,
`src/App.tsx`(진입 링크), `vite.config.ts`(prefix proxy), `tests/runtime.test.ts`,
`scripts/test-local.mjs`, `docs/LIVE_RUNTIME.md`; runtime README 및 이 보고서·측정 원자료.

증거: `react-ui-metrics.json`, `react-ui-candidates.json`, `react-live-grid.png`(실제 동시 재생),
`react-live-detail.png`(실제 P4 결과/근거), `react-live-grid-final.png`(관제사 처리 기록).

발표 문장: “Figma 기반 관제 UI에 실제 9개 MP4의 CV 후보와 비동기 AI 결과를 직접 연결했습니다.
이번 두 후보는 생성 후 화면 표시까지 135ms와 270ms가 걸렸으며, P4 완료를 기다리지 않았습니다.
영상 속 최초 이상 징후부터의 지연, 위험 사건 누락률, RTSP·477대 확장성은 아직 검증하지 않았습니다.”
