"""Runtime file-access audit for the P3 model path (Python audit hook). Any open of forbidden material = FAIL."""
import sys
from pathlib import Path

FORBIDDEN = ('private_ground_truth', 'human_grading', 'readme', 'benchmark_lock', 'annotation', 'candidate_report',
             'contact_sheet', 'evaluation_selection', 'summary.md', 'summary.csv', 'reviewer', '/media/', '.mp4', '.xml',
             'results/p0_cv_only', 'results/p1_decisions', 'results/p2_clef_flash',
             'p1_decisions/raw_api', 'p1_decisions/logs', 'p2_clef_flash/raw_api', 'p2_clef_flash/logs', 'p2_clef_flash/evaluation',
             'common_adapter_v2/normalized', 'common_adapter_v2/logs', 'p3_gpt61_sol_state/evaluation', 'auto_eval',
             'p0_cv_only/debug', 'organized_data', '/data/')
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
        norm = sorted({str(Path(p)).replace('\\', '/').lower() for p in self.opens})
        bad = [p for p in norm if any(f in p for f in FORBIDDEN) and '/.venv/' not in p and 'site-packages' not in p]
        return {'files_opened': len(norm), 'forbidden_paths_opened': bad, 'pass': not bad}
