# Repair 对比实验：代码、环境核对与首批开发建议

> 核对日期：2026-09-29｜依据：本目录现行 v0.2 三份正文及启动提示词。
> 当前（2026-10-08）：B的001～010最新真实复测严格通过9/10，005已新会话真实通过，007按用户意见保留失败。[当前表](../../../dataset/processed/experiments/repair-comparison/current/README.md)与[历史备份](../../../dataset/processed/experiments/repair-comparison/history/README.md)分开；独立评分修正后基线与当前冻结产物同版重算，原报告未覆盖。未开启Goal，所有服务停止。后十题先核对Pipeline支持并制作损坏材料，用户检查后再实验。§6.15保留原批次历史检查点；两个demo仍是开发证据。
> §2–5及§6.1–6.10保留先前核对／实施时点事实。本文说明进展；机器准入与实际运行分别保存在实验工作区，不能把离线夹具当成模型成绩。

## 1. 初次就绪核对与开发建议（历史）

**已按用户第一轮反馈重写两套简单开发题，两题均为信息充分题。** 请求不用GUID、构件名或方法提示；窗题按西侧外墙的方位和现有窗排序定位，门题按二层唯一空门洞定位，开向不再强设澄清。新版附实际IFC、验收条件、来源许可和独立格式报告，保持pending_human_review供复核。工具支持准备、检查及白名单导出，尚不执行模型或问答循环，见§6。

