from types import SimpleNamespace
import pytest
from text2ifc_web.observation import ObservedProvider


def test_observer_preserves_provider_result_and_actual_call_count():
    result=SimpleNamespace(metadata={'usage':{'input_tokens':12,'output_tokens':8}})
    calls=[];events=[]
    class Provider:
        def generate_candidate(self,**kw):calls.append(kw);return result
    wrapped=ObservedProvider(Provider(),events.append)
    assert not hasattr(wrapped,'generate_live')
    assert wrapped.generate_candidate(state={'stage':'scene','attempt':1},prompt='exact') is result
    assert len(calls)==1 and calls[0]['prompt']=='exact'
    assert [e['action'] for e in events]==['started','completed']
    assert events[-1]['usage']=={'input_tokens':12,'output_tokens':8}


def test_observation_error_does_not_retry_or_change_provider_failure():
    calls=[]
    class Provider:
        def generate_candidate(self,**kw):calls.append(1);raise TimeoutError('fixed-test')
    def broken(event):raise OSError('test observer failure')
    with pytest.raises(TimeoutError,match='fixed-test'):
        ObservedProvider(Provider(),broken).generate_candidate(state={'attempt':2})
    assert calls==[1]
