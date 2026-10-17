"""Run the Linux memory family without importing host pytest in the image."""
import ast
import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.skipif(os.environ.get('REPAIR_LATER_TEN_DOCKER')!='1',reason='explicit Linux RSS check')
def test_linux_exec_accounting(tmp_path):
    from scripts.ifc_repair.repair_comparison.isolated_b import build_runtime_bundle
    repo=Path(__file__).resolve().parents[3];bundle=tmp_path/'bundle'
    build_runtime_bundle(repo,bundle)
    family=repo/'tests/ifc_repair/test_validation_worker_rss.py'
    tree=ast.parse(family.read_text(encoding='utf8'))
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef)
                  and node.name=='test_exec_worker_excludes_parent_memory_but_retains_own_peak')
    function.decorator_list=[]
    code='import json, subprocess, sys\n'+ast.unparse(function)+'\n'+function.name+'()\nprint("Linux RSS family passed")'
    result=subprocess.run(['docker','run','--rm','--network=none','--read-only','--memory=8g','--cpus=4',
        '--pids-limit=256','--cap-drop=ALL','--security-opt=no-new-privileges',
        '--env=PYTHONPATH=/runtime/src','--env=PYTHONDONTWRITEBYTECODE=1',
        '--mount',f'type=bind,source={bundle},target=/runtime,readonly',
        'text2ifc/repair-tools:py312-ifc085-property-v1','python','-c',code],
        capture_output=True,text=True,encoding='utf8',timeout=90)
    (tmp_path/'rss-native.log').write_text(result.stdout+result.stderr,encoding='utf8')
    assert result.returncode==0,result.stdout+result.stderr
