# 墙体0.1 mm与整栋上下文：离线诊断

权威结果在 `reviewed-run/summary.json`。此目录不是新的真实整栋生成，也不是accepted Proof。

输入是旧真实整栋BIM JSON和上一轮真实单墙BIM JSON，独立副本只替换W013的Representation。原墙放置、材料、其他实体和关系不变；正确换算参考系后，输入图世界顶点与单墙相符。

实际结果：旧整栋图可重编译；集成图在材料层厚和基础窗矩形宿主两项合同检查处被拒。`reviewed-run/integrated-offline.compilation.json`记录对应W013、N003的错误；没有成功的`integrated-offline.ifc`。没有删除材料/窗或绕过正向Gate。

`reviewed-run/baseline-comparison-wall-0.1mm.json`是旧产物在新墙体阈值下的重算，非墙保留旧设置。历史20 mm报告未覆盖。扣洞后整栋集成几何因为编译阻断尚未评估。

根目录的首轮输入及单次编译错误保留，用于说明诊断脚本最初在负例失败时提前退出；`reviewed-run/`随后把拒绝当作明确结果记录，不把它改成通过。`validation/tests.xml`为23项聚焦测试，之后对报告口径做1项重复复验（不新增独立样本）。

前序真实预算仍为1400238/2000000 tokens、重建14/14、写作21，本轮零Provider调用。正向代码和系统Prompt未改动。

完整说明：`docs/reports/ifc2text-wall-tolerance-and-system-context-2026-09-21.md`。
