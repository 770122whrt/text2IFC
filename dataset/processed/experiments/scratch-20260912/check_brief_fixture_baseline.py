import json,sys,types
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root/'src')]
from tests.agent.test_phase6_1_live import _RecordingLiveProvider,_valid_ready_brief
module=types.ModuleType('text2ifc_agent._baseline_pipeline')
module.__file__=str(root/'src/text2ifc_agent/live_pipeline.py')
exec(compile((root/'.tmp/public-brief-baseline.py').read_text(encoding='utf-8-sig'),module.__file__,'exec'),module.__dict__)
case=module.complete_room_case();brief=_valid_ready_brief(case);brief['schema_version']='text2ifc/design-brief/2.1'
out=root/'.tmp/brief-fixture-baseline-output'
result=module.run_design_brief_stage(provider=_RecordingLiveProvider(brief),output_dir=out,case=case)
print(json.dumps({'valid':result['valid'],'validation':json.loads((out/'validation.json').read_text(encoding='utf-8'))},ensure_ascii=False))
