def main():
    import contextlib
    import datetime as dt
    import hashlib
    import io
    import json
    import sys
    import xml.etree.ElementTree as ET
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root), str(root/'src')]
    old = root/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
    out = root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
    retry = '--retry-input' in sys.argv
    runtime = out / ('runtime-02' if retry else 'runtime')
    execution_path = out / ('execution-02.json' if retry else 'execution.json')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    original = json.loads((old/'admission/generation-final/admission.json').read_text(encoding='utf-8'))
    binding = json.loads((old/'generation/corrective-02-general-revalidation/binding-admission.json').read_text(encoding='utf-8'))
    assert original['status'] == binding['status'] == 'admitted'
    for p,h in original['files_sha256'].items():
        assert sha(root/p) == binding['changed_source_sha256'].get(p,h), p
    suite = root/'.tmp/two-storey-natural-input-01.xml'
    assert all(all(int(s.get(k,'0')) == 0 for k in ['failures','errors','skipped']) for s in ET.parse(suite).iter('testsuite'))
    expected = json.loads((out/'frozen-expectations.json').read_text(encoding='utf-8'))
    assert sha(out/'request.txt') == expected['request_sha256']
    assert not runtime.exists()
    def save(path, value):
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save(out/('admission-02.json' if retry else 'admission.json'), {'status':'admitted','scope':'same existing Generation stage, new two-storey development case, unchanged public production sources; current stair/geometry/public and target tests 54 passed',
        'base_admission_sha256':sha(old/'admission/generation-final/admission.json'),
        'scoped_source_admission_sha256':sha(old/'generation/corrective-02-general-revalidation/binding-admission.json'),
        'scoped_tests_sha256':sha(suite), 'request_sha256':sha(out/'request.txt'),
        'expectations_sha256':sha(out/'frozen-expectations.json'),'network_transport_attempted':False})
    if '--check-only' in sys.argv:
        print('Admission valid; no Provider calls.')
        return
    from scripts.agent.run_phase6_2_cli import main as cli
    record = {'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),
              'network_transport_attempted':True, 'provider':'DeepSeek api.deepseek.com',
              'scope':'new synthetic two-storey user request through public CLI, no Repair IFC/private Gold input'}
    record['input_normalization'] = 'Remove file-terminal CR/LF characters only; frozen request.txt unchanged.'
    save(execution_path,record)
    with (out/('cli-02.log' if retry else 'cli.log')).open('x',encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            result = cli(['--live','--stop-after','ifc','--env-file',str(root/'.env'),
                          '--output-root',str(runtime),'--prompt',(out/'request.txt').read_text(encoding='utf-8').rstrip('\r\n')],
                         stdin=io.StringIO(''))
            record.update(status='cli_finished',exit_code=result)
        except Exception as error:
            record.update(status='exception',exception_type=type(error).__name__)
    record['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    save(execution_path,record)
    print(json.dumps(record,ensure_ascii=False))

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
