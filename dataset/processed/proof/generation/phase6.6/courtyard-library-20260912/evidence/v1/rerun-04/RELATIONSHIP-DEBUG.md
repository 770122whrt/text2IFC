# 门窗关系恢复边界

真实运行 `3cd339b0be4fd872` 在 Brief 原始响应和一次语义修正后进入 Generator；整栋 JSON 完整返回。55 个 basic_filling 均缺少 IfcRelFillsElement，相应墙洞口也缺少 IfcRelVoidsElement。严格校验正确阻断，Repair 将 BASIC_FILLING_CONSTRAINT_CONFLICT 归为不可修复，未调用修复 Provider；旧整楼 scaffold 因缺少其固定 building.width 字段而停止。没有 IFC 发布。

按顺序排查：候选是否真的漏关系（已确认）；新版本是否遗漏关系校验接入（否，校验正常运行）；是否仅关系缺失且存在充分明确事实（待离线复算）；是否还有被首条错误遮住的尺寸或宿主冲突（待完整复验）。不修改 Prompt、Schema 或检查容差，也不增加案例别名。

小步修复合同：仅 Generation 的 basic_filling、BIM JSON2.1/2.2。在冻结 Brief 的 canonical identity 投影、明确 host_wall 和候选放置父链一致时，允许补缺失 void/fill；不推断几何位置决定宿主，不修改实体、不改写既有关系。候选重复身份、关系冲突、共享洞口、多重宿主、放置不一致、缺少 Brief 事实或完整验证仍失败时整批不应用。保留原候选与追加关系及来源记录。此路径不能用于修补任意外部 Repair IFC。

失败族先冻结为 tests/agent/test_filling_relationship_recovery.py：四个模板、两种合同、missing fill/void/both、多个目标、任一目标冲突整批回滚、合法已有关联、不同场景标识及公开 Repair seam。原真实响应只做离线诊断，不能作为盲测或新 Provider 输出。最终仍须编译、重开、全候选语义与几何检查及 Audit。
