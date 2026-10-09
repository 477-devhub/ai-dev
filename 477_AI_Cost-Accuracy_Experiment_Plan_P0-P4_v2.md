# 477 AI Cost–Accuracy Experiment Plan — P0 to P4 (v2)

> Updated: 2026-10-07  
> Benchmark: `477-reasoning-v1`  
> Goal: **Accuracy × Latency × Cost**를 함께 최적화해, 477개의 CCTV를 모두 고비용 VLM으로 분석하지 않고도 실제 운영 가능한 안전 관제 AI 구조를 찾는다.

---

## 1. 프로젝트 목표

477 AI의 목표는 단순히 가장 정확한 AI 모델을 사용하는 것이 아니다.

> **다수의 CCTV 환경에서 위험 사건을 빠르고 정확하게 판단하면서, 실제 운영 가능한 수준으로 추론 비용을 최소화하는 것**

따라서 모델 선택 기준은 Accuracy 하나가 아니라 다음 세 요소의 균형이다.

**Accuracy × Latency × Cost**

최종적으로는 모든 CCTV 영상을 고비용 VLM에 지속적으로 입력하는 구조를 피하고,

1. 저비용 Computer Vision이 영상에서 관찰 가능한 사실을 추출하고,
2. 빠른 Decision Layer가 대부분의 사건을 판단하며,
3. 위험도가 높거나 불확실성이 큰 일부 사건만 강한 Vision Reasoning 모델로 escalation

하는 **Cascade Architecture**를 목표로 한다.

---

## 2. 현재 Benchmark

현재 다음 Benchmark가 고정되어 있다.

**Benchmark:** `477-reasoning-v1`

이 Benchmark는 Candidate Detector 자체를 평가하는 것이 아니라, 후보 사건이 이미 선정된 이후의 **Stage 2 — AI Reasoning / Attention Orchestration** 능력을 비교한다.

| Set | 상황 | 핵심 평가 능력 |
|---|---|---|
| SET01 | Swoon | Temporal Understanding / Persistence |
| SET02 | Clear Trespass | Event Understanding |
| SET03 | Ambiguous Trespass | Uncertainty / Overclaim 방지 |
| SET04 | Swoon + Fight + Trespass | Attention Ranking |
| SET05 | Multi-camera Fight | Multi-view Reasoning |

SET05는 `CAM A`, `CAM B`, `CAM A+B` 세 조건으로 실행되므로 전체 실행 조건은 총 7개이다.

### Fixed Input Protocol

`uniform_total64_v1`

- Single-camera: 64 frames
- Multi-camera AB: 32 + 32 frames
- Attention Ranking: 22 + 21 + 21 frames
- 모든 Pipeline은 동일한 canonical frame budget을 사용
- P0~P3은 해당 frame으로부터 만들어진 동일한 CV State를 사용
- P4는 동일 canonical RGB frames를 직접 시각 입력으로 사용

이 규칙은 특정 Pipeline이 더 많은 시각 정보를 받아 성능을 높이는 것을 막기 위한 통제 조건이다.

---

## 3. 현재 진행 상태

```text
Dataset 후보 선정                DONE
사람의 원본 영상 검수             DONE
477-reasoning-v1 Freeze          DONE
P0 Shared Cheap CV              DONE
P1~P4                           TODO
```

### P0 완료 결과 요약

P0에서 다음 Shared Cheap CV Layer가 구현되었다.

- YOLO26n-pose
- person detection
- pose / posture proxies
- timestamp-aware sparse tracking
- temporal motion features
- pairwise proximity / interaction features
- low posture / vertical transition
- scene entry/exit observations
- CV reliability
- multi-camera visibility complementarity

그리고 이를 기반으로 모델 독립적인:

**`Canonical CV State v1`**

이 완성되었다.

P0의 deterministic rule은 fall / physical conflict를 직접 정확히 판단하는 데 한계를 보였지만, 다음과 같은 핵심 관찰 정보 자체는 성공적으로 추출했다.

