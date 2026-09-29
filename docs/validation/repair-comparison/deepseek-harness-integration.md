# DeepSeek Harness：渐进调研、实验接入与隔离计划

> 更新：2026-09-29｜版本：v0.2｜文档类型：接入与环境设计。
> 状态：§13安装范围已获准，固定版DSH已安装并完成首批原生离线验证；阶段3的统一账本和四组隔离接线仍在推进，不含真实模型调用。实际结果见[开发就绪审查§6.9](development-readiness.md#69-阶段3dsh安装与首批原生离线验收)。
> 适用对象：D / `deepseek_native`；分组与任务见[计划](plan.md)，计分与资源口径见[指标](metrics.md)。

## 1. 要接入什么，不接入什么

将 DeepSeek 官方 Harness（DSH）作为独立答题系统：获得当前题的中性请求和 IFC 工作副本，在自己的 agent loop、工具和上下文中完成操作、提出问题、接收回答并提交 IFC。

接入是“调度程序能启动、交互、记录和停止 DSH”，不是把 DSH 作为 B 的一个子 Agent，也不是把我们的 repair 工具装进 DSH。D 不阅读 Text2IFC 开发仓库、私有参考或其他组结果，不负责开发我们的修复程序。

用户已同意从头逐步调研和隔离；Docker 是优先候选，不以本文件为立即安装或运行付费模型的指令。日常 Codex、个人技能与会话保持不变。

## 2. 前版已读资料与本轮核实边界

2026-09-29 重新核对官方源码与发行元数据：源码标签 `dsh-v0.2.0-rc.1` 对应 `4878cdabd87d4041bdaff61d04c966883b9fd07a`，PyPI SDK/runtime 最新发布仍为 `0.1.5rc1`。建议后续固定已审阅源码的完整 `sdk` profile，使用同版配套制品或从同一提交构建；不能拿新源码文档混装旧 wheel。固定引用、环境事实和实现建议集中在[就绪审查 §5](development-readiness.md#5-dsh-官方调研入口可确定原生接入仍有工作)。

最初D0静态核对确认 SDK 支持同会话继续、根事件和子Agent通知，但标准协议没有现成人工问答RPC；原生question服务需要仅转接的answerer bridge。当时venv/PATH没有DSH，Docker客户端存在但引擎不可连接，未启动服务。这是安装前记录；安装后版本、问答、摘要／失败记录和停止实测统一见就绪报告§6.9，不能继续把D0环境当作当前状态。

| 需要核对的内容 | 前版读取线索 | 接入前动作 |
|---|---|---|
| Python 驱动 | `deepseek-harness-sdk` 通过子进程驱动运行时 | 检查目标平台制品、SDK/runtime 配套版本及实际字段 |
| 原生组合 | 完整 `sdk` 与 `sdk-minimal` 是不同组合 | 选择完整原生组合；不能为接入方便换成精简后仍称原生完整基线 |
| 一次性入口 | headless 可输出事件、继续已知会话 | 检查当前版本如何提问和继续，单轮结束不等于整题终态 |
| 状态位置 | 显式 home、会话、profile 数据 | 核查 HOME／DSH_HOME／缓存及继承设置，工作目录不是权限边界 |
| 模型传输 | 前版看到原生 Messages 路线 | 核查实际端点、鉴权、thinking、tool history、usage；不能直接套旧 Chat Completions 地址 |
| 事件范围 | 根事件与子 Agent 通知范围不同 | 验证能否覆盖子 Agent、摘要和失败，不只统计主对话 |

用户已明确 DSH 未做本项目实验接入。即使机器有全局安装，也不能直接沿用个人数据目录当作已准备好的实验环境。

## 3. 调研顺序与交付

### D0：只读检查，不启动原生任务

查明本机／候选服务器的系统、Python、Docker/WSL 状态和现有依赖。只读取版本、配置说明和路径，不读取或输出密钥，不触发登录、不更改全局配置。选择官方文档与源码作为依据，记录日期和所对应的版本。

本步骤交付一个具体结论：推荐哪种入口、哪些本地条件已具备、哪些未知，以及下一次最小验证需要什么。不要仅罗列大量工具选型，也不要立即搭全功能代理网关。

### D1：确定最小独立环境

优先考虑一次性 Linux 容器；Docker 不可用时，依据实际环境提出专用虚拟机／服务器隔离方案及差别，不自动要求用户迁移日常开发。

确认安装范围、依赖来源、网络、磁盘与权限后再执行安装。限定实验镜像或明确的独立环境，不默认全局 npm／pip 更新或修改 `~/.codex`、`~/.agents`、`~/.dsh`。

### D2：离线启动与真实工具验证

在已经获准的独立环境中，用假模型传输验证实际 DSH 运行时、文件工具和 Shell。可以替换远端模型响应，但不能 mock 整个 DSH loop 后称原生接入通过。

先验证读写本题文件和退出，再验证普通提问／回答／继续、失败、截断、超时及子进程清理。所有 fake/replay 结果明确标为离线，不作为真实修复成绩。

### D3：轨迹和预算

验证接口返回推理、工具往返、根与子 Agent、摘要、重试及 usage 的归集。动态预算按 task_id 绑定，不以 SDK turn 或进程作为预算单元。先证明观察准确，再决定必要的外部限额方式。

### D4：非正式真实联调

只有有效阶段准入、用户认可的费用上限及实验环境可用时，才用非正式开发样例验证实际传输与交互。不得直接启动 20 题或假称试运行不耗额度。开发样例不计入正式 20 题。

### D5：冻结 D 组配置

固定版本、入口、profile、激活插件、工具、模型路由、推理设置、原生重试、压缩、问答方式、网络及预算规则。无法完成的项记录 partial／blocked，不能仅凭成功启动一次就标为 ready。

## 4. 为什么 D 要包住整个运行时

A/C 的 API 调用由外部控制代码发出，模型要求执行的文件操作和命令进入沙箱。D 保留原生 agent loop，自己发请求并调用工具，因此隔离对象更完整：

```text
外部调度与观察
  ├─ 公共任务发放、任务级预算、问答转发、终态收集
  ├─ 受控用户答复卡（不暴露给 Agent）
  └─ 运行完全结束后独立评分

D 组任务环境
  ├─ SDK 驱动／原生启动入口
  ├─ dsh 运行时和原生 agent loop
  ├─ 文件工具、Shell、所有子 Agent
  ├─ 本题工作副本和可写工作目录
  └─ 本题 HOME、DSH_HOME、会话与运行缓存
```

只把 Python 放进容器、让 DSH 的文件工具仍运行在宿主机不满足此方案。只设置 cwd 或另建 Git 分支也不能证明 Gold 与其他任务不可访问。

配置安全边界是实验环境工作，不以给 D 追加“不要读取答案”提示代替。它与让 A/C 自由选择 IFC 修改方法并不冲突。

## 5. 文件、安装、状态与生命周期

### 5.1 工作副本和最小挂载

| 路径角色 | 内容与权限 |
|---|---|
| `/workspace/task.md` | 共同公开请求，只读，不标注题目是否澄清 |
| `/workspace/model.ifc` | 当前题可写工作副本，允许直接编辑 |
| `/workspace/work/`、`output/` | 自己生成的脚本、临时文件和另存产物 |
| `/state/home/`、`/state/dsh/` | 本题独立 HOME／DSH_HOME，保持同题状态 |
| 运行时安装区 | 固定 SDK／runtime 和依赖，不包含私有数据或项目修复实现 |

G、冻结 D、删除信息、人工损坏报告、答复卡、评分器、其他方法输出、开发仓库和个人 Agent 配置不挂载。不给 Docker socket 或其他能控制宿主环境的接口。

直接编辑只作用于可写副本；冻结 D 始终在评估侧。正常提交副本或另存文件后由外部收集器冻结唯一结果，不把某个目录里的“最新 IFC”随意当最终答案。

镜像构建上下文也要白名单，不先复制全仓库再删除 Gold，因为删除后的文件仍可能留在镜像层。安装包缓存可以复用，任务答案和会话缓存不能复用。

### 5.2 不同题重置，同题保持

不同 task×arm 创建新工作目录、新会话、新 HOME／DSH_HOME。profile 模板只能有固定配置和无历史安装资源，不包含个人或开发任务的会话记录。

同一任务进入 awaiting_user 后保留文件、计划、会话和 ledger，收到回答后继续。原生可能生成新的 turn／调用编号，但外部 run_id 不变；不能借“重新启动”重新获得完整额度。

任务内的正常计划、记忆、工具和子 Agent 保留。隔离跨题学习不等于删掉原生会话内能力。

### 5.3 终态与文件冻结

明确提交或原生真正结束后，先保证相关写入者已停止，再检查实际提交路径是本题普通文件并冻结。不能从多个候选中借私有评分挑最好一个。

超时或不可恢复错误时，撤销任务继续调用能力并终止后代进程；只关闭 SDK 父进程未必足够。遗留 IFC 可保存为诊断，不自动提升为正常正式提交。

## 6. 网络方案分阶段决定

### 6.1 D 需要必要模型通道

A/C 的代码容器可禁网，由外部 API loop 通信；D 的原生运行时自己调用模型，不能直接全禁网后期待它运行。需要限制到实验允许的模型通信，网页检索、远程 MCP、个人同步和其他任务资源不默认开放。

控制端不借网络给 D 提供专用 IFC 知识或评分反馈；四组共同用户输入保持一致。原生安装依赖在准备阶段完成，正式任务中不让某组独享在线查资料。

### 6.2 首选最小可验证方式

先调研运行时是否支持明确模型端点、任务级记录及可靠关闭。能够以独立环境、专用凭据、出站限制和原生日志满足需要时，不强制先开发完整网关。

只有当完整计量、凭据隔离或预算执行确实需要时，再增加薄的模型转发层。该层只做协议转发、认证、计量和限制，不改请求语义、不修回答、不注入额外工具或隐藏事实。

不能只设置 HTTP_PROXY 就宣布没有直连。若选择网关，需验证实际网络规则、清空代理变量后是否仍能绕过、原生辅助请求是否也受限。具体参数必须来自所选版本，不写不存在的禁网／禁记忆选项。

### 6.3 协议兼容

前轮读到的原生 route 为 Messages 形式，可能不同于本项目 B 的 Chat Completions。实际 SDK/adapter 版本的 base URL、认证头、请求路径、流式块、thinking 与 tool history 要逐项核对。

不为了省开发将 D 改成 A 的传输／loop 后仍声称完整原生基线。同一底座跨协议参数无法完全等价时，保留可观察配置和限制，不伪称完全等算力。

## 7. 用户澄清与同题继续

### 7.1 区分 turn 结束和 task 结束

D 可能在一个 turn 的最终消息中提出问题，也可能有原生用户输入事件。调研要确认当前入口如何表示，并用实际版本验证；不能仅根据 finish_reason=completed 或 CLI 退出 0 判定整题已经完成。

实验应支持：原样捕获问题 → awaiting_user → 人工按答复卡回答 → 原生会话继续 → 后续工具执行／最终提交。适配器不得替 D 识别缺失尺寸再生成额外问题。

### 7.2 回复一致性与原生性

初始消息仍只有中性请求和 IFC，不提示“请先澄清”。普通向用户提问的能力对所有 20 题开放，不让公开文件名、工具 schema 或 metadata 暗示哪些题需要问。

答案来自受控卡片，按被问到事实提供，四组同义问题获得相同信息。不得把完整答复卡挂载给 D；不得在运行后查 G 或 mutation mapping 来答题。若需要人工判断一个原生消息是否为问题，保留原文及判断，不凭私有参考自动补全。

### 7.3 等待时间和预算

等待人工期间停止模型／工具主动工作。active 时间可暂停，wall 时间继续；若子 Agent 仍活动，就必须继续计算对应时间与用量。收到答复后沿用本题累计预算，不计作第二个正式任务。

用户未答复的处理由任务规则规定，不能 UI 窗口关闭就丢任务，也不能无限等待且声称已经完成。问对与修好分别记录，指标见[交互规范](metrics.md#11-澄清的记录与判定)。

## 8. DeepSeek 推理与原生事件

### 8.1 保留实际返回内容

保存原生 API 返回的推理字段或内容块，和最终文本、工具调用、工具返回分开引用。必要协议元数据随原始记录保留，不把 Messages 形式强制压成一个假定的 reasoning_content 字符串。

前版提供的 Chat Completions reasoning_content 线索适用于相应协议，D 的原生块和历史回传要求需要单独核实。未返回的内容不补写，截断／空／缺失／脱敏状态明确记录。

不通过提示要求模型“输出完整思维链”，不为了凑日志开启其他未经确认的推理模式；保存记录不应改变任务条件。原始推理只供事后分析，不重新注入其他题或另一组。

### 8.2 根、子 Agent 和失败

不要只保存 result.final_response 或根 events。调研 notifications、持久会话、子 Agent 祖先关系和原生传输记录，确认摘要、失败／重试是否能关联到同一个 task。

终端展示可能截断或略去未提交消息，所以日志覆盖必须实测。原生日志与外部账本互相校对，缺失就标 partial／unavailable；不能用可见文本长度估计完整 token 并当作真实账单。

记录 request_id、run_id、native_session_id、parent_session_id、stage、attempt、model_requested/observed、wire_protocol、reasoning_ref/status、finish_reason、usage 和时间。认证头／密钥不写入公开材料；诊断应通过脱敏副本展示。

## 9. 动态预算与可靠停止

按 task_id 读取预算配置，同题各组采用相同分配和增加规则，不再默认每题统一 128k／900 秒。增加额度需有事前触发条件、追加量和总限额，不能读私有评分或优待某组。

SDK 的单次输出参数与整个任务累计 budget 分开。摘要、子 Agent、Provider 内部重试和同题继续都进入累计账本；任何辅助模型不同时记录其型号，不能仍称全部同底座。

先核实 usage 语义、输入缓存和推理子集，避免重复累加累计快照。并发请求会有在途消费，事后统计不等于硬限制。需要严格总额时验证预留／结算与最大过冲；不可精确时如实报告，按批准方式执行。

超时或 token 超限由外部停止机制执行，任务进程及后代均应回收。暂停人工等待与运行终止不是同一动作，前者保留状态等待继续，后者冻结终态并阻止后续收费请求。

## 10. 接入验证清单

| 验证主题 | 最低证据 |
|---|---|
| 配套安装 | 实际版本、平台、入口、依赖与无个人配置继承 |
| 原生性 | 完整 profile 与真实运行时，非替换为我们的 loop |
| 中性输入 | 公共输入没有方法提示、教程、答案或澄清标签 |
| 工作副本 | 直接编辑可用，冻结 D 不受影响；其他题与宿主路径不可达 |
| 干净状态 | 新题无上题记忆，同题提问后可继续 |
| 问答往返 | 原生问题捕获、人工答复、上下文与预算延续 |
| 推理轨迹 | 真实返回推理和 content 分离，截断／缺失有状态 |
| 完整用量 | 根、子 Agent、摘要与重试计数不漏不重，未知被标注 |
| 网络 | 必要模型通道可用，非允许访问与绕过途径被检查 |
| 停止与提交 | 后代进程可停止、唯一产物可冻结、不从诊断候选挑最好 |
| 评分边界 | G／私有合同不进入 D，只在运行后由统一评分读取 |

离线测试可使用无敏感 canary 验证不可访问区域，不拿真实凭据试验。测试与真实连通性分开记录，初始化成功不算 IFC 修复成功。

## 11. 发现问题时如何处理

版本不匹配先查制品与接口，认证失败先核对协议，工具读到宿主路径先修隔离；不要不断试收费请求或靠更强提示掩盖环境错误。事件流有 final 但无 IFC 时记录无产物，不补造输出。

对已明确的 Docker 候选、四组结构、GPT API、推理记录和澄清，不重复征求原则选择。只有安装会改变日常环境、原生能力无法在当前平台保持、网络／权限需实际变更或需要费用授权时，提交具体问题和最小替代方案。

## 12. 来源与更新记录

以下保留上游导航入口；2026-09-29 实际核对所用的固定提交、PyPI 元数据及逐项引用见[就绪审查的官方资料](development-readiness.md#官方资料)。导航中的master不作为实验版本锁，本机运行证据见该报告§6.9：

- Python SDK：`https://github.com/deepseek-ai/deepseek-harness/blob/master/python/sdk/README.md`
- headless：`https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/bundle/headless/README.md`
- 原生模型传输：`https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/llm/llm-deepseek/README.md`
- 上游环境说明：`https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md`
- Docker mount：`https://docs.docker.com/engine/storage/bind-mounts/`

2026-09-28 / v0.2：将一次性完整 SDK／网关实施改为先调研、最小环境、逐步验证；保留完整原生边界，采用可写工作副本；补澄清同题继续、推理轨迹和任务动态预算。详细安装命令和 SDK 代码等到选定版本核实后写入，不将旧示例当已验证本机执行说明。

2026-09-29：先完成D0只读核对；随后用户另行批准§13安装，实际完成固定版构建／安装和首批原生离线验证。统一实验账本及四组完整准入尚未完成，没有真实模型调用。

## 13. 阶段3安装与隔离方案：已批准的具体范围

用户于2026-09-29明确答复“批准按§13安装并做离线验收”。下列范围已获准，不重复申请；实测结果在就绪报告更新，方案中的拟执行项不自动等于已通过。

2026-09-29批准前核对：Docker的`desktop-linux`引擎不可连接，WSL中的Ubuntu-22.04与docker-desktop均停止。Docker设置的`CustomWslDistroDir`为`G:\dockerdata\DockerDesktopWSL`，该目录存在；G盘剩余92.88 GiB，E盘266.09 GiB，C盘22.29 GiB。批准后启动成功，实际VHD位置也已核实，见就绪报告§6.9；未迁移已有Docker数据。

### 13.1 推荐执行范围

保持已审阅的`dsh-v0.2.0-rc.1`／`4878cdabd87d4041bdaff61d04c966883b9fd07a`，从同一提交构建Linux x64的SDK与runtime配套wheel，保留完整`sdk` profile。重新读取PyPI元数据后，公开SDK/runtime仍为`0.1.5rc1`；它不是本方案的替代安装来源。官方构建产物还包含ripgrep、Office资源及其配套运行时，不能只拷贝一个可执行文件或删掉原生能力来节约空间。[构建说明](https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/python/development.md)、[运行时内容](https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/python/sdk-runtime/README.md)。

| 项目 | 本次拟执行的范围 |
|---|---|
| 宿主变化 | 启动已安装的Docker Desktop及其WSL2后端；不另装Docker／WSL，不更改个人Codex、DSH、系统Python或仓库`.venv` |
| 构建 | 独立Linux x64 builder；Node 24、源码指定pnpm 11.7.0、Python构建工具、编译依赖均在容器内；使用源码锁文件，保存实际依赖版本、wheel哈希和镜像digest |
| 固定依赖 | 最终公共工具环境使用Python 3.12、IfcOpenShell 0.8.5；A/C共用完全相同镜像。B另加白名单生产包／公开schema／prompt及必要资源；D另加官方完整运行时及问答转接层 |
| 主机保存位置 | 专用构建缓存／镜像由现有Docker数据盘管理；实验导出物只在`E:\code for project\bimnet\.cache\repair-comparison\dsh`，运行测试在仓库`.tmp/repair-comparison-isolation`。只维持这一套活动目录 |
| 构建网络 | 仅构建容器可访问官方源码和常规依赖源：GitHub及其制品域名、Docker Hub、npm registry、PyPI、Node/Python发行源和基础镜像系统包源；不传入`.env`或API凭据，不执行安装脚本中的真实模型smoke |
| 离线运行网络 | A/C工具容器禁网；B/D原生离线验证仅连专用内部网络中的假模型服务，服务无外网出口，不发布宿主端口。真实模型网络另在阶段5/6验收与费用授权后启用 |
| 资源边界 | 首次构建最多4 CPU、8 GiB内存、60分钟；本轮新增Docker构建数据与导出物以20 GiB为停止阈值，定期检查磁盘，不把它宣称为文件系统硬配额。C盘低于10 GiB或G盘低于20 GiB时停止准备并报告，不自行清理其他项目 |
| 费用 | 不读取模型密钥，不调用真实模型，不购买云资源；仅本机下载、构建和假模型验收 |

启动Docker后先核实引擎、数据盘、资源限制和是否有其他活动容器；不停止其他项目。Docker若要求更新、重新安装或迁移数据，先报告具体变更，不把它含混归入本次启动。完成测试后只移除本实验容器／临时网络；镜像和必要诊断保留在上述固定位置，不执行全局`docker system prune`。

### 13.2 已核对的构建入口

下面命令已在固定源码容器中执行成功。`build-python-release.py`把仓库版本规范化为`0.2.0rc1`，SDK精确绑定到同版runtime。实际入口为`dsh/build-runtime.sh`：Git archive保留Unix模式／符号链接，显式传入官方支持的`DSH_CLIENT_COMMIT_HASH`；依赖按锁文件安装，基础镜像固定digest。版本、耗时和失败修正见就绪报告§6.9。

```sh
pnpm install --frozen-lockfile
pnpm exec tsx scripts/build-exe-for-python-sdk.ts --targets=node24-linux-x64
python scripts/build-python-release.py --package sdk --output-dir dist-python
python scripts/build-python-release.py --package runtime --platform linux-x64 --runtime-exe dist-exe/deepseek-harness-sdk-runtime-linux-x64 --output-dir dist-python
```

参数依据：[可执行文件构建器](https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/scripts/build-exe-for-python-sdk.ts)、[wheel构建器](https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/scripts/build-python-release.py)、[官方构建工作流](https://github.com/deepseek-ai/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/.github/workflows/build-exe-for-python-sdk.yml)。不运行上游带`sdk-live`的验收命令，也不直接运行可能包含真实调用的`all`场景。

若同版构建失败或超过上述范围，保存日志，先判断缺失的具体依赖；不自动切为0.1.5rc1、`sdk-minimal`或另一套loop。源码中的Office和原生系统构建可能影响耗时／体积，20 GiB和60分钟是本次准备的限制，不是已测得的用量或耗时。

### 13.3 容器与验收顺序

1. **先验隔离。** 每个task×arm独立`/workspace`与`/state`，非root、只读安装区、drop capabilities、no-new-privileges、PID／CPU／内存限制；不挂载仓库、Docker socket、Gold、答复卡、其他组或个人配置。B只打包实际生产依赖；A/C/D不包含B代码。用无敏感canary验证读不到宿主与其他组，并验证A/C直接文本编辑及脚本执行均可用。
2. **再验真实DSH。** 新home、完整`sdk`、假模型传输，调用实际文件和Shell工具。记录根／子Agent、摘要、重试、返回推理与usage；缺失字段保留未知。原生问题通过仅转发的bridge呈现，人工回答后沿同session继续，预算不重置。
3. **最后验外部控制。** 原生Shell挂起和后台子进程、模型超时、人工等待、恢复与取消；先停止全部写入者及收费通道，才暂停活动计时或收集唯一产物。B也增加容器外停止看护，不能沿用同步API调用就宣称超时回收成立。

本轮安装验收只回答运行时和隔离是否成立。正式20题人审、评分冻结、完整阶段准入及真实模型费用仍各自独立；没有通过的条目照实保留，不用A/C/B的已有回放测试替代D的真实运行时测试。

### 13.4 已安装环境的离线探针入口

从仓库根目录执行下列准备，仅使用§6.9记录的本地镜像，不下载依赖。假服务单独挂载测试答复与wire记录；D只获得当前工作区、Linux状态卷、驱动和问答桥。该服务只用于测试，不是正式人工答复或费用网关。

```powershell
$repairRoot = Join-Path (Get-Location).Path '.tmp/repair-comparison-isolation'
$repairGateway = (Resolve-Path tests/ifc_repair/repair_comparison/dsh_fake_gateway.py).Path
New-Item -ItemType Directory -Force -Path "$repairRoot/gateway" | Out-Null
docker network create --internal --label text2ifc.experiment=repair-comparison text2ifc-repair-offline
docker run -d --pull never --name text2ifc-repair-dsh-fixture --network text2ifc-repair-offline --network-alias dsh-fixture --label text2ifc.experiment=repair-comparison --user 10001:10001 --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 512m --pids-limit 64 --tmpfs /tmp:rw,nosuid,size=64m --mount "type=bind,source=$repairGateway,target=/fixture.py,readonly" --mount "type=bind,source=$repairRoot/gateway,target=/evidence" text2ifc/repair-tools:py312-ifc085 python /fixture.py
& scripts/ifc_repair/repair_comparison/dsh/run-offline-probe.ps1 -Case core
docker wait text2ifc-repair-dsh-core-native
docker logs text2ifc-repair-dsh-core-native
```

可选case为`core / retry / missing-usage / subagent / truncated / hang / compaction`，逐个运行并检查退出、`/state`原始结果及独立wire；正常case有150秒容器外层截止。`hang`需在确认子进程心跳后从控制侧`docker stop --timeout 3`，再核对停止状态和停止后的文件不再变化。`compaction`仅验证人工降低压力阈值下的原生组件行为。重复场景须先导出证据并显式清理相应测试容器／状态卷、重新启动假服务计数，不能把旧state当新题。

原生可执行文件和缓存需要Linux可执行临时空间；运行探针使用`/tmp`的`exec` tmpfs及独立Linux状态卷，安装区保持只读。验收后已导出原始记录、移除本次测试容器／临时网络和用例状态卷；本地镜像、wheel、源码和唯一构建缓存保留，未清理其他项目。
