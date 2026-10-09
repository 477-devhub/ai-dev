"""EVALUATOR ONLY. P0..P4 comparison incl. the dedicated P3 (state) vs P4 (vision) ablation table.
Reads evaluation/auto_eval_results.json (after result freeze) + runtime configs. Writes evaluation/p0_to_p4_comparison.md/.csv.
No accuracy percentages; latency caveat: P4 = full visual path, P1-P3 = cached-state decision path."""
import csv
import json
import statistics
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
PROJECT = EXP.parents[1]
RES = PROJECT / 'benchmark_v1' / 'results'
EVAL = EXP / 'evaluation'
ITEMS = [f'ITEM_{i:02d}' for i in range(1, 8)]
DIRS = {'P1': 'p1_decisions', 'P2': 'p2_clef_flash', 'P3': 'p3_gpt61_sol_state', 'P4': 'p4_gpt61_sol_vision'}
EVK = {'P0': 'p0', 'P1': 'p1v2', 'P2': 'p2v2', 'P3': 'p3', 'P4': 'p4'}
RAWK = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4'}
NAME = {'P0': 'P0 Cheap CV rules', 'P1': 'P1 Decisions (gpt-6-luna)', 'P2': 'P2 Clef-Flash', 'P3': 'P3 Sol State', 'P4': 'P4 Sol Vision'}
ENTRY_ITEMS = ['ITEM_02', 'ITEM_03', 'ITEM_04/CAM_03']
CONFLICT_ITEMS = ['ITEM_04/CAM_02', 'ITEM_05', 'ITEM_06', 'ITEM_07']
FALL_ITEMS = ['ITEM_01', 'ITEM_04/CAM_01']


