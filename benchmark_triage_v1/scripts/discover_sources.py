"""Step 1 — discover every local source video usable for 477-triage-normal-v1.

Inputs (read only): AI Hub 171 swoon/trespass (data/recovered), AI Hub 171 fight (downloads ZIP),
AI Hub 71953 multi-view fight (downloads ZIP), benchmark_v1 media build records (for overlap only).
ZIP members are copied to _work/source_cache/ (CRC-verified by zipfile); originals are untouched.

Writes candidate_pool/candidate_sources.json and candidate_pool/source_thumbs/*.jpg (one frame per
video, for scene identity checks). Uses NO model output of any kind.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from _common import (BENCH, EVENT_BUFFER_SEC, POOL, ROOT, WORK, assert_writable, ffprobe_fast, read_json, rel,
                     write_json)

AIHUB171 = ROOT / "data" / "recovered" / "19.이상행동CCTV"
FIGHT_ZIP = ROOT / "downloads" / "fight" / "19.이상행동CCTV" / "02.싸움(fight)" / "실내(원본)" / "insidedoor_04.zip"
MV_DIR = ROOT / "downloads" / "multiview_fight" / "21.다각도_CCTV_생활안전_데이터" / "3.개방데이터" / "2.데이터(NIA)" / "Validation"
MV_VIDEO_ZIP = MV_DIR / "01.원천데이터" / "VS_싸움_신체적충돌을동반한싸움.zip"
MV_LABEL_ZIP = MV_DIR / "02.라벨링데이터" / "VL_싸움_신체적충돌을동반한싸움.zip"
CACHE = WORK / "source_cache"

LICENSE_NOTE = ("AI Hub (aihub.or.kr) dataset; use is governed by AI Hub terms of use. Clips are derived for internal "
                "477 evaluation only; do not redistribute outside the project without checking the AI Hub license.")


def hms(s: str) -> float:
    h, m, sec = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(sec)


def parse_171_xml(text: str) -> dict:
    root = ET.fromstring(text)
    hdr = {c.tag: (c.text or "").strip() for c in root.find("header")}
    fps = float(hdr.get("fps") or 30)
    ev = root.find("event")
    ev_start = hms(ev.findtext("starttime"))
    ev_dur = hms(ev.findtext("duration"))
    actions = []
    for obj in root.findall("object"):
        for act in obj.findall("action"):
            for fr in act.findall("frame"):
                actions.append({"object": obj.findtext("objectname"), "action": act.findtext("actionname"),
                                "start_sec": round(int(fr.findtext("start")) / fps, 3),
                                "end_sec": round(int(fr.findtext("end")) / fps, 3)})
    return {"header": hdr, "event": {"name": ev.findtext("eventname"), "start_sec": ev_start,
                                     "end_sec": round(ev_start + ev_dur, 3)}, "actions": actions}


def extract_member(z: zipfile.ZipFile, member: str, dest: Path) -> Path:
    dest = assert_writable(dest)
    info = z.getinfo(member)
    if dest.exists() and dest.stat().st_size == info.file_size:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with z.open(member) as src, open(tmp, "wb") as out:      # zipfile raises BadZipFile on CRC mismatch
        shutil.copyfileobj(src, out, 1 << 22)
    tmp.replace(dest)
    return dest


def reasoning_v1_usage() -> dict[str, list[dict]]:
    """source video filename -> windows used by 477-reasoning-v1 (overlap audit only)."""
    rec = read_json(ROOT / "benchmark_v1" / "private_ground_truth" / "media_build_records.json")
    used: dict[str, list[dict]] = {}
    for clip, r in rec.items():
        name = re.split(r"[\\/]", r["source_path"])[-1]
        used.setdefault(name, []).append({"benchmark_clip": clip, "start_sec": r["source_clip_start_sec"],
                                          "end_sec": r["source_clip_end_sec"]})
    return used


def thumb(video: Path, t: float, out: Path) -> None:
    out = assert_writable(out)
    if out.exists():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                    "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", str(out)], check=True)


def main() -> None:
    used = reasoning_v1_usage()
    sources = []

    # --- AI Hub 171 swoon / trespass (already extracted locally) -------------------------------
    for mp4 in sorted(AIHUB171.glob("*/실외/extracted/*/*.mp4")):
        xml = mp4.with_suffix(".xml")
        ann = parse_171_xml(xml.read_text(encoding="utf-8"))
        sources.append({"path": mp4, "xml_path": rel(xml), "dataset": "aihub_171_abnormal_cctv", "ann": ann,
                        "origin": "local_extracted"})

    # --- AI Hub 171 fight (ZIP members -> cache) ----------------------------------------------
    with zipfile.ZipFile(FIGHT_ZIP) as z:
        for m in sorted(n for n in z.namelist() if n.endswith(".mp4")):
            ann = parse_171_xml(z.read(m[:-4] + ".xml").decode("utf-8"))
            dest = extract_member(z, m, CACHE / "aihub171_fight" / m)
            sources.append({"path": dest, "xml_path": f"{rel(FIGHT_ZIP)}::{m[:-4]}.xml", "zip_member": f"{rel(FIGHT_ZIP)}::{m}",
                            "dataset": "aihub_171_abnormal_cctv", "ann": ann, "origin": "zip_member_cached"})

    # --- AI Hub 71953 multi-view fight -------------------------------------------------------
    with zipfile.ZipFile(MV_LABEL_ZIP) as zl, zipfile.ZipFile(MV_VIDEO_ZIP) as zv:
        for jn in sorted(n for n in zl.namelist() if n.endswith(".json")):
            lab = __import__("json").loads(zl.read(jn).decode("utf-8"))
            for v in lab["videos"]:
                member = f"{jn.split('/')[0]}/{v['filename']}"
                dest = extract_member(zv, member, CACHE / "aihub71953_fight" / member)
                sources.append({"path": dest, "zip_member": f"{rel(MV_VIDEO_ZIP)}::{member}",
                                "xml_path": f"{rel(MV_LABEL_ZIP)}::{jn}", "dataset": "aihub_71953_multiview_cctv",
                                "origin": "zip_member_cached",
                                "mv": {"event_id": jn.split("/")[0], "view": v["view"], "site": v["cctv_distribution"],
                                       "camera_model": v["cctv_camera"], "angle": v["cctv_angle"], "date": v["date"],
                                       "time": v["time"], "event_class": lab["annotations"]["event_class"]}})

    out = []
    for s in sources:
        p: Path = s["path"]
        meta = ffprobe_fast(p)
        name = p.name
        if s["dataset"] == "aihub_171_abnormal_cctv":
            m = re.match(r"(?P<take>\d+-\d+)_(?P<cam>cam\d+)_(?P<cat>[a-z]+)(?P<catn>\d+)_(?P<place>place\d+)_(?P<tod>[a-z]+)_(?P<season>[a-z]+)", name)
            hdr, ev, acts = s["ann"]["header"], s["ann"]["event"], s["ann"]["actions"]
            first_action = min([a["start_sec"] for a in acts] + [ev["start_sec"]])
            last_action = max([a["end_sec"] for a in acts] + [ev["end_sec"]])
            excl_start = max(0.0, first_action - EVENT_BUFFER_SEC)
            excl_end = min(meta["duration"], last_action + EVENT_BUFFER_SEC)
            rec = {
                "source_id": p.stem, "dataset": s["dataset"], "category": m["cat"] + m["catn"],
                "take_id": m["take"], "camera": m["cam"], "place": m["place"], "season": m["season"],
                "time_of_day": m["tod"], "inout": hdr.get("inout"), "location_header": hdr.get("location"),
                "weather": hdr.get("weather"), "population": hdr.get("population"), "character": hdr.get("character"),
                "known_annotation": {"source_label": ev["name"], "event_start_sec": ev["start_sec"],
                                     "event_end_sec": ev["end_sec"], "actions": acts},
                "event_exclusion_sec": [round(excl_start, 3), round(excl_end, 3)],
                "pre_event_region_sec": [0.0, round(excl_start, 3)],
                "post_event_region_sec": [round(excl_end, 3), round(meta["duration"], 3)],
                "danger_region_sec": [round(first_action, 3), round(last_action, 3)],
            }
        else:
            mv = s["mv"]
            rec = {
                "source_id": p.stem, "dataset": s["dataset"], "category": "fight_mv", "take_id": mv["event_id"],
                "camera": mv["view"], "place": mv["site"], "season": None, "time_of_day": None, "inout": None,
                "location_header": mv["site"], "weather": None, "population": None, "character": None,
                "camera_model": mv["camera_model"], "recorded": f"{mv['date']} {mv['time']}",
                "known_annotation": {"source_label": mv["event_class"], "note": "whole clip is the annotated event; no pre-event region"},
                "event_exclusion_sec": [0.0, round(meta["duration"], 3)],
                "pre_event_region_sec": [0.0, 0.0], "post_event_region_sec": [round(meta["duration"], 3)] * 2,
                "danger_region_sec": [0.0, round(meta["duration"], 3)],
            }
        u = used.get(name, [])
        rec.update({
            "original_path": s.get("zip_member") or rel(p), "annotation_path": s["xml_path"],
            "local_read_path": rel(p), "origin": s["origin"],
            "video": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in meta.items()},
            "used_in_reasoning_v1": bool(u), "reasoning_v1_windows": u,
            "licensing_note": LICENSE_NOTE,
        })
        t = 20.0 if rec["pre_event_region_sec"][1] > 25 else max(1.0, meta["duration"] / 2)
        thumb(p, t, POOL / "source_thumbs" / f"{rec['source_id']}.jpg")
        rec["thumbnail"] = f"candidate_pool/source_thumbs/{rec['source_id']}.jpg"
        rec["thumbnail_t_sec"] = t
        out.append(rec)

    write_json(POOL / "candidate_sources.json", {
        "benchmark": "477-triage-normal-v1", "stage": "source discovery",
        "searched": ["data/recovered/19.이상행동CCTV/*/실외/extracted (AI Hub 171 swoon, trespass)",
                     f"{rel(FIGHT_ZIP)} (AI Hub 171 fight, ZIP)",
                     f"{rel(MV_VIDEO_ZIP)} + labels (AI Hub 71953 multi-view fight)",
                     "benchmark_v1/private_ground_truth/media_build_records.json (overlap audit only)"],
        "not_found": "No normal/benign-class dataset exists locally. Normal candidates can only come from pre/post-event regions of abnormal-scenario videos.",
        "source_count": len(out), "sources": out})
    print(f"sources={len(out)}  used_in_reasoning_v1={sum(r['used_in_reasoning_v1'] for r in out)}")


if __name__ == "__main__":
    main()
