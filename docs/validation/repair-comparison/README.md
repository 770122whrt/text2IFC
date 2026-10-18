# IFC Repair 实验

当前汇总：[A—G已结束任务、IFC产出与格式校验](../../reports/repair-experiment-summary-20261015/README.md) · [1200题数据集组成与来源许可](../../reports/repair-dataset-1200-summary-20261015/README.md)。[运行代码与验证范围](../../handoffs/repair/current-code-package-20261015.md)。下文的开发过程与旧批次记录保留各自历史范围。

更新：2026-10-12。目录配对、七组展开、有限并发和按题号续跑已接入。formal-40-pairs-25-20261010 的修复回测统一见[当前结果入口](../../../.tmp/repair-formal-1200-20261011/cycle/README.md)。用户已批准“修复→原题回测→另抽两题→通过后批量”的流程；脚本维护阶段状态与独立检查，Codex只查看摘要并处理失败。此前B两题无输出及F/G接入失败见[原始记录](../../../.tmp/repair-formal-1200-20261011/README.md)，接通不等于修复通过。[此前 B/E/F 试验](../../../.tmp/repair-bef-new-20261011/README.md)、[reserve-005 与 external-020 回归](../../../.tmp/repair-be-debug-20261011/prompt-followup/results/README.md)、[反馈 v0.4 试验](../../../.tmp/repair-be-feedback-20261011/results/README.md)、[上轮定位案例](../../../.tmp/repair-be-locator-20261011/results/README.md)、[前批四组实验表](../../../dataset/processed/experiments/repair-comparison/current/README.md)及[20题审阅入口](../../../dataset/processed/ifc-repair/repair-comparison/formal/README.md)保留原义。提交、评分通过与待评分别记录，不由提交数推定成功率。

前批使用20个源IFC、每模型一个任务、四组共80个任务单元。A是DeepSeek API通用执行器，B是DeepSeek＋仓库RepairAPI，C是GPT API＋与A相同的执行器，D是官方DeepSeek Harness完整SDK/runtime。日常Codex是开发工具。

| 文档 | 职责 |
|---|---|
| [实验计划](plan.md) | 研究目标、公共输入、私有隔离、题包、阶段准入、预算与唯一发布合同 |
| [指标规范](metrics.md) | 数量、构件、关系、格式、保全、澄清与用量；后十题评分待定 |
| [B当前链路](b-common-repair.md) | 公开场景定位、已修共性问题、最终检验回环及支持边界 |
| [D配置](deepseek-harness-integration.md) | 官方DSH版本、安装范围、搜索与网页代理、最新真实问答 |
| [短上下文调研与候选设计](../../architecture/repair-short-context-design.md) | F/G 窗口适配、工具历史精简与可回读证据；已实现兼容层及后置研究的边界见正文 |

当前汇报只保留最终IFC、比较信息、问答、API实际返回推理和真实用量。过期开发文档与未提交日志已退役。已提交机器证据因仓库合同及自动审批限制暂留原位，不进入当前结果表；不另建归档或平行报告。总预算已消耗及未知用量仍保留，不能因精简抹去费用或把未知当作零。

后续调用使用新冻结配置和适用阶段准入。固定预算采用`repair-comparison-fixed-budget-policy/0.2`，token上限见下方输入表；活动时间上限仍为30／40／50分钟，同题各组一致。已启动题目保留0.1预算；排队不消耗活动时间，暂停恢复不重置累计预算。新批次只设每项任务预算，不设总API预算；历史消耗和未知用量仍保留，API预算与Codex账号额度分开。原Phase、R1及已接受Proof状态保持原义。

## 批量脚本

入口：`python -m scripts.ifc_repair.repair_comparison.batch_operator`。脚本负责等待、工具执行、检查、精简导出和推进。正常执行最后只返回一条`summary`，包含完成数、各终态数量、用量及结果入口；阻塞或需要人工时返回简短摘要。Codex不逐题查看IFC、报告、推理或日志，不持续轮询。当前回归从页首结果入口查看；[此前 E 四题定位失败](../../../.tmp/repair-e-random-20261010/results/README.md)、[更早三题及其失败](../../../.tmp/repair-e-pilot-20261010/results/README.md)保留为历史证据；上述四组表保留为前批记录，[原两轮准备记录](../../../.tmp/repair-small-rounds-20261010/results/README.md)保持原义。

