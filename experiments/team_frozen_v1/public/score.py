"""Offline team submission scorer. This program never calls a model or API."""
import argparse
import csv
import copy
import json
from pathlib import Path
from pipeline477.contract import COLUMNS
from pipeline477.team_benchmark import score_submission, template_rows


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                             if isinstance(value, (dict, list)) or value is None else value
                             for key, value in row.items() if key in columns})


def write_score_results(path, rows, root):
    """Keep dense records in JSON artifacts, preserving standard CSV reader compatibility."""
    compact = []
    for row in rows:
        saved = copy.deepcopy(row)
        saved["stage_outputs"] = {}
        for stage, record in row["stage_outputs"].items():
            artifact = path.parent / "records" / row["item_id"] / (stage + ".json")
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            saved["stage_outputs"][stage] = {"record_path": artifact.relative_to(root).as_posix(),
                "status": record.get("status"), "executed": record.get("executed")}
        compact.append(saved)
    write_csv(path, compact, COLUMNS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path)
    parser.add_argument("--output", type=Path, default=Path("scores"))
    parser.add_argument("--create-template", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.create_template:
        rows = template_rows(root)
        columns = [key for key in COLUMNS if key not in {"ground_truth", "metrics"}]
        write_csv(args.submission, rows, columns)
        print(json.dumps({"template": str(args.submission), "items": len(rows), "model_calls": 0}))
        return
    if args.ground_truth is None:
        parser.error("--ground-truth is required; evaluator reference must never enter model input")
    rows, summary = score_submission(args.submission, root, args.ground_truth)
    args.output = (args.output if args.output.is_absolute() else root / args.output).resolve()
    if not args.output.is_relative_to(root):
        parser.error("--output must remain inside benchmark folder so CSV record paths are portable")
    args.output.mkdir(parents=True, exist_ok=True)
    write_score_results(args.output / "results.csv", rows, root)
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"results": str(args.output / "results.csv"), "summary": str(args.output / "summary.json"), "items": len(rows), "model_calls": 0}))


if __name__ == "__main__":
    main()
