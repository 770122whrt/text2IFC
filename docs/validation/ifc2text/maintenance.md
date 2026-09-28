# IFC2Text 故障定位与回归

更新：2026-09-28。这里保存已遇到的原因和对应回归，当前运行数字见[结果页](component-v26/README.md)，旧失败原稿见[历史索引](history.md)。文档不能保证不再出错；修改相关路径时重跑对应失败族，才是防止复发的依据。

## 先定位信息在哪一步改变

保留同一案例的 **源 IFC → facts → 公开说明 → Brief → BIM JSON → 输出 IFC → 独立比较**。每一步同时看对象身份、单位、坐标和完整值，不只看数量或 Audit 的通过标记。

1. 源有、facts 没有：查解析及不支持原因，不能让 LLM 凭名称猜几何。
2. facts 有、说明没有：查描述覆盖与压缩；共享构件只描述一次，但引用不能遗漏。
3. 说明有、Brief／BIM JSON 没有：查版本路由、字段传播、提示和 Provider 原始响应。
4. BIM JSON 正确、IFC 错：查编译、部件变换、宿主开口及实际几何重开结果。
5. IFC 看似正确、Compare 报错：核对比较版本、世界坐标和测量覆盖。若要更换评价器，用同一版本重评分两侧，不修改旧报告。

重试写新运行目录；Provider 原始失败与拒绝原因保留。源 IFC 不修改，重建端只读取已公开的设计说明。Audit 检查说明满足度，Compare 检查源模型保真，两者不能替代。

## 已知失败族与对应检查

以下路径均从仓库根目录执行，测试使用确定性输入；它们不是新的真实 Provider 成功证据。

| 症状／原因 | 应保持的修复规则 | 定向回归 |
|---|---|---|
| Brief 写了空间，但高度预期未读到：字段投影／版本衔接遗漏 | 世界端点和区间明确对应；半对端点、冲突值不能偷偷用层高补齐 | [空间投影 v1.3](../../../tests/agent/test_space_geometry_projection_v13.py)、[v1.2](../../../tests/agent/test_space_geometry_projection_v12.py) |
| 特殊墙镜像或缺口丢失，包围盒近似掩盖轮廓错误 | 保留局部截面、方向与变换，核对世界轮廓；不改源顶点迎合比较器 | [多边形宿主](../../../tests/compiler/test_polygon_wall_hosts_v24.py)、[世界坐标](../../../tests/agent/test_component_world_placement.py) |
| 凹口墙材料／安装检查按凸形或包围盒处理 | BIM JSON 2.6 使用真实多边形交集；旧合同范围不暗改；合法轮廓只补完全相同的闭合终点 | [凹口墙](../../../tests/compiler/test_notched_wall_hosts_v26.py)、[闭合恢复](../../../tests/agent/test_polygon_closure_recovery.py) |
| 门含多个材料名，旧链把清单误作分层材料或拒绝 | 清单保持多个材料名，不猜层厚、部件材料归属 | [描述接缝](../../../tests/ifc2text/test_material_list_description_seam.py)、[Agent 路由](../../../tests/agent/test_material_list_v25_route.py)、[编译](../../../tests/compiler/test_material_list_v25.py) |
| 2.6 房间属性名错误；恢复白名单漏接或专用提示被覆盖 | 从注册合同推导唯一字段更名，保留原值和其余属性；删除旧键不能用 null 冒充 | [枚举字段恢复](../../../tests/agent/test_enum_field_recovery.py)、[早期恢复](../../../tests/agent/test_early_field_recovery.py) |
| 百叶缺片、孔被填实、把手被模板替换、父变换重复 | 检查源父构件完整 Body、公开部件身份与输出真实 ShapeAspect；不按已识别实体过滤源几何 | [部件几何](../../../tests/compiler/test_component_geometry_v26.py)、[真实几何比较](../../../tests/ifc2text/test_filling_compare_v12.py)、[身份](../../../tests/agent/test_component_public_identity.py) |
| 不支持项被静默省略，旧回答误批准新对象 | 暂停不生成；明确批准列明对象后才能继续，输出标为部分重建 | [人工复核／恢复](../../../tests/ifc2text/test_component_review.py)、[宿主公开链](../../../tests/ifc2text/test_component_hosted_public_chain.py) |
| Repair 成功候选未送到 Audit，或重试覆盖失败／重置预算 | 独立 continuation 复制选定候选，校验父输入哈希并保留失败；未结算账本不能当成新预算 | [候选延续](../../../tests/ifc2text/test_component_candidate_continuation.py)、[预算](../../../tests/ifc2text/test_component_budget.py) |
| 把局部宽／深差当世界误差，或 1 mm 判断不一致 | IfcOpenShell 解析真实几何后比较；线性差 ≤1 mm，未评估项、缺失项和原始结论保留 | [容差边界](../../../tests/ifc2text/test_precision_compare_v11.py)、[开口 v1.3](../../../tests/ifc2text/test_opening_compare_v13.py) |
| 只改一个叶片却影响其他部件／关系 | 修改范围保持到部件，未选对象及宿主关系保持 | [局部修改公开链](../../../tests/ifc2text/test_component_single_part_edit.py)、[修改范围](../../../tests/agent/test_component_geometry_repair_scope.py) |

例如修订房间字段恢复时，使用仓库虚拟环境、工作区内全新临时目录：

```powershell
.venv\Scripts\python.exe -m pytest `
  tests/agent/test_enum_field_recovery.py `
  tests/agent/test_early_field_recovery.py `
  tests/ifc2text/test_component_candidate_continuation.py `
  --basetemp=.tmp/pytest-ifc2text-field-new -q
```

根据实际改动选行，不必每次重跑整仓。新阶段真实调用前另按[Agent 准入协议](../agent-capability-evaluation.md)核验准入；Full Preflight 需要单独说明范围并获批准。

## 实现入口

- 解析／描述：[facts.py](../../../src/text2ifc_ifc2text/facts.py)、[compact.py](../../../src/text2ifc_ifc2text/compact.py)、[compact_pipeline.py](../../../src/text2ifc_ifc2text/compact_pipeline.py)。
- 当前整栋比较：[precision_compare_v13.py](../../../src/text2ifc_ifc2text/precision_compare_v13.py)，门窗真实形状比较由 [filling_compare_v12.py](../../../src/text2ifc_ifc2text/filling_compare_v12.py)提供。
- 保留失败继续处理：[component_candidate_continuation.py](../../../scripts/ifc2text/component_candidate_continuation.py)。
- 人工处理不支持项：[component_review_cli.py](../../../scripts/ifc2text/component_review_cli.py)。

历史上出现过“测试临时目录无权限”“原生探针漏 provenance”“汇总 source 键被网格指标覆盖”“临时 shape 生命周期导致空网格”。这些记录在历史索引中保留；遇到同类症状先核对运行环境、原始响应和实际 IFC，不靠放宽容差解释过去。
