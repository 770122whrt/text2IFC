"""Create a local recovery ZIP before proposing deletion of pytest workspaces."""
from pathlib import Path
import os,json,zipfile,hashlib
ROOT=Path("E:/code for project/bimnet")
REPORT=Path(__file__).resolve().parent
source=json.loads((REPORT/"pytest-directory-provenance.json").read_text(encoding="utf-8"))
selected=[d for d in source["directories"] if not d["unresolved_fixture_names"]]
backup=ROOT/".tmp/cleanup-recovery-20260912"
backup.mkdir(exist_ok=False)
archive=backup/"pytest-workspaces.zip"
records=[];counts={}
with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
    for item in selected:
        directory=Path(item["path"])
        if directory.parent!=ROOT/".tmp" or directory.is_symlink() or directory.is_junction():raise ValueError("unsafe source")
        count=0;size=0
        def onerror(error):raise error
        for parent,dirs,names in os.walk(directory,followlinks=False,onerror=onerror):
            for name in dirs:
                p=Path(parent)/name
                if p.is_symlink() or p.is_junction():raise ValueError("linked source")
            for name in names:
                p=Path(parent)/name
                if p.is_symlink():raise ValueError("linked file")
                rel=p.relative_to(ROOT).as_posix();info=p.stat();digest=hashlib.sha256()
                with p.open("rb") as src,z.open(rel,"w",force_zip64=True) as dst:
                    while chunk:=src.read(1048576):digest.update(chunk);dst.write(chunk)
                records.append({"path":rel,"bytes":info.st_size,"sha256":digest.hexdigest()});count+=1;size+=info.st_size
        if count!=item["files"] or size!=item["bytes"]:raise ValueError("directory changed during backup")
        counts[item["path"]]={"files":count,"bytes":size}
    z.writestr("RECOVERY-MANIFEST.json",json.dumps(records,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for entry in records:
        with z.open(entry["path"]) as f:assert hashlib.file_digest(f,"sha256").hexdigest()==entry["sha256"]
with archive.open("rb") as f:archive_hash=hashlib.file_digest(f,"sha256").hexdigest()
summary={"status":"backed_up_pending_user_deletion_approval","archive":str(archive),"archive_sha256":archive_hash,"archive_bytes":archive.stat().st_size,"directories":counts,"files":len(records),"original_bytes":sum(r["bytes"] for r in records),"recovery_manifest":"RECOVERY-MANIFEST.json inside ZIP","provider_calls":0,"sources_deleted":False,"scope":"All top-level fixture folders match tracked pytest function names; recoverable local backup, not accepted Proof"}
(REPORT/"pytest-workspace-recovery.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"directories":len(selected),"files":len(records),"original_bytes":summary["original_bytes"],"archive_bytes":summary["archive_bytes"]}))
