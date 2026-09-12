"""Offline three-storey public ready-session path, with actual IFC gates."""
import json, sys, time, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]

def main():
    import ctypes, ifcopenshell
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    process=ctypes.windll.kernel32.GetCurrentProcess
    process.restype=wintypes.HANDLE
    get_memory=ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    from text2ifc_agent.complex_scaffold import build_scaffold_candidate
    from text2ifc_agent.expected_facts import build_expected_facts
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    fixture=json.loads((ROOT/'dataset/processed/agent-demo/phase6.5-cases/three-storey-case.json').read_text(encoding='utf-8'))
    brief=fixture['design_brief']
    out=ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/scale-public-04'
    out.mkdir(exist_ok=False)
    store=SessionStore.open(out/'sessions.sqlite',artifact_root=out)
    session=store.create_session(original_input=brief['original_request'])
    brief.update(user_corrections=[],clarification_questions=[],provenance={'source_turns':['turn-user-001'],'selected_evidence_ids':[],'few_shot_ids':[]})
    design_result=run_design_brief_stage(provider=SequenceProvider([brief]),
        case={'case_id':session.session_hash,'user_request':brief['original_request'],'conversation':[{'turn_id':'turn-user-001','role':'user','content':brief['original_request']}]},
        output_dir=session.run_dir/'design-brief',design_brief_schema_version='text2ifc/design-brief/2.0')
    assert design_result['valid'],design_result
    (session.run_dir/'design-brief.json').write_text(json.dumps(brief,ensure_ascii=False),encoding='utf-8')
    store.mark_session_status(session.session_id,'ready')
    expected=build_expected_facts(case_id=session.session_hash,design_brief=brief)
    candidate=build_scaffold_candidate(case_id=session.session_hash,design_brief=brief,expected_facts=expected)
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
           'deterministic_gate_status':'passed','findings':[],
           'evidence_paths':['generator/candidate.json','ifc-verification.json']}
    class MeasuredProvider(SequenceProvider):
        def generate_live(self, **kwargs):
            prompt_sizes.append(len(kwargs['prompt'].encode('utf-8')))
            return super().generate_live(**kwargs)
    prompt_sizes=[]
    provider=MeasuredProvider([candidate,audit])
    stopped=threading.Event(); peak=[0]
    def sample():
        while not stopped.is_set():
            stats=Counters();stats.cb=ctypes.sizeof(stats)
            if not get_memory(process(),ctypes.byref(stats),stats.cb):
                raise ctypes.WinError()
            peak[0]=max(peak[0],stats.PeakWorkingSetSize)
            stopped.wait(.05)
    monitor=threading.Thread(target=sample,daemon=True);monitor.start();start=time.monotonic()
    try:
        result=run_ready_session_to_ifc(store=store,session=session.session_id,provider_factory=lambda:provider)
    finally:
        stopped.set();monitor.join();store.close()
    elapsed=time.monotonic()-start
    counts={}
    if result.ifc_path:
        model=ifcopenshell.open(str(result.ifc_path))
        counts={c:len(model.by_type(c)) for c in ['IfcBuildingStorey','IfcWall','IfcSpace','IfcStairFlight','IfcDoor','IfcWindow']}
    record={'evidence_class':'deterministic_fake_provider','status':result.status,'ifc':str(result.ifc_path),
        'counts':counts,'seconds':elapsed,'parent_peak_working_set_bytes':peak[0],
        'memory_scope':'Parent process Windows peak working set; child process memory not measured',
        'prompt_utf8_bytes':prompt_sizes,
        'candidate_entities':len(candidate['entities']),'provider_calls':len(provider.calls),
        'network_transport_attempted':False,'limits':{'seconds':180,'peak_rss_bytes':2*1024**3,'prompt_utf8_bytes':256000},
        'scope':'Three-storey representative geometry through public ready-session API; old contract compatibility. New 2.1 full chain separately tested.'}
    record['passed']=result.status=='compiled' and counts.get('IfcBuildingStorey')==3 and elapsed<180 and peak[0]<2*1024**3 and all(n<256000 for n in record['prompt_utf8_bytes'])
    (out/'scale-result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False))
    assert record['passed'],record

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
