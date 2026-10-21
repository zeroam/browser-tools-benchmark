"""A shared quick-start must not turn an incomplete run into a tool verdict."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReportTest(unittest.TestCase):
    def test_partial_quality_runs_do_not_decide_tool_choice(self):
        for script, kind, prefix, summary in [
            ('score.py', 'f3', '', 'summary.json'),
            ('score_v2.py', 'h1', 'v2-', 'summary-v2.json'),
        ]:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for name in ('score.py', 'score_v2.py'):
                    shutil.copy2(ROOT / name, root / name)
                (root / 'results').mkdir()
                for arm in ('pwcli', 'agentbrowser'):
                    rid = prefix + 'sample-' + arm
                    run = root / 'runs' / rid
                    run.mkdir(parents=True)
                    metric = {'tokens': {'fixed_overhead': 10, 'max_context': 100,
                                         'tool_output_est_tokens': 10},
                              'tool_calls': 1, 'num_turns': 1, 'tool_errors': 0, 'retries': 0,
                              'duration_api_ms': 100, 'duration_ms': 1000}
                    data = {'item': {'id': rid, 'arm': arm, 'mode': 'headless',
                                     'kind': kind, 'task': kind, 'rep': 0},
                            'judge': {'success': True, 'false_success': False},
                            'tokens_total': 100, 'cost_usd': 0.01, 'wall_s': 1,
                            'stable': True, 'flags': [], 'fail_type': None,
                            'metrics': [metric], 'finish': [],
                            'exec': [{'leftover_browser_procs': 0, 'max_browser_mb': 10}]}
                    (run / 'meta.json').write_text(json.dumps(data))
                result = subprocess.run([sys.executable, str(root / script)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                decision = json.loads((root / 'results' / summary).read_text())['decision']
                self.assertIn('판정 보류', decision['verdict'])
                self.assertFalse(decision.get('switch_candidates'))
                self.assertIsNone(decision.get('keep'))


if __name__ == '__main__':
    unittest.main()
