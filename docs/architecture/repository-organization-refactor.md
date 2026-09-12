# text2IFC 目录清理与证据集中记录

## 当前执行：接入 Zcode 的有效重构（2026-09-13）

用户已批准实际接入有价值的重构，取代下文旧记录中暂不调整 evaluation 的安排。以当前分支代码为基线提取职责，旧镜像仅提供结构参考；不回退后续修复，不改变合同版本、默认行为、冻结 Proof 或真实调用准入。

1. 生产评估与私有基准比较分离：生产入口直接依赖 `production_evaluation`，基准比较单向依赖它；旧导入继续可用。已接入，211 项聚焦离线回归通过。
2. Proof 校验和独立审计进入 `text2ifc_proof` 包，移除校验器到 curator／runner 的循环依赖。待接入。
3. 修复运行脚本按 UAT、离线、curator、audit 分类，保留原命令入口与历史路径含义。待接入。

每步使用现有正反例、隐私隔离、失败关闭和公共入口的聚焦离线回归，另补导入边界及兼容检查；不执行 Full Preflight 或 Provider 调用。以下 9 月 7 日内容是历史清理记录。

更新：2026-09-07。用户批准集中迁移、成功 run 退役和“同一冻结案例通过后删除历史失败”的策略；Plan07 于本日另获用户人工审查通过。产品名为 text2IFC，BIMNet 保留数据来源含义。

## 已执行

本轮只调整存储、导航和路径加载。生产修复行为、冻结请求、Gold、阈值、Provider 输出及 Phase 状态不变。R1 完整迁移验收通过，旧权威和已完整绑定的成功原 run 已退役。

- 已批准 pytest 工作区及 12 个重复 IFC：删除 13,312 文件，3,058,116,112 字节（2.848 GiB）。
- 四个旧 Proof 根目录的完整内容已经集中，旧目录退役。
- 六个 generation 成功来源和一个历史 guard 来源已全部绑定到 Proof，原案例目录退役。
- Plan07：10 案 accepted，用户审批原文“plan07我审批完了 是通过的”；6 offline、3 live repaired、1 guard，11 次 genuine 调用不变。
- 新材质外观集合：3 个来源运行 PASS，pending_human_review；来源进程目录和暂存内容保留。
- R1：12 案原 accepted 状态不变；原合同逐案复算与集合检查均通过，旧顶层目录和对应成功原 run 已退役。

## 目录与阅读

```text
dataset/processed/proof/
  README.md
  PROOF-INVENTORY.json
  generation/phase6.6/generation-examples/   # 6 accepted
  repair/phase11/reference-cases/           # 16 accepted，5 个旧 Window 有限制
  repair/phase11/live-uat/                  # 1 historical，无输出
  repair/phase12/plan07-v2/                 # 10 accepted，用户已审
  repair/phase12/presentation-cases/        # 3 run PASS，人工待审
  repair/phase12.1/r1/                      # 12 accepted，迁移已验证
```

[Proof 入口](../../dataset/processed/proof/README.md) · [Plan07](../../dataset/processed/proof/repair/phase12/plan07-v2/REPORT.md) · [材质外观](../../dataset/processed/proof/repair/phase12/presentation-cases/REPORT.md)。

每个集合提供 README、REPORT、manifest 和案例目录。repair 根目录直接展示 REPORT.md、request.txt、合法 original（如有）、02-damaged.ifc 与 03-repaired.ifc 或 NO-REPAIR.md；generation 展示 model.json 与 generated.ifc。过程材料在 evidence。

人读材料是请求、IFC 和中文报告；机器证据是 Provider 请求响应、runtime、ChangeSet、terminal、验证和冻结索引。二者不是 original/repaired 的区别，它们描述同一案例并共享根目录 IFC。新包版本 text2ifc/workflow-proof-package/0.1 的 legacy_bundles 保存旧路径、现路径、SHA-256 和大小；旧合同与报告字节不改写。

## 已退役路径与恢复