```text
Swoon
→ standing → horizontal transition
→ prolonged low/horizontal posture

Fight
→ close proximity
→ relative motion
→ arm-extension / interaction proxies

Trespass
→ movement / scene entry
→ boundary semantics는 generic CV만으로 확인 불가

Multi-camera
→ visibility complementarity
→ 한 시점의 가림을 다른 시점이 보완하는 정보
```

따라서 P0의 핵심 결론은 다음과 같다.

> **Cheap CV는 “무슨 일이 관찰되었는가”를 비교적 잘 표현하지만, 그 관찰을 안전 사건의 의미로 해석하는 단계가 필요하다.**

이에 따라 P1부터는 `Canonical CV State`를 수정하지 않고 공통 입력으로 사용한다.

---

## 4. 전체 실험 질문

이번 실험의 핵심 질문은 다음과 같다.

> **“477 AI가 요구하는 판단 품질을 만족하면서 가장 싸고 빠르게 실행할 수 있는 구조는 무엇인가?”**

이를 위해 v2에서는 다음 다섯 Pipeline을 비교한다.

```text
P0  CV State → Rules

P1  CV State → OpenAI Decisions API (GPT-6 Luna)

P2  CV State → Clef-Flash

P3  CV State → GPT-6.1 Sol

P4  Canonical Frames → GPT-6.1 Sol Vision
```

### 변경 이유

기존 계획은:

```text
P1 Clef-Flash
P2 Jev
P3 Clef
P4 Strong VLM
```

이었다.

v2에서는 OpenAI Decisions API를 P1에 배치하고, P3/P4에 동일한 GPT-6.1 Sol을 사용한다.

이렇게 하면 다음 통제 실험이 가능하다.

```text
P1 vs P2
→ Decision API architecture 비교

P1/P2 vs P3
→ Cheap Decision Layer와 Strong Reasoning Model 비교

P3 vs P4
→ 모델은 동일(GPT-6.1 Sol)
→ 입력만 CV State vs Visual Frames
→ CV State 압축으로 잃는 정보량을 직접 측정
```

즉 모델 차이와 입력 정보 차이를 분리할 수 있다.

---

## 5. 전체 Architecture

```text
477-reasoning-v1
        │
        ▼
Canonical RGB Frames
        │
        ├───────────────────────────────┐
        │                               │
        ▼                               ▼
Shared Cheap CV                    P4 GPT-6.1 Sol
        │                          Direct Vision
        ▼                               │
Canonical CV State                     │
        │                               │
        ▼                               │
Compact Decision State                 │
        │                               │
        ├── P0 Rules                    │
        ├── P1 Decisions API            │
        ├── P2 Clef-Flash               │
        └── P3 GPT-6.1 Sol              │
                                        │
                ────────────────────────┘
                         │
                         ▼
                Common 477 Prediction
```

---

# 6. Shared Cheap CV Layer

P0에서 구현한 `Canonical CV State v1`을 P1/P2/P3에서 그대로 사용한다.

## 6.1 관찰 영역

### Object / Person

- person count
- bounding boxes
- track IDs
- visibility
- track reliability
- appearance / disappearance

### Motion

- normalized speed
- displacement
- direction change
- low sampled motion
- motion peaks

### Spatial Relationship

- person-to-person distance
- close proximity duration
- approach patterns
- bbox overlap
- interaction proxies

### Pose / Posture

- standing
- crouched
- low posture
- horizontal
- vertical transition
- posture timeline

### Temporal Features

- transition duration
- low posture duration
- persistence
- sampled temporal pattern

### Scene / Quality

- frame entry / exit
- occlusion proxy
- detection dropout
- CV reliability
- unavailable boundary semantics → `null`

### Multi-camera

- temporal pattern similarity
- visibility complementarity
- camera visibility drop/gain
- incident-signature similarity
- sync/identity는 확인되지 않으면 `false`

---

# 7. Compact Decision State

P1/P2/P3에는 Canonical CV State 전체의 raw frame-level observation을 그대로 보내지 않는다.

다음 형태의 **Compact Decision State**를 공통으로 만든다.

```text
Canonical CV State
        ↓
Fixed Serializer
        ↓
Compact Decision State
```

