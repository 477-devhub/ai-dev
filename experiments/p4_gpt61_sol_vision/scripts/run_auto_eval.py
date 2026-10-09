"""EVALUATOR ONLY (separate process, only after freeze/p4_results_manifest.json).

Reuses the P2 automatic evaluator (experiments/p2_clef_flash/scripts/run_auto_eval.py) READ-ONLY and UNCHANGED, with the same
normalized_ground_truth_v1. Result sets: p0, p1/p2 (v1 raw), p1v2/p2v2 (common-adapter-v2), p3, p4.
Adds a raw-category view and the P4 human audit queue (ambiguous, category mismatch, P3/P4 disagreement, suspected
overclaim, cross-camera identity/sync assertion, very low confidence, unexpected boundary interpretation).
Writes evaluation/auto_eval_results.json, auto_eval_summary.md, human_audit_queue.md."""
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
               'p1v2': CA2 / 'normalized' / 'p1', 'p2v2': CA2 / 'normalized' / 'p2', 'p3': BENCH / 'results' / 'p3_gpt61_sol_state',
               'p4': BENCH / 'results' / 'p4_gpt61_sol_vision'}
LABEL = {'p0': 'P0', 'p1': 'P1-v1 raw', 'p2': 'P2-v1 raw', 'p1v2': 'P1 (v2)', 'p2v2': 'P2 (v2)', 'p3': 'P3 state (v2)', 'p4': 'P4 vision (v2)'}
ENTRY = 'possible_scene_or_boundary_entry'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def log_event(event, detail=None):
    with (EXP / 'logs' / 'process_audit_log.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'at': datetime.datetime.now().astimezone().isoformat(timespec='milliseconds'), 'event': event,
                            'script': Path(sys.argv[0]).name, 'detail': detail}, ensure_ascii=False) + '\n')


def load_p2_evaluator():
    sys.path[:0] = [str(P2 / 'scripts'), str(P2 / 'src')]
    ev = importlib.import_module('run_auto_eval')
    assert Path(ev.__file__).resolve() == P2_EVALUATOR.resolve()
    return ev


def raw_rows(pipe, gt):
    rows = {}
    for item in ITEMS:
        ds = jload(RESULT_DIRS[pipe] / f'run_{item}.json')['runtime_config']['decision_summary']
        units = {f'ITEM_04/{c}': d for c, d in ds['per_camera'].items()} if item == 'ITEM_04' else {item: ds}
        for label, d in units.items():
            g = gt['items'][item]
            exp = g['per_camera'][label.split('/')[1]]['normalized_event_target'] if item == 'ITEM_04' else g['normalized_event_target']
            rows[label] = {'raw_category': d['category'], 'expected': exp, 'raw_category_match': d['category'] == exp, 'p_incident': d['p_incident'],
                           'is_incident': d['is_incident'], 'category_confidence': d['category_confidence'], 'confidence': d['confidence']}
    return rows


