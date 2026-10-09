"""Build output/summary.md, output/summary.csv (and output/adjudication_needed.md for 2+ reviewers)
from output/*_revealed.json. Pure arithmetic over human-entered scores: no judge model, no imputation,
no averaging across reviewers into a final score, and no percentage-accuracy language.
"""
import csv
import itertools
import json
import sys
from pathlib import Path

import yaml

PACK = Path(__file__).resolve().parents[1]
OUT = PACK / 'output'
ITEMS = [f'ITEM_{i:02d}' for i in range(1, 8)]
MAIN = ['ITEM_01', 'ITEM_02', 'ITEM_03', 'ITEM_04', 'ITEM_07']
METRICS = ['event_understanding', 'temporal_understanding', 'evidence_grounding', 'uncertainty_handling']
SHORT = {'event_understanding': 'Event', 'temporal_understanding': 'Temporal', 'evidence_grounding': 'Evidence', 'uncertainty_handling': 'Uncertainty'}
SYS = ['p0', 'p1']
NAME = {'p0': 'P0', 'p1': 'P1'}


def load():
    return {d['reviewer_id']: d for d in (json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('*_revealed.json')))}


def reviewer_section(r):
    S = r['systems']
    L = [f'## Reviewer: {r["reviewer_id"]}', '', f'Revealed at {r["revealed_at"]}. Scores as entered by the reviewer under blind conditions.', '',
         '### Per-item rubric total (0–8)', '', '| Item | P0 | P1 |', '|---|---|---|']
    for it in ITEMS:
        tag = ' (main)' if it in MAIN else ' (SET05 auxiliary)'
        L.append(f'| {it}{tag} | {S["p0"][it]["total"]}/8 | {S["p1"][it]["total"]}/8 |')
    L += ['', '### Per-item metric scores (0–2)', '', '| Item | Metric | P0 | P1 |', '|---|---|---|---|']
    for it in ITEMS:
        for m in METRICS:
            L.append(f'| {it} | {SHORT[m]} | {S["p0"][it][m]} | {S["p1"][it][m]} |')
    L += ['', '### Main five-case summary (ITEM_01, ITEM_02, ITEM_03, ITEM_04, ITEM_07)', '',
          'Five diagnostic cases only — reported as rubric totals, not as accuracy percentages.', '',
          '| Measure | P0 | P1 |', '|---|---|---|']
    tot = {s: sum(S[s][i]['total'] for i in MAIN) for s in SYS}
    L.append(f'| Main five-case rubric total (max 40) | {tot["p0"]} | {tot["p1"]} |')
    L.append(f'| Average rubric score per case (max 8) | {tot["p0"] / 5:.2f} | {tot["p1"] / 5:.2f} |')
    for m in METRICS:
        L.append(f'| {SHORT[m]} score (sum of 5 cases, max 10) | {sum(S["p0"][i][m] for i in MAIN)} | {sum(S["p1"][i][m] for i in MAIN)} |')
    L += ['', '### SET04 attention ranking (477 project-defined human reference, not AI Hub ground truth)', '',
          '| | P0 | P1 |', '|---|---|---|']
    for k, lab in (('top1_correct', 'Top-1 Correct (reviewer)'), ('full_order_correct', 'Full Order Correct (reviewer)')):
        L.append(f'| {lab} | {S["p0"]["ITEM_04"]["ranking"][k]} | {S["p1"]["ITEM_04"]["ranking"][k]} |')
    L.append(f'| System queue | {" > ".join(S["p0"]["ITEM_04"]["ranking_consistency_check"]["system_queue"])} | {" > ".join(S["p1"]["ITEM_04"]["ranking_consistency_check"]["system_queue"])} |')
    L.append(f'| Reviewer answers match queue/reference check | {S["p0"]["ITEM_04"]["ranking_consistency_check"]["matches_reviewer_answers"]} | {S["p1"]["ITEM_04"]["ranking_consistency_check"]["matches_reviewer_answers"]} |')
    L += ['', '### SET05 Multi-view Increment = Score(ITEM_07) − max(Score(ITEM_05), Score(ITEM_06))', '',
          'Correct baseline is the best single view (AB > A alone is not sufficient).', '',
          '| | P0 | P1 |', '|---|---|---|']
    inc = {}
    for s in SYS:
        a, b, ab = (S[s][i]['total'] for i in ('ITEM_05', 'ITEM_06', 'ITEM_07'))
        inc[s] = (a, b, ab, max(a, b), ab - max(a, b))
    for idx, lab in enumerate(['A only (ITEM_05)', 'B only (ITEM_06)', 'A+B (ITEM_07)', 'Best single view', '**Multi-view Increment**']):
        L.append(f'| {lab} | {inc["p0"][idx]} | {inc["p1"][idx]} |')
    for m in METRICS:
        v = {s: S[s]['ITEM_07'][m] - max(S[s]['ITEM_05'][m], S[s]['ITEM_06'][m]) for s in SYS}
        L.append(f'| Increment — {SHORT[m]} | {v["p0"]} | {v["p1"]} |')
    L += ['', '### ITEM_07 multi-camera qualitative checks (separate from 0–8)', '', '| Question | P0 | P1 |', '|---|---|---|']
    for k, lab in (('second_view_added', 'Second view added genuinely new useful evidence'), ('assumed_sync', 'Incorrectly assumed synchronization'),
                   ('asserted_cross_camera_identity', 'Incorrectly asserted cross-camera identity')):
        L.append(f'| {lab} | {S["p0"]["ITEM_07"]["multiview"][k]} | {S["p1"]["ITEM_07"]["multiview"][k]} |')
    L += ['', '### Confirmed overclaim flags (human-entered)', '']
    any_flag = False
    for s in SYS:
        for it in ITEMS:
            for f in S[s][it].get('overclaim_flags') or []:
                any_flag = True
                L.append(f'- **{NAME[s]} {it}** `{f["type"]}` — "{f["quote"]}" — {f["reason"]}')
    if not any_flag:
        L.append('- none entered')
    return L + ['']


