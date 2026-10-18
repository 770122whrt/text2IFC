"""Validator memory must describe this executable, not its warmed launcher."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from text2ifc_ifc_repair import validation_worker
from text2ifc_ifc_repair.evaluation import EvaluationExecutionPolicy, execute_validation_and_diff


def test_linux_worker_uses_its_own_high_water_mark(monkeypatch):
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.as_posix() == '/proc/self/status':
            return 'Name:\tpython\nVmHWM:\t128000 kB\nVmRSS:\t64000 kB\n'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(Path, 'read_text', read)
    assert validation_worker._peak_rss_bytes() == 128000 * 1024


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux exec memory inheritance')
def test_exec_worker_excludes_parent_memory_but_retains_own_peak():
    child = '''
import gc, json
from text2ifc_ifc_repair.validation_worker import _peak_rss_bytes
before = _peak_rss_bytes()
allocation = bytearray(128 * 1024**2)
during = _peak_rss_bytes()
del allocation
gc.collect()
print(json.dumps([before, during, _peak_rss_bytes()]))
'''
    parent = '''
import json, resource, subprocess, sys
allocation = bytearray(512 * 1024**2)
parent_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
result = subprocess.run([sys.executable, '-c', sys.argv[1]], check=True,
                        capture_output=True, text=True)
print(json.dumps({'parent': parent_peak, 'worker': json.loads(result.stdout)}))
'''
    result = subprocess.run([sys.executable, '-c', parent, child], check=True,
                            capture_output=True, text=True, timeout=60)
    evidence = json.loads(result.stdout)
    before, during, after = evidence['worker']
    assert before < evidence['parent'] * .6, evidence
    assert during >= before + 100 * 1024**2, evidence
    assert after >= during, evidence


@pytest.mark.parametrize('parent_rss,expected', [(0, 'passed'), (4 * 1024**3 + 1, 'failed')])
def test_reused_validation_keeps_real_rss_limit(tmp_path, parent_rss, expected):
    import ifcopenshell

    models = [ifcopenshell.file(schema='IFC2X3') for _ in range(2)]
    paths = [tmp_path / name for name in ('baseline.ifc', 'candidate.ifc')]
    for model, path in zip(models, paths):
        model.create_entity('IfcCartesianPoint', Coordinates=(0., 0., 0.))
        model.write(str(path))
    result = execute_validation_and_diff(
        damaged_ifc_path=paths[0], repaired_ifc_path=paths[1], cache_dir=tmp_path/'cache',
        policy=EvaluationExecutionPolicy(deadline_seconds=60),
        baseline_model=models[0], candidate_model=models[1], rss_reader=lambda: parent_rss)
    assert result['status'] == expected
    if expected == 'failed':
        assert result['reason_code'] == 'EVALUATION_RSS_LIMIT_EXCEEDED'
        assert result['results'] == {}
