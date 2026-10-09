# 477 AI Evaluation Selection

사람이 최종 평가 영상을 고르기 위한 후보 탐색 pipeline이다. 모델을 학습하지 않고 최종 5개나 risk priority 정답을 확정하지 않는다.

## 데이터 위치

현재 실행 환경은 Windows이다. 요청한 `/mnt/d/projects/477`은 `D:/projects/477`에 대응한다. 실제 경로를 manifest와 리포트에 저장했다.

- Fight ZIP: `D:/projects/477/downloads/fight/19.이상행동CCTV/02.싸움(fight)/실내(원본)/insidedoor_04.zip`
- Swoon: `D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/extracted`
- Trespass: `D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/extracted`

## 실행 방법

기존 Python과 OpenCV, Pillow를 사용했다. 이 실행에서는 패키지를 설치하지 않았다. ffprobe/ffmpeg는 PATH에 없으므로 OpenCV를 사용했다.

PowerShell 또는 CMD에서:

```powershell
cd D:/projects/477/evaluation_selection
python scripts/build_inventory.py
# dataset_structure.md 및 inventory_details.json을 먼저 확인
python scripts/select_candidates.py
python scripts/extract_contact_sheets.py
python scripts/review_alternate_views.py
python scripts/build_report.py
python scripts/validate_outputs.py
```

`inspect_dataset.py`도 동일 구조 조사 기능을 실행한다. 스크립트는 스크립트 위치에서 출력 루트를 계산하므로 실행 cwd에 영향을 받지 않는다. Linux에서 이 폴더를 `/mnt/d/projects/477/evaluation_selection`으로 열면 데이터 경로가 해당 mount 기준으로 재생성된다. Pillow font는 Windows Consolas를 사용하며 Linux에서는 기본 font를 사용한다.

pipeline에는 자동화할 수 없는 영상 해석 판단이 있다. `select_candidates.py`의 SPECS는 XML 행동 구간과 source ID/카메라/계절 다양성을 고려한 검토 표본을 고정한다. `review_alternate_views.py`는 차량 가림과 pairing 의심을 조사하기 위한 추가 Swoon 9개를 만든다. `review_decisions.json`에 시간순 sheet 검토로 얻은 점수·문장 근거·제외·scenario 연결을 저장하고, 재실행에서는 이를 재사용한다. 새로운 데이터를 넣으면 검토자가 이 파일을 갱신해야 한다. 재실행이 새로운 시각적 판단을 자동 생성하는 것은 아니다.

Fight 기존 임시 파일은 파일 크기를 확인하여 재사용한다. 자동 삭제하지 않는다. 기존 alternate view metadata/시트는 재사용한다. 다시 생성하려면 `python scripts/review_alternate_views.py --refresh`를 실행한다. 원본 pairing 변경이나 시간 오프셋 보정은 수행하지 않는다.

## 생성 파일

- `dataset_structure.md`: pairing, XML topology, label/action/frame/keypoint 구조와 제한사항.
- `dataset_inventory.csv`, `inventory_details.json`: 전체 118개 영상 목록, 파일 크기, XML 메타데이터, decoder 대조 값 및 원본 XML tree/hash.
- `zip_listing.json`: ZIP member/size/compressed size/CRC. 전체 압축 해제 없음.
- `candidates.csv`, `candidates.json`: 25개 scenario 항목, 실제 22개 서로 다른 영상. CSV에도 각 기준 이유 컬럼을 추가했다.
- `candidate_report.md`: 후보별 원본/실제 재생 절대경로, 근거, 점수, sheet, 조합 및 제한사항.
- `contact_sheets/`: 검토 표본 30개 각각 9장 사건 시트와 24장 temporal 시트. CSV 후보는 해당 시트를 참조한다. D는 기존 표본을 재사용하며 source_candidate_id로 추적한다.
- `review_decisions.json`: 선정 판단. AI Hub 정답과 분리.
- `source_annotation_facts.json`: 전체 원본 annotation 사실 및 tree/hash. semantic pairing이 의심되는 파일도 출처 사실로만 보존한다. `ground_truth.json`을 새로 만들지 않았다.
- `ranking_combinations.json`: 3개 가상 동시 발생 조합과 약 35초 seek 구간. priority_ground_truth는 null.
- `excluded_review.json`: 주간 annotation과 야간 영상이 맞지 않아 제외된 Swoon 7개. 품질이 나쁜 Hard Case로 대신 쓰지 않았다.
- `data_issues.json`: XML/영상 길이 차이.
- `temporary_files.json`: Fight 선택 추출 파일 12개(영상 6 + XML 6)의 절대경로와 byte. 삭제 가능 여부 검토용이며 자동 삭제하지 않는다.
- `capacity_check.json`, `storage_summary.json`, `validation_result.json`: 공간 확인 및 결과 검증.

