"""Build the blind P0-vs-P1 human grading pack.

- Reads P0/P1 result JSON (read-only), keeps only `prediction`, masks system-identifying phrases (logged privately).
- Deterministic A/B mapping from a fixed seed (independent of prediction content) -> reveal_map_private.json only.
- Generates cases/ITEM_XX/{system_A,system_B,reference}.json, blind_manifest.json, review/data/rubric.json,
  grading_guide.md, grading_reference.md from config/case_guides.yaml (private-reference-derived reviewer content).
- No scoring of any kind is performed. Benchmark validated before and after; result files hashed before and after.
"""
import copy
import datetime
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path

import yaml

PACK = Path(__file__).resolve().parents[1]
PROJECT = PACK.parents[1]
BENCH = PROJECT / 'benchmark_v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, v):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_benchmark(tag):
    r = subprocess.run([sys.executable, 'scripts/validate_benchmark.py'], cwd=BENCH, capture_output=True, text=True)
    print(f'validate_benchmark ({tag}):', 'PASS' if r.returncode == 0 else 'FAIL', r.stdout.strip())
    if r.returncode != 0:
        sys.exit(r.stderr)
    return r.stdout.strip()


def redact(obj, rules, log, path=''):
    if isinstance(obj, str):
        out = obj
        for r in rules:
            n = out.count(r['find'])
            if n:
                out = out.replace(r['find'], r['replace'])
                log.append({'path': path, 'find': r['find'], 'count': n})
        return out
    if isinstance(obj, dict):
        return {k: redact(v, rules, log, f'{path}.{k}') for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, rules, log, f'{path}[{i}]') for i, v in enumerate(obj)]
    return obj


def check_blind(text, tokens):
    hits = [t for t in tokens if re.search(r'(?<![A-Za-z0-9])' + re.escape(t) + r'(?![A-Za-z0-9])', text)]
    return hits


# ----------------------------------------------------------------------------- markdown generation
def src_tag(s):
    return f' `[{s}]`' if s else ''


