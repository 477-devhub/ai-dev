# E2.1 Human Review Protocol

모든 Candidate는 UNREVIEWED이고 GT는 없다. Codex·원본 action label·파일명·CV·P1/P4 출력을 Human GT로 대체하지 않는다. Reviewer가 실제 영상과 원본 구간을 재생하고 저장한다. 현재 자료는 안전 매트 등을 사용하는 staged 연구 참고 영상이므로 실제 촬영에서 관찰한 사실과 그 사건이 실제 시설에서 의미하는 위험을 분리한다. 실제 사람인지·마네킹/연기 여부·관제 의미를 구분할 수 없으면 uncertainty에 기록하고 AMBIGUOUS도 사용할 수 있다.

1. 서로 다른 Reviewer ID(예 reviewer_01 / reviewer_02)로 각각 독립 검토한다. 첫 제출 이전에는 다른 Reviewer 답을 보지 않는다.
2. Candidate 전체와 원본 Candidate 구간, 필요한 앞뒤 문맥을 재생한다. Loop/원본 시작 버튼을 사용할 수 있다. 전체 재생 및 원본 확인 checkbox는 사람이 사실대로 체크한다. UI 재생 telemetry는 보조 기록이고 실제 인지나 전체 재생의 증명이 아니다.
3. CLEAR_NORMAL / HARD_NEGATIVE_NORMAL / ANCHORED_DANGER / AMBIGUOUS 중 선택하고 사실 및 관제 판단 근거를 작성한다. AMBIGUOUS에는 판단을 막는 이유를 필수로 남긴다. 경계 정책·권한을 모르면 임의 사건 GT를 부여하지 않는다.
4. 보조 태그는 원본 영상 관측과 Reviewer 해석을 별도 그룹으로 기록한다. Nullable boolean에서 미확인과 false를 구분한다. 인원 수가 불명확하면 공란이다. CV sample의 gap이 원본 영상의 실제 미관측과 같다고 간주하지 않는다.
5. 같은 Reviewer의 재저장은 append-only revision이며 2명 검토로 계산하지 않는다. 두 사람이 같은 Label이면 AGREEMENT_READY지만 자동 Finalize하지 않는다.
6. 두 Label이 다르면 DISAGREEMENT. 별도 제3 Human Adjudicator가 원본을 다시 보고 근거와 최종 Label을 저장하여 ADJUDICATED로 만든다. 근거 없는 다수결·모델 답으로 해결하지 않는다.
7. Human Finalizer가 명시적으로 Finalize한다. 기본은 두 명 합의 또는 Adjudication 필수다. 단일 Reviewer만 가능하면 명시적 single 체크로 FINALIZED할 수 있으나 `single_reviewer_explicit`로 표시되고 Export 기본값은 제외한다.
8. Label 저장/Finalize는 Review record만 갱신한다. Integrity/independence 검사 이후 `prepare_dataset.py export`를 실행해야 E2-compatible Manifest에 포함된다. 새 Label이 자동으로 유료 API에 전달되는 경로는 없다.

Source independence curation은 GT review와 별도다. 사람이 기존 triage/reasoning/team 영상·촬영 장소·세션·배우·같은 사건 관계를 확인하고 evidence를 기록한다. 현재 모든 Source는 INDEPENDENCE_UNVERIFIED다. Source 이름/Hash가 다르다는 이유로 확인 상태를 바꾸지 않는다. dHash screen은 near-duplicate 의심을 보류하는 보조 검사이며 같지 않음이 독립성 증명은 아니다.

60~100개 탐색 목표를 채우려면 여러 독립 촬영 장소/세션의 정상 보행·출입·작업·동행, 근접/굽힘/회복 Hard Negative, 실제 위험 및 불확실한 영상을 추가해야 한다. 현재 28개 파일은 28개 독립 사건이나 독립 위험 샘플로 주장하지 않는다. 이 Collection은 향후 Calibration/Independent Safety Test에 재사용하지 않도록 Development registry에 보존한다.
