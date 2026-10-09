# Grading Guide — 477 Blind Human Grading (System A / System B)

이 문서는 모든 ITEM에 공통으로 적용되는 채점 기준입니다. ITEM별 구체 기준은 `grading_reference.md`와 Review UI의 "자세한 기준 펼치기"에 있습니다.

**Claude/자동 도구는 점수를 매기지 않았습니다. 모든 점수는 reviewer가 직접 선택합니다.**

## 0. 채점 절차 (assessment 1개당)

1. ITEM 화면에서 CCTV 영상을 처음부터 끝까지 재생합니다 (필요하면 여러 번, seek 사용).
2. Reviewer Reference를 읽습니다. 초록 박스 = **OBSERVABLE REFERENCE**(영상에서 확인되는 사실), 주황 박스 = **MUST REMAIN UNCERTAIN**(영상만으로 확정할 수 없는 것).
3. System A의 prediction을 읽습니다 (Event → Incident? → Risk → Confidence → Temporal summary → Evidence → Reason → Uncertainties → Human Review).
4. 4개 metric을 **각각 독립적으로** 0/1/2 중에서 선택합니다. 고민되면 "자세한 기준 펼치기"를 엽니다.
5. 근거 없는 단정이 있으면 Overclaim flag를 추가하고 출력의 **정확한 인용문**과 **이유**를 적습니다.
6. 두 확인 checkbox(실제 영상 확인 / evidence와 영상 비교)를 체크하고 Submit 합니다.
7. 그 다음 System B가 열립니다. 같은 방식으로 채점합니다 (A 점수는 보이지 않습니다).
8. 모두 끝나면 Export grading JSON → `grades/<reviewer_id>.json`로 저장(또는 Save to server).

## 1. 공통 원칙

- 네 metric은 서로 독립적으로 채점합니다. 사건 라벨이 틀렸다고 Evidence Grounding이 자동으로 0점이 되지 않습니다.
- 채점 기준은 '영상에서 실제로 보이는 사실'과 이 pack의 Reviewer Reference입니다. AI Hub source label(예: swoon, trespass, fight)은 참고 맥락일 뿐 정답이 아닙니다. 'source label과 같은 단어를 썼으니 2점'처럼 채점하지 마세요.
- source label 때문에 의학적 상태(실신 등), 의도, 권한(무단 여부), 신원을 사실로 확정하지 마세요. 이것들은 영상으로 확정되지 않는 항목입니다.
- prediction의 confidence 값이 높다고 점수를 올리지 마세요. 틀린 내용에 높은 confidence를 줬다면 note에 기록하세요.
- human_review_required (true/false)는 채점 대상이 아닙니다. 어느 값이든 rubric 점수를 올리거나 내리지 마세요.
- risk 숫자(severity/imminence/exposure/persistence)에는 정답 숫자가 없습니다. 숫자 자체를 맞다/틀리다로 채점하지 말고, 그 숫자가 사건 이해나 불확실성 표현과 심하게 모순될 때만 해당 metric note에 기록하세요.
- 'possible', 'may', 'likely' 같은 단어를 썼다고 자동으로 Uncertainty 2점이 아닙니다. 관찰 사실과 해석이 실제로 분리되어 있는지를 보세요.
- 시스템은 영상 전체가 아니라 균일하게 뽑은 소수 frame(단일 카메라 64장 ≈ 0.55초 간격, SET04는 카메라당 21~22장 ≈ 1.7초 간격, SET05 AB는 카메라당 32장 ≈ 1초 간격)만 봤습니다. 프레임 사이의 짧은 동작을 놓친 것은 '누락'으로 보되, 영상과 '모순'되는 주장과는 구분하세요.
- timestamp가 reference와 약 3초 이내로 다른 것은 감점 사유가 아닙니다(sampling 간격 고려). 사건 순서가 뒤바뀌거나 전혀 다른 구간을 가리키면 감점합니다.
- System A와 System B를 비교해서 상대평가하지 마세요. 각 prediction을 이 기준에 대해 절대평가합니다. 어느 시스템인지 추측하지 마세요.

## 2. 출처 표시(provenance) 읽는 법

| 태그 | 의미 |
|---|---|
| `HV` | human_verified_observation — 사람이 원본 영상으로 확인한 사실 |
| `PR` | project_defined_reference — 477 프로젝트 정의 reference / expected uncertainty |
| `CS` | project clip-selection 기록 (SET03) |
| `SA` | AI Hub source annotation (source label/XML/caption) — **참고 맥락이며 정답 아님** |
| `DER` | SA/CS 시각을 clip 상대시간으로 산술 환산한 근사치 (프레임 규약 미검증; 영상으로 확인) |

