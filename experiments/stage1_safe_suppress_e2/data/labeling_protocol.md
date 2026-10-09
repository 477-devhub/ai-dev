# E2 독립 Development Human Review Protocol

현재 적합 Human GT는 0개다. `human_review_queue.csv`는 기존 Pool 709개 구간의 **제외 감사용 Queue**이며 새 Development에 편입할 수 없다. `new_human_review_queue.csv`는 새 출처를 등록할 빈 Queue다. 기존 Frozen의 라벨을 복사하거나 빈 행을 Normal로 채우지 않는다.

1. 새로운 source를 수집하고 original video path/hash, camera scene, 실제 촬영 장소/배우/세션/동일 사건을 묶는 physical group을 기록한다. 다른 파일명·카메라·crop·시간 구간은 독립성 근거가 아니다.
2. `exclusion_registry.json`과 기존 reasoning/triage/team Frozen 사용 출처를 대조한다. source·scene·physical group·media hash 겹침, 또는 관계를 확인할 수 없으면 보류한다. Group 이름을 바꾸는 것은 독립성 확보가 아니다. 사람이 원본 장소/세션 정보를 확인하고 `independence.evidence`, reviewer, checked_at을 기록한다. `checked_datasets`에 `477-triage-normal-v1`, `477-reasoning-v1`, `new477-total64-v1`을 모두 기록한다.
3. Reviewer는 모델 출력·파일명의 action·원본 dataset label·CV 요약을 보지 않고 **실제 원본 영상의 전체 candidate window를 재생**한다. 자세 변화·위험·회복 시각을 확인하고 앞뒤 문맥이 필요한 경우 주변 구간도 본다. Sample contact sheet만으로 Human GT를 만들지 않는다.
4. CLEAR_NORMAL=명확한 일상 관측, HARD_NEGATIVE_NORMAL=위험처럼 보이나 원본 영상에서 정상 맥락을 확인, ANCHORED_DANGER=관제 필요 위험을 실제 영상에서 확인, AMBIGUOUS=가림·마지막 공백·품질·경계 의미 등으로 판단 불가. 불확실한 사례를 Normal에 강제로 포함하지 않는다.
5. Observable summary를 작성한다. 낮은 자세/회복/Unknown 구간, physical contact 관측과 단순 근접, 필요한 scene semantics를 사실과 해석으로 구분한다. Reviewer identity, timestamp, watched_full_window=true를 기록한다. 모델 score로 label을 대체하지 않는다.
6. 가능한 경우 두 명이 독립적으로 검토하고 disagreement는 합의 전까지 AMBIGUOUS 또는 보류로 둔다. 충분한 실제 정상 영상(보행/출입/작업/동행)도 수집한다. 기존 abnormal staging 영상의 전후 구간만 모으면 selection bias가 남는다.
7. CV 생성자는 동일한 canonical sampling으로 기존 P0만 실행하여 `cv_provenance`에 original hash/canonical hash/builder version을 남긴다. E2 모델 입력에는 GT·source name·group·human summary를 넣지 않는다.
8. 사람이 확인한 사실만 `development_manifest.json`에 등록한다. JSON Schema와 independence audit 통과 후 initial pilot은 2 candidates × 4 arms로 실행한다. 새 데이터의 모델 실패를 보고 라벨을 변경하지 않는다. Label correction은 원본 영상 근거와 version을 별도로 기록한다.

필수 사례: 안정적 보행/출입/일상 움직임, 앉기/웅크림/굽혔다가 회복, 인사·단순 근접·동행·청소/작업, fragmentation/jitter, 실제 쓰러짐/충돌/경계 위험, low 이후 관측 종료/occlusion/불량 영상/scene semantics 미확인. 모든 유형을 포함하는 것이 권장되지만 부족한 유형의 GT를 만들지 않는다.

독립 신규 샘플의 수집·라벨링은 아직 수행되지 않았다. Metadata 검사 통과는 실제 독립성과 Human 판단의 완전성을 자동 보장하지 않는다.
