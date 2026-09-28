"""Production controller recovers a recorded ready Brief without model replay."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from text2ifc_agent.session_store import SessionStore
from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop,run_ready_session_to_ifc
from text2ifc_agent.providers import ProviderOutputError

ROOT=Path(__file__).resolve().parents[2]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_connection_failed_session_recovers_via_public_brief_controller(tmp_path):
    fixtures=module('retry_fixtures','tests/ifc2text/test_offline_public_bridge.py')
    retry=module('retry_entry','scripts/ifc2text/retry_transport_generation.py')
    class FailedTransport:
        def generate_live(self,**kwargs):
            raise ProviderOutputError('fixture transport failure',details={'failure_class':'provider_connection_error'})
    with SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path) as store:
        session=store.create_session(original_input='单层房间长6米宽4米高3米，四面墙300毫米，南门900乘2100毫米，北窗1200乘1500毫米，窗台900毫米。')
        first=run_design_brief_clarification_loop(store=store,session=session.session_id,
            invoke_design_brief=fixtures._design_brief_invoker(store),user_answers=())
        assert first.status=='ready'
        failed=run_ready_session_to_ifc(store=store,session=session.session_id,provider_factory=FailedTransport)
        assert failed.status=='provider_failed'
        original=(session.run_dir/'design-brief.json').read_bytes()
        restored=retry.restore_ready_public(store,session.session_id)
        assert restored.status=='ready'
        assert store.get_session(session.session_id).status=='ready'
        assert (session.run_dir/'design-brief.json').read_bytes()==original
        assert not (session.run_dir/'output.ifc').exists()
