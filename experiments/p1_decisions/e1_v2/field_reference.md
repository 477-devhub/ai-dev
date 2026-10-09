# E1 전체 Feature 및 필드 참조

Schema의 전체 경로 목록이다. 배열 tuple의 원소 의미는 Schema description과 README를 참조한다. Canonical metadata·signature는 모델 입력에서 제외한다.

## Canonical 전체 Feature

| 경로 | 타입 | Nullable | Schema 의미 |
|---|---|---|---|
| `state_version` | const "cv-state-v1" | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.layer` | const "shared_cheap_cv" | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.name` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.task` | const "pose" | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.weights_file` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.weights_sha256` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.library` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.library_version` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.precision` | enum ["fp16", "fp32"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.input_size` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.conf_threshold` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.iou_threshold` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_model.pretrained_only` | const true | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_config_sha256` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.cv_code_sha256` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.external_api_calls` | const 0 | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `generator.llm_or_vlm_used` | const false | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.item_id` | string | 아니오 | Harness metadata only; must not be shown to decision models as semantic input. |
| `input.task` | enum ["single", "attention", "multi_camera"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.frame_protocol` | const "uniform_total64_v1" | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.input_fingerprint` | string | 아니오 | SHA256 over per-camera SHA256 of the exact canonical RGB bytes. |
| `input.benchmark_input_fingerprint` | object | 아니오 | Exact load_model_input.load_item(...)['input_fingerprint']. |
| `input.total_frames` | const 64 | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.camera_ids` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.camera_ids[]` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.frames_per_camera` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `input.time_reference` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].camera_id` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].image_size` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].image_size[]` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frame_count` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].duration_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frame_fingerprint_sha256` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].sampling` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].sampling.timestamps_sec` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].sampling.timestamps_sec[]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].sampling.median_interval_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].sampling.max_interval_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].sampling.note` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].index` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].timestamp_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].frame_number` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].person_count` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].image_stats` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].image_stats.brightness` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].image_stats.contrast` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].image_stats.sharpness` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].det_index` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].track_id` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].track_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].bbox_norm` | array | 아니오 | [x1,y1,x2,y2] / image size |
| `cameras[].frames[].detections[].bbox_norm[]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].confidence` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].keypoints_norm` | object / null | 예 | COCO-17 [x/W, y/H, conf] |
| `cameras[].frames[].detections[].keypoints_norm` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].keypoints_norm[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].keypoints_norm[][]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].link` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].link` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].link.affinity` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].link.ambiguous` | boolean | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].link.gap_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.label` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.confidence` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.basis` | enum ["keypoints", "bbox_only", "insufficient_keypoints", "low_confidence"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.torso_angle_deg` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.body_orientation_angle_deg` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.hip_height_normalized` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.shoulder_height_normalized` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.leg_extension_ratio` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.body_height_ratio` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.aspect_ratio` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.keypoint_visibility` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.upright_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.horizontal_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].frames[].detections[].posture.crouched_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.person_count_min` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.person_count_max` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.person_count_median` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.person_count_mean` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.frames_with_person_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.total_detections` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].detection_summary.mean_detection_confidence` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].track_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.association_confidence` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.observed_frames` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.visible_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.max_gap_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.ambiguous_links` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.reliability_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].reliability.reliability_label` | enum ["high", "medium", "low", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection.first_seen_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection.last_seen_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection.observed_frames` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection.visible_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection.visible_fraction_of_clip` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].detection.mean_detection_confidence` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].observations` | array | 아니오 | [frame index, det_index] pairs |
| `cameras[].tracks[].observations[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].observations[][]` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.bbox_center_x` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.bbox_center_y` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.bbox_width` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.bbox_height` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.bbox_area_ratio` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.reference_height` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.center_path` | array | 아니오 | [t, x/W, y/H] |
| `cameras[].tracks[].geometry.center_path[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.center_path[][]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.bbox_area_change` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].geometry.vertical_position_change` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.units` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.normalized_speed_mean` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.normalized_speed_max` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.body_height_speed_mean` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.body_height_speed_max` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.displacement_total` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.net_displacement` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.direction_change_count` | ['integer', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].motion.stationary_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.pose_observed_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.known_posture_observations` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.posture_counts` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.posture_counts.standing` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.posture_counts.crouched` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.posture_counts.low_posture` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.posture_counts.horizontal` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.posture_counts.unknown` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.low_or_horizontal_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.mean_torso_angle_deg` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.mean_body_orientation_angle_deg` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.mean_upright_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.mean_horizontal_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.mean_crouched_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.timeline` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].posture.timeline[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.upright_to_low_transition` | ['boolean', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.upright_to_horizontal_transition` | ['boolean', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.max_downward_change` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.downward_change_basis` | enum ["hip", "bbox_top", null] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.transition_start_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.transition_end_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.transition_duration_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.from_posture` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.from_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.to_posture` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.to_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.confidence` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].vertical_transition.temporal_resolution_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion.semantics` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion.low_motion_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion.longest_low_motion_interval_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion.post_transition_low_motion_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion.post_transition_low_posture_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].tracks[].low_motion.post_transition_observed_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].pair_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].track_a` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].track_b` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].co_observed_frames` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].co_observed_start_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].co_observed_end_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].minimum_normalized_distance` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].mean_normalized_distance` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].distance_units` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].distance_series` | array | 아니오 | [t, distance_body_heights, close] |
| `cameras[].pairwise_interactions[].distance_series[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].approach_rate` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].max_approach_rate` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].rapid_approach_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].close_proximity_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].close_duration_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].first_close_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].last_close_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].bbox_overlap_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].mean_bbox_overlap` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].repeated_approach_count` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].relative_motion_intensity` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].relative_motion_intensity_when_close` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].relative_motion_max` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].arm_extension_toward_other_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].arm_extension_toward_other_max` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].rapid_limb_motion_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].limb_motion_note` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.terms` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.terms.close_bbox_distance` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.terms.pose_overlap` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.terms.rapid_relative_motion` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.basis` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.basis[]` | enum ["close_bbox_distance", "pose_overlap", "rapid_relative_motion"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].contact_proxy.note` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].reliability` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].pairwise_interactions[].temporal_resolution_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_entries` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_entries[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_entries[].track_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_entries[].time_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_entries[].type` | enum ["present_at_clip_start", "edge_entry", "appears_mid_frame"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_exits` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_exits[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_exits[].track_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_exits[].time_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.track_exits[].type` | enum ["present_at_clip_end", "edge_exit", "disappears_mid_frame"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].track_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].start_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].end_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].from_xy` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].from_xy[]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].to_xy` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].to_xy[]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.large_spatial_transitions[].net_displacement_fh` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.occlusion_candidates` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.occlusion_candidates[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.occlusion_candidates[].track_id` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.occlusion_candidates[].time_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.occlusion_candidates[].reappearance_candidate` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.occlusion_candidates[].reappearance_candidate` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[]` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].from_track` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].to_track` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].gap_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].from_end_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].to_start_sec` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].distance_body_heights` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change.from_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change.to_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change.downward_change` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change.downward_change_basis` | enum ["hip", "bbox_top"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].posture_change.confidence` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.fragment_links[].identity_confirmed` | const false | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.boundary_crossing` | null | 예 | Generic CV has no boundary semantics: always null (unknown), never false. |
| `cameras[].scene_observations.boundary_crossing_reliability` | const "unavailable" | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.scene_semantics` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.scene_semantics.zones` | null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.scene_semantics.reliability` | const "unavailable" | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].scene_observations.scene_semantics.note` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.mean_brightness` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.mean_contrast` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.mean_sharpness` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.dark_frame_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.temporal_resolution_sec` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.mean_person_box_area_ratio` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.small_person_fraction` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.pose_visibility` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.detection_dropout_rate` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.track_fragmentation` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.track_fragmentation_ratio` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.occlusion_proxy` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.overall_cv_reliability` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.overall_cv_reliability_label` | enum ["high", "medium", "low", "unknown"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cameras[].quality.note` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera` | object / null | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_a` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_b` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.alignment` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.phase_bins` | integer | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.person_count_similarity` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.temporal_pattern_similarity` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.motion_peak_similarity` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.posture_transition_similarity` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.incident_signature_similarity` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.incident_signature_vectors` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.incident_signature_fields` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.incident_signature_fields[]` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.phase_curves` | object | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.visibility_complementarity_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_a_visibility_drop` | boolean | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_b_visibility_drop` | boolean | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_b_has_observations_during_a_low_visibility_phase` | boolean | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_a_has_observations_during_b_low_visibility_phase` | boolean | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_a_low_visibility_phases` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_a_low_visibility_phases[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_a_low_visibility_phases[][]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_b_low_visibility_phases` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_b_low_visibility_phases[]` | array | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.camera_b_low_visibility_phases[][]` | number | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.same_incident_similarity_score` | ['number', 'null'] | 예 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.same_incident_similarity_note` | string | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.identity_link_confirmed` | const false | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |
| `cross_camera.sync_confirmed` | const false | 아니오 | 원본 Schema 필드; 계산 방식은 README의 코드 분석 참조 |

## Compact v1 전체 Feature

| 경로 | 타입 | Nullable | Canonical 원천 / 계산 |
|---|---|---|---|
| `schema_version` | const "compact-decision-state-v1" | 아니오 | serializer constant |
| `task` | enum ["single", "attention", "multi_camera"] | 아니오 | input.task |
| `observation_window_sec` | number | 아니오 | camera.duration_sec |
| `cameras` | array | 아니오 | state.cameras |
| `cameras[]` | object | 아니오 | state.cameras |
| `cameras[].camera` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | camera.camera_id |
| `cameras[].observation_window_sec` | ['number', 'null'] | 예 | camera.duration_sec |
| `cameras[].sampling` | object | 아니오 | camera.sampling |
| `cameras[].sampling.frame_count` | integer | 아니오 | camera.sampling.frame_count |
| `cameras[].sampling.median_interval_sec` | ['number', 'null'] | 예 | camera.sampling.median_interval_sec |
| `cameras[].sampling.max_interval_sec` | ['number', 'null'] | 예 | camera.sampling.max_interval_sec |
| `cameras[].quality` | object | 아니오 | camera.quality |
| `cameras[].quality.cv_reliability` | ['number', 'null'] | 예 | camera.quality.overall_cv_reliability |
| `cameras[].quality.cv_reliability_label` | enum ["high", "medium", "low", "unknown"] | 아니오 | camera.quality.overall_cv_reliability_label |
| `cameras[].quality.pose_visibility` | ['number', 'null'] | 예 | camera.quality.pose_visibility |
| `cameras[].quality.track_fragmentation` | ['number', 'null'] | 예 | camera.quality.track_fragmentation |
| `cameras[].quality.occlusion_proxy` | ['number', 'null'] | 예 | camera.quality.occlusion_proxy |
| `cameras[].quality.detection_dropout_rate` | ['number', 'null'] | 예 | camera.quality.detection_dropout_rate |
| `cameras[].quality.small_person_fraction` | ['number', 'null'] | 예 | camera.quality.small_person_fraction |
| `cameras[].quality.dark_frame_fraction` | ['number', 'null'] | 예 | camera.quality.dark_frame_fraction |
| `cameras[].people` | object | 아니오 | camera.people |
| `cameras[].people.count_min` | integer | 아니오 | camera.detection_summary.person_count_min |
| `cameras[].people.count_max` | integer | 아니오 | camera.detection_summary.person_count_max |
| `cameras[].people.count_median` | number | 아니오 | camera.detection_summary.person_count_median |
| `cameras[].people.frames_with_person_fraction` | ['number', 'null'] | 예 | camera.detection_summary.frames_with_person_fraction |
| `cameras[].people.tracks_total` | integer | 아니오 | len(camera.tracks) / selected tracks |
| `cameras[].people.tracks_included` | integer | 아니오 | len(camera.tracks) / selected tracks |
| `cameras[].tracks` | array | 아니오 | camera.tracks (v1 selection) |
| `cameras[].tracks[]` | object | 아니오 | camera.tracks (v1 selection) |
| `cameras[].tracks[].track_ref` | string | 아니오 | camera.tracks.track_id (T01→T1) |
| `cameras[].tracks[].reliability` | ['number', 'null'] | 예 | camera.tracks.reliability.reliability_score / pair reliability |
| `cameras[].tracks[].reliability_label` | enum ["high", "medium", "low", "unknown"] | 아니오 | camera.tracks.reliability.reliability_label |
| `cameras[].tracks[].observed_frames` | integer | 아니오 | camera.tracks.reliability.observed_frames |
| `cameras[].tracks[].visible_fraction` | ['number', 'null'] | 예 | camera.tracks.visible_fraction |
| `cameras[].tracks[].ambiguous_links` | integer | 아니오 | camera.tracks.reliability.ambiguous_links |
| `cameras[].tracks[].first_seen_sec` | number | 아니오 | camera.tracks.detection.first_seen_sec |
| `cameras[].tracks[].last_seen_sec` | number | 아니오 | camera.tracks.detection.last_seen_sec |
| `cameras[].tracks[].initial_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | tracks.posture.timeline (first non-unknown) |
| `cameras[].tracks[].final_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | camera.tracks.final_posture |
| `cameras[].tracks[].posture_distribution` | object | 아니오 | tracks.posture.timeline (all detected observations; unknown included) |
| `cameras[].tracks[].posture_distribution.standing` | ['number', 'null'] | 예 | tracks.posture.timeline (all detected observations; unknown included) |
| `cameras[].tracks[].posture_distribution.crouched` | ['number', 'null'] | 예 | tracks.posture.timeline (all detected observations; unknown included) |
| `cameras[].tracks[].posture_distribution.low_posture` | ['number', 'null'] | 예 | tracks.posture.timeline (all detected observations; unknown included) |
| `cameras[].tracks[].posture_distribution.horizontal` | ['number', 'null'] | 예 | tracks.posture.timeline (all detected observations; unknown included) |
| `cameras[].tracks[].posture_distribution.unknown` | ['number', 'null'] | 예 | tracks.posture.timeline (all detected observations; unknown included) |
| `cameras[].tracks[].strongest_vertical_transition` | object | 아니오 | camera.tracks.vertical_transition (strongest Canonical observation) |
| `cameras[].tracks[].strongest_vertical_transition.observed` | ['boolean', 'null'] | 예 | camera.tracks.vertical_transition.upright_to_low_transition |
| `cameras[].tracks[].strongest_vertical_transition.from` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | camera.tracks.vertical_transition.from_posture |
| `cameras[].tracks[].strongest_vertical_transition.to` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | camera.tracks.vertical_transition.to_posture |
| `cameras[].tracks[].strongest_vertical_transition.start_sec` | ['number', 'null'] | 예 | camera.tracks.vertical_transition.transition_start_sec |
| `cameras[].tracks[].strongest_vertical_transition.end_sec` | ['number', 'null'] | 예 | camera.tracks.vertical_transition.transition_end_sec |
| `cameras[].tracks[].strongest_vertical_transition.duration_sec` | ['number', 'null'] | 예 | camera.tracks.vertical_transition.transition_duration_sec |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh` | object | 아니오 | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh.value` | ['number', 'null'] | 예 | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh.reliability` | enum ["limited", "normal"] | 아니오 | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh.note` | string | 아니오 | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) |
| `cameras[].tracks[].strongest_vertical_transition.confidence` | ['number', 'null'] | 예 | camera.tracks.vertical_transition.confidence |
| `cameras[].tracks[].longest_low_posture_run_sec` | ['number', 'null'] | 예 | camera.tracks.longest_low_posture_run_sec |
| `cameras[].tracks[].post_transition_low_posture_sec` | ['number', 'null'] | 예 | camera.tracks.post_transition_low_posture_sec |
| `cameras[].tracks[].motion` | object | 아니오 | camera.tracks.motion |
| `cameras[].tracks[].motion.mean_speed_bh_per_sec` | ['number', 'null'] | 예 | camera.tracks.motion / low_motion.body_height_speed_mean |
| `cameras[].tracks[].motion.max_speed_bh_per_sec` | ['number', 'null'] | 예 | camera.tracks.motion / low_motion.body_height_speed_max |
| `cameras[].tracks[].motion.net_displacement_fh` | ['number', 'null'] | 예 | camera.tracks.motion / low_motion.net_displacement |
| `cameras[].tracks[].motion.direction_change_count` | ['integer', 'null'] | 예 | camera.tracks.motion / low_motion.direction_change_count |
| `cameras[].tracks[].motion.stationary_fraction` | ['number', 'null'] | 예 | camera.tracks.motion / low_motion.stationary_fraction |
| `cameras[].tracks[].motion.low_motion_fraction` | ['number', 'null'] | 예 | camera.tracks.motion / low_motion.low_motion_fraction |
| `cameras[].tracks[].motion.longest_low_motion_interval_sec` | ['number', 'null'] | 예 | camera.tracks.motion / low_motion.longest_low_motion_interval_sec |
| `cameras[].tracks[].motion.large_spatial_transition` | boolean | 아니오 | scene_observations.large_spatial_transitions (track membership) |
| `cameras[].tracks[].appearance` | object | 아니오 | camera.tracks.appearance |
| `cameras[].tracks[].appearance.entry` | enum ["present_at_clip_start", "edge_entry", "appears_mid_frame", null] | 예 | camera.tracks.scene_observations.track_entries.type |
| `cameras[].tracks[].appearance.exit` | enum ["present_at_clip_end", "edge_exit", "disappears_mid_frame", null] | 예 | camera.tracks.scene_observations.track_exits.type |
| `cameras[].tracks[].appearance.entered_frame` | boolean | 아니오 | scene track entry/exit type membership |
| `cameras[].tracks[].appearance.exited_frame` | boolean | 아니오 | scene track entry/exit type membership |
| `cameras[].interactions` | array | 아니오 | camera.pairwise_interactions (v1 selection) |
| `cameras[].interactions[]` | object | 아니오 | camera.pairwise_interactions (v1 selection) |
| `cameras[].interactions[].tracks` | array | 아니오 | camera.pairwise_interactions.track_a / track_b (per-camera refs) |
| `cameras[].interactions[].tracks[]` | string | 아니오 | camera.pairwise_interactions.track_a / track_b (per-camera refs) |
| `cameras[].interactions[].reliability` | ['number', 'null'] | 예 | camera.pairwise_interactions.reliability_score / pair reliability |
| `cameras[].interactions[].co_observed_frames` | integer | 아니오 | camera.pairwise_interactions.co_observed_frames |
| `cameras[].interactions[].co_observed_start_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.co_observed_start_sec |
| `cameras[].interactions[].co_observed_end_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.co_observed_end_sec |
| `cameras[].interactions[].minimum_distance_bh` | ['number', 'null'] | 예 | camera.pairwise_interactions.minimum_normalized_distance |
| `cameras[].interactions[].mean_distance_bh` | ['number', 'null'] | 예 | camera.pairwise_interactions.mean_normalized_distance |
| `cameras[].interactions[].close_fraction` | ['number', 'null'] | 예 | camera.pairwise_interactions.close_proximity_fraction |
| `cameras[].interactions[].close_duration_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.close_duration_sec |
| `cameras[].interactions[].first_close_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.first_close_sec |
| `cameras[].interactions[].last_close_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.last_close_sec |
| `cameras[].interactions[].approach_rate_bh_per_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.approach_rate |
| `cameras[].interactions[].approach_events` | integer | 아니오 | camera.pairwise_interactions.repeated_approach_count |
| `cameras[].interactions[].relative_motion_when_close_bh_per_sec` | ['number', 'null'] | 예 | camera.pairwise_interactions.relative_motion_intensity_when_close |
| `cameras[].interactions[].bbox_overlap_fraction` | ['number', 'null'] | 예 | camera.pairwise_interactions.bbox_overlap_fraction |
| `cameras[].interactions[].contact_proxy` | object | 아니오 | camera.pairwise_interactions.contact_proxy.score |
| `cameras[].interactions[].contact_proxy.value` | ['number', 'null'] | 예 | camera.pairwise_interactions.contact_proxy.score (proxy value / explicit limitation) |
| `cameras[].interactions[].contact_proxy.reliability` | const "limited" | 아니오 | camera.pairwise_interactions.contact_proxy.score (proxy value / explicit limitation) |
| `cameras[].interactions[].contact_proxy.note` | string | 아니오 | camera.pairwise_interactions.contact_proxy.score (proxy value / explicit limitation) |
| `cameras[].interactions[].arm_extension_score` | object | 아니오 | camera.pairwise_interactions.arm_extension_toward_other_score |
| `cameras[].interactions[].arm_extension_score.value` | ['number', 'null'] | 예 | camera.pairwise_interactions.arm_extension_toward_other_score (proxy value / explicit limitation) |
| `cameras[].interactions[].arm_extension_score.reliability` | const "limited" | 아니오 | camera.pairwise_interactions.arm_extension_toward_other_score (proxy value / explicit limitation) |
| `cameras[].interactions[].arm_extension_score.note` | string | 아니오 | camera.pairwise_interactions.arm_extension_toward_other_score (proxy value / explicit limitation) |
| `cameras[].interactions[].rapid_limb_motion_score` | object | 아니오 | camera.pairwise_interactions.rapid_limb_motion_score |
| `cameras[].interactions[].rapid_limb_motion_score.value` | ['number', 'null'] | 예 | camera.pairwise_interactions.rapid_limb_motion_score (proxy value / explicit limitation) |
| `cameras[].interactions[].rapid_limb_motion_score.reliability` | const "limited" | 아니오 | camera.pairwise_interactions.rapid_limb_motion_score (proxy value / explicit limitation) |
| `cameras[].interactions[].rapid_limb_motion_score.note` | string | 아니오 | camera.pairwise_interactions.rapid_limb_motion_score (proxy value / explicit limitation) |
| `cameras[].scene` | object | 아니오 | camera.scene_observations |
| `cameras[].scene.person_entry_observed` | boolean | 아니오 | whole camera.scene_observations (any / count) |
| `cameras[].scene.person_exit_observed` | boolean | 아니오 | whole camera.scene_observations (any / count) |
| `cameras[].scene.large_spatial_transition_observed` | boolean | 아니오 | whole camera.scene_observations (any / count) |
| `cameras[].scene.occlusion_candidate_count` | integer | 아니오 | whole camera.scene_observations (any / count) |
| `cameras[].scene.fragment_links` | array | 아니오 | camera.scene_observations.fragment_links |
| `cameras[].scene.fragment_links[]` | object | 아니오 | camera.scene_observations.fragment_links |
| `cameras[].scene.fragment_links[].from_track` | string | 아니오 | camera.scene_observations.from_track |
| `cameras[].scene.fragment_links[].to_track` | string | 아니오 | camera.scene_observations.to_track |
| `cameras[].scene.fragment_links[].gap_sec` | ['number', 'null'] | 예 | camera.scene_observations.gap_sec |
| `cameras[].scene.fragment_links[].distance_bh` | ['number', 'null'] | 예 | camera.scene_observations.distance_body_heights |
| `cameras[].scene.fragment_links[].same_person_confirmed` | const false | 아니오 | false constant: unconfirmed / unavailable (not negation of event) |
| `cameras[].scene.fragment_links[].posture_change` | object / null | 예 | camera.scene_observations.posture_change |
| `cameras[].scene.fragment_links[].posture_change` | object | 아니오 | camera.scene_observations.posture_change |
| `cameras[].scene.fragment_links[].posture_change.from` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | camera.scene_observations.from_posture |
| `cameras[].scene.fragment_links[].posture_change.to` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | camera.scene_observations.to_posture |
| `cameras[].scene.fragment_links[].posture_change.confidence` | ['number', 'null'] | 예 | camera.scene_observations.confidence |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh` | object | 아니오 | camera.scene_observations.max_downward_change / fragment posture_change.downward_change |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh.value` | ['number', 'null'] | 예 | camera.scene_observations.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh.reliability` | enum ["limited", "normal"] | 아니오 | camera.scene_observations.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh.note` | string | 아니오 | camera.scene_observations.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) |
| `cameras[].scene.boundary_semantics_available` | const false | 아니오 | false constant: unconfirmed / unavailable (not negation of event) |
| `cameras[].scene.boundary_crossing` | null | 예 | null constant: no scene ROI semantics |
| `cameras[].scene.authorization_known` | const false | 아니오 | false constant: unconfirmed / unavailable (not negation of event) |
| `cross_camera` | object / null | 예 | state.cross_camera (base observations only) |
| `cross_camera` | object | 아니오 | state.cross_camera (base observations only) |
| `cross_camera.camera_a` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | cross_camera.camera_a |
| `cross_camera.camera_b` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | cross_camera.camera_b |
| `cross_camera.sync_confirmed` | const false | 아니오 | false constant: unconfirmed / unavailable (not negation of event) |
| `cross_camera.identity_link_confirmed` | const false | 아니오 | false constant: unconfirmed / unavailable (not negation of event) |
| `cross_camera.alignment` | string | 아니오 | normalized clip phase only constant |
| `cross_camera.person_count_similarity` | object | 아니오 | cross_camera.person_count_similarity |
| `cross_camera.person_count_similarity.value` | ['number', 'null'] | 예 | cross_camera.person_count_similarity (proxy value / explicit limitation) |
| `cross_camera.person_count_similarity.reliability` | const "limited" | 아니오 | cross_camera.person_count_similarity (proxy value / explicit limitation) |
| `cross_camera.person_count_similarity.note` | string | 아니오 | cross_camera.person_count_similarity (proxy value / explicit limitation) |
| `cross_camera.temporal_pattern_similarity` | object | 아니오 | cross_camera.temporal_pattern_similarity |
| `cross_camera.temporal_pattern_similarity.value` | ['number', 'null'] | 예 | cross_camera.temporal_pattern_similarity (proxy value / explicit limitation) |
| `cross_camera.temporal_pattern_similarity.reliability` | const "limited" | 아니오 | cross_camera.temporal_pattern_similarity (proxy value / explicit limitation) |
| `cross_camera.temporal_pattern_similarity.note` | string | 아니오 | cross_camera.temporal_pattern_similarity (proxy value / explicit limitation) |
| `cross_camera.motion_peak_similarity` | object | 아니오 | cross_camera.motion_peak_similarity |
| `cross_camera.motion_peak_similarity.value` | ['number', 'null'] | 예 | cross_camera.motion_peak_similarity (proxy value / explicit limitation) |
| `cross_camera.motion_peak_similarity.reliability` | const "limited" | 아니오 | cross_camera.motion_peak_similarity (proxy value / explicit limitation) |
| `cross_camera.motion_peak_similarity.note` | string | 아니오 | cross_camera.motion_peak_similarity (proxy value / explicit limitation) |
| `cross_camera.posture_transition_similarity` | object | 아니오 | cross_camera.posture_transition_similarity |
| `cross_camera.posture_transition_similarity.value` | ['number', 'null'] | 예 | cross_camera.posture_transition_similarity (proxy value / explicit limitation) |
| `cross_camera.posture_transition_similarity.reliability` | const "limited" | 아니오 | cross_camera.posture_transition_similarity (proxy value / explicit limitation) |
| `cross_camera.posture_transition_similarity.note` | string | 아니오 | cross_camera.posture_transition_similarity (proxy value / explicit limitation) |
| `cross_camera.visibility_complementarity` | ['number', 'null'] | 예 | cross_camera.visibility_complementarity_score |
| `cross_camera.camera_a_visibility_drop_observed` | boolean | 아니오 | cross_camera.camera_a_visibility_drop |
| `cross_camera.camera_b_visibility_drop_observed` | boolean | 아니오 | cross_camera.camera_b_visibility_drop |
| `cross_camera.camera_b_has_observations_during_a_low_visibility_phase` | boolean | 아니오 | cross_camera.camera_b_has_observations_during_a_low_visibility_phase |
| `cross_camera.camera_a_has_observations_during_b_low_visibility_phase` | boolean | 아니오 | cross_camera.camera_a_has_observations_during_b_low_visibility_phase |
| `cross_camera.camera_a_low_visibility_phases` | array | 아니오 | cross_camera.camera_a_low_visibility_phases |
| `cross_camera.camera_a_low_visibility_phases[]` | array | 아니오 | cross_camera.camera_a_low_visibility_phases |
| `cross_camera.camera_a_low_visibility_phases[][]` | number | 아니오 | cross_camera.camera_a_low_visibility_phases |
| `cross_camera.camera_b_low_visibility_phases` | array | 아니오 | cross_camera.camera_b_low_visibility_phases |
| `cross_camera.camera_b_low_visibility_phases[]` | array | 아니오 | cross_camera.camera_b_low_visibility_phases |
| `cross_camera.camera_b_low_visibility_phases[][]` | number | 아니오 | cross_camera.camera_b_low_visibility_phases |
| `cross_camera.person_count_by_phase` | object | 아니오 | cross_camera.phase_curves[camera].count |

