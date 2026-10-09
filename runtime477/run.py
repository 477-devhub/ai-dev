"""python -m runtime477.run [--ai] [--port 8011] [--max-ai-jobs 3]."""
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8011)
    parser.add_argument('--ai', action='store_true')
    parser.add_argument('--max-ai-jobs', type=int, default=3)
    parser.add_argument('--env-file', default='experiments/.env')
    args = parser.parse_args()
    if args.ai:
        from dotenv import load_dotenv
        load_dotenv(Path(args.env_file), override=False)
        if not os.environ.get('OPENAI_API_KEY'):
            parser.error('OPENAI_API_KEY is not configured')
        os.environ['RUNTIME_AI'] = '1'
        os.environ['RUNTIME_MAX_AI_JOBS'] = str(args.max_ai_jobs)
    import uvicorn
    uvicorn.run('runtime477.server:app', host='127.0.0.1', port=args.port, workers=1, access_log=False)


if __name__ == '__main__':
    main()