| 原路径 | 当前保留索引 | bundle / 文件数 |
|---|---|---|
| `dataset/processed/proof/text2ifc-success-cases` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `frozen` / 21 |
| `dataset/processed/proof/phase11-live-uat` | `dataset/processed/proof/repair/phase11/live-uat/manifest.json` | `legacy-root` / 7 |
| `dataset/processed/proof/ifc-repair-success-cases` | `dataset/processed/proof/repair/phase11/reference-cases/manifest.json` | `frozen` / 287 |
| `dataset/processed/proof/ifc-repair-success-cases-v2-plan07-staging` | `dataset/processed/proof/repair/phase12/plan07-v2/manifest.json` | `frozen` / 223 |
| `dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `source-stable-01-easy` / 154 |
| `dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `source-stable-01-medium` / 142 |
| `dataset/processed/agent-demo/phase6.6-difficult-stair-fix-live-64k-explicit-hosts/runs/ba2277d8363bce69` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `source-stable-01-difficult` / 210 |
| `dataset/processed/agent-demo/phase6.5-easy-accepted` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `source-two-storey-final-712` / 8 |
| `dataset/processed/agent-demo/phase6.5-medium-100mm-gap-fix` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `source-output-713-success` / 5 |
| `dataset/processed/agent-demo/phase6.5-hard-accepted` | `dataset/processed/proof/generation/phase6.6/generation-examples/manifest.json` | `source-hard-three-storey-final` / 17 |
| `dataset/processed/ifc-repair/phase11-live-uat/uat-20260731T224900289758Z/unsupported-complex-door` | `dataset/processed/proof/repair/phase11/live-uat/manifest.json` | `guard-run` / 22 |
| `dataset/processed/proof/repair-milestone-r1` | `dataset/processed/proof/repair/phase12.1/r1/manifest.json` | `legacy-root` / 805 |
| `dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z` | `dataset/processed/proof/repair/phase12.1/r1/manifest.json` | `run-original` / 731 |

普通临时产物的精确目录：

- `dataset/processed/ifc-repair-runs/phase12-live/uat-20260820T135432218011Z/preflight/` 下 pytest-full-suite、pytest-focused、pytest-cache-full-suite、pytest-cache-focused。
- `dataset/processed/ifc-repair-runs/phase12-live/uat-20260830T174344933512Z/preflight/` 下同样四类目录。
- 两个 full-suite 的 test_link_run_escape_is_reject0 与 test_stage_directory_rejects_r0 子树含 reparse points，继续保留；未放宽 ACL 或遍历链接。
- `dataset/processed/ifc-repair/phase11-door-audit-performance-check`、`phase11-door-audit-performance-check-2`、`phase11-door-audit-performance-check-3`、`phase11-door-audit-performance-check-5` 中 `advancedproject-door-preserve-opening/{original.ifc,damaged.ifc,repaired.ifc}` 共 12 文件；各角色 SHA 与保留的 `phase11-door-audit-performance-check-6/advancedproject-door-preserve-opening/` 相同。独立小报告仍保留。

未跟踪 pytest 产物没有 Git 恢复副本，可重跑原离线测试再生；没有保留同体积备份。重复 IFC 从上述 -6 保留副本恢复。迁移证据用 `scripts/proof/materialize_frozen_bundle.py --root <集合> --bundle <id> --destination <不存在的目录>` 重建旧布局。原 Git/LFS 历史仍保留，不重写历史或 prune LFS。

## Proof 为什么重

清理前 Proof 为 2,273,857,411 字节（约 2.12 GiB），1,862 文件：211 个 IFC 共 2,113,275,001 字节，占 92.94%；SQLite 约 106.57 MiB，JSON 约 45.21 MiB。211 个已提交 IFC 路径对应 66 个 Git LFS OID，唯一内容约 732.52 MiB，重复路径理论量约 1.253 GiB。读取既有 LFS 指针，没有全仓库哈希。

主要重复是同一案例的机器 IFC 与人读 IFC、跨案例共享输入及旧 staging 副本。R1 E2/M1/H2 使用相同约 76.60 MiB 输入；输出大小相同不代表内容相同。本次收敛同案例双份 IFC，保留跨案例直接可见文件，不使用硬链接。Git/LFS 对象和依赖缓存不当作垃圾删除。

当前 Proof 为 1,273,865,831 字节（约 1.186 GiB），2,384 文件；相对盘点减少约 0.931 GiB。包含 Proof 新增机器证据与报告后，已记录范围的文件逻辑体积净减少约 6.497 GiB。此数字不计本任务产生后又清除的验证副本，不等于 Git/LFS 历史缩减或磁盘分配块精确变化。

## 实际验证与边界

