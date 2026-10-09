# 477 AI E2.1 — 신규 Development 데이터와 Human Review 준비

2026-10-09 (Asia/Seoul). **개발 작업 완료, Human Labeling·독립성 최종 확인은 미완료.** 신규 공식 영상28개와 Candidate28개를 준비했고 실제 P0 CV 생성28/28, v1/v2 및 A/B/C/D Offline 입력 준비28/28을 확인했다. Human Reviewed/Finalized는0이며 E2 평가에 편입된 후보도0이다. 유료 Decisions/P4 호출0회다.

Human Review 서버를 실행해 두었다: **[로컬 Review 열기](http://127.0.0.1:48771/)**. 브라우저에서 실제 Candidate와 원본 영상의 로드(readyState4, media error 없음)를 확인했고, 아무 Label도 제출하지 않았다.

## 1. Source Audit / 실제 수집

자세한 권한·접근·중복 위험 비교는 [source_audit.md](reports/source_audit.md), 로컬 Raw/ZIP 목록은 [local_inventory.json](reports/local_inventory.json)에 있다.

기존 data/downloads/benchmark media에서141개 영상 경로 및5개 ZIP을 조사했다.64개 경로는 기존 사용/연관 Source registry에 직접 연결되고77개는 INDEPENDENCE_UNVERIFIED다. 이77개가 새 독립 자료라는 뜻은 아니다. ZIP member·mock CCTV·원본 AIHub 장소/촬영 세션·기존 Team 자료의 관계와 사용 권한이 미확인인 것은 제외했다. 기존 128 sources/709 windows/43 Human reviews/Frozen37+Challenge6는 read-only reference다.

[ASSIST-IoT 저자 저장소](https://github.com/ASSIST-IoT-SRIPAS/multimodal-fall-detection-dataset)와 [저자 Zenodo](https://zenodo.org/records/8340379)에 Dataset CC BY4.0이 명시되어 있어 제한적으로 수집했다. Fixed commit `7a11c96b9a3576cef92f0795a19b3786c69a3335`의 사람 reference 영상28개(70,081,620bytes)만 수집하고 mannequin4개는 제외했다. 원본 Git blob checksum 및 SHA256를 검증했다. Attribution과 LICENSE/README/촬영 notes를 data/에 보존했고, clip 변환을 기록했다.

공식 원본 디렉터리 분류는 ADL19 / surface fall7 / immobility2다. 이는 **Source taxonomy이며 Human Normal/Danger GT 분포가 아니다**. 영상을 본 사람이 관제 필요성과 실제 관측 사실을 라벨링해야 한다. 동작명·파일명·URL·원본 분류를 Review UI에 노출하지 않는다.

VIRAT Ground, NTU RGB+D 및 CCTV-Fights는 계약/승인·사용 범위 확인이 필요해 수집하지 않았다. UCF-Crime/UP-Fall은 현재 영상 재사용·파생 조건이 충분히 명확하지 않아 수집 보류했다. UR 공식 URL은 조회 실패로 미확인이다. 팀 직접 촬영은 장소/참여자 동의 및 사용 조건을 사람이 확보해야 한다. 승인·이메일 발송·Terms 수락은 대신 수행하지 않았다.

## 2. Candidate Pool / CV

| 항목 | 현재 실제 수량 |
|---|---:|
| 다운로드된 신규 Source | 28 |
| Candidate Window | 28 |
| Source당 Window | 1 |
| 보수적인 Physical Group bucket | 1 |
| 미확정 Scene bucket | 1 |
| Canonical CV 성공 / 실패 | 28 / 0 |
| v1/v2 및 A/B/C/D 입력 준비 | 28 / 28 |
| Human independence confirmed | 0 |

Collection 전체를 하나의 Physical Group으로 묶고 Scene은 unresolved bucket으로 두었다. 실제 촬영 Scene이1개임을 주장하는 것이 아니라, 장소·배우·세션이 미확인인데 독립 Group 수를 부풀리지 않기 위한 분류다. 현재 자료는 staged 참고 영상이며 실제 CCTV 운영 Stage0 출력의 발생률/Recall/분포를 대표하지 않는다.

전체 원본의 첫 chronological 비중복 구간(최대30초)을 Source당1개 선택했다. 초 단위 원본 시작/끝, Original/Clip/Canonical hash와 Sampling/CV config를 저장했다. 후보 순서는 원래 경로의 Hash 순서이며 원본 행동명·P1/P4·Human Label로 선택하지 않았다. 현재28개 짧은 영상으로60~100개를 맞추려고 같은 사건을 여러 Window로 늘리지 않았다. **목표 수량·다양한 독립 Physical Group은 아직 부족하다.**

[pool.json](data/pool.json)에 모든 Candidate와 상태가 있다. CPU/GPU 환경은 기존 P0 venv·모델·설정을 사용하고 Detector/Tracker/FeatureExtractor를 변경하지 않았다. 신규 clip용 adapter가 round-half-up `j*(frame_count-1)/63`의64장 RGB를 읽고 기존 `StateBuilder._camera_state()`를 재사용한다. Canonical schema의 generic `ITEM_01`은 내부 metadata placeholder이며 실제 Candidate ID는 별도 Manifest에서 연결한다. CV가 Frozen benchmark에 붙어 있는 기존 frame loader를 바꾼 것은 아니다. 신규 wrapper의 decode는 OpenCV이며 기존 Frozen ffmpeg pixel byte와 동일하다는 주장은 하지 않는다. 같은 신규 Canonical에서 v1/v2를 생성하는 공정성은 유지된다.

실제 [cv_quality.json](reports/cv_quality.json): 모든 후보에서 person detection이 있었고 기존 P0 overall reliability label은 high26/medium2였다. 이는 GT·의료 상태·정상·위험 판단의 성공률이 아니다. pose visibility/fragmentation/ambiguous link 등의 원래 측정값을 별도로 저장했다. CV 오류는 FAILED/error를 남기고 candidate를 삭제하지 않으며, hash가 유효한 READY는 재실행하지 않는다.

## 3. Leakage / Integrity

기존 E2 `exclusion_registry.json`, Dataset Schema와 `validate_manifest()`를 그대로 재사용한다. 추가로 Video/Clip SHA256·Source/Group mapping·timestamp range·clip duration·Canonical Schema·원본/Clip/Window CV provenance·Human review media fingerprint를 확인한다. Labeling 이후 영상이나 Window가 바뀌면 `REVIEW_MEDIA_CHANGED`로 편입을 거부한다.

`historical_fingerprints.json`은 기존 evaluation MP4/mock media/등록 Scene별 raw 대표 영상86개와 available Team source sample28개를 screen한다. 총114개 record 중1개는 decode/probe 오류로 남았다. Team manifest에 존재하지만 로컬 PNG가 없는 sample도 있었다. 모든 Raw 구간을 exhaustively 비교하거나 모든 Team 원본 관계를 확인한 것은 아니다. Missing source mapping은 Human 독립성 확인에서 별도로 해결해야 한다.

3~5개 시점의 dHash를 사용하여 near-duplicate/같은 Scene 의심을 표시한다. Hamming6은 중복 검토용 고정 기준이며 안전 라우팅 Threshold가 아니다. crop/mirror/재촬영/다른 구간·카메라 변경은 놓칠 수 있고 단순 배경은 false flag를 만들 수 있다. **일치 flag가 없다고 independent로 인정하지 않는다.** 현재 모든 신규 Source는 INDEPENDENCE_UNVERIFIED이며 E2 평가에서 차단한다.

`development_group_registry.json`은 이 Development에 사용/검토한 Source/Scene/Physical Collection을 향후 독립 Calibration/Safety Test에서 제외하도록 보존한다. 자료 부족 상태에서 임의로 새 Calibration/Test split을 만들지 않았다.

## 4. Human Review Workflow

대규모 framework 없이 Python 표준 HTTP 서버와 HTML/JS로 구현했다. localhost만 bind하며 POST에는 origin/token 검사, media에는 Range/allowlisted opaque Candidate endpoint를 사용한다. Reviewer 화면은 모델/CV scores·원본 파일명·기존 action label을 보여주지 않는다.

1. Reviewer ID를 입력하고 Candidate를 선택한다. 후보28개를 순서대로 검토하면 된다. 원본 분류를 이용해 위험 우선순위를 정하지 않았다.
2. Candidate 전체와 원본 Candidate 구간 및 필요한 전후 맥락을 실제 재생한다. Loop/원본 구간 시작 버튼을 사용할 수 있다.
3. Label·관측 근거·불확실한 부분을 작성한다. 보조 태그의 관측/해석을 분리하고 모르면 null로 남긴다. boundary authorization/정책을 모르면 임의로 위험/정상 확정하지 않는다.
4. 실제 재생 확인 checkbox를 체크하고 저장한다. Player telemetry는 Human attestation 보조 기록이며 완전한 재생/인지의 자동 증명이 아니다.
5. Reviewer2는 다른 ID로 독립적으로 같은 후보를 본다. 자신의 첫 제출 전에는 다른 Reviewer의 답이 숨겨진다.
6. 일치하면 AGREEMENT_READY, 다르면 DISAGREEMENT다. 불일치는 기존 리뷰에 참여하지 않은 Human Adjudicator가 원본을 다시 보고 근거를 남겨 ADJUDICATED로 해결한다.
7. 명시적 Finalize 후 FINALIZED가 된다. 두 Review가 있다고 자동 Finalize하지 않는다. 단일 Reviewer는 명시적 옵션에서만 인정하고 기록하며 Export는 기본적으로 제외한다.

상태: UNREVIEWED / REVIEWED_ONCE / AGREEMENT_READY / DISAGREEMENT / ADJUDICATED / FINALIZED. 같은 Reviewer의 중복 저장은 append-only revision이며2명 검토로 세지 않는다. Finalized record 수정은 차단하고 별도의 versioned correction을 요구한다. [labeling_protocol.md](data/labeling_protocol.md)와 [Human schema](data/human_review.schema.json)에 규칙이 있다.

**저장만으로 평가 Manifest가 자동 갱신되지는 않는다.** Review 기록을 저장한 후 사람이 export 검증 명령을 실행해야 Finalized + independence/integrity 검사를 통과한 후보만 포함된다. 유료 API 자동 실행은 없다.

## 5. Human GT 현재 상태

| Label | Reviewed | Finalized |
|---|---:|---:|
| CLEAR_NORMAL | 0 | 0 |
| HARD_NEGATIVE_NORMAL | 0 | 0 |
| ANCHORED_DANGER | 0 | 0 |
| AMBIGUOUS | 0 | 0 |

실제 Human Labeling을 Codex가 완료 처리하지 않았다. Test의 Synthetic Review는 temporary fixture에만 쓰고 Production Review record로 저장하지 않았다. 현재0/28 finalized임을 실제 UI에서도 확인했다. Reviewer 간 일치도 역시 N=0이라 측정되지 않았다.

## 6. 실행 / Human Handoff

```powershell
# D:/projects/477에서 실행. 현재 Review 서버는 이미 localhost:48771에 실행 중.
$e21Python = 'experiments/p1_decisions/.venv/Scripts/python.exe'
& $e21Python experiments/stage1_dev_e21/scripts/serve_review.py --port 48771
```

이미 실행 중일 때 위 명령을 중복 실행하지 말고 [Review 화면](http://127.0.0.1:48771/)을 열면 된다. 프로세스 ID는 `review/server.pid`, 로그는 `review/server.stdout.log` / `server.stderr.log`에 있다. 재시작해도 저장한 Review는 이어진다. 부가 기록은 관측 태그(person count/posture change/recovery/close/occlusion/quality/gap)와 해석 태그(boundary context/operator reason/uncertainty)를 분리한다.

독립성은 별도 Human curator가 과거 triage/reasoning/team 출처·장면·배우·세션·사건과 비교해 기록한다. 확인할 수 없으면 아래 confirm 명령을 실행하지 않는다. Source별 확인 evidence와 reviewer를 실제 값으로 넣는다.

```powershell
& $e21Python experiments/stage1_dev_e21/scripts/prepare_dataset.py confirm-independence --source-id DEVSRC_001 --reviewer CURATOR_ID --evidence '실제 원본과 과거 촬영 그룹 비교 근거' --checked-datasets 477-triage-normal-v1 477-reasoning-v1 new477-total64-v1
```

위 Source ID는 형식 예시이며 독립성이 확인됐다는 뜻이 아니다. near-duplicate/이전 Group flag가 있으면 우회하지 말고 별도 근거 검토와 source registry correction이 필요하다. unknown location/session/actors를 추정으로 채우지 않는다.

검토 완료 또는 중간 상태 확인:

```powershell
& $e21Python experiments/stage1_dev_e21/scripts/prepare_dataset.py export
# reports/readiness.json: finalized_eligible, ABCD prepared, exclusion reasons
# data/development_manifest.json: Finalized + independent + integrity valid 후보만

# 새 GT 준비 후에도 이번 단계에서 API를 호출하지 않고 E2 prepare만 수행
& $e21Python experiments/stage1_safe_suppress_e2/scripts/run_e2.py prepare --manifest experiments/stage1_dev_e21/data/development_manifest.json --run e21_dev_prepare_v1 --max-candidates 2
```

현재 Manifest는 유효한 빈 Dataset이다. 실제 신규 영상의 Canonical/v1/v2/ABCD 준비는28개 있지만 finalized eligibility는0이라 유료 Pilot은 아직 실행하면 안 된다. 향후 실제 API는 별도 지시에 따라 E2 단계에서 수행한다. 기존 E2 data/Manifest를 덮어쓰지 않고 E21의 별도 `--manifest` 경로를 넘긴다.

자료 재생성/추가 등록:

```powershell
# 공식 limited collector는 이미 완료했으며 기존 checksum 일치 파일은 재다운로드하지 않음
& $e21Python experiments/stage1_dev_e21/scripts/acquire_assist.py
experiments/p0_cv_only/.venv/Scripts/python.exe experiments/stage1_dev_e21/scripts/build_pool.py --historical-index
experiments/p0_cv_only/.venv/Scripts/python.exe experiments/stage1_dev_e21/scripts/build_cv.py
& $e21Python experiments/stage1_dev_e21/scripts/validate_all.py
```

새 팀/공개 Source는 `sources.json`의 source path/hash/license evidence/neutral context/scene/physical/session 정보로 등록한 뒤 같은 Pool builder를 사용할 수 있다. Source당 max1이 기본이고 max3까지 명시적으로 요청할 수 있으나 같은 사건의 여러 Window를 독립 사례로 집계하지 않는다. 현재 source IDs·clip recipe·finalized review를 재배정/덮어쓰면 안 된다.

## 7. E2 연결 상태 / 정책 설계

* Original/Clip/Canonical Hash와 연결, 모든 신규 Canonical Schema, v1/v2 Schema 및 같은 Candidate의 A/B/C/D alignment 검증 완료.
* Human Finalized-only / clip media fingerprint / 독립성 Gate가 동작함. 현재 모든 후보는 Human 미검토와 독립성 미확인으로 평가 편입 차단.
* 실제 E2 Decisions API Pilot, 계정 접근·실제 Usage/성능/비용·지연은 이번에 평가하지 않음. P1/P4 호출0회.
* [shadow_policy_design.md](data/shadow_policy_design.md)에 기존 Baseline의 부분집합 Safe guard 한계와 safe-centered interface/evaluation family를 설계했다. 기존 E2 guard와 Arm 정의를 바꾸거나 새 Rule/Threshold를 실행하지 않았다. Prompt 효과와 CV veto 효과는 후속 별도 factor로 비교해야 한다.

## 8. 테스트 / 변경 파일 / 무결성

[tests.json](reports/tests.json): E2.1 신규26개 PASS, 기존 E2 36개 PASS, E1 21개 PASS, Fail/Error0. Hash·Time/Source mapping·Canonical link/schema·Frozen group/scene/near-duplicate/Team screen·unknown independence·Reviewer/Original provenance·disagreement·Finalize·media-change rejection·model field 차단·Range/CSRF/블라인딩·빈 Queue·resume·A/B/C/D를 Synthetic fixture 및 로컬 HTTP로 검증했다. Synthetic를 실제 Human GT 결과로 보고하지 않는다.

기존 E1/E2/P0 code/config/Frozen GT/Split/triage Results/P4 code 등 보호 대상의 byte hash 비교가 동일했고 기존 Git tracked 수정도 없다. 새 파일은 **experiments/stage1_dev_e21/**에만 작성했다. 백엔드 계약·연동 작업·mock CCTV 서버 파일을 수정하지 않았다.

| 신규 파일/영역 | 목적 |
|---|---|
| `src/dev_common.py`, `media_integrity.py`, `review_store.py` | E21 한정 atomic artifact, 영상/중복/연결 검증, Human 기록·상태·GT Gate |
| `scripts/acquire_assist.py`, `build_pool.py`, `build_cv.py` | 제한적 공식 Source 수집·checksum, 비중복 Candidate, 기존 P0 재사용 |
| `scripts/serve_review.py`, `prepare_dataset.py`, `validate_all.py` | local Human UI, source curation/export/E2 prep, 회귀/무결성 검증 |
| `review/index.html` | blinded 영상 재생·Label/태그·Reviewer·disagreement/Finalize UI |
| `tests/test_e21.py` | 자동화 integrity/GT/HTTP/E2 integration tests |
| `data/*` | Source audit/Pool/GT schemas, license/notes, 역사 fingerprint, 빈 GT Manifest, Development group registry, protocol/policy notes |
| `reports/*` | Source/Raw inventory, actual CV 품질·readiness·ABCD alignment·tests |
| `media/`, `data/canonical/`, `data/prepared/` | 실제 영상·CV·offline 입력. Git 제외, 로컬 artifact로 보존 |
| `.gitignore`, `README.md` | 대용량/중간 artifact 제외 및 한국어 인계 |

개발 완료와 데이터 연구 완료는 구분한다. 다음 Human 작업은 독립성 확인, 실제 Labeling/합의/Finalize, 여러 새로운 Source/Physical Group 확보다. 독립성이 입증되지 않은 후보나 소규모 단일 Collection을 근거로 안전한 Suppression을 주장하지 않는다.
