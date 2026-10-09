"""Decision values + compact state -> benchmark prediction via the frozen P1 templates (same as P1/P2).

experiments/p1_decisions/src/prediction_adapter.py is executed from its frozen bytes (SHA256 checked against
p1_freeze.json) with provider-name substitutions only. CV -> Evidence (templates), GPT-6.1 Sol -> Decision, Template ->
Explanation. No model-generated prose.
"""
import types

from utils import P1_ROOT, sha256_bytes

REL = 'src/prediction_adapter.py'
PROVIDER_SUBSTITUTIONS = [
    ('was refused by the Decisions API and treated as unknown',
     'was refused by GPT-6.1 Sol (Responses API) and treated as unknown'),
    ('OpenAI Decisions API ({model}) typed answers', 'OpenAI Responses API GPT-6.1 Sol ({model}) structured estimates'),
    ('(Decisions API scores)', '(GPT-6.1 Sol scores)'),
    ('Decisions API same-incident probability', 'GPT-6.1 Sol same-incident probability'),
    ('Decisions API: second view adds', 'GPT-6.1 Sol: second view adds'),
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
    mod = types.ModuleType('p3_prediction_templates')
    mod.__file__ = str(P1_ROOT / REL) + ' [P3 provider-name substitutions]'
    exec(compile(text, mod.__file__, 'exec'), mod.__dict__)
    return mod, {'p1_source_sha256': sha256_bytes(src), 'substituted_source_sha256': sha256_bytes(text.encode('utf-8')),
                 'substitutions': [list(x) for x in PROVIDER_SUBSTITUTIONS]}


def load_p1_decision_adapter(p1_freeze):
    rel = 'src/decision_adapter.py'
    src = (P1_ROOT / rel).read_bytes()
    if sha256_bytes(src) != p1_freeze['hashes'][rel]:
        raise RuntimeError(f'{rel} differs from p1_freeze.json')
    mod = types.ModuleType('p1_decision_adapter')
    exec(compile(src.decode('utf-8'), str(P1_ROOT / rel), 'exec'), mod.__dict__)
    return mod, sha256_bytes(src)
