# 接管 text2IFC

产品名为 `text2IFC`；`bimnet` 可能只是本地目录名，`BIMNet` 是数据来源。

## 先做四件事

1. 阅读根目录 [AGENTS.md](../../AGENTS.md)，确认 Git 根、分支、工作树和暂存区，保留他人的修改。
2. 阅读 [STATE](../../.planning/STATE.md)、[PROJECT](../../.planning/PROJECT.md)，按 [文档索引](../README.md)进入所需功能。
3. 为当前问题确定调用入口、受影响模块和验证范围。历史报告和完成计划不再充当当前任务指令。
4. 行为修改先保存可复现输入和失败边界，再执行针对性验证。测试恢复方式见[精简记录](../reports/lean-branch-20261007/REPORT.md)。

```sh
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git diff --cached --stat
```

## 代码地图

| 功能 | 实现 |
|---|---|
| Generation 交互与总编排 | `src/text2ifc_agent/repl_chat.py`、`interactive_cli_flow.py` |
| Brief、Expected Facts、分包 | `clarification.py`、`expected_facts.py`、`generation_packages.py`、`staged_generation.py` |
| Generation Gate／Audit／返工 | `dynamic_gates.py`、`live_pipeline.py`、`changeset_apply.py` |
| IFC Repair API／CLI | `src/text2ifc_ifc_repair/api.py`、`cli.py` |
| Repair 解析、绑定、应用和评估 | `target_query.py`、`property_resolution_coordinator.py`、`changesets.py`、`apply.py`、`production_evaluation.py` |
| IFC2Text 与往返比较 | `src/text2ifc_ifc2text/` |
| BIM JSON 合同、IFC 编译 | `src/text2ifc_contract/`、`src/text2ifc_compiler/` |
| 几何质量、材料／外观 | `src/text2ifc_quality/`、`src/text2ifc_presentation/` |
| 属性知识和数据 | `src/text2ifc_knowledge/`、`text2ifc_dataset/`、`text2ifc_text/` |
| 独立 Proof 校验 | `src/text2ifc_proof/`，不加载 Repair runner |

具体命令见 [scripts](../../scripts/README.md)。保留的旧版本入口仍可能被调用，不根据名称删除。

## 必须知道的行为

- Generation 由 Ready Brief 开始；默认 `legacy_full`，显式选择 `staged` 才分包。模型不直接写 IFC STEP。
- Generation 的 BIM JSON 返工与对已有 damaged IFC 的 Repair 是两条独立流程。
- Repair 在副本上原子应用，重开后通过 L0/L1/L2 和 preservation 才发布。失败不产生成功结果。
- 检索仅提供候选；确定性 binding／admissibility 决定是否可执行。私有 Gold 和损坏真值仅供评估。
- IFC2Text 的坐标精度、支持范围与往返误差以[当前合同和结果](../validation/ifc2text/README.md)为准。
- Phase 状态、Proof 集合状态、单次 run 状态分别报告；存在 IFC 文件不等于通过验收。

## 验证与资料

使用 Python ≥3.12 和 `.venv`。普通修改执行受影响路径的 scoped validation；真实 Provider 前遵循
[阶段准入协议](../validation/agent-capability-evaluation.md)。全仓 Full Preflight 仍需说明范围并获得用户明确授权。
缺少测试或准入时阻断真实调用，不能把静态编译当成阶段准入。

`dataset/processed/proof/` 是冻结证据；`experiments/` 是历史实验；`agent-demo/`、`ifc-repair/`、`ifc-repair-runs/`
仍有运行时或验证消费者。数据来源和许可证查 `dataset/sources/`、`dataset/manifests/`。
不要默认扫描整个数据集。仅对明确、已解析、处于授权范围内的路径执行删除。

提交前检查 diff 和验证结果，使用授权分支。交接说明修改内容、命令／结果、失败／未测项、commit 与远端状态。
