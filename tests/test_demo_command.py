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

STUB = '''import json,os,socket,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
def event(name):
    with (root/'events.jsonl').open('a') as f:
        f.write(json.dumps({'event':name,'time':time.monotonic(),'session':os.environ.get('BENCH_DEMO_SESSION')})+'\\n')
args=sys.argv[1:]
if args[0]=='serve':
    sockets=[]
    for key in ['DEMO_TEST_PORT1','DEMO_TEST_PORT2']:
        s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',int(os.environ[key])));s.listen();sockets.append(s)
    (root/'server.pid').write_text(str(os.getpid()))
    print('Fixture and WebGames ready',flush=True)
    while True:time.sleep(1)
elif args[0]=='run':
    suite='v2' if 'schedule-v2.json' in args else 'v1'
    event('start-'+suite)
    if suite=='v2' and os.environ.get('DEMO_TEST_ISOLATED_AGENT'):
        agent=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (root/'agent.pid').write_text(str(agent.pid))
        time.sleep(60)
    time.sleep(0.25)
    event('end-'+suite)
    if suite=='v1' and os.environ.get('DEMO_TEST_BUDGET_STOP'):sys.exit(2)
else:event(args[0])
'''


class DemoCommandTest(unittest.TestCase):
    def execute_demo(self, parallel, budget_stop=False, fresh_sessions=False, recently_used_port=False,
                     isolated_agent=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bench.py').write_text(STUB)
            for name in ('score.py', 'score_v2.py'):
                (root / name).write_text("from pathlib import Path\nprint('report generated')\n")
            (root / 'tools/node_modules/@playwright/test').mkdir(parents=True)
            (root / 'webgames/dist').mkdir(parents=True)
            (root / 'webgames/dist/index.html').touch()
            bindir = root / 'bin'
            bindir.mkdir()
            cli = bindir / 'playwright-cli'
            cli.write_text('#!' + sys.executable + '\nimport sys\nprint("browser command accepted")\n')
            cli.chmod(0o755)
            held = [socket.socket(), socket.socket()]
            for s in held:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', 0))
            ports = [s.getsockname()[1] for s in held]
            if recently_used_port:
                held[0].listen()
                client = socket.create_connection(('127.0.0.1', ports[0]))
                accepted, _ = held[0].accept()
                accepted.close()
                client.close()
            for s in held:
                s.close()
            env = {'DEMO_TEST_PORT1': str(ports[0]), 'DEMO_TEST_PORT2': str(ports[1]),
                   'PATH': str(bindir) + os.pathsep + os.environ.get('PATH', '')}
            if budget_stop:
                env['DEMO_TEST_BUDGET_STOP'] = '1'
            if isolated_agent:
                env['DEMO_TEST_ISOLATED_AGENT'] = '1'
            with patch.object(bench, 'ROOT', root), patch.object(bench, 'RESULTS', root / 'results'), \
                 patch.object(bench, 'WORK', root / 'work'), \
                 patch.object(bench, 'FIX_PORT', ports[0]), patch.object(bench, 'WG_PORT', ports[1]), \
                 patch.object(bench.shutil, 'which', return_value=sys.executable), patch.dict(os.environ, env):
                code = bench.cmd_demo(argparse.Namespace(parallel=parallel, budget_usd=15.0,
                                                         fresh_sessions=fresh_sessions))
            pid = int((root / 'server.pid').read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            if isolated_agent:
                agent_pid = int((root / 'agent.pid').read_text())
                try:
                    import subprocess
                    import time
                    deadline = time.monotonic() + 2
                    while True:
                        status = subprocess.run(['ps', '-p', str(agent_pid), '-o', 'stat='],
                                                capture_output=True, text=True)
                        running = status.returncode == 0 and 'Z' not in status.stdout
                        if not running or time.monotonic() >= deadline:
                            break
                        time.sleep(0.05)
                    self.assertFalse(running, 'Demo cancellation left an isolated agent running')
                finally:
                    try:
                        import signal
                        os.kill(agent_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
            return code, events

    def test_parallel_starts_both_suites_and_stops_owned_server(self):
        code, events = self.execute_demo(parallel=True)
        self.assertEqual(code, 0)
        times = {x['event']: x['time'] for x in events}
        self.assertLess(max(times['start-v1'], times['start-v2']), min(times['end-v1'], times['end-v2']))
        starts = {x['event']: x['session'] for x in events if x['event'].startswith('start-')}
        self.assertTrue(starts['start-v1'].startswith('v1-demo-'))
        self.assertTrue(starts['start-v2'].startswith('v2-demo-'))
        self.assertNotEqual(starts['start-v1'], starts['start-v2'])
        for start in starts:
            end = next(x for x in events if x['event'] == start.replace('start-', 'end-'))
            self.assertEqual(end['session'], starts[start])

    def test_fresh_mode_does_not_reuse_a_demo_session(self):
        code, events = self.execute_demo(parallel=True, fresh_sessions=True)
        self.assertEqual(code, 0)
        self.assertTrue(all(x['session'] is None for x in events))

    def test_recently_closed_connection_does_not_block_restart(self):
        code, _ = self.execute_demo(parallel=True, recently_used_port=True)
        self.assertEqual(code, 0)

    def test_sequential_budget_stop_does_not_start_v2(self):
        code, events = self.execute_demo(parallel=False, budget_stop=True)
        self.assertEqual(code, 2)
        self.assertNotIn('start-v2', [x['event'] for x in events])

    def test_parallel_budget_stop_preserves_budget_exit_code(self):
        code, _ = self.execute_demo(parallel=True, budget_stop=True)
        self.assertEqual(code, 2)

    def test_budget_stop_also_stops_agents_in_a_separate_process_group(self):
        code, _ = self.execute_demo(parallel=True, budget_stop=True, isolated_agent=True)
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
