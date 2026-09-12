# 过程与失败归因

| 历史 | 原始材料 | 已确认原因与处理 |
|---|---|---|
| 第一版首次Brief及后续调试 | [v1](v1/REPORT.md) | 语义字段散落、Type/材料作用域和屋盖开口投影；保留各次失败与局部修复证据 |
| 第一版最终续跑 | [continuation-01](v1/continuation-01/REPORT.md) | 门窗缺55组关系，确定性恢复110条后真实Audit；设计与概念方向仍有差距 |
| 第二版初次Brief | [墙布局诊断](v2/brief-envelope-debug/REPORT.md) | 开敞设计误用完整墙环检查；通用修复区分两类约束 |
| 第二版rerun-01 | [属性及修复诊断](v2/property-debug/REPORT.md) | 非法空间Pset、局部修复越界、楼梯外观目标错误；不得发布诊断候选 |
| 第二版rerun-02 | [真实运行](v2/rerun-02/live-run/) | 矩形边界对象/轮廓数组格式差异；仅接受严格等价规范化 |
| 第二版rerun-03 | [最终原报告](v2/rerun-03/REPORT.md) | 新鲜真实完整loop成功；原浮点颜色误判和HEX8评价修订均保留 |
| 概念来源 | [concept](concept/) | AI概念图仅作设计参考，不作为实际IFC图片 |

所有真实attempt、Prompt/响应、SQLite、账本、失败XML及一次性`test_*.py`随相应过程保留。它们是审计材料，默认pytest只从仓库tests收集。可重建缓存未收纳；没有删除真实失败分母。

旧文档中的原相对/绝对路径是历史环境。需要逐字节重建时，在仓库根执行现有工具，例如：

```powershell
.venv\Scripts\python.exe scripts/proof/materialize_frozen_bundle.py --root dataset/processed/proof/generation/phase6.6/courtyard-library-20260912 --bundle v2 --destination .tmp/courtyard-history-readonly
```

目标必须不存在。工具只还原文件，不调用Provider、不重开历史授权。当前入口以本集合README为准。
