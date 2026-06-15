# Mimo BIM JSON Prompt Iterations

这个文件记录 Mimo provider 的真实测试反馈和 prompt 版本变化。不要在这里写入 token、完整私有 URL、请求头值或任何密钥。

## mimo-bim-json-v3.md

Date: 2026-06-15

Goal: add a geometry gate contract after the simple-room IFC reopened but failed
spatial inspection in a viewer.

Observed failure:
- The IFC file contained four IfcWall objects and passed basic reopen checks.
- East/west walls were generated with the same local direction as south/north
  walls, so the room was visually disconnected.
- The model treated wall placement as a wall start or corner, while the IFC
  rectangle profile uses rectangle profile center-origin semantics.

New contract:
- `mimo-bim-json-v3.md` records the geometry gate rule.
- south/north walls run along X.
- east/west walls run along Y and normally use `ref_direction: [0, 1, 0]`.
- rectangle profile center-origin is explicit.
- geometry failure feedback must be repaired, or the response must remain Draft
  with Chinese clarification questions.
- The model must still output BIM JSON 2.0 only, not raw IFC or compiler-level
  objects.

## mimo-smoke-001

日期：2026-06-15

目标：验证 `.env` 中的 Mimo 配置是否能完成一次请求和回复。

结果：

- `.env` 中存在 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`、`TEXT2IFC_MIMO_MODEL`。
- 配置检查通过，模型名来自环境变量。
- 使用 `x-api-key` 方向可以获得 HTTP 200。
- 使用 Bearer 授权方向失败，后续 provider 继续使用 `x-api-key`。
- 低 `max_tokens` 时回复可能只包含 thinking 内容，没有可用 text。
- 增加 token 预算后，可以成功请求并获得文本回复。

结论：Mimo 可以连通并往返，但真实输出需要更强的输出合同约束。

## mimo-live-simple-room-001

日期：2026-06-15

目标：用中文自然语言描述一个简单房间，让 Mimo 生成 BIM JSON 2.0，再进入 IFC 编译链路。

输入摘要：

- 一个 6m x 4m x 3m 的单层矩形房间。
- 四面墙。
- 南墙一个 900mm x 2100mm 门。
- 北墙一个 1200mm x 1500mm 窗，窗台高 900mm。

结果：

- Mimo 返回 HTTP 200，说明请求往返成功。
- 返回内容是中文解释和分析，不是只输出一个 JSON 对象。
- 自动解析器从正文中抓到了普通尺寸 JSON：`{"length": "MILLIMETRE"}`。
- 校验结果是 validation failed，因为缺少 `schema_version`、`ifc_schema`、`entities`、`relationships`、`provenance` 等 Formal BIM JSON 必需字段。

问题判断：

- 模型把任务理解成“评价或说明参考 JSON”，而不是“生成唯一可校验 JSON”。
- prompt 没有足够强地禁止解释文本、Markdown 和片段 JSON。
- prompt 没有把失败反馈作为下一轮修复输入。

下一版合同：

- 新增 `mimo-bim-json-v1.md`。
- 强制“只输出一个完整 JSON 对象”。
- 明确根字段、实体字段、关系字段和 BIM JSON 2.0 / IFC2X3 固定值。
- 明确不要输出 IFC、STEP、`IfcCartesianPoint`、`IfcDirection`、`IfcOwnerHistory` 或 STEP ID。
- 明确 `REFERENCE_JSON` 只是结构参考。
- 明确 `VALIDATION_FEEDBACK` 必须被用于修复上一轮失败。
- 保留 prompt 版本和每轮失败原因，避免后续调参丢失上下文。

## mimo-live-simple-room-v1

日期：2026-06-15

目标：使用 `mimo-bim-json-v1.md`，再次让 Mimo 根据完整中文房间描述生成 BIM JSON 2.0，并尝试进入 IFC 编译。

结果：

- Mimo 返回 HTTP 200。
- 输出已经可以被 JSON 解析，不再是解释文本。
- BIM JSON 2.0 校验仍然失败。
- 失败点：根对象混入 `missing_facts` 和 `clarification_targets`，但同时又使用 `schema_version: "bim-json/2.0"`。
- 失败点：`entities` 为空，无法表达房间、墙、门、窗、洞口和关系。
- 搜索标记：entities 为空。
- 编译未尝试，因为 Formal BIM JSON 校验未通过。

问题判断：

- v1 成功约束了“只输出 JSON”，但没有阻止模型把完整输入误判成 Draft。
- `VALIDATION_FEEDBACK` 里的上一轮缺失信息被模型当成真实缺失继续沿用。
- 模型没有把“南墙中间”“北墙中间”“底部贴地”“窗台高”识别为足够的位置事实。

下一版合同：

- 新增 `mimo-bim-json-v2.md`。
- 明确信息足够时不要输出 Draft 字段。
- 明确 `entities` 不得为空。
- 明确 `missing_facts` 和 `clarification_targets` 不能混入 Formal BIM JSON 根对象。
- 明确“南墙中间”“北墙中间”等中文位置表达已经足够，可以计算居中洞口位置。
- 明确上一轮 validation feedback 只用于修复格式和字段错误，不代表用户真实缺失信息。

## mimo-live-simple-room-v2

日期：2026-06-15

目标：使用 `mimo-bim-json-v2.md`，要求 Mimo 对完整中文房间描述输出 Formal BIM JSON 2.0，并完成 JSON -> IFC 编译。

结果：

- HTTP 往返成功。
- `parse_status: ok`
- `validation_issue_count: 0`
- `compile_success: true`
- 输出 IFC：`dataset/processed/agent-demo/mimo-live-simple-room-v2/output.ifc`
- 重新打开 IFC 成功。
- BIM JSON 统计：13 个 entities，4 个 relationships。
- IFC 统计：4 个 `IfcWall`，1 个 `IfcDoor`，1 个 `IfcWindow`，1 个 `IfcSpace`。
- Agent artifact secret scan 结果：0 findings。

结论：

- v2 prompt 可以把这个简单中文完整输入稳定推进到 text -> BIM JSON 2.0 -> IFC。
- 当前成功仍是 simple-room 级别，不代表已经覆盖 BIMNet 复杂场景。
- 下一步应该把这条 live 路径固化为可复用脚本或受控 smoke test，并继续扩展到多轮 Draft 补全输入。
