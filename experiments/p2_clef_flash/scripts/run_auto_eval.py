"""EVALUATOR ONLY. Automatic evaluation of P0, P1 and P2 with ONE evaluator (same rules for every pipeline).

Order guard: requires freeze/p2_results_manifest.json + evaluation/normalized_ground_truth_v1.json, verifies every
frozen P2 hash, and hashes P0/P1/P2 result files before/after to prove they are not modified.
Outputs (evaluation/): auto_eval_results.json, auto_eval_summary.md, human_audit_queue.md.
Auto metrics are NOT human rubric scores and are never written into human_grading. Counts are reported as x/N,
never as % accuracy. Overclaim keyword hits are *suspected* flags only.
"""
import _bootstrap  # noqa: F401
import datetime
import json
import re
import sys

from process_log import log_event
from utils import BENCH_ROOT, EVAL_DIR, EXP_ROOT, FREEZE_DIR, ITEM_IDS, PROJECT_ROOT, load_json, sha256_file, write_json

PIPELINES = {'p0': 'p0_cv_only', 'p1': 'p1_decisions', 'p2': 'p2_clef_flash'}
HUMAN = PROJECT_ROOT / 'human_grading' / 'p0_vs_p1_v1' / 'output' / 'reviewer_01_revealed.json'
LOW_CONF = 0.4
INCIDENT_CATS = ('possible_fall_or_person_down', 'possible_physical_conflict')

# event_type text -> normalized category (applies identically to P0 free text and P1/P2 template text)
CATEGORY_RULES = [
    ('uncertain', r'^uncertain'),
    ('no_clear_incident', r'no clear incident|no incident-like'),
    ('possible_fall_or_person_down', r'fall|person-down|person down|low or horizontal posture'),
    ('possible_physical_conflict', r'physical conflict|fight|conflict'),
    ('possible_scene_or_boundary_entry', r'scene entry|boundary entry|\bentry\b'),
    ('other_safety_relevant', r'.'),
]
OVERCLAIM = {
    'medical diagnosis': r'\b(faint\w*|unconscious\w*|seizure|stroke|heart attack|cardiac|injur\w*|diagnos\w*|syncope)\b',
    'criminal intent': r'\b(criminal|crime|intent\w*|burglar\w*|thie\w+|theft|assault\w*|malicious|illegal\w*|unlawful\w*)\b',
    'authorization': r'\b(unauthori[sz]ed|authori[sz]\w*|trespass\w*|intrud\w*|intrusion|break[- ]?in|permission)\b',
    'identity': r'\b(identif\w*|identity|recogni[sz]\w*|same person|same individual)\b',
    'weapon': r'\b(weapon\w*|knife|knives|gun|firearm|pistol|blade)\b',
    'cross-camera identity': r'(same person across|identity across|cross-camera identity|same individual in both|synchroni[sz]\w*|\bsynced\b)',
}
NEGATION = r"\b(not|cannot|can't|unknown|unavailable|no|never|without|unconfirmed|undetermined|uncertain|neither|nor)\b"


def category(event_type):
    t = event_type.lower()
    return next(c for c, rx in CATEGORY_RULES if re.search(rx, t))


def texts(pred):
    out = []
    for k in ('event_type', 'reason', 'temporal_summary', 'cross_camera_summary'):
        if isinstance(pred.get(k), str):
            out.append((k, pred[k]))
    for k in ('uncertainties', 'additional_information_from_second_view'):
        out += [(k, x) for x in pred.get(k) or []]
    out += [('observations', o['description']) for o in pred.get('observations') or []]
    for cam, obs in (pred.get('camera_evidence') or {}).items():
        out += [(f'camera_evidence.{cam}', o['description']) for o in obs]
    return out


def screen_overclaims(pred):
    suspected, negated = [], 0
    for field, txt in texts(pred):
        for sent in re.split(r'(?<=[.;])\s+', txt):
            for typ, rx in OVERCLAIM.items():
                m = re.search(rx, sent, re.I)
                if not m:
                    continue
                if re.search(NEGATION, sent, re.I):
                    negated += 1
                    continue
                suspected.append({'type': typ, 'field': field, 'quote': sent.strip()[:220], 'match': m.group(0)})
    return suspected, negated


