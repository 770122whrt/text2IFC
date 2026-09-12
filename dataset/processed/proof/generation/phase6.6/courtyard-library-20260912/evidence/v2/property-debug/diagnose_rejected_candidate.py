"""Offline diagnostic only: rejected Provider candidate, never accepted output."""
from pathlib import Path
import dataclasses, hashlib, json, importlib.util
from text2ifc_compiler import compile_document

OUT = Path(__file__).resolve().parent
CASE = OUT.parent/'rerun-01'
SOURCE = CASE/'live-run/runs/d2c21f51c9bb69f6/repair/repaired-candidate.json'

def main():
    assert not (OUT/'diagnostic-rejected-candidate.ifc').exists()
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result = compile_document(json.loads(SOURCE.read_text(encoding='utf-8')), OUT/'diagnostic-rejected-candidate.ifc')
    record = {'role': 'Offline diagnosis of rejected candidate; not a successful live loop, no Audit, not a deliverable',
        'source_sha256': before, 'compile_success': result.success, 'compile_result': dataclasses.asdict(result)}
    if result.success:
        spec = importlib.util.spec_from_file_location('independent_diagnostic',CASE/'check_ifc.py')
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        checked = module.run(result.output_path)
        record['independent'] = checked
    assert before == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with (OUT/'rejected-candidate-diagnostic.json').open('x',encoding='utf-8') as f:
        json.dump(record,f,ensure_ascii=False,indent=2,default=lambda x:dataclasses.asdict(x));f.write('\n')
    print(json.dumps({'compile_success':result.success,'independent_passed':record.get('independent',{}).get('passed'),
        'failures':[c for c in record.get('independent',{}).get('checks',[]) if not c['passed']]},ensure_ascii=False))

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
