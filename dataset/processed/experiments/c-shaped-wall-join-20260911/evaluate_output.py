"""Post-run evaluation only. Frozen evaluator data never enters Provider input."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911'
def main():
    execution=json.loads((OUT/'live-run/execution.json').read_text(encoding='utf-8'))
    assert execution['status']!='running'
    run=Path(execution['run_dir']);source=run/'output.ifc'
    assert source.is_file(),'No IFC available for evaluation'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('frozen_c_check',SOURCE/'check_ifc.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.check_ifc(source)
    result['production_status']=execution['status']
    result['human_review_status']='pending' if result['status']=='passed' and execution['status']=='compiled' else 'not_ready'
    with (OUT/'independent-ifc-check.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    subprocess.run([sys.executable,str(OUT.parent/'c-shaped-teaching-building-20260910/export_views.py'),str(source),str(OUT/'views')],check=True)
    print(json.dumps({k:result[k] for k in ['production_status','status','check_count','failed','human_review_status']}))
if __name__=='__main__':main()