题包形式已经确认，阶段2账本、A/C中性工具、B薄适配和独立开发评分已落地。接下来完成D与账本的接线及四组容器运行路径，并把首批5个候选制成完整人审题包。DSH安装范围已批准，付费联调另留节点。整体保持约20个不同源IFC，优先明确许可，不把同族变体当独立样本；口径见[计划§6.1](plan.md#61-源模型选择)。

核对时点影响开发顺序的四个事实：

1. **B 的公共入口可以复用。** 已有澄清、状态版本、恢复和正式发布边界，不需要复制修复流程。
2. **现有 benchmark 不是方法无关评分器。** 它依赖 ChangeSet 和 application record；可复用差分、几何和语义原语，须另建实验侧评分入口。
3. **现有生产 validator 是“相对 D 无新增诊断”，且不执行 EXPRESS。** 不能直接拿其 `passed` 填四组的最终 IFC 校验成绩，也不应为实验改写旧生产 policy。
4. **Docker及配套DSH已安装，完整四组接线仍待完成。** 同进程原生问答已验证；标准SDK没有pending question冷恢复RPC，不能把另启会话当同题恢复，见§6.9。

## 2. 实际工作区与 v0.2 核对

### 2.1 分支、权限与变更边界

- Git 根：`E:\code for project\bimnet`；实际分支：`codex/repair-experiment`。
- HEAD：`ef4b7a2d198373403d1373969a388e165b65f090`。这是本次代码核对基线，不表示工作树干净。
- 开始时 `.planning/STATE.md`、文档索引、研究登记及多份 dataset 文件已有修改；整个 `repair-comparison/` 目录和 `tests/dataset/test_rvt_pipeline.py` 为已有未跟踪内容。保留这些增量，不暂存、提交或推送。
- 受限沙盒的 Git 曾把 426 个不可访问 Proof 文件显示为 `D`；一次提升权限的只读 `git status` 没有这些删除，仅显示原有修改。不能据受限输出恢复或删除 Proof。
- 本轮未读取 `.env`、密钥或 SSH 私钥。只核对 SSH 配置中的 Host 别名，不连接远程服务器。
- 已按仓库接管指南、文档入口、STATE、ROADMAP／PROJECT 和 Agent 准入协议核对。本次是 W0，未启动 Phase 13 或其他代码阶段。

使用已安装的 `fast-architecture-review`、`documentation-contract-audit`；可用技能目录未找到 `write-technical-document`，不为此安装。一个只读子任务核对评分和制题代码；没有委派文件修改。

### 2.2 条款一致性

| v0.2 要求 | 核对结论与实施影响 |
|---|---|
| A/B/C/D，20 源 IFC、20 题、80 个任务单元 | 三份正文一致；没有发现实际四组执行骨架。SDK turn、工具调用和澄清不另增任务数 |
| A/C 中性输入，可脚本也可直接文本编辑 | 正文一致。B 的禁止模型直接输出 STEP 仍约束 B；新执行器不能复用 B 的输出禁令 |
| 冻结 D 与可写副本分开 | 正文一致。需独立目录和字节复制，不能 hardlink 同一 inode，也不能把被修改副本作为评分 D |
| 全部 20 题人审，2–4 个澄清题先按 3 个准备 | 正文一致。制题程序默认 pending；小规模评分自检不能替代人审 |
| 普通提问、同题继续、预算不清零 | 正文一致；B 已有中间状态，外部任务 ledger 及 D 问答桥未实现 |
| 保存返回推理、工具、usage、失败和摘要 | 正文一致；已有原始响应保存可复用，但跨阶段、重试、子 Agent、摘要的完整覆盖尚未证明 |
| 按任务动态预算，不继承统一 128k／900 秒 | 正文一致。旧 Generation／IFC2Text 预算只能参考实现，不能继承额度、历史账本和默认值 |
| 关系为正确数／应修数，四组独立评分 | 正文一致；当前 validator 和 benchmark 的语义缺口属于待实施工作，不是应回退 v0.2 的理由 |

没有发现需要改回研究决定的正文冲突。本轮在原文增加核对结果入口、更新执行状态，并澄清 DSH 版本与接口边界；不复制指标公式或另建版本正文。

### 2.3 GPT／DeepSeek 型号证据的边界

OpenAI 官方模型页明确列出 `gpt-6-sol`；因此 C 的目标 ID 有[官方依据][O1]。本地已有 2026-09-28 的[网关最小请求记录](../../../.tmp/openai-model-probe-20260928-155317/gpt-6-sol.json)，仅证明当时该用户指定网关的 Chat Completions 返回 HTTP 200／`OK`，不证明工具往返、长上下文、真实上游版本或此次实验准入。本轮不重测，也不改选 Astra。

DeepSeek 当前官方 Chat Completions 文档的模型枚举为 `deepseek-flash`／`deepseek-v4-pro`，DSH SDK 示例仍使用 `deepseek-v4-flash`。依据：[API 文档][D10]、[SDK 示例][D1]。不据此自动替换项目原配置，也不能把两个 Flash 名称认作不可变同一快照。正式冻结前须核对 A/B/D 实际共同可用的精确路由、返回标识与推理参数；确认过程属于后续获准联调。

## 3. 代码复用与缺口

以下为静态代码核对；本轮没有重跑旧测试，不引用历史通过数作为当前验证。

| 责任 | 现有准确入口 | 可复用内容 | 本实验仍缺什么 |
|---|---|---|---|
| B 公共修复流程 | [`api.py`](../../../src/text2ifc_ifc_repair/api.py)：`RepairAPI`，`start`（140）、`continue_with_answer`（280）、`read_result`（467）、`resume`（470） | 保留原生入口；构造器接受 Provider 注入，公共输入不含 G／mutation mapping | 外部 task/run 与 native run 绑定；只收集正式发布结果；任务总预算与问答转接 |
| 等待和发布 | [`run_models.py`](../../../src/text2ifc_ifc_repair/run_models.py)：`RunStage`、`TERMINAL_STAGES`；[`run_store.py`](../../../src/text2ifc_ifc_repair/run_store.py)：`commit_terminal_publication`（185） | `clarification_required` 不在终态集合；有 state_version、clarification_id 与持久化边界 | 映射为实验 `awaiting_user`；恢复时保持外部身份、文件和累计资源；不得读 staging 挑结果 |
| B 模型传输 | [`openai_compat.py`](../../../src/text2ifc_agent/openai_compat.py)：`OpenAICompatibleLiveProvider.generate_live`（236） | DeepSeek Chat Completions、JSON 输出、connection retry、原始 envelope 与 usage | 当前是一轮结构化响应，未实现 A/C 工具循环；固定 `response_format=json_object`、`temperature=0`，没有独立 OpenAI 实验路由配置，不应拿历史 `mimo` 名称包装 C |
| 原始推理与 trace | [`request_stage.py`](../../../src/text2ifc_ifc_repair/request_stage.py)：`_call_provider`（426）；[`provider_stage.py`](../../../src/text2ifc_ifc_repair/provider_stage.py)：`_call_bound_provider`（851）；[`property_resolution_stage.py`](../../../src/text2ifc_ifc_repair/property_resolution_stage.py)：`_call_provider`（445） | 正常返回保留 live response／events；原始 envelope 可以携带返回的 `reasoning_content`，不是只有最终文本 | 缺统一 reasoning_ref/status、task 级 request/attempt 关联；连接重试循环未逐次发出完整失败 ledger。不能宣称全部失败已保存 |
| trace 写出 | [`live_trace.py`](../../../src/text2ifc_agent/live_trace.py)：`write_provider_failure_trace`（23）、`write_live_trace`（51） | 脱敏、原始证据及引用的写出模式 | compact 模式可能只存摘要／哈希，取决于 preserve_deep_evidence；需实验侧明确保留政策，日志副本不能破坏在线工具历史 |
| 现有预算 | [`generation_budget.py`](../../../src/text2ifc_agent/generation_budget.py)、[`goal_budget.py`](../../../src/text2ifc_ifc2text/goal_budget.py)：`GoalBudget.reserve/settle` | 持久账本、预留／结算、请求阻断的实现思路 | 四组共享 task 语义、人工等待、并发在途、DSH Messages cache 口径、动态增额规则；不直接接旧账本 |
| 旧私有比较 | [`benchmark_evaluation.py`](../../../src/text2ifc_ifc_repair/benchmark_evaluation.py)：`BenchmarkEvaluationInputs`（53）、`evaluate_benchmark`（151） | B 的生产／私有比较隔离 | 依赖 `ProductionEvaluationInputs` 的 ChangeSet、application_result 和 registry；不是四组 scorer |
| 独立 IFC 差分 | [`compare.py`](../../../src/text2ifc_ifc_repair/compare.py)：`build_ifc_difference_report`（580）、`normalized_model_diff`（659）、`compare_mapped_elements`（1332） | D/R 文件差分、STEP 归一化、重复 GUID 检查、已有映射后的新 GUID 对比 | 事前合同驱动的一对一目标匹配、关系归一化与指标；mapped comparison 不负责生成公平映射 |
| IFC 规则检查 | [`ifc_validation.py`](../../../src/text2ifc_ifc_repair/ifc_validation.py)：`compare_validation_models`（54）、`_collect_diagnostics`（127） | 生产相对诊断、缓存与差分流程 | policy 为 `ifcopenshell-schema-no-express/0.1`，`express_rules=False`；实验侧需固定规则、完整执行和最终阻断错误判定 |
| 几何、语义、保全 | [`geometry.py`](../../../src/text2ifc_ifc_repair/geometry.py)：`product_geometry_bounds_in_host_mm`、`measure_straight_rectangular_member`；[`semantic_facts.py`](../../../src/text2ifc_ifc_repair/semantic_facts.py)；[`occurrence_fidelity.py`](../../../src/text2ifc_ifc_repair/occurrence_fidelity.py) | 适用形状下的度量、属性／单位／ownership 抽取 | 不能泛化为任意几何；occurrence fidelity 的通用路径只覆盖 Window/Door/Opening。整 GUID allowlist 不足以表达“允许开洞但不许改墙厚” |
| 数据身份 | [`IFC_DATASET.md`](../../../dataset/external/IFC_DATASET.md)、`dataset/external/ifc-asset-register.jsonl`／`ifc-usable-register.jsonl` | 来源、实际 assessment 字节、哈希、family/leakage_group、许可与使用条件 | usable 不等于实验题合格；只对后续候选逐一核对 IFC2X3、支持前提、独立场景与权限，不能把文件变体算独立建筑 |
| 制题 | [`mutation.py`](../../../src/text2ifc_ifc_repair/mutation.py)：`remove_window_and_opening`（189）、批量窗（326）、`remove_door`（557）、批量门（695）、`remove_structural_members`（41） | 源不变、损坏副本和 private mutation 记录 | 人工合同、分母、人审卡、答复卡和公开包；程序 valid 不等于 accepted |

另需避开两个旧入口：`build_ifc_repair_benchmarks.py` 仅面向固定历史 benchmark，默认打印、指定 `--write` 才写旧 manifest；`build_small_ifc2x3_review_batch.py` 会联网发现／下载外部模型。它们都不是本次 20 题人审材料生成器。`run_damage_restoration.py` 还会进入 RepairAPI，不能当“只制题”命令使用。

在 `src/`、`scripts/`、`tests/`、`schemas/` 定向检索，未发现 v0.2 的四组执行器、answer card、task budget 或实验 run ledger。`text2ifc/ifc-repair-comparison/0.1` 是已有 IFC 差分 schema，不能误认作本次实验骨架。

## 4. 环境只读核对

| 项目 | 本轮实测 | 对开发的影响 |
|---|---|---|
| Python | 仓库 `.venv\Scripts\python.exe` 为 3.12.4；`pyproject.toml` 要求 ≥3.12 | 足以开展首批本地离线开发 |
| IFC／测试依赖 | IfcOpenShell 0.8.5，实际 import 成功；pytest 8.4.2；Pydantic 2.13.4 | 版本可查；未据此声明几何或评分正确 |
| API 库 | openai 2.43.0、openai-agents 0.17.6 | 已安装不等于有中性执行器；首批无需新增 SDK |
| validator CLI | `python -B -m ifcopenshell.validate --help` 列出 `--rules`、`--json` | 文档命令参数存在；尚未验证真实 IFC 的退出码、诊断和规则完整性 |
| DSH | 当前 venv 无 SDK/runtime-bin，PATH 无 dsh | 无本机初始化、隔离或原生联调证据 |
| Docker | Client 29.6.2、context `desktop-linux`；Server 为 null，`dockerDesktopLinuxEngine` pipe 不存在 | 引擎当前不可连接；未启动 Desktop、拉镜像或创建容器 |
| WSL | 提升权限只读查询可见 Ubuntu-22.04、docker-desktop，均 WSL2、Stopped | 不是“没装 WSL”；可在后续获准时启动现有环境再做 canary 隔离测试 |
| 磁盘 | C 盘剩余约 22.08 GiB，E 盘约 262.70 GiB | 后续先核实 Docker 数据盘位置及镜像实际大小；本轮不迁移或清理 |
| 服务器入口 | SSH CLI 存在；有 `suanliyun-agentic-AUV`、`Aliyun-IDSagent`、`agentic-AUV` 等别名 | 只是已配置入口，未连接、未核实空闲资源／Docker，也未将 AUV 服务器指定给本实验 |

受限环境第一次查询 Docker 配置、WSL 和 SSH config 时出现 Access denied／`E_ACCESSDENIED`。只做一次提升权限的只读核实即取得上述结果，没有更改 ACL、服务或凭据。

本轮环境证据止于版本、导入、CLI help、状态和磁盘；没有运行 pytest、IFC 规则实验或全仓 Preflight。

## 5. DSH 官方调研：入口可确定，原生接入仍有工作

### 5.1 固定版本，避免拿 master 文档安装旧 wheel

2026-09-29 查询官方仓库：标签 `dsh-v0.2.0-rc.1` 对应提交 `4878cdabd87d4041bdaff61d04c966883b9fd07a`（提交时间 2026-09-28 11:48 UTC）。下列源码结论绑定这个提交，不泛指所有版本。[固定源码][D0]

PyPI 元数据显示 SDK/runtime 最新发布为 **0.1.5rc1**，SDK 精确依赖同版本 runtime；提供 Linux x64／arm64、macOS、Windows x64 制品，Python ≥3.10。依据：[SDK 元数据][D2]、[runtime 元数据][D16]。因而现在无版本约束的 `pip install deepseek-harness-sdk` 不能被写成安装了上述 0.2.0 源码。

**建议 D 的接入候选固定到已审阅的 0.2.0-rc.1 源码与完整 `sdk` profile。** 获准安装阶段再检查该版配套制品；若尚未发布，则按上游 `scripts/build-python-release.py` 从同一提交构建 SDK/runtime 配套 wheel，记录哈希及镜像 digest，构建只发生在独立环境。不能把源码中占位的 `0.0.0.dev0` 当正式发行版。若构建成本不合适，可另行将候选降为配套 0.1.5rc1，但必须按它对应提交重核接口，不能套用本文的新源码能力。构建依据：[runtime 说明][D3]。这只是后续版本建议，本轮没有下载 wheel、clone 仓库或执行构建。

### 5.2 SDK、profile 与运行位置

Python `DeepSeekHarness` 通过 stdio JSON-RPC 启动 `dsh --profile sdk`；完整 `sdk` 基于 dsh-base，含原生提示、工具和编排。`sdk-minimal` 缺少部分文件工具、子 Agent 和压缩等，不适合作为这里的完整 D。运行完整打包 wheel 不要求宿主安装 Node；源码构建是另一条准备路径。依据：[SDK 接口][D1]、[runtime 包][D3]、[完整组合][D4]。

建议每个 task×arm 一个 Linux 容器：SDK 驱动、dsh、文件工具、Shell、子 Agent 全部在其中；容器可见本题公共请求、IFC 工作副本及固定依赖。G、冻结 D、答复卡、其他组、开发仓库及个人配置不挂载。独立 `HOME`、`DSH_HOME`、XDG 配置／缓存及临时目录，同题继续保留、换题全部换新。SDK `client.py` 会复制父进程环境，因此必须先清理容器启动环境，不能把 `env={...}` 当“不继承”。[client 源码][D5]

明确 `cwd=/workspace`、`runtime_cwd=/workspace`，只规定路径，不把 cwd 当沙箱。采用非特权用户、资源限制、无宿主 socket、白名单构建上下文；公共 task 文件只读、model 副本可写。挂载限制与实际 shell 越界结果要独立验证。上游也明确不能将自身权限提示当唯一隔离措施。依据：[官方安全说明][D6]、[Docker 挂载说明][D11]。

### 5.3 提问与继续：存在一个必须补的接缝

- `Session.run()` 从本次消息入队到整 agent idle 返回；`finish_reason` 来自最后的 root `turn/end`。同一个 harness／home／session_id 可继续原会话。`completed` 不代表 IFC 已明确提交。[SDK 接口][D1]
- 上游有原生 `ask_user_question` 和 `ctx.userQuestions.ask`。它等待 answerer，缺少 answerer 时返回错误；模型自己提出问题，转接器不生成问题。[问答服务][D7]、[工具说明][D15]
- **已读 SDK 协议只有 `initialize`、`session/prompt`、`shutdown` 三类请求，以及 session／subagent 通知，没有专用问答 request/answer 方法。** Python client 有通用 `next_request()/respond()`，不等于运行时已经把原生问题转成了这种请求。[SDK 协议][D8]、[client 源码][D5]

建议后续做一个仅呈现／转接的 user-questions answerer bridge，连接外部人工答复端；保留原生工具 schema、问题内容和 DSH loop。桥不接 G，不代选、不补意图、不提供修复建议。自然语言最终消息中的问题可先人工识别，按同 session 提交答复；这能验证文本继续，但不能冒充原生阻塞工具桥已通过。两条路径都进入同一个外部 run ledger。

标准 SDK 通知仅区分 `idle/running`，不能从它直接推导 `human_wait_s`。纯人工等待需证明全部活动已暂停；若子任务仍工作，继续计活动和用量。SDK 原生工具的挂起不等于子 Agent 全部暂停。

### 5.4 推理、用量和失败覆盖

| 来源 | 源码／文档支持 | 仍需离线核验 |
|---|---|---|
| `RunResult.events` | 根会话事件 | 不能单独统计整题 |
| `notifications`／`on_notification` | 根及已发现后代；保留原生会话关系 | 重启重订阅、在途事件、失败时的持久归集；远端子任务不是默认完整覆盖 |
| LLM 类型 | reasoning block／delta、usage、request attribution | request_id 与 stage/attempt 对齐，缺失／截断状态，协议原文与脱敏分析副本分离 |
| compaction | 原生压缩会额外调用模型，摘要有独立输出限制 | 源码只把返回文本写入摘要，不能凭摘要日志声称保存了该次完整推理；需传输层观察 |
| headless `--json` | 提供 text/thinking/tool/final 事件 | committed 投影省略被丢弃／重试内容；非 final 内容有截断，不能作为完整轨迹唯一来源 |

依据：[SDK 接口][D1]、[协议][D8]、[压缩][D9]、[LLM 类型][D13]、[headless 投影][D14]。建议在调用层只观察、不改模型输入输出，将所有原始返回推理、工具、usage 分开引用。先用固定协议 fixture 验证根、子 Agent、摘要、retry 和中断；不足就标 `partial/unavailable`，不能填零或以文本长度补算。

DSH `TokenUsage.inputTokens` 表示非缓存输入，cacheRead/cacheWrite 分列；`totalTokens` 可另返回。与 Chat Completions 的 prompt 总数不是可直接相加的同一口径。保留原始 usage，按协议规范化，事件重放去重；reasoning 若已包含于 output 不再加一次。依据：[DSH 类型][D13]、[Chat Completions 字段][D10]。

### 5.5 模型协议、网络与停止

原生 `deepseek-official` 使用 Messages：默认根 `https://api.deepseek.com/anthropic`，请求 `/v1/messages`，API key 使用 `x-api-key`；推理 effort 为 `output_config.effort`，工具／推理历史按块回传。它不是 B 的 Chat Completions。该版本 adapter 不接受一个 `protocol` 配置把它改成另一套协议。[Messages adapter][D12]

文本 IFC 实验不需要主动给模型图片或上传原文件；只让必要模型通道出站，普通网页、远程 MCP 和其他外联默认不开放。完整 profile 的组成和网络限制都应记录，不能悄悄删原生方法后仍称等同默认配置。请求中默认的 session-log／plugin inventory 扩展也要在隔离后核实其实际内容。[Messages adapter][D12]

**不建议现在搭完整网关。** 先做本地 fake Messages 服务验证真实 DSH 工具与记录。若原生观察接口不能涵盖摘要／重试，或需要在工具不可见处保管凭据和统一预留额度，再增加仅转发、记录和限额的薄服务。必须同时验证禁止直连，单设 HTTP_PROXY 不构成隔离；官方 adapter 使用 raw fetch，不能假定所有请求自动经过统一代理。[传输说明][D12]

SDK `max_tokens` 是请求输出上限，不是 task 总预算；摘要另有上限。源码 `close()` 先请求 shutdown，后 terminate／kill 直接子进程；SDK wire 没有 per-session cancel。后续应一任务一运行时，超限先停止新调用，再有界 shutdown，必要时终止整个容器并验证孙进程已退出；冻结文件前保证无写入者。仅 SDK 退出或设置 `request_timeout_seconds` 不足以证明任务总时限已实现。依据：[SDK 参数][D1]、[close 实现][D5]、[协议][D8]。

### 5.6 本轮证据等级

已取得：官方固定源码／文档、公开发行元数据、本地版本与服务状态。**未取得：DSH 安装、运行时离线启动、问答桥、隔离逃逸 canary、usage 全覆盖、进程树回收或真实联调结果。** 本文所有 D 接入流程均为拟实施建议。

## 6. 阶段 1 实际交付：两道开发题与最小工具

### 6.1 两套可审阅材料

[本地题包入口](../../../dataset/processed/ifc-repair/repair-comparison/development/README.md)。固定使用 `development/`，在原位置修订；当前输入、配方、审阅条件和工具纳入 Git。大型 `VIEW.html` 是可重建的本地输出。题包未安装到 accepted Proof，原始来源及采用的历史修复副本均保持不变。

| 题目 | 来源与损坏 | 公开要求与待审语义 | 检查结果 |
|---|---|---|---|
| [case-001](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/REVIEW.md) | LargeBuilding，MIT；使用事前选定的已登记历史修复副本作为 G，删除中间窗及洞口 | 两个参照窗中心连线的中点补窗；明确915×1830 mm、窗台305 mm，框和玻璃等指定以自北向南第二扇现存窗为准；1个主目标、3条应修关系 | G/D原生schema＋EXPRESS各0诊断；只删除指定窗和洞口；两扇参照的放置及世界网格完全一致 |
| [case-002](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/REVIEW.md) | Duplex Apartment，CC BY 4.0；删除Tag 150378的门，保留洞口及其void | 门为864×2032 mm；公开给出空洞和唯一样式参照门的全局平面坐标，左右开启均允许；1个主目标、2条应修关系 | G/D原生schema＋EXPRESS各0诊断；保留洞口及Tag 150478、159734门的放置、世界顶点和面索引完全一致；150478没有移动 |

每题含公开 `model.ifc`＋`request.txt`，私有 `reference.ifc`、`mutation/damaged.ifc`、损坏记录、任务条件、答复卡、来源许可、检查 JSON、定位 SVG 与可读 `REVIEW.md`。新增[窗题查看器](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/VIEW.html)／[门题查看器](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/VIEW.html)：用现有IfcOpenShell将真实几何编译成自包含HTML，G/D使用同一世界坐标和同步视角，支持俯视、斜视、定位参照、缩放和目标层剖切；不渲染原材质。SVG仍只是包围盒定位图。查看器和所有参考材料仅供人工审阅，不能送入被测系统。许可与修改说明见[来源说明](../../../scripts/ifc_repair/repair_comparison/source-notices.md)。

按用户意见，撤销门题此前“必须答复某一开向”的草案，答复卡的必要事实列表为空；不因未询问开向扣分，也不要求猜中G。后续澄清案例应确实缺位置、楼层或必需尺寸，不能把普通选项强行变成缺失事实。两题的1mm／0.1度仍为待审容差；旧门损坏快照的 `dimensions_mm` 标签仍以此处独立单位换算为准，未改生产代码。

两个请求全文见各题 `public/request.txt`。窗题方位已用D的TrueNorth≈(0,1)及同墙现存窗的南北顺序核对；Duplex没有TrueNorth，门题使用楼层和全局几何坐标，不编造方位。两题不再泛称“跟旁边一样”，而是指定唯一参照及需相同的部件。私有 `task.json` 记录定位依据和 `damage_profile`；两题均S1。S2两窗／一窗一门、S3多目标的分级规则已就位，当前生成器仍仅支持单目标，不把分级功能冒充多目标损坏生成已完成。

公开请求不提供IFC关系名称或修复方法，只表达在指定楼层开洞、安装门窗。评分侧保留任务必需的void/fill/containment语义检查；`IfcRelDefinesByType`不再作为必修边，允许实例表达等价语义。格式校验通过不代表这些任务关系齐全；模型能否自然补全是后续实验的问题，本轮没有调用模型验证。

### 6.2 实现与边界

| 已创建文件 | 实际职责 |
|---|---|
| [contracts.py](../../../scripts/ifc_repair/repair_comparison/contracts.py) | 开发定义、损伤规模标签、许可与源哈希引用、澄清事实约束；拒绝请求中的GUID及明确方法词，仍需人审自然性；拒绝越界、链接／junction／共享硬链接 |
| [prepare.py](../../../scripts/ifc_repair/repair_comparison/prepare.py) | 调用现有单门／单窗损坏器；同一待审开发题可原位刷新，已接受或不明目录拒绝覆盖；只保留关键IFC绑定，审阅文本不逐文件锁哈希；仅两份公共文件导出 |
| [inspection.py](../../../scripts/ifc_repair/repair_comparison/inspection.py) | 独立重开G/D、根差分、损坏数量、真实应修成员边及相关几何；G/D均须原生schema＋EXPRESS通过，不能只凭无新增错误；宿主无整体豁免 |
| [review_materials.py](../../../scripts/ifc_repair/repair_comparison/review_materials.py) | 可读审阅卡、私有定位图、答复和验收草案，不自动接受 |
| [viewer.py](../../../scripts/ifc_repair/repair_comparison/viewer.py)／[viewer.html](../../../scripts/ifc_repair/repair_comparison/viewer.html) | 真实世界坐标三角网格、同步视角本地查看器，以及保留参照的放置／顶点／面索引比较 |
| [development_cases.private.json](../../../scripts/ifc_repair/repair_comparison/development_cases.private.json) | 两道明确标注为私有的开发配方、公共请求、待审语义和来源；绝不能挂载到被测环境 |
| [test_preparation.py](../../../tests/ifc_repair/repair_comparison/test_preparation.py) | 37项聚焦测试；格式门禁、关键IFC绑定、原位刷新、可编辑审阅文字、权限继承、实际网格和移动检测、公共投影及CLI |

上述是原 M1.1–M1.3 的开发样例子集。用户随后认可材料风格并要求继续计划，已推进下方§6.5的离线基础；正式TaskSpec与20题人审仍未完成。目录分层和白名单导出不能证明运行时沙箱隔离。工具不会导入 `.env` 或调用模型。

### 6.3 已执行检查与复现

当前聚焦测试 **37 passed**。先保留原位刷新、审阅文本不锁哈希、权限继承及查看器的失败用例，再修正准备工具。已有格式门禁继续覆盖G/D同样有原生错误但无新增错误的负例。两题真实IFC另行校验，不用简化夹具代表建筑结果。HTML脚本通过 `node --check`；浏览器连接不可用，备用入口又因安全策略拒绝 `file:` URL，因此未完成浏览器交互及视觉验收，不将离线网格测试当作浏览器验收。

实际执行：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/ifc_repair/repair_comparison/test_preparation.py -q --basetemp .tmp/repair-final
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/prepare.py prepare --output dataset/processed/ifc-repair/repair-comparison/development
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/prepare.py check dataset/processed/ifc-repair/repair-comparison/development/case-001
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/prepare.py check dataset/processed/ifc-repair/repair-comparison/development/case-002
```

准备命令允许刷新同编号、待审的开发题。按用户授权，已删除 `development-20260929`、`development-review-20260929`、`development-natural-20260929` 三个旧副本，只维护 `development/`。不再生成全文件 `integrity.json`；保留源G、损坏D、公开副本及格式报告的必要绑定。检查返回 `valid: true, human_accepted: false`；格式结果见每题 `IFC-VALIDATION.md`。

旧 `mutation/` 的受保护ACL来自生产损坏器用临时目录原子重命名，未发现显式设置权限的制题逻辑。准备工具现在将临时结果的文件字节复制到普通新建目录，不继承临时目录ACL，也未改生产损坏器。实际两题 `mutation/` 的 `AreAccessRulesProtected=false`，继承父目录权限。

另独立执行本地validator命令行，两题都返回 `No validation issues found.`，退出码0：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m ifcopenshell.validate --rules dataset/processed/ifc-repair/repair-comparison/development/case-001/private/mutation/damaged.ifc
.\.venv\Scripts\python.exe -X utf8 -m ifcopenshell.validate --rules dataset/processed/ifc-repair/repair-comparison/development/case-002/private/mutation/damaged.ifc
```

这是IfcOpenShell 0.8.5的schema＋EXPRESS结果，不声称已向buildingSMART在线服务上传验证。输入格式正确仍然可以缺少任务要求的门窗，修复是否完成由后续独立评分判定。

直接复用的旧损坏器另做最窄回归：`test_mutation.py` 和 `test_door_mutation.py::test_door_mutation_records_identity_type_and_exact_scope` 合计 **5 passed**，覆盖单窗链和保留／删除洞口的单门路径；未运行批量制题或全仓 Preflight。

公开导出用法（尚未启动四组运行）：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/prepare.py export dataset/processed/ifc-repair/repair-comparison/development/case-001 .tmp/repair-comparison-public-example
```

导出仅含 `model.ifc` 和 `request.txt`，目标需位于私有题包外且尚不存在；新副本可写。正式部署仍需阶段 3/5 的真实隔离检查，不能把整个题包或仓库挂进去。

### 6.4 题包确认时的最小开发建议（实施见§6.5）

先补 M1.4 的 `ledger.py`、`budget.py` 与对应聚焦测试，再衔接 §7 的执行器与评分。保存原样问答、人工事实标注、追加事件、恢复状态、请求预留／结算、时间区间、实际推理引用及唯一终态。澄清和重启不清零；重复通知去重，缺失 usage 保留未知及未结清预留，仍有后台活动不暂停计时；并发不能重复花余额。

真实额度在开发联调和费用批准后填写，未赋合法额度不得发请求。fake用量与轨迹明确标记，不记模型成绩。fact ID由答复／评估端依据已认可题卡标注，适配器不猜意图或代提问；被测侧只取得实际回答，不取得整卡。该建议已实施为下节的“准备→问答→继续→累计→唯一提交”离线入口；尚不构成真实四组准入。

### 6.5 按确认的形式继续：离线实验基础（2026-09-29）

用户确认题包风格并要求按计划继续后，阶段2已实施下列开发模块。实验代码位于`scripts/ifc_repair/repair_comparison/`；随后另经用户明确授权修复一个生产尺寸写回点，见§6.6。不是正式四组准入。现有两题信息充分，测试里的提问用于验证暂停／恢复，不计为必要澄清题。

| 模块 | 已实施行为与实际边界 |
|---|---|
| `budget.py`、`ledger.py` | SQLite事务记录请求预留、原样响应、已知／未知用量、原样问答、人工事实标签、活动及等待时间、原生结果引用与唯一终态；重启不清零，未知用量不按0计算；只允许一个活动任务，同题各组预算一致 |
| `neutral_tools.py`、`direct_runner.py` | A/C同一工具协议：分页读文件、写文件、精确替换、命令执行、提问、显式提交；不附IFC方法指导。原子认领工具，疑似中断操作不自动重做；无提交不会挑工作区文件冒充结果 |
| `process_control.py`、`_command_worker.py` | 当前Windows用Job约束可信离线脚本的进程生命周期；超时及正常结束都确认子进程停止。这不是文件系统／网络沙箱，不能据此声称私有资料不可达 |
| `provider_observer.py`、`ours_adapter.py` | B调用现有`RepairAPI`，使用默认Intent 0.10及真实索引、解析、应用、校验、发布；只接受固定假响应。保留原生候选token、state_version和原样回答，恢复同一任务；只从原生正式发布路径收集IFC，不扫描staging |
| `scoring.py` | 当前两道单目标开发题的独立评分入口，仅读D、显式R／终态、事前题卡和问答证据，评估侧可读G；不要求ChangeSet或B评价。检查原生schema＋EXPRESS、数量、粗位置匹配后独立检查尺寸／几何／关系、原对象保全及澄清 |
| `experiment.py` | 离线CLI：`create`、`run`、`status`、`answer`、`score`；预算必须显式给定。无真实Provider入口，无D模拟器，无自动题卡代答 |

评分规则仍是开发实现，不能直接冻结为正式20题通用评价：支持新GUID和STEP重排；门允许左右替代；相同世界表面三角网格及样式可作为外观相符证据。不同剖分或尚不能证明的等价表示标为`needs_review`，不直接判错或放行。保全比较先在评估内存副本扣除新增对象，再比较原根对象；不整体豁免宿主，忽略编辑者／编辑时间元数据。原对象的等价重建、复杂外观、多目标匹配仍需后续扩展和人审。异常返回`not_evaluable`；待答返回`pending`，失败和无输出保留分母。

已经以真实公开D跑通两题×A/C的四次脚本工具、提交和评分闭环。脚本是**手写测试夹具**，仅在测试中作为假模型输出，不向实际A/C默认注入，也不读G。G派生的正确／错误产物仅作为独立评分器的评估侧对照。B的米制失败证据单独保留，获准修复后在原D上重验；另有公开D的毫米制转换对照，不计为新IFC样本。B的固定Intent旨在验证索引、确定性执行和正式发布，不证明模型能从自然语言生成同一Intent，也不表示其默认几何已满足请求中的全部参照样式条件。

聚焦验证使用本专题全部测试，及直接相关的既有`test_run_state.py`、`test_provider_stage.py`。不调用付费模型，不运行全仓Preflight。命令与结果见§6.8；D、真实隔离、B原生强制超时及HTTP内部重试用量覆盖尚未验收。

### 6.6 B自然语言定位核对与单位修复

**B支持自然语言定位。** `request_stage.py:149`将自然语言转为查询，`target_query.py:120/218`按类别、楼层、名称、宿主、空间、方向和几何条件解析真实IFC，`resolution_flow.py:170`及`api.py:934`提供候选澄清；保留洞口选定后，`door_resolution.py:552`可读取其尺寸及位置。不应因缺少某个查询字段就否定整个Harness。

针对当前两题的只读核对：西侧墙被索引为轴线朝north，所以“建筑西侧”不能直接翻译成墙朝west。门题按公开楼层高3100、宽864、高2032筛选有6个候选，5已填、1空；此人工查询默认5时目标排第6，`max_candidates=10`可包含它，当前候选不会自动扩大。这证明已有检索／澄清路径及具体边界，尚不是模型对自然语言请求的成功或失败证据。“最西侧＋自北向南窗排序＋中点”能否由现有模型／流程完整处理仍待获准实测；不为离线接线偷偷修改定位逻辑。

**另发现一个与自然语言无关的米／毫米写回缺陷。** 真实case-002的固定假Intent已定位正确门洞并进入Stage2；原生链路随后返回`UNIFIED_TRANSACTION_FAILED`、回滚且无正式IFC。证据链：

1. `operations/door.py:539–540`创建门时正确把864/2032 mm换为0.864/2.032 m。
2. `operations/door.py:811–826`产生规范化尺寸语义事实；`semantic_facts.py:674–684`的读取约定也使用毫米。
3. `apply.py:144`调用语义赋值；`semantic_authoring.py:533`直接把规范化864/2032写入IFC米制属性，覆盖了正确值。
4. 实际回读被解释为864000/2032000 mm，`DOOR_DIMENSIONS_MATCH`、`DOOR_GEOMETRY_ALIGNED_WITH_OPENING`失败。源D不变，失败没有被替换成毫米制对照的成功。

原始失败保存在`tests/ifc_repair/repair_comparison/fixtures/door-metre-before-fix.json`，来源及边界见同目录README；当前回归为`test_ours_adapter.py::test_native_real_metre_door_repair_and_preserved_before_fix_evidence`。`test_b_publication_control.py`单独验证毫米制对照。

用户已明确答复“同意修复该单位错误”。生产修改仅在`semantic_authoring.py`：对`attribute:OverallWidth/OverallHeight`将规范化毫米值换回IFC项目单位；显式长度单位复用既有转换函数，其他属性照常写入。题目、schema、语义事实、门创建器与定位策略不变。新回归族包含**门／窗×米／毫米×规范化None／显式mm**、显式m/cm、未知／非长度单位拒绝和普通文本属性不变；修复前9失败／5通过。旧窗语义测试原本未声明单位却断言毫米值，现明确补上毫米制项目单位，并验证语义回读仍为915mm。该修复是确定性执行bug修复，不是自然语言定位能力提升。

原米制case-002修复后已由真实RepairAPI发布IFC并回读0.864m×2.032m，源D不变；补充说明后重启也能继续同一任务、累计预算并发布。具体测试结果见下节。真实隔离、DSH及模型接入仍未放行。

另把该B固定响应生成的默认门交给独立评分：原生schema＋EXPRESS、数量、名义尺寸、关系和保全通过；与请求参照的几何范围／外观未全部符合，统一`repair_success=false`。固定Intent没有完整表达外观要求，因此这是评分分离对照，不是模型理解能力失败率。不能拿原生`successful_artifact_publishable`代替正式实验的任务分数。

### 6.7 离线CLI用法

用`.venv`运行，`--root`放在命令前。所有命令仅供离线开发；下面的预算文件和replay文件必须由开发者显式准备，不读取`.env`。

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/experiment.py --root .tmp/repair-offline create --public dataset/processed/ifc-repair/repair-comparison/development/case-001/public --case-id case-001 --arm A --budget <offline-budget.json>
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/experiment.py --root .tmp/repair-offline run case-001-A --replay <replay.json> --reservation 100
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/experiment.py --root .tmp/repair-offline status case-001-A
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/experiment.py --root .tmp/repair-offline answer case-001-A --question-id <当前问题ID> --text <用户原样答复> --event-id <唯一答复ID>
.\.venv\Scripts\python.exe -X utf8 scripts/ifc_repair/repair_comparison/experiment.py --root .tmp/repair-offline score case-001-A --case dataset/processed/ifc-repair/repair-comparison/development/case-001
```

预算JSON字段：`tokens`、`calls`、`active_seconds`、`tool_seconds`均为正值，`extensions`为预先定义的扩额规则数组（可空）。示例测试额度仅用于假响应，不是正式额度建议。A/C的replay是响应数组，各项含`tool_calls: [{name, arguments}]`及可选`usage`／接口实际返回的推理字段；B的replay是按全任务顺序排列的Intent响应，Stage2由固定的公开投影回放产生。B回答另通过`--native-answer <json>`传原生回答结构，并核对当前候选token；人工事实标签可用`--requested-fact`／`--answered-fact`记录，只作为评估元数据。

### 6.8 聚焦验证记录与下一步

以下数量对应各自命令，有重叠，不相加成一个总测试数：

| 验证范围 | 结果与解释 |
|---|---|
| 本专题全部测试＋既有`test_run_state.py`、`test_provider_stage.py` | **124 passed**；在生产单位修复前完成，米制B案例当时明确检查失败保留，没有把失败改称成功 |
| 单位修复及直接相关门窗应用／语义回归＋B两开发题／问答恢复／毫米对照 | **54 passed**；修复后的原米制D和窗题均通过真实RepairAPI发布；回读尺寸及源D不变。旧窗测试补明确单位声明，未削弱期望 |
| A/C两题公共D脚本闭环 | **4 passed**；真实命令工具→唯一IFC→独立评分，手写离线夹具，不是模型成绩 |
| 最终评分器与离线CLI回归 | **17 passed**；覆盖正确／错误产物、无输出、待答、答复卡`fact_id`接线及评估异常；内部评估错误不算模型修复失败 |

实际命令：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/ifc_repair/repair_comparison tests/ifc_repair/test_run_state.py tests/ifc_repair/test_provider_stage.py -q --basetemp .tmp/repair-offline-validation --tb=short
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/ifc_repair/test_semantic_attribute_units.py tests/ifc_repair/test_semantic_authoring.py tests/ifc_repair/test_door_application.py tests/ifc_repair/test_window_application.py tests/ifc_repair/test_window_semantic_authoring.py tests/ifc_repair/repair_comparison/test_ours_adapter.py tests/ifc_repair/repair_comparison/test_b_publication_control.py -q --basetemp .tmp/repair-units-verified --tb=short
```

最终自检另补了答复卡`fact_id`接线及评分器异常的测试，保证“问对但无产物”只算澄清成功，内部评估错误不算模型修复失败。评分／CLI命令为：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/ifc_repair/repair_comparison/test_scoring.py tests/ifc_repair/repair_comparison/test_experiment_cli.py -q --basetemp .tmp/repair-score-final --tb=short
```

后续仍按原阶段顺序推进。DSH安装现已获准并完成首批原生离线验证，正式首批5个源IFC已筛选，见§6.9–6.10。正式20题按每批5题人审；多目标与外观等价评价需随题卡补齐再冻结。

### 6.9 阶段3：DSH安装与首批原生离线验收

用户明确批准[DSH方案§13](deepseek-harness-integration.md#13-阶段3安装与隔离方案已批准的具体范围)：启动已有Docker，在独立Linux容器内构建固定版DSH和实验依赖并做假模型验收；4 CPU／8 GiB、首次构建60分钟、新增数据20 GiB停止阈值。不读取模型密钥，不调用真实模型。该安装授权与后续付费授权分开。

Docker引擎现已可用：Desktop 4.83.0、Engine 29.6.2、Linux amd64；启动核对时没有活动容器。实际数据VHD位于`G:\dockerdata\DockerDesktopWSL\disk\docker_data.vhdx`，与设置相符。已下载官方Node 24 bookworm基础镜像，digest为`sha256:64af3819f9275802414d7cdc38c27e9d82bd564dec4d4da87d008255d36c63b4`；官方源码HEAD核对为`4878cdabd87d4041bdaff61d04c966883b9fd07a`。

构建入口为[`dsh/build-runtime.sh`](../../../scripts/ifc_repair/repair_comparison/dsh/build-runtime.sh)，仅在容器执行。专用Linux构建卷为`text2ifc-repair-dsh-build`，宿主源码只读，导出至`.cache/repair-comparison/dsh/artifacts`。从首次启动到构建完成为UTC 11:26:43–11:46:22，**19分39秒**，所有修正共用原截止时间。SDK与完整runtime均为`0.2.0rc1`，未降级PyPI旧版、裁剪工具或替换原生loop。官方构建中的Office运行时／文档往返检查通过；这里只验证bookworm本机容器，不据wheel名称宣称跨发行版manylinux兼容。

安装入口为[`install-runtime.sh`](../../../scripts/ifc_repair/repair_comparison/dsh/install-runtime.sh)。实际Python **3.12.14**、IfcOpenShell **0.8.5**、Pydantic **2.13.5**，依赖检查通过；仓库`.venv`和系统Python不变。公共工具镜像供后续A/C容器后端共用，D另加同版wheel。固定制品如下，哈希只用于安装重现，不增加题包逐字节约束：

| 制品 | 固定值 |
|---|---|
| Python基础镜像digest | `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` |
| `text2ifc/repair-tools:py312-ifc085`镜像ID | `sha256:8488143fe4cf4031b66fc0a41fbbfd0ca10dce0b1f248e942bd5056ab7d47905` |
| `text2ifc/repair-dsh:0.2.0rc1`镜像ID | `sha256:754a47a1ff5113193fc85498a3b44321363bbfb86980c193c948bc5011184931` |
| SDK wheel SHA-256 | `26896976e1536c87266c34ef192c836fe251c0df2f202f31a5add19bcd04e4e5` |
| runtime wheel SHA-256 | `9f0b02797b48c21314725649de7feb73936a4df7ad20c770fcb4dbf9002864e1` |

原始构建／安装日志和wheel留在上述活动缓存；实际会话、SDK通知和假服务SSE留在`.tmp/repair-comparison-isolation/`。以下全部是**真实DSH运行时＋手写假模型**证据，token是夹具值，不是模型成绩或费用；未读取`.env`或真实密钥。

资源各次采样均未触发20 GiB新增数据停止阈值；收尾C盘约21.78 GiB、G盘约88.73 GiB可用。原始记录导出后已移除本实验18个容器、7个用例状态卷和内部网络，未遗留活动测试；保留两个实验镜像、wheel及唯一构建缓存，不清理其他项目的镜像或Build Cache。

| 实测项目 | 结果与边界 |
|---|---|
| 官方默认SDK | 原版`smoke-python-runtime.py --scenario sdk-default --installed-wheel`通过；完整`sdk`，非root、只读安装区、禁网 |
| 文件／Shell | 原生`read → edit → bash`通过；核对实际文件修改及Shell导入IfcOpenShell 0.8.5 |
| 问答及继续 | 挂载官方`dsh-tool-ask-user`与仅转发的[`question-bridge.mjs`](../../../scripts/ifc_repair/repair_comparison/dsh/question-bridge.mjs)；问题原样到独立控制容器，模拟人等待2秒期间无新增模型请求；答复后原session完成，再次继续仍保留问答 |
| 子Agent | 原生`subagent`通过；根2次＋子1次请求、子session通知与持久日志均保存，根收到子结果 |
| 503重试 | 首次503失败保留；原生重试后完成，共2次请求；失败请求无用量字段不能记零成本 |
| 推理／缺用量 | 返回内容中保留独立`reasoning`块；缺token字段时原生usage确实变成0，评估须依据wire字段存在性记`unavailable` |
| 截断响应 | 以`STREAM_CLOSED`终止，保留`assistant/attempt.stream`，没有自动续调。首版探针错误期待重试，其断言失败保留；只对原始结果核实正确终止并修正探针期望，未重跑挑成功结果 |
| 摘要组件 | 仅此用例降低原生压缩阈值、使用较长合成上下文，完整工具仍开启。实际2次摘要请求，1次写入`compaction/summary`，1次因摘要未缩短而不提交；两次wire响应均保存。不能只统计已提交摘要，也不由该用例确定正式阈值 |
| 进程停止 | 原生bash超时转后台；停止前可见Python子进程持续心跳。外部停止整个容器后`Running=false`、PID=0、退出143，2秒观察心跳不再变化 |
| 隔离 | D仅挂探针、桥、当前工作副本和Linux状态卷；假答复／wire日志在另一容器，不挂仓库、Gold、个人配置或Docker socket；内部网络无宿主端口，外网TCP探测返回`ENETUNREACH`。这不是四组隔离已完成 |

问答桥另有**7项Node聚焦测试通过**：等待、取消、错request／错问题／缺失／重复／未提供选项的答复拒绝。重复探针入口为[`run-offline-probe.ps1`](../../../scripts/ifc_repair/repair_comparison/dsh/run-offline-probe.ps1)，假服务／驱动为`tests/ifc_repair/repair_comparison/dsh_{fake_gateway,runtime_probe}.py`。这些入口没有真实模型选项，非空状态不能被当作新会话。

准备中保留了两类失败：tmpfs默认禁止执行，阻止解包的原生扩展及DSH自身缓存资源；在临时区允许执行后官方默认smoke通过，安装区仍只读。Windows绑定状态目录下首个turn停滞，150秒外部截止后退出；相同用例改用Linux卷后通过，未进一步断言具体文件锁根因，也未修改上游代码。

**阶段3整体仍未完成。** 下一步把D的wire／原生通知、人工答复与阶段2账本接起来，完成A/C容器工具后端和B白名单镜像／外部停止看护。当前只证明同进程问答继续；官方SDK没有冷恢复pending question的RPC，进程丢失不能声称恢复同一Promise或自动重开。需补冷中断终态、等待前无后台活动、未知用量及在途预算控制。阶段5四组完整准入和费用批准仍是进入真实调用的前提。

### 6.10 首批5个正式源IFC候选

当前只完成源模型筛选及只读几何检查，**尚不是5套待人审完整题包**。唯一候选清单为[`formal_candidates.private.json`](../../../scripts/ifc_repair/repair_comparison/formal_candidates.private.json)，含来源、既有许可证据、预选目标／保留参照、几何及后续事项；它是制题侧私有材料，不进入任何被测环境。没有复制或修改源IFC，也未改全局数据登记、训练划分或开发题。

| 暂定题号 | 源模型／许可 | 大小 | 门／窗数 | 拟制题内容 |
|---|---|---:|---:|---|
| formal-001 | Tafraout model2／CC BY4 | 0.89 MiB | 28／10 | S1：保留洞口，补一扇门 |
| formal-002 | European LCA Type4／CC BY4 | 9.85 MiB | 6／8 | S2同类：补两扇窗，保留另一扇同尺寸参照 |
| formal-003 | GNI model_18／CC BY4 | 1.69 MiB | 17／63 | S2混合：补一扇窗和一扇门，各留明确参照 |
| formal-004 | Jasmin-Sun-105／GPL3+ | 3.07 MiB | 8／12 | S1：补一扇地下层窗 |
| formal-005 | niedriha-V2／GPL3+ | 2.33 MiB | 16／16 | S1：保留洞口，补一扇门 |

五份均实际重开为IFC2X3，字节与已有schema＋EXPRESS零错误报告绑定一致；本轮复用了这些原生报告，没有把旧报告写成新跑的validator结果。当前重新核对所有门／窗的fill→opening→void→wall链，表中门窗均具有唯一有效墙链；13个预选目标／保留参照实际生成世界坐标几何。坐标尚只作私有选题检查，不把删除记录直接翻译成公开答案。制题时G和最终D仍须按既定规则独立校验。

场景去重采用现有保守分组：Tafraout三份模型整族只取一份，欧洲LCA原型族只取一份，GNI 2025课程模型整族只取一份；Jasmin与niedriha分别属于已有不同住宅模型族。五份之间以及与LargeBuilding／Duplex两开发题之间没有共享IfcElement GUID，但这只是辅助核对，不以GUID不相交证明设计独立。限定搜索既有Repair脚本、测试、私有案例登记和专题文档，没有命中这五个源名称；不宣称模型训练未见或全仓历史从未使用。

许可按逐模型记录使用：[Tafraout来源](https://zenodo.org/records/6397164)、[European LCA来源](https://data.mendeley.com/datasets/yv723tdtv9/1)、[GNI来源](https://zenodo.org/records/19722012)。GPL两题依据[TestData专项许可](https://github.com/opensourceBIM/TestFiles/blob/master/TestData/license.txt)，后续材料保留该许可及修改说明，不统一改贴MIT／CC BY。具体字节、版权声明和修改发布条件仍链接现有rights记录，不从整个仓库的软件许可推导陌生模型授权。GNI采用已登记的格式修复副本作为事前参考，原始下载文件与修复谱系继续保留。

下步制作这五套可逐项审阅的完整材料。S2双目标／混合制题与统一评分尚需实现和离线回归；不为赶批次默默退回五道单目标，也不按B的修复成绩筛选。真实澄清题另外从必要位置／楼层缺项选取，必须验证至少两个与D及初始请求相容的有效解释，不能把这批尚未完成的提案计作3道已成立澄清题。

### 6.11 Goal 本轮：首批五题与两个 demo 的四组接线（2026-10-04）

用户授权完成这两项交付，并批准真实开发联调约 20M token 的目标，超出无需重复审批。用户随后明确：**首批五题只审题和离线检查，保留作正式测试**。本轮未修改生产代码、注册 Prompt 或 Schema；此前另行批准的单位修复保持原版本。

[五题材料入口](../../../dataset/processed/ifc-repair/repair-comparison/formal/README.md)在固定 `formal/formal-001` 至 `formal-005` 维护。五个不同 IFC，三份 CC BY 4.0、两份 GPL；一门、两窗、窗门混合、一窗、两门，含 S1/S2。各题有公开请求和 D、私有 G／损伤／许可材料、`REVIEW.md`、格式报告及本地生成的 G/D 查看器。五题全部 schema＋EXPRESS 零诊断，删除范围、预定洞口保留／闭合及参照网格不变已检查。程序没有代写人审 accepted，也未向模型发送这五题。查看器已支持同时聚焦多个目标；本机浏览器插件连接不被信任，尚无浏览器视觉通过声明。

两个 demo 使用唯一公共输入副本，A/C 共用 `isolated_direct.py` 和 `container_tools.py`，可普通脚本、Shell 和直接文本操作，无 IFC 方法提示。B 的 `isolated_b.py` 白名单打包原生产 API/SDK 与注册资源，只挂载本题 D／请求／输出和 Linux 状态。D 的 `isolated_dsh.py`、`dsh/native_worker.py`运行官方完整 0.2.0rc1，保留原工具、子 Agent、压缩与原生问答。模型运行区不可读取 G、损伤配方、其他题／组工作区、宿主仓库或真实凭据。

`wire_gateway.py`逐个观测 HTTP attempt，包括 B 重试和 D 子会话／摘要；透传原协议，不用 Chat/Messages 转换替换 DSH。用量仅记实际返回，缺失保留未知及预算预留；推理仅保留实际返回字段。A/C 命令在无网络的单次容器内执行；B/D 仅接内部网络，转发器只提供固定模型端点和原生问题端点。真实密钥只在主机网关内存中读取。

本轮首次阶段准入只覆盖两道开发题的八条真实联调路径。真实容器＋假 HTTP 的八任务全部显式提交并独立通过回读、原生格式、名义尺寸、关系和保全检查；A/C/D 公共脚本夹具通过当前完整开发评分，B 夹具没有证明外观等价，不能称八题全修好。四组的额外澄清夹具恢复后保留同题预算；D 的原生问题在同一进程／会话继续。普通命令错误、后台进程超时停止、源输入不变、未知用量／截断／失败保留和唯一提交均有对应验证。

独立复核发现并在真实调用前修正了：A/C 不确定请求恢复重复发起、同工具重复认领、停止未确认却释放活动、批量工具澄清的消息顺序，以及非对象 JSON 响应不能结算。对应红例／回归保留，进程停止未确认仍阻断下一任务；DSH 冷中断不冒充暖会话恢复。

实际验证记录：账本／A/C／HTTP聚焦回归49通过；HTTP与原生产SDK／Provider seam43通过；B原生边界及D收取19通过、2个预期跳过（Windows无符号链接权限及另行选入的B容器组件，实际B容器已由完整CLI覆盖）；评分／公共CLI／公共D闭环／制题26通过；A/C新增批量工具与执行权8通过；执行权路径复核2通过；真实八任务及四组澄清的测试通过，停止夹具的转义错误另修后单测1通过。原UTF-8 CLI读取失败和停止夹具失败记录均未删除。编译及 scoped `git diff --check` 通过，没有 Full Preflight。

机器准入：[stage-admission.json](../../../.tmp/repair-comparison-runtime/stage-admission.json)，绑定实际代码／注册资源、两题公共输入、固定镜像、请求模型与开发保护预算；人审注释未纳入绑定。主机工具镜像补齐获准实验依赖为 `text2ifc/repair-tools:py312-ifc085-v2`，固定 DSH 镜像不变。开发保护预算暂为每任务 2.5M token／100次请求／5400秒活动时间／120秒单工具，同题四组相同，总目标20M；这不是正式实验预算或指标冻结。

真实工作区：[`.tmp/repair-comparison-demo-live`](../../../.tmp/repair-comparison-demo-live)。初次按窗题 A→B→C→D、门题 B→C→D→A 顺序；等待用户时先确认无后台活动再进行独立任务。实时任务状态、提交和独立检查统一见[联调结果页](demo-results.md)。窗题 A 因模型工具参数含非法 JSON 控制字符终止；C 已提交但新增 24 条 EXPRESS 唯一性错误；D 遇上游流截断，以 `STREAM_CLOSED` 终止，没有正式提交。两项 B 澄清均等待用户确认，没有从 G 找答复或自动代答。原失败不补跑，不凭开发联调推断能力差异。

DSH 截断暴露了实验侧的协议计账错误，已通过红测定位后修正：Messages 的未缓存输入、缓存读取和缓存写入相加，Chat 不重复加缓存；流初始输出零值不能当作最终用量。计账／HTTP／恢复的 42 项聚焦回归通过后刷新阶段准入。窗题 D 的旧推导 75857 token 由[追加更正](../../../.tmp/repair-comparison-demo-live/accounting-correction.json)取代，22 个完整响应合计 1093264 token，最后一个响应的最终用量未知并保留预留。原始 wire、原结算事件、原失败与最初准入保留，未重调该任务或修改原生 DSH。

门题 A 在 49 次调用、2185669 个返回 token 后因下一次预留超上限而停止，原终态误记为一般 403／runtime_error。原轨迹离线重建确认下一次预留 320467，合计超过 2500000；未为它补跑或冻结中间文件。实验端预算拒绝现在单独记录并正确标为 budget_exhausted，token／次数／活动时间及上游 403 对照的 47 项聚焦回归通过，再作 scoped 准入刷新。原失败状态保持，报告明确实际原因。当前六个任务已终止，两个 B 任务等待人答；尚无格式合格的正式开发提交，不把 HTTP 接通称为修复成功。

入口：`python -m scripts.ifc_repair.repair_comparison.demo_workflow status --root .tmp/repair-comparison-demo-live`；人工确认答复写入 UTF-8 JSON 后用 `answer --run-id <任务> --answer-file <文件>`，再恢复 A/C/B；DSH 原生提问由原进程接收答复继续。`check`只用冻结提交做开发检查，不重调模型。

### 6.12 五题修订、澄清对照与重启恢复（2026-10-07）

用户澄清了第二种门损伤的含义：制题时同时删除门和洞口，D 恢复连续墙面，修复任务是重新开洞并装门。001 保留空洞补门；003 的门和 005 的两扇门采用闭墙损伤。005 保留第三扇同层门作外观参照，两处门洞的中心与尺寸写入自然语言请求；不加入 GUID 或执行方法提示。004 的小窗在整体视图中不显眼，增加了真实网格的 Y/Z 立面放大，宿主墙闭合增加 0.135 立方米；输入没有为视觉效果夸大损伤。五题再次离线检查均 valid，人审仍待接受，未进行模型实验。

两 demo 的请求属于信息充分题。公开文本应把修复意图、唯一定位、尺寸和参照说清楚；不要求额外告知墙局部偏移、GUID 或关系操作。必要澄清针对 D 与请求无法确定的目标事实。B 提问局部参数或没有提供候选，是该次原生链路的实际表现，不据此把正式请求改写成 Harness 参数表。

用户重新批准 20M 开发预算，并确认两种窗题答复都尝试：只重申公开要求，以及追加仅由公共 D 算得的 12227.5 毫米局部偏移。对照从同一个原生待答状态分支，原问题、原生 ID、初始调用和已用预算保留；共用请求 ID 在总账只计一次。门题两种方案包含相同公开事实，只继续原任务一次。结果和每次追加调用统一记在 [联调结果页](demo-results.md)，不选较好分支替换原实验分母。

2026-10-07 继续时 Docker 已启动，但旧实验镜像和卷均不在当前数据环境。原配套 wheel、两个 B 的主机待答导出、账本和全部真实响应仍在。[恢复脚本](../../../scripts/ifc_repair/repair_comparison/containers/rebuild.ps1)在原批准的独立容器内使用原 Python digest 与原 DSH wheel 重建镜像；用 [`IsolatedB.restore_state`](../../../scripts/ifc_repair/repair_comparison/isolated_b.py)恢复新卷，只接受匹配本题公共输入的原生导出，不覆盖已有卷。生产 API、Prompt、Schema 和原始六项终止记录不变。新镜像 ID 及实际依赖重新记录，恢复后的四组假 HTTP 链路复核完成前不调用模型。

本次工作窗口从北京时间 19:05 开始，21:05 前为用户重启留出收尾时间；五题保持未见，付费范围仅为两个开发 demo。恢复状态和窗口记录在原运行区，最终在途请求、后台进程及停止检查以联调结果页为准。

### 6.13 B 场景定位链路修复与离线准入（2026-10-07）

用户批准按链路审查建议修改 B，并取消此前重启安排。实现及逐项验证见[场景定位修改计划](scene-grounding-plan.md)。第一阶段现在接收请求与公共 D 的精简场景，可继续查询真实楼层、世界坐标、宿主及参照构件；系统内部核验身份并计算墙局部位置，不要求用户给 Name、GUID 或局部偏移。新方法 `text2ifc/ifc-scene-grounding/0.2` 通过 API、CLI 和隔离 B 明确选择；旧任务保留原方法，恢复时不能切换。

本轮使用确定性 Provider 和假 HTTP 验证。两道开发题通过完整 Linux 实验链路与原固定评分器，格式、位置、尺寸、关系、外观和保全均通过；另一个 Linux 澄清恢复检查保持原生 ID 和累计预算。方向回归还修正了进口洞口轴向反转时参照窗框翻转的确定性缺陷，保留红例，未放宽评分条件。详细测试命令范围和结果见计划，不将重叠测试计为能力样本。

新 B 的两题开发准入为 `.tmp/repair-comparison-runtime/scene-stage-admission.json`，原准入保留作历史证据。Goal 已恢复，接下来在 `.tmp/repair-comparison-demo-scene-live` 使用原公开请求做真实开发尝试；旧八任务及答复对照不覆盖。首批五题继续只审题和离线检查，未向模型发送。本次属于已见开发题上的可运行性验证，不构成正式四组比较或系统级能力提升。

### 6.14 新 B 真实开发通过与覆盖核验优化（2026-10-07）

新 B 用原自然语言请求完成两个 demo，未人工补充 Name、GUID、偏移或其他事实。窗题8次请求309657 token，门题4次请求55004 token，两份唯一IFC经原固定评分器检查全部通过，schema＋EXPRESS零诊断。全量HTTP、Linux状态、返回推理与执行代码已追加归档，旧八任务及澄清失败保持。详细流程、费用和边界见[联调结果](demo-results.md)。首批五题保持正式未见、待真实人审。

用户随后要求优化完整列表查询。现在核对已提供ID是否覆盖公共D中的目标全集，再在本地排序；混合类别、冗余楼层条件和不同排序不必再发同样的单类查询。8轮上限和注册Prompt／Schema不变，缺项、相关几何未知、错误参照和排序歧义仍拒绝。43项聚焦回归、9项API／SDK检查和Linux两题假HTTP完整链路通过；冻结原前两次响应的离线比较表明旧核验器误拒、新核验器接受，无额外模型调用。优化后的阶段准入单独保存为 `.tmp/repair-comparison-runtime/scene-stage-admission-coverage.json`，原真实调用准入不覆盖。

### 6.15 二十题与四组评测 Goal（2026-10-08，进行中）

用户确认 formal-004 原源与展开几何候选均不能在 usBIM 正常显示，授权替换该源；随后开启 Goal：在首批五题基础补齐 15 个不同 IFC 的损伤与自然语言请求，并执行 A/B/C/D 共 80 个任务，交付通用指标表。允许 B 确定性缺陷的最小修复及相关测试；沿用约 20M 模型 token 目标，超出无需重复费用审批。此次已授权正式调用范围，仍须先满足当前正式阶段的离线准入，不继承两 demo 准入冒充正式准入。

执行顺序：替换 004 → 完成并校验 20 套 G/D/请求/私有条件 → 多目标独立评分与 80 任务编排离线验证 → 冻结样本、规则、配置、轮换顺序及按题预算 → 四组真实执行 → 固定评分器重开唯一产物并生成逐题及汇总表。继续限定简单门窗修复，含保留空洞补门、删除构件和洞口后重新开洞补门窗、S1/S2/S3 组合；不据这批结果宣称覆盖全部 IFC repair 能力。

公开请求使用自然语言、几何位置和明确尺寸，无 GUID、无不必要 Name、无工具/API 方法引导；REVIEW 用真实 Name 区分受损原件。技术审题负责尺寸、坐标、楼层、参照、损坏范围与 schema＋EXPRESS。用户明确委托：“审题托付给你先 我后续再审 你先做实验吧 如果没问题我就不审题了”。本批检查通过后记录`accepted_by_delegation`、`kind=delegated_technical`、授权原话及实际技术证据；`human_viewed=false`。委托替代本批原逐题人工接受节点，不伪写为用户已在usBIM逐题查看；后续人工复核保持可选。

源文件不修改。004 旧显示失败记录保留在原证据位置；替换后只维护同一题号和目录。20 个不同文件不自动等于 20 个独立场景族，原场景族与共同生成器在冻结清单及报告中明确保留。所有失败、无输出、待答、未知用量和实际返回推理入账，不重开正式任务挑最好结果。

当前已确认 Docker 和原固定镜像、DSH wheels 仍在；旧准入仅覆盖开发 demo。现有开发评分器不能直接读取正式 candidate/0.1 或多目标，故新增实验侧 `formal_scoring.py` 与其聚焦测试，不改写已使用开发评分语义。源选择、运行审计、评分实现按独立文件分工并行；本节随实际结果更新，不预写通过或完成。

20题已全部通过实际技术审题并冻结为 `formal/frozen-plan.private.json`：20个不同源、38个目标，S1/S2/S3为7/8/5题，9份CC-BY-4.0、9份MIT、2份GPL-3.0-or-later。三道澄清题（013、016、020）省略第一扇窗的洞底高度，备选高度的可解性也已实测；原图和答复卡只在实验侧。005参照门的几何剖分不能建立完整外观等价见证，固定评分器将未证明等价记录为待复核，不为揭示结果后临时放宽。

正式阶段父准入已通过，保存在 `.tmp/repair-comparison-formal-expansion/stage-admission.json`。依据包括：四组真实Docker运行时8项假模型任务及问答恢复、DSH预算停止；68项运行与公共修复合同回归；19项准入／回滚检查；54项正式评分与调度检查；2项实际CLI全链路测试（20个有效合成题、80个工作区和评分行，包含失败及卡外待答）。另有21项审题回归。范围存在重叠，不相加作为独立能力样本；这不是全仓Preflight或真实模型修复成绩。真实任务位于 `.tmp/repair-comparison-formal-live`，北京时间2026-10-08 02:17左右启动，按单活动任务与冻结轮换顺序执行，不自动重开失败任务。

首6次实际尝试使用`195952a0`，已保留终态与2,176,547实际token：A001严格通过，B001门框偏移，C001未显式提交，D001预算拒绝被记为运行错误，B002属性实例族冲突，C002构件和关系齐全但格式不合格。[三项最小修正](formal-stage-corrections.md)经真实红／绿与5条原生容器假模型链路验收，形成同阶段`stage-admission-revision-01.json`；代码提交`98bad0ee`。37个未启动A/C任务显式迁移中性提交协议，B只更新5个生产文件，74个未启动任务绑定修订证据，原六次不补跑或覆盖。北京时间03:32左右恢复调度。逐任务表将明确这些版本差异，不能将这批混合版本记录当成盲测能力改善。

第二次在19项终态、61项未启动时安全停下，累计已知用量12,299,162 token、未知调用0。B005暴露新增映射安装锚点收窄旧的无映射门类型路径；本次只在`resolution_flow.py`恢复其原有简单几何控制流，保持映射保护和其他能力限制。新增23项兼容性家族与原22项锚点家族联合45项通过，准入相关32项通过，完整真实容器假模型组合3项测试／6条任务路径通过；形成`stage-admission-revision-02.json`与`d8e5d388`。实际R1运行包及暂停材料已先封存，61项追加修订事件、19项原state／calls／events不改，只替换B的一个源码文件，A/C不再迁移。北京时间05:27左右从005-D恢复；执行版本最终分配为初始6项、修订01的13项、修订02的61项。题目、独立评分、模型、预算和顺序不变，失败不补跑。

第三次在30项终态、50项未启动时正常停止，已知用量20,867,899 token。D008原生final_response已明确声明唯一IFC，但宿主接收器漏掉说明末尾的JSON代码块；原no_output及候选未被覆盖或补认。仅接收器及准入测试注册变更，121项相关回归、39项准入检查、真实DSH假模型三个独立提交场景通过，`stage-admission-revision-03.json`与`3a621c62`封存；50项只追加修订事件，30项原state/calls/events不改，不替换B包或迁移A/C协议。北京时间07:01左右从008-B继续；已运行版本实际分配为初始6项、修订01的13项、修订02的11项，其余50项绑定修订03。沿用超20M无需再次审批的原授权，每题预算和其他冻结条件不变。原D008是接收器失败，不将其无输出解释为模型修复质量结论，见[修正记录](formal-stage-corrections.md)。

40项检查点覆盖前10题的四组：全部终态均已有固定独立评分，已知27,679,639 token、2条未知用量；011-C继续运行。[运行中20×4对照](../../../.tmp/repair-comparison-formal-live/operator/PROGRESS.md)与账本为实时入口。D009和D010提交通过统一评分；原失败不补跑。B010的数量、尺寸、关系与保全通过，三窗进深偏差275mm；公开请求未显式指定参照进深，保留冻结评分并注明语义局限。C010因HTTP502无正式产物，不能据此判断修复质量，详见[只读诊断补充](formal-stage-corrections.md#追加40项检查点的只读诊断)。

归档工具仍位于同一ignored脚本，23项自检通过；已补齐R3三份测试源码与实际绿测SHA的映射、异常返回思考字段守卫，以及精确终态HTTP错误的凭据排除引用。原state、calls、wire和IFC不替换；含本任务路由token的原events成员留在私有SQLite，包内只记录authority、selector和原派生字节哈希，显式标为`reference_only_secret_excluded`。正式产物和分数未改变。最终80项汇总将验证缓存评分输入、policy、产物、终态与澄清，再复用固定汇总函数；这是事后一致性检查，不补造早期评分执行证据，工具尚在聚焦验证中。

## 7. 后续任务按依赖安排（最新实施状态见§6.11–6.15）

| 后续任务 | 拟创建／复用路径与输入输出 | 验收及拟最窄测试 | 文件／环境副作用 |
|---|---|---|---|
| W2 A/C 公共工具 | `neutral_tools.py`、`direct_runner.py`离线实现已落地；后续补实际Provider协议和容器工具后端 | `test_direct_runner.py`、`test_experiment_cli.py`、`test_public_repair_flow.py`已覆盖离线路径；真实网络和Shell隔离另验 | 当前仅可信离线脚本；后续获准容器不挂载仓库或凭据 |
| W3 B 薄适配 | `ours_adapter.py`、`provider_observer.py`离线实现已落地；后续补真实HTTP重试、用量观测和外部超时看护 | `test_ours_adapter.py`及既有`test_run_state.py`、`test_provider_stage.py`；本轮未改HTTP适配器，未重跑无关的`test_phase6_2_openai_compat.py` | 仅实验目录；已单独获准的尺寸写回修复见§6.6，未改Prompt／Schema |
| W5 独立评分基本自检 | `scoring.py`已支持两题开发范围；后续扩展多目标、不同几何剖分和形式等价保全，再结合正式题卡冻结 | `test_scoring.py`及公共D脚本闭环；不导入B application record作为输入 | 仅开发评分；不改旧policy、正式分母和冻结Proof |
| W4 D 完整运行时接入 | `dsh/`已有构建、安装、原生问答桥和隔离探针；下一步接阶段2账本、人工答复和唯一提交 | §6.9已使用真实DSH＋fake Messages验证核心工具／问答／子Agent／摘要／失败／停止；冷中断、累计预算和四组准入仍待完成 | §13安装已获准并执行；不改上游loop，不调用真实模型 |

普通测试采用`python -m pytest tests/ifc_repair/repair_comparison/<指定测试文件> -q`；问答桥采用`node --test tests/ifc_repair/repair_comparison/dsh_question_bridge.test.mjs`；DSH原生探针在§6.9固定镜像中执行。缺失检查保持未验收，不能跳过后称通过。

独立评分的最低自检：外部 IFC 不含 ChangeSet 仍可评分；未修 D；合法新 GUID／STEP 重排；数量齐但尺寸错；错宿主／漏关系；属性写错对象；非目标误删；重复补建；目标无几何；最终无输出保留原分母；awaiting_user 保持 pending；未问但碰巧修对；问对但没修好；评分器异常为不可评估。匹配不能按待评分尺寸或关系挑最有利对象，墙开洞允许范围也不能放宽为整墙任意漂移。规则测试同时保留“已有错误”与“新增错误”，区分最终通过、预先冻结例外和相对诊断。

现有可参考的最窄回归入口是 `tests/ifc_repair/test_compare.py`、`test_ifc_validation.py`、`test_benchmark_evaluation.py`、`test_evaluation_boundaries.py`；本轮未跑。旧 validator 测试允许 baseline errors，不能替代新实验规则检查。

每次失败先区分基础设施、任务合同、评分器和模型输出；评分故障用原提交重算，不能重调模型挑成功轨迹。正式揭示结果后不换 GPT、放宽容差、改分母或单组追加额度。

## 8. 人工节点、阻断与本轮验证

**当前已完成第一轮人审意见的简单制题修订。** 用户认可其余内容并要求去GUID／无必要Name、自然语言定位、无方法引导、按数量组合分级，以及格式合格的D；已落实到§6题包和工具。门开向必答卡已撤销，修订后的请求与验收仍保留待复核状态。后续按批准计划衔接实验基础及每批5题正式材料，不重复请求已经获得的制题授权。

开发题卡形式、§13安装／Docker／构建网络范围及本轮开发调用已获准。后续需用户参与：首批五题及随后正式题逐一人工接受；确认真实澄清事实；正式批次预算和评分条件冻结。具体容差、合法替代或答复事实有语义歧义时，带已准备好的材料询问，不重复请求开发费用批准。

上述逐题人审要求是此前安排；2026-10-08用户在§6.15明确委托本批技术审题，允许先做正式实验。20题技术审查、多目标评分、正式冻结及阶段准入已完成，原80任务在63项终态处暂停。本轮单独修复B及原001～005、006～010两批开发复验均已完成；真实终态与005离线重放分列，原批次未恢复。依据为正式阶段父准入及适用的修订准入，不能用两题demo准入代替。缺失或过期准入不自动触发Full Preflight，也不继承以前IFC2Text额度。

初次就绪核对及阶段1–3历史验证见§6.3／6.8／6.9；先前五题准备、开发准入和demo进展见§6.11。首批五题原剖切图、浏览器桥不可用和当时待人工接受均为历史状态；当前20题另有技术审题和逐目标图像，不宣称用户已在usBIM逐题查看。demo六项真实终止记录及唯一提交已作[Git可恢复归档](../../../dataset/processed/experiments/repair-comparison-demo-20261004/README.md)，当时两项B待答状态仍保留。当前正式实验进度以§6.15及本轮账本为准。

## 官方资料

下面 DSH 源码链接绑定同一提交；访问日期均为 2026-09-29。文档支持、静态源码结论和实测环境已在正文分别标明。

[D0]: https://github.com/deepseek-ai/deepseek-harness/tree/4878cdabd87d4041bdaff61d04c966883b9fd07a
[D1]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/python/sdk/README.md
[D2]: https://pypi.org/pypi/deepseek-harness-sdk/0.1.5rc1/json
[D3]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/python/sdk-runtime/README.md
[D4]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/bundle/sdk-app/README.md
[D5]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/python/sdk/src/deepseek_harness/client.py
[D6]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/SAFETY.md
[D7]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/interaction/user-questions/README.md
[D8]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/sdk/protocol/src/types.ts
[D9]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/compaction/compaction-basic/README.md
[D10]: https://api-docs.deepseek.com/api/create-chat-completion/
[D11]: https://docs.docker.com/engine/storage/bind-mounts/
[D12]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/llm/llm-deepseek/README.md
[D13]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/llm/llm/src/types.ts
[D14]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/bundle/headless/README.md
[D15]: https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/interaction/tool-ask-user/README.md
[D16]: https://pypi.org/pypi/deepseek-harness-runtime-bin/0.1.5rc1/json
[O1]: https://developers.openai.com/api/docs/models/gpt-6-sol

- [DSH 固定源码与标签][D0]；[SDK 接口][D1]；[SDK 发布元数据][D2]；[runtime 发布元数据][D16]。
- [runtime 包与构建][D3]；[完整 sdk 组合][D4]；[Python client 生命周期][D5]；[官方隔离说明][D6]。
- [原生问答服务][D7]；[ask_user_question 工具][D15]；[SDK 协议][D8]；[SDK server 限制](https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/sdk/server/README.md)。
- [原生压缩][D9]；[usage／reasoning 类型][D13]；[headless 投影][D14]。
- [DeepSeek Chat Completions][D10]；[Messages adapter][D12]；[Docker 挂载][D11]；[GPT-6 Sol 官方模型页][O1]。
