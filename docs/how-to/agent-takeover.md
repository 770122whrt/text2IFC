# 接管 text2IFC

产品名为 `text2IFC`；`bimnet` 可能只是本地目录名，`BIMNet` 是数据来源。当前 Repair 实验、仓库整理与 UI 结合准备从 [STATE](../../.planning/STATE.md)和[现有清理记录](../reports/workspace-cleanup-20261017/README.md)进入。本文提供操作入口，适用合同仍以 AGENTS、Phase SPEC／VALIDATION 和验证协议为准。

## 1. 先做四件事

1. 阅读根目录 [AGENTS.md](../../AGENTS.md)，确认 Git 根、分支、工作树和暂存区，保留他人的修改。
2. 阅读 [STATE](../../.planning/STATE.md)、[PROJECT](../../.planning/PROJECT.md)，按 [文档索引](../README.md)进入所需功能。
3. 为当前问题确定调用入口、受影响模块和验证范围。历史报告和完成计划不再充当当前任务指令。
4. 行为修改先保存可复现输入和失败边界，再执行针对性验证。测试恢复方式见[精简记录](../reports/lean-branch-20261007/REPORT.md)。

```sh
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git diff --cached --stat
```

## 2. 代码地图

| 功能 | 实现 |
|---|---|
| Generation 交互与总编排 | `src/text2ifc_agent/repl_chat.py`、`interactive_cli_flow.py` |
| Brief、Expected Facts、分包 | `clarification.py`、`expected_facts.py`、`generation_packages.py`、`staged_generation.py` |
| Generation Gate／Audit／返工 | `dynamic_gates.py`、`live_pipeline.py`、`changeset_apply.py` |
| IFC Repair API／CLI | `src/text2ifc_ifc_repair/api.py`、`cli.py` |
| Repair 解析、绑定、应用和评估 | `target_query.py`、`property_resolution_coordinator.py`、`changesets.py`、`apply.py`、`production_evaluation.py` |
| IFC2Text 与往返比较 | `src/text2ifc_ifc2text/` |
| BIM JSON 合同、IFC 编译 | `src/text2ifc_contract/`、`src/text2ifc_compiler/` |
| 几何质量、材料／外观 | `src/text2ifc_quality/`、`src/text2ifc_presentation/` |
| 属性知识和数据 | `src/text2ifc_knowledge/`、`text2ifc_dataset/`、`text2ifc_text/` |
| 独立 Proof 校验 | `src/text2ifc_proof/`，不加载 Repair runner |

具体命令见 [scripts](../../scripts/README.md)。深入说明按[生成工作流](../architecture/current-workflow-and-data-flow.md)、[Repair 链路](../architecture/ifc-repair-pipeline-status-and-roadmap.md)和[IFC2Text 当前入口](../validation/ifc2text/README.md)进入。保留的旧版本入口仍可能被调用，不根据名称删除。

## 3. 必须知道的行为

- Generation 由 Ready Brief 开始；默认 `legacy_full`，显式选择 `staged` 才分包。模型不直接写 IFC STEP。
- Generation 的 BIM JSON 返工与对已有 damaged IFC 的 Repair 是两条独立流程。
- Repair 在副本上原子应用，重开后通过 L0/L1/L2 和 preservation 才发布。失败不产生成功结果。
- 检索仅提供候选；确定性 binding／admissibility 决定是否可执行。私有 Gold 和损坏真值仅供评估。
- IFC2Text 的坐标精度、支持范围与往返误差以[当前合同和结果](../validation/ifc2text/README.md)为准。
- Phase 状态、Proof 集合状态、单次 run 状态分别报告；存在 IFC 文件不等于通过验收。

## 4. 验证与资料

使用 Python ≥3.12 和 `.venv`。普通修改执行受影响路径的 scoped validation；真实 Provider 前遵循
[阶段准入协议](../validation/agent-capability-evaluation.md)。全仓 Full Preflight 仍需说明范围并获得用户明确授权。
2026-10-07 精简提交曾按授权退役测试，验证检查点和按需恢复方式见[精简记录](../reports/lean-branch-20261007/REPORT.md)。当前测试以实际保留及恢复的相关集合为准，不从历史退役记录推断整个 tests 目录仍为空。需要的测试缺失或准入无效时阻断真实调用；静态编译和旧检查点不能替代针对当前代码的阶段准入。

`dataset/processed/proof/` 是冻结证据；`experiments/` 是历史实验；`agent-demo/`、`ifc-repair/`、`ifc-repair-runs/`
仍有运行时或验证消费者。数据来源和许可证查 `dataset/sources/`、`dataset/manifests/`。
不要默认扫描整个数据集。仅对明确、已解析、处于授权范围内的路径执行删除。

提交前检查 diff 和验证结果，使用授权分支。交接说明修改内容、命令／结果、失败／未测项、commit 与远端状态。

