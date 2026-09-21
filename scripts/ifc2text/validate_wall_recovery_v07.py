"""Scoped admission for v0.7; inherits the unchanged forward-chain admission."""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.recover_wall_v07 import OUT, git
from scripts.ifc2text.attribute_roundtrip_v01 import dump, load

SCOPE=['src/text2ifc_ifc2text','src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract',
       'prompts/agent','schemas','scripts/ifc2text/recover_wall_v07.py','scripts/ifc2text/validate_wall_recovery_v07.py',
       'tests/ifc2text/test_wall_details_v07.py','tests/ifc2text/test_source_containment_v07.py','tests/ifc2text/test_recover_wall_v07.py']
TARGETS=['tests/ifc2text/test_wall_details_v07.py','tests/ifc2text/test_source_containment_v07.py','tests/ifc2text/test_recover_wall_v07.py',
         'tests/ifc2text/test_attribution_probe_v01.py','tests/ifc2text/test_compact_public_v04.py',
         'tests/ifc2text/test_goal_budget_v03.py','tests/agent/test_public_brief_failure_evidence.py',
         'tests/compiler/test_v2_geometry.py','tests/ifc2text/test_diagnostic_review.py']


def main():
    import compileall
    import pytest
    from scripts.ifc2text.validate_goal import OfflineRecorder
    out=OUT/'validation'; out.mkdir(parents=True,exist_ok=True)
    ancestor=load(ROOT/'dataset/processed/experiments/ifc2text-attribution-20260921-v01/validation/admission.json')
    assert ancestor['status']=='admitted'
    assert not git('diff',ancestor['code_commit'],'--','src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract','prompts/agent','schemas'), 'FORWARD_SYSTEM_CHANGED_REQUIRES_APPROVAL'
    clean=not git('status','--porcelain','--untracked-files=all','--',*SCOPE)
    if not clean:raise RuntimeError('COMMIT_SCOPE_BEFORE_LIVE_ADMISSION')
    suffix=uuid.uuid4().hex[:10]; log=io.StringIO(); recorder=OfflineRecorder()
    command=['-o','addopts=',*TARGETS,'-q','--basetemp='+str(out/('tmp-'+suffix)),'-p','no:cacheprovider']
    started=time.time()
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log),recorder.network_guard():
        exit_code=pytest.main(command,plugins=[recorder])
    (out/'pytest.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
    compiled=all(compileall.compile_file(str(ROOT/p),quiet=1) for p in ['scripts/ifc2text/recover_wall_v07.py',
        'scripts/ifc2text/validate_wall_recovery_v07.py','src/text2ifc_ifc2text/wall_details_v07.py','src/text2ifc_ifc2text/source_containment_v07.py'])
    passed=exit_code==0 and compiled and recorder.network_attempts==0 and recorder.setup_errors==0 and not recorder.counts['skipped']
    record={'status':'admitted' if passed else 'blocked','code_commit':git('rev-parse','HEAD'),'scope':SCOPE,
        'ancestor_admission':'ifc2text-attribution-20260921-v01/validation/admission.json',
        'forward_system_unchanged':True,'command':command,'exit_code':int(exit_code),'counts':recorder.counts,
        'setup_errors':recorder.setup_errors,'network_attempts':recorder.network_attempts,'compileall':compiled,
        'elapsed_seconds':time.time()-started,'full_preflight':False,'scope_clean':clean,
        'mode':'offline fake/frozen responses; not live capability evidence',
        'live_scope':'one v0.6 narration; one public Brief and one Generator stage diagnostic; no Audit or full-building acceptance',
        'network_transport_attempted':False,'nodeids':recorder.nodeids}
    dump(out/'admission.json',record)
    print(json.dumps({k:v for k,v in record.items() if k not in {'nodeids','command'}},ensure_ascii=True))
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
