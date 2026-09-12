"""Curate this failed live attempt without changing any runtime evidence."""
import hashlib
import json
from pathlib import Path
import re

from text2ifc_agent.artifact_scan import scan_path

OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def main():
    run = OUT/'A-revise/runtime/runs/135976189dc358f9'
    execution = json.loads((OUT/'A-revise/execution.json').read_text(encoding='utf-8'))
    assert execution['status'] == 'audit_blocked'
    assert not list(run.rglob('*.ifc'))
    assert not (OUT/'B-retain').exists()
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', (OUT/'REPORT.md').read_text(encoding='utf-8'))
    assert links and all((OUT/p).is_file() for p in links)
    initial = json.loads((run/'calls/01-design-brief/parsed-output.json').read_text(encoding='utf-8'))
    corrected = json.loads((run/'calls/01-design-brief/design-brief.json').read_text(encoding='utf-8'))
    for value in [initial, corrected]:
        value['known_facts'].pop('semantic_requirements', None)
        value['known_facts'].pop('semantic_review', None)
    assert initial == corrected
    scan = scan_path(OUT)
    write(OUT/'presentation-checks.json', {'status':'failed live diagnostic, not Proof acceptance',
        'links_checked':len(links),'broken_links':0,'no_ifc_output':True,'B_not_started':True,
        'brief_repair_nonsemantic_preservation':True,'artifact_scan':scan,
        'scan_limits':'Declared text suffixes only; no claim of a general secret audit.'})
    files = [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='FILES.json']
    write(OUT/'FILES.json', {'schema_version':'text2ifc/curated-evidence-files/1.0',
        'status':'failed live attempt preserved; no accepted Proof',
        'files':[{'path':p.relative_to(OUT).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
    print(json.dumps({'frozen_files':len(files),'report_links':len(links),'scan_findings':scan['finding_count']}))


if __name__ == '__main__':
    main()
