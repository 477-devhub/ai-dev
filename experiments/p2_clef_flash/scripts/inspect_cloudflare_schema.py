"""Fetch the live Workers AI model schema for @cf/cloudflare/clef-flash (+ model catalog entry) before any model call.
Writes logs/cloudflare_schema_snapshot.json. No inference request is made. Credentials are never recorded."""
import _bootstrap  # noqa: F401
import datetime
import os
import sys

import httpx

from utils import LOGS_DIR, load_cloudflare_env, redact, write_json

MODEL = '@cf/cloudflare/clef-flash'
BASE = 'https://api.cloudflare.com/client/v4/accounts/{acc}/ai'


def get(client, url, params):
    r = client.get(url, params=params)
    try:
        body = r.json()
    except Exception:
        body = {'non_json_body': redact(r.text[:2000])}
    return {'url_template': url.replace(os.environ['CLOUDFLARE_ACCOUNT_ID'], '{ACCOUNT_ID}'), 'params': params,
            'http_status': r.status_code, 'body': body}


def main():
    if not load_cloudflare_env():
        sys.exit('CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN not available')
    base = BASE.format(acc=os.environ['CLOUDFLARE_ACCOUNT_ID'])
    hdr = {'Authorization': f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"}
    with httpx.Client(headers=hdr, timeout=httpx.Timeout(60.0, connect=10.0)) as c:
        schema = get(c, f'{base}/models/schema', {'model': MODEL})
        search = get(c, f'{base}/models/search', {'search': 'clef'})
    snap = {
        'fetched_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'model': MODEL,
        'sources': {'model_schema_endpoint': 'GET /accounts/{ACCOUNT_ID}/ai/models/schema?model=@cf/cloudflare/clef-flash',
                    'model_catalog_endpoint': 'GET /accounts/{ACCOUNT_ID}/ai/models/search?search=clef',
                    'documentation': 'https://developers.cloudflare.com/workers-ai/models/clef-flash/'},
        'model_schema_response': schema,
        'model_catalog_response': search,
        'note': 'Authoritative live schema. Authorization header and account id are never recorded.',
    }
    write_json(LOGS_DIR / 'cloudflare_schema_snapshot_raw.json', snap)
    print('schema endpoint HTTP', schema['http_status'], '| catalog HTTP', search['http_status'])
    if schema['http_status'] != 200 or not schema['body'].get('success'):
        sys.exit('model schema not retrievable; refusing to implement from guesses')
    inp, out = schema['body']['result']['input'], schema['body']['result']['output']
    qv = inp['properties']['questions']
    cat = next((m for m in search['body'].get('result', []) if m['name'] == MODEL), None)
    props = {p['property_id']: p['value'] for p in (cat or {}).get('properties', [])}
    summary = {
        'fetched_at': snap['fetched_at'],
        'model_identifier': MODEL,
        'model_input_selector': {'field': 'model', 'pattern': inp['properties']['model']['pattern'],
                                 'value_used': 'clef-flash'},
        'required_request_fields': inp['required'],
        'question_container': {'type': qv['type'], 'min': qv['minProperties'], 'max': qv['maxProperties'],
                               'id_rule': qv['description']},
        'question_types': {
            o['properties']['type']['enum'][0]: {'required': o['required'], 'criteria': o['properties'].get('criteria', {}).get('description'),
                                                 'criteria_limits': {k: o['properties']['criteria'][k] for k in ('minItems', 'maxItems') if k in o['properties'].get('criteria', {})}}
            for o in qv['additionalProperties']['oneOf']},
        'response_structure': {
            'required': out['required'],
            'answers': {o['properties']['type']['enum'][0]: o['required'] for o in out['properties']['answers']['additionalProperties']['oneOf']},
            'refusal_answer_type': 'none defined in the output schema',
        },
        'usage_structure': out['properties']['usage'],
        'limits': {'questions_per_request': [qv['minProperties'], qv['maxProperties']],
                   'score_levels': '2-10', 'choice_options': '2-255',
                   'images': inp['properties']['images']['description'],
                   'state_truncation': inp['properties']['state']['description']},
        'context_window_tokens': int(props['context_window']) if 'context_window' in props else None,
        'pricing_catalog': props.get('price'),
        'catalog_description': (cat or {}).get('description'),
        'raw_snapshot_file': 'logs/cloudflare_schema_snapshot_raw.json',
    }
    write_json(LOGS_DIR / 'cloudflare_schema_snapshot.json', summary)
    print('question types:', list(summary['question_types']), '| context window:', summary['context_window_tokens'],
          '| price:', summary['pricing_catalog'])


if __name__ == '__main__':
    main()
