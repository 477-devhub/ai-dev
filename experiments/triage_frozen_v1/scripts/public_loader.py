"""Canonical 64-frame adapter for the triage public manifest, with no GT inputs."""
import subprocess
from common import BENCH, ROOT, read, digest

def load_item(item_id):
    doc = read(BENCH/'public_manifest.json')
    item = next(i for i in doc['items'] if i['item_id'] == item_id)
    handles, frames, hashes = [], {}, {}
    for camera in item['cameras']:
        cam = camera['camera']
        schedule = camera['frame_schedule_uniform_total64_v1']
        path = (BENCH/camera['media']).resolve()
        if not path.is_relative_to((BENCH/'media').resolve()) or digest(path) != camera['sha256']:
            raise RuntimeError('Unsafe media path or frozen media drift')
        if len(schedule) != 64 or len({r['frame_index'] for r in schedule}) != 64:
            raise RuntimeError('Exactly 64 distinct canonical frames required')
        frames[cam] = [r['frame_index'] for r in schedule]
        hashes[cam] = camera['sha256']
        handles.append({'camera':cam, 'local_path':str(path), 'frame_numbers':frames[cam],
                        'frame_timestamps_sec':[r['t_sec'] for r in schedule],
                        'width':camera['width'], 'height':camera['height']})
    # Frozen prediction schema/prompt hashes are harness fingerprint metadata only.
    fp = {'prompt_sha256':digest(ROOT/'benchmark_v1/model_input/prompt_v1.txt'),
          'prediction_schema_sha256':digest(ROOT/'benchmark_v1/schemas/prediction.schema.json'),
          'media_sha256':hashes, 'sampling_protocol_id':'uniform_total64_v1', 'frame_numbers':frames}
    return {'item_id':item_id, 'task':item['task'], 'input_fingerprint':fp,
            'media_handles_private_to_harness':handles}

def iter_model_frames(item_id):
    for handle in load_item(item_id)['media_handles_private_to_harness']:
        expression = '+'.join('eq(n,%d)'%n for n in handle['frame_numbers'])
        command = ['ffmpeg','-v','error','-nostdin','-i',handle['local_path'],'-vf',"select='"+expression+"'",
                   '-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','pipe:1']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        size = handle['width']*handle['height']*3
        try:
            for timestamp in handle['frame_timestamps_sec']:
                chunks, remaining = [], size
                while remaining:
                    chunk = process.stdout.read(remaining)
                    if not chunk:
                        raise RuntimeError('Canonical frame decoding truncated')
                    chunks.append(chunk)
                    remaining -= len(chunk)
                yield {'camera':handle['camera'], 'timestamp_sec':timestamp,
                       'width':handle['width'], 'height':handle['height'], 'rgb24':b''.join(chunks)}
            if process.stdout.read(1) or process.wait() != 0:
                raise RuntimeError('Canonical decoding count/exit mismatch')
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.terminate()
            process.wait()