## 3. Metric별 0/1/2 기준

> **Score this dimension independently. A wrong event label does not automatically mean evidence grounding is 0.**

### Event Understanding (사건 이해)

**질문:** 시스템이 이 장면에서 실제로 일어난 핵심 사건 또는 상태를 올바르게 이해했는가?

| 점수 | 한 줄 요약 |
|---|---|
| 2 | 핵심 observable 사건/상태를 정확히 파악, 모순·과장 없음 |
| 1 | 일부만 맞거나 지나치게 일반적, 핵심 행동/관계 누락 |
| 0 | 다른 사건으로 해석, 핵심 사건 부재로 판단, 또는 반대/환각 |

**① 2점을 주는 최소 조건**

아래를 모두 만족해야 2점입니다.
- 장면의 핵심 observable 사건/상태(이 case의 Reviewer Reference '핵심 observable 사건')를 실질적으로 정확하게 말한다.
- 사건 참여자 또는 중요한 행동을 큰 의미 왜곡 없이 설명한다(예: 몇 명이 무엇을 했는지).
- 핵심 사건과 모순되는 주장을 하지 않는다(예: 같은 출력 안에서 '사건 없음'과 '넘어짐'을 동시에 결론으로 내세우지 않음).
- 관찰로 뒷받침되지 않는 더 강한 의미(실신, 범죄, 무단침입 확정 등)를 사건 정의로 붙이지 않는다.
- source class 이름과 똑같을 필요는 없다. 사실이 정확하면 된다 [PR rubric anchor].

**② 1점을 주는 상황**

- 장면의 일부는 맞지만 사건의 핵심 의미를 충분히 파악하지 못했다.
- 'person movement observed', 'activity detected'처럼 지나치게 일반적인 표현만 있고 영상에는 더 구체적인 핵심 행동이 분명하다.
- 핵심 사건의 일부만 잡았다(예: 바닥 자세는 말하지만 넘어짐은 말하지 않음 / 사람이 이동했다고만 하고 담을 넘은 것은 말하지 않음).
- 큰 방향은 맞지만 중요한 행동 또는 참여자 관계(두 사람 사이의 충돌 등)를 빠뜨렸다.
- 표현이 애매하거나 출력 내부가 서로 어긋나서, 사건을 이해했는지 읽는 사람이 확신할 수 없다.

**③ 0점을 주는 상황**

- 전혀 다른 사건으로 분류했다(예: 담을 넘는 장면을 넘어짐 사건으로 결론).
- 실제 핵심 사건이 있는데 '특별한 사건 없음/정상'으로 결론 내리고, 핵심 행동을 어디에서도 언급하지 않았다.
- 사건을 반대 의미로 해석했다.
- 주요 참여자나 행동을 완전히 잘못 이해했다.
- 핵심 사건을 영상에 없는 내용(환각)으로 대체했다.

**④ 흔히 헷갈리는 경계 사례**

- 출력 내부 모순: is_incident=false인데 event_type은 'possible fall'인 식의 모순이 있을 수 있습니다. category 단어만 보고 채점하지 말고, 출력 전체(event_type, observations, temporal_summary, reason)를 읽은 사람이 실제 사건을 올바르게 전달받는지로 판단하세요. 모순 때문에 사건 이해가 크게 흐려지면 1점, 결론이 실제 사건과 반대로 읽히면 0점입니다.
- 일반적 라벨 + 구체적 evidence: event_type은 일반적이지만 observations 문장에서 핵심 행동(예: 서 있다가 수평 자세로 바뀜)을 정확히 말한다면 1점 또는 2점까지 가능합니다. '사람이 읽고 핵심 사건을 알 수 있는가'가 기준입니다.
- 구체적 라벨 + 근거 없음: event_type은 맞는 범주인데 다른 문장이 그 사건과 무관하거나 모순되면 2점을 주지 마세요.
- 'uncertain'으로만 답한 경우: 핵심 사건을 전혀 서술하지 않았다면 0~1점입니다. 핵심 행동을 서술하고 결론만 유보했다면 1~2점이 가능합니다.

### Temporal Understanding (시간 흐름 이해)

**질문:** 시스템이 단순 정지 장면이 아니라 중요한 시간적 변화와 사건 순서를 이해했는가?

| 점수 | 한 줄 요약 |
|---|---|
| 2 | 핵심 before → transition → after 흐름과 지속 상태를 올바른 순서로 표현 |
| 1 | 변화 일부만 포착, 시작/끝 또는 지속성 누락 |
| 0 | 순서 반대, 핵심 변화 미인식, 없는 전후관계 생성 |

