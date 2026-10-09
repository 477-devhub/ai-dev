"""Record the execution environment (OS, Python, PyTorch, CUDA, GPU, OpenCV, Ultralytics, CPU, RAM)."""
import _bootstrap  # noqa: F401
import json
import platform
import shutil
import subprocess

from utils import LOGS_DIR, write_json


def main():
    env = {'os': platform.platform(), 'machine': platform.machine(), 'python': platform.python_version(), 'python_executable': __import__('sys').executable}
    try:
        import torch
        env.update({'torch': torch.__version__, 'cuda_available': torch.cuda.is_available(), 'cuda_version': torch.version.cuda,
                    'cudnn_version': torch.backends.cudnn.version() if torch.cuda.is_available() else None,
                    'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                    'gpu_vram_total_mb': round(torch.cuda.get_device_properties(0).total_memory / 2**20) if torch.cuda.is_available() else None})
    except Exception as e:
        env['torch'] = f'unavailable: {e}'
    for mod in ('torchvision', 'cv2', 'ultralytics', 'numpy', 'scipy', 'jsonschema', 'yaml', 'psutil'):
        try:
            from importlib import metadata
            dist = {'cv2': 'opencv-python', 'yaml': 'pyyaml'}.get(mod, mod)
            env[mod] = metadata.version(dist)
        except Exception as e:
            env[mod] = f'unavailable: {e}'
    try:
        import psutil
        env['ram_total_gb'] = round(psutil.virtual_memory().total / 2**30, 2)
        env['cpu_logical_cores'] = psutil.cpu_count()
        env['cpu_physical_cores'] = psutil.cpu_count(logical=False)
    except Exception:
        pass
    env['cpu'] = platform.processor()
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, '\\'.join(['HARDWARE', 'DESCRIPTION', 'System', 'CentralProcessor', '0']))
        env['cpu'] = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
    except Exception:
        pass
    if shutil.which('nvidia-smi'):
        out = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'], capture_output=True, text=True)
        env['nvidia_smi'] = out.stdout.strip()
    if shutil.which('ffmpeg'):
        env['ffmpeg'] = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.splitlines()[0]
    write_json(LOGS_DIR / 'environment.json', env)
    print(json.dumps(env, indent=2))


if __name__ == '__main__':
    main()
