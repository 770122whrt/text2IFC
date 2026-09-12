import hashlib,json,re,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from text2ifc_agent.artifact_scan import scan_path
out=root/'dataset/processed/ifc-presentation-validation/c-shaped-brief-debug-20260910'
source=out.parent/'c-shaped-teaching-building-20260910'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
validation=out/'validation'
for name in ['brief-prompt-version-red','brief-prompt-final','brief-registry-final','brief-version-verified']:
    for suffix in ['xml','log']:
        p=root/'.tmp'/f'{name}.{suffix}'
        if p.exists():shutil.copyfile(p,validation/p.name)
tests=list(ET.parse(validation/'brief-version-verified.xml').getroot().iter('testcase'))
assert len(tests)==158 and all(not any(c.tag in ['failure','error','skipped'] for c in t) for t in tests)
old_files=read(source/'FILES.json')['files']
assert all(sha(source/row['path'])==row['sha256'] for row in old_files)
base=json.loads(subprocess.check_output(['git','show','75f70f5d:prompts/agent/registry.json'],cwd=root))
current=read(root/'prompts/agent/registry.json')
assert current['templates'][:-1]==base['templates']
new=root/'prompts/agent/design-brief-v2.9.md';old=root/'prompts/agent/design-brief-v2.7.md'
assert new.read_bytes()==old.read_bytes().replace(b'text2ifc/design-brief/2.0 Schema',b'text2ifc/design-brief/2.3 Schema')
linked=[]
for name in ['REPORT.md','README.md']:
    for p in re.findall(r'\]\(([^)]+)\)',(out/name).read_text(encoding='utf-8')):
        if '://' not in p:
            if p!='validation/verification.json':assert (out/p).exists(),p
            linked.append(p)
compiled=subprocess.run([sys.executable,'-m','compileall','-q',str(root/'src/text2ifc_agent/live_pipeline.py'),
    str(root/'src/text2ifc_agent/design_brief.py'),str(out)],capture_output=True)
assert compiled.returncode==0
(validation/'compileall-final.log').write_bytes(compiled.stdout+compiled.stderr)
scan=scan_path(out);assert scan['finding_count']==0,scan['findings']
write(validation/'verification.json',dict(status='passed',post_prompt_fix_tests=158,
    pre_live_effective_tests=220,full_preflight=False,old_c_frozen_files_unchanged=len(old_files),
    prompt_change='Only final schema version literal; prior registry entries unchanged.',
    installation_diagnostic='Initial new registry entry lacked sha256 prefix; registry failed closed; fixed before final158 checks. Intermediate failed logs retained. No real call used that intermediate registry.',
    links_checked=len(linked),scan=scan,live_response_count_this_diagnostic=1,
    live_used_prompt='design-brief.v2.7',new_prompt_v2_9_live=False))
files=[]
for p in sorted(out.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
        files.append(dict(path=p.relative_to(out).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write(out/'FILES.json',dict(status='single_stage_diagnostic_completed_no_ifc_or_proof',files=files))
paths=[(out/row['path']).relative_to(root).as_posix() for row in files]+[(out/'FILES.json').relative_to(root).as_posix(),
    'docs/architecture/semantic-appearance-plan.md']
(root/'.tmp/brief-debug-pathspec.nul').write_bytes(('\0'.join(paths)+'\0').encode())
print(json.dumps(dict(files=len(files),bytes=sum(r['bytes'] for r in files),scan_findings=0,links=len(linked),old_c_unchanged=len(old_files))))
