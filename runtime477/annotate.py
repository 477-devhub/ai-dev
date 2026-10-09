"""Join independently human-annotated source timestamps to a saved replay.

Annotation JSON: [{"candidate_id":"cand_...", "t0_video_sec":1.2,
                  "annotator":"human name", "uncertainty_sec":0.1}]
This offline join never feeds the detector or provider.
"""
import argparse
import json
from pathlib import Path
from .server import summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('annotations', type=Path)
    args = parser.parse_args()
    events = [json.loads(line) for line in (args.run/'audit.jsonl').read_text(encoding='utf-8').splitlines()]
    epoch = next(e['data']['epoch'] for e in events if e['kind'] == 'replay_epoch')
    candidates = {}
    for event in events:
        if event['kind'] in ('detected', 'updated', 'merged'):
            candidates[event['data']['candidate_id']] = event['data']
    rows = []
    for annotation in json.loads(args.annotations.read_text(encoding='utf-8')):
        if not annotation.get('annotator') or not isinstance(annotation['t0_video_sec'], (int, float)) or annotation['t0_video_sec'] < 0:
            raise ValueError('Human annotator and nonnegative timestamp required')
        c = candidates[annotation['candidate_id']]
        t0 = epoch + annotation['t0_video_sec']
        rows.append(dict(annotation, t0_wall=t0, t1=c['t1'], t2=c['t2'], t3=c['t3'],
                         time_to_first_alert_ms=(c['t3']-t0)*1000 if c['t3'] else None))
    output = {'scope': 'human annotation joined offline; playback PTS seconds', 'annotations': rows,
              'time_to_first_alert_ms': summary([r['time_to_first_alert_ms'] for r in rows if r['time_to_first_alert_ms'] is not None])}
    (args.run/'human-t0-report.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
