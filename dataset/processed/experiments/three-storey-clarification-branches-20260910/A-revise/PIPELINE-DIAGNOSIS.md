# 从实际失败区分 Prompt、Schema 与控制链路

**主阻断在确定性的错误路径转换与修复范围接入；首个候选还存在指令执行偏差和请求约束检查不完整。现有 Schema 能表达本次材料修复，无需为这一缺陷重构整个 Schema。**

本次仅诊断，没有新增 Provider 调用、生产代码修改、成功 IFC 或新的准入。原始请求、候选、Scope、Prompt、Expected Facts 和失败响应保持不变。

## 逐环节证据

| 环节 | 实际观察 | 判断 |
| --- | --- | --- |
| 用户对话 → Brief／冻结预期 | 追加澄清中的布局已进入 Brief；材料预期绑定实例且为 direct；Type 预期为0。合并冻结／当前投影后有38条材料记录，对应19个实例的重复约束，并非38个材料对象。 | 本次不是遗漏布局澄清或 Type 请求被错误提取。 |
| Generator Prompt／输入合同 | 实际发送的 Prompt 包含“未请求 Type 时不生成额外 Type 或 Style”；IFC_AUTHORING_CONTRACT 也明确要求省略，合法最小门样式由编译器处理。 | 不能归因于忘记发送该指令；单次响应无法证明具体措辞、上下文长度或模型偏好的因果关系。 |
| Generator 候选 | 创建15个 IfcWallType、3个 IfcSlabType、4个 IfcDoorStyle、15个 IfcWindowStyle，共37个显式类型对象。18个墙／板 Type 被附加分层材料；其关联实例已有请求的单材料。 | 模型没有遵守“不额外创建 Type”的指令，且扩大了材料作用域／表达；不能把类型材料当作满足实例直接材料要求的必要步骤。 |
| Schema／材料门禁 | 通用 BIM JSON 2.1 合同允许 Type、材料和空材料数组；请求门禁只允许已冻结实体身份的材料／属性，因而拒绝18处类型材料。 | Schema 的“合法表达”不同于当前请求的“授权表达”；此处材料拒绝与冻结 direct 实例作用域一致。 |
| 名称门禁 | 将“首层至二层”“二层至三层”的到达层名称识别为归属冲突，虽然 Expected Facts 的 from_storey／to_storey 与之相符。 | 确定性检查器误报；不能要求用户重写合法跨层描述。 |
| Gate → Issue → Change Scope | Gate 为 `/entities/<type>/materials`，`_targeted_issues` 保留实体 ID 却统一改成 `entity:<type>#/attributes`。Scope 随后忠实采用这个错误范围。 | 这是直接导致 loop 无法修材料的确定性缺陷。 |
| ChangeSet Prompt／Schema／响应 | Prompt 明确不能越出 Scope，无法修复须返回 Draft；真实响应准确指出 `/materials` 不在授权范围，并保持无写入。 | 本次修复 Agent 的拒绝越权符合合同，不应靠要求它更“大胆”来绕过。 |
| Audit／终端 | 新 Audit 保留用户决定及 `not_verified`，尊重硬门；终端未发布 IFC。 | 本次问题不是 Audit 静默抹掉问题或最终放行了坏模型。 |

## 隔离变量的离线对照

使用原始失败候选和原 revision，手工构造**仅作诊断**的18项 ChangeSet：各 Type 的 `/materials` 改为空数组，保留实例单材料。此 JSON 不是 Provider 输出，不保存为生成模型，不编译成展示 IFC。

1. ChangeSet Schema 与证据引用校验通过。
2. 在原 Scope 下应用：失败，18项 `CHANGESET_SCOPE_VIOLATION`。
3. 对诊断副本只将这18个目标的权限改为精确 `/materials`，其他输入与 ChangeSet 相同：实际 `apply_changeset` 成功，结果通过 BIM JSON 合同，材料越权问题归零。
4. 实际组件哈希变化恰好是这18个 Type，其他实体及关系无变化；原候选、原 Scope、原 Brief 等源文件哈希不变。

这证明本次材料字段无需新增 Schema 操作，卡点在 Scope 接入。该探针没有执行 Compiler／IFC 重读，且仍保留37个额外 Type，**不能称为完整产品修复或最终验收成功**。探针首轮因手写 evidence_refs 使用错误前缀而失败，修正诊断夹具后才完成上述对照，不计为产品失败。

机器结果：[pipeline-localization.json](pipeline-localization.json)。复现脚本：[localize_branch_pipeline.py](../localize_branch_pipeline.py)，使用仓库 `.venv`，第一个参数为一个尚不存在的新 JSON 输出路径。历史失败族及楼梯误报重放见 [offline-failure-diagnosis.json](offline-failure-diagnosis.json)。

## 比上轮诊断新增的结论

只修正材料路径仍不够：在诊断副本清空类型材料之后，当前语义禁止补值检查不再报错，但额外37个 Type 仍在。代码主要实施了材料／属性的请求白名单，未在该检查中完整实施 Prompt 的无请求 Type 政策。该结论仅针对当前检查，不声称其余全部最终发布路径一定会放行这37个 Type。

因此首轮生成质量不能只靠 Prompt；需要把已经批准的无请求 Type 边界落实为请求级语义合同。通用 Schema 仍应允许其他合法的、有明确 Type 请求的案例。

## 建议的小步顺序

1. **先修确定性接入**：结构化保留组件身份和精确字段路径；检验报错字段是否在修复 Scope 中可达。证据不充分或映射冲突时在调用前进入工程诊断，不让模型替系统向用户索要内部权限。不把所有错误都压成 geometry_invalid／attributes。
2. **修名称适用性**：依据冻结起止层及真实归属处理跨层构件；保留无关楼层、错误归属、身份歧义等负例。不要通过统一改名规避误报。
3. **补请求级 Type 检查**：区分明确请求的 Type 与编译器最小附件，阻止 Generator 自建未经请求的额外 Type／Style；为其关联关系建立准确、受限、可回滚的纠错范围。不能简单禁止所有 Type 或放宽材料授权。
4. **最后评估 Prompt／输入精简**：现有禁止指令已经存在，优先给模型提供清晰且可校验的请求事实、写入范围和只读依赖；有需要时新增窄版本或动态请求限制。以冻结相关案例族验证，不根据一次响应立即重写全部 Prompt／Schema。

依据入口：`src/text2ifc_agent/issue_normalizers.py::_targeted_issues`、`change_scope.py::derive_change_scope`、`semantic_requirements.py::unauthorized_candidate_semantics`、`dynamic_gates.py::_storey_name_consistency_gate`、`changeset_apply.py::apply_changeset`；实际 Prompt 为 `bim-json-generator.v2.2` 与 `bim-json-changeset.v1.5`，已有版本未修改。
