"""Read-only inventory; never infer emptiness after enumeration errors."""
from pathlib import Path
import os, json, hashlib, collections
ROOT = Path(r"E:/code for project/bimnet")
OUT = Path(__file__).resolve().parent
errors=[]
def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
files=[]
for p in (ROOT / ".tmp").iterdir():
    if not p.is_file():continue
    try:files.append({"path":p.relative_to(ROOT).as_posix(), "bytes":p.stat().st_size,"sha256":sha(p)})
    except OSError as e:errors.append({"path":str(p),"error":str(e)})
by_size=collections.defaultdict(list)
for item in files:by_size[item["bytes"]].append(item)
matched=collections.defaultdict(list)
for base in [ROOT/"dataset/processed/proof", ROOT/"dataset/processed/experiments", ROOT/"docs/reports"]:
    for parent,dirs,names in os.walk(base, followlinks=False,onerror=lambda e:errors.append({"path":str(e.filename),"error":str(e)})):
        dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
        for name in names:
            p=Path(parent)/name
            try:
                if p.stat().st_size not in by_size:continue
                digest=sha(p)
                for item in by_size[p.stat().st_size]:
                    if item["sha256"]==digest:matched[item["path"]].append(p.relative_to(ROOT).as_posix())
            except OSError as e:errors.append({"path":str(p),"error":str(e)})
for item in files:
    item["matching_archives"]=matched[item["path"]]
    item["disposition"]="duplicate_candidate_pending_reference_check" if item["matching_archives"] else "preserve_pending_content_review"
result={"scope":"Only immediate scratch files; directories and active integration worktree excluded", "files":files,"errors":errors}
(OUT/"local-scratch-files.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"files":len(files),"bytes":sum(x["bytes"] for x in files),"archive_matches":sum(bool(x["matching_archives"]) for x in files),"errors":len(errors)}))