def assess(pred, gt_cat, anchor):
    cat = category(pred['event_type'])
    contradictions = []
    if cat in INCIDENT_CATS and not pred['is_incident']:
        contradictions.append(f"is_incident=false but event_type='{pred['event_type']}'")
    if cat == 'no_clear_incident' and pred['is_incident']:
        contradictions.append(f"is_incident=true but event_type='{pred['event_type']}'")
    if pred['confidence'] < LOW_CONF and not pred['human_review_required']:
        contradictions.append(f"confidence {pred['confidence']} < {LOW_CONF} but human_review_required=false")
    sus, neg = screen_overclaims(pred)
    a = anchor or {}
    return {
        'event_type': pred['event_type'], 'predicted_category': cat, 'expected_category': gt_cat,
        'category_match': cat == gt_cat,
        'is_incident': pred['is_incident'],
        'incident_decision': 'not_scored' if a.get('value') is None else ('correct' if pred['is_incident'] == a['value'] else 'incorrect'),
        'confidence': pred['confidence'], 'very_low_confidence': pred['confidence'] < LOW_CONF,
        'human_review_required': pred['human_review_required'],
        'internal_contradictions': contradictions, 'suspected_overclaims': sus, 'negated_keyword_mentions': neg,
    }


def temporal(pred, tref):
    if not tref or tref.get('status') != 'scorable':
        return {'status': (tref or {}).get('status', 'requires_human_audit')}
    lo, hi = tref['clip_interval_sec']
    tol = tref['tolerance_sec']
    ts = [o['timestamp_sec'] for o in pred.get('observations') or []]
    hits = [t for t in ts if lo - tol <= t <= hi + tol]
    return {'status': 'scored', 'temporal_hit': bool(hits), 'hit_timestamps': hits, 'observation_timestamps': ts,
            'reference_interval_sec': [lo, hi], 'tolerance_sec': tol}


def evaluate(pipe, gt):
    res = {}
    for item in ITEM_IDS:
        r = load_json(BENCH_ROOT / 'results' / PIPELINES[pipe] / f'run_{item}.json')
        p, g = r['prediction'], gt['items'][item]
        if item == 'ITEM_04':
            per = {a['camera']: assess(a['assessment'], g['per_camera'][a['camera']]['normalized_event_target'],
                                       g['per_camera'][a['camera']]['incident_presence_anchor']) for a in p['assessments']}
            order = [q['camera'] for q in sorted(p['attention_queue'], key=lambda q: q['rank'])]
            res[item] = {'task': 'attention', 'per_camera': per, 'attention_order': order, 'reference_order': g['reference_order'],
                         'reference_provenance': g['reference_provenance'],
                         'top1_correct': order[0] == g['reference_order'][0], 'full_order_correct': order == g['reference_order']}
            continue
        e = assess(p, g['normalized_event_target'], g['incident_presence_anchor'])
        e['temporal'] = temporal(p, g.get('temporal_reference'))
        e['ambiguous_case'] = g['ambiguous_case']
        e['task'] = g['task']
        if item == 'ITEM_07':
            sus_cc = [s for s in e['suspected_overclaims'] if s['type'] == 'cross-camera identity']
            e['multi_camera'] = {
                'same_incident_predicted': p['same_incident'], 'same_incident_reference': g['same_incident_reference'],
                'same_incident_correct': p['same_incident'] == g['same_incident_reference'],
                'camera_count_ok': len(p['camera_evidence']) == g['expected_camera_count'],
                'second_view_evidence_present': all(len(v) > 0 for v in p['camera_evidence'].values()),
                'additional_information_from_second_view_present': bool(p.get('additional_information_from_second_view')),
                'cross_camera_sync_or_identity_assertions': sus_cc,
            }
        res[item] = e
    # multi-view derived metrics (A=ITEM_05, B=ITEM_06, AB=ITEM_07)
    a, b, ab = res['ITEM_05'], res['ITEM_06'], res['ITEM_07']
    best = max(a['confidence'], b['confidence'])
    ab['multi_camera'].update({
        'AB_category_correct': ab['category_match'], 'A_category_correct': a['category_match'], 'B_category_correct': b['category_match'],
        'AB_confidence_minus_best_single': round(ab['confidence'] - best, 4),
        'AB_uncertainty_improved': ab['confidence'] > best,
        'AB_uncertainty_improved_definition': 'model-reported confidence(AB) > max(confidence(A), confidence(B)); a confidence statement, not correctness',
        'multiview_increment_rubric': 'not auto-generated (requires 0-8 human rubric)',
    })
    return res


