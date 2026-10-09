"""Append-only process-order audit log (logs/process_audit_log.jsonl): model run -> leakage audit -> result freeze -> GT/eval."""
import _bootstrap  # noqa: F401
import datetime
import json
import os
import sys

from utils import LOGS_DIR

PATH = LOGS_DIR / 'process_audit_log.jsonl'


def log_event(event, detail=None):
    PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {'at': datetime.datetime.now().astimezone().isoformat(timespec='milliseconds'), 'event': event,
           'pid': os.getpid(), 'script': os.path.basename(sys.argv[0]), 'detail': detail}
    with PATH.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def events():
    if not PATH.exists():
        return []
    return [json.loads(l) for l in PATH.read_text(encoding='utf-8').splitlines() if l.strip()]
