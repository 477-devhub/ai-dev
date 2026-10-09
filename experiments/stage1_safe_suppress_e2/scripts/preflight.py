"""Local SDK / key-presence checks only; never sends a network request."""
import inspect
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from e2_common import ROOT, write


def main():
    import openai, httpx2, decisions_client
    from utils import load_api_key_env
    info={'sdk_version':openai.__version__,'http_client_version':httpx2.__version__,
        'decisions_resource_available':hasattr(openai.OpenAI,'decisions'),
        'api_key_configured':bool(load_api_key_env()),'model':decisions_client.MODEL,
        'endpoint':'/v1/decisions','network_requests':0,
        'account_model_access':'NOT VERIFIED (no request)',
        'original_application_retries':decisions_client.MAX_RETRIES,
        'e2_application_retries':0,'e2_sdk_retries':0}
    write(ROOT/'reports/api_preflight.json',info)
    print(info)


if __name__=='__main__': main()
