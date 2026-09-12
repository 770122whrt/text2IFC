# 光庭两版成品与人工验收

用户于2026-09-12确认“人工检验完毕是可行的合理的proof。”本次登记最新第二版 `ce8116ce095acdcf` 为人工已验收；第一版保留为设计演进参考，不追加其未获得的设计验收。两个实际IFC均保留，未重新生成或修改几何、材料、颜色。

| 项目 | 第二版：正式验收 | 第一版：历史参考 |
|---|---|---|
| 输入和输出 | [案例入口](open-court-v2/REPORT.md) | [案例入口](reference-v1/REPORT.md) |
| 生成过程 | 全新真实Brief → Generator → Audit，无候选修复调用 | 真实Brief/Generator失败后，确定性追加110条门窗关系，再真实Audit续跑 |
| 设计 | 两层24×18m，南侧敞开U形、外露楼梯、围庭回廊、20柱6梁、14细杆护栏、44窗6门 | 完整外墙、较小内庭、楼梯藏在封闭空间、4块玻璃栏板 |
| 原独立检查 | 545/545通过；111网格成功 | 1084/1084及部件色72/72通过 |
| 机器状态 | compiled / audit accepted | 终端机器检查通过 |
| 人工状态 | accepted | historical reference；不称为符合第二版意图 |

第二版成功loop共3次、317,533 token。第一版及第二版所有真实尝试的累计账本为17次、1,591,587 token、2723.014秒。累计快照不能相加；reasoning已包含在output中。本次收纳新增Provider调用为0。

失败与实验统一从 [evidence/README.md](evidence/README.md) 查找。原失败响应、修复过程、脚本和XML都已归档，删除原运行工作目录不等于抹除真实尝试。三个原来源目录的逐文件旧路径、保存位置、大小与SHA见manifest的legacy_bundles；可用仓库现有materialize_frozen_bundle工具还原原布局。52个Python/pytest可重建缓存不属于冻结证据。

第二版原浮点色值比较失败和HEX8重算均保留。原Audit误称用户指定材料强度等级；实际请求和IFC没有该性能值，历史报告已勘误。收纳没有把represented标签当作实值验证，也没有将人工外观验收改成结构、消防或完整规范认证。

本次迁移验证见 [validation](validation/README.md)。范围是本集合文件保真、两版IFC重开、最终第二版独立复算、图片来源和受影响的回归；未运行全仓Full Preflight、Provider或新的能力实验。原机器验收与当前迁移复验分别保存。
