"""Step 4 — broad candidate pool, scene grouping, de-duplication and review-queue selection.

Selection inputs are ONLY: source metadata/annotation timing, visual scene identity, generic CV discovery
features (person count, motion, low posture, close pair, speed, brightness) and a fixed seed (477).
No P0-P4 prediction, cascade threshold or evaluator output is read.

suggested_candidate_type / discovery_hints are NOT labels. Final labels come only from human review.

Writes:
  candidate_pool/candidates.csv          every generated window + features + filter/dedup status
  manifests/scene_manifest.json          visual scene views and physical split groups
  manifests/source_manifest.json         per source video: scene, split group, reasoning-v1 relation
  review/human_review_queue.csv          selected candidates for human review (labels empty)
  review/human_review_queue_reviewer2.csv  second independent review subset (all danger + 20 others)
"""
from __future__ import annotations

import json
import random
from collections import Counter, defaultdict

import cv2
import numpy as np

from _common import (BENCH, MANIFESTS, POOL, REVIEW, SEED, WINDOW_SEC, WORK, read_json, write_csv, write_json)

FRAMES, FEATS = WORK / "frames", WORK / "features"

# discovery heuristics (generic, fixed before looking at any candidate; NOT labels)
LOW_ASPECT = 1.0            # bbox h/w below this -> low/horizontal body
LOW_TORSO = 0.5             # torso verticality below this -> torso far from vertical
CLOSE_PAIR = 0.75           # centre distance < 0.75 x mean bbox height
RUN_SPEED_BH = 1.5          # body heights per second
DARK = 50                   # mean grey (0-255) on 160x90
CROWD = 4
VIEW_OWN_MAX = 0.40          # a source whose background matches its own header view below this...
VIEW_MARGIN = 0.10          # ...and matches another view at least this much better is visually reassigned
NEAR_DUP_HAMMING = 6        # per-frame dHash distance for near duplicates
CAPS = {"normal_per_view": 8, "empty_per_view": 2, "post_event_per_view": 2, "danger_per_view": 3, "danger_per_split_group": 6}

QUEUE_FIELDS = ["candidate_id", "scene_group_id", "split_group_id", "source_video_id", "start_sec", "end_sec",
                "window_kind", "suggested_candidate_type", "discovery_hints", "source_label",
                "related_to_reasoning_benchmark", "contact_sheet", "review_clip",
                "review_label", "review_confidence", "observable_summary", "danger_type_if_any",
                "hard_negative_type_if_any", "normal_subtype", "ambiguous_reason", "exclude_reason",
                "reviewer", "reviewed_at"]