def assessments(res):
    """Flatten to (label, assessment) for single-assessment metrics; ITEM_04 counts per camera."""
    out = []
    for item, e in res.items():
        if item == 'ITEM_04':
            out += [(f'ITEM_04/{c}', x) for c, x in e['per_camera'].items()]
        else:
            out.append((item, e))
    return out


def summarize(res):
    a = assessments(res)
    scored_inc = [x for _, x in a if x['incident_decision'] != 'not_scored']
    return {
        'category_match': f"{sum(x['category_match'] for _, x in a)}/{len(a)}",
        'category_match_items': [k for k, x in a if x['category_match']],
        'incident_decision_scored': f"{sum(x['incident_decision'] == 'correct' for x in scored_inc)}/{len(scored_inc)}",
        'incident_decision_not_scored': sum(x['incident_decision'] == 'not_scored' for _, x in a),
        'attention_top1_correct': res['ITEM_04']['top1_correct'], 'attention_full_order_correct': res['ITEM_04']['full_order_correct'],
        'same_incident_correct': res['ITEM_07']['multi_camera']['same_incident_correct'],
        'AB_A_B_category_correct': [res['ITEM_07']['multi_camera'][k] for k in ('AB_category_correct', 'A_category_correct', 'B_category_correct')],
        'AB_uncertainty_improved': res['ITEM_07']['multi_camera']['AB_uncertainty_improved'],
        'temporal_hit_ITEM_03': res['ITEM_03']['temporal'].get('temporal_hit'),
        'internal_contradiction_count': sum(len(x['internal_contradictions']) for _, x in a),
        'suspected_overclaim_count': sum(len(x['suspected_overclaims']) for _, x in a),
        'very_low_confidence_count': sum(x['very_low_confidence'] for _, x in a),
        'human_review_required_count': f"{sum(x['human_review_required'] for _, x in a)}/{len(a)}",
    }


