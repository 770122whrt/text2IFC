# text2IFC 真实运行与人工检查

本批次尚未进入 accepted Proof。请分别检查两条链路：

| 链路 | 当前结果 | 人工入口 |
|---|---|---|
| Generation | 真实 Generator → Audit 接受 → 最终 IFC 验收通过，45 项独立检查通过 | [输入、输出与逐项报告](generation/REPORT.md)／[三维视图](generation/review-final.html) |
| Repair | dataset 原始→删除属性关联→真实修复，公共发布和独立核对通过 | [三元组与属性对照](repair/REPORT.md)／[三维视图](repair/review-repaired.html) |

[浏览器总览](index.html)可直接打开本地 HTML，或通过本地 HTTP 查看。每页使用实际 IFC 三角网格、深度遮挡、部件颜色；下拉选择构件，展开属性，拖动旋转、滚轮缩放。

## 已完成的通用修复

1. 冻结请求 ID 与规范实体 ID 在语义、几何和宿主检查中一致绑定；重复身份、错误类别继续阻断，跨楼层错误保留明确诊断。
2. IfcWallStandardCase 计入 IfcWall 家族，不混入非墙构件。
3. 合法关系 Name／Description 按文本保留，不能当作实体引用；覆盖开洞、填充、聚合、Type 和路径连接。
4. Design Brief 在解析前保留真实请求／响应；网络失败保留脱敏错误；澄清恢复不覆盖首轮；重复 call index 在网络前阻断。
5. 旧数据集／Proof 测试路径按已有迁移映射读取，不修改既有 Proof。

最终通用范围测试 82 passed，公共入口、staged 与恢复 34 passed；此前身份／几何相关 84 passed，关系／模板相关 77 passed。各组有重叠，不合并成能力样本数。更早 Generation 阶段 807 passed / 1 failed（旧回放合同修复后聚焦 110 passed）；Repair 全目录尝试超时且非全绿，后续属性阶段 379 passed / 1 failed 的旧 index 版本断言经 9 项复验通过；dataset 关系破坏的公共入口离线案例族 3 passed。所有失败 XML 保留。

未运行：Full Preflight、全库 pytest、accepted curator、用户人工验收。普通单例真实运行是可行性证据，不能证明系统能力提升。[真实调用清单](review-evidence/actual-provider-attempts.json)、[公开输入隔离检查](review-evidence/public-boundary-check.json)、[测试记录目录](admission/)。

后续：请分别人工确认 Generation 的输入／最终 IFC 与 Repair 的原始／损坏／修复 IFC。人工确认及适用机器检查通过后，才整理为 accepted Proof。真实 Generation 共 5 次调用，Repair 共 4 次调用（其中失败尝试 2 次保留）；不是首次盲测成功。

