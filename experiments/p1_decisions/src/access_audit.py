"""Runtime file-access audit for P1 (Python audit hook). Flags any open of forbidden benchmark/private material."""
import sys
from pathlib import Path

FORBIDDEN = ('private_ground_truth', 'readme', 'benchmark_lock', 'annotation', 'candidate_report', 'contact_sheet',
             '/media/', '.mp4', '.xml', 'p0_cv_only/debug', 'results/p0_cv_only')
_s = {'on': False, 'opens': []}


def _hook(event, args):
    if _s['on'] and event == 'open' and args and not isinstance(args[0], int):
        _s['opens'].append(str(args[0]))


sys.addaudithook(_hook)


class AccessAudit:
    def __enter__(self):
        _s.update(on=True, opens=[])
        return self

    def __exit__(self, *a):
        _s['on'] = False
        self.opens = list(_s['opens'])

    def report(self):
        norm = [str(Path(p)).replace('\\', '/').lower() for p in self.opens]
        bad = [p for p in norm if any(f in p for f in FORBIDDEN)]
        return {'files_opened': len(norm), 'forbidden_paths_opened': bad, 'pass': not bad}