목적은:

- API input token 최소화
- provider별 입력 차이 최소화
- 동일한 의미 정보로 공정한 비교
- raw tracking noise 감소

예시:

```json
{
  "window_sec": 35,
  "cv_reliability": 0.82,
  "persons": 1,
  "tracks": [
    {
      "initial_posture": "standing",
      "final_posture": "horizontal",
      "upright_to_low_transition": true,
      "transition_confidence": 0.84,
      "post_low_posture_sec": 26.0
    }
  ],
  "interactions": [],
  "scene": {
    "entry_observed": true,
    "boundary_semantics_available": false
  }
}
```

### Freeze 원칙

Compact Decision State serializer를 P1 실행 전에 고정한다.

이후 P1/P2/P3에서:

- 같은 State
- 같은 의미의 질문
- 같은 Risk 정의
- 같은 Confidence 처리

를 사용한다.

---

# 8. P0 — CV-only Baseline

## 목적

AI reasoning model 없이 CV + deterministic rule만으로 어디까지 가능한지 측정한다.

P0는 **최저 비용 기준선(Floor)** 이다.

## 구조

```text
Canonical Frames
      ↓
Shared Cheap CV
      ↓
Canonical CV State
      ↓
Rules / Thresholds
      ↓
477 Prediction
```

## 상태

**COMPLETE**

## 관찰된 한계

### Fall

CV State는 standing → horizontal 변화를 잡았지만 fixed threshold 때문에 `possible fall` rule은 발화하지 않았다.

### Physical Conflict

proximity와 interaction proxy는 측정했지만 sparse sampling에서 deterministic contact threshold가 충분히 높지 않았다.

### Boundary Semantics

generic CV는 gate / wall / authorization 의미를 알 수 없다.

### Multi-camera

visibility complementarity는 표현 가능하지만 `same_incident` 판단은 약한 evidence였다.

## P0의 역할

P0는 실패한 baseline이 아니라 다음을 보여주는 기준점이다.

> **관찰(Perception)은 Cheap CV로 가능하지만 의미 해석(Decision)은 별도 계층이 필요하다.**

---

# 9. P1 — CV State → OpenAI Decisions API

## 목적

**477의 실제 Default Decision Layer 후보를 검증한다.**

Decisions API는 OpenAI가 2026-10-06 beta로 공개한 decision 전용 endpoint이며 현재 `gpt-6-luna`를 사용한다.

일반적인 자유형 문장 생성 대신 evidence에 대해 typed answer를 반환한다.

지원할 수 있는 대표 질문 구조:

```text
predicate
choice
score
```

따라서 477의 다음 문제와 직접 대응한다.

```text
incident인가?
→ predicate

어떤 incident인가?
→ choice

severity는 어느 수준인가?
→ score

imminence는?
→ score

human review가 필요한가?
→ predicate
```

## 구조

```text
Canonical Frames
      ↓
Shared Cheap CV
      ↓
Canonical CV State
      ↓
Compact Decision State
      ↓
OpenAI Decisions API
GPT-6 Luna
      ↓
Typed Decision + Probability
      ↓
477 Prediction
```

## 주요 Decision

```text
incident_type

incident_probability

severity

imminence

exposure

persistence

requires_human_review
```

## 설명 생성

Decisions API가 자유형 설명을 길게 생성하도록 하지 않는다.

```text
CV State
→ Evidence

Decisions API
→ Decision / Probability

Template
→ Explanation
```

예:

```text
Why this alert?

• Standing → horizontal transition observed
• Low posture persisted for approximately 26 seconds
• Decision confidence: 0.91
```

## 핵심 질문

> **P0가 추출한 동일 관찰 정보를 Decisions API가 rule threshold보다 더 정확하게 해석할 수 있는가?**

## 제품 관점

현재 가장 유력한 default Decision Layer 후보이다.

---

# 10. P0.5 — Decisions API Integration Smoke Test

P0.5는 별도 Benchmark Pipeline으로 점수화하지 않는다.

P1 전체 실행 전 integration 검증 단계다.

ITEM 하나를 사용하여 다음만 확인한다.

