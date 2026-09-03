# Processed Dataset 与 Proof 分层

本目录同时包含可重建的中间产物、原始运行记录和正式 Proof。三者用途不同，不能仅按文件名相似就合并。

## 目录职责

| 目录 | 职责 | Git / 清理原则 |
|---|---|---|
| ifc-repair-runs/ | repair 的原始 run、Provider attempts、clarification、索引、staging 与终端材料 | 默认由 .gitignore 作为本地运行区；genuine Provider attempts 保留；离线 pytest、preflight 和 admission 缓存可在不含跟踪文件时删除 |
| proof/ | 已冻结或待人工检查的证据视图与机器权威包 | 已提交 authority 按 append-only 处理；重复副本可在逐文件确认相同后删除 |
| proof/ifc-repair-success-cases/ | 人读优先的成功案例集合；案例根目录直接放 IFC、请求与报告 | 主 manifest 只列 accepted case；待检查批次使用独立 review manifest |
| 其他 processed 子目录 | extraction、projection、benchmark 或阶段性派生产物 | 按各自 manifest 与上游脚本判断，不因“processed”名称统一删除 |

## IFC Repair 的两层证据

人类检查从 [Plan 07 报告](proof/ifc-repair-success-cases/PLAN07-REPORT.md) 或各 Proof 集合的 REPORT.md 开始。完整 Provider/runtime/Proof 细节保留在机器权威包中，并由案例 FILES.json 和 evidence/README.md 指回。

成功 repair 案例的最低可见文件是 request、damaged IFC、repaired IFC 和 REPORT.md。只有角色在运行前合法冻结时才将 original IFC 解释为 private Ground Truth；否则 original 只能是明确标注的物理对照，IFCCompare 记为 N/A。

Guard 或 unsupported 案例的正确结果可能是没有 repaired IFC。此时必须有 NO-REPAIR.md，并证明没有 mutation 和 publish。

## 清理边界

可以直接清理：

- pytest 临时目录和 Python cache；
- 已结束的离线 admission/preflight 工作目录；
- 与已提交 curated 包逐路径、逐大小确认一致的未跟踪重复副本。

不得直接清理：

- genuine Provider 的成功或失败 attempts；
- accepted 或 committed machine authority；
- repaired IFC、终端 manifest、独立 evaluation；
- 尚未判断角色的 source/original/damaged 文件。

失败 genuine run 不进入成功 Proof，但仍是行为与审计记录。若空间压力需要归档，应先生成索引并保持原 run ID、终端状态和 Provider attempts 可追溯。

详细展示规范见 [IFC Repair Proof 人类可读收纳规范](../../docs/validation/ifc-repair-proof-format.md)。
