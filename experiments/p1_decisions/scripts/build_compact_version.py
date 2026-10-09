"""Offline serializer CLI. Explicit version and output; never imports API clients."""
import argparse
from pathlib import Path

import _bootstrap
from compact_versions import prepare_compact
from utils import read_allowed_json, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--version', choices=['v1', 'v2'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Keep cached v1 artifacts, configs, frozen outputs and backend paths untouched.
    safe_root = Path(__file__).resolve().parents[1] / 'e1_v2'
    if not args.output.resolve().is_relative_to(safe_root.resolve()):
        parser.error('output must be under experiments/p1_decisions/e1_v2')
    result = prepare_compact(read_allowed_json(args.input), args.version)
    write_json(args.output, result['compact'])
    print(f"{result['compact']['schema_version']} {result['compact_sha256']} -> {args.output}")


if __name__ == '__main__': main()