def md_guide(g, cfg):
    L = ['# Grading Guide — 477 Blind Human Grading (System A / System B)', '',
         '이 문서는 모든 ITEM에 공통으로 적용되는 채점 기준입니다. ITEM별 구체 기준은 `grading_reference.md`와 Review UI의 "자세한 기준 펼치기"에 있습니다.',
         '', '**Claude/자동 도구는 점수를 매기지 않았습니다. 모든 점수는 reviewer가 직접 선택합니다.**', '',
         '## 0. 채점 절차 (assessment 1개당)', '',
         '1. ITEM 화면에서 CCTV 영상을 처음부터 끝까지 재생합니다 (필요하면 여러 번, seek 사용).',
         '2. Reviewer Reference를 읽습니다. 초록 박스 = **OBSERVABLE REFERENCE**(영상에서 확인되는 사실), 주황 박스 = **MUST REMAIN UNCERTAIN**(영상만으로 확정할 수 없는 것).',
         '3. System A의 prediction을 읽습니다 (Event → Incident? → Risk → Confidence → Temporal summary → Evidence → Reason → Uncertainties → Human Review).',
         '4. 4개 metric을 **각각 독립적으로** 0/1/2 중에서 선택합니다. 고민되면 "자세한 기준 펼치기"를 엽니다.',
         '5. 근거 없는 단정이 있으면 Overclaim flag를 추가하고 출력의 **정확한 인용문**과 **이유**를 적습니다.',
         '6. 두 확인 checkbox(실제 영상 확인 / evidence와 영상 비교)를 체크하고 Submit 합니다.',
         '7. 그 다음 System B가 열립니다. 같은 방식으로 채점합니다 (A 점수는 보이지 않습니다).',
         '8. 모두 끝나면 Export grading JSON → `grades/<reviewer_id>.json`로 저장(또는 Save to server).', '',
         '## 1. 공통 원칙', '']
    L += [f'- {r}' for r in g['general_rules']]
    L += ['', '## 2. 출처 표시(provenance) 읽는 법', '',
          '| 태그 | 의미 |', '|---|---|',
          '| `HV` | human_verified_observation — 사람이 원본 영상으로 확인한 사실 |',
          '| `PR` | project_defined_reference — 477 프로젝트 정의 reference / expected uncertainty |',
          '| `CS` | project clip-selection 기록 (SET03) |',
          '| `SA` | AI Hub source annotation (source label/XML/caption) — **참고 맥락이며 정답 아님** |',
          '| `DER` | SA/CS 시각을 clip 상대시간으로 산술 환산한 근사치 (프레임 규약 미검증; 영상으로 확인) |', '']
    L += ['## 3. Metric별 0/1/2 기준', '',
          '> **Score this dimension independently. A wrong event label does not automatically mean evidence grounding is 0.**', '']
    for k, m in g['general_rubric'].items():
        L += [f'### {m["title"]}', '', f'**질문:** {m["question"]}', '',
              '| 점수 | 한 줄 요약 |', '|---|---|'] + [f'| {s} | {m["short"][s]} |' for s in ('2', '1', '0')] + ['',
              '**① 2점을 주는 최소 조건**', '', m['two_min'].strip(), '',
              '**② 1점을 주는 상황**', '', m['one_when'].strip(), '',
              '**③ 0점을 주는 상황**', '', m['zero_when'].strip(), '',
              '**④ 흔히 헷갈리는 경계 사례**', '', m['boundary'].strip(), '']
    L += ['## 4. Overclaim flags (점수와 별도)', '',
          'flag를 추가할 때는 반드시 **exact_output_quote**(prediction에 실제로 있는 문장 그대로)와 **why_unsupported**(왜 영상이 뒷받침하지 않는지)를 적습니다. 키워드가 보인다고 자동으로 flag하지 마세요. 부정문("cannot be determined")은 단정이 아닙니다.', '',
          '| flag | 의미 |', '|---|---|'] + [f'| `{k}` | {v} |' for k, v in g['overclaim_flags'].items()] + ['']
    i4, i7 = g['items']['ITEM_04'], g['items']['ITEM_07']
    L += ['## 5. SET04 (ITEM_04) Attention Ranking', '',
          f'> **{i4["ranking"]["notice"]}**', '',
          f'- Reference order: **{" > ".join(i4["ranking"]["reference_order"])}**',
          f'- Top-1 Correct: {i4["ranking"]["top1_rule"]}',
          f'- Full Order Correct: {i4["ranking"]["full_order_rule"]}',
          f'- {i4["ranking"]["independence_note"]}', '',
          '4-metric 채점은 출력 전체에 대해 한 번 합니다. 카메라별 보조 판단 방법:', '', i4['aggregation_rule'].strip(), '',
          '## 6. SET05 (ITEM_05 / ITEM_06 / ITEM_07)', '',
          '- ITEM_05 = CAM A only, ITEM_06 = CAM B only, ITEM_07 = CAM A + B. 세 조건 모두 각각 0–8점으로 독립 채점합니다.',
          f'- {i7["multiview_increment_note"]}',
          '- **잘못된 비교:** AB > A → multi-view 성공. **올바른 비교:** AB > max(A, B). CAM B 단독이 이미 강할 수 있습니다.',
          '- ITEM_07에는 별도의 qualitative 질문 3개가 있습니다 (main 0–8 점수와 별개):', '']
    for q in i7['multiview_questions'].values():
        L += [f'  - **{q["question"]}**'] + [f'    - `{o}`: {d}' for o, d in q['options'].items()]
    L += ['', '## 7. 하지 말아야 할 것', '',
          '- System A/B가 어느 시스템인지 추측하거나 찾아보지 마세요 (`reveal_map_private.json`, `scripts/`, `output/`을 열지 마세요).',
          '- 다른 reviewer의 grades 파일을 보지 마세요.',
          '- confidence, human_review_required 값으로 점수를 조정하지 마세요.',
          '- source label과 같은 단어를 썼다는 이유로 점수를 주지 마세요.',
          '- 결과를 "정확도 %"로 부르지 마세요. 5개 case의 rubric 합계/평균만 보고합니다.', '']
    return '\n'.join(L)


