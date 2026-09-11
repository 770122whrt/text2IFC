# 六构件混合修复

状态：**pending_human_review**。来源运行和机器检查为 **PASS**；本次归档不代替你的视觉审查，不新增模型能力结论。

## 请求、损伤与实际修改

公共请求：[request.txt](request.txt)。修复输入：[02-damaged.ifc](02-damaged.ifc)。

输入删除 2 Window、2 Door、1 Beam、1 Column。Provider 在公共输入中选择目标、类型及材质颜色；确定性代码原子应用六项操作。第一组窗门为深灰铝合金 RGB (0.18,0.20,0.22)，第二组为浅橡木 RGB (0.72,0.45,0.24)；梁柱复用存活类型。

[01-original.ifc](01-original.ifc) 是修复前已有 canonical VVO 物理对照。它仅供修复后评估，不是根据 repaired 补造的 case-specific private Gold。公开请求中明确给出的参数属于本次授权输入；原始删除身份、变异配方及原件对照事实不应被解释为 Provider 自主推断能力。

## 输出与结论

成功发布文件：[03-repaired.ifc](03-repaired.ifc)。包内哈希由 [冻结 authority](evidence/frozen/authority.json) 绑定，源记录声明与 terminal 发布内容相同。

| 维度 | 原记录与限制 |
|---|---|
| Provider 语义 | genuine Stage 1 / Stage 2；选择见 repair-intent、resolution 和 bound-changeset |
| 确定性执行 | application passed；successful_artifact_publishable=true |
| 产物 | succeeded、complete_repair_success=true；不是 staging candidate |
| 证据合同 | proof-check passed；冻结四份根文件哈希。完整失败历史仍在源工作目录，不属于本包覆盖范围 |
| L0 / L1 / L2 | public-evaluation 记录强制 L1/L2 通过；L0 未单独汇总，写未知，不从输出存在推断 |
| atomicity / preservation | 原报告记录原子应用；public-evaluation preservation passed；失败回滚不是此单个成功案例的验证范围 |
| reopen | 来源报告已有重开检查；本次额外验证三份 IFC2X3 均可打开 |
| IFCCompare | 原件—损坏—修复物理比较适用；仓库比较器记录不等同于另行运行第三方 IFCCompare。本次未运行它 |
| genuine run ID | `repair-9c96869574ac414bb8af8d857055e0bb` |
| 本成功运行调用次数 | 2（Stage 1=1、Stage 2=1；不含源目录其他失败尝试） |
| 人工审查 | 待审；请核对几何、材质、颜色及非目标构件是否符合请求 |

完整机器材料：[evidence/README.md](evidence/README.md)。[原英文报告](evidence/frozen/source-REPORT.md)保留原文字节和更详细的原结论。本集合按 Phase 12 的结构/混合 repair 工作流组织，不改变 Phase 12 或 12.1 的关闭状态。