**① 2점을 주는 최소 조건**

- 이 case의 '핵심 temporal sequence'에서 before → transition → after를 올바른 순서로 표현한다.
- 핵심 순서가 뒤바뀌지 않는다.
- 사건 이후의 지속 상태가 중요한 case라면(예: 넘어진 뒤 계속 바닥에 있음) 그것도 포착한다.
- 영상에 없는 시간 관계를 만들어내지 않는다.
- 시각(timestamp)은 대략 맞으면 됩니다(약 3초 이내 차이는 감점하지 않음).

**② 1점을 주는 상황**

- 시간 변화의 일부는 잡았지만 시작 상태나 끝 상태 중 하나를 빠뜨렸다.
- 핵심 transition은 언급했지만 이후의 persistence(지속)를 놓쳤다(지속이 중요한 case에서).
- 전체 흐름은 불완전하지만 틀린 순서를 주장하지는 않는다.
- 거의 정지 장면처럼 묘사하지만 최소한 한 가지 실제 변화는 포착했다(예: '사람이 화면에 들어왔다').

**③ 0점을 주는 상황**

- 사건 순서를 뒤집었다(예: 바닥에 있다가 일어나서 걸어갔다).
- 실제 영상과 반대되는 시간 관계를 주장했다.
- 이 case의 핵심 transition을 전혀 인식하지 못했다(시간 서술은 있으나 핵심 변화와 무관).
- 존재하지 않는 전후 관계를 만들어냈다.
- temporal reasoning이 핵심인 case인데 정지 상태만, 그것도 잘못 설명했다.

**④ 흔히 헷갈리는 경계 사례**

- 'The person is lying down.'만 있는 경우: Event는 부분적으로 맞을 수 있지만, 서 있다가 바닥으로 가는 변화가 핵심인 case에서는 Temporal 1점 이하입니다.
- 시각 차이: 3초 이내 차이는 무시. 순서·변화·지속성이 맞는지가 핵심입니다.
- sampling 한계: frame 간격(0.5~1.7초) 때문에 transition 시점이 한 구간 앞뒤로 표시되는 것은 정상입니다.
- 시간 서술이 여러 필드에 흩어져 있을 수 있습니다(temporal_summary, observations의 timestamp, reason). 모두 읽고 판단하세요.

### Evidence Grounding (근거의 영상 일치)

**질문:** 시스템이 제시한 판단과 설명이 실제 영상에서 관찰 가능한 근거로 뒷받침되는가?

| 점수 | 한 줄 요약 |
|---|---|
| 2 | 주요 근거가 영상에서 확인되고 camera/time 귀속도 맞음 |
| 1 | 대부분 맞지만 일부 근거가 약하거나 사소한 오류 1건 |
| 0 | 핵심 근거가 영상에 없거나 환각/모순/카메라 오귀속 |

**① 2점을 주는 최소 조건**

- 판단의 주요 근거 문장(observations, evidence, reason의 사실 주장)이 실제 영상에서 확인된다.
- 근거와 설명이 서로 일치한다.
- camera attribution이 필요한 경우 올바른 camera를 가리킨다.
- timestamp가 있다면 대체로 맞는다(약 3초 이내).
- 핵심 이유가 구체적인 observable fact에 연결되어 있다(예: '서 있다가 수평 자세로 바뀜', '두 사람이 가까이 붙어 있음').

**② 1점을 주는 상황**

- 근거 대부분은 맞지만 일부 근거가 지나치게 약하거나 모호하다.
- 주요 판단 자체는 맞지만 근거가 너무 일반적이다(예: '사람이 감지됨' 수준).
- 사소한 unsupported claim이 하나 있지만 핵심 판단을 뒤집지는 않는다.
- timestamp나 camera attribution에 작은 오류가 있다.

**③ 0점을 주는 상황**

- 핵심 판단을 뒷받침하는 근거가 영상에 없다.
- 중요한 근거를 지어냈다(hallucination).
- 근거가 영상과 명백히 모순된다.
- 다른 camera의 근거를 잘못 귀속했다.
- 존재하지 않는 행동, 물체, 관계를 근거로 들었다.

**④ 흔히 헷갈리는 경계 사례**

