"""Step 9/10 — validate human review labels. Never fills or infers a label.

Exit code 0 only if every queued candidate carries a valid human label.
Writes review/review_status.json (counts, problems, reviewer agreement).
"""
from __future__ import annotations

import re
import sys
import argparse
from collections import Counter

from _common import REVIEW, read_csv, write_json

LABELS = {"CLEAR_NORMAL", "HARD_NEGATIVE_NORMAL", "ANCHORED_DANGER", "AMBIGUOUS", "EXCLUDE"}
CONF = {"HIGH", "MEDIUM", "LOW"}
DANGER = {"possible_fall_or_person_down", "possible_physical_conflict", "clear_boundary_crossing", "other_visual_safety_incident"}
HN = {"HN01_crouch_then_recover", "HN02_sit_or_lie_normally", "HN03_normal_running", "HN04_normal_doorway_entry",
      "HN05_normal_gate_entry", "HN06_close_pair", "HN07_brief_physical_contact", "HN08_object_pickup", "HN09_bending",
      "HN10_occlusion", "HN11_darkness_or_low_visibility", "HN12_crowd_flow", "HN13_rapid_arm_motion_non_conflict",
      "HN14_person_temporarily_on_ground_non_incident", "HN15_camera_motion_or_visual_noise"}
NORMAL_SUB = {"walking", "standing", "sitting", "entering_or_leaving", "passing_each_other", "conversation",
              "vehicle_only", "empty_scene", "other"}
FORBIDDEN = re.compile(r"\b(criminal|illegal|trespass\w*|intruder|burglar|thief|attacker|victim|assault\w*|fainted|"
                       r"unconscious|medical emergency|seizure|drunk|suspicious person)\b", re.I)


def check_row(r: dict) -> list[str]:
    p = []
    lab, conf = r.get("review_label", "").strip(), r.get("review_confidence", "").strip()
    if not lab:
        return ["missing review_label"]
    if lab not in LABELS:
        p.append(f"invalid review_label '{lab}'")
    if conf not in CONF:
        p.append(f"invalid/missing review_confidence '{conf}'")
    summ = r.get("observable_summary", "").strip()
    if not summ:
        p.append("missing observable_summary")
    if FORBIDDEN.search(summ):
        p.append(f"forbidden inference term in observable_summary: '{FORBIDDEN.search(summ).group(0)}'")
    if not r.get("reviewer", "").strip():
        p.append("missing reviewer")
    if not r.get("reviewed_at", "").strip():
        p.append("missing reviewed_at")
    if lab == "ANCHORED_DANGER" and r.get("danger_type_if_any", "").strip() not in DANGER:
        p.append("ANCHORED_DANGER needs a valid danger_type_if_any")
    if lab == "HARD_NEGATIVE_NORMAL":
        ts = [t.strip() for t in r.get("hard_negative_type_if_any", "").split("|") if t.strip()]
        if not ts or any(t not in HN for t in ts):
            p.append("HARD_NEGATIVE_NORMAL needs valid hard_negative_type_if_any")
    if lab == "CLEAR_NORMAL" and r.get("normal_subtype", "").strip() not in NORMAL_SUB:
        p.append("CLEAR_NORMAL needs a valid normal_subtype")
    if lab == "AMBIGUOUS" and not r.get("ambiguous_reason", "").strip():
        p.append("AMBIGUOUS needs ambiguous_reason")
    if lab == "EXCLUDE" and not r.get("exclude_reason", "").strip():
        p.append("EXCLUDE needs exclude_reason")
    if lab in {"CLEAR_NORMAL", "HARD_NEGATIVE_NORMAL"} and r.get("danger_type_if_any", "").strip():
        p.append("normal label must not carry danger_type_if_any")
    return p


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority", action="store_true", help="minimal human GT for the priority subset")
    args = ap.parse_args()
    if args.priority:
        from _priority_gt import validate_labels
        status = validate_labels()
        print("PRIORITY HUMAN REVIEW — " + ("PASS" if status["human_review_complete"] else "FAIL"))
        print(f"Selected: {status['queue_size']}\nLabelled: {status['labelled']}/{status['queue_size']}")
        for label, count in sorted(status["label_counts"].items()):
            print(f"{label}: {count}")
        print(f"Primary usable: {status['primary_usable']}\nAmbiguous challenge: {status['ambiguous_challenge']}")
        print("Auxiliary metadata missing (warnings only):", status["auxiliary_missing"])
        print("Additional human review required:", "NO" if status["human_review_complete"] else "ONLY IF HUMAN LABEL MISSING")
        if status["problems"]:
            print(status["problems"])
        return 0 if status["human_review_complete"] else 1
    q = read_csv(REVIEW / "human_review_queue.csv")
    problems, labelled = {}, 0
    for r in q:
        pr = check_row(r)
        if r.get("review_label", "").strip():
            labelled += 1
            if pr:                                  # unlabelled rows are pending, not problems
                problems[r["candidate_id"]] = pr

    # second reviewer (only if someone actually filled it)
    agreement = {"second_reviewer_present": False}
    r2p = REVIEW / "human_review_queue_reviewer2.csv"
    if r2p.exists():
        r2 = [r for r in read_csv(r2p) if r.get("review_label", "").strip()]
        if r2:
            first = {r["candidate_id"]: r for r in q}
            dis = []
            for r in r2:
                pr = check_row(r)
                if pr:
                    problems[f"{r['candidate_id']}#reviewer2"] = pr
                a = first.get(r["candidate_id"], {})
                same_person = a.get("reviewer", "").strip() and a.get("reviewer", "").strip() == r.get("reviewer", "").strip()
                if same_person:
                    problems[f"{r['candidate_id']}#reviewer2"] = ["second review must be by a different reviewer"]
                if a.get("review_label", "").strip() and a["review_label"].strip() != r["review_label"].strip():
                    dis.append({"candidate_id": r["candidate_id"], "reviewer_1": a["review_label"], "reviewer_2": r["review_label"],
                                "status": "adjudication_required"})
            agreement = {"second_reviewer_present": True, "double_reviewed": len(r2),
                         "exact_label_agreement": len(r2) - len(dis), "adjudication_required": dis}

    counts = Counter(r.get("review_label", "").strip() or "PENDING" for r in q)
    conf = Counter((r.get("review_label", "").strip(), r.get("review_confidence", "").strip()) for r in q if r.get("review_label", "").strip())
    complete = labelled == len(q) and not problems and not agreement.get("adjudication_required")
    status = {
        "queue_size": len(q), "labelled": labelled, "pending": len(q) - labelled,
        "label_counts": dict(counts), "label_by_confidence": {f"{k[0]}/{k[1]}": v for k, v in conf.items()},
        "problems": problems, "reviewer_agreement": agreement,
        "human_review_complete": complete,
        "status": "COMPLETE" if complete else ("NEEDS HUMAN REVIEW" if labelled < len(q) else "NEEDS FIXES"),
    }
    write_json(REVIEW / "review_status.json", status)
    print(f"{status['status']}: labelled {labelled}/{len(q)}, problems {len(problems)}")
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
