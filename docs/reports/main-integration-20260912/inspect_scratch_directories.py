"""Inventory local scratch directories without following links or active worktrees."""
from pathlib import Path
import os,json,collections
ROOT=Path("E:/code for project/bimnet/.tmp")
OUT=Path(__file__).resolve().parent
rows=[]
for top in ROOT.iterdir():
    if not top.is_dir() or top.name=="main-integration-20260912":continue
    errors=[];count=0;size=0;sample=[];linked=[];suffixes=collections.Counter()
    if top.is_symlink() or top.is_junction():
        rows.append({"path":str(top),"classification":"linked_path_preserve"});continue
    for parent,dirs,names in os.walk(top,followlinks=False,onerror=lambda e:errors.append(str(e))):
        for d in list(dirs):
            p=Path(parent)/d
            if p.is_symlink() or p.is_junction():linked.append(str(p));dirs.remove(d)
        for name in names:
            p=Path(parent)/name
            try:
                if p.is_symlink():linked.append(str(p));continue
                count+=1;size+=p.stat().st_size;suffixes[p.suffix]+=1
                if len(sample)<8:sample.append(p.relative_to(top).as_posix())
            except OSError as e:errors.append(str(e))
    classification="preserve_permission_or_link_uncertainty" if errors or linked else "readable_requires_provenance_review"
    rows.append({"path":str(top),"files_observed":count,"bytes_observed":size,"errors":errors,"linked":linked,"sample":sample,"suffixes":dict(suffixes),"classification":classification})
(OUT/"scratch-directories.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"directories":len(rows),"inaccessible_or_linked":sum(x["classification"]!="readable_requires_provenance_review" for x in rows),"observed_bytes":sum(x.get("bytes_observed",0) for x in rows)}))
