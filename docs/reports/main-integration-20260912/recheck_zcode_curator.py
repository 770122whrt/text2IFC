"""Re-run the full curator against hash-checked extracted historical inputs.

Only path relocation is adapted; frozen input bytes and acceptance checks stay
unchanged. Never executes a Provider or writes to the frozen Proof collection.
"""
from pathlib import Path, PureWindowsPath
import json,zipfile,hashlib,shutil,traceback
from scripts.proof.package import contained, digest
from scripts.ifc_repair.composite_evidence import curate_damage_restoration_c1_c5 as curator
ROOT=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parent
LEGACY=ROOT/"dataset/processed/proof/repair-damage-restoration/c1-c5-live-20260904-combined"
WORK=ROOT/".tmp/zcode-curator-revalidation-01"
ARCHIVE=ROOT/"archive/zcode-local-20260905/worktree-evidence.zip"
RUNS=["repair-damage-restoration-c1-c2-live-20260904-v9", "repair-damage-restoration-c3-c5-live-20260904-v7"]
OLD=PureWindowsPath("E:/code for project/bimnet-zcode/w")

def main():
    WORK.mkdir(parents=True,exist_ok=False)
    hashes={}
    prefixes=[f"w/dataset/processed/ifc-repair-runs/{run}/" for run in RUNS]
    with zipfile.ZipFile(ARCHIVE) as archive:
        for info in archive.infolist():
            if info.is_dir() or not any(info.filename.startswith(p) for p in prefixes):continue
            # contained rejects traversal, absolute names and symlinks in destination.
            if (info.external_attr>>16)&0o170000==0o120000:raise ValueError("archive symlink")
            relative=info.filename.removeprefix("w/")
            target=contained(WORK,relative);target.parent.mkdir(parents=True,exist_ok=True)
            with archive.open(info) as src,target.open("xb") as dst:shutil.copyfileobj(src,dst)
            hashes[relative]=digest(target)
    frozen=json.loads((LEGACY/"freeze.json").read_text(encoding="utf-8"))
    assert frozen==curator.FREEZE
    for case in frozen["cases"]:
        source=LEGACY/case["case_id"]/"01-original.ifc"
        target=contained(WORK,case["source"]);target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copyfile(source,target)
        assert digest(source)==digest(target)
    execution=json.loads((LEGACY/"source-runs/batch-01/execution-result.json").read_text(encoding="utf-8"))
    target=contained(WORK,execution["preflight"]["evidence_path"]);target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(LEGACY/"source-runs/batch-01/preflight.json",target)
    original_inside=curator._inside
    def relocate_inside(path, case_root):
        recorded=PureWindowsPath(str(path))
        try:relative=recorded.relative_to(OLD).as_posix()
        except ValueError:return original_inside(path,case_root)
        mapped=contained(WORK,relative)
        if relative not in hashes or digest(mapped)!=hashes[relative]:raise ValueError("RELOCATED_ARCHIVE_HASH_MISMATCH")
        return original_inside(mapped,case_root)
    curator.ROOT=WORK
    curator._inside=relocate_inside
    mapping={f"C{i}":WORK/"dataset/processed/ifc-repair-runs"/RUNS[0 if i<3 else 1]/"cases"/f"C{i}" for i in range(1,6)}
    result=curator.curate_case_runs(case_run_roots=mapping,proof_root=WORK/"recomputed-proof")
    unchanged=all(digest(WORK/relative)==sha for relative,sha in hashes.items())
    assert unchanged
    report={"status":result["status"],"scope":"Full curator with hash-checked archive path relocation; no frozen record edits", "provider_calls":0,"source_files":len(hashes),"source_bytes_unchanged":unchanged,"cases":result["cases"],"output":str(WORK/"recomputed-proof")}
    (REPORT/"zcode-full-curator.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"status":result["status"],"cases":len(result["cases"]),"source_bytes_unchanged":unchanged}))

if __name__=="__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
