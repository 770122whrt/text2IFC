"""Authorized same-task continuation with frozen Brief and accumulated budget."""
import contextlib, datetime as dt, hashlib, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
BASE=ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909'
def main():
    import os
    from scripts.agent.run_phase6_2_cli import load_env_file, _default_openai_live_provider_factory
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    admission=json.loads((BASE/'admission/roof-admission.json').read_text(encoding='utf-8'))
    assert admission['status']=='admitted'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for p,h in admission['files_sha256'].items():
        assert sha(ROOT/p)==h,f'Stale admission: {p}'
    old=BASE/'runtime/runs/148bdf3872e74ccd'
    out=BASE/'geometry-continuation';out.mkdir(exist_ok=False)
    load_env_file(ROOT/'.env')
    record={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'previous_run':old.relative_to(ROOT).as_posix(),'request_sha256':sha(BASE/'request.txt'),
        'admission_sha256':sha(BASE/'admission/roof-admission.json'),
        'claim':'same disclosed development case; original live Brief reused byte-for-byte, fresh live Generator/Audit; budget retained',
        'network_transport_attempted':True}
    def save(): (out/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    with (out/'cli.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        store=SessionStore.open(out/'sessions.sqlite',artifact_root=out)
        try:
            session=store.create_session(original_input=(BASE/'request.txt').read_text(encoding='utf-8').rstrip('\r\n'))
            for name in ['design-brief','calls']:
                shutil.copytree(old/name,session.run_dir/name)
            for name in ['design-brief.json','generation-budget.json']:
                shutil.copyfile(old/name,session.run_dir/name)
            store.mark_session_status(session.session_id,'ready')
            record['session_hash']=session.session_hash;record['run_dir']=session.run_dir.relative_to(ROOT).as_posix();save()
            factory=_default_openai_live_provider_factory(openai_client_factory=None)
            result=run_ready_session_to_ifc(store=store,session=session.session_id,provider_factory=factory)
            record.update(status=result.status,ifc_path=str(result.ifc_path) if result.ifc_path else None,report_path=str(result.report_path) if result.report_path else None)
        except Exception as exc:
            import traceback
            traceback.print_exc();record.update(status='exception',exception_type=type(exc).__name__)
        finally:store.close()
    record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save();print(json.dumps(record,ensure_ascii=False))
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
