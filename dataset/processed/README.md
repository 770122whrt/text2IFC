# Processed dataset 与 Proof

| 目录 | 当前用途 | 处理原则 |
|---|---|---|
| [proof/](proof/README.md) | generation / repair 人读视图与原位机器权威 | 从 workflow → Phase → collection 阅读；状态写在索引中 |
| ifc-repair-runs/ | 原始 repair runs、genuine 成功和失败 attempts | 不整体忽略或删除 |
| ifc-repair/ | 早期 repair 运行和来源材料 | 即使被 Git ignore，也不是自动可删除缓存 |
| agent-demo/ | generation 运行、session 和验收来源 | 保留 provenance 引用的材料及真实 attempts |
| bim-json-1.0/、bim-json-2.0/、full_dump/、roundtrip_ifc/、roundtrip_json/ | 提取、版本合同及回转派生产物 | 按实际消费者判断，不按版本名删除 |
| descriptions/、text2json/、phase4/、phase6/ | 历史数据构建和训练／评估产物 | 保留 split、来源和实验边界 |
| review/ | 数据审查产物 | 不自动提升为正式训练数据 |
| ifc-presentation-validation/ | 其他任务的展示验证工作 | 本次不吸收或清理 |
| jsonfix/、ifc_parsed_data.json、ifc_parsed_enhanced.json | 既有修复／解析材料 | 未确认废弃前保留 |

重点入口：[Plan 07 待审矩阵](proof/repair/phase12/plan07-v2/REPORT.md)、[R1](proof/repair/phase12.1/r1/REPORT.md)、[generation](proof/generation/README.md)。

pytest 临时目录只有确认不再使用、未跟踪且可重建后才能清理。依赖缓存、下载数据与 genuine attempts 不按 tmp / failed / staging 名称判定垃圾。

[Proof 展示规范](../../docs/validation/ifc-repair-proof-format.md)