两题开发回归使用`development_cycle prepare/run/check`。它冻结选题与评估控制，脚本只返回终态、格式、独立检查和有界原因；新题排除已揭示源模型，同一轮两题均通过才获得批量准入条件。修复后可用`gate --revision 名称`保留新检查，再用`admit --scoped-receipt 路径`绑定，旧失败不覆盖。`refresh-unstarted`允许尚无运行账本的准备批次更新场景方法、已授权的单位约定或调度设置，保留旧配置并要求重新准入；已开始任务仍按冻结配置恢复。

本次已授权自动确认**明确且核验一致的既有实例属性修改**。`run`或`resume`加`--confirm-existing-properties`后，委托授权保存在该批账本，恢复沿用。宿主脚本仅用公开请求与损坏IFC核对目标集合、属性路径、值、原类型和当前预览绑定，再通过原确认接口答复；记录为用户委托规则下的程序核验，不记作逐题人工审阅。多对象／多属性逐项核对，缺项、歧义、类型冲突、新增属性、未知请求形式或不完整预览仍保留澄清。这个开关不跳过Harness校验，不读取私有参考，也不重置会话或预算；默认不开启。

本轮用户确认属性数值以对应 IFC 属性的有效单位为准。新 `prepare` 可加 `--request-convention existing-ifc-property-units/1.0`，只在七组共用的公开任务副本追加单位说明；原请求、IFC 和交付回执保持原样，原始／实际输入哈希分别记录。已准备但从未启动的批次可用 `refresh-unstarted` 加同一参数更新，保留旧计划并重新准入；中断后重复该命令恢复，已启动批次拒绝更改。

本批明确题采用 `run/resume --clarification-policy fail`：先处理已授权且公开核验一致的既有属性确认，剩余未答澄清记 `no_output`，原因 `UNANSWERED_CLARIFICATION_COMPLETE_INPUT_POLICY`，报告保留问题，然后继续。A～G 使用相同规则；D 必须合作停止原生进程并保存用量／会话后才能终止。策略绑定批次并随恢复沿用；省略参数的既有默认仍为 `wait`，产品澄清能力保持。这个终态只表示任务未完成，不把题目歧义、模型错误和 Harness 缺陷混为同一原因。

| 组 | 系统 |
|---|---|
| A/B | DeepSeek＋通用执行器／仓库Harness |
| C/E | GPT＋通用执行器／同一仓库Harness |
| D | DeepSeek＋官方DSH（搜索与网页代理已配置） |
| F/G | Qwen＋仓库Harness／同一通用执行器 |

目录批量默认将N道题展开为N×7项，默认同时运行2项；`--concurrency 1..7`在准备时固定并发上限。加`--qwen-first`会优先派发F/G，Qwen共用两个槽位上限，其余槽位继续派发其他组；CSV与续跑序号保持原顺序。源IFC只读，七组有独立工作区、会话和单题预算。并发受资源及接口限流约束，不保证同时开七项。原两轮方案用`--scope two-rounds`保留：首轮相同两题只跑B/E/F，共6项，优先F；次轮另两题跑A～G，共14项，两轮后停止。该模式需要题型登记，不能用缺少题型的纯文件目录自动选题。

Qwen使用用户提供的腾讯接口及`ms-gmk85rth`，可不带鉴权；地址、模型、可选凭据环境变量和请求参数可在新批次用`--providers`指定。API恢复或更换后先冻结新配置并完成相关准入，已冻结批次不静默换配置。用户于2026-10-11重新提供接口，本轮两道新题的B/E/F并行兼容性测试已结束；F仍有输出截断与定位协议响应错误，当前配置不代表修复验收通过。终态与独立检查见当前结果入口，不把接口响应或Harness自报成功直接记作修复通过。

### 给数据集侧的接口要求

