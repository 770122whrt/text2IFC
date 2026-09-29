import json
from pathlib import Path
import subprocess
import sys
import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize('arm,case_id', [('A', 'case-001'), ('C', 'case-002')])
def test_public_cli_question_restart_submit_and_independent_score(tmp_path, arm, case_id):
    script = REPO / 'scripts/ifc_repair/repair_comparison/experiment.py'
    assert script.exists(), 'Offline CLI missing'
    root = tmp_path / 'run'
    case = REPO / 'dataset/processed/ifc-repair/repair-comparison/development' / case_id
    budget = tmp_path / 'budget.json'
    budget.write_text(json.dumps({'tokens': 1000, 'calls': 5, 'active_seconds': 600, 'tool_seconds': 5, 'extensions': []}), encoding='utf-8')
    transcript = tmp_path / 'replay.json'
    transcript.write_text(json.dumps([
        {'tool_calls': [{'name': 'ask_user', 'arguments': {'question': '离线问答机制演练？'}}], 'usage': {'input_tokens': 2, 'output_tokens': 3}},
        {'tool_calls': [{'name': 'submit', 'arguments': {'path': 'model.ifc'}}], 'usage': {'input_tokens': 2, 'output_tokens': 3}}
    ]), encoding='utf-8')
    def cli(*args):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(script), '--root', str(root), *map(str, args)], cwd=REPO, capture_output=True, text=True, encoding='utf-8', timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)
    created = cli('create', '--public', case / 'public', '--case-id', case_id, '--arm', arm, '--budget', budget)
    run_id = created['run_id']
    first = cli('run', run_id, '--replay', transcript, '--reservation', 100)
    assert first['status'] == 'awaiting_user'
    cli('answer', run_id, '--question-id', first['question']['question_id'], '--text', '继续演练。', '--event-id', 'human-1')
    final = cli('run', run_id, '--replay', transcript, '--reservation', 100)
    assert final['status'] == 'submitted' and final['usage']['total_tokens'] == 10
    scored = cli('score', run_id, '--case', case)
    assert scored['repair_success'] is False  # deliberately submitted unchanged D
    assert scored['products']['required'] == 1
    assert Path(final['artifact']['path']).read_bytes() == (case / 'public/model.ifc').read_bytes()
