def main():
    import datetime as dt
    import hashlib
    import json
    import os
    import shutil
    import sys
    import xml.etree.ElementTree as ET
    from pathlib import Path
    ROOT=Path(__file__).resolve().parents[1]
    sys.path[:0]=[str(ROOT),str(ROOT/'src')]
    BASE=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
    GEN=BASE/'generation'
    original=GEN/'runtime/runs/bd9a2fd94c6e4be8'
    OUT=GEN/'corrective-attempt-02'
    family=BASE/'admission/rotation-family.xml'
    assert all(all(int(s.get(k,'0'))==0 for k in ['failures','errors','skipped']) for s in ET.parse(family).iter('testsuite'))
    admission=json.loads((BASE/'admission/generation-final/admission.json').read_text(encoding='utf-8'))
    addon=json.loads((GEN/'resume-admission.json').read_text(encoding='utf-8'))
    for p,h in admission['files_sha256'].items():
        expected=addon['changed_source_sha256'].get(p,h)
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==expected,p
    OUT.mkdir(exist_ok=False)
    shutil.copytree(original/'design-brief',OUT/'design-brief')
    for name in ['design-brief.json','expected-facts.json','request-semantics.json']:
        if (original/name).is_file():shutil.copyfile(original/name,OUT/name)
    feedback={'reason':'BASIC_FILLING_CONSTRAINT_CONFLICT','previous_validation':json.loads((original/'generator/validation.json').read_text(encoding='utf-8')),
              'previous_candidate':json.loads((original/'generator/parsed-output.json').read_text(encoding='utf-8')),
              'instruction':'ObjectPlacement.axis and ref_direction are LOCAL to relative_to. East/west wall is already rotated with ref_direction [0,1,0] relative to storey. Openings relative to those walls and fillings relative to those openings must each have LOCAL ref_direction [1,0,0] and axis [0,0,1] to inherit orientation once. Keep requested dimensions, positions, material, absence of properties, and warm-residential appearance. Produce the complete corrected Formal 2.1 document; do not merely label requirements represented.'}
    (OUT/'feedback.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import OpenAICompatibleLiveProvider, load_openai_compatible_runtime_config
    from text2ifc_agent.live_pipeline import run_generator_stage,run_candidate_gate_stage,run_repair_stage,run_audit_report_stage,run_final_acceptance_stage,run_semantic_coverage_stage
    load_env_file(ROOT/'.env')
    provider=OpenAICompatibleLiveProvider(config=load_openai_compatible_runtime_config(dict(os.environ)))
    record={'status':'running','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'network_transport_attempted':True,'origin_session':'bd9a2fd94c6e4be8','evidence_class':'real_provider_corrective_attempt','public_entry':'existing live_pipeline Generator feedback -> candidate gate -> repair routing -> Audit -> final acceptance; no claimed new CLI first-attempt success','frozen_failure_family_sha256':hashlib.sha256(family.read_bytes()).hexdigest()}
    def save(): (OUT/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        generator=run_generator_stage(provider=provider,output_dir=OUT/'generator',design_source_dir=OUT/'design-brief',case_id='reception-corrective-02',generation_feedback=feedback,generator_call_index=2)
        record['generator']=generator;save()
        if not generator['valid']:record['status']='generator_blocked';return
        gates=run_candidate_gate_stage(case_dir=OUT,output_dir=OUT,case_id='reception-corrective-02')
        record['candidate_gates']=gates;save()
        if not gates['valid']:record['status']='gates_blocked';return
        route=run_repair_stage(provider_factory=lambda:provider,output_dir=OUT/'repair',generator_source_dir=OUT/'generator',case_id='reception-corrective-02')
        record['repair_route']=route;save()
        audit=run_audit_report_stage(provider=provider,case_dir=OUT,case_id='reception-corrective-02')
        record['audit']=audit;save()
        if not audit['valid'] or audit['status']!='accepted':record['status']='audit_blocked';return
        record['final']=run_final_acceptance_stage(case_dir=OUT,output_dir=OUT,case_id='reception-corrective-02')
        record['status']='succeeded' if record['final']['valid'] else 'final_blocked'
    except Exception as e:
        record.update(status='exception',exception_type=type(e).__name__,message=str(e)[:500])
    finally:
        record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save();print(json.dumps({'status':record['status']},ensure_ascii=False))

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