## 후보 선정 기준과 점수

UNDERSTAND / TEMPORAL / REASONING / UNCERTAINTY / ATTENTION의 서로 다른 질문을 만들 수 있도록 후보를 구성했다. A는 보이는 신체 충돌, B는 보행→넘어짐→낮은 움직임, C는 접근·조작·경계 이동, D는 거리·가림·짧은 동작·맥락 부족, E는 사건 종류가 다른 세 모니터를 비교한다.

event_visibility, event_clarity, temporal_value, visual_quality, reasoning_value, demo_suitability: 1 낮음, 3 보통/제한 존재, 5 매우 높음. ambiguity: 1 매우 명확, 3 일부 맥락 필요, 5 매우 애매. A/B는 낮은 ambiguity를 우선하고 D는 높은 ambiguity를 검토 가치로 사용한다. 모든 점수는 리뷰 판단이며 정답, severity, risk, priority, 모델 confidence가 아니다. 각 점수 문장 이유는 CSV/JSON/리포트에 보존한다. 수치 종합순위는 만들지 않고 시나리오 적합성으로 Top 3 검토 순서를 제안했다.

## 원본 데이터 보호 정책

원본 영상·ZIP·XML을 읽기만 한다. 이름 변경/수정/이동/삭제를 수행하지 않는다. 새 산출물과 임시 Fight 추출 파일은 evaluation_selection 아래에만 쓴다. Swoon/Trespass 원본 영상은 복사하지 않는다. ZIP 54개 영상 중 6개만 원래 member 이름을 유지하여 tmp/fight에 추출한다. 전체 frame dump나 최종 Evaluation Set 복사/확정은 하지 않는다. 원본을 향하는 쓰기 모드와 자동 삭제 코드는 없다.

대용량 생성 전 `shutil.disk_usage`로 D: 여유 공간 및 계획 추출 byte를 확인한다. 이는 Windows에서 `df -h /mnt/d/projects/477`에 대응하며 WSL이 접근 제한되어 Linux 명령은 실행되지 않았다. 공간이 필요한 byte + 2 GiB보다 작으면 중단한다.

## 알려진 제한사항

- Fight는 검토한 모든 표본이 녹색 스튜디오이다. 실제 현장 CCTV 환경 대표성은 제한된다.
- Clear Swoon 6개 중 4개는 상대적으로 명확하고 S02/S04 2개는 차량 가림 때문에 조건부 후순위다. B Top 3는 이 조건부 표본을 제외한다.
- 일부 Swoon filename/XML은 day지만 실제 영상은 night이다. 해당 7개는 source pairing/content 검증이 필요하여 후보에서 제외했다. 원인이 복구 오류인지 확정하지 않는다.
- 11개 Swoon에서 XML과 decoder duration 차이가 있다. 시간 오프셋을 임의 생성하거나 XML을 고치지 않았다.
- 모든 118개 XML을 조사했지만 영상 시각 검토는 30개, Fight 실제 metadata 확인은 6개에 한정된다. 나머지 Fight 48개 metadata는 XML 값이다. 전체 품질 상위 후보라고 주장하지 않는다.
- 9+24장 시퀀스로 시간 흐름을 확인했으며 영상 전체 연속 재생이나 완전한 무동작 측정을 하지 않았다. 사용자는 최종 선정 시 실제 구간을 재생해야 한다.
- XML keypoint는 bbox가 아니다. 제한구역 polygon과 출입 권한도 없다. 담장/대문 경계 통과와 불법 침입 판정은 구분해야 한다.
- Source frame indexing은 미확인, sheet frame은 decoder 0-based이다. 경계에서 한 frame 수준 차이가 있을 수 있다.
- 일부 Fight XML 종료 뒤에도 화면 접촉이 남는다. AFTER는 XML 구간 이후라는 뜻이며 사건이 실제 완전히 끝났다는 판단이 아니다.
- person counts/접촉/낮은 움직임/경계 통과는 표본 프레임 관찰이다. source 사실 파일과 분리되어 있고 unknown은 null이다.
- 같은 ID/카메라/계절 및 scenario 간 중복이 있다. 25개 항목은 25개 독립 사건이 아니다.
- D는 positive hard case이다. 정상 negative가 없으므로 false-positive rate 자체를 추정할 수 없다.
- Ranking은 가상 동시 발생이며 현재 제안 구간만 존재한다. 클립을 생성하지 않았다. 위험 순위의 평가 기준은 사용자가 나중에 정의해야 한다.
