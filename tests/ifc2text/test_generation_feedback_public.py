"""Optional validator feedback uses the real public Generator, not a trace-only stub."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pytest
from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop, run_ready_session_to_ifc
from text2ifc_agent.session_store import SessionStore
ROOT=Path(__file__).resolve().parents[2]


def test_explicit_feedback_reaches_registered_prompt_and_real_compile(tmp_path):
    spec=importlib.util.spec_from_file_location('feedback_fixtures',ROOT/'tests/ifc2text/test_offline_public_bridge.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    candidate=json.loads((ROOT/'dataset/processed/agent-demo/phase6.1-mimo-live/complete-room/generator/candidate.json').read_text(encoding='utf-8'))
    provider=m._SequenceLiveProvider([candidate,{'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}])
    feedback={'reason':'Prior public output violated closed-ring encoding; keep original dimensions.', 'issues':[{'code':'OPEN_POLYGON_PROFILE'}]}
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        s=store.create_session(original_input='单层房间6米乘4米高3米，四墙厚300毫米，南门900乘2100毫米，北窗1200乘1500毫米，窗台900毫米。')
        run_design_brief_clarification_loop(store=store,session=s.session_id,invoke_design_brief=m._design_brief_invoker(store),user_answers=())
        result=run_ready_session_to_ifc(store=store,session=s.session_id,provider_factory=lambda:provider,
            generation_feedback=feedback,generator_call_index=2)
        assert result.status=='compiled' and Path(result.ifc_path).is_file()
        rendered=json.loads((s.run_dir/'generator/prompt-render-input.json').read_text(encoding='utf-8'))
        assert rendered['GENERATION_FEEDBACK']==feedback
        assert provider.session_ids[0].endswith('generator-02')
        assert 'closed-ring' in (s.run_dir/'generator/prompt-rendered.md').read_text(encoding='utf-8')


def test_feedback_not_silently_ignored_by_staged_strategy(tmp_path):
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        s=store.create_session(original_input='test')
        with pytest.raises(ValueError,match='legacy_full'):
            run_ready_session_to_ifc(store=store,session=s.session_id,provider_factory=lambda:None,
                generation_strategy='staged',generation_feedback={'reason':'test'})
