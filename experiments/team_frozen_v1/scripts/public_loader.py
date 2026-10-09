"""Pixels/relative timestamps only; no source descriptions, labels or reference input."""
from common import *
def rows(identifier):
    j=job(identifier)
    return [r for r in read(PUBLIC/f"data/frames/{j['item_id']}/manifest.json")['frames'] if r['source_id']==j['source_id']]
def load_item(identifier):
    rr=rows(identifier)
    return {'item_id':identifier,'task':'single','input_fingerprint':{
        'sampling_protocol_id':'uniform_total64_v1','team_source_suballocation':len(rr),
        'prompt_sha256':digest(ROOT/'benchmark_v1/model_input/prompt_v1.txt'),
        'prediction_schema_sha256':digest(ROOT/'benchmark_v1/schemas/prediction.schema.json'),
        'media_sha256':{'CAM_01':hashlib.sha256(''.join(r['sha256'] for r in rr).encode()).hexdigest()},
        'frame_numbers':{'CAM_01':[r['frame_number'] for r in rr]}},
        'media_handles_private_to_harness':[{'camera':'CAM_01','frame_numbers':[r['frame_number'] for r in rr],
            'frame_timestamps_sec':[r['timestamp_sec'] for r in rr]}]}
def iter_model_frames(identifier):
    from PIL import Image
    for r in rows(identifier):
        p=(PUBLIC/r['image_path']).resolve()
        if not p.is_relative_to(PUBLIC.resolve()) or digest(p)!=r['sha256']:raise RuntimeError('Image drift')
        with Image.open(p) as image:
            rgb=image.convert('RGB')
            assert rgb.size==(r['width'],r['height'])
            yield {'camera':'CAM_01','timestamp_sec':r['timestamp_sec'],'width':r['width'],
                   'height':r['height'],'rgb24':rgb.tobytes()}
def load_frames(identifier):
    import time
    started=time.perf_counter(); frames=[]
    for f in iter_model_frames(identifier):
        frames.append({**f,'ref':f'F{len(frames)+1:03d}','rgb_sha256':hashlib.sha256(f['rgb24']).hexdigest()})
    assert len(frames)==job(identifier)['frame_count']
    return frames,(time.perf_counter()-started)*1000,{'CAM_01':len(frames)},load_item(identifier)['input_fingerprint']