## 5. 最小调查、执行节奏与额度

开始编码前应能回答：

1. 用户要求的是诊断、修改、验证、报告，还是 live run？
2. 哪个 SPEC/PLAN/VALIDATION 是当前权威？
3. 失败发生在哪个阶段，违反了什么 invariant？
4. 哪些文件属于本任务，哪些是已有用户修改？
5. 最小可复现测试是什么？
6. 最终允许声称的是 bug fixed、offline pass、live viability，还是 accepted Proof？

搜索优先使用 `rg` 和 `rg --files`，并从相关包、测试或文档开始。只有现有证据
不足时才扩大范围。

### 5.1 连续执行与上下文

批量任务、测试等待、轮询和日志汇总交给持久化脚本或现有调度器。脚本保存会话、
累计预算、日志位置和终态，并在内部等待或轮询；对 Codex 只输出状态变化、完成、
异常或需要人工处理的摘要。正常未变化的等待不触发新的模型判断。

Codex 在阶段启动、完成、异常、澄清回复和决策边界介入。没有自动唤醒能力时，
让脚本持久运行并留下完成／异常回执，后续读取回执；不要以频繁模型轮询代替通知。
脚本故障仍保留原失败，恢复方式遵守本阶段的幂等、预算和安全停止合同。

大型日志先由脚本筛出错误、变化、计数和相关文件行号，再按需读取原文。摘要不覆盖
原始证据。子 Agent 仅用于收益明确、职责独立的工作，接收最小背景和文件范围；
无必要不继承整段历史，也不为等状态额外派 Agent。

### 5.2 推理档位的实际控制

常规状态检查、整理和简单修改优先 low／medium；复杂定位才提高，定位完成后回到
常规档位。先减少无关上下文和无变化的调用，而不是靠设置名称声称已节省额度。

当前主任务没有工具可直接切换自身模型或推理档位，需要用户在 Codex 界面调整。
子 Agent 的 `reasoning_effort` 可在非完整历史继承时指定；创建或获准消息发送到其他
任务的 `thinking` 只控制那个任务，不能据此声称本任务已切换，也不为换档另建任务。
工具枚举包含 low、medium、high、xhigh、max，部分模型支持 ultra；其他任务的
`thinking` 还枚举 none／minimal，但实际组合须经对应模型验证。
完整历史继承的子 Agent 沿用父任务设置。写入规则不等于设置生效，未经授权不改全局配置。

