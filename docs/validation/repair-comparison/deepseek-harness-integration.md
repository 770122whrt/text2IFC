# D组接线与实验配置

更新：2026-10-10。D使用官方DeepSeek Harness的Python SDK和完整运行时；B使用仓库自己的RepairAPI。

<a id="14-原生-web-search-接线"></a>
## 搜索测试的实际结果

**网页代理已接通，完整真实问答已完成。** 官方DSH主模型实际搜索、读取官方网页正文并继续作答；本次用了6次主模型请求＋4次搜索请求，共180,063 token，约88秒。容器和代理已停止，下次运行由脚本自动启动。此前只调用辅助接口的探针不算完整问答。

问题是：“截至2026-10-10，OpenAI最新GPT是什么？区分ChatGPT与API，给出发布日期和官方来源。”DSH实际答复与独立核对如下：

| 项目 | DSH最终答复 | 官方核对 | 判定 |
|---|---|---|---|
| ChatGPT最新推广系列 | GPT-6，10月7日开始推广 | [官方发布记录](https://openai.com/research/index/release/)、[ChatGPT更新说明](https://help.openai.com/en/articles/6825453-chatgpt-release-notes) | 系列与公告日期一致 |
| API最新新增型号 | GPT-6.1 Sol，9月29日发布；区分最新新增与旗舰Astra | [发布索引](https://openai.com/research/index/release/)、[API模型目录](https://developers.openai.com/api/docs/models) | 关键型号与日期一致 |
| ChatGPT免费／付费分档 | D注明来自二级来源，未读取公告正文 | 官方说明还区分10月7日付费推广、次日免费推广及Pro选项 | 细节未完全核验，不能称整份答案完全准确 |

**实际网页读取：**本次8次原生`web_fetch`中，API模型目录、API更新日志、指南Markdown和官方新闻RSS共5次返回200；OpenAI主站与Help页面3次返回403。D使用可访问的官方入口完成回答。原生搜索仍只交给主模型标题和URL，正文由原生`web_fetch`读取。D超过了开发问题建议的6次抓取上限；固定整题预算未超限，这项执行表现保留。

**用量口径：**最新问答与此前所有真实调用同计原20M授权。既有实际消耗、未知调用及其9M保守占位在当前结果预算记录中单列；占位不是已知实际消耗，未知不能记作零。

代理和配置的聚焦检查、官方完整运行时的假模型／假网页链路均通过；HTTP和HTTPS实际出网也已验证。现在可确认“搜索→网页正文→主模型继续推理→最终作答”可运行，关键型号和日期能够核对；这不是知识准确率或IFC修复能力评测。

<a id="13-阶段3安装与隔离方案已批准的具体范围"></a>
## 当前实验配置

| 项目 | 配置 |
|---|---|
| 请求模型标识 | `deepseek-v4-flash` |
| SDK和运行时 | 官方完整`0.2.0rc1`，不裁剪工具；原生上下文压缩保留 |
| IFC库 | IfcOpenShell `0.8.5` |
| 容器 | 每题独立Linux容器，4 CPU／8 GiB |
| 模型单次输出 | 最多65,536 token |
| 搜索 | 原生`web_search`；辅助输出最多4,096 token，每次工具调用最多5次服务器搜索 |
| 网页 | 原生`web_fetch`通过网关代理读取公共HTTP／HTTPS网页；无需新增密钥 |
| 每题预算 | 按已审损伤等级固定为1.5M／2M／2.5M；同题四组一致，详见[预算规则](plan.md#81-按任务分配与动态调整) |
| 批次预算 | 已批准20M token，根模型、搜索、摘要、子Agent和重试一起累计 |
| 输入隔离 | 只提供公开请求和损坏IFC工作副本，不提供原件G、私有题卡或其他组结果 |

搜索配置放在宿主`.env`，不把真实密钥放入容器：

```dotenv
DEEPSEEK_SEARCH_BASE_URL=https://api.deepseek.com/anthropic/v1
DEEPSEEK_SEARCH_API_KEY=
```

官方端点可复用已有`DEEPSEEK_API_KEY`；自定义端点需单独填写搜索密钥。配置示例见[.env.example](../../../.env.example)。安装复用现有镜像与缓存；原构建授权为4 CPU／8 GiB、60分钟、新增20 GiB停止阈值，不自动扩大安装范围。

## 后续批次保留什么

结果目录尽量精简：成功保留唯一正式IFC；无产物时，在统一结果表写明状态和简短原因。表里保留题号、组别、用量、时间、问答和API实际返回推理；前十题已有分数，后十题评分指标待定。

批次脚本使用`--results 结果目录`，完成后自动汇出正式IFC、统一结果记录和压缩的实际返回推理。也可用`python -m scripts.ifc_repair.repair_comparison.results --root 工作目录 --output 结果目录`单独汇出。执行期间保留内部预算与恢复记录；终态后可将账本退役为只含费用及流式完成标记的检查点。它不能用于恢复任务或冒充结果权威。

## 后续批次如何启用

新批次的冻结入口增加`--d-web-access proxy`，运行时自动启动网页代理并给DSH注入以下环境变量；要同时启用搜索，另加`--d-web-search`。不需要手工修改宿主代理或新增凭据。

代理复用现有双网络网关，D仍在内部网络；模型和搜索通过`NO_PROXY`保持原路径。

```dotenv
HTTPS_PROXY=http://repair-gateway:8000
HTTP_PROXY=http://repair-gateway:8000
NO_PROXY=repair-gateway,localhost,127.0.0.1
```

代理模块位于`scripts/ifc_repair/repair_comparison/dsh/web_proxy.py`，支持HTTP读取和HTTPS隧道，仅允许公共地址的80／443端口；服务不发布宿主端口、不持有模型密钥。源IFC、私有材料和密钥挂载边界保持，复用已有镜像，无新增依赖。

网页选项写入新批次冻结配置和准入；旧批次默认不开启，不直接改已冻结批次。正式IFC调用仍需对应阶段准入。批次由脚本运行，完成或异常时再交给Codex处理。

最新问答的[结果与用量](../../../dataset/processed/experiments/repair-comparison/development/dsh-integration/result.json)和[实际返回推理](../../../dataset/processed/experiments/repair-comparison/development/dsh-integration/reasoning.jsonl.gz)保留在开发记录；正式IFC成绩见[当前实验表](../../../dataset/processed/experiments/repair-comparison/current/README.md)。本文件只维护D配置。旧未提交接线日志已精简，累计消耗与未知用量继续保留。
