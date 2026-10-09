"""EVALUATOR ONLY. P1 (OpenAI Decisions API / gpt-6-luna) vs P2 (Cloudflare Clef-Flash) on identical frozen compact states
and identical semantic questions. Writes evaluation/p1_vs_p2.md and evaluation/p1_vs_p2.csv.
Token counts are tokenizer-specific and are shown for reference only; cost/latency/quality are the comparison axes."""
import _bootstrap  # noqa: F401
import csv
import statistics

from process_log import log_event
from utils import BENCH_ROOT, EVAL_DIR, ITEM_IDS, load_json

PIPE = {'P1': 'p1_decisions', 'P2': 'p2_clef_flash'}


def rc(pipe, item):
    return load_json(BENCH_ROOT / 'results' / PIPE[pipe] / f'run_{item}.json')['runtime_config']


def lat(r):
    return r['latency'].get('request_total_ms', r['latency'].get('decision_api_latency_ms'))


def units(item, ds):
    if item == 'ITEM_04':
        return [(f'{item}/{c}', d) for c, d in ds['per_camera'].items()]
    return [(item, ds)]


def f(x, d=3):
    return '' if x is None else (f'{x:.{d}f}' if isinstance(x, float) else str(x))


def main():
    ev = load_json(EVAL_DIR / 'auto_eval_results.json')
    log_event('compare_p1_p2', {'phase': 'start'})
    rows = []
    for item in ITEM_IDS:
        r1, r2 = rc('P1', item), rc('P2', item)
        u1, u2 = dict(units(item, r1['decision_summary'])), dict(units(item, r2['decision_summary']))
        for label in u1:
            d1, d2 = u1[label], u2[label]
            a1 = ev['per_item']['p1'][item]['per_camera'][label.split('/')[1]] if item == 'ITEM_04' else ev['per_item']['p1'][item]
            a2 = ev['per_item']['p2'][item]['per_camera'][label.split('/')[1]] if item == 'ITEM_04' else ev['per_item']['p2'][item]
            row = {'assessment': label, 'expected_category': a1['expected_category']}
            for tag, d, a in (('p1', d1, a1), ('p2', d2, a2)):
                row.update({f'{tag}_p_incident': d['p_incident'], f'{tag}_is_incident': d['is_incident'], f'{tag}_category': d['category'],
                            f'{tag}_category_conf': d['category_confidence'], f'{tag}_category_match': a['category_match'],
                            f'{tag}_severity': d['risk']['severity'], f'{tag}_imminence': d['risk']['imminence'],
                            f'{tag}_priority': d['priority_score'], f'{tag}_confidence': d['confidence'],
                            f'{tag}_p_human_review': d['p_human_review'], f'{tag}_human_review': d['human_review_required'],
                            f'{tag}_contradictions': len(a['internal_contradictions']), f'{tag}_suspected_overclaims': len(a['suspected_overclaims'])})
            first = label == next(iter(u1))
            for tag, r in (('p1', r1), ('p2', r2)):   # request-level values only on the item's first row
                row.update({f'{tag}_request_latency_ms': lat(r) if first else None,
                            f'{tag}_input_tokens': r['usage']['input_tokens'] if first else None,
                            f'{tag}_external_api_cost_usd': r['external_api_cost_usd'] if first else None})
            rows.append(row)
    with (EVAL_DIR / 'p1_vs_p2.csv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    agg = {}
    for tag in ('P1', 'P2'):
        rs = [rc(tag, i) for i in ITEM_IDS]
        ls = [lat(r) for r in rs]
        cs = [r['external_api_cost_usd'] for r in rs]
        agg[tag] = {'lat_median': statistics.median(ls), 'lat_min': min(ls), 'lat_max': max(ls), 'cost_total': sum(cs),
                    'cost_mean': sum(cs) / len(cs), 'tokens_total': sum(r['usage']['input_tokens'] for r in rs),
                    'retries': sum(r['retry_count'] for r in rs)}
    s1, s2 = ev['summary']['p1'], ev['summary']['p2']
    m1, m2 = ev['per_item']['p1']['ITEM_07']['multi_camera'], ev['per_item']['p2']['ITEM_07']['multi_camera']
    o1, o2 = ev['per_item']['p1']['ITEM_04']['attention_order'], ev['per_item']['p2']['ITEM_04']['attention_order']
    agree_cat = sum(r['p1_category'] == r['p2_category'] for r in rows)
    agree_inc = sum(r['p1_is_incident'] == r['p2_is_incident'] for r in rows)
    L = ['# P1 vs P2 — OpenAI Decisions API (gpt-6-luna) vs Cloudflare Clef-Flash', '',
         'Same canonical frames, same cheap CV, same cv-state-v1, **byte-identical compact-decision-state-v1 input**, same semantic questions, '
         'same frozen adapter. Only the decision model differs. One primary request per item for both. Automatic metrics are diagnostic counts (x/N), '
         'not % accuracy and not human rubric scores.', '',
         '## Headline', '',
         '| Axis | P1 (gpt-6-luna) | P2 (Clef-Flash) |', '|---|---|---|',
         f"| Event category match (9 assessments) | {s1['category_match']} | {s2['category_match']} |",
         f"| Incident decision (HV-anchored only) | {s1['incident_decision_scored']} | {s2['incident_decision_scored']} |",
         f"| Attention order (ref CAM_01>CAM_02>CAM_03) | {' > '.join(o1)} (top1 {s1['attention_top1_correct']}, full {s1['attention_full_order_correct']}) | {' > '.join(o2)} (top1 {s2['attention_top1_correct']}, full {s2['attention_full_order_correct']}) |",
         f"| same_incident (ref true) | {m1['same_incident_predicted']} | {m2['same_incident_predicted']} |",
         f"| AB / A / B category correct | {m1['AB_category_correct']} / {m1['A_category_correct']} / {m1['B_category_correct']} | {m2['AB_category_correct']} / {m2['A_category_correct']} / {m2['B_category_correct']} |",
         f"| Internal contradictions | {s1['internal_contradiction_count']} | {s2['internal_contradiction_count']} |",
         f"| Suspected overclaims | {s1['suspected_overclaim_count']} | {s2['suspected_overclaim_count']} |",
         f"| Very low confidence (<0.4) | {s1['very_low_confidence_count']} | {s2['very_low_confidence_count']} |",
         f"| Human review required | {s1['human_review_required_count']} | {s2['human_review_required_count']} |",
         f"| Decision API latency median (min–max), ms | {agg['P1']['lat_median']:.0f} ({agg['P1']['lat_min']:.0f}–{agg['P1']['lat_max']:.0f}) | {agg['P2']['lat_median']:.0f} ({agg['P2']['lat_min']:.0f}–{agg['P2']['lat_max']:.0f}) |",
         f"| Theoretical external API cost, 7 items | ${agg['P1']['cost_total']:.7f} | ${agg['P2']['cost_total']:.7f} |",
         f"| Mean cost per candidate (item) | ${agg['P1']['cost_mean']:.7f} | ${agg['P2']['cost_mean']:.7f} |",
         f"| Input tokens, 7 items (provider tokenizer; not comparable) | {agg['P1']['tokens_total']} | {agg['P2']['tokens_total']} |",
         f"| Retries | {agg['P1']['retries']} | {agg['P2']['retries']} |", '',
         f"P1/P2 agree on category in {agree_cat}/{len(rows)} assessments and on is_incident in {agree_inc}/{len(rows)}.", '',
         'Latency: single primary call per item on each provider, measured at different times from the same client; not a controlled repeated benchmark. '
         'Cost: published input-token rates × provider-reported input tokens (P1 $0.10/M, P2 $0.09/M); actual P2 billing may be $0 under the Workers AI daily free Neuron allocation.', '',
         '## Per assessment', '',
         '| Assessment | Expected | P1 category (conf) | P2 category (conf) | P1 p(inc) → is_incident | P2 p(inc) → is_incident | P1 sev / imm | P2 sev / imm | P1 review | P2 review |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        mk = lambda t: '✓' if r[f'{t}_category_match'] else '✗'
        L.append(f"| {r['assessment']} | {r['expected_category']} | {r['p1_category']} {mk('p1')} ({f(r['p1_category_conf'], 2)}) | {r['p2_category']} {mk('p2')} ({f(r['p2_category_conf'], 2)}) | "
                 f"{f(r['p1_p_incident'], 2)} → {r['p1_is_incident']} | {f(r['p2_p_incident'], 2)} → {r['p2_is_incident']} | "
                 f"{f(r['p1_severity'], 2)} / {f(r['p1_imminence'], 2)} | {f(r['p2_severity'], 2)} / {f(r['p2_imminence'], 2)} | {r['p1_human_review']} | {r['p2_human_review']} |")
    L += ['', '## Per request (latency / tokens / cost)', '', '| Item | P1 ms | P2 ms | P1 input tokens | P2 input tokens | P1 cost USD | P2 cost USD |', '|---|---|---|---|---|---|---|']
    for i in ITEM_IDS:
        a, b = rc('P1', i), rc('P2', i)
        L.append(f"| {i} | {lat(a):.0f} | {lat(b):.0f} | {a['usage']['input_tokens']} | {b['usage']['input_tokens']} | {a['external_api_cost_usd']:.7f} | {b['external_api_cost_usd']:.7f} |")
    L += ['', '## Notes', '',
          '- The frozen P1-v1 adapter has no category/is_incident reconciliation; both runs keep it (fix deferred to common-adapter-v2 for both).',
          '- Evidence/temporal/uncertainty text is template-generated from the same compact state, so it is identical in structure for P1 and P2.',
          '- Calibration of the auto event-category metric vs reviewer_01 is borderline (see auto_eval_summary.md); treat quality rows as diagnostic.', '']
    (EVAL_DIR / 'p1_vs_p2.md').write_text('\n'.join(L), encoding='utf-8')
    log_event('compare_p1_p2', {'phase': 'end'})
    print('\n'.join(L[:24]))


if __name__ == '__main__':
    main()