# ----------------------------------------------------------------------------- helpers
def dhash(img_gray: np.ndarray) -> int:
    s = cv2.resize(img_gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (s[:, 1:] > s[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def low(p: dict) -> bool:
    return p["aspect_hw"] < LOW_ASPECT or p.get("torso_vertical", 1.0) < LOW_TORSO


def centre_h(p: dict):
    x1, y1, x2, y2 = p["box"]
    return ((x1 + x2) / 2, (y1 + y2) / 2), (y2 - y1)


def window_features(frames: list[dict]) -> dict:
    n = len(frames)
    if n == 0:
        return {"n_frames": 0}
    pc = [len(f["people"]) for f in frames]
    low_flags = [any(low(p) for p in f["people"]) for f in frames]
    close = 0
    for f in frames:
        ps = f["people"]
        hit = False
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                (ci, hi), (cj, hj) = centre_h(ps[i]), centre_h(ps[j])
                if np.hypot(ci[0] - cj[0], ci[1] - cj[1]) < CLOSE_PAIR * (hi + hj) / 2:
                    hit = True
        close += hit
    speeds = []
    for a, b in zip(frames, frames[1:]):
        dt = max(b["t"] - a["t"], 1e-3)
        for p in b["people"]:
            (cb, hb) = centre_h(p)
            best = None
            for q in a["people"]:
                (ca, ha) = centre_h(q)
                d = np.hypot(ca[0] - cb[0], ca[1] - cb[1]) / max((ha + hb) / 2, 1)
                best = d if best is None or d < best else best
            if best is not None:
                speeds.append(best / dt)
    low_idx = [i for i, v in enumerate(low_flags) if v]
    recover = bool(low_idx) and any(pc[k] > 0 and not low_flags[k] for k in range(low_idx[0] + 1, n))
    heights = [centre_h(p)[1] for f in frames for p in f["people"]]
    return {
        "n_frames": n,
        "person_frames_frac": round(sum(c > 0 for c in pc) / n, 3),
        "max_persons": max(pc), "mean_persons": round(float(np.mean(pc)), 2),
        "low_posture_frac": round(sum(low_flags) / n, 3), "low_then_upright": recover,
        "close_pair_frac": round(close / n, 3),
        "max_speed_bh_s": round(float(np.percentile(speeds, 90)), 2) if speeds else 0.0,
        "motion_mean": round(float(np.mean([f["motion"] for f in frames[1:]] or [0])), 2),
        "brightness_mean": round(float(np.mean([f["brightness"] for f in frames])), 1),
        "median_person_h_px": round(float(np.median(heights)), 1) if heights else 0.0,
    }


def hints_for(feat: dict) -> list[str]:
    h = []
    if feat.get("n_frames", 0) == 0:
        return ["no_frames"]
    if feat["person_frames_frac"] == 0:
        h.append("empty_scene")
        if feat["motion_mean"] > 6:
            h.append("HN15_visual_motion_no_person")
        return h
    if feat["low_posture_frac"] > 0:
        h.append("HN01_HN09_low_then_upright" if feat["low_then_upright"] else "HN02_HN14_low_posture_sustained")
    if feat["close_pair_frac"] > 0:
        h.append("HN06_HN07_close_pair")
    if feat["max_speed_bh_s"] > RUN_SPEED_BH:
        h.append("HN03_fast_movement")
    if feat["brightness_mean"] < DARK:
        h.append("HN11_dark")
    if feat["max_persons"] >= CROWD:
        h.append("HN12_multiple_people")
    if 0 < feat["median_person_h_px"] < 40:
        h.append("HN10_small_or_distant_person")
    return h


# ----------------------------------------------------------------------------- scene grouping
def background_signature(src_id: str) -> np.ndarray:
    fr = json.load(open(FRAMES / src_id / "frames.json"))["frames"]
    idx = np.linspace(0, len(fr) - 1, min(15, len(fr))).astype(int)
    stack = [cv2.resize(cv2.imread(str(FRAMES / src_id / fr[i]["file"]), cv2.IMREAD_GRAYSCALE), (64, 36)).astype(np.float32)
             for i in idx]
    med = np.median(np.stack(stack), axis=0)
    # local structure, not brightness: edge map of the median background
    gx, gy = cv2.Sobel(med, cv2.CV_32F, 1, 0), cv2.Sobel(med, cv2.CV_32F, 0, 1)
    e = np.hypot(gx, gy).flatten()
    return (e - e.mean()) / (e.std() + 1e-6)


class UF:
    def __init__(self, items):
        self.p = {i: i for i in items}

    def f(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


REASSIGNED: list[dict] = []


def group_scenes(sources: list[dict]) -> tuple[dict, dict]:
    """Camera view = metadata group (dataset, category, place, camera), visually corrected.

    Pure visual clustering over-splits (season lighting and small per-take camera shifts), which would let
    more clips of one background through the per-scene cap. So metadata groups are the default, and a source
    is moved to another group only when its background clearly matches that group and not its own
    (mean correlation to own group < VIEW_OWN_MAX and to the other group > own + VIEW_MARGIN).
    """
    ids = [s["source_id"] for s in sources]
    sig = {i: background_signature(i) for i in ids}
    corr = lambda a, b: float(np.mean(sig[a] * sig[b]))
    meta = {s["source_id"]: (s["dataset"], s["category"], s["place"], s["camera"]) for s in sources}
    groups = defaultdict(list)
    for i in ids:
        groups[meta[i]].append(i)
    assign = dict(meta)
    for i in ids:
        own = [j for j in groups[meta[i]] if j != i]
        own_c = np.mean([corr(i, j) for j in own]) if own else 1.0
        best_g, best_c = None, -1.0
        for g, mem in groups.items():
            if g == meta[i] or g[0] != meta[i][0]:
                continue
            c = float(np.mean([corr(i, j) for j in mem]))
            if c > best_c:
                best_g, best_c = g, c
        if own_c < VIEW_OWN_MAX and best_g is not None and best_c > own_c + VIEW_MARGIN:
            assign[i] = best_g
            REASSIGNED.append({"source_id": i, "header_view": "/".join(meta[i][1:]), "visual_view": "/".join(best_g[1:]),
                               "mean_corr_own": round(float(own_c), 3), "mean_corr_matched": round(best_c, 3)})
    view = UF(ids)
    by_view = defaultdict(list)
    for i in ids:
        by_view[assign[i]].append(i)
    for mem in by_view.values():
        for m in mem[1:]:
            view.u(mem[0], m)
    # split groups: same view OR same staged take (same actors / same recording) -> must stay together
    split = UF(ids)
    for a in ids:
        split.u(a, view.f(a))
    by_take = defaultdict(list)
    for s in sources:
        by_take[(s["dataset"], s["take_id"])].append(s["source_id"])
    for members in by_take.values():
        for m in members[1:]:
            split.u(members[0], m)
    for a in ids:
        split.u(a, view.f(a))

    def name_groups(uf, prefix):
        roots = sorted({uf.f(i) for i in ids}, key=lambda r: min(i for i in ids if uf.f(i) == r))
        nm = {r: f"{prefix}{k+1:02d}" for k, r in enumerate(roots)}
        return {i: nm[uf.f(i)] for i in ids}

    return name_groups(view, "SCN_"), name_groups(split, "SPG_")


# ----------------------------------------------------------------------------- windows
def tile(region: list[float]) -> list[float]:
    a, b = region
    starts, s = [], a
    while s + WINDOW_SEC <= b + 1e-6:
        starts.append(round(s, 3))
        s += WINDOW_SEC
    return starts


def danger_windows(src: dict) -> list[float]:
    a, b = src["danger_region_sec"]
    dur = src["video"]["duration"]
    if src["dataset"] != "aihub_171_abnormal_cctv":
        return [0.0]                                     # whole short clip
    cat = src["category"]
    lead = {"swoon01": 10.0, "trespass01": 15.0, "trespass03": 10.0}.get(cat, 5.0)
    return [round(min(max(0.0, a - lead), max(0.0, dur - WINDOW_SEC)), 3)]


def main() -> None:
    rnd = random.Random(SEED)
    srcs = read_json(POOL / "candidate_sources.json")["sources"]
    by_id = {s["source_id"]: s for s in srcs}
    view_of, split_of = group_scenes(srcs)
    v1_views = {view_of[s["source_id"]] for s in srcs if s["used_in_reasoning_v1"]}
    v1_splits = {split_of[s["source_id"]] for s in srcs if s["used_in_reasoning_v1"]}

    feats = {s["source_id"]: json.load(open(FEATS / f"{s['source_id']}.json"))["frames"] for s in srcs}

    pool = []
    for s in srcs:
        sid = s["source_id"]
        kinds = [("pre_event", t) for t in tile(s["pre_event_region_sec"])] + \
                [("post_event", t) for t in tile(s["post_event_region_sec"])] + \
                [("event", t) for t in danger_windows(s)]
        fr_all = json.load(open(FRAMES / sid / "frames.json"))["frames"]
        for kind, st in kinds:
            en = round(min(st + WINDOW_SEC, s["video"]["duration"]), 3)
            wf = [f for f in feats[sid] if st <= f["t"] < en]
            wfr = [f for f in fr_all if st <= f["t"] < en]
            idx = np.linspace(0, len(wfr) - 1, 4).astype(int) if wfr else []
            hashes = [dhash(cv2.imread(str(FRAMES / sid / wfr[i]["file"]), cv2.IMREAD_GRAYSCALE)) for i in idx]
            feat = window_features(wf)
            hints = hints_for(feat) if kind != "event" else ["source_event_window"]
            if kind == "event":
                stype = "danger_source_candidate" if s["category"] != "trespass03" else "entry_event_candidate"
            elif "empty_scene" in hints:
                stype = "possible_clear_normal_empty"
            elif any(h.startswith("HN") for h in hints):
                stype = "possible_hard_negative"
            else:
                stype = "possible_clear_normal"
            if kind == "post_event":
                stype = "post_event_candidate:" + stype
            pool.append({
                "window_id": f"{sid}@{st:07.1f}", "source_video_id": sid, "dataset": s["dataset"],
                "category": s["category"], "take_id": s["take_id"], "camera": s["camera"],
                "scene_group_id": view_of[sid], "split_group_id": split_of[sid],
                "window_kind": kind, "start_sec": st, "end_sec": en, "duration_sec": round(en - st, 3),
                "suggested_candidate_type": stype, "discovery_hints": "|".join(hints),
                "source_label": s["known_annotation"]["source_label"],
                "source_event_sec": json.dumps([s["known_annotation"].get("event_start_sec"), s["known_annotation"].get("event_end_sec")]),
                "seconds_before_first_annotated_action": (round(s["danger_region_sec"][0] - en, 1) if kind == "pre_event" else ""),
                "same_source_video_as_reasoning_v1": s["used_in_reasoning_v1"],
                "same_scene_view_as_reasoning_v1": view_of[sid] in v1_views,
                "same_split_group_as_reasoning_v1": split_of[sid] in v1_splits,
                "frame_dhash": "|".join(f"{h:016x}" for h in hashes),
                **feat,
            })

    # ---------------- filtering + dedup ----------------
    status = {}
    for w in pool:
        if w["same_source_video_as_reasoning_v1"]:
            status[w["window_id"]] = "removed:same_source_video_as_reasoning_v1"
        elif w.get("n_frames", 0) < 10:
            status[w["window_id"]] = "removed:too_few_frames"
        elif w["brightness_mean"] < 8:
            status[w["window_id"]] = "removed:black_or_unusable"
    exact, near = 0, 0
    kept_by_view = defaultdict(list)
    for w in sorted(pool, key=lambda w: (w["scene_group_id"], w["source_video_id"], w["start_sec"])):
        if w["window_id"] in status:
            continue
        hs = [int(h, 16) for h in w["frame_dhash"].split("|") if h]
        dup = None
        for o in kept_by_view[w["scene_group_id"]]:
            oh = [int(h, 16) for h in o["frame_dhash"].split("|") if h]
            # windows with people are distinct moments even on the same background: never hash-deduped
            # (the per-scene caps handle that redundancy). Only person-free static windows are compared.
            if w["person_frames_frac"] != 0 or o["person_frames_frac"] != 0 or len(hs) != len(oh):
                continue
            if hs == oh:
                dup = ("exact", o)          # identical 4-frame perceptual hash (not byte-identical media)
                break
            if all(hamming(a, b) <= NEAR_DUP_HAMMING for a, b in zip(hs, oh)):
                dup = ("near", o)
                break
        if dup:
            status[w["window_id"]] = f"removed:{dup[0]}_duplicate_of:{dup[1]['window_id']}"
            exact += dup[0] == "exact"
            near += dup[0] == "near"
        else:
            kept_by_view[w["scene_group_id"]].append(w)
            status[w["window_id"]] = "kept"
    for w in pool:
        w["pool_status"] = status[w["window_id"]]

    # ---------------- review-queue selection (diversity, deterministic) ----------------
    selected = []
    danger_per_split = Counter()
    for view in sorted(kept_by_view):
        ws = kept_by_view[view]
        danger = [w for w in ws if w["window_kind"] == "event"]
        rnd.shuffle(danger)
        # distinct takes first (different actors/attempts), then fill; capped per view and per split group
        firsts, rest, seen_take = [], [], set()
        for w in danger:
            (rest if w["take_id"] in seen_take else firsts).append(w)
            seen_take.add(w["take_id"])
        pick = []
        for w in firsts + rest:
            if len(pick) >= CAPS["danger_per_view"] or danger_per_split[w["split_group_id"]] >= CAPS["danger_per_split_group"]:
                break
            pick.append(w)
            danger_per_split[w["split_group_id"]] += 1
        selected += pick

        normals = [w for w in ws if w["window_kind"] != "event"]
        buckets = defaultdict(list)
        for w in normals:
            hs = [h for h in w["discovery_hints"].split("|") if h.startswith("HN")]
            key = ("post:" if w["window_kind"] == "post_event" else "") + (hs[0] if hs else
                   ("empty" if "empty_scene" in w["discovery_hints"] else "plain_activity"))
            buckets[key].append(w)
        for b in buckets.values():
            rnd.shuffle(b)
        order = sorted(buckets, key=lambda k: (len(buckets[k]), k))       # rarest hint first
        pick, n_empty, n_post, used_src_window = [], 0, 0, set()
        while len(pick) < CAPS["normal_per_view"] and any(buckets[k] for k in order):
            for k in order:
                if not buckets[k] or len(pick) >= CAPS["normal_per_view"]:
                    continue
                w = buckets[k].pop(0)
                if k.endswith("empty"):
                    if n_empty >= CAPS["empty_per_view"]:
                        continue
                    n_empty += 1
                if k.startswith("post:"):
                    if n_post >= CAPS["post_event_per_view"]:
                        continue
                    n_post += 1
                # avoid temporally adjacent windows of the same source video
                adj = any(o["source_video_id"] == w["source_video_id"] and abs(o["start_sec"] - w["start_sec"]) <= WINDOW_SEC
                          for o in pick)
                if adj:
                    continue
                pick.append(w)
        selected += pick

    selected.sort(key=lambda w: (w["scene_group_id"], w["window_kind"] == "event", w["source_video_id"], w["start_sec"]))
    for i, w in enumerate(selected):
        w["candidate_id"] = f"CAND_{i+1:04d}"
        w["pool_status"] = "kept:sent_to_review"
    sel_ids = {w["window_id"]: w["candidate_id"] for w in selected}
    for w in pool:
        w["candidate_id"] = sel_ids.get(w["window_id"], "")
        if w["pool_status"] == "kept" and not w["candidate_id"]:
            w["pool_status"] = "kept:not_selected_scene_cap"

    write_csv(POOL / "candidates.csv", pool)

    queue = []
    for w in selected:
        queue.append({
            "candidate_id": w["candidate_id"], "scene_group_id": w["scene_group_id"], "split_group_id": w["split_group_id"],
            "source_video_id": w["source_video_id"], "start_sec": w["start_sec"], "end_sec": w["end_sec"],
            "window_kind": w["window_kind"], "suggested_candidate_type": w["suggested_candidate_type"],
            "discovery_hints": w["discovery_hints"], "source_label": w["source_label"],
            "related_to_reasoning_benchmark": w["same_scene_view_as_reasoning_v1"] or w["same_split_group_as_reasoning_v1"],
            "contact_sheet": f"review/contact_sheets/{w['candidate_id']}.jpg",
            "review_clip": f"review/clips/{w['candidate_id']}.mp4",
        })
    write_csv(REVIEW / "human_review_queue.csv", queue, QUEUE_FIELDS)

    # second-reviewer subset: all danger/entry candidates + 20 possible hard negatives (seeded)
    hn = [q for q in queue if "hard_negative" in q["suggested_candidate_type"]]
    random.Random(SEED).shuffle(hn)
    r2 = [q for q in queue if q["window_kind"] == "event"] + sorted(hn[:20], key=lambda q: q["candidate_id"])
    write_csv(REVIEW / "human_review_queue_reviewer2.csv",
              [{k: q[k] for k in ["candidate_id", "contact_sheet", "review_clip", "start_sec", "end_sec"]} for q in r2],
              ["candidate_id", "contact_sheet", "review_clip", "start_sec", "end_sec"] + QUEUE_FIELDS[13:])

    # manifests
    views = defaultdict(list)
    for s in srcs:
        views[view_of[s["source_id"]]].append(s)
    write_json(MANIFESTS / "scene_manifest.json", {
        "definition": {
            "scene_group_id": "camera view = (dataset, category, place, camera) header group, visually corrected by median-background edge-map correlation (see reassigned_sources); max 3 final clips per scene_group",
            "split_group_id": "connected component of scene views + staged takes (same actors / same recording session). The calibration/test split unit.",
            "note": "Header 'place'/'cam' labels were NOT trusted for identity: e.g. swoon cam01 and cam02 are different physical places, and 710-3 cam01 summer matches the cam02 night view visually.",
        },
        "scene_groups": {v: {"split_group_id": split_of[m[0]["source_id"]], "n_sources": len(m),
                             "categories": sorted({x["category"] for x in m}), "cameras": sorted({x["camera"] for x in m}),
                             "takes": sorted({x["take_id"] for x in m}), "related_to_reasoning_v1": v in v1_views,
                             "split_group_related_to_reasoning_v1": split_of[m[0]["source_id"]] in v1_splits,
                             "example_thumbnail": m[0]["thumbnail"]} for v, m in sorted(views.items())},
        "split_groups": sorted(set(split_of.values())),
        "reassigned_sources": REASSIGNED,
    })
    write_json(MANIFESTS / "source_manifest.json", {"sources": [
        {"source_id": s["source_id"], "dataset": s["dataset"], "original_path": s["original_path"],
         "local_read_path": s["local_read_path"], "scene_group_id": view_of[s["source_id"]],
         "split_group_id": split_of[s["source_id"]], "used_in_reasoning_v1": s["used_in_reasoning_v1"],
         "character": s["character"], "season": s["season"], "camera": s["camera"]} for s in srcs]})

    c = Counter(w["pool_status"].split(":")[0] + ":" + (w["pool_status"].split(":")[1] if ":" in w["pool_status"] else "") for w in pool)
    print("pool", len(pool), dict(c))
    print("exact dup", exact, "near dup", near)
    print("scene views", len(views), "split groups", len(set(split_of.values())))
    print("queue", len(queue), Counter(q["suggested_candidate_type"] for q in queue))
    print("reviewer2", len(r2))


if __name__ == "__main__":
    main()
