# IFC2Text 往返归因：冻结探针 v0.1

研究方案沿用 `docs/architecture/bim2text-bidirectional-bridge-research.md`。本轮只诊断已揭示的 hxp，不声称跨建筑能力提升，不重写旧 Prompt、Schema 或 IFC。

## 假设与可证伪预测

| 假设 | 实验与判别 |
|---|---|
| H1：五个空间的问题主要是 Brief 没有几何 | 冻结原 Brief，检查 polygon/z_mm，再重放 Expected Facts 与 geometry expectation；若几何已有而投影不读，归因改为字段衔接，不再归给写作。 |
| H2：五扇门多材料丢失是材料合同限制 | 检查原 Text→Brief ambiguities→BIM JSON→IFC，独立验证当前 Schema 能否表达 IfcMaterialList；拒绝时，不靠要求模型更认真恢复。 |
| H3：窗记录楼层被宿主规则覆盖，明确说明可避免静默修改 | 相同完整公开文本、同一注册 Brief Prompt/Schema/Provider 配置；B仅在A后追加通用“记录楼层与宿主关系分别保留；不支持就说明”规则。比较位置、host、记录楼层、真实结构归属与阻断状态。每臂一次，不把差异当统计结论。 |
| H4：三面墙不是整体位移，而是源截面与重建截面不同 | 对原/重建 IFC 独立提取截面类型，比较有/无开口布尔后的包围盒；若未切洞也有差异，不能只归因为洞口定位。 |
| H5：34 unassessed 来自测量方法标记 | 逐项统计跳过原因；分开报告可比包围盒和不可同口径的轴/本征尺寸，不把跳过当错误或通过。 |

## 实际边界

只新增离线诊断脚本、Brief探针运行器、测试和本报告；不修改生成器、比较器判据或生产 Schema。旧 hxp 是 development；测试中的同名对象只是定位入口，不是匹配真值。Provider只接收已公开设计说明；归因文件、源IFC和Compare不传入。B臂不增加任何尺寸或模型专属规则。

真实探针复用已经准入的公共 Brief controller。先核对祖先138项阶段验证，再对未变的Brief路径和新增运行器做针对性离线复验；无 Full Preflight。使用现有累计账本，起点1,052,352 tokens（含一次用量未知连接失败的293,791保守占额）；累计重建侧实际8次，非旧轻量summary误记的7次。本轮最多两次Brief调用，不进入Generator。由于旧64k实际截断，两臂统一使用已授权128k输出/128k输入、thinking开启；预算总上限仍200万、重建侧总12次。失败计费、响应与错误原样保存，连接失败或截断后停止付费回到离线诊断。

## 证据位置

`scripts/ifc2text/attribute_roundtrip_v01.py`：重放原始链路并保全字节。

`scripts/ifc2text/attribution_probe_v01.py`：相同公共入口的A/B诊断探针。

`dataset/processed/experiments/ifc2text-attribution-20260921-v01/`：逐阶段事实、离线准入与真实响应。结果和下一步见后续收尾报告，不在此预填成功。
