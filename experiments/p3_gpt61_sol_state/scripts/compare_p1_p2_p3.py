"""EVALUATOR ONLY. P1 (Decisions API gpt-6-luna) vs P2 (Clef-Flash) vs P3 (GPT-6.1 Sol, high) on byte-identical compact
states and the same semantics, all presented through common-adapter-v2 (P1/P2 v1 raw records kept separately).
Writes evaluation/p1_vs_p2_vs_p3.md and .csv. Latency = one primary call per item (NOT a controlled repeated benchmark)."""
import csv
import json
import statistics
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
BENCH = PROJECT / 'benchmark_v1' / 'results'
EVAL = EXP / 'evaluation'
ITEMS = [f'ITEM_{i:02d}' for i in range(1, 8)]
DIRS = {'P1': 'p1_decisions', 'P2': 'p2_clef_flash', 'P3': 'p3_gpt61_sol_state'}
MODEL = {'P1': 'OpenAI Decisions API gpt-6-luna', 'P2': 'Cloudflare Clef-Flash', 'P3': 'GPT-6.1 Sol (Responses, high)'}
PROB_SRC = {'P1': 'native Decisions API probability', 'P2': 'native Clef decision probability', 'P3': 'model-generated structured estimate'}
EVK = {'P1': 'p1v2', 'P2': 'p2v2', 'P3': 'p3'}


