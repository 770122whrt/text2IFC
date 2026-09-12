import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from text2ifc_agent.live_pipeline import run_generator_stage
BASE=ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909'
OUT=BASE/'geometry-payload-preview'
class StopBeforeTransport(Exception): pass
class Preview:
    def generate_live(self,**kwargs):
        (OUT/'provider-payload-preview.json').write_text(json.dumps({k:v for k,v in kwargs.items()},ensure_ascii=False,indent=2),encoding='utf-8')
        raise StopBeforeTransport()
try:
    run_generator_stage(provider=Preview(),output_dir=OUT,
        design_source_dir=BASE/'runtime/runs/148bdf3872e74ccd/design-brief',case_id='geometry-continuation-preview')
except StopBeforeTransport: pass
print(json.dumps({'network_transport_attempted':False,'prompt':str(OUT/'prompt-rendered.md'),'payload_bytes':(OUT/'provider-payload-preview.json').stat().st_size}))
