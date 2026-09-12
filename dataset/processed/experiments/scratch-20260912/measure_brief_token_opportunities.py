import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from text2ifc_agent.openai_compat import estimate_openai_compatible_input_tokens as estimate
out=root/'dataset/processed/ifc-presentation-validation/c-shaped-brief-budget-experiment-20260910'
source=out.parent/'c-shaped-brief-debug-20260910/live-attempt/design-brief'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
inputs=read(source/'prompt-render-input.json')
parts=[]
for name,value in inputs.items():
    text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
    compact=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,separators=(',',':'))
    parts.append(dict(name=name,utf8_bytes=len(text.encode()),estimated_tokens=estimate(text),compact_estimated_tokens=estimate(compact)))
response=read(source/'response.raw.json');text=response['choices'][0]['message']['content']
brief=json.loads(text);compact=json.dumps(brief,ensure_ascii=False,separators=(',',':'))
known=brief['known_facts']
facts=[dict(name=name,estimated_tokens=estimate(json.dumps(value,ensure_ascii=False))) for name,value in known.items()]
diagnosis=dict(source_response_sha256=__import__('hashlib').sha256((source/'response.raw.json').read_bytes()).hexdigest(),
    source_is_previous_successful_v2_7_call=True,estimator='Repository conservative ASCII/CJK estimate, not provider tokenizer or measured savings.',
    input_sections=sorted(parts,key=lambda r:r['estimated_tokens'],reverse=True),
    visible_output=dict(raw_chars=len(text),compact_chars=len(compact),raw_estimated_tokens=estimate(text),compact_estimated_tokens=estimate(compact)),
    known_fact_sections=sorted(facts,key=lambda r:r['estimated_tokens'],reverse=True),
    actual_usage=response['usage'],constraints=['Do not omit explicit facts or source evidence.','No automatic IFC Type sharing from textual compression.',
        'No realised token-saving claim without new controlled runs.','This turn does not implement compression or staged extraction.'])
(out/'token-opportunities.json').write_text(json.dumps(diagnosis,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'input_sections':diagnosis['input_sections'],'visible_output':diagnosis['visible_output'],'top_known_facts':diagnosis['known_fact_sections'][:4]},ensure_ascii=False))
