"""Producer/consumer entry point: wait for immutable CV states, then original frozen P1 worker.

No prompt, model, decision or threshold logic changes. This permits CV and P1 to
overlap without calling P1 on missing inputs or restarting model evaluations.
"""
import argparse
import ctypes
import time
import worker
from common import RUN, stage_ids, verify_frozen, install_model_boundary

def alive(pid):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:
        return False
    try:
        code=ctypes.c_ulong()
        return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
    finally:
        kernel.CloseHandle(handle)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage',choices=['calibration','test'],required=True)
    ap.add_argument('--cv-pid',type=int,required=True)
    args=ap.parse_args()
    verify_frozen()
    ids=stage_ids(args.stage)
    def ready_items(stage):
        if stage!=args.stage:
            raise RuntimeError('Stage mismatch')
        for item in ids:
            while not ((RUN/'cv_states'/f'{item}.json').is_file() and (RUN/'cv_logs'/f'{item}.json').is_file()):
                if not alive(args.cv_pid):
                    raise RuntimeError(f'CV worker exited before {item} was ready; no API request made for it')
                time.sleep(2)
            yield item
    worker.stage_ids=ready_items
    install_model_boundary()
    worker.models('p1',args.stage)

if __name__=='__main__':
    main()
