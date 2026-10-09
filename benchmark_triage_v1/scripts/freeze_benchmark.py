"""Step 15 — freeze 477-triage-normal-v1. Writes BENCHMARK_LOCK.json only if ALL lock conditions hold
(brief section 49). After freeze nothing may change; fixes go to 477-triage-normal-v2.

Conditions:
  human review complete            review/review_status.json
  duplicate audit complete         reports/validation.json review checks
  scene diversity check complete   reports/diversity_report.md exists (build_report.py)
  class counts approved            review/approvals.json  {"class_counts_approved_by": ..., "split_approved_by": ..., ...}
  split finalized                  review/approvals.json
  GT validation PASS               validate_benchmark.py all_pass (except the lock check itself)
  existing benchmark overlap audit reports/leakage_report.md + no reasoning-v1 source video in the benchmark
"""
from __future__ import annotations

import datetime as dt
import sys

from _common import BENCH, BENCHMARK_ID, REVIEW, read_json, sha256, write_json

LOCKED_GLOBS = ["media/*.mp4", "public_manifest.json", "private_ground_truth/triage_labels.json",
                "challenge_public_manifest.json", "review/human_review_priority.csv", "review/priority_review_manifest.json",
                "manifests/*.json", "candidate_pool/candidate_sources.json", "candidate_pool/candidates.csv",
                "review/human_review_queue.csv", "review/human_review_queue_reviewer2.csv", "review/approvals.json",
                "scripts/*.py"]


def main() -> int:
    if (BENCH / "BENCHMARK_LOCK.json").exists():
        print("REFUSED: already frozen. Create 477-triage-normal-v2 for any change.")
        return 1
    gt_path = BENCH / "private_ground_truth/triage_labels.json"
    priority = gt_path.exists() and read_json(gt_path).get("human_gt_policy") == "priority_minimal_v1"
    if priority:
        # Revalidate actual artifacts now; never freeze based on stale status files.
        from _priority_gt import validate_labels, validate_built
        fresh_labels = validate_labels()
        fresh_validation = validate_built()
        if not fresh_labels["human_review_complete"] or not fresh_validation["ready_to_freeze"]:
            print("REFUSED: priority GT or technical validation failed; see validation.json")
            return 1
    reasons = []
    st = read_json(REVIEW / "review_status.json") if (REVIEW / "review_status.json").exists() else {}
    if not st.get("human_review_complete"):
        reasons.append("human review not complete")
    ap = read_json(REVIEW / "approvals.json") if (REVIEW / "approvals.json").exists() else {}
    for k in ("class_counts_approved_by", "split_approved_by", "approved_at"):
        if not ap.get(k):
            reasons.append(f"approvals.json missing {k}")
    val = read_json(BENCH / "reports" / "validation.json") if (BENCH / "reports" / "validation.json").exists() else {"checks": {}}
    if not val["checks"].get("benchmark_built", {}).get("pass"):
        reasons.append("benchmark has not passed built-artifact validation")
    for k, v in val["checks"].items():
        if k != "benchmark_lock_hashes_valid" and not k.startswith("info_") and not v["pass"]:
            reasons.append(f"validation failed: {k}")
    for f in ("reports/diversity_report.md", "reports/leakage_report.md"):
        if not (BENCH / f).exists():
            reasons.append(f"missing {f}")
    if reasons:
        print("REFUSED to freeze:\n - " + "\n - ".join(reasons))
        return 1
    if priority:
        split_path = BENCH / "manifests/split_manifest.json"
        split_manifest = read_json(split_path)
        split_manifest.update({"finalized": True, "approved_by": ap["split_approved_by"],
                               "approved_at": ap["approved_at"]})
        write_json(split_path, split_manifest)
    files = sorted({p for g in LOCKED_GLOBS for p in BENCH.glob(g) if p.is_file()})
    write_json(BENCH / "BENCHMARK_LOCK.json", {
        "benchmark_version": BENCHMARK_ID, "frozen_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "approvals": ap, "policy": "No clip/label/split/window/subtype change after freeze; use 477-triage-normal-v2.",
        "sha256": {str(p.relative_to(BENCH)).replace("\\", "/"): sha256(p) for p in files}})
    print(f"FROZEN: {len(files)} files hashed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