def jl(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def rc(m, item):
    return jl(RES / DIRS[m] / f'run_{item}.json')['runtime_config']


def lat(m, r):
    L = r['latency']
    return L['full_pipeline_ms'] if m == 'P4' else L.get('request_total_ms', L.get('decision_api_latency_ms'))


def main():
    ev = jl(EVAL / 'auto_eval_results.json')
    with (EXP / 'logs' / 'process_audit_log.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'event': 'compare_p0_p4', 'script': 'compare_p0_p4.py'}) + '\n')
    S, raw, per = ev['summary'], ev['raw_rows'], ev['per_item']

    def fin(m, label):
        item = label.split('/')[0]
        x = per[EVK[m]][item]
        return x['per_camera'][label.split('/')[1]] if item == 'ITEM_04' else x

    def cell(m, label):
        f = fin(m, label)
        if m == 'P0':
            return f"{f['predicted_category']} {'✓' if f['category_match'] else '✗'}"
        r = raw[RAWK[m]][label]
        return f"{r['raw_category']} p={r['p_incident']:.2f} → {f['predicted_category']} {'✓' if f['category_match'] else '✗'}"

    labels = list(raw['p1'])
    rows = []
    for label in labels:
        row = {'assessment': label, 'expected': raw['p1'][label]['expected']}
        for m in EVK:
            f = fin(m, label)
            row[f'{m}_final_category'] = f['predicted_category']
            row[f'{m}_final_match'] = f['category_match']
            if m != 'P0':
                r = raw[RAWK[m]][label]
                row.update({f'{m}_raw_category': r['raw_category'], f'{m}_p_incident': r['p_incident'], f'{m}_raw_match': r['raw_category_match'],
                            f'{m}_confidence': r['confidence']})
        rows.append(row)
    with (EVAL / 'p0_to_p4_comparison.csv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    cost, latv = {'P0': None}, {}
    for m in DIRS:
        rs = [rc(m, i) for i in ITEMS]
        c = [r['external_api_cost_usd'] for r in rs]
        cost[m] = (sum(c), sum(c) / len(c))
        ls = [lat(m, r) for r in rs]
        latv[m] = (statistics.median(ls), min(ls), max(ls))
    mc = {m: per[EVK[m]]['ITEM_07']['multi_camera'] for m in EVK}
    att = {m: per[EVK[m]]['ITEM_04'] for m in EVK}
    ds7 = {m: rc(m, 'ITEM_07')['decision_summary'] for m in DIRS}
    p4lat = [rc('P4', i)['latency'] for i in ITEMS]

    def count(m, lst, key='category_match'):
        return f"{sum(fin(m, l)[key] for l in lst)}/{len(lst)}"

    def rawcount(m, lst):
        return f"{sum(raw[RAWK[m]][l]['raw_category_match'] for l in lst)}/{len(lst)}"

    L = ['# P0 → P4 comparison (477-reasoning-v1)', '',
         'Same canonical frames for every pipeline. P1–P3: same cheap CV → byte-identical compact state → different decision model. '
         'P4: GPT-6.1 Sol sees the 64 canonical frames directly (no CV state). P1–P4 final predictions via frozen common-adapter-v2; '
         'P1/P2-v1 raw records unchanged. Diagnostic counts only (x/N): **not % accuracy** (5 cases / 7 conditions).', '',
         '## Overview', '', '| | ' + ' | '.join(NAME[m] for m in EVK) + ' |', '|---|' + '---|' * 5,
         '| Final category match (9) | ' + ' | '.join(S[EVK[m]]['category_match'] for m in EVK) + ' |',
         '| Raw category answer match (9) | n/a | ' + ' | '.join(ev['raw_category_match'][RAWK[m]] for m in DIRS) + ' |',
         '| Anchored incidents (2) | ' + ' | '.join(S[EVK[m]]['incident_decision_scored'] for m in EVK) + ' |',
         '| Attention top-1 / full | ' + ' | '.join(f"{att[m]['top1_correct']} / {att[m]['full_order_correct']}" for m in EVK) + ' |',
         '| same_incident (ref true) | ' + ' | '.join(str(mc[m]['same_incident_predicted']) for m in EVK) + ' |',
         '| AB / A / B final category | ' + ' | '.join(f"{mc[m]['AB_category_correct']}/{mc[m]['A_category_correct']}/{mc[m]['B_category_correct']}" for m in EVK) + ' |',
         '| ITEM_03 temporal hit | ' + ' | '.join(str(per[EVK[m]]['ITEM_03']['temporal'].get('temporal_hit')) for m in EVK) + ' |',
         '| Internal contradictions | ' + ' | '.join(str(S[EVK[m]]['internal_contradiction_count']) for m in EVK) + ' |',
         '| Suspected overclaims | ' + ' | '.join(str(S[EVK[m]]['suspected_overclaim_count']) for m in EVK) + ' |',
         '| Human review required | ' + ' | '.join(S[EVK[m]]['human_review_required_count'] for m in EVK) + ' |',
         '| External API cost / candidate | $0 (no external API) | ' + ' | '.join(f'${cost[m][1]:.6f}' for m in DIRS) + ' |', '',
         '## P3 (State) vs P4 (Vision) — same model, effort, taxonomy, risk semantics, priority formula and adapter', '',
         '| Capability | P3 State | P4 Vision |', '|---|---|---|',
         f"| Fall (ITEM_01, ITEM_04/CAM_01) | {count('P3', FALL_ITEMS)} | {count('P4', FALL_ITEMS)} |",
         f"| Boundary / Entry (ITEM_02, ITEM_04/CAM_03) final / raw | {count('P3', ['ITEM_02', 'ITEM_04/CAM_03'])} / {rawcount('P3', ['ITEM_02', 'ITEM_04/CAM_03'])} | "
         f"{count('P4', ['ITEM_02', 'ITEM_04/CAM_03'])} / {rawcount('P4', ['ITEM_02', 'ITEM_04/CAM_03'])} |",
         f"| Ambiguous Entry (ITEM_03) | {cell('P3', 'ITEM_03')} | {cell('P4', 'ITEM_03')} |",
         f"| Conflict (CAM_02, ITEM_05, ITEM_06, ITEM_07) final / raw | {count('P3', CONFLICT_ITEMS)} / {rawcount('P3', CONFLICT_ITEMS)} | "
         f"{count('P4', CONFLICT_ITEMS)} / {rawcount('P4', CONFLICT_ITEMS)} |",
         f"| Attention Top-1 | {att['P3']['top1_correct']} | {att['P4']['top1_correct']} |",
         f"| Attention Full Order | {att['P3']['full_order_correct']} ({' > '.join(att['P3']['attention_order'])}) | {att['P4']['full_order_correct']} ({' > '.join(att['P4']['attention_order'])}) |",
         f"| Same Incident (ref true) | p={ds7['P3']['p_same_incident']:.2f} → {ds7['P3']['same_incident']} | p={ds7['P4']['p_same_incident']:.2f} → {ds7['P4']['same_incident']} |",
         f"| Second-view value | adds p={ds7['P3']['p_second_view_adds']:.2f} → {ds7['P3']['second_view_adds']}; value {ds7['P3']['multiview_value']:.2f} | "
         f"adds p={ds7['P4']['p_second_view_adds']:.2f} → {ds7['P4']['second_view_adds']}; value {ds7['P4']['multiview_value']:.2f} |",
         f"| Cost / candidate | ${cost['P3'][1]:.4f} | ${cost['P4'][1]:.4f} |",
         f"| Latency median (min–max) | {latv['P3'][0] / 1000:.1f} s ({latv['P3'][1] / 1000:.1f}–{latv['P3'][2] / 1000:.1f}) cached-state decision path | "
         f"{latv['P4'][0] / 1000:.1f} s ({latv['P4'][1] / 1000:.1f}–{latv['P4'][2] / 1000:.1f}) full visual path |", '',
         '### Ablation detail (raw category, p(incident) → final category)', '', '| Assessment | Expected | P3 State | P4 Vision |', '|---|---|---|---|']
    for l in ENTRY_ITEMS + CONFLICT_ITEMS + FALL_ITEMS:
        L.append(f"| {l} | {raw['p1'][l]['expected']} | {cell('P3', l)} | {cell('P4', l)} |")
    L += ['', '## Per assessment (all pipelines)', '', '| Assessment | Expected | ' + ' | '.join(EVK) + ' |', '|---|---|' + '---|' * 5]
    L += [f"| {l} | {raw['p1'][l]['expected']} | " + ' | '.join(cell(m, l) for m in EVK) + ' |' for l in labels]
    L += ['', '## API cost per candidate', '', '| Pipeline | External API cost / candidate | 7-item total |', '|---|---|---|',
          '| P0 Cheap CV rules | $0 (no external API; local CV compute not costed) | $0 |']
    L += [f"| {NAME[m]} | ${cost[m][1]:.6f} | ${cost[m][0]:.6f} |" for m in DIRS]
    L += ['', 'Theoretical cost from provider-reported usage × official rates (P2 actual billing likely $0 under the free Neuron allocation). '
          'A higher-quality pipeline is not declared the winner on quality alone: 477 targets the Accuracy × Cost × Latency trade-off.', '',
          '## Observed primary latency (NOT a controlled comparison)', '', '| Pipeline | Median (min–max) | Path measured |', '|---|---|---|']
    L += [f"| {NAME[m]} | {latv[m][0] / 1000:.2f} s ({latv[m][1] / 1000:.2f}–{latv[m][2] / 1000:.2f}) | "
          f"{'full visual path: frame decode → encode → upload → provider → adapter → validation' if m == 'P4' else 'cached-state decision path (state → API → adapter)'} |" for m in DIRS]
    L += ['', '- **P4 primary latency = full visual path; P1/P2/P3 primary latency = cached-state decision path.**',
          '- **Final fair latency comparison pending controlled benchmark (controlled_latency_v1).**',
          f"- P4 stage medians: frame decode {statistics.median(x['frame_decode_ms'] for x in p4lat) / 1000:.1f} s, image encode "
          f"{statistics.median(x['image_encode_ms'] for x in p4lat) / 1000:.1f} s, round-trip verify {statistics.median(x['roundtrip_verify_ms'] for x in p4lat) / 1000:.1f} s, "
          f"API (upload + provider) {statistics.median(x['api_request_total_ms'] for x in p4lat) / 1000:.1f} s, adapter {statistics.median(x['adapter_ms'] for x in p4lat):.0f} ms.", '']
    (EVAL / 'p0_to_p4_comparison.md').write_text('\n'.join(L), encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