## Compact v2 전체 필드

| 경로 | 타입 | Nullable | 단위 | Canonical 원천 | 의미 / 요약 |
|---|---|---|---|---|---|
| `schema_version` | const "compact-decision-state-v2" | 아니오 | dimensionless / enum / structure | serializer constant | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `task` | enum ["single", "attention", "multi_camera"] | 아니오 | dimensionless / enum / structure | input.task | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `observation_window_sec` | number | 아니오 | seconds (clip-relative) | camera.duration_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras` | array | 아니오 | dimensionless / enum / structure | state.cameras | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[]` | object | 아니오 | dimensionless / enum / structure | state.cameras | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].camera` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | dimensionless / enum / structure | camera.camera_id | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].observation_window_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.duration_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].sampling` | object | 아니오 | dimensionless / enum / structure | camera.sampling | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].sampling.frame_count` | integer | 아니오 | count | camera.sampling.frame_count | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].sampling.median_interval_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.sampling.median_interval_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].sampling.max_interval_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.sampling.max_interval_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].sampling.timestamps_sec` | array | 아니오 | seconds (clip-relative) | camera.sampling.timestamps_sec | Canonical sample 시각 배열. run index를 이 배열에 대응; clip-relative seconds. |
| `cameras[].sampling.timestamps_sec[]` | number | 아니오 | seconds (clip-relative) | camera.sampling.timestamps_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality` | object | 아니오 | dimensionless / enum / structure | camera.quality | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.cv_reliability` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.quality.overall_cv_reliability | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.cv_reliability_label` | enum ["high", "medium", "low", "unknown"] | 아니오 | 0..1 proxy / enum | camera.quality.overall_cv_reliability_label | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.pose_visibility` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.quality.pose_visibility | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.track_fragmentation` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.quality.track_fragmentation | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.occlusion_proxy` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.quality.occlusion_proxy | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.detection_dropout_rate` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.quality.detection_dropout_rate | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.small_person_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.quality.small_person_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.dark_frame_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.quality.dark_frame_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].quality.aggregate_inputs_complete` | boolean | 아니오 | boolean | quality.pose_visibility,detection_dropout_rate,track_fragmentation,occlusion_proxy,small_person_fraction,dark_frame_fraction | 종합 CV 신뢰도 구성 요소의 이용 가능 여부; high confidence라는 뜻 아님. 6개 값 모두 non-null이면 true; false이면 cv_reliability=null 및 label=unknown |
| `cameras[].quality.mean_brightness` | ['number', 'null'] | 예 | pixel intensity 0..255 | quality.mean_brightness | 평균 영상 밝기. 직접 전달 |
| `cameras[].quality.mean_contrast` | ['number', 'null'] | 예 | pixel intensity standard deviation | quality.mean_contrast | 평균 영상 grayscale 표준편차. 직접 전달 |
| `cameras[].quality.mean_sharpness` | ['number', 'null'] | 예 | pixel intensity squared | quality.mean_sharpness | 평균 Laplacian variance; 카메라별 검증이 필요한 proxy. 직접 전달 |
| `cameras[].people` | object | 아니오 | dimensionless / enum / structure | camera.people | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].people.count_min` | integer | 아니오 | count | camera.detection_summary.person_count_min | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].people.count_max` | integer | 아니오 | count | camera.detection_summary.person_count_max | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].people.count_median` | number | 아니오 | count | camera.detection_summary.person_count_median | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].people.frames_with_person_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.detection_summary.frames_with_person_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].people.tracks_total` | integer | 아니오 | count | len(camera.tracks) / selected tracks | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].people.tracks_included` | integer | 아니오 | count | len(camera.tracks) / selected tracks | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks` | array | 아니오 | dimensionless / enum / structure | camera.tracks (v1 selection) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[]` | object | 아니오 | dimensionless / enum / structure | camera.tracks (v1 selection) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].track_ref` | string | 아니오 | dimensionless / enum / structure | camera.tracks.track_id (T01→T1) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].reliability` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.tracks.reliability.reliability_score / pair reliability | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].reliability_label` | enum ["high", "medium", "low", "unknown"] | 아니오 | 0..1 proxy / enum | camera.tracks.reliability.reliability_label | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].observed_frames` | integer | 아니오 | count | camera.tracks.reliability.observed_frames | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].ambiguous_links` | integer | 아니오 | count | camera.tracks.reliability.ambiguous_links | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].first_seen_sec` | number | 아니오 | seconds (clip-relative) | camera.tracks.detection.first_seen_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].last_seen_sec` | number | 아니오 | seconds (clip-relative) | camera.tracks.detection.last_seen_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].initial_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | dimensionless / enum / structure | tracks.posture.timeline (first non-unknown) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].posture_distribution` | object | 아니오 | dimensionless / enum / structure | tracks.posture.timeline (all detected observations; unknown included) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].posture_distribution.standing` | ['number', 'null'] | 예 | dimensionless / enum / structure | tracks.posture.timeline (all detected observations; unknown included) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].posture_distribution.crouched` | ['number', 'null'] | 예 | dimensionless / enum / structure | tracks.posture.timeline (all detected observations; unknown included) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].posture_distribution.low_posture` | ['number', 'null'] | 예 | dimensionless / enum / structure | tracks.posture.timeline (all detected observations; unknown included) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].posture_distribution.horizontal` | ['number', 'null'] | 예 | dimensionless / enum / structure | tracks.posture.timeline (all detected observations; unknown included) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].posture_distribution.unknown` | ['number', 'null'] | 예 | dimensionless / enum / structure | tracks.posture.timeline (all detected observations; unknown included) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition` | object | 아니오 | dimensionless / enum / structure | camera.tracks.vertical_transition (strongest Canonical observation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.observed` | ['boolean', 'null'] | 예 | dimensionless / enum / structure | camera.tracks.vertical_transition.upright_to_low_transition | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.from` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | dimensionless / enum / structure | camera.tracks.vertical_transition.from_posture | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.to` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | dimensionless / enum / structure | camera.tracks.vertical_transition.to_posture | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.start_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.tracks.vertical_transition.transition_start_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.end_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.tracks.vertical_transition.transition_end_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.duration_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.tracks.vertical_transition.transition_duration_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh` | object | 아니오 | body heights | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh.reliability` | enum ["limited", "normal"] | 아니오 | 0..1 proxy / enum | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.downward_change_bh.note` | string | 아니오 | dimensionless / enum / structure | camera.tracks.vertical_transition.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].strongest_vertical_transition.confidence` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.tracks.vertical_transition.confidence | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion` | object | 아니오 | dimensionless / enum / structure | camera.tracks.motion | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.mean_speed_bh_per_sec` | ['number', 'null'] | 예 | body heights / second | camera.tracks.motion / low_motion.body_height_speed_mean | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.max_speed_bh_per_sec` | ['number', 'null'] | 예 | body heights / second | camera.tracks.motion / low_motion.body_height_speed_max | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.net_displacement_fh` | ['number', 'null'] | 예 | frame heights | camera.tracks.motion / low_motion.net_displacement | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.direction_change_count` | ['integer', 'null'] | 예 | count | camera.tracks.motion / low_motion.direction_change_count | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.stationary_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.tracks.motion / low_motion.stationary_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.low_motion_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.tracks.motion / low_motion.low_motion_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.longest_low_motion_interval_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.tracks.motion / low_motion.longest_low_motion_interval_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].motion.large_spatial_transition` | boolean | 아니오 | dimensionless / enum / structure | scene_observations.large_spatial_transitions (track membership) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].appearance` | object | 아니오 | dimensionless / enum / structure | camera.tracks.appearance | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].appearance.entry` | enum ["present_at_clip_start", "edge_entry", "appears_mid_frame", null] | 예 | dimensionless / enum / structure | camera.tracks.scene_observations.track_entries.type | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].appearance.exit` | enum ["present_at_clip_end", "edge_exit", "disappears_mid_frame", null] | 예 | dimensionless / enum / structure | camera.tracks.scene_observations.track_exits.type | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].appearance.entered_frame` | boolean | 아니오 | dimensionless / enum / structure | scene track entry/exit type membership | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].appearance.exited_frame` | boolean | 아니오 | dimensionless / enum / structure | scene track entry/exit type membership | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].coverage` | object | 아니오 | object | tracks.observations | 전체 Clip/Track span의 관측 coverage. coverage 정의 참조 |
| `cameras[].tracks[].coverage.clip_sample_fraction` | ['number', 'null'] | 예 | ratio 0..1 | tracks.observations / sampling.timestamps_sec | Clip 전체 샘플 중 이 Track 또는 Pair를 관측한 비율. 영상 시간 점유율이 아님. 고유 관측 sample index 수 / 전체 sample 수 |
| `cameras[].tracks[].coverage.span_sample_fraction` | ['number', 'null'] | 예 | ratio 0..1 | tracks.observations | 첫~마지막 관측 sample index 사이의 관측 비율. N / (last_index-first_index+1); 관측 0개이면 null |
| `cameras[].tracks[].coverage.missing_inside_span_samples` | integer | 아니오 | samples | tracks.observations | 첫~마지막 관측 사이 할당되지 않은 샘플 수. 존재하지 않음의 증거가 아님. 연속 관측 index 차이에서 1을 뺀 값의 합 |
| `cameras[].tracks[].coverage.max_missing_run_samples` | integer | 아니오 | samples | tracks.observations / frame_count | Clip 전체에서 연속 할당되지 않은 최대 샘플 수; 시작과 끝 포함. 내부 gap, leading, tail의 최댓값 |
| `cameras[].tracks[].coverage.max_gap_bracket_sec` | ['number', 'null'] | 예 | seconds | observations / sampling.timestamps_sec | 내부 미관측 샘플을 둘러싼 관측 시각 간 최대 간격; 실제 부재 기간 아님. index gap>1인 양끝 sample 시간차 최대; gap 없음 0 |
| `cameras[].tracks[].coverage.max_observation_interval_sec` | ['number', 'null'] | 예 | seconds | observations / sampling.timestamps_sec | 연속 관측 시각 간 최대 시간차; 정상 sampling interval도 포함. 연속 관측 시간차 최대; 2개 미만 null |
| `cameras[].tracks[].coverage.tail_unobserved_samples` | integer | 아니오 | samples | observations / frame_count | 마지막 관측 이후 끝까지 미관측 sample 수. frame_count-1-last_index |
| `cameras[].tracks[].coverage.last_sample_age_sec` | ['number', 'null'] | 예 | seconds | sampling.timestamps_sec / observations | 영상 마지막 sample 기준 마지막 관측의 나이; clip duration 기준이 아님. last_sample_time-last_observed_time; 관측 없음 null |
| `cameras[].tracks[].coverage.leading_unobserved_samples` | integer | 아니오 | samples | tracks.observations | 첫 관측 앞의 미관측 샘플 수. 첫 index; 관측 없음이면 frame_count |
| `cameras[].tracks[].temporal` | object | 아니오 | object | frames.detections.posture / tracks.observations | 자세 proxy의 관측 Timeline, Unknown, 회복 관측. temporal 정의 참조 |
| `cameras[].tracks[].temporal.runs` | array | 아니오 | tuple array | frames.detections.posture / tracks.observations | 동일 자세이며 sample index가 인접한 관측 구간. Tuple=[start_index,end_index,posture,min_confidence,bases]. 자세 변화 또는 빠진 sample마다 분리; confidence 일부 null이면 min null; bases 정렬 고유값 |
| `cameras[].tracks[].temporal.runs[]` | array | 아니오 | dimensionless / enum / structure | camera.tracks.runs | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].temporal.low_observed_samples` | integer | 아니오 | samples | frames.detections.posture.label | crouched/low_posture/horizontal 관측 수. LOW 집합 label 개수 |
| `cameras[].tracks[].temporal.unknown_posture_samples` | integer | 아니오 | samples | frames.detections.posture.label | 검출되었으나 자세 unresolved인 관측 수. unknown label 개수 |
| `cameras[].tracks[].temporal.low_adjacent_span_sec` | ['number', 'null'] | 예 | seconds | posture / observations / sampling.timestamps_sec | 인접 sample 양끝에 low 계열 자세를 관측한 시간차의 합; 실제 지속시간 아님. low label 간 변화 허용; 미관측 및 unknown은 끊음; singleton 0 |
| `cameras[].tracks[].temporal.longest_low_adjacent_span_sec` | ['number', 'null'] | 예 | seconds | posture / observations / sampling.timestamps_sec | low 계열 양끝 관측의 최대 인접 sample 시간 span. low 인접 구간 시간차 누적 최대; singleton 0 |
| `cameras[].tracks[].temporal.last_observed_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | posture enum | frames.detections.posture.label | 마지막 검출 sample의 자세. unknown을 건너뛰지 않음. 마지막 observation label; 관측 없음 null |
| `cameras[].tracks[].temporal.last_known_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | posture enum | frames.detections.posture.label | 마지막 unknown 이외 자세; 최신 상태로 간주하면 안 됨. known label 마지막; 전부 unknown이면 null |
| `cameras[].tracks[].temporal.last_known_posture_sec` | ['number', 'null'] | 예 | seconds | posture / sampling.timestamps_sec | 마지막 known posture의 sample 시각. known sample 시각; 없으면 null |
| `cameras[].tracks[].temporal.last_sample_posture` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", "not_observed"] | 아니오 | posture or not_observed | observations / frames.detections.posture | 영상 마지막 sample의 관측 자세; 할당 없음은 not_observed. last_index == frame_count-1이면 label, 아니면 not_observed |
| `cameras[].tracks[].temporal.low_to_standing_observations` | array | 아니오 | tuple array | frames.detections.posture / observations / timestamps | low 이후 standing이 다시 관측된 전환 목록. 이전 사건 제거 근거 아님. Tuple=[last_low_sec,standing_sec,missed_samples,unknown_samples_between]. low를 최신값으로 갱신; 다음 standing에서 기록; []는 회복 관측 없음이며 회복 불가능의 증거 아님 |
| `cameras[].tracks[].temporal.low_to_standing_observations[]` | array | 아니오 | dimensionless / enum / structure | camera.tracks.low_to_standing_observations | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].tracks[].mean_detection_confidence` | ['number', 'null'] | 예 | score 0..1 | tracks.detection.mean_detection_confidence | 관측 detection confidence의 평균. 직접 전달; null 보존 |
| `cameras[].tracks[].association_confidence` | ['number', 'null'] | 예 | score 0..1 | tracks.reliability.association_confidence | SparseTracker의 링크 affinity 평균; 보정된 identity probability가 아님. 직접 전달; null이면 track reliability도 null/unknown |
| `cameras[].tracks[].fragment_link_candidates` | integer | 아니오 | count | scene_observations.fragment_links | 해당 track을 연결하는 fragment 후보 수; 동일인 확인 아님. from/to track 일치 개수 |
| `cameras[].interactions` | array | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions (v1 selection) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[]` | object | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions (v1 selection) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].tracks` | array | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.track_a / track_b (per-camera refs) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].tracks[]` | string | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.track_a / track_b (per-camera refs) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].reliability` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.pairwise_interactions.reliability_score / pair reliability | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].co_observed_frames` | integer | 아니오 | count | camera.pairwise_interactions.co_observed_frames | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].co_observed_start_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.pairwise_interactions.co_observed_start_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].co_observed_end_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.pairwise_interactions.co_observed_end_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].minimum_distance_bh` | ['number', 'null'] | 예 | body heights | camera.pairwise_interactions.minimum_normalized_distance | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].mean_distance_bh` | ['number', 'null'] | 예 | body heights | camera.pairwise_interactions.mean_normalized_distance | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].close_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.pairwise_interactions.close_proximity_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].first_close_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.pairwise_interactions.first_close_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].last_close_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.pairwise_interactions.last_close_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].approach_rate_bh_per_sec` | ['number', 'null'] | 예 | body heights / second | camera.pairwise_interactions.approach_rate | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].approach_events` | integer | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.repeated_approach_count | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].relative_motion_when_close_bh_per_sec` | ['number', 'null'] | 예 | body heights / second | camera.pairwise_interactions.relative_motion_intensity_when_close | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].bbox_overlap_fraction` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.pairwise_interactions.bbox_overlap_fraction | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].contact_proxy` | object | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.contact_proxy.score | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].contact_proxy.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.pairwise_interactions.contact_proxy.score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].contact_proxy.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | camera.pairwise_interactions.contact_proxy.score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].contact_proxy.note` | string | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.contact_proxy.score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].arm_extension_score` | object | 아니오 | 0..1 proxy / enum | camera.pairwise_interactions.arm_extension_toward_other_score | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].arm_extension_score.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.pairwise_interactions.arm_extension_toward_other_score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].arm_extension_score.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | camera.pairwise_interactions.arm_extension_toward_other_score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].arm_extension_score.note` | string | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.arm_extension_toward_other_score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].rapid_limb_motion_score` | object | 아니오 | 0..1 proxy / enum | camera.pairwise_interactions.rapid_limb_motion_score | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].rapid_limb_motion_score.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.pairwise_interactions.rapid_limb_motion_score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].rapid_limb_motion_score.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | camera.pairwise_interactions.rapid_limb_motion_score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].rapid_limb_motion_score.note` | string | 아니오 | dimensionless / enum / structure | camera.pairwise_interactions.rapid_limb_motion_score (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].interactions[].coverage` | object | 아니오 | object | intersection(tracks[a].observations, tracks[b].observations) | 양쪽 track이 함께 검출된 sample의 coverage. coverage 정의 참조 |
| `cameras[].interactions[].coverage.clip_sample_fraction` | ['number', 'null'] | 예 | ratio 0..1 | tracks.observations / sampling.timestamps_sec | Clip 전체 샘플 중 이 Track 또는 Pair를 관측한 비율. 영상 시간 점유율이 아님. 고유 관측 sample index 수 / 전체 sample 수 |
| `cameras[].interactions[].coverage.span_sample_fraction` | ['number', 'null'] | 예 | ratio 0..1 | tracks.observations | 첫~마지막 관측 sample index 사이의 관측 비율. N / (last_index-first_index+1); 관측 0개이면 null |
| `cameras[].interactions[].coverage.missing_inside_span_samples` | integer | 아니오 | samples | tracks.observations | 첫~마지막 관측 사이 할당되지 않은 샘플 수. 존재하지 않음의 증거가 아님. 연속 관측 index 차이에서 1을 뺀 값의 합 |
| `cameras[].interactions[].coverage.max_missing_run_samples` | integer | 아니오 | samples | tracks.observations / frame_count | Clip 전체에서 연속 할당되지 않은 최대 샘플 수; 시작과 끝 포함. 내부 gap, leading, tail의 최댓값 |
| `cameras[].interactions[].coverage.max_gap_bracket_sec` | ['number', 'null'] | 예 | seconds | observations / sampling.timestamps_sec | 내부 미관측 샘플을 둘러싼 관측 시각 간 최대 간격; 실제 부재 기간 아님. index gap>1인 양끝 sample 시간차 최대; gap 없음 0 |
| `cameras[].interactions[].coverage.max_observation_interval_sec` | ['number', 'null'] | 예 | seconds | observations / sampling.timestamps_sec | 연속 관측 시각 간 최대 시간차; 정상 sampling interval도 포함. 연속 관측 시간차 최대; 2개 미만 null |
| `cameras[].interactions[].coverage.tail_unobserved_samples` | integer | 아니오 | samples | observations / frame_count | 마지막 관측 이후 끝까지 미관측 sample 수. frame_count-1-last_index |
| `cameras[].interactions[].coverage.last_sample_age_sec` | ['number', 'null'] | 예 | seconds | sampling.timestamps_sec / observations | 영상 마지막 sample 기준 마지막 관측의 나이; clip duration 기준이 아님. last_sample_time-last_observed_time; 관측 없음 null |
| `cameras[].interactions[].coverage.leading_unobserved_samples` | integer | 아니오 | samples | tracks.observations | 첫 관측 앞의 미관측 샘플 수. 첫 index; 관측 없음이면 frame_count |
| `cameras[].interactions[].close_adjacent_span_sec` | ['number', 'null'] | 예 | seconds | pairwise_interactions.distance_series / observations | 인접 sample에서 두 번 모두 close인 시간차 합; contact duration 아님. sample index가 인접하고 양끝 close=true인 시간차만 합 |
| `cameras[].interactions[].distance_change_bh_per_sec` | ['number', 'null'] | 예 | body heights / second | pairwise_interactions.distance_series | 인접 co-observed sample에서 관측한 거리 변화율. 양수=거리 증가; 음수=감소. 인접 쌍 거리 변화 합 / 해당 시간차 합; 인접 쌍 없음 null |
| `cameras[].interactions[].relative_motion_mean_bh_per_sec` | ['number', 'null'] | 예 | body heights / second | pairwise_interactions.relative_motion_intensity | Canonical 상대 velocity 차이 norm 평균; co-movement/intent 판단 아님. 직접 전달; Canonical tracker max gap 제한 적용된 값, 중간 sample gap 가능 |
| `cameras[].interactions[].contact_proxy_terms_available` | integer | 아니오 | count of 3 terms | pairwise_interactions.contact_proxy.terms | 3개 contact proxy 구성 항 중 측정 가능한 항의 수. 일부 항만으로 재가중한 score의 coverage; 실제 contact 확인 아님. close_bbox_distance, pose_overlap, rapid_relative_motion 중 non-null 개수 |
| `cameras[].scene` | object | 아니오 | dimensionless / enum / structure | camera.scene_observations | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.person_entry_observed` | boolean | 아니오 | dimensionless / enum / structure | whole camera.scene_observations (any / count) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.person_exit_observed` | boolean | 아니오 | dimensionless / enum / structure | whole camera.scene_observations (any / count) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.large_spatial_transition_observed` | boolean | 아니오 | dimensionless / enum / structure | whole camera.scene_observations (any / count) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.occlusion_candidate_count` | integer | 아니오 | count | whole camera.scene_observations (any / count) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links` | array | 아니오 | count | camera.scene_observations.fragment_links | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[]` | object | 아니오 | count | camera.scene_observations.fragment_links | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].from_track` | string | 아니오 | dimensionless / enum / structure | camera.scene_observations.from_track | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].to_track` | string | 아니오 | dimensionless / enum / structure | camera.scene_observations.to_track | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].gap_sec` | ['number', 'null'] | 예 | seconds (clip-relative) | camera.scene_observations.gap_sec | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].distance_bh` | ['number', 'null'] | 예 | body heights | camera.scene_observations.distance_body_heights | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].same_person_confirmed` | const false | 아니오 | dimensionless / enum / structure | false constant: unconfirmed / unavailable (not negation of event) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change` | object / null | 예 | dimensionless / enum / structure | camera.scene_observations.posture_change | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change` | object | 아니오 | dimensionless / enum / structure | camera.scene_observations.posture_change | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.from` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | dimensionless / enum / structure | camera.scene_observations.from_posture | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.to` | enum ["standing", "crouched", "low_posture", "horizontal", "unknown", null] | 예 | dimensionless / enum / structure | camera.scene_observations.to_posture | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.confidence` | ['number', 'null'] | 예 | 0..1 proxy / enum | camera.scene_observations.confidence | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh` | object | 아니오 | body heights | camera.scene_observations.max_downward_change / fragment posture_change.downward_change | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | camera.scene_observations.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh.reliability` | enum ["limited", "normal"] | 아니오 | 0..1 proxy / enum | camera.scene_observations.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.fragment_links[].posture_change.downward_change_bh.note` | string | 아니오 | dimensionless / enum / structure | camera.scene_observations.max_downward_change / fragment posture_change.downward_change (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.boundary_semantics_available` | const false | 아니오 | dimensionless / enum / structure | false constant: unconfirmed / unavailable (not negation of event) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.boundary_crossing` | null | 예 | dimensionless / enum / structure | null constant: no scene ROI semantics | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].scene.authorization_known` | const false | 아니오 | dimensionless / enum / structure | false constant: unconfirmed / unavailable (not negation of event) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].selection_coverage` | object | 아니오 | dimensionless / enum / structure | whole camera tracks/pairs/fragment_links vs selected sets | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cameras[].selection_coverage.tracks_omitted` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.pairs_total` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.pairs_included` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.pairs_omitted` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.fragment_links_total` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.fragment_links_included` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.fragment_links_omitted` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 원본/포함/제외 집계; min observation filter, track filter 및 cap에 의한 제외 모두 포함. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.omitted_tracks_with_low_samples` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 선택으로 제외된 관측 신호 개수; 사건/안전 판정이 아님. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.omitted_tracks_with_upright_to_low` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 선택으로 제외된 관측 신호 개수; 사건/안전 판정이 아님. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.omitted_tracks_with_unknown_posture` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 선택으로 제외된 관측 신호 개수; 사건/안전 판정이 아님. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.omitted_pairs_with_close_samples` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 선택으로 제외된 관측 신호 개수; 사건/안전 판정이 아님. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cameras[].selection_coverage.omitted_fragment_posture_changes` | integer | 아니오 | count | tracks, pairwise_interactions, scene_observations.fragment_links (전체 Canonical camera) | 선택으로 제외된 관측 신호 개수; 사건/안전 판정이 아님. Serializer 선택 결과와 원본 차집합; low/transition/unknown/close/posture_change 관측 여부로 개수 집계 |
| `cross_camera` | object / null | 예 | dimensionless / enum / structure | state.cross_camera (base observations only) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera` | object | 아니오 | dimensionless / enum / structure | state.cross_camera (base observations only) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_a` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | dimensionless / enum / structure | cross_camera.camera_a | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_b` | enum ["CAM_01", "CAM_02", "CAM_03"] | 아니오 | dimensionless / enum / structure | cross_camera.camera_b | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.sync_confirmed` | const false | 아니오 | dimensionless / enum / structure | false constant: unconfirmed / unavailable (not negation of event) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.identity_link_confirmed` | const false | 아니오 | dimensionless / enum / structure | false constant: unconfirmed / unavailable (not negation of event) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.alignment` | string | 아니오 | dimensionless / enum / structure | normalized clip phase only constant | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.person_count_similarity` | object | 아니오 | 0..1 proxy / enum | cross_camera.person_count_similarity | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.person_count_similarity.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | cross_camera.person_count_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.person_count_similarity.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | cross_camera.person_count_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.person_count_similarity.note` | string | 아니오 | dimensionless / enum / structure | cross_camera.person_count_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.temporal_pattern_similarity` | object | 아니오 | 0..1 proxy / enum | cross_camera.temporal_pattern_similarity | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.temporal_pattern_similarity.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | cross_camera.temporal_pattern_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.temporal_pattern_similarity.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | cross_camera.temporal_pattern_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.temporal_pattern_similarity.note` | string | 아니오 | dimensionless / enum / structure | cross_camera.temporal_pattern_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.motion_peak_similarity` | object | 아니오 | 0..1 proxy / enum | cross_camera.motion_peak_similarity | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.motion_peak_similarity.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | cross_camera.motion_peak_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.motion_peak_similarity.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | cross_camera.motion_peak_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.motion_peak_similarity.note` | string | 아니오 | dimensionless / enum / structure | cross_camera.motion_peak_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.posture_transition_similarity` | object | 아니오 | 0..1 proxy / enum | cross_camera.posture_transition_similarity | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.posture_transition_similarity.value` | ['number', 'null'] | 예 | dimensionless / enum / structure | cross_camera.posture_transition_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.posture_transition_similarity.reliability` | const "limited" | 아니오 | 0..1 proxy / enum | cross_camera.posture_transition_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.posture_transition_similarity.note` | string | 아니오 | dimensionless / enum / structure | cross_camera.posture_transition_similarity (proxy value / explicit limitation) | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.visibility_complementarity` | ['number', 'null'] | 예 | dimensionless / enum / structure | cross_camera.visibility_complementarity_score | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_a_visibility_drop_observed` | boolean | 아니오 | dimensionless / enum / structure | cross_camera.camera_a_visibility_drop | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_b_visibility_drop_observed` | boolean | 아니오 | dimensionless / enum / structure | cross_camera.camera_b_visibility_drop | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_b_has_observations_during_a_low_visibility_phase` | boolean | 아니오 | dimensionless / enum / structure | cross_camera.camera_b_has_observations_during_a_low_visibility_phase | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_a_has_observations_during_b_low_visibility_phase` | boolean | 아니오 | dimensionless / enum / structure | cross_camera.camera_a_has_observations_during_b_low_visibility_phase | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_a_low_visibility_phases` | array | 아니오 | dimensionless / enum / structure | cross_camera.camera_a_low_visibility_phases | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_a_low_visibility_phases[]` | array | 아니오 | dimensionless / enum / structure | cross_camera.camera_a_low_visibility_phases | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_a_low_visibility_phases[][]` | number | 아니오 | dimensionless / enum / structure | cross_camera.camera_a_low_visibility_phases | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_b_low_visibility_phases` | array | 아니오 | dimensionless / enum / structure | cross_camera.camera_b_low_visibility_phases | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_b_low_visibility_phases[]` | array | 아니오 | dimensionless / enum / structure | cross_camera.camera_b_low_visibility_phases | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.camera_b_low_visibility_phases[][]` | number | 아니오 | dimensionless / enum / structure | cross_camera.camera_b_low_visibility_phases | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `cross_camera.person_count_by_phase` | object | 아니오 | count | cross_camera.phase_curves[camera].count | v1 관측 요약 유지; 원천 값의 null을 보존 |
| `evidence_semantics` | string | 아니오 | dimensionless / enum / structure | serializer constant | v1 관측 요약 유지; 원천 값의 null을 보존 |
