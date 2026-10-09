"""Decision values + compact state -> benchmark prediction (prediction.schema.json), via the frozen P1 templates.

The P1 template module experiments/p1_decisions/src/prediction_adapter.py is loaded from its exact frozen bytes (SHA256
checked against p1_freeze.json). Only the provider-name strings below are substituted so explanations do not claim the
OpenAI Decisions API produced P2 answers. Evidence, temporal summary, uncertainty rules, reason structure, attention
queue text and multi-camera text are otherwise byte-identical to P1:

  CV -> Evidence (deterministic templates)   Clef-Flash -> Decision   Template -> Explanation (no model free text)
"""
import types

from utils import P1_ROOT, sha256_bytes

REL = 'src/prediction_adapter.py'
PROVIDER_SUBSTITUTIONS = [
    ('was refused by the Decisions API and treated as unknown',
     'was missing or invalid in the Clef-Flash response and treated as unknown'),
    ('OpenAI Decisions API ({model}) typed answers', 'Cloudflare Workers AI Clef-Flash ({model}) typed answers'),
    ('(Decisions API scores)', '(Clef-Flash scores)'),
    ('Decisions API same-incident probability', 'Clef-Flash same-incident probability'),
    ('Decisions API: second view adds', 'Clef-Flash: second view adds'),
]


def load_templates(p1_freeze):
    src = (P1_ROOT / REL).read_bytes()
    if sha256_bytes(src) != p1_freeze['hashes'][REL]:
        raise RuntimeError(f'{REL} differs from p1_freeze.json')
    text = src.decode('utf-8')
    for old, new in PROVIDER_SUBSTITUTIONS:
        if text.count(old) != 1:
            raise RuntimeError(f'provider substitution not unique in P1 templates: {old!r}')
        text = text.replace(old, new)
    mod = types.ModuleType('p2_prediction_templates')
    mod.__file__ = str(P1_ROOT / REL) + ' [P2 provider-name substitutions]'
    exec(compile(text, mod.__file__, 'exec'), mod.__dict__)
    return mod, {'p1_source_sha256': sha256_bytes(src), 'substituted_source_sha256': sha256_bytes(text.encode('utf-8')),
                 'substitutions': [list(x) for x in PROVIDER_SUBSTITUTIONS]}