def jl(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def rc(m, item):
    return jl(BENCH / DIRS[m] / f'run_{item}.json')['runtime_config']


def lat(r):
    return r['latency'].get('request_total_ms', r['latency'].get('decision_api_latency_ms'))


def units(item, ds):
    return [(f'{item}/{c}', d) for c, d in ds['per_camera'].items()] if item == 'ITEM_04' else [(item, ds)]


def dist(xs):
    xs = sorted(xs)
    return f'{xs[0]:.2f} / {statistics.median(xs):.2f} / {xs[-1]:.2f}'


def main():
    ev = jl(EVAL / 'auto_eval_results.json')
    with (EXP / 'logs' / 'process_audit_log.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'event': 'compare_p1_p2_p3', 'script': 'compare_p1_p2_p3.py'}) + '\n')
    S = ev['summary']
    raw = ev['raw_category_view']
    rows = []
    for item in ITEMS:
        per = {m: dict(units(item, rc(m, item)['decision_summary'])) for m in DIRS}
        for label in per['P1']:
            row = {'assessment': label}
            for m in DIRS:
                d = per[m][label]
                fin = ev['per_item'][EVK[m]][item]
                fin = fin['per_camera'][label.split('/')[1]] if item == 'ITEM_04' else fin
                row.update({f'{m}_p_incident': d['p_incident'], f'{m}_raw_category': d['category'], f'{m}_category_conf': d['category_confidence'],
                            f'{m}_final_event_type': fin['event_type'], f'{m}_is_incident': d['is_incident'],
                            **{f'{m}_{k}': d['risk'][k] for k in ('severity', 'imminence', 'exposure', 'persistence')},
                            f'{m}_priority': d['priority_score'], f'{m}_confidence': d['confidence'], f'{m}_p_human_review': d['p_human_review'],
                            f'{m}_human_review': d['human_review_required']})
            row['expected'] = raw['p1']['rows'][label]['expected']
            rows.append(row)
    with (EVAL / 'p1_vs_p2_vs_p3.csv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    agg = {}
    for m in DIRS:
        rs = [rc(m, i) for i in ITEMS]
        ls, cs = [lat(r) for r in rs], [r['external_api_cost_usd'] for r in rs]
        agg[m] = {'lat': (statistics.median(ls), min(ls), max(ls)), 'cost_total': sum(cs), 'cost_mean': sum(cs) / len(cs),
                  'in': sum(r['usage']['input_tokens'] for r in rs), 'out': sum(r['usage'].get('output_tokens') or 0 for r in rs),
                  'retries': sum(r['retry_count'] for r in rs)}
    mc = {m: ev['per_item'][EVK[m]]['ITEM_07']['multi_camera'] for m in DIRS}
    ds7 = {m: rc(m, 'ITEM_07')['decision_summary'] for m in DIRS}
    att = {m: ev['per_item'][EVK[m]]['ITEM_04'] for m in DIRS}
    pri4 = {m: {c: d['priority_score'] for c, d in rc(m, 'ITEM_04')['decision_summary']['per_camera'].items()} for m in DIRS}
    anchored = ['ITEM_01', 'ITEM_04/CAM_01']
    L = ['# P1 vs P2 vs P3 — same frames, CV, state and semantics; different decision model', '',
         'All three decision models received the byte-identical compact-decision-state-v1 text and the same frozen P1 question semantics. '
         'Final predictions are compared through the frozen common-adapter-v2 (P1-v1/P2-v1 raw records unchanged). '
         'Automatic diagnostics only (x/N); not % accuracy, not human rubric scores.', '',
         '| | P1 | P2 | P3 |', '|---|---|---|---|',
         '| Decision model | ' + ' | '.join(MODEL[m] for m in DIRS) + ' |',
         '| Probability source | ' + ' | '.join(PROB_SRC[m] for m in DIRS) + ' |', '',
         '## Category behavior', '', '| | P1 | P2 | P3 |', '|---|---|---|---|',
         f"| Raw category answer match (9) | {raw['p1']['raw_category_match']} | {raw['p2']['raw_category_match']} | {raw['p3']['raw_category_match']} |",
         f"| Final event category match (adapter-v2, 9) | {S['p1v2']['category_match']} | {S['p2v2']['category_match']} | {S['p3']['category_match']} |",
         '| Raw categories used | ' + ' | '.join(', '.join(f'{k}×{v}' for k, v in sorted(
             __import__('collections').Counter(r[f'{m}_raw_category'] for r in rows).items())) for m in DIRS) + ' |', '',
         '## Incident detection', '',
         '| | P1 | P2 | P3 |', '|---|---|---|---|',
         f"| HV-anchored incident decisions (ITEM_01, ITEM_04/CAM_01) | {S['p1v2']['incident_decision_scored']} | {S['p2v2']['incident_decision_scored']} | {S['p3']['incident_decision_scored']} |",
         '| p(incident) on anchored falls | ' + ' | '.join(', '.join(f"{r[f'{m}_p_incident']:.2f}" for r in rows if r['assessment'] in anchored) for m in DIRS) + ' |',
         '| is_incident=true count (9) | ' + ' | '.join(str(sum(r[f'{m}_is_incident'] for r in rows)) for m in DIRS) + ' |',
         '| p(incident) min / median / max | ' + ' | '.join(dist([r[f'{m}_p_incident'] for r in rows]) for m in DIRS) + ' |', '',
         '## Risk score distributions (min / median / max over 9 assessments, 0-1)', '',
         '| Risk | P1 | P2 | P3 |', '|---|---|---|---|']
    L += [f'| {k} | ' + ' | '.join(dist([r[f'{m}_{k}'] for r in rows]) for m in DIRS) + ' |' for k in ('severity', 'imminence', 'exposure', 'persistence', 'priority', 'confidence')]
    L += ['', '## Attention ranking (ITEM_04; reference CAM_01 > CAM_02 > CAM_03, 477 project-defined)', '', '| | P1 | P2 | P3 |', '|---|---|---|---|',
          '| Order | ' + ' | '.join(' > '.join(att[m]['attention_order']) for m in DIRS) + ' |',
          '| Top-1 / full order | ' + ' | '.join(f"{att[m]['top1_correct']} / {att[m]['full_order_correct']}" for m in DIRS) + ' |',
          '| Priority CAM_01 / CAM_02 / CAM_03 | ' + ' | '.join(' / '.join(f'{pri4[m][c]:.3f}' for c in ('CAM_01', 'CAM_02', 'CAM_03')) for m in DIRS) + ' |',
          '', '## Multi-camera (ITEM_07; same-incident reference = true)', '', '| | P1 | P2 | P3 |', '|---|---|---|---|',
          '| p(same_incident) → same_incident | ' + ' | '.join(f"{ds7[m]['p_same_incident']:.2f} → {ds7[m]['same_incident']}" for m in DIRS) + ' |',
          '| p(second_view_adds) → second_view_adds | ' + ' | '.join(f"{ds7[m]['p_second_view_adds']:.2f} → {ds7[m]['second_view_adds']}" for m in DIRS) + ' |',
          '| multiview_value (0-1) | ' + ' | '.join(f"{ds7[m]['multiview_value']:.2f}" for m in DIRS) + ' |',
          '| AB / A / B final category correct | ' + ' | '.join(f"{mc[m]['AB_category_correct']} / {mc[m]['A_category_correct']} / {mc[m]['B_category_correct']}" for m in DIRS) + ' |',
          '', '## Consistency, review, overclaims', '', '| | P1 | P2 | P3 |', '|---|---|---|---|',
          f"| Internal contradictions: v1 raw → adapter-v2 | {S['p1']['internal_contradiction_count']} → {S['p1v2']['internal_contradiction_count']} | "
          f"{S['p2']['internal_contradiction_count']} → {S['p2v2']['internal_contradiction_count']} | n/a → {S['p3']['internal_contradiction_count']} |",
          '| human_review_required | ' + ' | '.join(S[EVK[m]]['human_review_required_count'] for m in DIRS) + ' |',
          '| p(human_review) min / median / max | ' + ' | '.join(dist([r[f'{m}_p_human_review'] for r in rows]) for m in DIRS) + ' |',
          '| Very low confidence (<0.4) | ' + ' | '.join(str(S[EVK[m]]['very_low_confidence_count']) for m in DIRS) + ' |',
          '| Suspected overclaims | ' + ' | '.join(str(S[EVK[m]]['suspected_overclaim_count']) for m in DIRS) + ' |',
          '', '## API cost and observed primary latency', '', '| | P1 | P2 | P3 |', '|---|---|---|---|',
          '| Theoretical external API cost, 7 items | ' + ' | '.join(f"${agg[m]['cost_total']:.6f}" for m in DIRS) + ' |',
          '| Mean cost per candidate | ' + ' | '.join(f"${agg[m]['cost_mean']:.6f}" for m in DIRS) + ' |',
          '| Primary latency median (min–max), ms | ' + ' | '.join(f"{agg[m]['lat'][0]:.0f} ({agg[m]['lat'][1]:.0f}–{agg[m]['lat'][2]:.0f})" for m in DIRS) + ' |',
          '| Input / output tokens, 7 items (provider tokenizers) | ' + ' | '.join(f"{agg[m]['in']} / {agg[m]['out']}" for m in DIRS) + ' |',
          '| Retries | ' + ' | '.join(str(agg[m]['retries']) for m in DIRS) + ' |', '',
          'Cost = provider-reported usage × official rates (P1 $0.10/M input; P2 $0.09/M input, actual billing likely $0 under the free Neuron allocation; '
          'P3 $2/M input, $0.10/M cached, $2.50/M cache write, $10/M output incl. reasoning). '
          '**Latency is one primary call per item at different times — NOT a controlled repeated latency benchmark** (planned after P4). '
          'No winner is declared from cost alone.', '',
          '## Per assessment', '', '| Assessment | Expected | P1 raw cat (p_inc) | P2 raw cat (p_inc) | P3 raw cat (p_inc) | P1 / P2 / P3 final event_type |', '|---|---|---|---|---|---|']
    for r in rows:
        L.append(f"| {r['assessment']} | {r['expected']} | " + ' | '.join(f"{r[f'{m}_raw_category']} ({r[f'{m}_p_incident']:.2f})" for m in DIRS)
                 + ' | ' + ' / '.join(r[f'{m}_final_event_type'] for m in DIRS) + ' |')
    (EVAL / 'p1_vs_p2_vs_p3.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
