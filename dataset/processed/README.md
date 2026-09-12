# Processed dataset 与 Proof

| 目录 | 当前用途 | 处理原则 |
|---|---|---|
| [proof/](proof/README.md) | generation / repair 自包含案例与冻结证据 | 从 workflow → Phase → collection 阅读；状态写在索引中 |
| [experiments/](experiments/README.md) | 已结束的实验、失败归因、原始响应、账本和一次性脚本 | 通过归档索引查旧路径；不自动提升人工或机器状态 |
| ifc-repair-runs/ | 当前 Plan07 测试和运行器所需的来源基线 | 已结束的 Phase12／R1 运行见 experiments 中的 Phase 历史 |
| ifc-repair/ | 仍有消费者的 Repair 案例、离线源及权限隔离材料 | 已结束的 Phase9–12 开发记录按路径映射归档 |
| agent-demo/ | 当前 few-shot、回归夹具、旧验证器输入和运行输出位置 | 已结束的无依赖历史运行归档至 experiments |
| bim-json-1.0/、bim-json-2.0/、full_dump/、roundtrip_ifc/、roundtrip_json/ | 提取、版本合同及回转派生产物 | 按实际消费者判断，不按版本名删除 |
| descriptions/、text2json/、phase4/、phase6/ | 历史数据构建和训练／评估产物 | 保留 split、来源和实验边界 |
| review/ | 数据审查产物 | 不自动提升为正式训练数据 |
| ifc-presentation-validation/ | 新展示验证的工作区 | 已结束的光庭、A/B、三层及语义外观等工作区归档至 Proof／experiments；实际退役见整理记录 |
| jsonfix/、ifc_parsed_data.json、ifc_parsed_enhanced.json | 既有修复／解析材料 | 未确认废弃前保留 |

重点入口：[Plan 07 已通过矩阵](proof/repair/phase12/plan07-v2/REPORT.md)、[R1](proof/repair/phase12.1/r1/REPORT.md)、[generation](proof/generation/README.md)。

pytest 临时目录只有确认不再使用、未跟踪且可重建后才能清理。依赖缓存、下载数据与 genuine attempts 不按 tmp / failed / staging 名称判定垃圾。

[Proof 展示规范](../../docs/validation/ifc-repair-proof-format.md)

新增 [材质与外观修复案例](proof/repair/phase12/presentation-cases/REPORT.md)：3 个运行 PASS，人工待审。来源进程的已结束工作目录按 [路径映射](experiments/development-retirement-20260912.json) 退役，状态不变。

2026-09-12：[光庭两版成品](proof/generation/phase6.6/courtyard-library-20260912/README.md)已集中收纳，最新第二版人工已验收。[实验入口](experiments/README.md)提供失败归因；原运行目录及一次性调试脚本的处理见 [整理记录](../../docs/reports/courtyard-proof-closeout-20260912/REPORT.md)。通用回归留在tests，生产代码不依赖归档运行器。

其他已结束案例与开发临时目录的追加清理见 [执行报告](../../docs/reports/development-cleanup-20260912/REPORT.md)。

更早的 [Phase 6、9–12 历史](experiments/phase-history-20260912/README.md) 已压缩收纳，包括真实失败和原始响应。目录是否已删除以执行报告为准；旧路径通过归档 manifest 查找，历史验收状态不变。