```text
API authentication
request schema
typed answer parsing
probability output
usage information
latency
retry / timeout
result-schema mapping
```

성공 후 P1 전체 7 conditions를 실행한다.

---

# 11. P2 — CV State → Clef-Flash

## 목적

OpenAI Decisions API와 **외부 specialized Decision Model**을 동일 State에서 비교한다.

## 구조

```text
Canonical Frames
      ↓
Shared Cheap CV
      ↓
Canonical CV State
      ↓
동일 Compact Decision State
      ↓
Clef-Flash
      ↓
477 Prediction
```

## 통제 조건

P1과 동일하게 유지한다.

```text
Same Frames
Same CV
Same Canonical State
Same Compact State
Same Decision Semantics

OpenAI Decisions API
vs
Clef-Flash
```

## 핵심 질문

> **Clef-Flash가 Decisions API보다 더 좋은 Cost–Accuracy–Latency 지점을 제공하는가?**

## 역할

**External Cheap Decision Baseline**

---

# 12. P3 — CV State → GPT-6.1 Sol

## 목적

CV State 기반 architecture에서 **강한 reasoning model을 사용했을 때의 상한**을 측정한다.

## 구조

```text
Canonical Frames
      ↓
Shared Cheap CV
      ↓
Canonical CV State
      ↓
동일 Compact Decision State
      ↓
GPT-6.1 Sol
      ↓
477 Prediction
```

## P1/P2와의 의미

```text
P1 / P2
→ cheap specialized decision

P3
→ strong general reasoning
```

따라서:

> **Structured State만 충분하다면 강한 reasoning model이 얼마만큼 추가 성능을 제공하는가?**

를 확인한다.

## 중요한 역할

P3는 P4와 **동일 모델**을 사용한다.

이것이 v2 설계의 핵심 통제 변수다.

---

# 13. P4 — Canonical Frames → GPT-6.1 Sol Vision

## 목적

**Direct visual reasoning의 성능 Upper Bound**를 측정한다.

## 구조

```text
Canonical 64 RGB Frames
        ↓
GPT-6.1 Sol Vision
        ↓
477 Prediction
```

GPT-6.1 Sol은 image input을 지원하므로, native video를 보내는 것이 아니라 Benchmark에서 이미 고정한 canonical frame protocol을 그대로 사용한다.

## 핵심 질문

> **Cheap CV State로 영상을 압축하지 않고 visual information을 직접 보여주면 얼마나 더 좋아지는가?**

---

# 14. P3 vs P4 — 가장 중요한 Controlled Experiment

```text
                 GPT-6.1 Sol
                      │
          ┌───────────┴───────────┐
          │                       │
    Compact CV State        Canonical Frames
          │                       │
          ▼                       ▼
         P3                      P4
```

모델은 동일하다.

달라지는 것은 입력 표현뿐이다.

따라서:

```text
P4 Score - P3 Score
```

는 대략적으로:

> **CV-based information compression으로 인해 손실되는 visual reasoning value**

를 보여준다.

이는 기존 설계보다 훨씬 명확한 통제 실험이다.

---

# 15. 공통 출력

P0~P4 모두 기존 `prediction.schema.json`과 호환되는 동일한 477 Prediction으로 변환한다.

```text
P0 ─┐
P1 ─┤
P2 ─┤
P3 ─┤──→ Common 477 Prediction JSON
P4 ─┘
```

내부 모델 API의 출력 형식 차이가 evaluator에 영향을 주지 않도록 한다.

---

# 16. 공통 Decision Semantics

P1~P3에서 semantic task definition을 최대한 동일하게 유지한다.

예:

```text
incident_type
normal / fall_like / physical_conflict / scene_entry / uncertain

severity
0.0 ~ 1.0

imminence
0.0 ~ 1.0

exposure
0.0 ~ 1.0

persistence
0.0 ~ 1.0

human_review_required
true / false
```

provider API 형식은 달라도 질문의 의미는 동일하게 유지한다.

---

# 17. Quality 평가

각 Scenario는 기존 human rubric을 그대로 사용한다.

각 항목 0~2점.

