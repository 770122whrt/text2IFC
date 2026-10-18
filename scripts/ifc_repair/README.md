# Repair 运行与维护入口

通用产品入口是 [`repair.py`](repair.py)／[`text2ifc_ifc_repair.cli`](../../src/text2ifc_ifc_repair/cli.py)。下面的专项执行器按用途维护，不能替代产品 API 或证明当前阶段已具备真实调用准入。

| 目录 | 职责 | 例子 |
|---|---|---|
| [uat/](uat/) | 有界验收执行器，含离线／真实模式及准入门 | [Phase 12](uat/run_phase12_live_uat.py)、[R1](uat/run_repair_milestone_r1.py) |
| [offline/](offline/) | 离线案例、确定性公共修复与回归矩阵 | [结构修复](offline/run_phase12_public_structural_repair.py) |
| [curators/](curators/) | 证据核对、暂存与验收安装 | [Phase 12](curators/curate_phase12_live_proof.py)、[R1](curators/curate_repair_milestone_r1_proof.py) |
| [audits/](audits/) | 兼容性、比较器测量与已授权运行续接工具 | [比较器测量](audits/run_phase10_4_comparator_benchmark.py) |
| [composite_evidence/](composite_evidence/) | C1–C5 等组合修复证据链 | 保留当前已合并实现与结构 |
| [repair_comparison/](repair_comparison/) | 四组题包、隔离执行、预算与记录 | [prepare.py](repair_comparison/prepare.py)、[batch_operator.py](repair_comparison/batch_operator.py)；真实调用须有当前阶段准入和预算授权，见[题包与执行边界](../../docs/validation/repair-comparison/README.md) |

25 个原顶层入口保留为兼容转发，Python 普通导入指向同一实现，原命令仍可用。新代码优先引用上述分类目录。v2 专项、诊断和 assembler 暂留当前位置，它们继续使用兼容导入；不要为目录整齐修改冻结运行或准入路径。

2026-10-10 退役了四个 `run_r1_*_genuine_diagnostic.py` 及 `composite_evidence/regen_damage_restoration_reports.py`、`reverify_live_contracts.py`：它们只诊断或改写已完成的旧运行，没有当前调用。原文按[固定 Git 修订](../../dataset/processed/experiments/README.md#repair-旧材料按需从-git-恢复2026-10-10)恢复。冻结 Composite 指纹仍保留原字节；历史重放必须恢复对应版本，不能复用其准入作为当前 Harness 的准入。

Proof 集合校验、Door 独立审计和 transcript 审计实现在 [`src/text2ifc_proof/`](../../src/text2ifc_proof/)，旧 `validate_success_cases.py` 与 `audit_door_repair_triplet.py` 保留命令兼容。人读 Proof 的映射与布局工具仍在 [`scripts/proof/`](../proof/)。

示例（仅查看用法，不启动 Provider）：

```powershell
.\.venv\Scripts\python.exe scripts/ifc_repair/uat/run_phase12_live_uat.py --help
.\.venv\Scripts\python.exe scripts/ifc_repair/validate_success_cases.py --help
```

结构迁移不延续旧真实调用授权。当前 changed-scope 校验还必须绑定新实现与共享审计模块的哈希，缺失或不匹配继续失败关闭；不修改历史准入文件。[本次接入与验证记录](../../docs/reports/zcode-refactor-adoption-20260913/REPORT.md)。

## 四组实验的新批次

新批次使用`formal_workflow freeze-execution`，从已审题卡生成固定预算，保留指标待定状态。预算权威见[计划§8.1](../../docs/validation/repair-comparison/plan.md#81-按任务分配与动态调整)，D搜索配置与验收见[DSH接线§14](../../docs/validation/repair-comparison/deepseek-harness-integration.md#14-原生-web-search-接线)。旧冻结文件继续验证，不运行原位迁移。

```powershell
.\.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.formal_workflow freeze-execution --cases dataset/processed/ifc-repair/repair-comparison/formal --output .tmp/NEW-BATCH/plan.json --case-ids formal-011 formal-012 --total-token-limit 20000000 --b .tmp/APPROVED-B-PROPERTY-CONFIG.json --d-web-search
```

示例路径需换为本次新目录和已有B配置；命令只冻结，不调用模型。新执行计划拥有本批预算与指标待定状态，不改写已审题卡或旧冻结预算。默认将B最终检验修正次数冻结为2；可在冻结时用`--b-validation-corrections 0`或`1`选择较低上限。完整四组真实调用仍须有匹配配置和当前代码的阶段准入。D原生搜索新接线未经实际运行时验收时，不能沿用旧准入启动该变体。

初始化后交给`batch_operator`持续执行，脚本处理等待、只在变化时写摘要、累计全部尝试并按总预算停止；Codex处理完成或异常，不持续读取完整日志。

```powershell
.\.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator --root .tmp/NEW-BATCH
```

该命令仅在完成准入、实际初始化且本批已有费用授权后使用。源IFC、私有隔离、唯一发布和失败证据合同保持。

## UI 接入与版本维护

UI 调用 [RepairAPI](../../src/text2ifc_ifc_repair/api.py)；CLI 使用上方产品入口。`repair_comparison`、dataset 制作、历史 UAT 和 curator 是实验/维护工具，不是 UI 业务入口。

Prompt 版本由 [registry.json](../../prompts/agent/registry.json)和 [operation profiles](../../src/text2ifc_ifc_repair/prompt_profiles.py)加载。现有 19 份 Repair 模板、21 个 profile 与 58 个 few-shot 均有注册/引用，保留冻结重放和回归兼容所需的旧版本。dataset 的 `prompts_v3` 依赖 `prompts_v2` 与基础 `prompts`，不能只留下后缀最大的文件。当前选用版本以运行配置、默认代码和冻结记录为准。

2026-10-17 实际退役五个无当前调用者的一次性脚本：`checkpoint_stopped_batch.py`、`prepare_initial_audit.py`、`report_initial_dataset_audit.py`、`composite_evidence/curate_damage_restoration.py`、`composite_evidence/finalize_proof_pack.py`。前三者固化已完成批次的停止/首批审计，后两者操作已退役的旧 Proof 目录；既有报告、生成器哈希和冻结证据保留。原始代码从[固定 Git 版本](https://github.com/770122whrt/text2IFC/tree/48f32bba4c1976178a97267a98e569080f44063e/scripts/ifc_repair)恢复，不能作为新的产品入口。
