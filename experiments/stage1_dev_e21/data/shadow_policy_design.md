# E2.1 Shadow Policy Interface — 설계만

기존 E2 baseline_guard / safe_guard_095 / safe_guard_099는 그대로 둔다. 기존 Safe guard는 Baseline의 부분집합이므로 Baseline에서 추가로 정상 후보를 제거할 수 없다는 구조적 한계가 있다.

후속 평가에는 safe-centered 진단을 별도 family로 두되 E2 Original/Safe 질문 요인과 CV v1/v2 요인을 유지한다. 입력 인터페이스는 `{answer_validity, common_decisions, safe_predicate, observation_sufficiency_evidence, unresolved_hazard_evidence, safety_veto_evidence, policy_version}`다. 출력은 `{shadow_eligible, veto_reasons, insufficient_evidence_reasons, policy_family, parameter_version}`의 내부 진단 artifact이며 외부 decision/action을 만들지 않는다.

Concept: Valid Answers AND Human/CV 근거 기준의 충분한 관측 AND 미해결 위험 없음 AND Safe Signal AND No Veto. 어떤 관측 threshold가 충분한지, safe predicate cutoff가 얼마인지, recovery/gap/scene-context의 veto 여부는 아직 정하지 않았다. 미보정 확률을 안전 보증으로 해석하지 않는다.

실험 순서: (1) 2×2 Arm의 Raw scores와 공통 답 변화, (2) 같은 답변에서 기존 guard 진단, (3) 같은 answers에 safe-centered family 적용, (4) CV veto 유무를 별도 policy factor로 비교. Safe question 효과와 Rule 효과를 하나의 개선률로 합치지 않는다. Answer missing/refusal/invalid은 eligible=false로 유지한다. Ambiguous는 Normal 분모에 포함하지 않는다.

Parameters는 새로운 Development에서만 탐색하고 채택은 새 Calibration 이후다. GT Danger false suppression과 source/physical group별 실패를 우선하며, 독립 Safety Test는 Development Source/Scene/Physical Group을 재사용하지 않는다. 이번 단계에서 실행 가능한 guard·운영 threshold·routing 코드를 구현하거나 API 실험하지 않았다.
