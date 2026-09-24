"""Live-run wrapper guards, exercised without a network connection."""
import json
from pathlib import Path
import pytest


def peak_working_set():
    import sys
    if sys.platform=='win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[
                (name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize',
                    'QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
                    'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        psapi=ctypes.WinDLL('psapi',use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        counters=Counters();counters.cb=ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.PeakWorkingSetSize
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)


def test_frozen_public_input_rejects_changed_source_or_text(tmp_path):
    from scripts.ifc2text.component_campaign import frozen_text, digest
    source=tmp_path/'input.ifc';source.write_bytes(b'frozen native IFC')
    text=tmp_path/'description.md';text.write_text('部件说明',encoding='utf-8')
    case={'source':str(source),'source_sha256':digest(source),'text':str(text),'text_sha256':digest(text)}
    assert frozen_text(case)=='部件说明'
    text.write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError,match='PUBLIC_TEXT_CHANGED'):frozen_text(case)
    text.write_text('部件说明',encoding='utf-8');source.write_bytes(b'changed')
    with pytest.raises(ValueError,match='SOURCE_CHANGED'):frozen_text(case)


@pytest.mark.parametrize('source',[
    'dataset/external/bimnet/hxp.ifc',
    'dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc'])
def test_real_building_context_reaches_public_brief_and_stops_at_unsupported(tmp_path,source):
    import time
    from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker,unsupported_brief
    from text2ifc_ifc2text.compact_pipeline import prepare_compact
    from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
    from text2ifc_agent.session_store import SessionStore
    started=time.monotonic();before=Path(source).read_bytes()
    report=prepare_compact(source,tmp_path/'description',description_version='1.0')
    text=(tmp_path/'description/design-description-deterministic.md').read_text(encoding='utf-8')
    assert report['component_unsupported_count']>0
    requests=[];root=tmp_path/'generation'
    with SessionStore.open(root/'sessions.sqlite',artifact_root=root) as store:
        def invoke(transcript,index):
            return fake_brief_invoker(store.list_sessions()[-1].run_dir,unsupported_brief(text),requests)(transcript,index)
        result=reconstruct_description_with_public_text2ifc(text,store=store,invoke_design_brief=invoke,
            provider_factory=lambda:pytest.fail('Unsupported whole building cannot generate'),bim_json_schema_version='bim-json/2.6')
    assert result['status']=='needs_clarification' and len(requests)==1
    assert Path(source).read_bytes()==before
    encoded=json.dumps(requests[0],ensure_ascii=False)
    assert source not in encoded and 'source-facts.json' not in encoded
    (tmp_path/'real-size-offline.json').write_text(json.dumps({'source':source,
        'description_utf8_bytes':len(text.encode('utf-8')),'request_utf8_bytes':len(encoded.encode('utf-8')),
        'elapsed_seconds':time.monotonic()-started,'process_peak_working_set_bytes':peak_working_set(),
        'real_provider_calls':0,'status':result['status']}),encoding='utf-8')
