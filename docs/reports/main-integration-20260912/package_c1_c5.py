"""Build current navigation without modifying historical C1-C5 evidence."""
from pathlib import Path
import json
from scripts.proof.package import capture_bundle, digest, validate_package
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/"dataset/processed/proof/repair-damage-restoration/c1-c5-live-20260904-combined"
DEST=ROOT/"dataset/processed/proof/repair/phase12/c1-c5-damage-restoration"
DEST.mkdir(parents=True,exist_ok=False)
mapping={}
for i in range(1,6):
    case=f"C{i}"
    for name in ("01-original.ifc","02-damaged.ifc","03-repaired.ifc"):mapping[f"{case}/{name}"]=f"{case}/{name}"
    mapping[f"{case}/input/request.txt"]=f"{case}/request.txt"
bundle=capture_bundle(OLD,DEST,"frozen",mapping)
bundle["old_root"]=OLD.relative_to(ROOT).as_posix()
legacy=json.loads((OLD/"manifest.json").read_text(encoding="utf-8"))
calls={}
for p in (OLD/"source-runs").glob("*/execution-result.json"):
    for case in json.loads(p.read_text(encoding="utf-8"))["cases"]:calls[case["case_id"]]=case["genuine_provider_calls"]
cases=[]
for oldcase in legacy["cases"]:
    key=oldcase["case_id"];root=DEST/key
    artifacts={}
    for name in ("01-original.ifc","02-damaged.ifc","03-repaired.ifc","request.txt"):
        p=root/name
        artifacts[name]={"source":f"{key}/{name}","sha256":digest(p),"size_bytes":p.stat().st_size}
    (root/"evidence").mkdir(exist_ok=True)
    (root/"evidence/README.md").write_text(f"# 历史证据\n\n完整原记录位于 [冻结权威](../../evidence/frozen/{key}/manifest.json)。原报告、FILES和所有Provider记录按原字节保留；旧路径由集合manifest.json映射。本轮检查结果位于 docs/reports/main-integration-20260912，不覆盖历史结论。\n",encoding="utf-8",newline="\n")
    (root/"REPORT.md").write_text(f"# {key} 损坏与修复对照\n\n本案为Zcode已接受的历史真实Provider结果，本次只整理展示，不重新调用模型、不改变验收状态。历史机器结果为 `{oldcase['status']}`，真实调用记录为 {calls[key]} 次；本次调用为0次。\n\n先读 [用户输入](request.txt)，再对照 [原始模型](01-original.ifc)、[损坏输入](02-damaged.ifc)、[修复输出](03-repaired.ifc)。原始模型是运行前冻结的损坏基准，仅供事后评价，未作为Provider输入。\n\n细节和构件GUID对应见 [原报告](../evidence/frozen/{key}/REPORT.md) 与 [完整证据入口](evidence/README.md)。原focused IFCcompare通过，整个模型GlobalId并非完全相同；不能据本案声称系统级能力提升。本轮完整curator复核与历史验收分开记录。\n",encoding="utf-8",newline="\n")
    cases.append({"case_id":key,"path":key,"status":"accepted","machine_status":oldcase["status"],"outcome":"repaired","evidence_mode":"genuine_live_provider","provider_calls":calls[key],"original_role":"private_ground_truth","authority":f"evidence/frozen/{key}/manifest.json","artifacts":artifacts})
doc={"schema_version":"text2ifc/workflow-proof-package/0.1","collection_id":"c1-c5-damage-restoration","workflow":"repair","phase":"phase12","status":"accepted","human_review":{"decision":"historical_acceptance_preserved","basis":"docs/reports/zcode-integration-20260905/REPORT.md states user-accepted C1-C5 results; no new acceptance decision"},"current_revalidation":"pending_full_curator_and_integration_preflight","legacy_bundles":[bundle],"cases":cases}
(DEST/"manifest.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
text="# C1–C5 历史修复 Proof\n\n沿用 Zcode 已接受的5案真实运行，保留142份冻结文件原字节；本轮只改导航。每案直接提供请求、原始IFC、损坏IFC和修复IFC，模型源于运行前冻结的dataset材料。当前整合的机器复核单独记录，尚未完成；历史PASS不会自动代表当前代码复验通过。\n\n"+"\n".join(f"- [{c['case_id']} 报告]({c['case_id']}/REPORT.md)" for c in cases)+"\n\n旧路径映射及所有原始哈希见manifest.json；完整历史报告位于evidence/frozen/REPORT.md。\n"
for name in ("README.md","REPORT.md"):(DEST/name).write_text(text,encoding="utf-8",newline="\n")
result=validate_package(DEST,doc,reopen=True)
(ROOT/"docs/reports/main-integration-20260912/c1-c5-human-view.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(result)