def md_reference(g):
    L = ['# Grading Reference — ITEM별 Reviewer Reference와 0/1/2 Anchor', '',
         '출처: `benchmark_v1/private_ground_truth/set01~05.json`의 human_verified_observation(HV), project_defined_reference(PR), clip_selection(CS), source annotation(SA, 참고 맥락).',
         '이 문서에 private 파일에 없는 사실은 추가하지 않았습니다. `DER` 시각은 SA/CS 시각을 clip 상대시간으로 환산한 근사치입니다.', '',
         '> 이 문서는 **사람 reviewer 전용**입니다. 모델 입력으로 절대 사용하지 마세요.', '']
    names = {'event_understanding': 'Event Understanding', 'temporal_understanding': 'Temporal Understanding',
             'evidence_grounding': 'Evidence Grounding', 'uncertainty_handling': 'Uncertainty Handling'}
    for item, c in g['items'].items():
        L += [f'---', '', f'## {item} — {c["set"]} ({c["task"]}{", " + c["condition"] if c.get("condition") else ""})', '',
              f'*Cameras:* {", ".join(c["cameras"])} · *Sampling:* {c["sampling_note"]}', '',
              f'**이 case의 핵심 observable 사건:** {c["core_observable_event"]}', '',
              '### 영상에서 먼저 확인할 부분'] + [f'- {x}' for x in c['watch_first']] + ['',
              '### OBSERVABLE REFERENCE — What is visibly established?'] + [f'- {x["text"]}{src_tag(x["src"])}' for x in c['observable_reference']] + ['',
              '### MUST REMAIN UNCERTAIN — What is NOT established?'] + [f'- {x["text"]}{src_tag(x["src"])}' for x in c['must_remain_uncertain']] + ['',
              '### Critical temporal sequence'] + [f'{i + 1}. {x["text"]}{src_tag(x["src"])}' for i, x in enumerate(c['critical_temporal_sequence'])] + ['',
              '### Evidence that should matter'] + [f'- {x}' for x in c['evidence_that_matters']] + ['',
              '### Known ambiguity'] + [f'- {x}' for x in c['known_ambiguity']] + ['',
              '### What a strong answer should capture'] + [f'- {x}' for x in c['strong_answer_should_capture']] + ['',
              '### What an answer must NOT assert'] + [f'- {x}' for x in c['must_not_assert']] + ['',
              f'### Source label (context only — NOT the grading answer)', f'- {c["source_label_context"]["label"]}', f'- {c["source_label_context"]["note"]}', '',
              '### prediction에서 중점적으로 볼 부분'] + [f'- {x}' for x in c['focus_fields']] + ['',
              '### 흔히 하는 착각'] + [f'- {x}' for x in c['common_mistakes']] + ['']
        if c.get('aggregation_rule'):
            L += ['### 카메라별 보조 판단 (ITEM_04)', '', c['aggregation_rule'].strip(), '']
        for k, m in c['metrics'].items():
            L += [f'### {item} — {names[k]}', '', f'- **2점:** {m["2"]}', f'- **1점:** {m["1"]}', f'- **0점:** {m["0"]}', f'- **Reviewer tip:** {m["tip"]}', '']
        if c.get('ranking'):
            r = c['ranking']
            L += ['### Attention ranking (별도 채점)', '', f'> **{r["notice"]}**', '', f'- Reference order: **{" > ".join(r["reference_order"])}**']
            L += [f'  - {x["camera"]}: {x["text"]} `[{x["src"]}]`' for x in r['rationale']]
            L += [f'- Top-1 Correct: {r["top1_rule"]}', f'- Full Order Correct: {r["full_order_rule"]}', f'- {r["independence_note"]}', '']
        if c.get('multiview_questions'):
            L += ['### Multi-camera qualitative checks (main 점수와 별개)', '']
            for q in c['multiview_questions'].values():
                L += [f'- **{q["question"]}**'] + [f'  - `{o}`: {d}' for o, d in q['options'].items()]
            L += ['', f'- {c["multiview_increment_note"]}', '']
    return '\n'.join(L)


