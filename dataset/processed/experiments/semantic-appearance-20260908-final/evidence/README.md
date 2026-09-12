# 离线验证记录

这些是本任务的 pytest 记录，不是 Provider attempts 或 accepted Proof。

- `semantic-stage-final.xml`：451 passed / 1 failed。失败发生在更新新 Prompt 文件与 registry 哈希之间；测试读到了短暂不一致状态。原始失败记录保留。
- `semantic-frozen-final-recheck.xml`：冻结文件后的相关 47 项全部通过，覆盖该失败、四模板两策略、完整语义/详细门窗最终验收、共享 Type、Prompt registry 和颜色值检查。
- 首轮阶段回归为 406 passed / 1 failed；畸形 Type 引用在材料继承路径的异常已修复，之后相关 91 项通过。

范围为 Compiler、Contract v2 和相关 Agent/Repair 文件；不是全库 pytest 或 Full Preflight。测试中标为 live 的历史函数名仍使用注入 fake/replay Provider，本任务真实 Provider 调用数为零。首次渲染失败和其他中间目录保留原处。

首轮 Design Brief 新调用降版防护补测先红后绿。扩展至旧 API/CLI 兼容时发现 5 个旧测试仍向新的默认调用返回 2.0；旧版本回放改为显式选择 2.0，新默认 CLI 的 fake 响应改为 2.1。原始 `semantic-design-contract-final.xml`（70 passed / 5 failed）保留；最终 `semantic-design-contract-recheck.xml` 为 75 passed / 0 failed。此组包含新版首轮拒绝降版、完整房间/详细门窗最终验收、材料/属性/Type、两策略、真实持久化及注入 fake Provider 的澄清/CLI 路径。

验证对应已提交代码 `82476b5b`（外观/几何及语义依赖亦在其历史中）。该 SHA 仅记录这次确定性实现，不是模型能力指标。

原始失败 XML 中保留了 pytest traceback 的行尾空白；git diff --check 会对这些日志行告警。未为格式检查改写机器记录，代码、文档与视图的 scoped diff check 通过。