推荐交付一个**只含公开损坏输入和公开请求**的目录，并附UTF-8的`inputs.csv`。参考原件、Gold、损伤记录、删去对象名单和答复卡留在评估侧，不列入CSV，也不进入被测系统。路径使用目录内的相对路径，支持子目录；不要用绝对路径、`..`或链接。

| 字段 | 要求 |
|---|---|
| `case_id` | 必填，唯一；使用英文字母、数字、点、下划线或连字符，最多101字符，避开Windows保留名 |
| `ifc_path` | 必填，损坏后的`.ifc`；必须能通过IfcOpenShell schema＋EXPRESS检查。当前Harness实验优先IFC2X3 |
| `request_path` | 必填，非空UTF-8 `.txt`，自然语言修复请求；脚本原样使用，不改写、不补充方法引导 |
| `level` | 必填，`S1`／`S2`／`S3`，对应750k／1M／1.25M token；同题七组一致 |
| `primary_target_count` | 建议填写，受损主要构件数量；1→S1、2→S2、≥3→S3，附属洞口和关系不重复计数 |
| `task_kind` | 建议填写，`geometry`／`property`／`mixed`；缺失时使用已有属性运行环境，不自动猜题型 |

公开请求尽量用方位、坐标或构件顺序定位，不用GUID；确有必要才写Name。尺寸、单位、参照关系必须准确。必要澄清题可以缺少预先约定的信息，答复事实单独保管；运行脚本不会读取私有参考替用户回答。IFC格式通过只说明文件可用，不等于题目语义或修复正确。

```csv
case_id,ifc_path,request_path,level,primary_target_count,task_kind
case-001,case-001.ifc,case-001.txt,S1,1,geometry
case-002,case-002.ifc,case-002.txt,S2,2,property
```

