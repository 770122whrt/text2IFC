# C 型楼：第一次同步运行结果

状态：真实 Brief 失败，未生成 IFC，未登记 Proof。原 REPORT.md 是运行前快照，不是最终结果。

run `cf0a6e858a2a74a8` 使用已验证的新普通 Prompt v2.10，从原输入重新提取 Brief。Provider 正常 stop，但返回 JSON 缺少结束括号；解码失败在第17507列，不是本轮输出截断。原文、响应、失败校验和会话记录均保留在 [live-run](live-run)。没有自动补括号、伪造成功 Brief 或发布 IFC。

这次输入18641、输出47974（包含reasoning35884），合计66615 token、172.296秒；C累计5次367155 token、1059.013秒，含旧失败。response_id：04107290-427d-4196-95cb-f93a4825fa34。

离线通过实际适配器/公共Brief入口重放同一响应，仍按JSON_DECODE_ERROR阻断，网络调用0，源响应不变。见 [诊断](failure-diagnosis.json) 与 [复现脚本](diagnose_failure.py)。这证明严格解析守住边界，不证明模型JSON稳定性已修复。

无效响应提示入口与梯段距离过近；独立核对请求坐标后，向用户真实提问。用户批准入口中心南移至4.2米，后续合法运行单独保存在 [澄清后报告](../c-shaped-clarified-entry-20260911/REPORT.md)。原始请求、失败和账本保持原样，后续累计使用新账本。
