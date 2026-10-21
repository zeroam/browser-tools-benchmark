#!/usr/bin/env python3
"""Run the original dummy dashboard and prove the example test catches defects."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
MODES = ('normal', 'slow', 'bug-value', 'bug-side', 'bug-extra', 'bug-missing', 'bug-nav', 'bug-404')


def fixture(token):
    os.environ['FIXTURE_ADMIN_TOKEN'] = token
    spec = importlib.util.spec_from_file_location('demo_fixture', ROOT / 'fixtures/server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.NS['demo'] = {'kind': 'f4', 'config': {'mode': 'normal', 'target': 'b1'},
                         'sessions': {}, 'log': []}
    return module


def set_mode(port, token, mode):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/__admin/ns/demo/mode',
        data=json.dumps({'mode': mode}).encode(),
        headers={'X-Admin-Token': token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def verify():
    fx = fixture(secrets.token_hex(16))
    server = ThreadingHTTPServer(('127.0.0.1', 0), fx.H)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    out = ROOT / '.demo'
    out.mkdir(exist_ok=True)
    records = []
    try:
        for mode in MODES:
            set_mode(server.server_port, fx.ADMIN_TOKEN, mode)
            env = {**os.environ, 'DEMO_URL': f'http://demo.localhost:{server.server_port}',
                   'PLAYWRIGHT_HTML_OPEN': 'never'}
            result = subprocess.run(['node', str(ROOT / 'tools/node_modules/@playwright/test/cli.js'),
                'test', 'demo/positions.spec.ts', '--config', str(ROOT / 'tools/playwright.config.ts'), '--reporter=json'],
                env=env, cwd=ROOT, capture_output=True, text=True, timeout=90)
            (out / f'{mode}.json').write_text(result.stdout)
            (out / f'{mode}.stderr.txt').write_text(result.stderr)
            report = json.loads(result.stdout)
            tests = [t for suite in report.get('suites', []) for spec in suite.get('specs', [])
                     for t in spec.get('tests', [])]
            # A missing browser/server/import failure is never a successfully caught defect.
            errors = '\n'.join(e.get('message', '') for t in tests
                               for r in t.get('results', []) for e in r.get('errors', []))
            normal = mode in ('normal', 'slow')
            passed = len(tests) == 1 and tests[0]['status'] == 'expected' and result.returncode == 0
            caught = (len(tests) == 1 and tests[0]['status'] == 'unexpected'
                      and result.returncode == 1 and ('POSITION_ROWS' in errors or 'BOT_DETAIL' in errors))
            ok = passed if normal else caught
            records.append({'mode': mode, 'expected': 'pass' if normal else 'assertion failure', 'ok': ok})
            print(f'{"PASS" if ok else "FAIL"} {mode}: {"normal passes" if normal else "defect detected"}', flush=True)
        (out / 'summary.json').write_text(json.dumps(records, indent=2) + '\n')
        return 0 if all(r['ok'] for r in records) else 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    serve = sub.add_parser('serve')
    serve.add_argument('--port', type=int, default=5420)
    mode = sub.add_parser('mode')
    mode.add_argument('value', choices=MODES)
    mode.add_argument('--port', type=int, default=5420)
    sub.add_parser('verify')
    args = ap.parse_args()
    if args.command == 'verify':
        return verify()
    token_file = ROOT / '.demo-token'
    if args.command == 'mode':
        set_mode(args.port, token_file.read_text().strip(), args.value)
        print(args.value)
        return 0
    token = secrets.token_hex(16)
    fx = fixture(token)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), fx.H)
    token_file.touch(mode=0o600, exist_ok=True)
    token_file.chmod(0o600)
    token_file.write_text(token)
    print(f'Dummy dashboard: http://demo.localhost:{args.port}/ (Ctrl-C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