不带CSV也可以：目录顶层使用同名`case-001.ifc`＋`case-001.txt`配对，并显式传`--default-level S1`（所有题统一档位）。脚本拒绝缺对、重复ID、空请求和不合格IFC。原有`summary.json`／`cases.csv`／`build.json`登记数据集仍可直接接入，复用其已通过的准入检查。数据集侧统一编排、公开导出及私有回执分离见[数据集脚本说明](../ifc-repair-dataset/README.md#数据集脚本说明统一编排与实验交付)。

```powershell
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator prepare --root .tmp/新批次 --dataset 数据集目录 --input-format pairs --scope full --groups A B C D E F G --concurrency 7 --qwen-first --providers docs/validation/repair-comparison/providers.json
# 绑定当前已验证的运行时；源码、镜像或测试证据变化时会拒绝复用：
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator gate --root .tmp/新批次 --tests tests/ifc_repair/repair_comparison/test_scalable_groups.py tests/ifc_repair/repair_comparison/test_scalable_controller_safety.py
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator admit --root .tmp/新批次 --native-receipt .tmp/repair-formal-1200-20261011/admission/native-final/test_seven_groups_actual_linux0/native-stage.json --property-receipt .tmp/repair-formal-1200-20261011/admission/property-final/test_harness_profiles_existing0/property-native-stage.json
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator run --root .tmp/新批次
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator status --root .tmp/新批次 --brief
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator pause --root .tmp/新批次
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator resume --root .tmp/新批次
# 可选：明确核对从冻结 CSV 的第 500 条继续；前 499 条必须已全部进入终态。
.venv\Scripts\python.exe -m scripts.ifc_repair.repair_comparison.batch_operator resume --root .tmp/新批次 --from-case 500
```

上例将每道题展开为 A～G 七项，其中 F 是 Qwen＋仓库 Harness，G 是 Qwen＋通用执行器；省略 `--groups` 也默认七组。上例最多同时运行七项，其中F/G合计最多两项；空出槽位后继续派发，其余排队。并发数是整批槽位上限，不保证每组始终各占一个槽位。大型 IFC 或属性检索需按机器内存选择并发数，不能把小题并发验收当作任意规模的资源保证。准备完成后配置即冻结，恢复沿用原批次。

[当前 Provider 配置](providers.json)不含密钥；DeepSeek/GPT沿用环境变量，Qwen可无鉴权。Qwen服务窗口为262144 token，输入和输出合计；2026-10-12的边界探针也确认了这一限制。配置输入128000、输出32768、`temperature=0.6`、`top_p=0.95`，使用 `chat_template_kwargs: {"enable_thinking": false}`，见[官方非思考模式接口](https://huggingface.co/Qwen/Qwen3.5-35B-A3B#instruct-or-non-thinking-mode)。未返回的思维链不补造；不传`--providers`仍使用旧默认值，恢复沿用各自冻结配置，整题S1/S2/S3预算不变。

当前128000输入值被传入F的Harness；G的通用执行器尚未执行累计输入限制，历史工具结果会不断累加，不能把配置中的数值视为已有保护。本批F/G已暂停派发，A～E继续；并发诊断和后续配置方案集中在[当前实验入口](../../../.tmp/repair-formal-1200-20261011/cycle/README.md)。扩大上下文或调整工具结果保留方式需要新的配置／执行器版本与相关准入，不能静默修改运行中的冻结批次。并发访问正常只证明接口接通，不等于IFC修复通过。

独立 F/G 兼容入口已实现于 [qwen_batch.py](../../../scripts/ifc_repair/qwen_batch.py)：复用当前 Harness／通用执行器，增加 50K 工作窗口、官方 tokenizer 输入估计、历史精简与回读、有界退避、持久化熔断。上段仍描述原冻结入口；新入口不更换原在途配置。具体行为和限制集中在[短上下文说明 §0](../../architecture/repair-short-context-design.md)。使用新根目录，默认仅 F/G、两项并发；`--providers` 仍可配置地址／模型／可选鉴权，`--policy` 可读取指定策略 JSON，准备后不能静默修改。

```powershell
.venv\Scripts\python.exe -m scripts.ifc_repair.qwen_batch prepare --root .tmp/qwen-fg --dataset <公开配对目录> --input-format pairs --providers docs/validation/repair-comparison/providers.json
# 完成与本配置绑定的 gate/admit 后再执行真实模型；未准入会拒绝调用。
.venv\Scripts\python.exe -m scripts.ifc_repair.qwen_batch run --root .tmp/qwen-fg --confirm-existing-properties --clarification-policy fail
.venv\Scripts\python.exe -m scripts.ifc_repair.qwen_batch status --root .tmp/qwen-fg --brief
.venv\Scripts\python.exe -m scripts.ifc_repair.qwen_batch pause --root .tmp/qwen-fg
.venv\Scripts\python.exe -m scripts.ifc_repair.qwen_batch resume --root .tmp/qwen-fg --from-case 500
```

原格式检查交付回执、属性单位公开约定、暂停／恢复和精简导出参数沿用下面的合同。`--from-case 500`仍只是检查点断言，不能跳过前面的未完成题。新 F/G 方法与原结果分开标识；短窗口兼容验收不等于真实 Qwen 修复成功或能力提升。

已封存数据集可在 `prepare --input-format pairs --dataset <数据集>/public` 时加 `--delivery-receipt <数据集>/private/finalization/summary.json`，由宿主程序验证公开交付文件与已有 native＋EXPRESS 回执的绑定，复用充分通过的检查。该回执只在实验侧读取；母本、Gold和损伤配方不挂入运行时。没有可复用回执时仍检查损坏IFC格式。准备后公开输入、CSV顺序和单题预算固定。

续跑以同一个 `--root` 下的账本为准，不需要手填游标：已完成组跳过，第500条若只完成部分组，就继续该条剩余组。`--from-case 500`是检查点断言，不是忽略前面未完成任务的快捷方式；序号从1开始，指本批次冻结的CSV行顺序（抽样批次指抽样后的顺序）。`status --brief`只读调度账本，返回已完成任务数／题数、下一条序号和ID、用量及阻塞原因，不打开IFC、报告或模型响应。完成任务后还会从账本时间投影各组样本数与平均单题耗时（`timing_by_group`），并给出满槽假设的初步剩余天数（`eta_days_at_capacity`）；该估计未计资源争用、限流和Qwen双槽瓶颈，不能当作完成日期保证。

`prepare`读取登记或文件配对、复制公开输入并冻结题目、预算、组别、模型配置、顺序和并发数；纯文件配对的损坏IFC会逐题做一次格式检查，失败时保留准备现场并阻止运行。`--mode offline`使用无密钥假Provider；默认`live`在准入不完整时阻止调用。首次准入用`gate --tests ...`记录实际相关检查，用`admit --native-receipt ... --property-receipt ...`绑定真实容器＋假Provider回执；失败或漂移时不能真实调用。这些是阶段检查，不是全仓Preflight。每个新批次须绑定与实际输入和组别一致的准入；脚本验收不能推定七组模型修复通过。

小规模兼容性测试可以在`prepare --scope full`时加`--groups E --case-ids 题号1 题号2`，只冻结指定题目和组别；不改请求，不自动扩展到其他题目。准入必须覆盖全部实际选择的组，记录也只授权这些组。E与B/F共用最终检验回到ChangeSet的链路，当前冻结上限为2次纠正；C是通用执行器。模型提交、格式通过与任务要求检查通过分别记录。

本轮目录批量的[离线验收回执](../../../.tmp/pytest/parallel-native-20261010-02/test_paired_directory_public_c0/parallel-summary-receipt.json)：七组在现有Linux运行时中完成假Provider任务，实际并发峰值2；每项只有报告与IFC，schema＋EXPRESS检查通过，源输入不变，进程停止，程序只返回一条摘要。修正报告字段断言后复用了已完成批次，恢复没有新增模型／工具调用。原失败断言记录保留；这些是脚本与运行环境证据，不是模型修复成绩。

2026-10-11补充[六路并发回执](../../../.tmp/repair-bef-new-20261011/admission/native/test_paired_directory_public_c0/parallel-summary-receipt.json)：A～F同时运行，实测峰值6，精简导出、schema＋EXPRESS、源文件不变和进程停止通过。同期七组原生接线及Qwen澄清恢复通过；均使用假模型，不计真实实验成绩。

每项对外只导出`report.md`（最多64KiB）和正式提交的`repaired.ifc`；无输出只有报告。报告记录终态、失败阶段／原因、格式检查、时间、实际用量和最多8KiB的实际返回推理，缺失和截断会标明。提交不代表修复评价通过，指标暂待定。

普通修复失败保留后继续；接口、环境、隔离故障或不同题上重复的Harness系统错误停止新派发。`pause`也停止新派发，已启动任务按原规则完成或进入等待，不直接杀进程。在默认 `wait` 策略下，澄清保留原会话与累计预算，D必须保留原生进程等待；用`resume --run-id ... --answer-file ...`提交标为`source: user_confirmed`的回答，不从私有参考临时找答案。多个任务提问时，可先续跑已答复的原任务，其他问题保留等待，新题不启动。恢复不能更改冻结配置或并发数。待处理任务保留恢复状态；完成精简导出且确认进程停止后，脚本清理该任务的临时工作区、原始调用文件和容器状态卷，共用账本保留费用、问答和失败依据。

`resume`恢复可继续的批次／原会话，不重开已经终止的失败题；正式失败不会自动反复调用直到成功。意外进程退出、调用仍在进行但失去控制者、D原生等待进程丢失时，脚本报恢复异常并停止新派发，不能承诺任意崩溃后自动重启。后续确需复测时另留尝试记录，原失败和费用不覆盖。正常运行由脚本内部等待；操作者只需接收完成／异常摘要，按需用`status --brief`查看调度状态。成功率等统计可以后做，但执行时仍记录终态、格式检查和用量；有IFC不等于修复评价通过。

调试时可在 `prepare` 加 `--retain-debug`，将保留策略与批次一起冻结；恢复时不能更改。完成终态、停止及导出检查后，保留原始模型响应、候选 IFC、校验记录、工作区和原生状态卷，便于确定性重放。使用 `debug-export --root <batch>` 将已停止 B/E/F 的原生状态卷复制到宿主机；完整快照可复用，部分或被改动的快照不会覆盖。默认批量仍精简清理，每项对外仍最多两个结果文件。本轮由 [调试驱动](../../../.tmp/repair-bef-new-20261011/live/run_experiment.ps1) 负责运行、停止后快照及独立评估；详细材料仅用于用户已授权的排错，不计为新的能力提升证据。
