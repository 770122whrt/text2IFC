# text2IFC 清理与分支整合报告

当前结果：当前分支和 Zcode 已完成真实历史合并；采用用户最后确认的精简验证范围。main 发布结果以最终 Git 推送核对为准。本轮真实 Provider 调用为 0。

## 已完成

- 当前分支以 d2a62b76 为基线，从远端 main（cbd4e158）创建隔离整合分支；f997b7cf 合入当前分支，f49bbf42 合入 Zcode（d0e18fa0）。原工作树没有切换或被覆盖。
- 生产行为以当前 text2IFC 为准，保留最新 Generation、Repair 外观和语义保全。Zcode 补入标识集合顺序容忍、门窗复用 Type 几何定位、门开口数量授权、混合构件语义以及属性缓存指纹等独有修复。
- 同名 v0.12 Prompt 保留当前发布字节；Zcode 历史版本及 registry 保存在 archive/zcode-local-20260905/published-contracts。新增门 profile v0.4、窗 profile v0.3 和 profile Schema 0.4，明确保留用户容差，旧 intent 0.5–0.9 维持当前分支路由。
- 语义包展开复用既有 expand_semantic_bundles，移除重复算法；修复数量属性包展开错误。实验输出改用 pytest tmp_path，避免向仓库根写临时文件。
- 历史 IFC 路径通过已有迁移登记和其中的哈希定位，不改冻结 JSON、不恢复旧 train/test 目录；未知、越界、重复映射及内容漂移均拒绝。Windows Schema 检出固定 LF，保留已发布字节和原有哈希断言。

## 清理与保留

- 经用户明确批准，删除 93 个重复 scratch 单文件，共 1,334,134 字节；保留副本不变。准确路径及结果见 SCRATCH-CLEANUP.md、scratch-deletion-results.jsonl。
- 319 份开发辅助脚本和历史测试日志已归档到 dataset/processed/experiments/development-support-20260912：388,693,628 原字节，ZIP 18,917,819 字节。原文件尚未删除。
- 117 个可确认来源的 pytest 临时目录已备份为原工作树 .tmp/cleanup-recovery-20260912/pytest-workspaces.zip：111,195 文件、1,222,538,840 原字节，ZIP 242,365,843 字节。仅为本地恢复包，原目录未删除，不计 Proof。
- 本轮旧基线输出 9 目录／54 文件已复制到本报告 baseline-runs；原目录未删除。
- 下一批准确清单在 NEXT-CLEANUP.md、next-cleanup-proposal.json。尚未获该批批准，不执行删除；本次快速合并不以扩大清理为前提。
- 不删除有效回归测试。盘点的 332 个原跟踪 Python 测试文件没有整文件重复；保留兼容、失败、回滚和保全断言，补充迁移与组合语义回归。旧测试的默认版本断言按当前已发布合同区分，未放宽实体/值保全判断。
- 保留 Zcode 全部恢复归档，尤其 **archive/zcode-local-20260905/refactor-workspace.zip**：含重构镜像、交接文档、脚本及 tmp/source-snapshot。此重构仍是历史备份，不宣称其全部设计已接入当前生产代码。
- 原 ifc-bench 子模块用户删除项、访问权限不明目录、会话恢复材料及其他工作树均保留；不清理 Git/LFS 历史，不删除分支。

## Proof 与实验入口

统一入口：dataset/processed/proof/README.md；实验入口：dataset/processed/experiments/README.md。

- A/B/C 等既有集合保留人工验收状态和冻结原字节。
- Zcode 历史已接受 C1–C5 新增规范人读入口 repair/phase12/c1-c5-damage-restoration；原 142 文件均通过 manifest 旧路径映射保留，人工状态沿用原接受记录，没有捏造新验收。
- C1–C5 的确定性 offline replay 另归档 experiments/repair-c1-c5-offline-20260903-v2（152 文件）。两个旧 Proof 目录暂保留至集中删除批准，不把 offline replay 当成真实 Provider 成功。
- 当前索引直接展示案例 51→56。双层阅读楼中历史机器阻断状态不被人工接受覆盖。

## 验证结果与边界

用户最后要求减少测试、简单 preflight、停止大范围哈希检查，以尽快合并。以下如实区分：

|检查|结果|
|---|---|
|最终聚焦检查 final-light-preflight|111 passed，40.73 秒|
|旧 profile／Schema／默认版本相关检查|28 passed；保留原 Schema 哈希断言|
|历史源路径与 C2–C5 Type 保全|13 passed，32 deselected|
|此前组合语义／保全聚焦检查|125 passed；另有 32 项路由及 12 项外观组合检查通过，具体日志保留|
|公共链路测试|123 passed／4 failed 后，4 项测试源注入问题修正并聚焦通过；不合并计成一次全通过|
|静态合同检查|编译通过；63 Schema、86 Prompt 注册项、21 profile 检查通过|
|9 个人读 Proof 集合|布局、角色、路径和 IFC 重开通过|
|C1–C5 完整 curator|5 案通过；使用字节校验路径映射，不改冻结记录|
|A/B/C Generation 离线 Final Acceptance|3 案通过；语义、几何、编译重读、Audit 绑定及 secret scan 通过；冻结来源不变|
|全量 pytest|运行到约 70% 后按用户要求停止，未完成、未判通过；原日志保留|
|额外 composite 全组检查|按用户要求中止，未判通过|
|真实 Provider、新 token 实验|未运行|
|全仓 Git/LFS fsck、扩大哈希重扫|按用户最新范围不执行|

全量探索过程中发现旧路径、历史默认版本断言和本地 Torch DLL 访问异常。路径与上述合同夹具已聚焦修正；Torch 在独立进程加载正常（torch-isolated-probe.txt），全量进程内的加载顺序问题尚未完成复验。隔离工作树通过本地 junction 引用已有 BGE 权重，没有下载或修改权重。**本次是经聚焦验证的分支整合，不是全仓测试全通过或系统能力提升结论。**

暂存检查中的空白告警主要来自冻结历史 Prompt、Proof 和失败测试 XML；为保留证据未重写这些字节。提交不包含 dataset/external 子模块指针变更。
