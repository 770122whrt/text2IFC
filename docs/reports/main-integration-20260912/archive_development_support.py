"""Archive reviewed local development support; never execute or delete sources."""
from pathlib import Path
import json,hashlib,zipfile
from text2ifc_agent.artifact_scan import SECRET_PATTERNS, ALLOWED_ENV_NAMES
ROOT=Path("E:/code for project/bimnet")
REPO=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parent
DEST=REPO/"dataset/processed/experiments/development-support-20260912"
record=json.loads((REPORT/"local-scratch-files.json").read_text(encoding="utf-8"))
accepted=[];excluded=[]
for item in record["files"]:
    if item["matching_archives"]:continue
    p=ROOT/item["path"]
    if any(term in p.name.lower() for term in ("codex", "session-recovery")):
        excluded.append({"path":item["path"],"reason":"outside project scope: session recovery"});continue
    findings=[]
    with p.open("r",encoding="utf-8",errors="replace") as stream:
        for line_no,line in enumerate(stream,1):
            for env in ALLOWED_ENV_NAMES:line=line.replace(env,"")
            for code,pattern in SECRET_PATTERNS:
                if pattern.search(line):findings.append({"line":line_no,"code":code})
    if findings:
        excluded.append({"path":item["path"],"reason":"scan findings: preserve locally pending review", "findings":findings});continue
    with p.open("rb") as f:digest=hashlib.file_digest(f,"sha256").hexdigest()
    if digest!=item["sha256"]:raise ValueError("source changed: "+str(p))
    accepted.append(item)
DEST.mkdir(parents=True,exist_ok=False)
zip_path=DEST/"historical-support.zip"
with zipfile.ZipFile(zip_path,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for item in accepted:z.write(ROOT/item["path"],item["path"])
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    for item in accepted:
        with z.open(item["path"]) as f:assert hashlib.file_digest(f,"sha256").hexdigest()==item["sha256"]
manifest={"status":"archived_development_support_not_accepted_proof","source_root":str(ROOT),"provider_calls_this_task":0,"source_files_deleted":False,"archive":"historical-support.zip","files":accepted,"excluded":excluded}
(DEST/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
(DEST/"README.md").write_text("# 历史开发辅助材料\n\n收纳尚未在 Proof / experiments 找到同哈希副本的旧临时脚本、测试日志、XML 结果及暂存路径记录。它们按原字节打包，不属于生产入口，不自动构成系统能力或验收证据；脚本只供阅读，不应直接重新执行。已发布的实验结论仍以原集合为准。\n\n文件名、原路径、大小及 SHA-256 见 manifest.json；historical-support.zip 按原 .tmp 相对路径还原。扫描发现项和会话恢复材料留在原地，未打包；本轮不删除这些唯一来源，待备份推送后另行确认。\n",encoding="utf-8",newline="\n")
print(json.dumps({"archived_files":len(accepted),"excluded_files":len(excluded),"original_bytes":sum(x["bytes"] for x in accepted),"zip_bytes":zip_path.stat().st_size}))
