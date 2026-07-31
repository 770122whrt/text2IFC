# Phase 11 Door Storey Policy Erratum

## 决策

`Door storey = host-wall storey` 中的 “host-wall storey” 指目标 Opening
高度处的宿主墙空间上下文，不等同于 `IfcWall.ContainedInStructure` 的唯一
direct container。

确定性顺序为：

1. 宿主墙必须有且仅有一个 direct `IfcBuildingStorey`，否则 fail closed；
2. 只在该 Storey 所属的同一 Building 内比较 Storey；
3. 计算 retained Opening 几何底部的世界标高；
4. 若最近 Storey 与墙的 direct container 相同，使用它；
5. 若墙跨楼层且 Opening 底部距另一个 Storey 标高不超过 `1000 mm`，使用
   该 Opening-height Storey；
6. 若最近候选等距则拒绝；若 Opening 没有足够接近的其他楼层证据，则回退到
   墙的唯一 direct container。

该规则不读取 original IFC、被删除 Door 或 mutation manifest。

## 为什么需要勘误

权威审计文档 B3 的简写规则要求使用 host wall spatial container，但 supplied
vvo IFC 的真实 authoring 结构是：

- 目标墙跨越多个楼层，direct containment 为 `标高0`；
- 两个 retained Opening 的实际底部位于 `标高2`；
- original Door 也属于 `标高2`；
- 旧修复把 direct wall container `标高0` 机械复制给 Door，正是已确认的
  阻塞缺陷。

如果把 “host-wall storey” 机械解释为 direct containment，会重新制造
`标高2 → 标高0` 错误，并与同一权威文档的 fixture-level acceptance criteria
矛盾。因此本勘误把它收敛为“Opening 高度处的宿主墙上下文 Storey”。

## 验证

- vvo 回归明确证明 wall direct Storey=`标高0`、Opening context
  Storey=`标高2`；
- 正常单楼层墙仍返回 direct Storey；
- 缺失或重复 wall containment 均 fail closed；
- Storey 解析结果进入 Index、Applicator postcondition、L1 与 L2
  `relationship:storey` 的同一事实路径。