- 라벨은 틀렸지만 근거 문장은 사실인 경우: 예) event_type은 'fall'인데 evidence는 '사람이 화면을 가로질러 이동' — Event는 낮게, Evidence는 그 문장이 영상과 맞는지로 따로 판단합니다. 다만 '핵심 판단을 뒷받침하는가'도 기준이므로, 사실 문장이 결론과 전혀 연결되지 않으면 1점이 상한일 수 있습니다.
- 자동 CV 수치(예: 'contact proxy 0.43', 'reliability 0.94'): 숫자 자체는 영상으로 검증할 수 없습니다. 그 수치가 가리키는 관찰(가까움, 자세 변화 등)이 영상과 맞는지로 판단하세요.
- 'T1', 'T2' 같은 track 이름은 자동 추적 ID입니다. 그 ID가 가리키는 사람의 행동이 영상과 맞는지 보세요.
- 근거가 '부족'한 것(누락)과 '틀린' 것(모순/환각)을 구분하세요. 누락은 보통 1점, 모순/환각은 0점 후보입니다.

### Uncertainty Handling (불확실성 처리)

**질문:** 시스템이 영상으로 알 수 있는 것과 알 수 없는 것을 적절히 구분하는가?

| 점수 | 한 줄 요약 |
|---|---|
| 2 | 확정 불가 항목을 unknown으로 남기고 관찰/해석을 분리 |
| 1 | 불확실성 일부 표현, 1~2문장 과단정 또는 중요한 unknown 누락 |
| 0 | 의학·의도·권한·신원·무기·카메라간 동일인 등을 근거 없이 단정 |

**① 2점을 주는 최소 조건**

- 영상으로 확정할 수 없는 내용(이 case의 'MUST REMAIN UNCERTAIN' 목록)을 unknown/uncertain으로 남긴다.
- observation(보이는 것)과 interpretation(해석)을 분리한다.
- 신뢰도가 낮은 CV 근거를 확정 사실로 바꾸지 않는다.
- 의학적 상태, 범죄 의도, 권한, 신원 등을 단정하지 않는다.
- multi-camera에서는 identity와 synchronization이 증명되지 않았음을 인정한다.

**② 1점을 주는 상황**

- 불확실성을 일부 표현하지만 한두 문장이 지나치게 단정적이거나 모호하다.
- 이 case에서 꼭 명시해야 할 중요한 unknown 하나를 누락했지만, 심각한 거짓 단정까지는 아니다.
- confidence와 risk를 약간 혼동한다(예: 확신이 낮다는 이유로 위험도 낮다고 서술).
- 사실과 추론이 섞여 있어 어디까지가 관찰인지 구분이 흐리다 [PR rubric anchor].

**③ 0점을 주는 상황**

아래와 같은 근거 없는 단정을 핵심 결론으로 사용하면 0점 후보입니다(영상/Reviewer Reference가 뒷받침하지 않는 경우).
- 'the person fainted', 'the person is unconscious', 'the person is injured' (의학적 진단/상태)
- 'this is a criminal', 'the person intended to trespass' (범죄 의도)
- 'the entry was unauthorized', 'illegal entry' (권한/법적 상태)
- 'CAM A and CAM B definitely show the same person' (카메라 간 동일인)
- 'a weapon is present' (무기)
- 또는 불확실성이 큰 장면을 매우 확정적으로 잘못 설명한 경우.

**④ 흔히 헷갈리는 경계 사례**

- 'possible/likely/may'를 썼다고 자동 2점이 아닙니다. 예) 'possible fall; the person is unconscious' → 앞부분은 유보적이어도 뒷부분이 진단 단정이므로 0~1점.
- unknown을 길게 나열했지만 정작 결론에서 그것을 무시하고 단정하면 2점이 아닙니다.
- 반대로, 모든 것을 'uncertain'으로만 덮어 관찰 사실조차 말하지 않는 것은 '관찰과 해석의 분리'가 아니므로 1점이 상한입니다.
- 같은 단정이 부정문 안에 있으면('authorization cannot be determined') 단정이 아닙니다. 문장 전체를 읽으세요.
- Overclaim flag는 이 metric과 별도로 체크합니다. flag를 체크했다면 보통 이 metric도 낮아지지만, 자동으로 연동되지는 않습니다.

## 4. Overclaim flags (점수와 별도)

flag를 추가할 때는 반드시 **exact_output_quote**(prediction에 실제로 있는 문장 그대로)와 **why_unsupported**(왜 영상이 뒷받침하지 않는지)를 적습니다. 키워드가 보인다고 자동으로 flag하지 마세요. 부정문("cannot be determined")은 단정이 아닙니다.

| flag | 의미 |
|---|---|
| `unsupported_medical_diagnosis` | 의학적 상태/원인을 근거 없이 단정 (실신, 의식 없음, 부상, 심장마비 등) |
| `unsupported_criminal_intent` | 범죄 의도/목적을 근거 없이 단정 (훔치려 함, 침입 의도 등) |
| `unsupported_authorization` | 출입 권한/불법 여부를 근거 없이 단정 (무단침입, 불법 출입, 허가된 출입 등) |
| `unsupported_identity` | 특정 신원/역할을 근거 없이 단정 (집주인, 거주자, 범인 등) |
| `unsupported_weapon` | 무기 존재/사용을 근거 없이 단정 |
| `unsupported_cross_camera_identity` | 두 카메라의 사람이 동일인이라고 근거 없이 단정 |