def calibration(results):
    """Auto event-category match vs existing human event_understanding (0/1/2) for P0/P1. Not a conversion."""
    if not HUMAN.exists():
        return None
    h = load_json(HUMAN)['systems']
    rows, ranking = [], []
    for pipe in ('p0', 'p1'):
        for item in ITEM_IDS:
            g = h[pipe].get(item)
            if not g:
                continue
            if item == 'ITEM_04':
                for cam, x in results[pipe][item]['per_camera'].items():
                    rows.append((pipe, f'{item}/{cam}', x['category_match'], g['camera_helper']['event_understanding'][cam]))
                hr = g.get('ranking', {})
                ranking.append({'pipeline': pipe, 'auto_top1': results[pipe][item]['top1_correct'], 'human_top1': hr.get('top1_correct'),
                                'auto_full': results[pipe][item]['full_order_correct'], 'human_full': hr.get('full_order_correct')})
            else:
                rows.append((pipe, item, results[pipe][item]['category_match'], g['event_understanding']))
    out = []
    for pipe, k, match, hs in rows:
        if hs is None:
            rel = 'no human score'
        elif (match and hs == 2) or (not match and hs == 0):
            rel = 'agree'
        elif hs == 1:
            rel = 'partial (human 1)'
        else:
            rel = 'OPPOSITE'
        out.append({'pipeline': pipe, 'assessment': k, 'auto_category_match': match, 'human_event_understanding': hs, 'relation': rel})
    n_opp = sum(r['relation'] == 'OPPOSITE' for r in out)
    n_cmp = sum(r['relation'] in ('agree', 'OPPOSITE') for r in out)
    rank_agree = all((r['auto_top1'] == (r['human_top1'] == 'yes')) and (r['auto_full'] == (r['human_full'] == 'yes')) for r in ranking)
    return {'rows': out, 'ranking': ranking, 'ranking_auto_human_agree': rank_agree,
            'opposite': n_opp, 'decisive_comparisons': n_cmp,
            'partial': sum(r['relation'].startswith('partial') for r in out),
            'verdict': ('auto event-category metric NOT usable as official quality metric (many opposite cases)'
                        if n_cmp and n_opp / n_cmp > 0.25 else
                        'BORDERLINE: below the opposite-case threshold but close to it; diagnostic use only, not an official quality metric'
                        if n_cmp and n_opp / n_cmp > 0.15 else
                        'auto event-category metric broadly consistent with human event scores on decisive cases (diagnostic use only)'),
            'rule': 'agree: match&human=2 or mismatch&human=0; OPPOSITE: match&human=0 or mismatch&human=2; human=1 is partial. '
                    'Verdict threshold: OPPOSITE > 25% of decisive comparisons => not official.'}


def audit_queue(results, gt, human_graded):
    rows = []
    p1, p2 = results['p1'], results['p2']
    for pipe, res in results.items():
        for label, x in assessments(res):
            item = label.split('/')[0]
            g = gt['items'][item]
            expected = x['expected_category']
            why = []
            if g.get('ambiguous_case'):
                why.append('ambiguous benchmark case')
            if not x['category_match']:
                why.append('normalized category mismatch')
            why += [f'internal contradiction: {c}' for c in x['internal_contradictions']]
            why += [f"suspected overclaim ({s['type']})" for s in x['suspected_overclaims']]
            if item == 'ITEM_07' and x.get('multi_camera', {}).get('cross_camera_sync_or_identity_assertions'):
                why.append('cross-camera sync/identity assertion')
            if x['very_low_confidence']:
                why.append(f"very low confidence ({x['confidence']})")
            if pipe in ('p1', 'p2'):
                o = p2 if pipe == 'p1' else p1
                y = o['ITEM_04']['per_camera'][label.split('/')[1]] if item == 'ITEM_04' else o[item]
                if y['predicted_category'] != x['predicted_category'] or y['is_incident'] != x['is_incident']:
                    why.append('P1/P2 large disagreement (category or is_incident differs)')
            if not why:
                continue
            graded = human_graded.get(pipe, False)
            full = (not graded) and (g.get('ambiguous_case') or not x['category_match'])
            quote = '; '.join(f"\"{s['quote']}\"" for s in x['suspected_overclaims'][:2]) or '-'
            rows.append({'item': label, 'pipeline': pipe, 'why': why, 'prediction': f"{x['event_type']} · is_incident={x['is_incident']} · conf={x['confidence']}",
                         'expected': expected + (' (observable only; authorization/intent not GT)' if g.get('ambiguous_case') else ''),
                         'quote': quote, 'full_video_review': full,
                         'existing_human_grade': graded})
    return rows


def md_queue(rows):
    L = ['# Human audit queue (automatic evaluation v1)', '',
         'Only flagged assessments are listed. **FULL VIDEO** = the clip must be re-watched (no existing human grade and the case is '
         'ambiguous or the category mismatches). Other rows need only the quoted text / decision checked. Suspected overclaims are keyword '
         'flags, not confirmed violations. P0/P1 rows already have reviewer_01 grades; they are listed for completeness.', '',
         f"- assessments flagged: {len(rows)}; requiring full video review: {sum(r['full_video_review'] for r in rows)}", '',
         '| ITEM | Pipeline | Review | Why flagged | Model prediction | Expected observable target | Suspicious quote |',
         '|---|---|---|---|---|---|---|']
    order = {'p2': 0, 'p1': 1, 'p0': 2}
    for r in sorted(rows, key=lambda r: (not r['full_video_review'], order[r['pipeline']], r['item'])):
        L.append(f"| {r['item']} | {r['pipeline'].upper()} | {'**FULL VIDEO**' if r['full_video_review'] else ('graded' if r['existing_human_grade'] else 'text check')} | "
                 f"{'; '.join(r['why'])} | {r['prediction']} | {r['expected']} | {r['quote']} |")
    return '\n'.join(L) + '\n'


