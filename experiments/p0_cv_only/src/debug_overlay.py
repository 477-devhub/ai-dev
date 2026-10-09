"""Human-inspection overlays: generic track ID, bbox, keypoints, posture proxy, timestamp, confidence.
Never draws ground truth, expected events, annotations or private references."""
import cv2
import numpy as np

from utils import DEBUG_DIR

SKELETON = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
SCALE = 0.5


def _color(track_id):
    if not track_id:
        return (200, 200, 200)
    n = int(track_id[1:])
    rng = np.random.RandomState(n * 7919)
    return tuple(int(x) for x in rng.randint(60, 255, 3))


def render_item(item_id, state, kept_frames, vis_conf=0.5):
    out_dir = DEBUG_DIR / 'overlays' / item_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for cam in state['cameras']:
        frames = kept_frames[cam['camera_id']]
        thumbs = []
        for f, (ts, rgb) in zip(cam['frames'], frames):
            img = cv2.resize(np.ascontiguousarray(rgb[:, :, ::-1]), None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
            H, W = img.shape[:2]
            for d in f['detections']:
                c = _color(d['track_id'])
                x1, y1, x2, y2 = d['bbox_norm']
                p1, p2 = (int(x1 * W), int(y1 * H)), (int(x2 * W), int(y2 * H))
                cv2.rectangle(img, p1, p2, c, 2)
                if d['keypoints_norm']:
                    kp = d['keypoints_norm']
                    for a, b in SKELETON:
                        if kp[a][2] >= vis_conf and kp[b][2] >= vis_conf:
                            cv2.line(img, (int(kp[a][0] * W), int(kp[a][1] * H)), (int(kp[b][0] * W), int(kp[b][1] * H)), c, 1)
                    for x, y, k in kp:
                        if k >= vis_conf:
                            cv2.circle(img, (int(x * W), int(y * H)), 2, c, -1)
                p = d['posture']
                label = f"{d['track_id']} {p['label']}" + (f" {p['confidence']:.2f}" if p['confidence'] is not None else '') + f" det{d['confidence']:.2f}"
                cv2.putText(img, label, (p1[0], max(12, p1[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 3)
                cv2.putText(img, label, (p1[0], max(12, p1[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1)
            head = f"{cam['camera_id']} t={f['timestamp_sec']:.2f}s  persons={f['person_count']}"
            cv2.putText(img, head, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(img, head, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.imwrite(str(out_dir / f"{cam['camera_id']}_{f['index']:02d}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            thumbs.append(cv2.resize(img, (320, 180), interpolation=cv2.INTER_AREA))
        cols = 8
        while len(thumbs) % cols:
            thumbs.append(np.zeros_like(thumbs[0]))
        sheet = np.vstack([np.hstack(thumbs[i:i + cols]) for i in range(0, len(thumbs), cols)])
        cv2.imwrite(str(out_dir / f"{cam['camera_id']}_contact_sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return out_dir
