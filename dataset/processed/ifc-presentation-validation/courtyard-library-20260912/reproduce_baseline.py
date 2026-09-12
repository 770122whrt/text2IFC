"""Run the corrected frozen test family on pre-fix modules without editing a checkout."""
import importlib
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT))
BASE='d2a62b76'
for name in ['text2ifc_agent.semantic_requirements','text2ifc_agent.cross_storey_identity',
    'text2ifc_agent.semantic_coverage','text2ifc_agent.generation_packages',
    'text2ifc_quality.floor_openings','text2ifc_agent.brief_semantic_repair',
    'text2ifc_agent.issue_normalizers']:
    module=importlib.import_module(name)
    path='src/'+name.replace('.','/')+'.py'
    content=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode('utf8')
    exec(compile(content,str(ROOT/path),'exec'),module.__dict__)
import pytest
raise SystemExit(pytest.main(['tests/agent/test_brief_semantic_roles.py','tests/agent/test_roof_opening_projection.py',
    '-q','-p','no:cacheprovider','--basetemp=.tmp/courtyard-baseline-corrected',
    '--junitxml='+str(OUT/'baseline-corrected.xml')]))
