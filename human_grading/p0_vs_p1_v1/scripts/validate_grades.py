"""Validate reviewer grade files (blind; does not read the reveal map).

Checks: all 14 assessments present and submitted; every metric is 0/1/2; both video-confirmation checkboxes true;
every overclaim flag has a valid type, an exact quote that appears verbatim in that system's blinded prediction, and a
reason; ITEM_04 ranking answers (yes/no); ITEM_07 multi-camera qualitative fields.
Usage: python scripts/validate_grades.py grades/reviewer_01.json [grades/reviewer_02.json ...]
"""
import json
import sys
from pathlib import Path

import yaml

PACK = Path(__file__).resolve().parents[1]
METRICS = ['event_understanding', 'temporal_understanding', 'evidence_grounding', 'uncertainty_handling']
SYSTEMS = ['System_A', 'System_B']


def strings(v, out):
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, dict):
        for x in v.values():
            strings(x, out)
    elif isinstance(v, list):
        for x in v:
            strings(x, out)
    return out


def validate(path):
    manifest = json.loads((PACK / 'blind_manifest.json').read_text(encoding='utf-8'))
    flag_types = set(yaml.safe_load((PACK / 'config' / 'case_guides.yaml').read_text(encoding='utf-8'))['overclaim_flags'])
    g = json.loads(Path(path).read_text(encoding='utf-8'))
    errs = []
    if g.get('pack_version') != manifest['pack_version']:
        errs.append('pack_version mismatch')
    if not g.get('reviewer_id'):
        errs.append('missing reviewer_id')
    n_ok = 0
    for it in manifest['items']:
        item, task = it['item_id'], it['task']
        for s in SYSTEMS:
            where = f'{item}/{s}'
            a = (g.get(item) or {}).get(s)
            if a is None:
                errs.append(f'{where}: missing assessment')
                continue
            bad = len(errs)
            if not a.get('submitted'):
                errs.append(f'{where}: not submitted')
            for m in METRICS:
                if a.get(m) not in (0, 1, 2) or isinstance(a.get(m), bool):
                    errs.append(f'{where}: {m} must be 0/1/2 (got {a.get(m)!r})')
            if a.get('total') is not None and all(a.get(m) in (0, 1, 2) for m in METRICS) and a['total'] != sum(a[m] for m in METRICS):
                errs.append(f'{where}: total does not equal metric sum')
            if a.get('video_confirmed') is not True:
                errs.append(f'{where}: "실제 영상을 확인했습니다" not checked')
            if a.get('evidence_compared') is not True:
                errs.append(f'{where}: "prediction의 evidence와 영상을 비교했습니다" not checked')
            pred = json.loads((PACK / 'cases' / item / f'system_{s[-1]}.json').read_text(encoding='utf-8'))['prediction']
            texts = strings(pred, [])
            for i, f in enumerate(a.get('overclaim_flags') or []):
                if f.get('type') not in flag_types:
                    errs.append(f'{where}: flag #{i + 1} invalid type {f.get("type")!r}')
                q = (f.get('quote') or '').strip()
                if not q:
                    errs.append(f'{where}: flag #{i + 1} missing exact_output_quote')
                elif not any(q in t for t in texts):
                    errs.append(f'{where}: flag #{i + 1} quote not found verbatim in the prediction')
                if not (f.get('reason') or '').strip():
                    errs.append(f'{where}: flag #{i + 1} missing why_unsupported reason')
            if task == 'attention':
                r = a.get('ranking') or {}
                for k in ('top1_correct', 'full_order_correct'):
                    if r.get(k) not in ('yes', 'no'):
                        errs.append(f'{where}: ranking.{k} must be yes/no')
            if task == 'multi_camera':
                mv = a.get('multiview') or {}
                if mv.get('second_view_added') not in ('yes', 'partially', 'no'):
                    errs.append(f'{where}: multiview.second_view_added must be yes/partially/no')
                for k in ('assumed_sync', 'asserted_cross_camera_identity'):
                    if mv.get(k) not in ('yes', 'no'):
                        errs.append(f'{where}: multiview.{k} must be yes/no')
            if len(errs) == bad:
                n_ok += 1
    return errs, n_ok, manifest['total_assessments']


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    all_ok = True
    for p in sys.argv[1:]:
        errs, n_ok, n = validate(p)
        print(f'{p}: {n_ok}/{n} assessments complete and valid')
        for e in errs:
            print('  -', e)
        print('  PASS' if not errs else '  FAIL')
        all_ok &= not errs
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