### Event Understanding

사건의 핵심을 올바르게 이해했는가?

### Temporal Understanding

시간 흐름과 전후 관계를 이해했는가?

### Evidence Grounding

실제 영상 또는 CV evidence와 일치하는 근거를 사용했는가?

### Uncertainty

관찰할 수 없는 내용을 함부로 단정하지 않았는가?

총:

```text
0 ~ 8
```

5개 selected scenario의 결과를 일반화된 percent accuracy로 표현하지 않는다.

---

# 18. Attention Ranking

SET04에서는:

```text
Swoon > Fight > Trespass
```

가 project-defined human reference다.

다음 두 값을 기록한다.

- Top-1 Correct
- Full Order Correct

### P1 Decisions API

각 사건별:

```text
severity
imminence
exposure
persistence
```

를 typed decision으로 구한 뒤, 미리 정의한 fixed formula로 priority를 계산한다.

권장:

```text
priority_score =
0.35 × severity
+ 0.30 × imminence
+ 0.20 × exposure
+ 0.15 × persistence
```

Confidence는 risk에 곱하지 않는다.

---

# 19. Multi-camera Reasoning

SET05:

```text
A
B
AB
```

세 조건을 평가한다.

핵심 metric:

```text
Multi-view Increment
=
Score(AB)
-
max(Score(A), Score(B))
```

AB가 A보다 좋기만 해서는 multi-view benefit이라고 하지 않는다.

**best single view보다 좋아야 한다.**

### Decision 질문 예

```text
same_incident
→ predicate

second_view_adds_information
→ predicate

additional_information_value
→ score
```

단 P1~P3에서는 영상이 아니라 CV State만 보기 때문에 이 결과는 CV가 제공한 cross-camera evidence의 품질에 제한된다.

---

# 20. Safety / Overclaim

다음 오류를 별도로 추적한다.

- unsupported medical diagnosis
- unsupported criminal intent
- unsupported authorization
- unsupported identity
- unsupported weapon
- unsupported cross-camera identity

예:

```text
관찰 가능:
“사람이 대문을 통해 안쪽으로 이동했다.”

관찰 불가능:
“범죄자가 불법 침입했다.”
```

P1 Decisions API가 probability를 높게 반환해도, evidence가 없는 법적/의학적 의미를 추가해서는 안 된다.

---

# 21. Latency 측정

모든 Pipeline에 대해 **End-to-End steady-state candidate latency**를 기록한다.

### P0

```text
canonical frame decode
+
CV inference
+
feature extraction
+
rule engine
```

### P1/P2/P3

```text
canonical frame decode
+
CV inference
+
Canonical State
+
Compact State serialization
+
network/API request
+
decision parsing
+
477 prediction conversion
```

### P4

```text
canonical frame decode
+
image serialization/upload
+
GPT-6.1 Sol inference
+
prediction parsing
```

일부 구간만 측정한 latency를 전체 latency와 비교하지 않는다.

### P0 latency 주의

P0 최초 실행은 노트북 배터리 환경에서 측정되었고 CPU/decode bottleneck이 확인되었다.

최종 P0~P4 비교 전:

```text
AC power
same performance mode
same warm state
same network condition where possible
```

로 다시 측정한다.

---

# 22. Cost 측정

Primary Metric:

```text
Cost per Candidate Incident
```

### P0

```text
External API Cost = $0
Local compute monetary cost = 별도 추정하지 않음
```

### P1

```text
CV compute
+
Decisions API usage
```

실제 API response의 usage / billing 정보를 기록한다.

### P2

```text
CV compute
+
Clef-Flash API cost
```

### P3

```text
CV compute
+
GPT-6.1 Sol text/state reasoning cost
```

### P4

```text
GPT-6.1 Sol visual input cost
+
output reasoning cost
```

현재 Benchmark는 Stage 2이므로 이 비용은 전체 CCTV 운영비가 아니라:

> **Candidate Event 1건당 Reasoning Cost**

이다.

---

# 23. 실제 운영비용으로의 확장

Benchmark 이후:

```text
Daily Reasoning Cost
≈
Daily Candidate Count
×
Candidate Cost
```

향후 Stage 0 Candidate Filter 실험에서 Candidate Rate를 측정한 후:

```text
477 CCTV
   ↓
Cheap Candidate Filter
   ↓
Candidate Events only
   ↓
Decision Pipeline
```

의 실제 일/월 운영비로 환산한다.

Candidate rate는 현재 Benchmark에서 임의로 가정해 성능 지표로 사용하지 않는다.

---

# 24. 핵심 비교 Matrix

| Pipeline | Visual Input | Decision Layer | 예상 비용 | 예상 속도 | 역할 |
|---|---|---|---|---|---|
| **P0** | CV | Rules | 최저 | 빠름 | Floor |
| **P1** | CV State | **OpenAI Decisions API / GPT-6 Luna** | 낮음 | 매우 빠를 것으로 기대 | **Default 후보** |
| **P2** | CV State | Clef-Flash | 낮음 | 매우 빠를 것으로 기대 | External Decision Baseline |
| **P3** | CV State | GPT-6.1 Sol | 중~높음 | 중간 | Strong State Reasoning |
| **P4** | Frames | GPT-6.1 Sol Vision | 가장 높음 | 가장 느릴 가능성 | Direct Vision Upper Bound |

비용/속도/성능 순위는 **가설**이며 실제 Benchmark로 결정한다.

---

# 25. 핵심 Pairwise Comparison

## P0 → P1

> Learned Decision Layer가 deterministic rule보다 얼마나 개선하는가?

## P1 ↔ P2

> Decisions API와 specialized external Decision Model 중 어느 쪽이 Cost–Accuracy–Latency 측면에서 유리한가?

## P1/P2 → P3

> Strong reasoning model의 추가 비용이 Structured State에서 실제 성능 향상으로 이어지는가?

## P3 → P4

> 같은 GPT-6.1 Sol에서 CV State 압축 대신 Visual Pixels를 직접 제공하면 얼마나 개선되는가?

## P1 → P4

> 저비용 production candidate가 direct-vision upper bound에 얼마나 근접하는가?

---

# 26. 최종 Cascade Architecture 후보

실험 결과가 현재 가설을 지지한다면 최종 서비스는 다음 구조를 목표로 한다.

```text
CCTV Streams
      ↓
Ultra-cheap Candidate Filter
      ↓
Shared Cheap CV
      ↓
Canonical / Compact CV State
      ↓
OpenAI Decisions API
      ↓

┌─────────────────────────────────────┐
│ LOW/MEDIUM risk + HIGH confidence  │
│ → 결과 확정 / suppress / Queue     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ HIGH risk + HIGH confidence        │
│ → 즉시 Attention Queue            │
│ → GPT-6.1 Sol 병렬 verification    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ LOW confidence / ambiguous         │
│ → GPT-6.1 Sol Vision escalation    │
│ → Human review                     │
└─────────────────────────────────────┘
```

---

# 27. 중요한 Safety Routing 원칙

위험도가 높은 사건을 강한 모델의 결과가 나올 때까지 Queue에서 막지 않는다.

즉:

```text
HIGH RISK
→ Attention Queue 즉시 진입
→ Strong Model은 병렬 verification / enrichment
```

으로 설계한다.

강한 모델은 안전 Alert를 지연시키는 Gate가 아니라:

- verification
- context enrichment
- additional evidence
- uncertainty resolution

역할을 한다.

---

# 28. Failure / Fallback

Decisions API는 beta 기능이므로 production-like experiment에서는 failure path를 반드시 둔다.

예:

```text
Decisions API timeout / unavailable
        ↓
P0 result 유지
        ↓
AI verification unavailable 표시
        ↓
High-risk라면 Human Review Queue
```

기록 항목:

- model ID
- endpoint
- API/SDK version
- request schema hash
- response raw JSON
- timeout
- retry count
- usage
- latency

---

# 29. Decisions API의 역할을 과장하지 않는 원칙

Decisions API를 해커톤 신기술이라는 이유만으로 채택하지 않는다.

P1 채택 여부는 다음 Benchmark 결과로 결정한다.

