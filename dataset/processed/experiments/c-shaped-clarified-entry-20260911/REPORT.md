# C 型教学楼：入口澄清后的真实运行

状态：**audit_blocked，尚未通过交付检查，未登记 Proof，未人工验收。**

用户批准首层西入口中心由距南侧8.4米改为4.2米，其余尺寸、楼梯、门窗和要求不变。[原请求](request.txt)字节不改，[真实澄清记录](conversation.json)优先修订入口位置。独立预期仅改变这一个值，评价器代码保持不变；旧8.4米模型在负对照中被准确拒绝。

run `9b00e53444a948e7` 从新的真实Brief开始，经过Generator和Audit，3次真实响应；没有运行ChangeSet。Brief ready、候选正式且结构有效、IFC2X3编译和重开成功。入口位置、数量、门窗样式和材料相关检查通过，但整体未通过。文件：[诊断用IFC](live-run/runs/9b00e53444a948e7/output.ifc)、[完整执行记录](live-run/execution.json)、[独立IFC检查](independent-ifc-check-initial.json)。

独立检查485项中11项失败：三层墙体积以及两处楼板洞口的体积、覆盖与位置。原生产gate另发现三层缺口西墙偏移500毫米，但未成功提取楼板预期；Audit又把早期路由零几何反馈与后期失败理解为机器证据冲突，保持阻断。当前文件可查看，不能称作完整合格交付。

后续离线修复和原生图片见 [门禁诊断报告](../c-shaped-gate-debug-20260911/REPORT.md)。用户无需再回答入口问题。下一待修项是Brief的矩形墙接合合同，不是更改用户设计。

本run新增216280 token；包括旧失败/实验在内的C累计8次583435 token、1375.654秒，限额仍32次/200万token/3600秒。最新权威为 [预算账本](live-run/runs/9b00e53444a948e7/generation-budget.json)。Provider请求模型deepseek-v4-flash，响应报告deepseek-flash；不得把请求别名写成精确后端模型版本。

本次准入是现有Generation阶段证据加局部复验与4项精确运行器fake测试；没有Full Preflight或盲测能力评估。admission.json是当时快照，后续代码已改变，不能直接用于下一次真实调用。
