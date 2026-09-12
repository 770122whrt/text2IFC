def main():
    import contextlib
    import datetime as dt
    import hashlib
    import json
    import os
    import sys
    from pathlib import Path
    ROOT=Path(__file__).resolve().parents[1]
    sys.path[:0]=[str(ROOT),str(ROOT/'src')]
    BASE=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
    OUT=BASE/'repair'
    admission_path=BASE/'admission/repair-property-final/admission.json'
    admission=json.loads(admission_path.read_text(encoding='utf-8'))
    assert admission['status']=='admitted'
    for path,h in admission['files_sha256'].items(): assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
    mode = 'offline-03' if '--offline' in sys.argv else 'live-04'
    assert not (OUT/('runtime-'+mode)).exists()
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_ifc_repair.api import RepairAPI
    if '--offline' not in sys.argv: load_env_file(ROOT/'.env')
    source=OUT/'02-damaged.ifc'
    request=(OUT/'request.txt').read_text(encoding='utf-8')
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    record={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'network_transport_attempted':'--offline' not in sys.argv,'provider':'DeepSeek configured environment','admission_sha256':hashlib.sha256(admission_path.read_bytes()).hexdigest(),'public_source_sha256':before,'request_sha256':hashlib.sha256(request.encode()).hexdigest(),'private_original_input':False,'mutation_input':False}
    def save(): (OUT/('execution-'+mode+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    with (OUT/('api-'+mode+'.log')).open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
     try:
      if '--offline' in sys.argv:
       from tests.ifc_repair.test_relation_damage_public_path import PropertyProvider
       api=RepairAPI(OUT/('runtime-'+mode), provider=PropertyProvider(OUT/('runtime-'+mode),request))
      else:
       api=RepairAPI.from_environment(OUT/('runtime-'+mode))
      result=api.start(source,request,run_id='repair-vvo-property-relation-'+mode)
      (OUT/('result-'+mode+'.json')).write_text(json.dumps(result.to_dict(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
      record.update(status=result.status,reason_code=result.reason_code,run_id=result.run_id)
     except Exception as e: record.update(status='exception',exception_type=type(e).__name__,reason_code=str(getattr(e,'code','')))
    record['source_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==before
    record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save();print(json.dumps(record,ensure_ascii=False))

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
