# Repair 运行与维护入口

通用产品入口是 [`repair.py`](repair.py)／[`text2ifc_ifc_repair.cli`](../../src/text2ifc_ifc_repair/cli.py)。下面的专项执行器按用途维护，不能替代产品 API 或证明当前阶段已具备真实调用准入。

| 目录 | 职责 | 例子 |
|---|---|---|
| [uat/](uat/) | 有界验收执行器，含离线／真实模式及准入门 | [Phase 12](uat/run_phase12_live_uat.py)、[R1](uat/run_repair_milestone_r1.py) |
| [offline/](offline/) | 离线案例、确定性公共修复与回归矩阵 | [结构修复](offline/run_phase12_public_structural_repair.py) |
| [curators/](curators/) | 证据核对、暂存与验收安装 | [Phase 12](curators/curate_phase12_live_proof.py)、[R1](curators/curate_repair_milestone_r1_proof.py) |
| [audits/](audits/) | 兼容性、比较器测量与已授权运行续接工具 | [比较器测量](audits/run_phase10_4_comparator_benchmark.py) |
| [composite_evidence/](composite_evidence/) | C1–C5 等组合修复证据链 | 保留当前已合并实现与结构 |

25 个原顶层入口保留为兼容转发，Python 普通导入指向同一实现，原命令仍可用。新代码优先引用上述分类目录。v2 专项、诊断和 assembler 暂留当前位置，它们继续使用兼容导入；不要为目录整齐修改冻结运行或准入路径。

Proof 集合校验、Door 独立审计和 transcript 审计实现在 [`src/text2ifc_proof/`](../../src/text2ifc_proof/)，旧 `validate_success_cases.py` 与 `audit_door_repair_triplet.py` 保留命令兼容。人读 Proof 的映射与布局工具仍在 [`scripts/proof/`](../proof/)。

示例（仅查看用法，不启动 Provider）：

```powershell
.\.venv\Scripts\python.exe scripts/ifc_repair/uat/run_phase12_live_uat.py --help
.\.venv\Scripts\python.exe scripts/ifc_repair/validate_success_cases.py --help
```

结构迁移不延续旧真实调用授权。当前 changed-scope 校验还必须绑定新实现与共享审计模块的哈希，缺失或不匹配继续失败关闭；不修改历史准入文件。[本次接入与验证记录](../../docs/reports/zcode-refactor-adoption-20260913/REPORT.md)。
