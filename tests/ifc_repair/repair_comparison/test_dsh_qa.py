"""Admission/response boundaries for complete native DSH Q&A."""
import pytest

from scripts.ifc_repair.repair_comparison.contracts import write_json


@pytest.mark.parametrize('blocks, expected', [
    ([{'type': 'text', 'text': 'I searched the web.'}], False),
    ([{'type': 'web_search_tool_result', 'content': []}], False),
    ([{'type': 'web_search_tool_result', 'content': [{'type': 'web_search_result',
        'url': 'https://www.buildingsmart.org/', 'title': 'buildingSMART'}]}], True),
])
def test_connectivity_requires_actual_native_result_blocks(blocks, expected):
    from scripts.ifc_repair.repair_comparison.dsh.qa import search_sources
    assert bool(search_sources({'content': blocks})) is expected




def test_probe_requires_actual_successful_pytest_cases(tmp_path):
    from scripts.ifc_repair.repair_comparison.dsh.qa import passed_suite
    receipt = tmp_path/'suite.xml'
    receipt.write_text('<testsuites><testsuite tests="1"><testcase classname="expected" name="x"><failure/></testcase></testsuite></testsuites>', encoding='utf8')
    with pytest.raises(ValueError, match='SEARCH_OFFLINE_SUITE_FAILED'):
        passed_suite(receipt, 'expected')
    receipt.write_text('<testsuites><testsuite tests="0"/></testsuites>', encoding='utf8')
    with pytest.raises(ValueError, match='SEARCH_OFFLINE_SUITE_MISSING'):
        passed_suite(receipt, 'expected')




def test_complete_qa_requires_search_consumption_and_a_final_answer(tmp_path):
    from scripts.ifc_repair.repair_comparison.dsh.qa import qa_outcome
    from scripts.ifc_repair.repair_comparison.ledger import Ledger
    ledger = Ledger(tmp_path/'control.sqlite')
    run = 'native-qa-D'
    ledger.create(run, case_id='native-qa', arm='D', budget={'tokens': 1500000,
        'calls': 8, 'active_seconds': 300, 'tool_seconds': 120, 'extensions': []})
    ledger.start(run)
    directory = tmp_path/'wire'/run; directory.mkdir(parents=True)
    source = 'https://example.invalid/fake-qa'
    for call, stage, request, response in [
        ('root-1', 'model', {'messages': []}, {}),
        ('search-1', 'web_search', {}, {'body': {'content': [
            {'type': 'web_search_tool_result', 'content': [
                {'type': 'web_search_result', 'url': source}]}]}}),
        ('root-2', 'model', {'messages': [{'role': 'user', 'content': source}]}, {})]:
        ledger.reserve(run, call, 100, metadata={'stage': stage})
        ledger.settle(run, call, usage={'input_tokens': 1, 'output_tokens': 1},
            response=response, failed=False)
        write_json(directory/(call+'.json'), {'request_id': call, 'request': request, 'response': response})
    completed = {'ok': True, 'result': {'finish_reason': 'completed', 'final_response': 'Fixture answer '+source}}
    outcome = qa_outcome(tmp_path, run, completed)
    assert outcome['status'] == 'completed' and outcome['root_requests'] == 2
    assert outcome['search_results_consumed'] is True
    for native in [{'ok': True, 'result': {'finish_reason': 'error', 'final_response': 'partial'}},
                   {'ok': True, 'result': {'finish_reason': 'completed', 'final_response': ''}}]:
        assert qa_outcome(tmp_path, run, native)['status'] == 'failed'
    write_json(directory/'root-2.json', {'request_id': 'root-2', 'request': {'messages': []}, 'response': {}})
    assert qa_outcome(tmp_path, run, completed)['status'] == 'failed'


def test_qa_unknown_usage_hold_never_becomes_reported_usage():
    from scripts.ifc_repair.repair_comparison.dsh.qa import qa_budget_available
    usage = {'known_tokens': 8463560, 'reserved_tokens': 4344, 'unknown_calls': 1}
    assert not qa_budget_available(usage, 1500000, 20000000, 0)
    assert qa_budget_available(usage, 1500000, 20000000, 9000000)
    assert not qa_budget_available(usage, 1500000, 20000000, 11000000)
    assert usage['unknown_calls'] == 1 and usage['known_tokens'] == 8463560


def test_web_qa_requires_successful_page_body_in_a_root_request(tmp_path):
    from scripts.ifc_repair.repair_comparison.dsh.qa import page_evidence
    from scripts.ifc_repair.repair_comparison.ledger import Ledger
    ledger = Ledger(tmp_path/'control.sqlite')
    ledger.create('page-D', case_id='page', arm='D', budget={
        'tokens': 1500000, 'calls': 48, 'active_seconds': 1800, 'tool_seconds': 120, 'extensions': []})
    ledger.start('page-D'); ledger.reserve('page-D', 'root', 100, metadata={'stage': 'model'})
    ledger.settle('page-D', 'root', usage={'input_tokens': 1, 'output_tokens': 1}, response={}, failed=False)
    path = tmp_path/'wire/page-D/root.json'; path.parent.mkdir(parents=True)
    url = 'https://example.invalid/page'
    request = {'messages': [
        {'role': 'assistant', 'content': [{'type': 'tool_use', 'id': 'fetch', 'name': 'web_fetch', 'input': {'url': url}}]},
        {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'fetch', 'content': [
            {'type': 'text', 'text': 'Fetched '+url+' (HTTP 200)\n\nExternal web content follows.\n\nOFFLINE_PAGE_BODY'}]}]}]}
    write_json(path, {'request': request})
    pages = page_evidence(tmp_path, 'page-D')
    assert len(pages) == 1 and pages[0]['ok'] and 'OFFLINE_PAGE_BODY' in pages[0]['excerpt']
    for text in ('Error: web fetch failed: DNS unavailable', 'Fetched '+url+' (HTTP 403)\n\nDenied'):
        request['messages'][-1]['content'][0]['content'][0]['text'] = text
        write_json(path, {'request': request})
        assert page_evidence(tmp_path, 'page-D')[0]['ok'] is False