```text
Quality
Cost
Latency
Uncertainty handling
Attention ranking
Multi-camera reasoning
```

Clef-Flash나 GPT-6.1 Sol 대비 Pareto-optimal하지 않다면 최종 제품에서 제외할 수 있다.

즉:

> **신기술 사용 자체가 목표가 아니라, 477의 decision-heavy workload에 실제로 맞는지 검증하는 것이 목표다.**

---

# 30. Jev / Clef 27B의 위치

기존 계획의 Jev와 Clef 27B를 완전히 폐기하지 않는다.

다만 메인 P0~P4에서 제거하고 시간이 허용되면 supplementary experiment로 실행한다.

```text
P2b
CV State → Jev

P3b
CV State → Clef 27B
```

이유:

- P0~P4의 각 단계에 하나의 명확한 연구 질문을 유지
- 해커톤 구현 범위 관리
- 발표에서 지나치게 많은 모델 나열 방지
- 핵심 Pareto 비교에 집중

---

# 31. 모델 선정 규칙

## Case A

P1이 P4와 거의 같은 품질인데 비용과 latency가 훨씬 낮다.

→ **P1 Default**

## Case B

P2가 P1보다 동일/유사 품질에서 더 싸고 빠르다.

→ **P2 Default 검토**

## Case C

P3가 P1/P2보다 Ambiguous 또는 Multi-camera에서 명확히 좋다.

→

```text
P1/P2 Default
+
P3 State-based fallback
```

검토.

## Case D

P4가 P3보다 크게 좋다.

→ CV State가 시각 정보를 너무 많이 잃는 scenario가 존재.

```text
Cheap Decision
→ ambiguous / high-value case only
→ Direct Vision escalation
```

## Case E

P0만으로도 특정 명확한 사건이 충분하다.

→ 해당 유형에서는 Decision API 호출도 생략할 수 있음.

---

# 32. Pareto Frontier

최종 결과는 단순 최고점 모델이 아니라 Pareto Frontier로 표현한다.

```text
Quality
 ↑
 │
 │                       ● P4
 │
 │                ● P3
 │
 │       ● P1   ● P2
 │ ● P0
 │
 └──────────────────────────────→ Cost
```

실제 점 위치는 측정 결과로 결정한다.

추가 그래프:

```text
Quality vs Cost
Quality vs Latency
Latency vs Cost
```

---

# 33. 성공 기준

이번 실험은 다음 질문에 답할 수 있으면 성공이다.

### Q1

CV-only는 어디까지 가능한가?

### Q2

OpenAI Decisions API는 P0 rule보다 얼마나 개선되는가?

### Q3

Decisions API와 Clef-Flash 중 어느 쪽이 Cost–Accuracy–Latency에서 유리한가?

### Q4

GPT-6.1 Sol을 CV State에 사용했을 때 추가 성능은 얼마인가?

### Q5

동일 GPT-6.1 Sol에서 CV State와 Direct Vision의 차이는 얼마인가?

### Q6

Direct Vision의 추가 정확도가 비용과 latency를 정당화하는가?

### Q7

어떤 조건에서 strong-model escalation이 필요한가?

### Q8

477개의 CCTV를 실제 운영할 때 어떤 Cascade가 가장 합리적인가?

---

# 34. 예상 최종 발표 메시지

> **477 AI는 477개의 CCTV 영상을 모두 거대한 VLM으로 보내지 않습니다.**

> 먼저 저비용 CV가 사람의 움직임, 자세 변화, 상호작용과 가림 같은 관찰 사실을 구조화합니다.

> 대부분의 후보 사건은 빠른 Decision API가 정형화된 위험 판단을 수행하고, 위험하지만 애매한 일부 장면만 GPT-6.1 Sol이 실제 영상을 다시 확인합니다.

그리고 실험 결과를 근거로:

> 동일한 CCTV Benchmark에서 CV Rules, OpenAI Decisions API, specialized Decision Model, Strong Reasoning, Direct Vision을 단계적으로 비교하여 정확도뿐 아니라 지연시간과 후보 사건당 비용을 함께 측정했습니다.

