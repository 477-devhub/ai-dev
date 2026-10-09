"""Synthetic neutral image sequences for integration tests (moving circle / appearing rectangle). Not benchmark-like."""
import _bootstrap  # noqa: F401
from PIL import Image, ImageDraw

from utils import sha256_bytes

TASKS = {'single': {'CAM_01': 6}, 'attention': {'CAM_01': 2, 'CAM_02': 2, 'CAM_03': 2}, 'multi_camera': {'CAM_01': 3, 'CAM_02': 3}}


def frames(task, w=320, h=240):
    out, n = [], 0
    for ci, (cam, k) in enumerate(TASKS[task].items()):
        for j in range(k):
            im = Image.new('RGB', (w, h), (235, 235, 235))
            d = ImageDraw.Draw(im)
            x = 30 + j * 45 + ci * 10
            d.ellipse([x, 100, x + 40, 140], fill=(40, 90, 200))
            if j % 2:
                d.rectangle([200, 30, 260, 80], fill=(200, 120, 40))
            n += 1
            rgb = im.tobytes()
            out.append({'ref': f'F{n:03d}', 'camera': cam, 'timestamp_sec': round(j * 0.5, 3), 'width': w, 'height': h, 'rgb24': rgb, 'rgb_sha256': sha256_bytes(rgb)})
    return out
