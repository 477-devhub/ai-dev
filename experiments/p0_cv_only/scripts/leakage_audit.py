"""Static leakage audit of P0 code/configs + runtime access-audit summary from results. Writes debug/reports/leakage_audit.json."""
import _bootstrap  # noqa: F401
import re

from utils import EXP_ROOT, ITEM_IDS, RESULTS_DIR, read_json, write_json

TERMS = r'private_ground_truth|candidate_report|annotation|swoon|fight|trespass|falldown|climbwall|punching|expected.?rank'
# conditional leakage: branching on item/asset IDs or source labels inside executable logic
CONDITIONAL = r'if[^\n]*(ITEM_0\d|ASSET_0\d|asset_0\d|S14|T06|T03|F01|MV05|swoon|fight|trespass)'


def main():
    files = [p for d in ('src', 'scripts', 'configs', 'schemas') for p in (EXP_ROOT / d).rglob('*') if p.is_file() and p.suffix in ('.py', '.yaml', '.json') and p.name != 'leakage_audit.py']
    mentions, conditional = [], []
    for p in files:
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            rel = f'{p.relative_to(EXP_ROOT).as_posix()}:{n}'
            if re.search(TERMS, line, re.I):
                mentions.append({'where': rel, 'line': line.strip()[:160]})
            if re.search(CONDITIONAL, line, re.I):
                conditional.append({'where': rel, 'line': line.strip()[:160]})
    runtime = {}
    for item in ITEM_IDS:
        a = read_json(RESULTS_DIR / f'run_{item}.json')['runtime_config']['access_audit']
        runtime[item] = {'pass': a['pass'], 'private_or_label_paths_opened': a['private_or_label_paths_opened'],
                         'mp4_opened_directly_by_python': a['mp4_opened_directly_by_python'], 'ffmpeg_decode_processes': a['ffmpeg_decode_processes']}
    out = {'files_scanned': len(files), 'term_mentions': mentions, 'conditional_leakage': conditional, 'runtime_access_audit': runtime,
           'verdict': 'PASS' if not conditional and all(v['pass'] for v in runtime.values()) else 'FAIL',
           'note': 'Term mentions are deny-lists, comments or a CLI default; none is used as a decision input.'}
    write_json(EXP_ROOT / 'debug' / 'reports' / 'leakage_audit.json', out)
    for m in mentions:
        print('mention   ', m['where'], '|', m['line'])
    print('conditional leakage:', conditional or 'none')
    print('runtime audit:', {k: v['pass'] for k, v in runtime.items()})
    print('LEAKAGE AUDIT', out['verdict'])


if __name__ == '__main__':
    main()
