"""Fair factorial inputs: compact version and added predicate are the only factors."""
import copy
import os
import time

from e2_common import ROOT, P1, read, digest, file_hash, canonical
from compact_versions import prepare_compact


def question_configs():
    original = read(ROOT/'configs/original.json')
    safe = read(ROOT/'configs/original_plus_safe.json')
    if original != read(P1/'configs/decisions_questions_v1.json'):
        raise ValueError('E2 original questions differ from protected P1 config')
    rest = {k:v for k,v in safe.items() if k != 'e2_safe_question'}
    rest['decision_questions_version'] = original['decision_questions_version']
    if rest != original:
        raise ValueError('safe config may only add e2_safe_question and version')
    return original, safe


def build_questions(task, cameras, cfg):
    # Exact original builder reused; it performs no network calls.
    from decisions_client import build_questions as original_build
    out = original_build(task,cameras,cfg)
    extra = cfg.get('e2_safe_question')
    if extra:
        if task == 'attention':
            scopes = [(c.lower().replace('_','')+'_',cfg['scope']['camera'].format(camera=c)) for c in cameras]
        else:
            scopes = [('',cfg['scope']['single' if task == 'single' else 'multi_camera'])]
        for prefix, scope in scopes:
            out.append({'type':'predicate','name':prefix+extra['key'],
                'instructions':f"{scope} {extra['instructions']} {cfg['policy']}".strip()})
    return out


def token_estimate(text):
    cache = P1/'e1_v2/.cache'
    if cache.is_dir(): os.environ.setdefault('TIKTOKEN_CACHE_DIR',str(cache))
    try:
        import tiktoken
        return {'tokens':len(tiktoken.get_encoding('o200k_base').encode(text)),
                'method':'o200k_base proxy; not actual Decisions billing tokens'}
    except (ImportError, OSError, ValueError):
        return {'tokens':(len(text.encode('utf-8'))+3)//4,'method':'UTF-8 bytes/4 heuristic'}


def prepare_arms(state):
    original, safe = question_configs()
    cfg = read(ROOT/'configs/experiment.json')
    out = {}
    for arm, spec in cfg['arms'].items():
        start = time.perf_counter()
        prep = prepare_compact(state, spec['state'])
        qcfg = original if spec['questions']=='original.json' else safe
        questions = build_questions(prep['compact']['task'],[c['camera'] for c in prep['compact']['cameras']],qcfg)
        request = {'model':cfg['model'],'input':prep['input_text'],'questions':questions}
        request_bytes = len(canonical(request).encode('utf-8'))
        if request_bytes > cfg['request_byte_ceiling']: raise ValueError('request exceeds E2 byte ceiling')
        out[arm] = {**prep,'questions':questions,'task':state['input']['task'],
            'camera_ids':[c['camera'] for c in prep['compact']['cameras']],
            'state_version':spec['state'],'question_version':qcfg['decision_questions_version'],
            'canonical_state_hash':digest(state),'input_hash':digest(prep['input_text']),
            'prompt_hash':digest(questions),'question_config_hash':digest(qcfg),
            'question_config_file_hash':file_hash(ROOT/'configs'/spec['questions']),
            'request_hash':digest(request),'request_bytes':request_bytes,
            'serializer_prepare_ms':round((time.perf_counter()-start)*1000,4),
            'compact_input_tokens_estimated':token_estimate(prep['input_text']),
            'request_tokens_estimated':token_estimate(canonical(request)),
            'feature_bytes':feature_bytes(prep['compact'])}
    assert out['A']['input_hash']==out['B']['input_hash'] and out['C']['input_hash']==out['D']['input_hash']
    assert out['A']['prompt_hash']==out['C']['prompt_hash'] and out['B']['prompt_hash']==out['D']['prompt_hash']
    assert out['B']['questions'][:len(out['A']['questions'])]==out['A']['questions']
    return out


def feature_bytes(compact):
    # Disjoint new fields only; not causal performance ablation or additive tokenizer deltas.
    groups = {k:[] for k in ['coverage_gap_tail','posture_runs_recovery_unknown','detection_tracking_quality',
                             'interaction_evidence','selection_omission']}
    if compact['schema_version'].endswith('v1'): return None
    for c in compact['cameras']:
        groups['coverage_gap_tail'].append(c['sampling']['timestamps_sec'])
        groups['detection_tracking_quality'].append({k:v for k,v in c['quality'].items() if k in
            ('aggregate_inputs_complete','mean_brightness','mean_contrast','mean_sharpness')})
        groups['selection_omission'].append(c['selection_coverage'])
        for t in c['tracks']:
            groups['coverage_gap_tail'].append(t['coverage'])
            groups['posture_runs_recovery_unknown'].append(t['temporal'])
            groups['detection_tracking_quality'].append({k:t[k] for k in
                ('mean_detection_confidence','association_confidence','fragment_link_candidates')})
        for p in c['interactions']:
            groups['interaction_evidence'].append({k:p[k] for k in ('coverage','close_adjacent_span_sec',
                'distance_change_bh_per_sec','relative_motion_mean_bh_per_sec','contact_proxy_terms_available')})
    return {k:len(canonical(v).encode('utf-8')) for k,v in groups.items()}
