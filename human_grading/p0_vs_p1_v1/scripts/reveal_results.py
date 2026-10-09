"""Reveal System A/B -> P0/P1 for a COMPLETE, VALID grade file, then rebuild the summary.

Run only after grading is finished:
  python scripts/reveal_results.py --grades grades/reviewer_01.json
Writes output/<reviewer>_revealed.json and regenerates output/summary.md, output/summary.csv
(and output/adjudication_needed.md when two or more reviewers have been revealed).
Scores are copied exactly as the reviewer entered them; nothing is inferred, averaged into a final value, or filled in.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_summary  # noqa: E402
from validate_grades import validate  # noqa: E402

PACK = Path(__file__).resolve().parents[1]
METRICS = ['event_understanding', 'temporal_understanding', 'evidence_grounding', 'uncertainty_handling']
BENCHMARK_FIELD = {'event_understanding': 'event_understanding', 'temporal_understanding': 'temporal_understanding',
                   'evidence_grounding': 'evidence_grounding', 'uncertainty_handling': 'uncertainty_calibration'}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--grades', required=True, type=Path)
    a = ap.parse_args()
    errs, n_ok, n = validate(a.grades)
    if errs:
        print(f'Grades are not complete/valid ({n_ok}/{n}). Reveal refused. Run scripts/validate_grades.py for details.')
        sys.exit(1)
    g = json.loads(a.grades.read_text(encoding='utf-8'))
    reveal = json.loads((PACK / 'reveal_map_private.json').read_text(encoding='utf-8'))
    manifest = json.loads((PACK / 'blind_manifest.json').read_text(encoding='utf-8'))
    out = {'pack_version': g['pack_version'], 'reviewer_id': g['reviewer_id'],
           'revealed_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'grades_file': str(a.grades), 'systems': {'p0': {}, 'p1': {}},
           'metric_name_map_to_benchmark_human_grading': BENCHMARK_FIELD,
           'note': 'Scores exactly as entered by the reviewer under blind conditions. No automatic grading.'}
    for it in manifest['items']:
        item = it['item_id']
        for label, sys_key in reveal['mapping'][item].items():
            asm = dict(g[item][label])
            asm['blind_label'] = label
            asm['total'] = sum(asm[m] for m in METRICS)
            if it['task'] == 'attention':
                pred = json.loads((PACK / 'cases' / item / f'system_{label[-1]}.json').read_text(encoding='utf-8'))['prediction']
                order = [x['camera'] for x in sorted(pred['attention_queue'], key=lambda x: x['rank'])]
                ref = json.loads((PACK / 'cases' / item / 'reference.json').read_text(encoding='utf-8'))['ranking']['reference_order']
                # objective consistency check only; the reviewer's answers are kept unchanged
                asm['ranking_consistency_check'] = {
                    'system_queue': order, 'reference_order': ref,
                    'computed_top1_correct': 'yes' if order[0] == ref[0] else 'no',
                    'computed_full_order_correct': 'yes' if order == ref else 'no',
                    'matches_reviewer_answers': (asm['ranking']['top1_correct'] == ('yes' if order[0] == ref[0] else 'no')
                                                 and asm['ranking']['full_order_correct'] == ('yes' if order == ref else 'no')),
                }
            out['systems'][sys_key][item] = asm
    dest = PACK / 'output' / f'{g["reviewer_id"]}_revealed.json'
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Wrote', dest.relative_to(PACK))
    build_summary.main()


if __name__ == '__main__':
    main()
