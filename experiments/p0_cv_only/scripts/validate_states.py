"""Validate every states/ITEM_XX.json against schemas/canonical_cv_state.schema.json plus protocol invariants."""
import _bootstrap  # noqa: F401
import sys

from frame_source import CanonicalFrameSource
from utils import ITEM_IDS, STATES_DIR, read_json
from validation import validate_state


def main():
    ok = True
    for item in ITEM_IDS:
        p = STATES_DIR / f'{item}.json'
        try:
            s = read_json(p)
            validate_state(s)
            src = CanonicalFrameSource(item)   # public loader metadata only; no frames decoded here
            if s['input']['benchmark_input_fingerprint'] != src.benchmark_fingerprint:
                raise ValueError('benchmark input fingerprint mismatch')
            for cam in s['cameras']:
                nums = [f['frame_number'] for f in cam['frames']]
                if nums != src.frame_numbers[cam['camera_id']]:
                    raise ValueError(f"{cam['camera_id']}: frame numbers differ from canonical schedule")
                if cam['scene_observations']['boundary_crossing'] is not None:
                    raise ValueError('boundary_crossing must be null (unavailable)')
            if (s['cross_camera'] is None) != (len(s['cameras']) != 2):
                raise ValueError('cross_camera presence inconsistent with camera count')
            print(f'{item}: PASS ({len(s["cameras"])} camera(s), {sum(len(c["tracks"]) for c in s["cameras"])} tracks)')
        except Exception as e:
            ok = False
            print(f'{item}: FAIL - {e}')
    print('ALL STATES VALID' if ok else 'STATE VALIDATION FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
