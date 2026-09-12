# A 分支真实运行：已停止，尚无新 IFC

**本次运行失败，不能进入待验收 Proof。** 4次真实调用后终止为 `audit_blocked`，没有编译发布 IFC。B 尚未启动：A 暴露的修复范围映射和跨层名称检查缺口属于共用路径，需要先离线修复。

## 输入与实际运行

[原请求](request.txt)与旧例相同；[追加澄清](clarification.txt)选择内部调整，隔墙西移300毫米，两段楼梯错开；[完整对话](conversation.json)标明用户授权的测试脚本来源。旧 IFC 仅作为参考，原始 IFC 文件没有发送 Provider。

默认 `legacy_full`；请求模型 `deepseek-v4-flash`，响应元数据为 `deepseek-flash`，目的地 `api.deepseek.com`。会话 `48dcf264b1a6df16`。

| 阶段 | 真实响应 ID | reported token | Provider 活动秒数 |
| --- | --- | ---: | ---: |
| design-brief | `c302b904-4c8c-4fe2-ae76-06e35753bdfe` | 43,558 | 99.250 |
| generate | `dcf6610d-a2e1-4ff3-bc99-3d9d88106f8c` | 102,128 | 232.453 |
| audit | `ff549e10-88a9-44f7-8514-11afa1feccbf` | 60,968 | 41.172 |
| changeset | `a201baad-b735-4215-9861-bd67ef9f648f` | 81,808 | 73.875 |

共 **288,462 token，446.750秒 Provider 活动时间**；墙钟约456.806秒。预留额度没有计入实际用量。没有人工候选替代、合成成功或 IFC 手工补救。

## 在哪里停止，原因是什么

1. Brief 首次 ready，结构检查通过，已提取修订后的隔墙、空间、楼梯及洞口坐标。
2. 首个 Generator 候选通过 JSON 合同，但材料门禁拒绝18个 Type 上未授权作用域的材料；因此未进入成功编译发布。相关错误在不同门禁中重复呈现，不能当成36个独立材料问题。
3. 名称门禁还把“第一段楼梯（首层至二层）”“第二段楼梯（二层至三层）”中的合法到达层文字当成归属错误。独立重放表明，这两处到达层均与冻结起止层一致；这是名称检查的误报，不能据此说楼梯真的放错层。
4. Audit 3.0 保留用户决定、参考问题和 `not_verified`，遵守阻断门禁，未声称布局已通过工程审查。
5. ChangeSet 返回合法 Draft：门禁指向 `/materials`，但 normalizer 把具体字段统一写成 `#/attributes`，导致 CHANGE_SCOPE 不允许修改材料。模型选择不越权并提出澄清。这里缺少的是内部正确修复范围，不是用户再次批准建筑设计。

[离线复现](offline-failure-diagnosis.json)用原始候选／门禁重放，确认18个 Type 的修复路径不可达、2个楼梯名称误报；补充的4个合成边界探针中3项不满足目标不变量、1项未知目标保全通过。只是失败定位，未修改生产代码，也不声称已修好或能力提升。原运行文件哈希核对不变。

## 下一步的小步修复

- 保留确定性报错的组件 ID 和精确 JSON 字段路径，材料问题只开放对应材料字段；未知／冲突目标保持阻断，不扩为整实体权限。覆盖实例／Type、不同场景、嵌套字段、多个目标和非法路径，再验证公共 ChangeSet 应用／回滚与范围外保全。
- 楼梯名称检查应结合已经确认的起止楼层，允许描述合法终点，同时继续阻断无关楼层名称及真实错误归属；不靠删除合法人类名称掩盖检查器缺陷。
- 适用测试和新的准入通过之后，才可继续剩余有界运行；不得重置已有调用预算。B 的原授权仍有效但尚未使用，当前共用缺陷先阻断执行。

## 证据和边界

- [原始公共报告](runtime/runs/48dcf264b1a6df16/report.md)、[首次候选](runtime/runs/48dcf264b1a6df16/generator/candidate.json)、[Audit](runtime/runs/48dcf264b1a6df16/audit/audit-report.json)、[ChangeSet Draft](runtime/runs/48dcf264b1a6df16/changeset-round-01/draft.json)。原始报告仍沿用历史 Mimo 标题，实际 Provider 以本次响应元数据为准。
- [预算](runtime/runs/48dcf264b1a6df16/generation-budget.json)、[终端执行结果](execution.json)、[暂停原因](../RUN-HOLD.json)、[敏感信息扫描](../live-artifact-scan.json)（0项发现）。
- 没有新增 IFC，因此没有本次 IFC 重读、净空测量或真实模型图片；不复用旧图伪称新结果。旧请求和 IFC 哈希不变。
- 运行前离线准入有效；live 暴露共用确定性缺陷后，后续调用暂停。没有执行 Full Preflight。未登记 Proof、未进行新模型人工验收、未推送 GitHub。
