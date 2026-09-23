# text2IFC Generation：Novelty 与 Claim 基础版

> **历史材料，2026-09-16已整合。** 当前方向与实验统一见[研究方案](research-plan.md)，文献统一见[简版](literature-review-short.md)和[完整版](literature-review-full.md)。下文保留调查时的结论与编号，不再作为当前优先级。

更新：2026-09-15。基于当前实现与已核实文献。这里的三项是 **Demo 系统贡献草稿**，不是三个已证明的新算法。

**后续讨论状态：** 用户指出这三点偏工程，当前将它们保留为实现基础，不再作为已选定的三项论文创新。当前综合方案见 [Motivation / Novelty / Evaluation and Experiments](research-proposal.md)，逐篇依据见 [论文矩阵](paper-matrix.md)。

## 1. 一句话定位

**text2IFC 将自然语言需求转成可检查的 IFC，并在分步生成和纠错时限制修改范围，保留可追踪的模型版本。**

我们最关心的问题是：后面生成或修改一部分时，怎样减少对前面已有正确结果的破坏，同时仍然完成任务？

## 2. 三项可以写的系统贡献

### 贡献一：从需求到 IFC 的可核验流程

系统把需求整理为 Design Brief 和验收事实，再生成 BIM JSON、编译为 IFC，并检查输出文件。

**Claim 草稿：** 我们实现了从自然语言需求到 IFC 的完整工作流，将需求表示、生成候选与最终产物的检查连接起来，便于用户查看输出是否满足受支持的要求。

这部分是系统基础。生成前提取验证要求已有 Self-Verification 等先例，不单独主张首次或原创。

### 贡献二：有写入边界的分步生成

在 staged 策略中，系统先建立骨架，再按生成包追加构件和关系。每个包有允许创建的 ID；执行器拒绝越权覆盖，并检查此前组件是否保持不变。

**Claim 草稿：** 我们将复杂模型生成组织为有明确写入所有权的生成包，使后续包在规定范围内扩展已有模型。

这是目前值得继续研究的系统区别。当前引用规则允许访问已存在的 workspace ID，不能写成“所有跨包引用均严格隔离”。局部检查通过也不代表全局正确。

### 贡献三：绑定版本的局部纠错

验证发现问题后，scoped correction 路径使用绑定模型版本的 ChangeSet。执行器检查对象、字段和操作范围，拒绝过期或越权修改，调用方随后检查编译后的 IFC。

**Claim 草稿：** 我们把验证问题连接到受限的模型修订，使每次修改都能追踪到基础版本、允许范围与后续检查结果。

当前部分恢复路径仍返回完整 BIM JSON，再检查实际变更范围。因此不能写“所有纠错都只输出局部补丁”。

## 3. 可直接使用的贡献段落

本文展示 text2IFC，一个从自然语言需求生成可检查 IFC 的系统。系统连接需求整理、模型生成、确定性编译与产物验证；在分步生成时，通过明确的写入所有权约束生成包；在局部纠错时，通过版本绑定与范围检查管理模型修改。演示可呈现需求、生成结果、验证问题及模型修订之间的对应关系。

英文简版：

> We present text2IFC, a system for generating inspectable IFC models from natural-language requirements. It connects requirement extraction, model generation, deterministic compilation, and artifact verification. Ownership checks constrain staged construction, while revision and scope checks govern local correction. The demonstration makes requirements, detected issues, permitted changes, and resulting model versions available for inspection.

“可查看”描述的是系统产物和记录，不默认声明浏览器界面、在线部署或用户实验已经完成；具体演示方式应与实际可运行界面一致。

## 4. 哪些说法暂时不能写

| 不宜使用的说法 | 更准确的说法 |
| --- | --- |
| 首次 Text-to-BIM / Text-to-IFC | 实现了一套可核验的 IFC 生成系统 |
| Agent loop 本身是创新 | 研究 loop 中具体的生成与修改约束 |
| ownership、freeze、版本管理是新机制 | 将已有机制用于当前生成流程，组合价值需要比较 |
| 保证已正确的模型永远不会被破坏 | 检查规定范围外的组件变化；完整语义与几何保全仍需评估 |
| 显著提高成功率、降低成本 | 等待同模型、同预算、同任务的实验结果 |
| 已解决复杂整栋建筑生成 | 在明确支持范围内提供案例与机制证据 |

相关先例见 [文献综述](literature-review-demo.md)，包括 Text2BIM、Self-Verification、模型访问控制、ChronoSphere 和 PRISM。

## 5. 真正的研究候选，以及最少需要补的证据

**研究候选：有写入边界和版本约束的生成/纠错流程，能否减少迭代回退，并保持或提高任务完成率？**

它目前仍是候选方向。若要从 Demo 系统贡献升级为方法贡献，最少需要：

1. 同一失败候选上比较普通纠错、提示要求局部修改、执行器强制范围；同时报告完成率、回退率与成本。
2. 从原始需求独立检查最终 IFC，防止 Brief 漏要求而下游仍显示通过。
3. 若将分包作为主贡献，比较普通分包与加入所有权/状态保护的分包，排除调用次数与输出长度的影响。

先用现有实现测这些问题。只有发现固定范围妨碍可完成任务时，再考虑补“根据验证证据扩大范围”的机制；该机制目前不是已实现的 Claim。

## 6. 当前依据

- [生成前期望](../../../src/text2ifc_agent/expected_facts.py)、[分包 Gate](../../../src/text2ifc_agent/package_gates.py)、[分步生成](../../../src/text2ifc_agent/staged_generation.py)。
- [ChangeSet 应用](../../../src/text2ifc_agent/changeset_apply.py)、[交互调用与再验证](../../../src/text2ifc_agent/interactive_cli_flow.py)、[编译后 Gate](../../../src/text2ifc_agent/live_pipeline.py)。
- [详细审核与离线测试记录](../Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md)。其中 62 项测试是相关实现行为的离线证据，不是 62 个独立建筑实验。
- [光庭案例](../../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/open-court-v2/REPORT.md)采用 `legacy_full`，没有 Provider 修复，不能作为 staged 或纠错效果的对比证据。

本次复核时 HEAD 为 `ce3309bf3ac63ed8f47d793a32bc41ebf6bf0336`，关键代码边界与前一轮审核一致；本轮没有重新运行行为测试或真实模型实验。
