def main():
    import datetime as dt
    import hashlib
    import json
    import os
    import shutil
    import sys
    import xml.etree.ElementTree as ET
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root), str(root / 'src')]
    base = root / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
    source = base / 'generation/corrective-attempt-02'
    output = base / 'generation/corrective-02-general-revalidation'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    def write(p, value):
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    from text2ifc_agent.live_pipeline import run_candidate_gate_stage, run_repair_stage, run_audit_report_stage, run_final_acceptance_stage
    if '--offline' in sys.argv:
        tests = base / 'admission/semantic-binding-green.xml'
        assert all(all(int(s.get(k, '0')) == 0 for k in ['failures', 'errors', 'skipped'])
                   for s in ET.parse(tests).iter('testsuite'))
        relation_tests = base / 'admission/relation-names-green.xml'
        assert all(all(int(s.get(k, '0')) == 0 for k in ['failures', 'errors', 'skipped'])
                   for s in ET.parse(relation_tests).iter('testsuite'))
        geometry_tests = base / 'admission/geometry-identity-green-02.xml'
        assert all(all(int(s.get(k, '0')) == 0 for k in ['failures', 'errors', 'skipped'])
                   for s in ET.parse(geometry_tests).iter('testsuite'))
        general_tests = base / 'admission/general-boundaries-green-03.xml'
        public_tests = base / 'admission/general-public-final.xml'
        for suite in [general_tests, public_tests]:
            assert all(all(int(s.get(k, '0')) == 0 for k in ['failures', 'errors', 'skipped'])
                       for s in ET.parse(suite).iter('testsuite'))
        original = json.loads((base / 'admission/generation-final/admission.json').read_text(encoding='utf-8'))
        resume = json.loads((base / 'generation/resume-admission.json').read_text(encoding='utf-8'))
        changed = ['src/text2ifc_agent/live_pipeline.py', 'src/text2ifc_agent/semantic_requirements.py', 'src/text2ifc_compiler/relationships.py', 'src/text2ifc_agent/dynamic_gates.py', 'src/text2ifc_agent/interactive_cli_flow.py']
        hashes = {**resume['changed_source_sha256'], **{p: sha(root / p) for p in changed}}
        for p, h in original['files_sha256'].items():
            assert sha(root / p) == hashes.get(p, h), p
        output.mkdir(exist_ok=False)
        for name in ['design-brief', 'generator']:
            shutil.copytree(source / name, output / name)
        for name in ['design-brief.json', 'expected-facts.json']:
            shutil.copyfile(source / name, output / name)
        gates = run_candidate_gate_stage(case_dir=output, output_dir=output, case_id='corrective-02-binding-revalidation')
        def forbidden():
            raise AssertionError('Offline routing must not call Provider')
        route = run_repair_stage(provider_factory=forbidden, output_dir=output / 'repair',
                                 generator_source_dir=output / 'generator', case_id='corrective-02-binding-revalidation') if gates['valid'] else None
        record = {'status': 'admitted' if gates['valid'] and route['valid'] else 'blocked',
                  'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'scope': 'same Generation stage; identity binding, wall subtype counting, host/geometry aliases, relationship Name handling; 39 + 77 + 84 scoped tests (overlapping) and exact real candidate offline compile/reopen, geometry and no-call routing',
                  'base_admission_sha256': sha(base / 'admission/generation-final/admission.json'),
                  'resume_admission_sha256': sha(base / 'generation/resume-admission.json'),
                  'changed_source_sha256': hashes, 'revalidation_sha256': sha(tests),
                  'relationship_revalidation_sha256': sha(relation_tests),
                  'geometry_revalidation_sha256': sha(geometry_tests),
                  'general_boundaries_sha256': sha(general_tests),
                  'public_path_sha256': sha(public_tests),
                  'candidate_sha256': sha(output / 'generator/candidate.json'),
                  'frozen_expected_facts_sha256': sha(output / 'expected-facts.json'),
                  'network_transport_attempted': False, 'candidate_gates': gates, 'repair_route': route}
        assert sha(output / 'generator/candidate.json') == sha(source / 'generator/candidate.json')
        assert sha(output / 'expected-facts.json') == sha(source / 'expected-facts.json')
        write(output / 'binding-admission.json', record)
        print(json.dumps({'status': record['status'], 'compile': gates['compile_reopen_success'], 'geometry': gates['geometry_success']}))
        return
    admission = json.loads((output / 'binding-admission.json').read_text(encoding='utf-8'))
    assert admission['status'] == 'admitted'
    original = json.loads((base / 'admission/generation-final/admission.json').read_text(encoding='utf-8'))
    for p, h in original['files_sha256'].items():
        assert sha(root / p) == admission['changed_source_sha256'].get(p, h), p
    assert sha(output / 'generator/candidate.json') == admission['candidate_sha256']
    assert sha(output / 'expected-facts.json') == admission['frozen_expected_facts_sha256']
    assert not (output / 'audit').exists()
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider, load_openai_compatible_runtime_config
    load_env_file(root / '.env')
    provider = OpenAICompatibleLiveProvider(config=load_openai_compatible_runtime_config(dict(os.environ)))
    record = {'status': 'running', 'network_transport_attempted': True,
              'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'Real Audit and final acceptance of unchanged real Generator corrective response after offline deterministic binding fix; not a blind capability trial'}
    write(output / 'execution.json', record)
    try:
        audit = run_audit_report_stage(provider=provider, case_dir=output, case_id='corrective-02-binding-revalidation')
        record['audit'] = audit
        if audit['valid'] and audit['status'] == 'accepted':
            record['final'] = run_final_acceptance_stage(case_dir=output, output_dir=output, case_id='corrective-02-binding-revalidation')
            record['status'] = 'succeeded' if record['final']['valid'] else 'final_blocked'
        else:
            record['status'] = 'audit_blocked'
    except Exception as error:
        record.update(status='exception', exception_type=type(error).__name__, message=str(error)[:500])
    finally:
        record['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        write(output / 'execution.json', record)
        print(json.dumps(record, ensure_ascii=False))

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
