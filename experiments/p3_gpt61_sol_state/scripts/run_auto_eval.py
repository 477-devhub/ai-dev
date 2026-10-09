"""EVALUATOR ONLY (separate process, after freeze/p3_results_manifest.json).

Reuses the P2 automatic evaluator (experiments/p2_clef_flash/scripts/run_auto_eval.py) READ-ONLY and UNCHANGED: same
category rules, contradiction rules, overclaim screening, temporal/ranking/multi-camera metrics and the same
evaluation/normalized_ground_truth_v1.json. Only the set of result directories is extended:
  p0, p1 (v1 raw), p2 (v1 raw), p1v2 / p2v2 (common-adapter-v2 normalized), p3 (common-adapter-v2).
Adds (clearly separate) a raw-category view from runtime decision_summary.category, and the P3 audit queue.
Writes evaluation/auto_eval_results.json, auto_eval_summary.md, human_audit_queue.md.
"""
import datetime
import hashlib
import importlib
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
P2 = PROJECT / 'experiments' / 'p2_clef_flash'
CA2 = PROJECT / 'experiments' / 'common_adapter_v2'
BENCH = PROJECT / 'benchmark_v1'
EVAL = EXP / 'evaluation'
ITEMS = [f'ITEM_{i:02d}' for i in range(1, 8)]
P2_EVALUATOR = P2 / 'scripts' / 'run_auto_eval.py'
GT_FILE = P2 / 'evaluation' / 'normalized_ground_truth_v1.json'
RESULT_DIRS = {'p0': BENCH / 'results' / 'p0_cv_only', 'p1': BENCH / 'results' / 'p1_decisions', 'p2': BENCH / 'results' / 'p2_clef_flash',
               'p1v2': CA2 / 'normalized' / 'p1', 'p2v2': CA2 / 'normalized' / 'p2', 'p3': BENCH / 'results' / 'p3_gpt61_sol_state'}
LABEL = {'p0': 'P0', 'p1': 'P1-v1 raw', 'p2': 'P2-v1 raw', 'p1v2': 'P1 (adapter-v2)', 'p2v2': 'P2 (adapter-v2)', 'p3': 'P3 (adapter-v2)'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def log_event(event, detail=None):
    with (EXP / 'logs' / 'process_audit_log.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'at': datetime.datetime.now().astimezone().isoformat(timespec='milliseconds'), 'event': event,
                            'script': 'run_auto_eval.py', 'detail': detail}, ensure_ascii=False) + '\n')


def load_p2_evaluator():
    sys.path[:0] = [str(P2 / 'scripts'), str(P2 / 'src')]
    ev = importlib.import_module('run_auto_eval')
    assert Path(ev.__file__).resolve() == P2_EVALUATOR.resolve()
    return ev


def raw_units(pipe, item):
    """(label, raw category, is_incident, p_incident) from runtime decision_summary (model raw category answer)."""
    ds = jload(RESULT_DIRS[pipe] / f'run_{item}.json')['runtime_config'].get('decision_summary')
    if ds is None:
        return None
    if item == 'ITEM_04':
        return {f'ITEM_04/{c}': d for c, d in ds['per_camera'].items()}
    return {item: ds}


