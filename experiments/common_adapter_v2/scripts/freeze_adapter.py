"""Freeze common-adapter-v2 after validate_normalized PASS. Writes freeze/common_adapter_v2_freeze.json (no overwrite)."""
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from normalize_p1_p2 import jload, jwrite, sha  # noqa: E402

FROZEN = ['config/adapter_v2.json', 'src/common_adapter_v2.py']


def main():
    out = ROOT / 'freeze' / 'common_adapter_v2_freeze.json'
    if out.exists():
        sys.exit('common-adapter-v2 already frozen; changes require common-adapter-v3')
    val = jload(ROOT / 'logs' / 'validation.json')
    if val['verdict'] != 'PASS':
        sys.exit('normalized validation has not passed')
    man = jload(ROOT / 'logs' / 'normalize_manifest.json')
    if man['adapter_config_sha256'] != sha((ROOT / FROZEN[0]).read_bytes()) or man['adapter_src_sha256'] != sha((ROOT / FROZEN[1]).read_bytes()):
        sys.exit('adapter changed after normalization; re-run normalize + validate')
    rec = {'adapter_version': 'common-adapter-v2', 'frozen': True,
           'frozen_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'hashes': {f: sha((ROOT / f).read_bytes()) for f in FROZEN},
           'supporting_scripts_sha256': {f: sha((ROOT / f).read_bytes()) for f in
                                         ('scripts/normalize_p1_p2.py', 'scripts/validate_normalized.py')},
           'validated_on': 'P1-v1 and P2-v1 stored outputs (14 results, offline, 0 API calls)',
           'event_type_changes': val['event_type_changes'],
           'applies_to': 'P1, P2 (normalized offline), P3 and P4 (in-pipeline), unchanged'}
    jwrite(out, rec)
    print('FROZEN', out)
    for f, h in rec['hashes'].items():
        print(' ', h, f)


if __name__ == '__main__':
    main()
