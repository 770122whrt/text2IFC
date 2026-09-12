# Processed dataset 与 Proof

| 目录 | 当前用途 | 处理原则 |
|---|---|---|
| [proof/](proof/README.md) | generation / repair 自包含案例与冻结证据 | 从 workflow → Phase → collection 阅读；状态写在索引中 |
| ifc-repair-runs/ | 原始 repair runs、genuine 成功和失败 attempts | 不整体忽略或删除 |
| ifc-repair/ | 早期 repair 运行和来源材料 | 即使被 Git ignore，也不是自动可删除缓存 |
| agent-demo/ | generation 运行、session 和验收来源 | 保留 provenance 引用的材料及真实 attempts |
| bim-json-1.0/、bim-json-2.0/、full_dump/、roundtrip_ifc/、roundtrip_json/ | 提取、版本合同及回转派生产物 | 按实际消费者判断，不按版本名删除 |
| descriptions/、text2json/、phase4/、phase6/ | 历史数据构建和训练／评估产物 | 保留 split、来源和实验边界 |
| review/ | 数据审查产物 | 不自动提升为正式训练数据 |
| ifc-presentation-validation/ | 展示验证的原始运行工作区 | 已验收成品优先自包含收纳到 Proof；光庭两版已归档，原目录退役以整理报告为准；其他历史来源逐项保留 |
| jsonfix/、ifc_parsed_data.json、ifc_parsed_enhanced.json | 既有修复／解析材料 | 未确认废弃前保留 |

重点入口：[Plan 07 已通过矩阵](proof/repair/phase12/plan07-v2/REPORT.md)、[R1](proof/repair/phase12.1/r1/REPORT.md)、[generation](proof/generation/README.md)。

pytest 临时目录只有确认不再使用、未跟踪且可重建后才能清理。依赖缓存、下载数据与 genuine attempts 不按 tmp / failed / staging 名称判定垃圾。

[Proof 展示规范](../../docs/validation/ifc-repair-proof-format.md)

新增 [材质与外观修复案例](proof/repair/phase12/presentation-cases/REPORT.md)：3 个运行 PASS，人工待审。来源进程的 ifc-presentation-validation 工作目录保留。

2026-09-12：[光庭两版成品](proof/generation/phase6.6/courtyard-library-20260912/README.md)已集中收纳，最新第二版人工已验收。[实验入口](experiments/README.md)提供失败归因；原运行目录及一次性调试脚本的处理见 [整理记录](../../docs/reports/courtyard-proof-closeout-20260912/REPORT.md)。通用回归留在tests，生产代码不依赖归档运行器。
