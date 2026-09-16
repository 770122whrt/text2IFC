# Processed：成品、实验、数据与运行基线

优先从 [Proof](proof/README.md) 查看请求、IFC 和人工状态；从 [experiments](experiments/README.md) 查看实验、失败归因与 token 账本。

| 目录 | 用途 | 当前处理原则 |
|---|---|---|
| [proof/](proof/README.md) | Generation／Repair 成品及完整冻结证据 | 保持 workflow → Phase → collection；人工与机器状态分别记录 |
| [experiments/](experiments/README.md) | 已结束实验、诊断及原始运行记录 | 既有档案不反复搬迁；通过原路径映射查找 |
| [derived/](derived/README.md) | 提取／描述、BIM JSON 转换、回转结果、Phase 4／6 派生清单 | 统一派生产物位置；原文件内容及历史来源字段保留 |
| [text2json/](text2json/README.md) | 当前文本训练／评估数据、Gold、配对与 sidecar | 仍有直接消费者；不改变 split、授权和公私边界 |
| agent-demo/ | Generation few-shot、公共离线夹具及运行工作区 | 当前代码仍使用；新展示工作区统一放 [presentation/](agent-demo/presentation/README.md) |
| [ifc-repair/](ifc-repair/README.md) | Repair 案例、离线输入和权限隔离材料 | 活动消费者与权限不明项保留；不按名称删除 |
| ifc-repair-runs/ | Plan07 当前测试／运行器需要的源基线 | 保留当前依赖；历史运行见 experiments |

2026-09-13 已将原 8 个数据目录及两份解析 JSON 归入 `derived/`，旧 `jsonfix/` 完整收纳到 experiments，原展示目录归入 agent-demo；空 review 退役。顶层由 17 个目录与 2 份散落数据文件缩为 7 个用途目录。

[本轮整理报告](../../docs/reports/processed-cleanup-20260913/REPORT.md) · [旧路径至新路径](../manifests/processed-layout-20260913.json) · [此前 Phase 运行退役](../../docs/reports/development-cleanup-20260912/REPORT.md)

历史 manifest／报告中的路径是当时记录，以迁移映射解释；没有重新生成已验收 IFC、原始响应或历史数据。新运行必须使用新目录及当前准入，不能从归档中直接延续真实调用。
