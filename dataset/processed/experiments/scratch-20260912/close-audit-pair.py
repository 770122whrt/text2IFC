import json, hashlib, sys
from pathlib import Path
sys.path.insert(0, 'src')
from text2ifc_agent.artifact_scan import scan_path
p = Path('dataset/processed/ifc-presentation-validation/audit-token-pair-20260911')
r = lambda f: json.loads(f.read_text(encoding='utf-8'))
h = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
a = r(p/'admission.json'); protocol = r(p/'protocol.json'); e = r(p/'live/execution.json')
mismatches = [s for s,v in a['files_sha256'].items() if not Path(s).is_file() or h(Path(s)) != v]
assert not mismatches, mismatches
requests = [r(p/'live'/mode/'request.redacted.json')['request'] for mode in ['full','deduplicated']]
assert {k:v for k,v in requests[0].items() if k != 'messages'} == {k:v for k,v in requests[1].items() if k != 'messages'}
rows = {}
for arm in e['arms']:
    mode = arm['mode']; folder = p/'live'/mode; data = r(folder/'audit-report.json'); expected = protocol['expected_output']
    text = (folder/'prompt-rendered.md').read_text(encoding='utf-8')
    assert hashlib.sha256(text.encode()).hexdigest() == protocol['prompt_sha256'][mode]
    request = r(folder/'request.redacted.json')['request']
    assert any(m['content'] == text for m in request['messages'])
    for key in ['schema_version','recommendation','blocking','deterministic_gate_status']:
        assert data[key] == expected[key], key
    assert any(c['id'] == 'reference-stair-walking-clearance' and c['status'] == expected['offered_concern_status'] for c in data['design_review']['concerns'])
    assert arm['valid'] and '\ufffd' not in (folder/'model-text.txt').read_text(encoding='utf-8')
    rows[mode] = {'usage':arm['usage'], 'response_id':arm['response_id'], 'decision':{k:data[k] for k in ['schema_version','recommendation','blocking','deterministic_gate_status']}, 'findings':data['findings'], 'design_review':data['design_review']}
assert rows['full']['decision'] == rows['deduplicated']['decision']
assert e['source_unchanged'] and h(Path(protocol['input_path'])) == protocol['input_sha256']
c = r(Path(protocol['C_latest_budget_path']))
c['calls_used'] = len(c['attempts'])
c['tokens_used_or_reserved'] = sum(x['tokens_charged'] for x in c['attempts'])
assert c['calls_used'] == 4 and c['tokens_used_or_reserved'] == 300540
reduction = {}
for key in ['prompt_tokens','completion_tokens','total_tokens']:
    base = rows['full']['usage'][key]; candidate = rows['deduplicated']['usage'][key]
    reduction[key] = {'full':base, 'deduplicated':candidate, 'saved':base-candidate, 'reduction_percent':round(100*(base-candidate)/base,4)}
report = {'scope':'One real Audit pair, not an end-to-end Generation experiment', 'arms':rows, 'reduction':reduction, 'budget':e['budget_after'], 'checks':{'admission_bindings_match_before_closeout_doc_edits':len(a['files_sha256']), 'requests_identical_except_messages':True, 'frozen_prompt_text_and_wire_hashes_match':True, 'source_unchanged':True, 'C_budget_unchanged':True, 'C_calls':c['calls_used'], 'C_tokens':c['tokens_used_or_reserved'], 'preregistered_decision_checks_pass':True}, 'limitations':['One observed pair; no statistical quality non-inferiority claim.', 'Cache hits differ substantially; token reduction is not equal to fee reduction.', 'Deduplicated output includes two nonblocking informational findings; full output has none.', 'Output/reasoning reductions may reflect sampling variability.'], 'closeout_analysis_note':'Initial local analysis assertions incorrectly required empty findings, compared the local request wrapper including session ID, and compared Windows CRLF file bytes with the rendered LF text hash. None was a preregistered criterion. Raw responses and protocol were preserved. Actual HTTP request fields differ only in messages; rendered text matches wire content and the frozen text hash. Preregistered decisions pass; presentation differences are reported separately.'}
(p/'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'reduction':reduction, 'checks':report['checks'], 'scan':scan_path(p)}, ensure_ascii=False))
