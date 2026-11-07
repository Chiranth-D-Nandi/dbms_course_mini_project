"""Start both local services, choosing free ports and cleaning up owned child processes."""
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def free_port(start):
    for port in range(start, start + 30):
        with socket.socket() as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f'No free local port near {start}.')


def stop(process):
    if process is None or process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.killpg(process.pid, signal.SIGTERM)
    process.wait(timeout=10)


def main():
    load_dotenv(ROOT / '.env')
    frontend_port = free_port(int(os.getenv('FRONTEND_PORT', '3000')))
    backend_port = free_port(int(os.getenv('BACKEND_PORT', '8000')))
    print(f'Frontend: http://localhost:{frontend_port}', flush=True)
    print(f'Backend:  http://127.0.0.1:{backend_port}/api/', flush=True)
    if '--check' in sys.argv:
        return
    node = shutil.which('node')
    next_bin = ROOT / 'frontend' / 'node_modules' / 'next' / 'dist' / 'bin' / 'next'
    if not node or not next_bin.exists():
        raise SystemExit('Install Node and run the setup script first.')
    env = os.environ.copy()
    env['NEXT_PUBLIC_API_URL'] = f'http://127.0.0.1:{backend_port}/api'
    env['CORS_ALLOWED_ORIGINS'] = f'http://localhost:{frontend_port},http://127.0.0.1:{frontend_port}'
    env.pop('NEXT_BUILD_DIR', None)
    runtime = ROOT / '.runtime'
    runtime.mkdir(exist_ok=True)
    backend = frontend = None
    try:
        with (runtime / 'backend.log').open('w', encoding='utf-8') as log:
            backend = subprocess.Popen([sys.executable, str(ROOT / 'backend' / 'manage.py'), 'runserver', f'127.0.0.1:{backend_port}', '--noreload'],
                cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, start_new_session=os.name != 'nt')
            frontend = subprocess.Popen([node, str(next_bin), 'dev', '-p', str(frontend_port)], cwd=ROOT / 'frontend', env=env, start_new_session=os.name != 'nt')
            print('Press Ctrl+C to stop both services. Backend log: .runtime/backend.log', flush=True)
            while frontend.poll() is None:
                if backend.poll() is not None:
                    raise RuntimeError('Backend stopped. See .runtime/backend.log.')
                time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop(frontend)
        stop(backend)


if __name__ == '__main__':
    main()