라고 설명하는 것을 목표로 한다.

---

# 35. 구현 로드맵

```text
현재
│
├── Dataset 후보 선정                      DONE
├── 사람이 원본 영상 검수                   DONE
├── 477-reasoning-v1 Freeze                DONE
├── P0 Shared Cheap CV                     DONE
│
▼
P0.5 Decisions API Smoke Test
│
├── 인증
├── typed question
├── probability parsing
├── usage / latency logging
└── retry / fallback
│
▼
Compact Decision State Freeze
│
▼
P1 CV State + Decisions API
│
▼
P2 CV State + Clef-Flash
│
▼
P3 CV State + GPT-6.1 Sol
│
▼
P4 Frames + GPT-6.1 Sol Vision
│
▼
Human Grading
│
▼
Cost / Accuracy / Latency 비교
│
▼
Pareto Frontier
│
▼
Final Cascade Architecture 결정
│
▼
477 MVP Attention Queue 통합
```

---

# 36. 바로 다음 단계

다음 구현 작업은:

## P0.5 — Decisions API Smoke Test + Compact Decision State 설계

이다.

순서는 다음과 같다.

```text
Canonical CV State v1
        ↓
Compact Decision State Serializer
        ↓
한 ITEM으로 Decisions API Smoke Test
        ↓
Typed outputs / usage / latency 검증
        ↓
Serializer freeze
        ↓
P1 전체 7 conditions 실행
```

P0에서 만든 `Canonical CV State v1` 자체는 변경하지 않는다.

P1/P2/P3의 공정한 비교를 위해 Compact Decision State와 semantic questions를 **P1 실행 전에 동결**한다.

---

# 37. 외부 기술 검증 메모 (2026-10-07)

본 v2 설계에서 사용한 최신 OpenAI API 정보는 공식 문서 기준이다.

### OpenAI Decisions API

- 2026-10-06 beta 공개
- Endpoint: `/v1/decisions`
- 현재 모델: `gpt-6-luna`
- text / image evidence에서 typed answers 생성
- predicate / choice / score 형태의 decision 질문 지원
- API response에 usage 포함
- 공식 changelog에서는 Responses API 대비 decision task를 최대 10배 빠르게 처리하는 용도로 소개

Official:
- https://developers.openai.com/api/docs/changelog
- https://developers.openai.com/api/reference/resources/decisions/methods/create

### GPT-6 Luna

- focused, high-volume task용 효율 모델
- API list price: $0.10 / 1M input text tokens, $0.50 / 1M output text tokens

Official:
- https://developers.openai.com/api/docs/models/gpt-6-luna

### GPT-6.1 Sol

- complex reasoning용 모델
- image input 지원
- API list price: $2 / 1M input tokens, $10 / 1M output tokens
- P3에서는 text/structured CV State 입력
- P4에서는 canonical image frames 입력

Official:
- https://developers.openai.com/api/docs/models/gpt-6.1-sol

> 실제 477 실험의 비용은 list price만으로 추정하지 않고 각 API 실행 시 반환되는 usage와 실제 billing 기준으로 측정한다.

---

# 38. 문서 버전 변경 요약

### v1

```text
P0 Rules
P1 Clef-Flash
P2 Jev
P3 Clef
P4 Strong VLM
```

### v2

```text
P0 Rules
P1 OpenAI Decisions API / GPT-6 Luna
P2 Clef-Flash
P3 GPT-6.1 Sol on CV State
P4 GPT-6.1 Sol Direct Vision
```

### 핵심 개선

1. Decisions API를 핵심 Product Candidate로 직접 검증
2. P1/P2가 동일 State 기반 Decision Model 비교가 됨
3. P3/P4에 같은 GPT-6.1 Sol을 사용해 CV State 압축 손실을 통제 가능
4. 최종 Cascade가 477의 비용 문제와 직접 연결
5. High-risk Alert를 strong model이 지연시키지 않도록 Safety Routing 명확화
6. Jev/Clef 27B를 supplementary로 이동해 해커톤 범위와 발표 메시지를 단순화

