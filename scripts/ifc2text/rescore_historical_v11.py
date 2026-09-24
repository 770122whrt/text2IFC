"""Retain historical measurements and apply the user-approved 1 mm policy."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from text2ifc_ifc2text.precision_compare_v11 import rescore

def main():
    source = ROOT / 'dataset/processed/experiments/ifc2text-fixes-20260922/full-scene-final'
    output = ROOT / 'dataset/processed/experiments/ifc2text-rerun-20260922/historical-rescore-1mm'
    output.mkdir(exist_ok=True)
    summary = {}
    for name in ('baseline-compare-0.1mm.json', 'new-v24-composition-compare-0.1mm.json'):
        path = source / name
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        report = rescore(json.loads(path.read_text(encoding='utf-8')))
        (output / name.replace('0.1mm', '1mm')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        summary[name] = {'original_sha256': before, 'original_unchanged': before == hashlib.sha256(path.read_bytes()).hexdigest(), 'summary': report.get('summary'), 'status': report['status']}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))

if __name__ == '__main__':
    main()
