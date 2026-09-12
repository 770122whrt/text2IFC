def main():
    import datetime as dt, hashlib, json, os, shutil, sys
    import xml.etree.ElementTree as ET
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    sys.path[:0]=[str(root),str(root/'src')]
    base=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
    prior=root/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
    source=base/'runtime-02/runs/45743eb8eb1e77b0'
    retry_empty='--retry-empty' in sys.argv
    output=base/('corrective-04' if retry_empty else 'corrective-03')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def read(p):return json.loads(p.read_text(encoding='utf-8'))
    def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    admission=read(prior/'admission/generation-final/admission.json')
    override=read(prior/'generation/corrective-02-general-revalidation/binding-admission.json')
    for p,h in admission['files_sha256'].items(): assert sha(root/p)==override['changed_source_sha256'].get(p,h),p
    suite=root/'.tmp/two-storey-contracts-02.xml'
    for s in ET.parse(suite).iter('testsuite'):
        assert all(int(s.get(k,'0'))==0 for k in ['failures','errors','skipped'])
    assert sha(base/'request.txt')==read(base/'frozen-expectations.json')['request_sha256']
    feedback={'previous_candidate':read(source/'generator/parsed-output.json'),
        'previous_validation':read(source/'generator/validation.json'),
        'instruction':'Correct the full Formal 2.1 document against the unchanged user request, Design Brief and identity contract. The actual IFC2X3 IfcStairFlight attribute is NumberOfRiser (singular); NumberOfTreads is plural. Explicit IfcDoorStyle OperationType must be SINGLE_SWING_LEFT for door-left and SINGLE_SWING_RIGHT for door-right; do not attach a conflicting default or shared style. No user Type-sharing request exists; deterministic code can supply required minimal legal styles when explicit Type is omitted. ObjectPlacement.axis and ref_direction are LOCAL to relative_to. An opening relative to an already rotated wall, and its filling relative to that opening, use local identity ref_direction [1,0,0], axis [0,0,1] to inherit orientation once. Preserve user dimensions, world positions, storey elevations, stair rise/run and actual upper slab opening, panel templates, materials, absent unrequested properties and warm-residential appearance. Do not alter frozen request facts to clear errors. Return the entire corrected candidate, not a patch or represented labels.'}
    if retry_empty:
        assert (base/'corrective-03/generator/model-text.txt').read_bytes()==b''
        assert feedback==read(base/'corrective-03/feedback.json')
    if '--check-only' in sys.argv:
        assert not output.exists()
        write(base/'corrective-feedback-preview.json',feedback)
        print('Same-stage source admission verified; focused contracts passed; one real corrective Generator allowed by existing entry point; no Provider call made.')
        return
    output.mkdir(exist_ok=False)
    shutil.copytree(source/'design-brief',output/'design-brief')
    for name in ['design-brief.json','expected-facts.json','request-semantics.json']:
        if (source/name).is_file():shutil.copyfile(source/name,output/name)
    write(output/'feedback.json',feedback)
    write(output/'admission.json',{'status':'admitted','evidence_class':'same-stage scoped revalidation',
        'base_sha256':sha(prior/'admission/generation-final/admission.json'),'override_sha256':sha(prior/'generation/corrective-02-general-revalidation/binding-admission.json'),
        'tests_sha256':sha(suite),'diagnosis_sha256':sha(base/'offline-contract-diagnosis.json'),
        'scope':'One corrective Generator through existing live_pipeline feedback, then deterministic semantic/candidate checks. No Audit in this script. Original public CLI failed; corrective pipeline is reported separately. No production source, prompt, schema or profile changes.'})
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider,load_openai_compatible_runtime_config
    from text2ifc_agent.live_pipeline import run_generator_stage,run_semantic_coverage_stage,run_candidate_gate_stage
    load_env_file(root/'.env')
    provider=OpenAICompatibleLiveProvider(config=load_openai_compatible_runtime_config(dict(os.environ)))
    record={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'network_transport_attempted':True,'scope':'one real corrective Generator, no Audit; api.deepseek.com deepseek-v4-flash, synthetic public Generation request/Brief/candidate/validation only'}
    write(output/'execution.json',record)
    try:
        generator=run_generator_stage(provider=provider,output_dir=output/'generator',design_source_dir=output/'design-brief',case_id='two-storey-'+output.name,generation_feedback=feedback,generator_call_index=2)
        record['generator']=generator
        write(output/'execution.json',record)
        if not generator['valid']:record['status']='generator_blocked';return
        record['semantic_coverage']=run_semantic_coverage_stage(case_dir=output,output_dir=output,case_id='two-storey-'+output.name)
        if not record['semantic_coverage']['valid']:record['status']='semantic_blocked';return
        record['candidate_gates']=run_candidate_gate_stage(case_dir=output,output_dir=output,case_id='two-storey-'+output.name)
        record['status']='candidate_valid_pending_independent_and_audit' if record['candidate_gates']['valid'] else 'candidate_blocked'
    except Exception as e:
        record.update(status='exception',exception_type=type(e).__name__,message=str(e)[:500])
    finally:
        record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
        write(output/'execution.json',record)
        print(json.dumps({'status':record['status']},ensure_ascii=False))
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()

