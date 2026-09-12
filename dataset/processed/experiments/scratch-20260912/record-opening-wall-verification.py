from pathlib import Path
import json, hashlib, shutil, subprocess
from xml.etree import ElementTree as ET

out=Path('dataset/processed/ifc-presentation-validation/pipeline-opening-binding-20260909')
tests=[]
for name in ['opening-binding-red','opening-binding-green','opening-binding-boundary-red',
             'opening-binding-regression','wall-contract-red','wall-contract-green','wall-contract-final']:
    src=Path('.tmp')/(name+'.xml'); dest=out/src.name
    assert not dest.exists()
    shutil.copyfile(src,dest)
    suites=ET.parse(src).getroot().findall('testsuite')
    tests.append({'file':dest.name,**{key:sum(int(s.get(key,0)) for s in suites)
                  for key in ['tests','failures','errors','skipped']}})
files=['src/text2ifc_quality/floor_openings.py','src/text2ifc_quality/generated_ifc.py',
       'src/text2ifc_agent/semantic_coverage.py','src/text2ifc_agent/live_pipeline.py',
       'src/text2ifc_agent/interactive_cli_flow.py','src/text2ifc_agent/changeset_stage.py',
       'prompts/agent/design-brief-v2.3.md','prompts/agent/bim-json-changeset-v1.5.md',
       'prompts/agent/registry.json','tests/ifc_quality/test_floor_opening_identity.py',
       'tests/agent/test_explicit_wall_fact_contract.py','tests/agent/test_interactive_cli_flow.py']
old_prompts=['prompts/agent/design-brief-v2.2.md','prompts/agent/bim-json-changeset-v1.4.md']
for file in old_prompts:
    old=subprocess.check_output(['git','show',f'HEAD:{file}'])
    assert old.replace(b'\r\n',b'\n')==Path(file).read_bytes().replace(b'\r\n',b'\n')
record={'evidence_mode':'scoped offline tests and disclosed-case deterministic replay',
        'new_ifc_provider_calls':0,'full_preflight_run':False,'live_admission':'requires scoped update',
        'test_rounds':tests,'old_prompt_contents_unchanged':old_prompts,
        'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files},
        'limits':['Not a capability or live success-rate comparison',
                  'Original IFC, Audit and accepted human view unchanged',
                  'Two missing wall expectations in the original case remain blocking',
                  'R1 extraction completeness, shared opening identity, other Draft addressing and interruption reconciliation remain partial or pending']}
(out/'verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile('.tmp/replay-opening-binding.py',out/'replay-opening-binding.py')
print(json.dumps(tests))