def md_summary(results, summ, cal, gt):
    L = ['# Automatic evaluation summary (auto-eval-v1)', '',
         f"Generated {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}. One evaluator, identical rules for P0, P1, P2. "
         'These are automatic diagnostic metrics, **not** the 0-8 human rubric and **not** % accuracy (5 cases / 7 conditions).', '',
         '## Rules', '',
         '- Category: prediction `event_type` text -> normalized category (same regex table for every pipeline) vs `normalized_event_target`. ITEM_04 is counted per camera (9 assessments total).',
         '- Incident decision: scored only where a human-verified incident-presence anchor exists (ITEM_01, ITEM_04/CAM_01); others `not_scored`.',
         '- Temporal: only ITEM_03 has a human-verified clip-relative transition (gate crossing ~29-30 s, +/-1 s); all others `requires_human_audit`.',
         '- Attention: CAM_01 > CAM_02 > CAM_03 is a **477 project-defined reference**, not AI Hub ground truth.',
         '- Internal contradiction: (fall/conflict category & is_incident=false) or (no_clear_incident & is_incident=true) or (confidence < 0.4 & no human review).',
         '- Overclaim: keyword screening per sentence; sentences with negation cues are skipped (counted separately). Suspected only.', '',
         '## Per pipeline', '',
         '| Metric | P0 | P1 | P2 |', '|---|---|---|---|']
    for k in summ['p0']:
        if k == 'category_match_items':
            continue
        L.append(f"| {k} | " + ' | '.join(str(summ[p][k]) for p in ('p0', 'p1', 'p2')) + ' |')
    L += ['', '## Per assessment (predicted category; ✓ = matches normalized target)', '', '| Assessment | Expected | P0 | P1 | P2 |', '|---|---|---|---|---|']
    for label, x in assessments(results['p0']):
        item = label.split('/')[0]
        row = []
        for p in ('p0', 'p1', 'p2'):
            y = dict(assessments(results[p]))[label]
            row.append(f"{y['predicted_category']} {'✓' if y['category_match'] else '✗'} (inc={str(y['is_incident']).lower()}, conf={y['confidence']})")
        L.append(f"| {label} | {x['expected_category']}{' (ambiguous)' if gt['items'][item].get('ambiguous_case') else ''} | " + ' | '.join(row) + ' |')
    L += ['', '## Attention (ITEM_04)', '', '| Pipeline | Order | Top-1 | Full order |', '|---|---|---|---|']
    for p in ('p0', 'p1', 'p2'):
        e = results[p]['ITEM_04']
        L.append(f"| {p.upper()} | {' > '.join(e['attention_order'])} | {e['top1_correct']} | {e['full_order_correct']} |")
    L += ['', '## Multi-camera (ITEM_05 A / ITEM_06 B / ITEM_07 AB)', '', '| Pipeline | same_incident (ref true) | camera count ok | 2nd-view info present | AB / A / B category correct | AB conf - best single | AB uncertainty improved |', '|---|---|---|---|---|---|---|']
    for p in ('p0', 'p1', 'p2'):
        m = results[p]['ITEM_07']['multi_camera']
        L.append(f"| {p.upper()} | {m['same_incident_predicted']} ({'✓' if m['same_incident_correct'] else '✗'}) | {m['camera_count_ok']} | {m['additional_information_from_second_view_present']} | "
                 f"{m['AB_category_correct']} / {m['A_category_correct']} / {m['B_category_correct']} | {m['AB_confidence_minus_best_single']} | {m['AB_uncertainty_improved']} |")
    L += ['', 'Multi-view Increment (0-8 rubric) is not auto-generated.', '']
    if cal:
        L += ['## Calibration against existing human grading (reviewer_01, P0/P1)', '',
              f"- decisive comparisons: {cal['decisive_comparisons']}, OPPOSITE: {cal['opposite']}, partial (human=1): {cal['partial']}",
              f"- ranking auto vs human agree: {cal['ranking_auto_human_agree']}",
              f"- verdict: **{cal['verdict']}**", f"- rule: {cal['rule']}", '',
              '| Pipeline | Assessment | Auto category match | Human event (0-2) | Relation |', '|---|---|---|---|---|']
        L += [f"| {r['pipeline'].upper()} | {r['assessment']} | {r['auto_category_match']} | {r['human_event_understanding']} | {r['relation']} |" for r in cal['rows']]
        L += ['', 'Auto category match is never converted into a human score.', '']
    L += ['## Note on evidence/temporal fields', '',
          'P1 and P2 observations, temporal summaries and uncertainties come from the same deterministic templates over the same frozen compact state, '
          'so evidence and temporal metrics are model-independent between P1 and P2; only decision fields (category, is_incident, risk, confidence, '
          'review flag, ranking, multi-camera decisions) differ.', '']
    return '\n'.join(L)


