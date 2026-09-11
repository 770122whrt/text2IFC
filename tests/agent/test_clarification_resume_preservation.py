import json
import pytest
from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
from text2ifc_agent.session_store import SessionStore
from tests.agent.test_interactive_cli_flow import _brief, EVIDENCE


@pytest.mark.parametrize('answers', [[], ['200']])
def test_resume_preserves_first_call_and_uses_next_index(tmp_path, answers):
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    session=store.create_session(original_input='生成房间')
    calls=[]
    def invoke(transcript,index):
        calls.append(index)
        directory=session.run_dir/'calls'/f'{index:02d}-design-brief'
        directory.mkdir(parents=True,exist_ok=False)
        brief=_brief(original_request='生成房间',status='needs_clarification' if index==1 else 'ready',source_turns=['turn-user-001'] if index==1 else ['turn-user-001','turn-user-003'])
        (directory/'design-brief.json').write_text(json.dumps(brief),encoding='utf-8')
        (directory/'context-selection.json').write_text(json.dumps({'evidence':EVIDENCE}),encoding='utf-8')
        return ClarificationCall(index,f'response-{index}','design-brief.v2.2','sha256:test',str(directory),brief,EVIDENCE)
    first=run_design_brief_clarification_loop(store=store,session=session.session_hash,invoke_design_brief=invoke,user_answers=[])
    original=(session.run_dir/'calls/01-design-brief/design-brief.json').read_bytes()
    store.close()
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    result=run_design_brief_clarification_loop(store=store,session=session.session_hash,invoke_design_brief=invoke,user_answers=answers)
    assert calls==([1,2] if answers else [1])
    assert result.status==('ready' if answers else 'needs_clarification')
    assert (session.run_dir/'calls/01-design-brief/design-brief.json').read_bytes()==original
    assert [t.text for t in store.list_turns(session.session_hash)].count('生成房间')==1
    store.close()