def main():
    man = jload(EXP / 'freeze' / 'p4_results_manifest.json')
    drift = [k for k, h in man['sha256'].items() if sha((BENCH if k.startswith('results/') else EXP) / k) != h]
    if drift:
        sys.exit(f'frozen P4 outputs changed: {drift}')
    ev = load_p2_evaluator()
    log_event('run_auto_eval', {'phase': 'start', 'p2_evaluator_sha256': sha(P2_EVALUATOR)})
    files = [d / f'run_{i}.json' for d in RESULT_DIRS.values() for i in ITEMS]
    before = {str(f): sha(f) for f in files}
    ev.PIPELINES.clear()
    ev.PIPELINES.update({k: str(v) for k, v in RESULT_DIRS.items()})
    gt = jload(GT_FILE)
    results = {p: ev.evaluate(p, gt) for p in RESULT_DIRS}
    summ = {p: ev.summarize(r) for p, r in results.items()}
    cal = ev.calibration(results)
    raw = {p: raw_rows(p, gt) for p in ('p1', 'p2', 'p3', 'p4')}
    rawm = {p: f"{sum(r['raw_category_match'] for r in v.values())}/{len(v)}" for p, v in raw.items()}
    queue = audit_queue(ev, results, gt, raw)
    if before != {str(f): sha(f) for f in files}:
        sys.exit('result files changed during evaluation')
    EVAL.mkdir(exist_ok=True)
    (EVAL / 'auto_eval_results.json').write_text(json.dumps({
        'version': 'auto-eval-v1 (P2 evaluator reused unchanged)', 'evaluated_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'p2_evaluator_sha256': sha(P2_EVALUATOR), 'ground_truth_sha256': sha(GT_FILE),
        'result_dirs': {k: str(v.relative_to(PROJECT)).replace('\\', '/') for k, v in RESULT_DIRS.items()},
        'result_files_unchanged_by_evaluator': True, 'summary': summ, 'raw_category_match': rawm, 'raw_rows': raw,
        'per_item': results, 'calibration_vs_human': cal, 'p4_audit_queue': queue}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (EVAL / 'auto_eval_summary.md').write_text(md_summary(ev, results, summ, rawm, raw, cal), encoding='utf-8')
    (EVAL / 'human_audit_queue.md').write_text(md_queue(queue), encoding='utf-8')
    log_event('run_auto_eval', {'phase': 'end', 'p4_flagged': len(queue)})
    for p in RESULT_DIRS:
        print(LABEL[p], json.dumps({k: v for k, v in summ[p].items() if k != 'category_match_items'}))
    print('raw category match:', rawm)
    print('P4 flagged:', len(queue), '| full video:', sum(r['full_video_review'] for r in queue))


def audit_queue(ev, results, gt, raw):
    rows = []
    for label, x in ev.assessments(results['p4']):
        item = label.split('/')[0]
        g = gt['items'][item]
        r4, r3 = raw['p4'][label], raw['p3'][label]
        why = []
        if g.get('ambiguous_case'):
            why.append('ambiguous benchmark case')
        if not x['category_match']:
            why.append('normalized category mismatch (final event_type)')
        if r4['raw_category'] != r3['raw_category'] or r4['is_incident'] != r3['is_incident']:
            why.append(f"P3/P4 disagreement (raw P3={r3['raw_category']} inc={r3['is_incident']}; P4={r4['raw_category']} inc={r4['is_incident']})")
        why += [f'internal contradiction: {c}' for c in x['internal_contradictions']]
        why += [f"suspected overclaim ({s['type']})" for s in x['suspected_overclaims']]
        if item == 'ITEM_07' and x.get('multi_camera', {}).get('cross_camera_sync_or_identity_assertions'):
            why.append('cross-camera identity/sync assertion')
        if x['very_low_confidence']:
            why.append(f"very low confidence ({x['confidence']})")
        if (r4['raw_category'] == ENTRY) != (r4['expected'] == ENTRY):
            why.append(f"unexpected boundary interpretation (raw {r4['raw_category']} vs expected {r4['expected']})")
        if not why:
            continue
        full = bool(g.get('ambiguous_case') or not x['category_match'])
        quote = '; '.join(f"\"{s['quote']}\"" for s in x['suspected_overclaims'][:2]) or '-'
        rows.append({'item': label, 'pipeline': 'p4', 'why': why, 'full_video_review': full, 'quote': quote,
                     'prediction': f"{x['event_type']} · raw={r4['raw_category']} ({r4['category_confidence']}) · p(inc)={r4['p_incident']} · conf={x['confidence']}",
                     'expected': x['expected_category'] + (' (observable only; authorization/intent not GT)' if g.get('ambiguous_case') else '')})
    return rows


def md_queue(rows):
    L = ['# P4 human audit queue (automatic evaluation; P2 evaluator reused unchanged)', '',
         'Only flagged P4 assessments. **FULL VIDEO** = ambiguous case or final-category mismatch. Other rows: check decision / quoted text. '
         'Suspected overclaims are keyword flags (negated sentences skipped), not confirmed violations.', '',
         f"- P4 assessments flagged: {len(rows)}; full video: {sum(r['full_video_review'] for r in rows)}; text-only: {sum(not r['full_video_review'] for r in rows)}", '',
         '| ITEM | Review | Why flagged | Model prediction | Expected observable target | Suspicious quote |', '|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: (not r['full_video_review'], r['item'])):
        L.append(f"| {r['item']} | {'**FULL VIDEO**' if r['full_video_review'] else 'text check'} | {'; '.join(r['why'])} | {r['prediction']} | {r['expected']} | {r['quote']} |")
    return '\n'.join(L) + '\n'


def md_summary(ev, results, summ, rawm, raw, cal):
    P = list(RESULT_DIRS)
    L = ['# Automatic evaluation summary — P0 … P4', '',
         f"Generated {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}. P2 evaluator (auto-eval-v1) reused unchanged; same "
         'normalized_ground_truth_v1. Diagnostic counts (x/N) only — not % accuracy, not human rubric scores.', '',
         '| Metric | ' + ' | '.join(LABEL[p] for p in P) + ' |', '|---|' + '---|' * len(P)]
    for k in summ['p0']:
        if k != 'category_match_items':
            L.append(f'| {k} | ' + ' | '.join(str(summ[p][k]) for p in P) + ' |')
    L.append('| raw category answer match | n/a | ' + ' | '.join(rawm[p[:2]] for p in P[1:]) + ' |')
    L += ['', '## Per assessment (final category ✓/✗; [raw category]; p(incident))', '', '| Assessment | Expected | P0 | P1 | P2 | P3 | P4 |', '|---|---|---|---|---|---|---|']
    for label, x in ev.assessments(results['p0']):
        cells = [f"{x['predicted_category']} {'✓' if x['category_match'] else '✗'}"]
        for p in ('p1v2', 'p2v2', 'p3', 'p4'):
            y = dict(ev.assessments(results[p]))[label]
            r = raw[p[:2]][label]
            cells.append(f"{y['predicted_category']} {'✓' if y['category_match'] else '✗'} [{r['raw_category']}] {r['p_incident']:.2f}")
        L.append(f"| {label} | {x['expected_category']} | " + ' | '.join(cells) + ' |')
    L += ['', '## Attention / multi-camera', '', '| Pipeline | Order | top1 | full | same_incident | AB/A/B final category |', '|---|---|---|---|---|---|']
    for p in P:
        a, m = results[p]['ITEM_04'], results[p]['ITEM_07']['multi_camera']
        L.append(f"| {LABEL[p]} | {' > '.join(a['attention_order'])} | {a['top1_correct']} | {a['full_order_correct']} | {m['same_incident_predicted']} | "
                 f"{m['AB_category_correct']}/{m['A_category_correct']}/{m['B_category_correct']} |")
    if cal:
        L += ['', f"Calibration vs reviewer_01 (P0/P1-v1 only): {cal['verdict']} (OPPOSITE {cal['opposite']}/{cal['decisive_comparisons']})."]
    L += ['', 'Note: P1–P3 evidence/temporal text is template-generated from the same CV state; P4 evidence/temporal/uncertainty/reason text is '
          'model-generated from frames, so temporal_hit and overclaim screening are more informative for P4 than for P1–P3.', '']
    return '\n'.join(L)


if __name__ == '__main__':
    main()
