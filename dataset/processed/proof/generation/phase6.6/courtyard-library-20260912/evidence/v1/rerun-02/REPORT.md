# 光庭真实重跑 02：单次输出达到上限

2026-09-12。状态：真实 Provider 响应截断，未进入 Generator／Audit，没有完整 IFC。此记录不是待验收 Proof。

本次输入已经通过正常 ClarificationController 构造，真实发送的用户轮次为 `turn-user-001`。与上一次漏传轮次身份不同，本次失败发生在 Provider 输出长度边界：`finish_reason=length`，输出 token 正好达到 **65,536**，JSON 正文在末尾 `fact_sources` 数组内被截断。适配器保留原始响应并拒绝解析发布，未修补残缺 JSON。

本次输入 **21,755**、输出（含 reasoning）**65,536**，合计 **87,291 token**；耗时 **227.563 秒**。累计 **4 次调用／310,268 token／826.25 秒**。失败账本已结算实际 usage，未退回到未消费状态。旧账本保持原字节。

Provider 失败脱敏路径将细分 usage 元数据替换为 `[REDACTED]`；故本次不报告精确 reasoning token 数，不从正文字符数反推。总输入、总输出及终止原因可由 [原始响应](live-run/runs/5e0a62ff38ef73c1/calls/01-design-brief/response.raw.json)复核。

下一步仅将该案例单次输出上限由 65,536 提高到 98,304；模型、thinking、Prompt、Schema、请求、公共执行路径和累计 32 次／200 万 token／3600 秒限制保持原值。Provider [官方上限](https://api-docs.deepseek.com/quick_start/pricing)支持该数值（2026-09-12 核对）。此选择是一次配置实验，不代表 token 节约或能力改善。

新尝试和配置验证放在 [rerun-03](../rerun-03/)，不覆盖此失败。若仍触及长度边界，应转入有依据的输出分段设计讨论，不能无限提高上限或拼接缺失 JSON。
