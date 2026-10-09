"""Local review UI server (stdlib only). Serves review/ and saves labels back into the queue CSV.

  python scripts/serve_review.py              -> reviewer 1 queue (review/human_review_queue.csv)
  python scripts/serve_review.py --reviewer2  -> independent second-review file
  python scripts/serve_review.py --priority   -> reduced priority queue

Open the printed URL. Only the label columns are written; every other column is preserved.
Each save first copies the previous CSV to review/backups/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import http.server
import json
import shutil
import socketserver
import urllib.parse

from _common import BENCH, REVIEW, read_csv, write_csv

LABEL_FIELDS = ["review_label", "review_confidence", "observable_summary", "danger_type_if_any",
                "hard_negative_type_if_any", "normal_subtype", "ambiguous_reason", "exclude_reason", "reviewer", "reviewed_at"]


def make_handler(queue_path):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(BENCH), **kw)

        def log_message(self, *a):
            pass

        def handle(self):
            try:
                super().handle()
            except (ConnectionResetError, BrokenPipeError):
                # Browser cancelled a stream. Label save failures still propagate.
                if getattr(self, "command", None) != "GET":
                    raise

        def _json(self, obj, code=200):
            b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path == "/api/queue":
                rows = read_csv(queue_path)
                if queue_path.name == "human_review_priority.csv":
                    # Preserve opaque source context in the CSV, but hide it during review.
                    for r in rows:
                        r["source_label"] = ""
                if queue_path.name.endswith("reviewer2.csv"):          # second reviewer sees nothing of reviewer 1
                    meta = {r["candidate_id"]: r for r in read_csv(REVIEW / "human_review_queue.csv")}
                    for r in rows:
                        m = meta[r["candidate_id"]]
                        r.update({k: m[k] for k in ("start_sec", "end_sec", "contact_sheet", "review_clip", "source_label")})
                return self._json({"file": queue_path.name, "rows": rows})
            if u.path in ("/", ""):
                self.send_response(302)
                self.send_header("Location", "/review/review.html")
                self.end_headers()
                return
            return super().do_GET()

        def do_POST(self):
            if urllib.parse.urlparse(self.path).path != "/api/save":
                return self._json({"error": "not found"}, 404)
            if (BENCH / "BENCHMARK_LOCK.json").exists():
                return self._json({"error": "benchmark is frozen; annotation changes require v2"}, 409)
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
            rows = read_csv(queue_path)
            byid = {r["candidate_id"]: r for r in rows}
            r = byid.get(body.get("candidate_id"))
            if r is None:
                return self._json({"error": "unknown candidate"}, 400)
            for k in LABEL_FIELDS:
                if k in body:
                    r[k] = str(body[k]).strip()
            bk = REVIEW / "backups"
            bk.mkdir(exist_ok=True)
            shutil.copyfile(queue_path, bk / f"{queue_path.stem}.{dt.datetime.now():%Y%m%dT%H%M%S%f}.csv")
            fields = list(rows[0].keys())
            write_csv(queue_path, rows, fields)
            return self._json({"ok": True})
    return H


def main():
    ap = argparse.ArgumentParser()
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--reviewer2", action="store_true")
    modes.add_argument("--priority", action="store_true")
    ap.add_argument("--port", type=int, default=4771)
    a = ap.parse_args()
    name = ("human_review_priority.csv" if a.priority else
            "human_review_queue_reviewer2.csv" if a.reviewer2 else "human_review_queue.csv")
    qp = REVIEW / name
    if not qp.is_file():
        ap.error(f"review queue does not exist: {qp}")
    port = a.port
    while True:
        try:
            srv = socketserver.ThreadingTCPServer(("127.0.0.1", port), make_handler(qp))
            break
        except OSError:
            port += 1
    print(f"Reviewing {qp.name}: open http://127.0.0.1:{port}/review/review.html  (Ctrl+C to stop)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
