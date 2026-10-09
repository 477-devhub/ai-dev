# Dataset structure

Windows native execution. Requested /mnt/d/projects/477 maps to D:/projects/477.

MP4 + same-directory, identical-stem XML. ZIP members use archive absolute path::member syntax; this is a locator, not an extracted file. No original renamed or changed.

XML: annotation/folder, filename, source, size, header, event, repeated object. Event interval = event/starttime + event/duration, seconds. Object/action/frame has inclusive-looking start/end indices; source frame indexing is not explicitly documented, so no zero/one-based assumption is asserted. Contact sheet indices are decoder zero-based indices.

Objects contain person keypoints at keyframes and action intervals. Keypoints are not bounding boxes. Population is an annotation value, not a measured visible-person count. No severity/risk/priority/confidence ground truth exists in these fields.

All XML parsed directly; source XML tree and SHA256 retained in inventory_details.json. ZIP not extracted for inventory. OpenCV is used because ffprobe/ffmpeg are absent from PATH. Fight metadata is annotation-only until candidate extraction.

## fight
- Videos: 54; paired XML: 54; MP4.
- Mean XML duration: 310.678 sec.
- FPS: [30.0]; resolution: [(3840, 2160)].
- Total video bytes: 20266886901.
- Action labels: ['falldown', 'kicking', 'pulling', 'punching', 'pushing', 'threaten'].
- Bbox present: 0; objects, keyframes and action frame intervals present.
- Event duration range: 102.6–248.3 sec.

## swoon
- Videos: 20; paired XML: 20; MP4.
- Mean XML duration: 300.655 sec.
- FPS: [30.0]; resolution: [(3840, 2160)].
- Total video bytes: 10969069465.
- Action labels: ['falldown', 'totter'].
- Bbox present: 0; objects, keyframes and action frame intervals present.
- Event duration range: 12.5–34.8 sec.

## trespass
- Videos: 44; paired XML: 44; MP4.
- Mean XML duration: 303.198 sec.
- FPS: [30.0]; resolution: [(3840, 2160)].
- Total video bytes: 26241502119.
- Action labels: ['climbwall', 'pulling', 'running', 'walking'].
- Bbox present: 0; objects, keyframes and action frame intervals present.
- Event duration range: 1.4–208.9 sec.

## Audit findings
- 710-2_cam02_swoon01_place01_day_spring.mp4: XML/video duration difference -0.867s
- 710-2_cam02_swoon01_place01_day_summer.mp4: XML/video duration difference 3.133s
- 710-3_cam01_swoon01_place01_day_summer.mp4: XML/video duration difference 2.133s
- 710-3_cam02_swoon01_place01_day_spring.mp4: XML/video duration difference -1.467s
- 710-3_cam02_swoon01_place01_day_summer.mp4: XML/video duration difference 4.233s
- 710-4_cam02_swoon01_place01_day_spring.mp4: XML/video duration difference 3.333s
- 710-4_cam02_swoon01_place01_day_summer.mp4: XML/video duration difference -13.367s
- 710-5_cam02_swoon01_place01_day_spring.mp4: XML/video duration difference 7.134s
- 710-5_cam02_swoon01_place01_day_summer.mp4: XML/video duration difference -3.167s
- 710-6_cam02_swoon01_place01_day_spring.mp4: XML/video duration difference 4.633s
- 710-6_cam02_swoon01_place01_day_summer.mp4: XML/video duration difference -4.067s
- Multiple camera/season versions share source IDs: candidates are not independent events. Keep related IDs together in any future split.
- Trespass annotations describe climbwall or pulling/walking; restricted-area geometry and legal access rights are not supplied.
- 145-5 cam02 spring trespass event is unusually long (208.9s); do not silently repair it.
## Candidate video crosscheck and visual audit

Fight candidates: 6 actual MP4 metadata checks; remaining 48 XML-only. All probed sources are 3840x2160 / 30 FPS (minor floating point rates retained). Reviewed videos: 30. S07–S13 source/visual day-night and event mismatch suspected; see excluded_review.json. No semantic re-pairing performed. No bbox in any of 118 XML files.