def main():
    man = jload(EXP / 'freeze' / 'p3_results_manifest.json')
    drift = [k for k, h in man['sha256'].items() if sha((BENCH if k.startswith('results/') else EXP) / k) != h]
    if drift:
        sys.exit(f'frozen P3 outputs changed: {drift}')
    ev = load_p2_evaluator()
    evaluator_sha = sha(P2_EVALUATOR)
    log_event('run_auto_eval', {'phase': 'start', 'p2_evaluator_sha256': evaluator_sha})
    files = [d / f'run_{i}.json' for d in RESULT_DIRS.values() for i in ITEMS]
    before = {str(f): sha(f) for f in files}
    ev.PIPELINES.clear()
    ev.PIPELINES.update({k: str(v) for k, v in RESULT_DIRS.items()})   # absolute dirs; rule code untouched
    gt = jload(GT_FILE)
    results = {p: ev.evaluate(p, gt) for p in RESULT_DIRS}
    summ = {p: ev.summarize(r) for p, r in results.items()}
    cal = ev.calibration(results)
    # raw-category view (model's category answer before common-adapter-v2), same regex-free direct comparison
    raw_view = {}
    for p in ('p1', 'p2', 'p3'):
        rows = {}
        for item in ITEMS:
            g = gt['items'][item]
            for label, d in raw_units(p, item).items():
                exp = g['per_camera'][label.split('/')[1]]['normalized_event_target'] if item == 'ITEM_04' else g['normalized_event_target']
                rows[label] = {'raw_category': d['category'], 'expected': exp, 'raw_category_match': d['category'] == exp,
                               'p_incident': d['p_incident'], 'is_incident': d['is_incident'], 'category_confidence': d['category_confidence']}
        raw_view[p] = {'rows': rows, 'raw_category_match': f"{sum(r['raw_category_match'] for r in rows.values())}/{len(rows)}"}
    queue = audit_queue(ev, results, gt, raw_view)
    after = {str(f): sha(f) for f in files}
    if before != after:
        sys.exit('result files changed during evaluation')
    EVAL.mkdir(exist_ok=True)
    out = {'version': 'auto-eval-v1 (P2 evaluator reused unchanged)', 'evaluated_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'p2_evaluator_file': 'experiments/p2_clef_flash/scripts/run_auto_eval.py', 'p2_evaluator_sha256': evaluator_sha,
           'ground_truth': 'experiments/p2_clef_flash/evaluation/normalized_ground_truth_v1.json', 'ground_truth_sha256': sha(GT_FILE),
           'result_dirs': {k: str(v.relative_to(PROJECT)).replace('\\', '/') for k, v in RESULT_DIRS.items()},
           'result_files_unchanged_by_evaluator': True, 'summary': summ, 'raw_category_view': raw_view,
           'per_item': results, 'calibration_vs_human': cal, 'p3_audit_queue': queue}
    (EVAL / 'auto_eval_results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (EVAL / 'auto_eval_summary.md').write_text(md_summary(ev, results, summ, raw_view, cal, gt), encoding='utf-8')
    (EVAL / 'human_audit_queue.md').write_text(md_queue(queue), encoding='utf-8')
    log_event('run_auto_eval', {'phase': 'end', 'p3_flagged': len(queue)})
    for p in RESULT_DIRS:
        print(LABEL[p], json.dumps({k: v for k, v in summ[p].items() if k != 'category_match_items'}))
    print('raw category match:', {p: v['raw_category_match'] for p, v in raw_view.items()})
    print('P3 flagged:', len(queue), '| full video:', sum(r['full_video_review'] for r in queue))


def audit_queue(ev, results, gt, raw_view):
    rows = []
    for label, x in ev.assessments(results['p3']):
        item = label.split('/')[0]
        g = gt['items'][item]
        why = []
        if g.get('ambiguous_case'):
            why.append('ambiguous benchmark case')
        if not x['category_match']:
            why.append('normalized category mismatch (final event_type)')
        why += [f'internal contradiction: {c}' for c in x['internal_contradictions']]
        why += [f"suspected overclaim ({s['type']})" for s in x['suspected_overclaims']]
        if item == 'ITEM_07' and x.get('multi_camera', {}).get('cross_camera_sync_or_identity_assertions'):
            why.append('cross-camera sync/identity assertion')
        if x['very_low_confidence']:
            why.append(f"very low confidence ({x['confidence']})")
        r3, r1, r2 = (raw_view[p]['rows'][label] for p in ('p3', 'p1', 'p2'))
        if (r3['raw_category'] != r1['raw_category'] and r3['raw_category'] != r2['raw_category']) or \
                (r3['is_incident'] != r1['is_incident'] and r3['is_incident'] != r2['is_incident']):
            why.append(f"P1/P2/P3 major disagreement (raw category P1={r1['raw_category']}, P2={r2['raw_category']}, P3={r3['raw_category']}; "
                       f"is_incident P1={r1['is_incident']}, P2={r2['is_incident']}, P3={r3['is_incident']})")
        if not why:
            continue
        full = bool(g.get('ambiguous_case') or not x['category_match'])
        quote = '; '.join(f"\"{s['quote']}\"" for s in x['suspected_overclaims'][:2]) or '-'
        rows.append({'item': label, 'pipeline': 'p3', 'why': why,
                     'prediction': f"{x['event_type']} · raw={r3['raw_category']} ({r3['category_confidence']}) · p(inc)={r3['p_incident']} · conf={x['confidence']}",
                     'expected': x['expected_category'] + (' (observable only; authorization/intent not GT)' if g.get('ambiguous_case') else ''),
                     'quote': quote, 'full_video_review': full})
    return rows


def md_queue(rows):
    L = ['# P3 human audit queue (automatic evaluation, P2 evaluator reused)', '',
         'Only flagged P3 assessments. **FULL VIDEO** = ambiguous case or final-category mismatch (P3 has no human grade). '
         'Other rows: check the decision / quoted text only. Suspected overclaims are keyword flags, not confirmed violations.', '',
         f"- P3 assessments flagged: {len(rows)}; full video: {sum(r['full_video_review'] for r in rows)}; text-only: {sum(not r['full_video_review'] for r in rows)}", '',
         '| ITEM | Review | Why flagged | Model prediction | Expected observable target | Suspicious quote |', '|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: (not r['full_video_review'], r['item'])):
        L.append(f"| {r['item']} | {'**FULL VIDEO**' if r['full_video_review'] else 'text check'} | {'; '.join(r['why'])} | {r['prediction']} | {r['expected']} | {r['quote']} |")
    return '\n'.join(L) + '\n'


def md_summary(ev, results, summ, raw_view, cal, gt):
    P = list(RESULT_DIRS)
    L = ['# Automatic evaluation summary — P0 / P1 / P2 / P3', '',
         f"Generated {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}. The P2 evaluator (auto-eval-v1) is reused unchanged with the same "
         'normalized_ground_truth_v1. Diagnostic counts only (x/N), not % accuracy, not human rubric scores. '
         '"v1 raw" = official raw experiment records; "adapter-v2" = common-adapter-v2 presentation (event_type = "no clear incident" when p(incident) < 0.5).', '',
         '| Metric | ' + ' | '.join(LABEL[p] for p in P) + ' |', '|---|' + '---|' * len(P)]
    for k in summ['p0']:
        if k != 'category_match_items':
            L.append(f'| {k} | ' + ' | '.join(str(summ[p][k]) for p in P) + ' |')
    L += [f"| raw category match (model category answer, before adapter) | n/a | {raw_view['p1']['raw_category_match']} | {raw_view['p2']['raw_category_match']} | "
          f"{raw_view['p1']['raw_category_match']} | {raw_view['p2']['raw_category_match']} | {raw_view['p3']['raw_category_match']} |", '',
          '## Per assessment (final event category; raw category in brackets)', '',
          '| Assessment | Expected | P0 | P1 (v2) | P2 (v2) | P3 (v2) |', '|---|---|---|---|---|---|']
    for label, x in ev.assessments(results['p0']):
        cells = []
        for p in ('p0', 'p1v2', 'p2v2', 'p3'):
            y = dict(ev.assessments(results[p]))[label]
            raw = '' if p == 'p0' else f" [{raw_view[p[:2]]['rows'][label]['raw_category']}]"
            cells.append(f"{y['predicted_category']} {'✓' if y['category_match'] else '✗'}{raw} p={raw_view[p[:2]]['rows'][label]['p_incident'] if p != 'p0' else '-'}")
        L.append(f"| {label} | {x['expected_category']}{' (ambiguous)' if gt['items'][label.split('/')[0]].get('ambiguous_case') else ''} | " + ' | '.join(cells) + ' |')
    L += ['', '## Attention / multi-camera', '', '| Pipeline | Attention order | top1 | full | same_incident | AB/A/B final category | AB conf - best single |', '|---|---|---|---|---|---|---|']
    for p in P:
        a, m = results[p]['ITEM_04'], results[p]['ITEM_07']['multi_camera']
        L.append(f"| {LABEL[p]} | {' > '.join(a['attention_order'])} | {a['top1_correct']} | {a['full_order_correct']} | {m['same_incident_predicted']} | "
                 f"{m['AB_category_correct']}/{m['A_category_correct']}/{m['B_category_correct']} | {m['AB_confidence_minus_best_single']} |")
    if cal:
        L += ['', f"Calibration vs reviewer_01 (P0/P1-v1 only, unchanged): {cal['verdict']} (OPPOSITE {cal['opposite']}/{cal['decisive_comparisons']}, partial {cal['partial']})."]
    L += ['', 'Note: P1/P2/P3 observations, temporal summaries and uncertainties come from the same deterministic templates over the same frozen state; '
          'evidence/temporal metrics do not distinguish the decision models.', '']
    return '\n'.join(L)


if __name__ == '__main__':
    main()
