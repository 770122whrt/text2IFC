# C 型教学楼：最新代码上的一次新真实生成

2026-09-11。**本次重新调用真实 Provider，产出完整 IFC2X3；3次调用完成，未进入修复 loop。Audit accept，独立重开 IFC 检查485项通过。待人工检查，未登记 accepted Proof。**

[下载/打开完整 IFC](generated.ifc) · [原始中文输入](request.txt) · [已批准入口澄清](CLARIFICATIONS.md) · [整体图片](views/overall.png) · [可旋转查看](views/viewer.html)

实际请求是三层向东开敞的 C 型教学活动楼；原输入保留入口8.4米原文，实际遵照用户随后批准的西墙入口中心4.2米澄清。完整问答见 [conversation.json](conversation.json)。本次没有使用上一轮 Brief、候选或 IFC 作为生成输入，没有手工改写生成结果。

## 真实调用与产物

- 运行ID：`05c6de3a19ed20f9`，代码快照 `d0c39dc4`，已包含 `35813a00` 的跨层名称语境修复。
- 目的地 `api.deepseek.com`，请求模型 `deepseek-v4-flash`，响应模型字段 `deepseek-flash`。
- Brief 首次通过；Generator 首次通过；确定性编译/重开及几何、语义、楼层名称检查全部通过；真实 Audit 接受。
- 原始 response、实际发送文本和终态完整保留，见 [执行记录](live-run/execution.json)、[最终验收记录](live-run/final-acceptance.json)、[逐次用量与响应ID](usage-summary.json)。
- `generated.ifc` 与本轮机器输出逐字节一致，上一轮文件保持不变。

| 阶段 | Input | Output（含推理） | 其中推理 | 总token |
| --- | ---: | ---: | ---: | ---: |
| Brief | 19715 | 46754 | 35821 | 66469 |
| Generator | 43246 | 39777 | 17184 | 83023 |
| Audit | 62316 | 8912 | 7334 | 71228 |
| 本轮合计 | 125277 | 95443 | 60339 | 220720 |

C 历史累计20次、1597750 token、2628.983秒活动时间；旧失败和本次调用共用原32次/200万token/3600秒限额。Provider 前缀缓存计入原始usage，没有重复利用旧响应。与上次调用数不同不能单独证明token优化效果或系统成功率提升。

## 检查结果与边界

[独立 IFC 检查](independent-ifc-check.json)485项全部通过，确认三层C形、开敞缺口、墙角与洞口、全楼9个空间（每层3个）、2个梯段、21扇窗、7樘门、门窗宿主/模板、部件分色、砖与混凝土、最小必要门Style等。评分器和冻结请求预期没有修改。

原生 IFC 网格导出64个有表示实体、失败0。整体视图已简单查看，体量、窗列和暖色配色协调；[首层俯视](views/ground-floor.png)、[窗近景](views/IfcWindow.png)、[门近景](views/IfcDoor.png)供人工继续检查。俯视图仅为检查墙界而隐藏上层及梯段，不代表源IFC缺少楼梯。

原始 Audit 末段把“全楼9个空间”误写为“每层9个空间”；独立检查和实际IFC均为每层3个、全楼9个。该叙述错误已在这里更正说明，原响应保留，不能把模型文字作为构件数量权威。

本次准入继承未变的阶段证据，并核对名称修复后的99项相关回归（含两种策略公共链路）及本次新运行器2项离线检查，见 [admission.json](admission.json)。未运行 Full Preflight，没有人工验收或结构、消防、楼梯净高、可施工性等全面工程认证。本次仅证明当前配置在这一已见案例的新真实运行成功。
