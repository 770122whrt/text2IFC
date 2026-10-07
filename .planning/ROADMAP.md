# text2IFC 路线与边界

当前执行位置见 [STATE](STATE.md)，稳定约束见 [PROJECT](PROJECT.md)。

| 方向 | 当前基线 | 后续范围 |
|---|---|---|
| Generation | Brief／澄清、完整或分包 BIM JSON、IFC2X3 编译、Gate／Audit、局部返工 | 需求保全、token 效率与复杂建筑能力需独立实验 |
| IFC Repair | 索引、目标／Type／属性解析、Window／Door／Opening／Beam／Column 等已注册操作，L0/L1/L2 与原子发布 | Wall 几何编辑、曲墙／自由形态、更多 MEP／结构类别尚未纳入通用支持 |
| 属性检索 | 精确 canonical 路径；自然语言检索候选后经 Stage 1.5 与确定性 admissibility | 检索分数不能授权修改，不恢复旧 alias 权威 |
| IFC2Text | 参数化门窗、建筑描述及独立往返比较 | 自进化、跨建筑策略学习和部件物理材料归属仍未完成 |
| 大型 IFC / Phase 13 | 保留已有规模与性能证据 | 128k／近上限实验需要独立任务，不自动改变默认预算 |

## 维护合同

`.planning/phases/` 保留规格与验证材料；已完成的执行计划、讨论和重复总结转由 Git 历史查询。
当前工作不自动执行旧计划中的 Next Action。已注册的旧 Schema／Prompt 保持可用。

Repair 源文件不原地修改，Gold／损坏真值只供评估，事务、保全与发布门禁持续生效。
L3 authoring／identity exactness 保持已记录的研究边界，不由本次清理升级为兼容性保证。

阶段映射、历史完成数字和完整旧计划入口见[清理前路线图](https://github.com/770122whrt/text2IFC/blob/d8ee81607c3c1239256c40c4b6dfff1761f40db3/.planning/ROADMAP.md)。
本次精简不是新的全仓验收或研究能力评测，结果见[精简记录](../docs/reports/lean-branch-20261007/REPORT.md)。