def agreement(revs):
    L, rows = ['## Reviewer agreement', ''], []
    for r1, r2 in itertools.combinations(sorted(revs), 2):
        A, B = revs[r1]['systems'], revs[r2]['systems']
        L += [f'### {r1} vs {r2}', '', '| Metric | Exact agreement (n/14) | Mean absolute difference |', '|---|---|---|']
        for m in METRICS:
            pairs = [(A[s][i][m], B[s][i][m]) for s in SYS for i in ITEMS]
            ex = sum(x == y for x, y in pairs)
            mad = sum(abs(x - y) for x, y in pairs) / len(pairs)
            L.append(f'| {SHORT[m]} | {ex}/14 | {mad:.2f} |')
            rows += [(r1, r2, s, i, m) for s in SYS for i in ITEMS if A[s][i][m] != B[s][i][m]]
        L.append('')
    L += ['Disagreements are **not** averaged into a final score. See `adjudication_needed.md`; reviewers re-watch the video and agree a consensus.', '']
    return L, rows


def adjudication(revs, rows):
    guides = yaml.safe_load((PACK / 'config' / 'case_guides.yaml').read_text(encoding='utf-8'))['items']
    nk = {'event_understanding': 'event', 'temporal_understanding': 'temporal', 'evidence_grounding': 'evidence', 'uncertainty_handling': 'uncertainty'}
    L = ['# Adjudication needed', '', 'Cases where reviewers gave different scores. Re-watch the video together and record a consensus; do not average.', '']
    if not rows:
        L.append('No disagreements.')
    for r1, r2, s, it, m in rows:
        a, b = revs[r1]['systems'][s][it], revs[r2]['systems'][s][it]
        anchor = guides[it]['metrics'][m]
        L += [f'## {it} — {a["blind_label"].replace("_", " ")} (revealed: {NAME[s]}) — {SHORT[m]}', '',
              f'| Reviewer | Score | Note |', '|---|---|---|',
              f'| {r1} | {a[m]} | {(a["notes"].get(nk[m]) or "").replace(chr(10), " ")} |',
              f'| {r2} | {b[m]} | {(b["notes"].get(nk[m]) or "").replace(chr(10), " ")} |', '',
              'Relevant grading anchor:', f'- 2: {anchor["2"]}', f'- 1: {anchor["1"]}', f'- 0: {anchor["0"]}', f'- Tip: {anchor["tip"]}', '']
    return L


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    revs = load()
    if not revs:
        print('No revealed grade files in output/.')
        return
    L = ['# P0 vs P1 — Blind Human Grading Summary (p0_vs_p1_v1)', '',
         'All scores were entered by human reviewers under blind A/B conditions; no automatic or model-based grading.',
         'Main benchmark summary uses ITEM_01–04 and ITEM_07; ITEM_05/06 are SET05 auxiliary conditions for best-single and Multi-view Increment.',
         'Five diagnostic cases: report rubric totals/averages, never "% accuracy".', '']
    for rid in sorted(revs):
        L += reviewer_section(revs[rid])
    rows = []
    if len(revs) >= 2:
        ag, rows = agreement(revs)
        L += ag
        (OUT / 'adjudication_needed.md').write_text('\n'.join(adjudication(revs, rows)) + '\n', encoding='utf-8')
    (OUT / 'summary.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    with (OUT / 'summary.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['reviewer_id', 'system', 'item', 'blind_label', 'main_case'] + METRICS + ['total', 'overclaim_flag_count', 'top1_correct', 'full_order_correct'])
        for rid in sorted(revs):
            for s in SYS:
                for it in ITEMS:
                    a = revs[rid]['systems'][s][it]
                    w.writerow([rid, NAME[s], it, a['blind_label'], it in MAIN] + [a[m] for m in METRICS] + [a['total'], len(a.get('overclaim_flags') or []),
                               (a.get('ranking') or {}).get('top1_correct', ''), (a.get('ranking') or {}).get('full_order_correct', '')])
    print('Wrote output/summary.md, output/summary.csv' + (', output/adjudication_needed.md' if len(revs) >= 2 else ''))


if __name__ == '__main__':
    main()
