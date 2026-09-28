# 参数化门窗与 IFC2Text：运行结果

结果日期：2026-09-26；文档整理：2026-09-28。批准范围已完成，两栋均为**经人工批准排除不支持项后的部分重建**。本次整理没有重新运行 Provider，也没有扩大原来的成功范围。

## 整栋结果

| 案例 | 源／匹配 | 明确排除 | 已测几何超差 | 最大已测线性差 | 材料内容／元数据差异 | 已测关系差异 |
|---|---:|---|---:|---:|---:|---:|
| hxp | 66／61 | D003–D007 | 0 | 0.087470 mm | 0／36 | 0 |
| i5n_1 | 101／100 | D002 | 0 | 0.083108 mm | 0／44 | 0 |

两栋均无额外对象，最大已测线性差均来自 R003 房间包围盒 X 尺寸。墙与开口保留；hxp 四扇圆弧复合截面门和一扇 BRep 门、i5n_1 一扇含 22 项 BRep 的门没有生成。i5n_1 的“暂停不生成”和“批准排除后继续”两条分支均有验证。

材料元数据差异主要涉及层集合名称等组织信息，不能写成材料完全一致。原始 `reconstruction_consistent=false` 保留。hxp 的 34 面墙、i5n_1 的 42 面墙仍有 intrinsic 方法未评估项，另有排除的 5／1 个填充物；已经通过的世界几何测量不能抹掉这些未评估项。

## 证据入口

| 案例 | 已提交的紧凑索引 | 本地完整证据 | 本地最终 IFC |
|---|---|---|---|
| hxp | [接受摘要与 SHA](hxp-accepted-summary.json) | [人读报告](../../../../dataset/processed/experiments/component-v26-building-continuation-20260926-02/hxp/HUMAN-REPORT.md) | [output.ifc](../../../../dataset/processed/experiments/component-v26-building-continuation-20260926-02/hxp/accepted/output.ifc) |
| i5n_1 | [接受摘要与 SHA](i5n-accepted-summary.json) | [人读报告](../../../../dataset/processed/experiments/component-v26-building-continuation-20260926-08/i5n_1/HUMAN-REPORT.md) | [output.ifc](../../../../dataset/processed/experiments/component-v26-building-continuation-20260926-08/i5n_1/accepted/output.ifc) |

完整运行目前保留在本地实验目录，不能把紧凑索引已推送理解为 IFC 与全部轨迹已上传。摘要记录源、公开输入、候选、Audit、最终 IFC 与比较报告的路径和哈希。旧失败及重试保留在父实验目录，详细阶段时间线由[历史索引](../history.md)引用，不在本页重复保存。

## 验证到哪一步

| 层次 | 已得到的证据 | 不代表什么 |
|---|---|---|
| 原生解析与编译 | hxp 10 项门窗：5 通过／5 拒绝；TallBuilding 26 项：25 通过／1 拒绝；[原生摘要](native-summary.json) | 无 LLM，不代表文本生成成功 |
| 公开描述与交互 | [S2 摘要](stage2-summary.json)；离线公开链覆盖补参、拒绝、保存恢复及源不变 | 离线回放不冒充真实 Provider |
| 单门／单窗 | hxp 与 TallBuilding 各一门一窗，四个真实文本往返 | 不是任意门窗都支持 |
| 宿主安装 | 门、窗各一个真实场景 | 不是任意宿主拓扑都支持 |
| 两栋 loop | 上表两栋经真实修复、Audit、最终编译、重开及独立 Compare 1.3 | 部分重建不是全源一致，也不是未见建筑能力提升 |
| 局部部件编辑 S6 | 离线公开链验证 | 尚无真实模型自然语言编辑实验 |

几何范围、部件身份、颜色／透明度与旧模板兼容约定统一见[计划 v1.0](../../../architecture/text2ifc-component-plan-v1.0.md)。部件物理材料和跨建筑自进化仍待后续工作。

## 比较如何解释

IfcOpenShell 负责 IFC 解析、单位、变换、真实形状与网格；项目在其结果上计算距离、拓扑和体积。整栋采用 Compare 1.3；先前单构件记录使用 Compare 1.2，不能混称为同一次重测。线性差 **≤1 mm** 接受；数量、拓扑、材料另查。不同局部坐标的开口宽／深参数差不是实测世界几何误差。

网格线性偏差设置为 0.1 mm，双向表面采样并非连续 Hausdorff 上界证明。IfcDiff 0.8.5 只作为四个单构件的附加几何交叉检查，不能单独证明 1 mm 精度或完整材料／外观一致。

## 预算与后续

截至本轮完成，Provider 实耗 6,224,946 token，授权上限 6,696,347，余额 471,401；账本 `component-v26-budget-20260926-04`。本次文档整理没有新增调用。

后续修复从[故障定位与回归](../maintenance.md)进入；新真实调用仍须遵循[Agent 准入协议](../../agent-capability-evaluation.md)，不能用这两栋已见案例当作新方法的盲测提升。
