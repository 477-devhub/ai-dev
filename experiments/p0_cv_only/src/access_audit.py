"""Runtime access audit: records every file open and subprocess launched by the P0 pipeline.

Used by smoke_test / run_p0 to prove that the pipeline never touches private_ground_truth,
never opens MP4 files directly (only the official loader's ffmpeg subprocess decodes media),
and never reads annotation/label sources.
"""
import sys

FORBIDDEN_PATH_PARTS = ('private_ground_truth', 'candidate_report', 'annotation', '.xml', 'README', 'BENCHMARK_LOCK')

_state = {'active': False, 'opens': [], 'procs': []}


def _hook(event, args):
    if not _state['active']:
        return
    if event == 'open' and args and not isinstance(args[0], int):
        _state['opens'].append(str(args[0]))
    elif event == 'subprocess.Popen':
        cmd = args[1] if len(args) > 1 else args[0]
        _state['procs'].append(cmd if isinstance(cmd, str) else ' '.join(str(a) for a in cmd))   # Windows passes a command string


sys.addaudithook(_hook)


class AccessAudit:
    def __enter__(self):
        _state.update({'active': True, 'opens': [], 'procs': []})
        return self

    def __exit__(self, *exc):
        _state['active'] = False
        self.opens = list(_state['opens'])
        self.procs = list(_state['procs'])
        return False

    def report(self):
        norm = [p.replace('\\', '/') for p in self.opens]
        private = [p for p in norm if any(x.lower() in p.lower() for x in FORBIDDEN_PATH_PARTS)]
        media_direct = [p for p in norm if p.lower().endswith('.mp4')]
        ffmpeg = [c for c in self.procs if c.lower().startswith('ffmpeg')]
        other = [c for c in self.procs if not c.lower().startswith('ffmpeg')]
        nonofficial_ffmpeg = [c for c in ffmpeg if "select='eq(n," not in c or ' -vf ' not in c]
        return {
            'files_opened': len(norm),
            'private_or_label_paths_opened': private,
            'mp4_opened_directly_by_python': media_direct,
            'ffmpeg_decode_processes': len(ffmpeg),
            'ffmpeg_processes_not_using_canonical_select': len(nonofficial_ffmpeg),
            'other_subprocesses': other,
            'pass': not private and not media_direct and not nonofficial_ffmpeg and not other,
        }
