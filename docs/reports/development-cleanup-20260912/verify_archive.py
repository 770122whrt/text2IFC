"""Verify only the new retirement mappings and scan their publishable contents."""
from pathlib import Path
import hashlib
import io
import json
import re
import sqlite3
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'src'), str(ROOT)]
from text2ifc_agent.artifact_scan import SECRET_PATTERNS, ALLOWED_ENV_NAMES

REPORT = Path(__file__).resolve().parent
OUT = ROOT/'dataset/processed/experiments'


def main():
    archive = json.loads((OUT/'development-retirement-20260912.json').read_text(encoding='utf8'))
    scratch = json.loads((OUT/'scratch-retirement-20260912.json').read_text(encoding='utf8'))
    entries = [e for b in archive['bundles'] for e in b['entries']] + scratch['entries']
    unique = {}
    for e in entries:
        p = ROOT/e['retained_path']
        member = e.get('archive_member')
        if member:
            assert hashlib.sha256(p.read_bytes()).hexdigest() == e['container_sha256']
            with zipfile.ZipFile(p) as z:
                with z.open(member) as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                assert z.getinfo(member).file_size == e['size_bytes']
        else:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            assert p.stat().st_size == e['size_bytes']
        assert digest == e['sha256'], str(p)
        unique[(e['retained_path'], member)] = p
    findings = []
    scanned = 0
    for (name, member), p in unique.items():
        suffix = Path(member or name).suffix.lower()
        if suffix not in {'.py','.ps1','.json','.jsonl','.txt','.log','.md','.xml','.html','.sqlite','.db','.patch'}:
            continue
        scanned += 1
        def scan(lines):
            for n, line in enumerate(lines, 1):
                for env in ALLOWED_ENV_NAMES:
                    line = line.replace(env, '')
                for code, pat in SECRET_PATTERNS:
                    match = pat.search(line)
                    if match:
                        findings.append(dict(path=name, member=member, line=n, code=code,
                            variable_reference=bool(re.search(r'api_key\s*=\s*(self\.|config\.|os\.)',match.group()))))
        if member:
            with zipfile.ZipFile(p) as z, z.open(member) as f, io.TextIOWrapper(f,encoding='utf8',errors='replace') as text:
                scan(text)
        elif suffix in {'.sqlite','.db'}:
            with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as c:
                scan(c.iterdump())
        else:
            with p.open(encoding='utf8',errors='replace') as f:
                scan(f)
    result = dict(binding_status='passed', checked_entries=len(entries), unique_files=len(unique),
        scanned_text_or_database_files=scanned, finding_count=len(findings), findings=findings,
        ifc_bytes_modified=False, provider_calls=0)
    (REPORT/'archive-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k != 'findings'}))
    print(json.dumps(findings[:12]))


if __name__ == '__main__':
    main()