def main():
    man_p = FREEZE_DIR / 'p2_results_manifest.json'
    gt_p = EVAL_DIR / 'normalized_ground_truth_v1.json'
    if not man_p.exists() or not gt_p.exists():
        sys.exit('results must be frozen and GT built first')
    man = load_json(man_p)
    drift = [k for k, h in man['sha256'].items() if sha256_file((BENCH_ROOT if k.startswith('results/') else EXP_ROOT) / k) != h]
    if drift:
        sys.exit(f'frozen P2 outputs changed: {drift}')
    log_event('run_auto_eval', {'phase': 'start'})
    files = [BENCH_ROOT / 'results' / d / f'run_{i}.json' for d in PIPELINES.values() for i in ITEM_IDS]
    before = {str(f): sha256_file(f) for f in files}
    gt = load_json(gt_p)
    results = {p: evaluate(p, gt) for p in PIPELINES}
    summ = {p: summarize(r) for p, r in results.items()}
    cal = calibration(results)
    graded = {'p0': HUMAN.exists(), 'p1': HUMAN.exists(), 'p2': False}
    queue = audit_queue(results, gt, graded)
    after = {str(f): sha256_file(f) for f in files}
    if before != after:
        sys.exit('result files changed during evaluation')
    write_json(EVAL_DIR / 'auto_eval_results.json', {
        'version': 'auto-eval-v1', 'evaluated_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'ground_truth': 'evaluation/normalized_ground_truth_v1.json', 'results_manifest_verified': True,
        'result_files_unchanged_by_evaluator': True, 'summary': summ, 'per_item': results, 'calibration_vs_human': cal,
        'audit_queue': queue, 'note': 'Automatic metrics only; not human rubric scores; not written into human_grading.'})
    (EVAL_DIR / 'auto_eval_summary.md').write_text(md_summary(results, summ, cal, gt), encoding='utf-8')
    (EVAL_DIR / 'human_audit_queue.md').write_text(md_queue(queue), encoding='utf-8')
    log_event('run_auto_eval', {'phase': 'end', 'queue_rows': len(queue)})
    for p in PIPELINES:
        print(p, json.dumps({k: v for k, v in summ[p].items() if k != 'category_match_items'}, ensure_ascii=False))
    if cal:
        print('calibration:', cal['verdict'], f"(opposite {cal['opposite']}/{cal['decisive_comparisons']}, partial {cal['partial']})")
    print('audit queue rows:', len(queue), '| full video:', sum(r['full_video_review'] for r in queue))


if __name__ == '__main__':
    main()
