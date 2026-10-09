import json
import time
from pathlib import Path
from fastapi.testclient import TestClient
from runtime477.server import Runtime, create_app

CFG = json.loads((Path(__file__).parents[1]/'config.json').read_text())


def test_status_clock_ack_evidence_and_human_update(tmp_path):
    rt = Runtime(CFG, tmp_path)
    with TestClient(create_app(rt)) as client:
        assert client.get('/').status_code == 200
        assert len(client.get('/api/snapshot').json()['cameras']) == 9
        c, _ = rt.ledger.detect({'camera_id': 'CAM_01', 'pts': 2, 't1': time.time(), 'observations': {}},
                                {'reason': 'MOTION_CHANGE', 'zone': 'scene'}, b'preview')
        cid = c['candidate_id']
        assert client.get('/evidence/'+cid+'/preview').content == b'preview'
        assert client.get('/evidence/'+cid+'/unknown').status_code == 404
        assert client.post('/api/candidates/'+cid+'/displayed', json={'t3_server_epoch': c['t1']-1, 'clock_uncertainty_ms': 1}).status_code == 422
        payload = {'t3_server_epoch': time.time(), 'clock_uncertainty_ms': 1}
        assert client.post('/api/candidates/'+cid+'/displayed', json=payload).status_code == 200
        first = c['t3']
        assert client.post('/api/candidates/'+cid+'/displayed', json=payload).status_code == 200
        assert c['t3'] == first
        client.post('/api/candidates/'+cid+'/human', json={'action': 'dismissed'})
        assert not rt.ledger.update(cid, 0, status='AI_DANGER_ESTIMATE')
        assert c['human_disposition'] == 'dismissed'
        assert client.get('/api/metrics').json()['candidate_to_frontend_ms']['count'] == 1


def test_websocket_reconnect_snapshot_and_bounded_subscriber(tmp_path):
    rt = Runtime(CFG, tmp_path)
    with TestClient(create_app(rt)) as client:
        with client.websocket_connect('/ws') as ws:
            first = ws.receive_json()
            assert first['instance'] == rt.instance
        rt.ledger.audit('test_event', {})
        with client.websocket_connect('/ws') as ws:
            assert ws.receive_json()['revision'] > first['revision']


def test_recorded_mode_never_enables_provider(tmp_path):
    recorded = tmp_path/'recorded.json'
    recorded.write_text('[]')
    rt = Runtime(dict(CFG, ai_enabled=True, mode='RECORDED_RESULT_DEMO_MODE', recorded_results=str(recorded)), tmp_path/'run')
    assert not rt.cfg['ai_enabled'] and rt.cfg['mode'] == 'RECORDED_RESULT_DEMO_MODE'
