"""Inspect local mock videos; never run inference or derive incident labels."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
MEDIA = ROOT / "data/mock_cctv/media"
SOURCES = [
    ("사건2-개큰사건다각도.mp4", "사건2 · 다른 시점"),
    ("사건2-개큰사건.mp4", "사건2 · 원본"),
    ("사건8-대로일상.mp4", "대로 일상"),
    ("사건1-아리까리사건.mp4", "사건1"),
    ("사건3-일상도로.mp4", "일상 도로"),
    ("사건4-비둘기일상.mp4", "비둘기 일상"),
    ("사건5-자전거일상.mp4", "자전거 일상"),
    ("사건6-큰교차로일상.mp4", "큰 교차로 일상"),
    ("사건7-학교일상.mp4", "학교 일상"),
]


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    cameras = []
    for i, (source, title) in enumerate(SOURCES, 1):
        camera_id = f"CAM_{i:02d}"
        path = MEDIA / f"{camera_id}.mp4"
        info = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)
        ], encoding="utf-8"))
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        duration = float(info["format"]["duration"])
        if duration <= 0 or video["width"] <= 0 or video["height"] <= 0:
            raise ValueError(f"Invalid video: {camera_id}")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        cameras.append({
            "camera_id": camera_id, "title": title,
            "source_filename": source, "video_path": path.relative_to(ROOT).as_posix(),
            "stream_url": f"/stream/{camera_id}", "clip_ref": "MOCK_CLIP_03_V2" if i == 3 else f"MOCK_CLIP_{i:02d}",
            "duration_sec": duration, "width": video["width"], "height": video["height"],
            "video_codec": video["codec_name"], "pixel_format": video.get("pix_fmt"),
            "bytes": path.stat().st_size, "sha256": digest,
            "is_mock": True, "analysis_status": "not_analyzed", "loop": True, "muted": True,
            "reused_from": None,
            "source_group": f"source_{i:02d}",
            "same_event_group": "source_event_02" if i in (1, 2) else None,
            "synchronization_verified": False,
        })
    assert len({c["sha256"] for c in cameras}) == 9
    write_json("manifest.json", {
        "schema_version": "mock-cctv-1", "is_mock": True,
        "source_archive": "데모용-사건-영상-20261009T050528Z-1-001.zip",
        "additional_source_files": ["사건8-대로일상.mp4"],
        "unique_sources": 9, "camera_count": 9,
        "notes": "파일명/제공 자료에 따른 표시명이며 AI 판정이나 정답이 아님. 다각도 시간 동기화 미검증.",
        "cameras": cameras,
    })
    write_json("asset-map.json", {c["clip_ref"]: f'{c["camera_id"]}.mp4' for c in cameras})
    # Compatible with the existing backend; no invented incidents or risk scores.
    write_json("demo-scenario.json", {
        "schema_version": "demo-scenario-1", "decision_source": "scripted_not_ai",
        "cameras": [{
            "id": c["camera_id"], "region": c["title"], "sync_group": None,
            "offset_sec": 0, "role": "unassigned", "video_file": f'{c["camera_id"]}.mp4',
        } for c in cameras], "incidents": [],
    })
    print(f"Validated {len(cameras)} cameras / 9 unique videos; wrote manifests to {HERE}")


if __name__ == "__main__":
    main()
