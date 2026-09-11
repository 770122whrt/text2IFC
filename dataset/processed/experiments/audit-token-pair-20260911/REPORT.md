# Audit 去重：一次真实配对实验

日期：2026-09-11。状态：实验完成，未生成新 IFC，未登记 Proof。

使用 B 修复后冻结 Audit 输入，向 api.deepseek.com 的 deepseek-v4-flash 发送去重格式和原格式各一次。实际输入减少 **24.20%**；两次通过生产 Audit 输出合同检查，接受结论与用户保留的已知缺陷状态一致。仅为一个已见案例的可行性结果，不证明整体质量不下降或成功率提升；默认仍为 full。

## 实验与实测

运行前冻结 [protocol.json](protocol.json)、[authorization.json](authorization.json)、[payload-preview.json](payload-preview.json) 和两份 Prompt。顺序 deduplicated → full，实际HTTP请求字段仅 messages 不同；每次输出上限65,536，输入保护131,072，其他设置一致。输入保护仅适用于本实验。去重只复用完全相等的 JSON 证据，确定性还原校验保全信息；用户请求、Brief、完整候选不删。

| Provider 实际用量 | full | deduplicated | 减少 |
| --- | ---: | ---: | ---: |
| input | 91,765 | 69,558 | 22,207 / 24.20% |
| output（含 reasoning） | 6,033 | 4,160 | 1,873 / 31.05% |
| 其中 reasoning | 5,452 | 3,251 | 2,201 |
| 合计 | 97,798 | 73,718 | 24,080 / 24.62% |
| input cache hit | 91,520 | 0 | 不作节省率解释 |
| input cache miss | 245 | 69,558 | 不作节省率解释 |
| 活动秒数 | 28.563 | 24.281 | 单次观察 |

共 **171,516 token、52.844活动秒**；共用上限2次/500,000 token/900秒，无失败、重试或未结预留。总历时约61.868秒。reasoning已含于output，不能重复加总。缓存命中差异很大，不能将token减少率当作费用减少率；未作价格归一化的费用结论。输出与推理减少也可能受采样影响。

响应ID：去重 `2524062e-0bd4-414b-a764-c10381762bd1`；原格式 `6509e3d3-5656-4c19-b3d4-f349ead59276`。原始请求、响应、usage和事件保留在 [deduplicated](live/deduplicated/) 与 [full](live/full/)；[账本](live/generation-budget.json)；[逐字段对照](comparison.json)。

## 质量结果与限度

两次均为 audit/3.0、accept、blocking=false、deterministic_gate_status=passed；`reference-stair-walking-clearance` 均为 retained_known_issue，并声明未做完整建筑规范审查。这不代表本次重新运行了生成、编译或独立IFC工程验算。

输出并非完全一致：full 的 findings 为空，去重有两条 info、nonblocking 说明，分别重复保留缺陷和总结确定性检查；full 在 design_review 中给出更多限制与证据路径。预先冻结的关键判断通过，但信息组织有波动，不能宣称严格质量等价。输入下降来自实际发送文本的重复证据减少，输出下降的因果关系尚未建立。

收尾分析最初错误要求 findings 为空、比较包含session_id的本地包装，以及将Windows文件字节与LF渲染文本哈希直接比较，断言因此中止；这些均非预注册判据。随后按真实HTTP字段、线上文本哈希和原判据核验，记录输出差异，未改变冻结协议或原始响应。UTF-8文件正常。

## 验证与边界

- 6项失败复现提交为 `2d62595a`；实现runner后，与上下文测试共42项通过。另复用已冻结的130项相关公共路径回归，计数有重叠，不相加当新覆盖量。见 [validation](validation/)。
- [准入](admission.json) 继承已准入Generation路径，限定本次Audit实验；调用前及收尾文档更新前核对1,475份绑定，无不一致。未运行Full Preflight。
- 线上Prompt文本与冻结哈希一致；HTTP请求除messages外一致；源输入未变；secret-like扫描0发现。
- C账本哈希未变，仍4次/300,540 token/886.717活动秒；本次未使用或重置C预算。
- 未发送原IFC文件、private Gold、其他任务数据或凭据正文；未修改accepted Proof。准入保留为本次调用历史快照，收尾文档更新后不能直接作为新调用准入。

## 下一步

小实验结束，其他token研究后置，返回C型教学楼。对 Brief 将“洞口与任何同层 IfcSpace 重叠”一律视为冲突的规则建立通用正反例，区分明确的楼梯交通空间包含关系、普通房间真实冲突和用途不明情况；再新增版本修正规则、验证公共澄清路径。不能为C特判或跳过独立几何检查。C尚无最终IFC，未进入待人工验收Proof。
