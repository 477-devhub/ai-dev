"""Read-only audit of frozen artifacts; writes only this research directory.

No model imports, inference, calibration, alternate test thresholds, or benchmark writes.
Run: python -B planning/stage1_router_v2_research/audit_artifacts.py
"""
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
RUN = ROOT / "experiments/triage_frozen_v1"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def summary(values):
    values = sorted(values)
    return {"mean": statistics.mean(values), "median": statistics.median(values),
            "min": values[0], "max": values[-1],
            "p95_nearest_rank": values[math.ceil(.95 * len(values)) - 1]}


def main():
    policy = read(RUN / "routing_policy_lock.json")
    threshold = policy["T_normal"]
    pricing = read(ROOT / "experiments/p4_gpt61_sol_vision/configs/p4_v1.json")["pricing"]
    report = {"audit_date_kst": "2026-10-09", "mode": "fixed-policy artifact diagnostics only",
              "api_calls": 0, "test_threshold_sweeps": 0, "T_normal": threshold,
              "original_final_metrics": read(RUN / "analysis/final_test_evaluation.json")["metrics"],
              "splits": {}, "integrity": {}, "cost_basis": "provider usage x repository frozen rates; not invoice"}
    labels = {}
    for split in ("calibration", "test"):
        gt = read(RUN / f"analysis/{split}_gt.json")
        labels[split] = gt
        rows, timing, costs, tokens, cv_ms = [], {}, {}, {}, []
        for model in ("p1", "p4"):
            timing[model] = {k: [] for k in ("api_last_attempt_ms", "api_total_ms", "full_harness_ms")}
            costs[model], tokens[model] = [], {k: [] for k in ("input", "output", "cached", "cache_write")}
        for item, label in gt.items():
            results = {model: read(RUN / model / "results" / f"{item}.json") for model in ("p1", "p4")}
            d, d4 = results["p1"]["decision"], results["p4"]["decision"]
            cv = read(RUN / "cv_states" / f"{item}.json")["cameras"][0]
            gates = {"score": d["p_incident"] is not None and d["p_incident"] <= threshold,
                     "review": not d["human_review_required"], "category": d["category"] == "no_clear_incident",
                     "confidence": d["confidence"] >= .90, "refusal": not d["refused_questions"]}
            rows.append({"item_id": item, "label": label["triage_label"], "score": d["p_incident"],
                         "category": d["category"], "confidence": d["confidence"], "gates": gates,
                         "p4_surface": bool(d4["is_incident"] or d4["human_review_required"] or d4["refused_questions"]),
                         "people_max": cv["detection_summary"]["person_count_max"], "tracks_total": len(cv["tracks"]),
                         "short_tracks": sum(t["reliability"]["observed_frames"] < 2 for t in cv["tracks"]),
                         "pair_count": len(cv["pairwise_interactions"]), "cv_reliability": cv["quality"]["overall_cv_reliability"],
                         "dropout_missing": cv["quality"]["detection_dropout_rate"] is None})
            cv_ms.append(sum(read(RUN / "cv_logs" / f"{item}.json")["timing"].values()))
            for model, result in results.items():
                u = result["usage"]
                det = u.get("input_tokens_details") or {}
                n, o, c, w = u["input_tokens"], u["output_tokens"], det.get("cached_tokens") or 0, det.get("cache_write_tokens") or 0
                long = n > pricing["long_context_threshold_tokens"]
                if model == "p1":
                    cost = n * .10 * (2 if long else 1) / 1e6
                else:
                    cost = ((n-c-w)*pricing["input_usd_per_1m_tokens"] + c*pricing["cached_input_usd_per_1m_tokens"]
                            + w*pricing["cache_write_usd_per_1m_tokens"]) * (2 if long else 1) / 1e6
                    cost += o*pricing["output_usd_per_1m_tokens"] * (1.5 if long else 1) / 1e6
                costs[model].append(cost)
                for key, value in zip(("input", "output", "cached", "cache_write"), (n, o, c, w)):
                    tokens[model][key].append(value)
                for key, value in (("api_last_attempt_ms", result["api_timing"]["last_attempt_ms"]),
                                   ("api_total_ms", result["api_timing"]["total_including_retries_ms"]),
                                   ("full_harness_ms", result["full_harness_ms"])):
                    timing[model][key].append(value)
        groups = {}
        for label in sorted({row["label"] for row in rows}):
            subset = [row for row in rows if row["label"] == label]
            groups[label] = {"n": len(subset), "score_summary": summary([row["score"] for row in subset]),
                             "failed_gates_nonexclusive": {g: sum(not row["gates"][g] for row in subset) for g in gates},
                             "suppressed": sum(all(row["gates"].values()) for row in subset),
                             "p4_surfaced": sum(row["p4_surface"] for row in subset),
                             "category_counts": dict(collections.Counter(row["category"] for row in subset))}
        report["splits"][split] = {"groups": groups, "fixed_policy_rows": rows,
            "cost_usd": {m: summary(v) for m, v in costs.items()},
            "usage_tokens": {m: {k: summary(v) for k, v in kv.items()} for m, kv in tokens.items()},
            "timing_ms": {m: {k: summary(v) for k, v in kv.items()} for m, kv in timing.items()},
            "cv_component_sum_ms": summary(cv_ms),
            "danger_types": dict(collections.Counter(g.get("danger_type_if_any") for g in gt.values() if g["reference_binary"] == "DANGER"))}
    report["split_overlaps"] = {key: sorted({g[key] for g in labels["calibration"].values()} & {g[key] for g in labels["test"].values()})
                               for key in ("scene_group_id", "split_group_id", "source_video_id", "source_sha256")}
    checks = []
    locks = [(ROOT, RUN / "HARNESS_LOCK.json", "sha256"),
             (ROOT / "benchmark_triage_v1", ROOT / "benchmark_triage_v1/BENCHMARK_LOCK.json", "sha256")]
    for name, filename in (("p1_decisions", "p1_freeze.json"), ("p4_gpt61_sol_vision", "p4_freeze.json"),
                           ("common_adapter_v2", "common_adapter_v2_freeze.json")):
        base = ROOT / "experiments" / name
        locks.append((base, base / "freeze" / filename, "hashes"))
    for base, lock_path, key in locks:
        lock = read(lock_path)
        drift = [p for p, h in lock[key].items() if not (base/p).is_file() or digest(base/p) != h]
        checks.append({"lock": str(lock_path.relative_to(ROOT)), "checked": len(lock[key]), "drift": drift})
    final = read(RUN / "RESULTS_LOCK.json")
    policy_hash = digest(RUN / "routing_policy_lock.json")
    final_ok = digest(RUN / "analysis/final_test_evaluation.json") == final["final_test_report_sha256"] and policy_hash == final["routing_policy_sha256"]
    frozen_report = read(RUN / "analysis/final_test_evaluation.json")
    result_drifts = [key for key, h in frozen_report["test_result_hashes"].items()
                     if digest(RUN / key.split('/')[0] / "results" / f"{key.split('/')[1]}.json") != h]
    report["integrity"] = {"locks": checks, "final_report_and_policy_match": final_ok, "test_result_drift": result_drifts}
    report["zero_event_one_sided_95_upper_bound_iid_assumption"] = {str(n): 1-.05**(1/n) for n in (3, 10, 13)}
    report["independent_zero_event_sample_target"] = {str(t): math.ceil(math.log(.05)/math.log(1-t)) for t in (.01, .005, .001)}
    p1, p4 = (report["splits"]["test"]["cost_usd"][m]["mean"] for m in ("p1", "p4"))
    report["monthly_scenarios_not_forecasts"] = [{"cameras": cam, "candidates_per_camera_day": freq, "days": 30,
        "candidates": cam*freq*30, "p4_rate": rate, "p1_calls": cam*freq*30,
        "p4_calls": cam*freq*30*rate, "api_usd": cam*freq*30*(p1+rate*p4)}
        for cam, freq in ((50, 2), (100, 10), (500, 20)) for rate in (1.0, .75, .5, .25)]
    report["p4_avoidance_break_even_fraction_vs_p4_only"] = p1/p4
    (OUT / "audit_metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT / "audit_metrics.json"), "integrity": report["integrity"],
                      "split_overlaps": report["split_overlaps"], "test_cost": {"p1": p1, "p4": p4}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
