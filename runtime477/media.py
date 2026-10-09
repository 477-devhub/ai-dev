import asyncio
import json
import os
import tempfile
from pathlib import Path


async def prepare(path, end_ms, python, timeout=240):
    with tempfile.TemporaryDirectory(prefix='477-runtime-') as name:
        directory = Path(name)
        request = directory/'request.json'
        request.write_text(json.dumps({'path': str(path), 'end_ms': end_ms}))
        proc = await asyncio.create_subprocess_exec(python, str(Path(__file__).with_name('prepare_worker.py')),
            str(request), str(directory), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            **({'creationflags': 0x00004000} if os.name == 'nt' else {}))
        try:
            await asyncio.wait_for(proc.wait(), timeout)
            if proc.returncode:
                raise ValueError('prepare_failed')
            result = json.loads((directory/'result.json').read_text())
            result['_assets'] = {f['ref']: (directory/(f['ref']+'.webp')).read_bytes() for f in result['frames']}
            return result
        finally:
            if proc.returncode is None:
                if os.name == 'nt':
                    killer = await asyncio.create_subprocess_exec('taskkill', '/PID', str(proc.pid), '/T', '/F',
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                    await killer.wait()
                if proc.returncode is None:
                    proc.kill()
                await proc.wait()