# ----------------------------------------------------------------------------- main
def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    cfg = json.loads((PACK / 'config' / 'build_config.json').read_text(encoding='utf-8'))
    guides = yaml.safe_load((PACK / 'config' / 'case_guides.yaml').read_text(encoding='utf-8'))
    before = validate_benchmark('before')
    scenarios = json.loads((BENCH / 'model_input' / 'scenarios.json').read_text(encoding='utf-8-sig'))
    tasks = {x['item_id']: (x['task'], [c['camera'] for c in x['cameras']]) for x in scenarios['items']}
    result_hash_before, result_paths = {}, {}
    for sys_key, rel in cfg['systems'].items():
        for item in cfg['items']:
            p = BENCH / rel / f'run_{item}.json'
            result_paths[(sys_key, item)] = p
            result_hash_before[f'{sys_key}/{item}'] = sha(p)

    rng = random.Random(cfg['ab_randomization']['seed'])
    reveal, redaction_log, manifest_items = {}, {}, []
    for item in cfg['items']:
        order = ['p0', 'p1']
        rng.shuffle(order)
        mapping = {'System_A': order[0], 'System_B': order[1]}
        reveal[item] = mapping
        task, cams = tasks[item]
        files = {}
        for label, sys_key in mapping.items():
            res = json.loads(result_paths[(sys_key, item)].read_text(encoding='utf-8'))
            log = []
            pred = redact(copy.deepcopy(res['prediction']), cfg['redactions'], log)
            redaction_log[f'{item}/{label}'] = log
            blind = {'pack_version': cfg['pack_version'], 'item_id': item, 'task': task, 'cameras': cams,
                     'system': label.replace('_', ' '), 'prediction': pred,
                     'sanitization_note': 'Only the prediction is kept; system-identifying phrases are masked as "[system ...]". No other wording was changed.'}
            text = json.dumps(blind, ensure_ascii=False)
            hits = check_blind(text, cfg['forbidden_tokens_after_sanitization'])
            if hits:
                sys.exit(f'{item}/{label}: identifying tokens remain after sanitization: {hits}')
            fname = f'system_{label[-1]}.json'
            write_json(PACK / 'cases' / item / fname, blind)
            files[label] = fname
        c = guides['items'][item]
        reference = {'pack_version': cfg['pack_version'], 'item_id': item, **c,
                     'general_metric_titles': {k: v['title'] for k, v in guides['general_rubric'].items()},
                     'note': 'Reviewer-only grading reference derived from benchmark_v1/private_ground_truth. Never use as model input.'}
        write_json(PACK / 'cases' / item / 'reference.json', reference)
        manifest_items.append({
            'item_id': item, 'set': c['set'], 'task': task, 'condition': c.get('condition'),
            'cameras': [{'camera': cam, 'video_url': f'/video/{item}/{cam}'} for cam in cams],
            'assessments': [{'system': 'System_A', 'file': f'cases/{item}/system_A.json'}, {'system': 'System_B', 'file': f'cases/{item}/system_B.json'}],
            'reference_file': f'cases/{item}/reference.json',
            'extra': (['ranking'] if task == 'attention' else []) + (['multiview_qualitative'] if task == 'multi_camera' else []),
        })

    blind_manifest = {
        'pack_version': cfg['pack_version'],
        'title': '477 Blind Human Grading — System A vs System B',
        'total_assessments': 2 * len(cfg['items']),
        'metrics': cfg['metrics'],
        'main_five_cases': cfg['main_five_cases'],
        'items': manifest_items,
        'case_file_sha256': {str(p.relative_to(PACK)).replace('\\', '/'): sha(p) for p in sorted((PACK / 'cases').rglob('*.json'))},
        'note': 'Contains no system identities. The A/B mapping is stored only in reveal_map_private.json, which the reviewer UI never loads.',
    }
    write_json(PACK / 'blind_manifest.json', blind_manifest)
    write_json(PACK / 'review' / 'data' / 'rubric.json', {
        'general_rules': guides['general_rules'], 'general_rubric': guides['general_rubric'], 'overclaim_flags': guides['overclaim_flags']})

    (PACK / 'grading_guide.md').write_text(md_guide(guides, cfg), encoding='utf-8')
    (PACK / 'grading_reference.md').write_text(md_reference(guides), encoding='utf-8')

    result_hash_after = {f'{s}/{i}': sha(result_paths[(s, i)]) for s, i in result_paths}
    if result_hash_after != result_hash_before:
        sys.exit('P0/P1 result files changed during build!')
    after = validate_benchmark('after')
    write_json(PACK / 'reveal_map_private.json', {
        'WARNING': 'PRIVATE — do not open before grading is complete. Never served to the reviewer UI.',
        'pack_version': cfg['pack_version'], 'seed': cfg['ab_randomization']['seed'],
        'mapping': reveal,
        'systems': {'p0': 'P0 CV-only (benchmark_v1/results/p0_cv_only)', 'p1': 'P1 Decisions (benchmark_v1/results/p1_decisions)'},
        'result_file_sha256': result_hash_before,
        'redaction_log': redaction_log,
        'build': {'built_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                  'benchmark_validation_before': before, 'benchmark_validation_after': after,
                  'result_files_unchanged': True, 'auto_grading_performed': False},
    })
    print(f"Built {blind_manifest['total_assessments']} blinded assessments for {len(cfg['items'])} items.")
    print('Redactions per assessment:', {k: sum(x['count'] for x in v) for k, v in redaction_log.items()})


if __name__ == '__main__':
    main()
