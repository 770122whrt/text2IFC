# Zcode 有效重构接入

基线：`a25ec1d4`，分支 `codex/workflow-dataset-links`。用户要求将旧镜像中有价值的重构落实到当前代码。使用当前函数体与合同，不覆盖为旧版本；归档退役另见 [archive 报告](../archive-retirement-20260913/REPORT.md)。

## 1. 生产评估与私有基准比较：已接入

- `production_evaluation.py` 承接生产输入、生产评估和公共／基准复用的内部计算；`benchmark_evaluation.py` 保留私有输入、比较、投影及“不得提升失败生产结果”的检查。内部计算仍可由基准比较器传入私有模型，公开生产入口始终使用受限输入并禁止该来源。
- 12 个生产消费者改用生产模块，包括当前 orchestrator、离线／UAT 和 C1–C5 执行器；旧导入重导出同一对象。兼容 workflow 仍保留独立的基准比较入口。
- 16 个迁移函数／类的 AST 与当前基线一致，只改 policy 常量名称，值仍为 `phase8.1`。加速调度测试的 monkeypatch 指向新归属模块，原断言保留。
- 修改前现有回归 29 passed；新增导入边界检查 2 failed，分别命中公共 orchestrator 加载私有基准模块、新生产模块缺失。修改后同组加调度回归 44 passed；评估合同、L1、策略、公共应用、终态、安全与澄清回归 167 passed。共 211 项聚焦离线检查通过。

这验证职责迁移及已覆盖路径的兼容，不代表发现了既有 Gold 泄漏，也不代表系统修复成功率提高。

## 2. Proof 校验独立成包：已接入

`text2ifc_proof` 承接当前集合校验、Door 三方审计和 live transcript 审计。校验器不再导入 curator／runner，10 个脚本消费者直接使用新包；两处旧脚本保留 CLI 与 Python 模块别名。当前后续新增的结构恢复与冻结路径处理保留；集合投影仍使用仓库既有 `scripts/proof/package.py`，本次没有把整个项目改造成独立可分发的 Proof 产品。

103 个 validator 定义、33 个 Door auditor 定义在去除 import 调整后与基线 AST 一致；39 个共享 live 审计定义的 AST 完全一致。新增导入／CLI 检查初始 5 failed，提取后通过。入口／UAT 回归 117 passed、1 failed；R1／结构 Proof 回归 51 passed、15 failed。

16 个失败均在固定提交 `2d1a18bb` 的原始四个脚本上复现：4 个仍读已退役 Proof 路径，11 个旧模拟 transcript 在 profile 路由门被拒绝，1 个缺少旧 v2 准入文件。基线在子进程内加载 Git 原代码，普通导入和按文件加载均绑定原代码，工作树不回滚；未改测试断言。原始失败与基线分别保留在 [本次结果](proof-authority-tests.xml)、[原代码复核](proof-original-baseline.xml)，提取核对见 [JSON](proof-extraction-checks.json)。首次定位还运行过 R1 `-x`（16 passed、1 failed）及结构 Proof `-x`（25 passed、1 failed），均属同一失败，不能重复计入通过总数。

因此这一步是结构接入与已覆盖行为保持，不是全套 Proof 检查通过。后续修复测试数据绑定时必须恢复其原来的关键断言覆盖，不允许更新冻结 Prompt 或恢复撤回的验收资格来凑通过。缺失的 live 准入继续阻止真实调用。

## 3. 运行脚本分类：已接入

25 个当前实现进入 UAT（10）、offline（7）、curators（5）、audits（3），原文件成为兼容入口；[完整路径映射](runner-paths.json)与[使用入口](../../../scripts/ifc_repair/README.md)。标准 Python 导入返回同一实现模块，保留 `main` 与旧命令；6 个测试文件仅更新按文件加载的实现位置，避免 monkeypatch 落在转发层。所有 25 个实现的函数／类体在忽略 import 后与迁移前相同，见 [AST 核对](runner-body-parity.json)。根定位深度单独调整，R1 curator 补直接命令所需的路径引导。

准入另补一个必要边界：`REQUIRED_CHANGED_SCOPE_FILES` 保留 8 个原路径，并加入 6 个新实现／共享模块路径，防止以后只冻结兼容入口而遗漏真正执行的代码。旧准入与证据文件没有重写；新增缺失／错误哈希反例仍由原校验门拒绝。

验证记录：

- 新入口测试先命中缺失分组的失败；分组后旧／新模块、四类命令、Proof 包与公共隔离 42 passed。新增实现绑定检查也先失败，再补路径。
- 分组后的公共／UAT／属性链路初次 148 passed、3 failed：[结果](grouped-public-tests.xml)。3 个失败是本轮模拟准入夹具未补齐新文件清单，补全模拟数据后准入正例、缺失项、错误哈希、篡改证据和禁止自动 Full Preflight 共 5 passed、104 deselected：[复验](grouped-admission-fixed.xml)。原通过的其他路径未修改，未重复整组；不能把分段复验说成一次完整全绿执行。
- 属性公开链另一次聚焦 8 passed。历史 Window／Door 检查 5 passed、2 failed：[结果](grouped-legacy-tests.xml)。其中本地 VVO 五门批量修复、IFC 重开与注入失败原子回滚通过；两个失败都依赖缺失的旧 `dataset/ifc/train/vvo.ifc`，固定 `d9a91212` 原 Window runner 调用 `verify_matrix` 同样报该文件缺失。没有恢复旧路径、改变冻结清单或换源 IFC。
- 测试源码未删除，关键断言保留。18 项既有失败（上一节 16 项加旧 Window 2 项）保留为后续测试数据／夹具维护债务。本轮新增的 3 项失败已修复。

旧镜像中 README／地图目标已有当前导航替代，生产评估拆分、Proof 包和 25 项脚本分类均已实际采用。其未实施的提案（例如退休 legacy workflow、拆开 Agent 包）不因位于历史文档中就成为本轮承诺。当前 v2、诊断、assembler 和 C1–C5 已有实现保留，不能用旧镜像覆盖。

## 验证边界

本轮无 Provider 调用、Full Preflight、完整 curator 或新人工验收。现有 Proof 字节与状态不变，不删除测试以取得通过。保留其他任务的 RVT、Proof 未跟踪文件和 ifc-bench 修改。

机器生成的 pytest XML 原样保留，其 traceback 自带行末空白；Git 空白检查仅对这几份原始结果文件作排除，代码和文档检查仍执行。三步按独立提交保存，普通推送当前分支；本轮不额外合入 main。

本轮自行创建的 pytest 工作区：13 个目录、5,124 个文件／889,911,793.0 字节已清除，4 个目标不存在；原始测试 XML 与结果报告保留。仅 `.tmp/zcode-refactor-baseline` 因 Windows ACL 无法读取而保留，已请求提权执行仍未获得该目录读取能力，没有改 ACL 或删除不明内容。见[精确记录](temporary-cleanup.json)。
