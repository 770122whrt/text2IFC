def main():
    import contextlib,datetime as dt,hashlib,io,json,sys,os
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    sys.path[:0]=[str(root),str(root/'src')]
    out=root/'dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909'
    admission=json.loads((out/'admission.json').read_text(encoding='utf-8'))
    assert admission['status']=='admitted'
    for p,h in admission['files_sha256'].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
    from scripts.agent.run_phase6_2_cli import main as cli,load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config
    load_env_file(root/'.env');config=load_openai_compatible_runtime_config(dict(os.environ))
    assert 'api.deepseek.com' in config.base_url and config.model=='deepseek-v4-flash'
    preview={'destination':'https://api.deepseek.com','model':config.model,'generation_strategy':'legacy_full',
      'public_input':(out/'request.txt').read_text(encoding='utf-8'),
      'subsequent_payload_scope':'Only this new request, its public clarification dialogue, generated Brief, candidate JSON, automated feedback and runtime metadata. No source IFC, private Gold, mutation recipe, credentials in content, or old attempts.',
      'execution':'Public CLI with existing bounded task budget; no hand-authored successful outputs.'}
    preview_path=out/'payload-preview.json'
    if preview_path.exists():assert json.loads(preview_path.read_text(encoding='utf-8'))==preview
    else:
        with preview_path.open('x',encoding='utf-8') as f:json.dump(preview,f,ensure_ascii=False,indent=2)
    if '--check-only' in sys.argv:
        print('Current admission and destination verified; no network transport.')
        return
    runtime=out/'runtime';assert not runtime.exists()
    record={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),
      'provider':config.model,'destination':config.base_url,'network_transport_attempted':True,
      'input_note':'Only terminal CR/LF stripped for CLI argument; frozen request bytes unchanged.'}
    def save(): (out/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    with (out/'cli.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        try:
            result=cli(['--live','--stop-after','ifc','--env-file',str(root/'.env'),
              '--output-root',str(runtime),'--prompt',preview['public_input'].rstrip('\r\n')],stdin=io.StringIO(''))
            record.update(status='cli_finished',exit_code=result)
        except Exception as error:
            record.update(status='exception',exception_type=type(error).__name__)
    record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save()
    print(json.dumps(record,ensure_ascii=False))
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
