"""Exercise orchestration with real child processes and local fake servers, without AI calls."""
import argparse
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bench

STUB = '''import json,os,socket,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
def event(name):
    with (root/'events.jsonl').open('a') as f:
        f.write(json.dumps({'event':name,'time':time.monotonic()})+'\\n')
args=sys.argv[1:]
if args[0]=='serve':
    sockets=[]
    for key in ['DEMO_TEST_PORT1','DEMO_TEST_PORT2']:
        s=socket.socket();s.bind(('127.0.0.1',int(os.environ[key])));s.listen();sockets.append(s)
    (root/'server.pid').write_text(str(os.getpid()))
    print('Fixture and WebGames ready',flush=True)
    while True:time.sleep(1)
elif args[0]=='run':
    suite='v2' if 'schedule-v2.json' in args else 'v1'
    event('start-'+suite)
    time.sleep(0.25)
    event('end-'+suite)
    if suite=='v1' and os.environ.get('DEMO_TEST_BUDGET_STOP'):sys.exit(2)
else:event(args[0])
'''


class DemoCommandTest(unittest.TestCase):
    def execute_demo(self, parallel, budget_stop=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bench.py').write_text(STUB)
            for name in ('score.py', 'score_v2.py'):
                (root / name).write_text("from pathlib import Path\nprint('report generated')\n")
            (root / 'tools/node_modules/@playwright/test').mkdir(parents=True)
            (root / 'webgames/dist').mkdir(parents=True)
            (root / 'webgames/dist/index.html').touch()
            held = [socket.socket(), socket.socket()]
            for s in held:
                s.bind(('127.0.0.1', 0))
            ports = [s.getsockname()[1] for s in held]
            for s in held:
                s.close()
            env = {'DEMO_TEST_PORT1': str(ports[0]), 'DEMO_TEST_PORT2': str(ports[1])}
            if budget_stop:
                env['DEMO_TEST_BUDGET_STOP'] = '1'
            with patch.object(bench, 'ROOT', root), patch.object(bench, 'RESULTS', root / 'results'), \
                 patch.object(bench, 'FIX_PORT', ports[0]), patch.object(bench, 'WG_PORT', ports[1]), \
                 patch.object(bench.shutil, 'which', return_value=sys.executable), patch.dict(os.environ, env):
                code = bench.cmd_demo(argparse.Namespace(parallel=parallel, budget_usd=15.0))
            pid = int((root / 'server.pid').read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
            return code, events

    def test_parallel_starts_both_suites_and_stops_owned_server(self):
        code, events = self.execute_demo(parallel=True)
        self.assertEqual(code, 0)
        times = {x['event']: x['time'] for x in events}
        self.assertLess(max(times['start-v1'], times['start-v2']), min(times['end-v1'], times['end-v2']))

    def test_sequential_budget_stop_does_not_start_v2(self):
        code, events = self.execute_demo(parallel=False, budget_stop=True)
        self.assertEqual(code, 2)
        self.assertNotIn('start-v2', [x['event'] for x in events])

    def test_parallel_budget_stop_preserves_budget_exit_code(self):
        code, _ = self.execute_demo(parallel=True, budget_stop=True)
        self.assertEqual(code, 2)

    def test_busy_port_is_rejected_without_touching_its_listener(self):
        with tempfile.TemporaryDirectory() as tmp, socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
            listener.listen()
            with patch.object(bench, 'ROOT', Path(tmp)), patch.object(bench, 'FIX_PORT', port), \
                 patch.object(bench.shutil, 'which', return_value=sys.executable):
                with self.assertRaisesRegex(SystemExit, 'already in use'):
                    bench.cmd_demo(argparse.Namespace(parallel=True, budget_usd=15.0))
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                pass


if __name__ == '__main__':
    unittest.main()