可用档位随模型和客户端变化，参见 [官方配置参考](https://developers.openai.com/codex/config-reference)。

### 5.3 三种预算与低额度检查点

| 预算 | 计数与用途 |
|---|---|
| Codex 账号额度 | 用账号工具返回的适用额度窗口判断；剩余为 `100 - usedPercent`，空值表示未知。不是实验 API token，也不是 credits 余额 |
| Codex Goal 预算（如启用） | 由 Goal 工具报告的线程目标使用量／剩余量；不是账号剩余百分比。开启长 Goal 前说明实际返回口径；未确认的输入、缓存、推理或子 Agent 计入方式明确标为未知，不虚构换算 |
| 实验 API 预算 | 按实验账本累计被测模型可获取的用量，未知用量另记；保留现有费用和超额授权，不转填 Codex Goal 的 `token_budget` |

长任务分阶段执行；阶段开始、完成或真实额度异常时核对账号额度，不在状态轮询中
查询。需要新的 Goal 预算值时再问用户；普通任务不自动开启 Goal。账号消耗还受
模型、上下文和工具使用影响，不能从实验 token 推算，见 [官方额度说明](https://developers.openai.com/codex/pricing)。

任一已知适用账号窗口剩余 ≤20% 时，保存检查点，并向用户汇报剩余额度和当前进度。
用户继续对话后，继续交流并推进已授权工作，无需另行确认恢复；不能仅因低额度
阻止后续对话或执行。检查点沿用当前状态入口，记录任务／会话 ID、当前步骤、
产物与日志、累计实验用量、未处理问题和恢复命令；不另造同义报告。
如果平台实际限额导致无法继续，保留状态并说明具体限制。后台任务仍遵守既有
协作停止与持久化合同；低额度本身不触发暂停，不直接杀进程、重开挑结果或丢记录。
此阈值不是实验预算变化或新的费用审批。

## 6. 验证强度如何选择

验证应匹配本次变更可能引入的真实失败：

| 变化 | 起步验证 |
|---|---|
| README、报告或链接 | 路径、链接、声明和格式检查 |
| 新增人读 Proof 视图 | 必需文件、角色、authority link、IFC reopen、repair/no-output 互斥 |
| 普通行为修复 | 先写聚焦失败测试，再运行相关回归 |
| Agent/Prompt/Schema 行为 | failure family 与 changed scope；首次进入阶段或 admission 失效时才重建适用 seam／完整离线链路 |
| 新 genuine Provider run | 复用仍有效的阶段准入，所有适用检查通过后才允许 live；保留每次真实 attempt |
| accepted collection 或 evidence semantics | 对应 Proof validator；只有合同要求时运行 curator |

不要用 curator 代替定位，也不要因为只改导航就普遍重跑 curator。反过来，
source mutation、unoffered identity、inadmissible property、missing repaired IFC、
no-output 案出现 repaired IFC、broken authority link 或适用 Proof gate 失败仍必须
fail closed。

已经充分通过的检查不因交接、整理报告或等待结束重复运行；仅在新修改、失败或
实际风险增加时补充验证。缺失／失效准入仍阻断真实调用，不自动升级为全仓 Preflight。

## 7. Agent 与确定性代码的边界

生产 Repair Harness 中，Agent 可以理解请求、提出澄清、在有界候选中给出语义建议，但不能：

- 直接生成或修改 IFC STEP；
- 越过当前 offered candidate set 绑定目标；
- 通过别名表、案例文本或错误输出兼容映射绕过 admissibility；
- 覆盖确定性 Gate 的失败；
- 把 private Gold、pristine IFC 或 mutation truth 放入 Provider Prompt；
- 把一次成功 live run 描述为系统级能力提升。

确定性代码负责 identity binding、scope、transaction、IFC apply、reopen、L0/L1/L2、
preservation 和 publish gate。涉及真实 LLM 前，完整要求见
[`agent-capability-evaluation.md`](../validation/agent-capability-evaluation.md)。

对比实验按其既定执行合同运行：A/C 可自行选择脚本或直接编辑 IFC，D 保留官方
原生工具，通用执行器不额外引导方法。这不改变源 IFC 不变、私有隔离和统一独立评分要求。

## 8. 常用验证入口

优先使用仓库 `.venv`，Python 版本须满足
[`pyproject.toml`](../../pyproject.toml) 的要求。示例命令仅表示入口；实际范围仍由
适用 Phase 合同决定。

```powershell
# 聚焦测试
.venv\Scripts\python -m pytest <relevant-test> -q

# Python 静态编译检查
.venv\Scripts\python -m compileall <changed-python-path>

# Plan 07 人读视图
.venv\Scripts\python scripts\ifc_repair\install_plan07_human_proof.py --validate-only

# R1 人读布局
.venv\Scripts\python scripts\proof\validate_human_views.py `
  --root dataset\processed\proof\repair\phase12.1\r1

# Git 格式边界
git diff --check
```

Windows 下 pytest 临时目录权限异常时，使用仓库内明确的 `--basetemp`，先创建其
父目录。不要指定 Proof 或现有运行目录作为 basetemp。不要将跳过、超时、替代验证
或较窄的检查描述为完整通过。

## 9. Dataset、run 与 Proof 的清理边界

- 成品及冻结机器权威从 `dataset/processed/proof/` 查找；实验、失败归因和归档运行从 `experiments/` 查找，当前依赖的源基线留在 `ifc-repair-runs/` 等目录。
- 已收纳的证据保持原字节、验收状态和旧路径映射。根目录不再写 `composite-evidence-*`，回归输出使用 pytest `tmp_path`。
- `test*.py` 可能是仍有独立覆盖价值的回归源码；不能根据文件名或一次修复成功就删除。一次性执行器、临时输出和生产回归要按消费者与保留依据区分。
- 历史清理许可只适用于当时获批的准确清单，不是以后销毁失败记录或任意 run 的通用授权。新增删除项先核实依赖、证据保留位置和用户授权范围；归属或权限不清的内容保留。
- 真实成功、失败及 token 账本不因重试成功而改写。确有获批销毁的历史项时保留退役记录与证据局限，不能声称失败分母仍完整。

删除前先解析准确路径并确认它位于预期仓库子树；再用 `git ls-files` 判断是否已被
跟踪，并检查链接与活动工作树。不要对 dataset 根目录、仓库根目录或未解析变量
执行递归删除。Windows 受限沙盒曾把不可读 Proof 误报为删除；遇到大量 `D` 或权限
错误先核实真实文件状态，不据此 restore、重新收纳、重置权限或删除。

## 10. 完成任务时如何交接

按任务规模简述结论、修改、实际验证、证据等级和剩余问题；适用时附 live run ID、
产物、Git 状态及恢复入口。记录 skip／timeout 或范围限制，不把局部通过说成全仓
或 live 成功。详细命令和机器证据留在现有权威，交接链接过去，不再全文复制。

当前实验结果保持一个人读主入口，历史记录独立保留；其他索引与 `STATE.md` 只链接
并说明执行位置。变动数字只在其负责的结果表／账本更新，不同步抄写到多份报告，
也不为同一批充分保存的证据重复生成归档。
