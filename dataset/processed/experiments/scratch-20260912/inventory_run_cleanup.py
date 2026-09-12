import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/reports/run-cleanup-review-20260910';OUT.mkdir(exist_ok=False)
PROOF=ROOT/'dataset/processed/proof/generation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[];index={}
for base,dirs,files in os.walk(PROOF,onerror=lambda e:errors.append(str(e))):
    for name in files:
        p=Path(base)/name
        if p.is_symlink():continue
        try:index.setdefault((p.stat().st_size,sha(p)),[]).append(p.relative_to(ROOT).as_posix())
        except OSError as error:errors.append(str(error))
targets=[ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910',
    ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909']
targets.extend(ROOT/'.tmp'/name for name in ['brief-evidence-core-final','brief-evidence-firstfail','brief-evidence-green',
    'brief-evidence-red','brief-fixture-baseline-output','brief-prompt-final','brief-registry-final','brief-version-verified','cshape-geometry-tests-20260910'])
rows=[]
for target in targets:
    assert target.resolve().is_relative_to(ROOT.resolve())
    files=[];local_errors=[];reparse=[]
    for base,dirs,names in os.walk(target,onerror=lambda e:local_errors.append(str(e))):
        for d in list(dirs):
            p=Path(base)/d
            if p.is_symlink() or (p.stat().st_file_attributes & 1024):reparse.append(str(p));dirs.remove(d)
        for name in names:
            p=Path(base)/name
            if p.is_symlink():reparse.append(str(p));continue
            try:
                size=p.stat().st_size;digest=sha(p)
                files.append(dict(path=p.relative_to(target).as_posix(),bytes=size,sha256=digest,
                                  proof_copies=index.get((size,digest),[])))
            except OSError as e:local_errors.append(str(e))
    tracked=subprocess.check_output(['git','ls-files','-z','--',target.relative_to(ROOT).as_posix()],cwd=ROOT).decode().split('\0')
    row=dict(target=target.relative_to(ROOT).as_posix(),absolute_path=str(target),files=len(files),bytes=sum(f['bytes'] for f in files),
        tracked_files=len([x for x in tracked if x]),proof_identical_files=sum(bool(f['proof_copies']) for f in files),
        uncovered_files=[f['path'] for f in files if not f['proof_copies']],file_inventory=files,errors=local_errors,reparse_points=reparse,
        proposed_action='pending_user_approval_only; no deletion performed',
        category='synthetic_pytest_temporary_outputs' if target.parent.name=='.tmp' else 'reviewed_run_source')
    rows.append(row)
payload=dict(status='inventory_only_no_deletion',head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    proof_scan_errors=errors,targets=rows,retained=['C-shaped original failure and successful Brief: active request/budget/evaluator dependencies.',
        'A/B earlier failures not copied into accepted final Proof: not proposed for deletion.'])
(OUT/'inventory.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'path':r['target'],'files':r['files'],'mb':round(r['bytes']/1048576,2),'proof_copies':r['proof_identical_files'],
    'uncovered_count':len(r['uncovered_files']),'errors':len(r['errors'])} for r in rows],ensure_ascii=False))
