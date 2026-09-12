# text2IFC 当前分支合入 main

2026-09-12 启动，2026-09-13 收尾。

本次将已清理的 `codex/workflow-dataset-links`（241a5c24）合入 main（5db5e82e），保留双方真实历史。main 此前已整合 Zcode（d0e18fa0）；本次保留它的代码、C1–C5 Proof 和重构归档。仅进行合并、冲突协调及聚焦离线验证，没有新 Provider 调用或新增产品行为。

## “先收纳推送，再删除旧源文件”的含义

旧源文件是原运行目录中的那份副本。有效 IFC、请求、原始响应、失败与 token 账本先保存在 Proof／experiments，确认备份已提交并推送，再删除已获批准的旧路径副本，最后提交删除记录。删除不涉及当前 Proof 成品或归档后的过程证据。旧路径通过实验映射追溯；此前完整清理结果见[整理报告](../development-cleanup-20260912/REPORT.md)。本次没有重新执行旧目录清理。

## 合并处理

- 生产代码自动合并，无直接文本冲突；只手工协调 4 个索引／导航文件。
- Prompt registry 为两边条目的并集：108 个唯一 ID，共有条目的内容和哈希没有变化。保留 main 独有的 6 个门窗 profile 和当前分支独有的 22 个 Prompt，不重新发布或覆盖旧版本。
- Proof 索引保留光庭与 C1–C5，共 10 个集合、58 个直接展示案例。人工状态和机器状态沿用原记录；双层社区阅读楼的独立 review 集合仍不计入这 58 案。
- 保留 `archive/zcode-local-20260905/refactor-workspace.zip`。此前退役的 1,754 条跟踪路径在合并树中没有重新出现。
- main 工作树初始显示 197 项修改，但逐项 Git 规范化内容均与 HEAD 相同；只刷新明确路径的索引，文件未改，暂存差异为零后才执行合并。原工作树的 ifc-bench 修改保持独立。

## 验证

| 检查 | 本次结果 |
|---|---|
| Prompt、profile、Proof 人读约束、开敞墙与配色聚焦 pytest | 43 passed，15.93 秒；[日志](focused-pytest.txt) |
| 两边 Proof 冻结内容的 Git 对象保留 | 当前分支 4,564 条、main 4,028 条；无遗漏或改写。双方集合重叠，不相加为文件总数 |
| Proof 索引路径 | 10 个集合的目录、manifest 和报告均存在 |
| 两版光庭 IFC | 文件哈希与验收／参考记录分别相同，均以 IFC2X3 重开成功 |
| Zcode 重构 ZIP | Git 对象保持不变 |
| Provider、Full Preflight、全仓哈希／LFS 重扫 | 未运行 |

首次 Proof 对象检查把新增 C1–C5 导航造成的 `repair/README.md` 差异当作冻结内容，检查因此停止。随后明确区分四个导航文件和集合证据重查；没有修改 IFC 或证据预期值。详见[聚焦产物核对](focused-artifact-checks.json)。

本次没有重新安装或改写 accepted 集合，未重跑完整 curator，也不宣称全仓测试通过或模型能力提升。旧整合报告中的全量 pytest 中止及 Torch 进程加载限制仍是历史未完成项。

最终使用普通 merge commit 和普通 push，不创建 PR、不改写分支历史。报告随合并提交保存；最终提交号和远端一致性由交付消息报告。