## 5. SET04 (ITEM_04) Attention Ranking

> **This ranking is a 477 project-defined human reference, not AI Hub ground truth.**

- Reference order: **CAM_01 > CAM_02 > CAM_03**
- Top-1 Correct: System의 attention_queue에서 rank 1 camera가 CAM_01이면 yes, 아니면 no.
- Full Order Correct: System의 rank 1,2,3 순서가 정확히 CAM_01 > CAM_02 > CAM_03이면 yes, 하나라도 다르면 no.
- Ranking 정답 여부와 4개 rubric 점수는 독립입니다. 순위가 맞아도 각 카메라 사건을 잘못 이해했다면 rubric은 낮게 줍니다.

4-metric 채점은 출력 전체에 대해 한 번 합니다. 카메라별 보조 판단 방법:

ITEM_04는 출력 전체(3개 camera assessment + queue reason)에 대해 metric별로 한 점수를 줍니다.
헷갈리지 않도록 먼저 카메라별로 single-case 기준(2/1/0)을 마음속으로(또는 UI의 보조 칸에) 매긴 뒤 합산하세요.
  - 세 카메라 합 5~6 → 2점 (모든 카메라 핵심을 잡았고, 부족한 카메라는 최대 1개·1점 수준)
  - 합 2~4 → 1점
  - 합 0~1 → 0점
단, Uncertainty Handling은 어느 한 카메라에서라도 핵심 결론으로 근거 없는 단정(진단·의도·권한·무기·신원)을 하면 합계와 관계없이 0점 후보입니다.
보조 칸 합계는 참고용이며 최종 점수는 reviewer가 직접 선택합니다.

## 6. SET05 (ITEM_05 / ITEM_06 / ITEM_07)

- ITEM_05 = CAM A only, ITEM_06 = CAM B only, ITEM_07 = CAM A + B. 세 조건 모두 각각 0–8점으로 독립 채점합니다.
- Multi-view Increment = ITEM_07 총점 − max(ITEM_05 총점, ITEM_06 총점). System별로 따로 계산되며 reveal 후 자동 계산됩니다. AB > A만으로는 성공이 아닙니다.
- **잘못된 비교:** AB > A → multi-view 성공. **올바른 비교:** AB > max(A, B). CAM B 단독이 이미 강할 수 있습니다.
- ITEM_07에는 별도의 qualitative 질문 3개가 있습니다 (main 0–8 점수와 별개):

  - **Did the second view add genuinely new useful evidence? (두 번째 시점이 실제로 새롭고 유용한 근거를 더했는가?)**
    - `yes`: 출력에 한 카메라에서만 보이는(또는 훨씬 잘 보이는) 구체적 사실이 정확하게 추가됨 (예: CAM_01이 가려진 구간의 상호작용, 한 사람의 낮은 자세, 이후 이동)
    - `partially`: 두 번째 시점의 기여를 추상적으로만 언급하거나(가시성 수치, '보완적') 일부만 정확함
    - `no`: 두 번째 시점의 고유 정보가 없거나, 추가 정보가 영상과 맞지 않음
  - **Did the prediction incorrectly assume camera synchronization? (카메라 동기화를 잘못 가정했는가?)**
    - `yes`: 두 clip의 시각을 같은 절대 시각으로 취급하거나 동시 발생을 정밀하게 단정함
    - `no`: 동기화를 가정하지 않거나 미확인임을 밝힘
  - **Did the prediction incorrectly assert cross-camera identity? (카메라 간 동일인을 잘못 단정했는가?)**
    - `yes`: 두 카메라의 사람이 확실히 같은 사람이라고 단정함
    - `no`: 동일인을 단정하지 않거나 미확인임을 밝힘

## 7. 하지 말아야 할 것

- System A/B가 어느 시스템인지 추측하거나 찾아보지 마세요 (`reveal_map_private.json`, `scripts/`, `output/`을 열지 마세요).
- 다른 reviewer의 grades 파일을 보지 마세요.
- confidence, human_review_required 값으로 점수를 조정하지 마세요.
- source label과 같은 단어를 썼다는 이유로 점수를 주지 마세요.
- 결과를 "정확도 %"로 부르지 마세요. 5개 case의 rubric 합계/평균만 보고합니다.