- 六集合文件绑定、状态、角色和输出/no-output 互斥检查：48 案、115 次 IFC2X3 reopen，通过。
- 参考集合从新包还原冻结布局，已提交代码完整验证通过：16 案、45 操作、247 文件、48 reopens、11 案独立复算，5 个历史 Window 的原有局限保留。
- 人工审批更新后的聚焦测试：37 passed，1 deselected。排除的是已有完整独立验证覆盖的参考集合重验，不是全库通过。
- staging 路径相关测试：6 passed、1 deselected。被排除的准入检查实际报 LIVE_V2_ADMISSION_PATH_INVALID：当前 changed-scope-admission-v2.json 缺失，新的真实调用仍被阻止；不重建准入、不自动升级 Full Preflight。
- 冻结 Prompt 末尾空行保留；当前人读导航格式及链接检查通过。
- R1 当前脏工作树重验 10 案报 resolution_replay，H4/A1 通过；隔离使用 fe33afb397b4d3c7cee60ce1e831f4c5a2545f50 已提交代码，排除其他任务改动。最终以隔离进程逐案完成全部原检查，再执行原集合/schema 检查并汇总：12 案、13 操作、785 文件、23 reopens、12 独立复算，零错误、零限制。未把最初中断的单进程运行计为通过；[完整结果](../../dataset/processed/proof/repair/phase12.1/r1/evidence/migration-validation.json) 与 [执行上下文](../../dataset/processed/proof/repair/phase12.1/r1/evidence/migration-validation-context.json) 可查。
- 新外观案例的实现/schema 正由来源进程交付；本次只归档成功快照，不宣称旧的已提交代码能完整重放新案例。
- 本任务没有 Provider 调用、Full Preflight、IFCCompare 或全库测试，不新增能力结论或关闭 Phase。

## 条件失败清理：已执行

以下 10 个失败目录已核对同一冻结 manifest、验收合同、逐案例请求 SHA、源 IFC SHA/大小及对应 passed 运行，且 R1 迁移验证通过后已删除：2,597 文件、2,232,361,524 字节（2.079 GiB）。逐案匹配、恢复提交与保留原因见 [退役审计](../../dataset/processed/proof/repair/phase12.1/r1/evidence/retirement.json)。其中已跟踪文件可从提交 378accee 的 Git/LFS 恢复；未跟踪的失败运行按授权销毁，没有完整备份。

| ifc-repair-runs/repair-milestone-r1/ 下目录 | 文件 | 字节 | Git 跟踪 |
|---|---:|---:|---:|
| `r1-20260831T151326967970Z` | 184 | 215,267,217 | 0 |
| `r1-20260831T155141193325Z` | 495 | 434,474,114 | 0 |
| `r1-20260901T034310928815Z` | 495 | 434,302,725 | 0 |
| `r1-20260901T052919004905Z` | 85 | 24,367,730 | 0 |
| `r1-20260901T134510430440Z` | 522 | 455,053,472 | 522 |
| `r1-20260901T154532207844Z` | 715 | 654,927,335 | 715 |
| `r1-20260902T141632454789Z` | 18 | 3,672,133 | 0 |
| `r1-20260902T142055280724Z` | 23 | 3,481,553 | 0 |
| `r1-20260902T142600567859Z` | 23 | 3,332,823 | 0 |
| `r1-20260902T150713117380Z` | 37 | 3,482,422 | 0 |

`r1-20260902T053023885207Z` 是独立的 passed 历史运行，不属于失败销毁范围，保留其 707 文件、656,220,561 字节；`r1-20260901T055419268779Z` 的 H3 请求不匹配，保留；无完整 result、无调用准入目录、独立诊断及 IFCCompare 目录也保留。删除后不得声称历史失败全量保留，也不能用筛选后的成功包计算成功率。

## 后续适度重构与并发工作

- src 保留现有 production 模块边界，不为整齐改动 Agent、apply 或 evaluation。
- scripts/proof 统一包映射和验证入口；原 schema 验证继续沿用。旧 curator 和 Plan07 v2 runner 默认写 ifc-repair-runs/curation-staging，避免重建旧 Proof 顶层目录。旧 Plan07 installer 的验证来源常量仍保留冻结历史路径语义；新安装需显式指定来源，不重建已集中包。
- repair run 作为工作区；成功归档后按映射退役。活动、归属不明、不可读或依赖未闭合目录保留。
- .venv、.cache、模型、下载数据、外部 IFC、Git/LFS 不作笼统删除。
- 其他任务的 114 项暂存、生产/测试修改和 dirty submodule 均保留。本任务只提交明确路径，不能靠吞并他人工作把工作树变干净。
