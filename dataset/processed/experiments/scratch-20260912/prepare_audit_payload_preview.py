"""Local-only payload preview. No client, credentials or network transport."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from text2ifc_agent.live_pipeline import run_audit_report_stage

base = ROOT / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
source = base / 'generation/corrective-02-general-revalidation'
preview = base / 'generation/audit-payload-preview'
assert not (source / 'audit').exists()
shutil.copytree(source, preview)

class PreviewCaptured(Exception):
    pass

class LocalPreview:
    def generate_live(self, **kwargs):
        prompt = kwargs['prompt']
        # The case contains only the authorized synthetic Generation example.
        forbidden = ['2CsmzAChHF6O6maGXlo6PS', 'vvo.ifc', 'mutation_manifest', 'private_ground_truth']
        assert not any(value in prompt for value in forbidden)
        record = {'status': 'local_payload_preview_only', 'network_transport_attempted': False,
                  'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
                  'prompt_characters': len(prompt), 'sensitive_repair_tokens_absent': True,
                  'provider': 'DeepSeek', 'model': 'deepseek-v4-flash',
                  'payload': 'Synthetic Generation request, clarification, Design Brief, Formal candidate, deterministic gate feedback and run metadata; no IFC binary upload.',
                  'source': '../corrective-02-general-revalidation',
                  'note': 'Preview has its own local evidence paths. Real stage reconstructs the same content from the source case. No Provider response is simulated.'}
        (preview / 'PREVIEW.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(record, ensure_ascii=False))
        raise PreviewCaptured()

try:
    run_audit_report_stage(provider=LocalPreview(), case_dir=preview, case_id='corrective-02-binding-revalidation')
except PreviewCaptured:
    pass
assert not (source / 'audit').exists()
