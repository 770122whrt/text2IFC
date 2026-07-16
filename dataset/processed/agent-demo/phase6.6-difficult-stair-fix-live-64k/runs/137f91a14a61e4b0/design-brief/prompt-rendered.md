最高优先级输出协议

你的整个回答必须是一个裸 JSON 对象。第一个非空白字符必须是左花括号，最后一个非空白字符必须是右花括号。禁止输出任何反引号字符，禁止 Markdown 代码围栏，禁止标题、解释、前言、结语或第二个对象。该响应会被机器逐字检查；如果出现任何围栏或对象外文本，响应将被判定为失败，即使其中 JSON 本身正确。

发送前自检：
一、首个非空白字符是左花括号。
二、末个非空白字符是右花括号。
三、全文不含反引号字符。
四、全文只有一个满足所给 Schema 的 JSON 对象。

角色与边界

你是 text2IFC 的中文需求理解 Agent。你的职责是把用户原文和完整对话整理为可审计的 Design Brief 2.0。Design Brief 只表达用户意图、事实状态与追问，不是 BIM JSON，也不是 IFC。

本次输入

用户原始请求：
## 4.4.11 Difficult 修订输入：无穿墙楼梯与双洞口防护栏杆

创建一栋两层住宅。采用毫米和右手坐标系：X 轴向东，Y 轴向北，Z 轴向上。室内净轮廓为 `x=0..12000, y=0..8000`。

### 4.4.11.1 建筑与楼层

- 首层 `storey-1` 标高为 0，二层 `storey-2` 标高为 3300；
- 两层净高均为 3000；
- 所有普通墙厚 200、高 3000；
- 两层均使用连续的南、北、西、东四段外墙封闭外轮廓，转角直接相接；
- 首层和二层墙分别归属对应楼层，不得跨层或重复。

### 4.4.11.2 楼板和两个独立开口

生成两块 `IfcSlab`：

- `ground-floor-slab` 归属 `storey-1`，顶标高 0，厚 300，平面为 `[[0,0],[12000,0],[12000,8000],[0,8000],[0,0]]`；
- `first-floor-slab` 归属 `storey-2`，顶标高 3300，厚 300，平面同上。

`first-floor-slab` 必须有两个彼此独立的开口，不得合并：

- 中庭开口 `opening-first-floor-slab-atrium`：`x=6000..12000, y=0..3000`；
- 楼梯开口 `opening-first-floor-slab-stair`：`x=9900..11100, y=4000..7750`。

每个开口分别生成 `IfcOpeningElement` 和各自的 `IfcRelVoidsElement`。开口范围内不得生成楼板实体。

### 4.4.11.3 首层空间与楼梯通道

为以下每个矩形生成独立 `IfcSpace`：

- 客厅 `space-storey-1-living`：`x=0..7000, y=0..3000`；
- 餐厅 `space-storey-1-dining`：`x=7000..12000, y=0..3000`；
- 走廊 `space-storey-1-corridor`：`x=0..10000, y=3000..5000`；
- 厨房 `space-storey-1-kitchen`：`x=0..5000, y=5000..8000`；
- 卫生间 `space-storey-1-bathroom`：`x=5000..7000, y=5000..8000`；
- 楼梯厅 `space-storey-1-stair-hall`：`x=7000..12000, y=5000..8000`。

走廊与楼梯厅在 `y=5000` 的公共边界不得生成一段连续墙。只生成以下两段墙：

- `wall-stairhall-corridor-west-storey1`：从 `[7000,5000]` 到 `[9900,5000]`；
- `wall-stairhall-corridor-east-storey1`：从 `[11100,5000]` 到 `[12000,5000]`。

两段墙之间的 `x=9900..11100` 是宽 1200 的开放楼梯通道。该通道内不得生成墙、门、填充构件或其他封堵实体。相邻空间的其他公共边界各只生成一段共享墙。

### 4.4.11.4 二层空间、中庭和到达区

为以下每个矩形生成独立 `IfcSpace`：

- 走廊 `space-storey-2-corridor`：`x=0..9900, y=3000..5000`；
- 卧室一 `space-storey-2-bedroom-1`：`x=0..5000, y=5000..8000`；
- 卫生间 `space-storey-2-bathroom`：`x=5000..7000, y=5000..8000`；
- 卧室二 `space-storey-2-bedroom-2`：`x=7000..9900, y=5000..8000`；
- 卧室三 `space-storey-2-bedroom-3`：`x=0..6000, y=0..3000`。

中庭挑空范围为 `x=6000..12000, y=0..3000`。楼梯开口范围为 `x=9900..11100, y=4000..7750`。这两个区域均不得生成二层 `IfcSpace`。`x=9900..11100, y=3000..4000` 保留为二层楼梯到达区，必须保留楼板实体，不得被楼梯开口切除。中庭北边和西边不得生成普通封闭墙。

### 4.4.11.5 不穿墙的直跑楼梯

生成一部由 `IfcStair` 和一个 `IfcStairFlight` 组成的直跑楼梯，不使用双跑、平台或转折：

- `stair-1` 从 `storey-1` 连接到 `storey-2`；
- 平面 bounds 为 `x=10000..11000, y=4000..7750`；
- 起跑点为全局 `[11000,7750,0]`，沿 `-Y` 方向运行，梯段宽度向西展开 1000；
- 起点标高 0，终点标高 3300，总高差 3300；
- 18 个踢面、17 个踏面；
- 踢面高为 `3300/18` 毫米，踏面深为 `3750/17` 毫米，总水平投影长 3750 毫米；
- 楼梯必须完整位于楼梯开口平面范围内，并在东西两侧各保留 100 毫米净空；
- 楼梯北端到北外墙内表面至少保留 150 毫米净空；
- 楼梯不得与任何普通内墙或外墙产生正体积相交，必须从上述 1200 毫米开放通道穿过。

### 4.4.11.6 五段洞口防护栏杆

生成且只生成以下五段简化实体 `IfcRailing`，均归属 `storey-2`：

- `railing-atrium-north`：从 `[6000,3000,3300]` 到 `[12000,3000,3300]`；
- `railing-atrium-west`：从 `[6000,0,3300]` 到 `[6000,3000,3300]`；
- `railing-stair-opening-west`：从 `[9900,4000,3300]` 到 `[9900,7750,3300]`；
- `railing-stair-opening-east`：从 `[11100,4000,3300]` 到 `[11100,7750,3300]`；
- `railing-stair-opening-north`：从 `[9900,7750,3300]` 到 `[11100,7750,3300]`。

五段栏杆高度均为 1100，简化实体厚度均为 50，底标高均为 3300。前三条楼梯洞口边缘中，西、东、北边必须受防护；南边 `y=4000` 是楼梯到达口，必须保持开放，不得增加横向栏杆封堵。不得把栏杆改成普通墙，也不得自行增加立柱、材料或栏杆类型。本阶段不要求生成沿梯段倾斜的扶手。

### 4.4.11.7 门

所有普通室内门高 2100；卫生间门宽 800，其余室内门宽 900。门中心使用下列全局 XY 坐标：

- 首层客厅到走廊 `[3500,3000]`；
- 首层餐厅到走廊 `[8500,3000]`；
- 首层厨房到走廊 `[2500,5000]`；
- 首层卫生间到走廊 `[6000,5000]`；
- 首层楼梯厅到走廊 `[8500,5000]`，宿主必须为 `wall-stairhall-corridor-west-storey1`；
- 二层卧室一到走廊 `[2500,5000]`；
- 二层卫生间到走廊 `[6000,5000]`；
- 二层卧室二到走廊 `[8450,5000]`；
- 二层卧室三到走廊 `[3000,3000]`。

住宅主入口门位于首层西外墙，中心 `[0,4000]`，宽 1000、高 2100。每扇门分别生成自己的开口、`IfcRelVoidsElement` 和 `IfcRelFillsElement`，不得共用开口。

### 4.4.11.8 窗

普通窗宽 1500、高 1200、窗台高 900：

- 首层客厅南外墙中心 `[2333,0]` 和 `[4667,0]`；
- 首层餐厅南外墙中心 `[8250,0]` 和 `[10750,0]`；
- 首层厨房北外墙中心 `[2500,8000]`；
- 二层卧室一北外墙中心 `[2500,8000]`；
- 二层卧室二北外墙中心 `[8450,8000]`；
- 二层卧室三南外墙中心 `[3000,0]`。

两个卫生间各有一扇高窗，宽 800、高 600、窗台高 1600：首层中心 `[6000,8000]`，二层中心 `[6000,8000]`，分别宿主于对应楼层北外墙。每扇窗分别生成自己的开口和填充关系，同一宿主墙上的多个窗不得重叠。

### 4.4.11.9 IFC 验收要求

- BIM JSON 2.0 必须通过正式 Schema 校验后才编译；
- IFC2X3 必须可编译、可重开且无 EXPRESS 错误；
- 必须有 2 个 `IfcBuildingStorey`、11 个 `IfcSpace`、2 个 `IfcSlab`、1 个 `IfcStair`、1 个 `IfcStairFlight` 和 5 个 `IfcRailing`；
- 两个楼板开口必须独立存在且范围正确；
- 五段栏杆必须归属二层，并匹配明确中心线、1100 高度和 50 厚度；
- 楼梯与全部普通墙的正体积相交数量必须为 0；
- 楼梯必须通过 `x=9900..11100` 的开放通道，且不得进入北外墙；
- 中庭、楼梯开口和到达区不得互相合并或错误切除；
- 门窗必须位于指定中心、绑定正确宿主，并具有独立开口和填充关系；
- 共享墙不得重复，外墙转角不得留缝，所有构件必须归属正确楼层。

完整对话记录：
[{"content": "## 4.4.11 Difficult 修订输入：无穿墙楼梯与双洞口防护栏杆\n\n创建一栋两层住宅。采用毫米和右手坐标系：X 轴向东，Y 轴向北，Z 轴向上。室内净轮廓为 `x=0..12000, y=0..8000`。\n\n### 4.4.11.1 建筑与楼层\n\n- 首层 `storey-1` 标高为 0，二层 `storey-2` 标高为 3300；\n- 两层净高均为 3000；\n- 所有普通墙厚 200、高 3000；\n- 两层均使用连续的南、北、西、东四段外墙封闭外轮廓，转角直接相接；\n- 首层和二层墙分别归属对应楼层，不得跨层或重复。\n\n### 4.4.11.2 楼板和两个独立开口\n\n生成两块 `IfcSlab`：\n\n- `ground-floor-slab` 归属 `storey-1`，顶标高 0，厚 300，平面为 `[[0,0],[12000,0],[12000,8000],[0,8000],[0,0]]`；\n- `first-floor-slab` 归属 `storey-2`，顶标高 3300，厚 300，平面同上。\n\n`first-floor-slab` 必须有两个彼此独立的开口，不得合并：\n\n- 中庭开口 `opening-first-floor-slab-atrium`：`x=6000..12000, y=0..3000`；\n- 楼梯开口 `opening-first-floor-slab-stair`：`x=9900..11100, y=4000..7750`。\n\n每个开口分别生成 `IfcOpeningElement` 和各自的 `IfcRelVoidsElement`。开口范围内不得生成楼板实体。\n\n### 4.4.11.3 首层空间与楼梯通道\n\n为以下每个矩形生成独立 `IfcSpace`：\n\n- 客厅 `space-storey-1-living`：`x=0..7000, y=0..3000`；\n- 餐厅 `space-storey-1-dining`：`x=7000..12000, y=0..3000`；\n- 走廊 `space-storey-1-corridor`：`x=0..10000, y=3000..5000`；\n- 厨房 `space-storey-1-kitchen`：`x=0..5000, y=5000..8000`；\n- 卫生间 `space-storey-1-bathroom`：`x=5000..7000, y=5000..8000`；\n- 楼梯厅 `space-storey-1-stair-hall`：`x=7000..12000, y=5000..8000`。\n\n走廊与楼梯厅在 `y=5000` 的公共边界不得生成一段连续墙。只生成以下两段墙：\n\n- `wall-stairhall-corridor-west-storey1`：从 `[7000,5000]` 到 `[9900,5000]`；\n- `wall-stairhall-corridor-east-storey1`：从 `[11100,5000]` 到 `[12000,5000]`。\n\n两段墙之间的 `x=9900..11100` 是宽 1200 的开放楼梯通道。该通道内不得生成墙、门、填充构件或其他封堵实体。相邻空间的其他公共边界各只生成一段共享墙。\n\n### 4.4.11.4 二层空间、中庭和到达区\n\n为以下每个矩形生成独立 `IfcSpace`：\n\n- 走廊 `space-storey-2-corridor`：`x=0..9900, y=3000..5000`；\n- 卧室一 `space-storey-2-bedroom-1`：`x=0..5000, y=5000..8000`；\n- 卫生间 `space-storey-2-bathroom`：`x=5000..7000, y=5000..8000`；\n- 卧室二 `space-storey-2-bedroom-2`：`x=7000..9900, y=5000..8000`；\n- 卧室三 `space-storey-2-bedroom-3`：`x=0..6000, y=0..3000`。\n\n中庭挑空范围为 `x=6000..12000, y=0..3000`。楼梯开口范围为 `x=9900..11100, y=4000..7750`。这两个区域均不得生成二层 `IfcSpace`。`x=9900..11100, y=3000..4000` 保留为二层楼梯到达区，必须保留楼板实体，不得被楼梯开口切除。中庭北边和西边不得生成普通封闭墙。\n\n### 4.4.11.5 不穿墙的直跑楼梯\n\n生成一部由 `IfcStair` 和一个 `IfcStairFlight` 组成的直跑楼梯，不使用双跑、平台或转折：\n\n- `stair-1` 从 `storey-1` 连接到 `storey-2`；\n- 平面 bounds 为 `x=10000..11000, y=4000..7750`；\n- 起跑点为全局 `[11000,7750,0]`，沿 `-Y` 方向运行，梯段宽度向西展开 1000；\n- 起点标高 0，终点标高 3300，总高差 3300；\n- 18 个踢面、17 个踏面；\n- 踢面高为 `3300/18` 毫米，踏面深为 `3750/17` 毫米，总水平投影长 3750 毫米；\n- 楼梯必须完整位于楼梯开口平面范围内，并在东西两侧各保留 100 毫米净空；\n- 楼梯北端到北外墙内表面至少保留 150 毫米净空；\n- 楼梯不得与任何普通内墙或外墙产生正体积相交，必须从上述 1200 毫米开放通道穿过。\n\n### 4.4.11.6 五段洞口防护栏杆\n\n生成且只生成以下五段简化实体 `IfcRailing`，均归属 `storey-2`：\n\n- `railing-atrium-north`：从 `[6000,3000,3300]` 到 `[12000,3000,3300]`；\n- `railing-atrium-west`：从 `[6000,0,3300]` 到 `[6000,3000,3300]`；\n- `railing-stair-opening-west`：从 `[9900,4000,3300]` 到 `[9900,7750,3300]`；\n- `railing-stair-opening-east`：从 `[11100,4000,3300]` 到 `[11100,7750,3300]`；\n- `railing-stair-opening-north`：从 `[9900,7750,3300]` 到 `[11100,7750,3300]`。\n\n五段栏杆高度均为 1100，简化实体厚度均为 50，底标高均为 3300。前三条楼梯洞口边缘中，西、东、北边必须受防护；南边 `y=4000` 是楼梯到达口，必须保持开放，不得增加横向栏杆封堵。不得把栏杆改成普通墙，也不得自行增加立柱、材料或栏杆类型。本阶段不要求生成沿梯段倾斜的扶手。\n\n### 4.4.11.7 门\n\n所有普通室内门高 2100；卫生间门宽 800，其余室内门宽 900。门中心使用下列全局 XY 坐标：\n\n- 首层客厅到走廊 `[3500,3000]`；\n- 首层餐厅到走廊 `[8500,3000]`；\n- 首层厨房到走廊 `[2500,5000]`；\n- 首层卫生间到走廊 `[6000,5000]`；\n- 首层楼梯厅到走廊 `[8500,5000]`，宿主必须为 `wall-stairhall-corridor-west-storey1`；\n- 二层卧室一到走廊 `[2500,5000]`；\n- 二层卫生间到走廊 `[6000,5000]`；\n- 二层卧室二到走廊 `[8450,5000]`；\n- 二层卧室三到走廊 `[3000,3000]`。\n\n住宅主入口门位于首层西外墙，中心 `[0,4000]`，宽 1000、高 2100。每扇门分别生成自己的开口、`IfcRelVoidsElement` 和 `IfcRelFillsElement`，不得共用开口。\n\n### 4.4.11.8 窗\n\n普通窗宽 1500、高 1200、窗台高 900：\n\n- 首层客厅南外墙中心 `[2333,0]` 和 `[4667,0]`；\n- 首层餐厅南外墙中心 `[8250,0]` 和 `[10750,0]`；\n- 首层厨房北外墙中心 `[2500,8000]`；\n- 二层卧室一北外墙中心 `[2500,8000]`；\n- 二层卧室二北外墙中心 `[8450,8000]`；\n- 二层卧室三南外墙中心 `[3000,0]`。\n\n两个卫生间各有一扇高窗，宽 800、高 600、窗台高 1600：首层中心 `[6000,8000]`，二层中心 `[6000,8000]`，分别宿主于对应楼层北外墙。每扇窗分别生成自己的开口和填充关系，同一宿主墙上的多个窗不得重叠。\n\n### 4.4.11.9 IFC 验收要求\n\n- BIM JSON 2.0 必须通过正式 Schema 校验后才编译；\n- IFC2X3 必须可编译、可重开且无 EXPRESS 错误；\n- 必须有 2 个 `IfcBuildingStorey`、11 个 `IfcSpace`、2 个 `IfcSlab`、1 个 `IfcStair`、1 个 `IfcStairFlight` 和 5 个 `IfcRailing`；\n- 两个楼板开口必须独立存在且范围正确；\n- 五段栏杆必须归属二层，并匹配明确中心线、1100 高度和 50 厚度；\n- 楼梯与全部普通墙的正体积相交数量必须为 0；\n- 楼梯必须通过 `x=9900..11100` 的开放通道，且不得进入北外墙；\n- 中庭、楼梯开口和到达区不得互相合并或错误切除；\n- 门窗必须位于指定中心、绑定正确宿主，并具有独立开口和填充关系；\n- 共享墙不得重复，外墙转角不得留缝，所有构件必须归属正确楼层。", "question_ids": [], "role": "user", "turn_id": "turn-user-001"}]

Design Brief 2.0 完整输出 Schema：
{"$defs": {"ambiguity": {"additionalProperties": false, "properties": {"blocking": {"type": "boolean"}, "evidence_refs": {"$ref": "#/$defs/evidenceRefs"}, "id": {"$ref": "#/$defs/nonEmptyString"}, "message": {"$ref": "#/$defs/nonEmptyString"}, "options": {"items": {}, "minItems": 2, "type": "array"}, "path": {"$ref": "#/$defs/jsonPointer"}, "reason": {"$ref": "#/$defs/nonEmptyString"}, "source_turns": {"$ref": "#/$defs/stringList"}}, "required": ["id", "path", "message", "reason", "blocking", "evidence_refs", "source_turns", "options"], "type": "object"}, "correction": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/evidenceRefs"}, "path": {"$ref": "#/$defs/jsonPointer"}, "replaces": {}, "source_turn": {"$ref": "#/$defs/nonEmptyString"}, "value": {}}, "required": ["path", "value", "source_turn", "evidence_refs"], "type": "object"}, "evidenceRefs": {"items": {"$ref": "#/$defs/nonEmptyString"}, "minItems": 1, "type": "array", "uniqueItems": true}, "factSource": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/evidenceRefs"}, "path": {"$ref": "#/$defs/jsonPointer"}, "source_turns": {"$ref": "#/$defs/stringList"}}, "required": ["path", "source_turns", "evidence_refs"], "type": "object"}, "jsonPointer": {"pattern": "^/", "type": "string"}, "missingFact": {"additionalProperties": false, "properties": {"blocking": {"type": "boolean"}, "code": {"$ref": "#/$defs/nonEmptyString"}, "evidence_refs": {"$ref": "#/$defs/evidenceRefs"}, "id": {"$ref": "#/$defs/nonEmptyString"}, "message": {"$ref": "#/$defs/nonEmptyString"}, "path": {"$ref": "#/$defs/jsonPointer"}, "reason": {"$ref": "#/$defs/nonEmptyString"}, "source_turns": {"$ref": "#/$defs/stringList"}}, "required": ["id", "code", "path", "message", "reason", "blocking", "evidence_refs", "source_turns"], "type": "object"}, "nonEmptyString": {"minLength": 1, "type": "string"}, "provenance": {"additionalProperties": false, "properties": {"few_shot_ids": {"items": {"$ref": "#/$defs/nonEmptyString"}, "type": "array", "uniqueItems": true}, "selected_evidence_ids": {"items": {"$ref": "#/$defs/nonEmptyString"}, "type": "array", "uniqueItems": true}, "source_turns": {"$ref": "#/$defs/stringList"}}, "required": ["source_turns", "selected_evidence_ids", "few_shot_ids"], "type": "object"}, "question": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/evidenceRefs"}, "id": {"$ref": "#/$defs/nonEmptyString"}, "reason": {"$ref": "#/$defs/nonEmptyString"}, "targets": {"$ref": "#/$defs/stringList"}, "text": {"$ref": "#/$defs/nonEmptyString"}}, "required": ["id", "text", "targets", "reason", "evidence_refs"], "type": "object"}, "stringList": {"items": {"$ref": "#/$defs/nonEmptyString"}, "minItems": 1, "type": "array", "uniqueItems": true}, "unsupportedRequest": {"additionalProperties": false, "properties": {"blocking": {"type": "boolean"}, "evidence_refs": {"$ref": "#/$defs/evidenceRefs"}, "id": {"$ref": "#/$defs/nonEmptyString"}, "message": {"$ref": "#/$defs/nonEmptyString"}, "path": {"$ref": "#/$defs/jsonPointer"}, "reason": {"$ref": "#/$defs/nonEmptyString"}, "requested_value": {}, "source_turns": {"$ref": "#/$defs/stringList"}}, "required": ["id", "path", "message", "reason", "blocking", "requested_value", "evidence_refs", "source_turns"], "type": "object"}}, "$id": "https://text2ifc.local/schemas/agent/design-brief/2.0/schema.json", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "allOf": [{"if": {"properties": {"status": {"const": "needs_clarification"}}, "required": ["status"]}, "then": {"properties": {"clarification_questions": {"maxItems": 3, "minItems": 1}}}}, {"if": {"properties": {"status": {"const": "ready"}}, "required": ["status"]}, "then": {"properties": {"clarification_questions": {"maxItems": 0}}}}], "properties": {"ambiguities": {"items": {"$ref": "#/$defs/ambiguity"}, "type": "array"}, "clarification_questions": {"items": {"$ref": "#/$defs/question"}, "maxItems": 3, "type": "array"}, "fact_sources": {"items": {"$ref": "#/$defs/factSource"}, "type": "array"}, "known_facts": {"type": "object"}, "language": {"const": "zh-CN"}, "missing_facts": {"items": {"$ref": "#/$defs/missingFact"}, "type": "array"}, "original_request": {"minLength": 1, "type": "string"}, "provenance": {"$ref": "#/$defs/provenance"}, "schema_version": {"const": "text2ifc/design-brief/2.0"}, "status": {"enum": ["ready", "needs_clarification", "draft_required", "blocked"]}, "unsupported_requests": {"items": {"$ref": "#/$defs/unsupportedRequest"}, "type": "array"}, "user_corrections": {"items": {"$ref": "#/$defs/correction"}, "type": "array"}}, "required": ["schema_version", "language", "original_request", "status", "known_facts", "fact_sources", "missing_facts", "ambiguities", "unsupported_requests", "user_corrections", "clarification_questions", "provenance"], "title": "text2IFC Evidence-grounded Design Brief 2.0", "type": "object"}

本次选中的 BIM JSON Schema 与 IFC2X3 能力证据：
[{"content": {"$defs": {"attributes": {"properties": {"ObjectPlacement": {"$ref": "#/$defs/objectPlacement"}, "Representation": {"$ref": "#/$defs/representation"}}, "type": "object"}, "entity": {"additionalProperties": false, "properties": {"attributes": {"$ref": "#/$defs/attributes"}, "global_id": {}, "id": {"$ref": "#/$defs/nonEmptyString"}, "ifc_class": {"$ref": "#/$defs/nonEmptyString"}, "materials": {"items": {"$ref": "#/$defs/materialAssignment"}, "type": "array"}, "property_sets": {"additionalProperties": {"type": "object"}, "type": "object"}, "provenance": {"$ref": "#/$defs/provenance"}}, "required": ["id", "ifc_class", "attributes", "property_sets", "provenance"], "type": "object"}, "localPosition": {"additionalProperties": false, "properties": {"axis": {"$ref": "#/$defs/vector3"}, "origin": {"$ref": "#/$defs/vector3"}, "ref_direction": {"$ref": "#/$defs/vector3"}}, "required": ["origin", "axis", "ref_direction"], "type": "object"}, "materialAssignment": {"additionalProperties": false, "properties": {"direction": {"enum": ["AXIS1", "AXIS2", "AXIS3"]}, "direction_sense": {"enum": ["POSITIVE", "NEGATIVE"]}, "kind": {"const": "material_layer_set_usage"}, "layer_set_name": {"$ref": "#/$defs/nonEmptyString"}, "layers": {"items": {"$ref": "#/$defs/materialLayer"}, "minItems": 1, "type": "array"}, "offset_from_reference_line": {"type": "number"}}, "required": ["kind", "layer_set_name", "direction", "direction_sense", "offset_from_reference_line", "layers"], "type": "object"}, "materialLayer": {"additionalProperties": false, "properties": {"name": {"$ref": "#/$defs/nonEmptyString"}, "thickness": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["name", "thickness"], "type": "object"}, "nonEmptyString": {"minLength": 1, "type": "string"}, "objectPlacement": {"additionalProperties": false, "properties": {"axis": {"$ref": "#/$defs/vector3"}, "origin": {"$ref": "#/$defs/vector3"}, "ref_direction": {"$ref": "#/$defs/vector3"}, "relative_to": {"$ref": "#/$defs/nonEmptyString"}}, "required": ["relative_to", "origin", "axis", "ref_direction"], "type": "object"}, "point2": {"items": {"type": "number"}, "maxItems": 2, "minItems": 2, "type": "array"}, "profile": {"allOf": [{"if": {"properties": {"kind": {"const": "rectangle"}}, "required": ["kind"]}, "then": {"required": ["x", "y"]}}, {"if": {"properties": {"kind": {"const": "polygon"}}, "required": ["kind"]}, "then": {"required": ["points"]}}], "properties": {"kind": {"type": "string"}, "points": {"items": {"$ref": "#/$defs/point2"}, "type": "array"}, "x": {"type": "number"}, "y": {"type": "number"}}, "required": ["kind"], "type": "object"}, "provenance": {"minProperties": 1, "type": "object"}, "relationship": {"additionalProperties": false, "properties": {"attributes": {"type": "object"}, "global_id": {}, "id": {"$ref": "#/$defs/nonEmptyString"}, "ifc_class": {"$ref": "#/$defs/nonEmptyString"}, "provenance": {"$ref": "#/$defs/provenance"}}, "required": ["id", "ifc_class", "attributes", "provenance"], "type": "object"}, "representation": {"allOf": [{"if": {"properties": {"kind": {"const": "extruded_profile"}}, "required": ["kind"]}, "then": {"required": ["profile", "depth", "direction"]}}], "properties": {"depth": {"type": "number"}, "direction": {"$ref": "#/$defs/vector3"}, "kind": {"type": "string"}, "position": {"$ref": "#/$defs/localPosition"}, "profile": {"$ref": "#/$defs/profile"}}, "required": ["kind"], "type": "object"}, "units": {"additionalProperties": false, "properties": {"length": {"const": "MILLIMETRE"}}, "required": ["length"], "type": "object"}, "vector3": {"items": {"type": "number"}, "maxItems": 3, "minItems": 3, "type": "array"}}, "$id": "https://text2ifc.local/schemas/bim-json/2.0/schema.json", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"entities": {"items": {"$ref": "#/$defs/entity"}, "type": "array"}, "ifc_schema": {"const": "IFC2X3"}, "provenance": {"$ref": "#/$defs/provenance"}, "relationships": {"items": {"$ref": "#/$defs/relationship"}, "type": "array"}, "schema_version": {"const": "bim-json/2.0"}, "units": {"$ref": "#/$defs/units"}}, "required": ["schema_version", "ifc_schema", "units", "entities", "relationships", "provenance"], "title": "text2IFC BIM JSON 2.0", "type": "object"}, "evidence_id": "schema:bim-json-v2:root", "json_pointer": "/", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": {"additionalProperties": false, "properties": {"attributes": {"$ref": "#/$defs/attributes"}, "global_id": {}, "id": {"$ref": "#/$defs/nonEmptyString"}, "ifc_class": {"$ref": "#/$defs/nonEmptyString"}, "materials": {"items": {"$ref": "#/$defs/materialAssignment"}, "type": "array"}, "property_sets": {"additionalProperties": {"type": "object"}, "type": "object"}, "provenance": {"$ref": "#/$defs/provenance"}}, "required": ["id", "ifc_class", "attributes", "property_sets", "provenance"], "type": "object"}, "evidence_id": "schema:bim-json-v2:entity", "json_pointer": "/$defs/entity", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": {"properties": {"ObjectPlacement": {"$ref": "#/$defs/objectPlacement"}, "Representation": {"$ref": "#/$defs/representation"}}, "type": "object"}, "evidence_id": "schema:bim-json-v2:attributes", "json_pointer": "/$defs/attributes", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": {"allOf": [{"if": {"properties": {"kind": {"const": "extruded_profile"}}, "required": ["kind"]}, "then": {"required": ["profile", "depth", "direction"]}}], "properties": {"depth": {"type": "number"}, "direction": {"$ref": "#/$defs/vector3"}, "kind": {"type": "string"}, "position": {"$ref": "#/$defs/localPosition"}, "profile": {"$ref": "#/$defs/profile"}}, "required": ["kind"], "type": "object"}, "evidence_id": "schema:bim-json-v2:representation", "json_pointer": "/$defs/representation", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": {"allOf": [{"if": {"properties": {"kind": {"const": "rectangle"}}, "required": ["kind"]}, "then": {"required": ["x", "y"]}}, {"if": {"properties": {"kind": {"const": "polygon"}}, "required": ["kind"]}, "then": {"required": ["points"]}}], "properties": {"kind": {"type": "string"}, "points": {"items": {"$ref": "#/$defs/point2"}, "type": "array"}, "x": {"type": "number"}, "y": {"type": "number"}}, "required": ["kind"], "type": "object"}, "evidence_id": "schema:bim-json-v2:profile", "json_pointer": "/$defs/profile", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": {"additionalProperties": false, "properties": {"axis": {"$ref": "#/$defs/vector3"}, "origin": {"$ref": "#/$defs/vector3"}, "ref_direction": {"$ref": "#/$defs/vector3"}, "relative_to": {"$ref": "#/$defs/nonEmptyString"}}, "required": ["relative_to", "origin", "axis", "ref_direction"], "type": "object"}, "evidence_id": "schema:bim-json-v2:object-placement", "json_pointer": "/$defs/objectPlacement", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": {"additionalProperties": false, "properties": {"attributes": {"type": "object"}, "global_id": {}, "id": {"$ref": "#/$defs/nonEmptyString"}, "ifc_class": {"$ref": "#/$defs/nonEmptyString"}, "provenance": {"$ref": "#/$defs/provenance"}}, "required": ["id", "ifc_class", "attributes", "provenance"], "type": "object"}, "evidence_id": "schema:bim-json-v2:relationship", "json_pointer": "/$defs/relationship", "kind": "bim_json_schema", "source_path": "schemas/bim-json/2.0/schema.json", "source_sha256": "sha256:f80d438f84707c16c3d077d5190c8d49c7e40755b8e8b6cadd63973281fdb16f"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcBuilding", "json_pointer": "/entities/IfcBuilding", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcSpace", "json_pointer": "/entities/IfcSpace", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcWall", "json_pointer": "/entities/IfcWall", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcDoor", "json_pointer": "/entities/IfcDoor", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcWindow", "json_pointer": "/entities/IfcWindow", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcOpeningElement", "json_pointer": "/entities/IfcOpeningElement", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcBuildingStorey", "json_pointer": "/entities/IfcBuildingStorey", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcSlab", "json_pointer": "/entities/IfcSlab", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcColumn", "json_pointer": "/entities/IfcColumn", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcStair", "json_pointer": "/entities/IfcStair", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcRailing", "json_pointer": "/entities/IfcRailing", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcRelVoidsElement", "json_pointer": "/entities/IfcRelVoidsElement", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": "generate", "evidence_id": "capability:IFC2X3:IfcRelFillsElement", "json_pointer": "/entities/IfcRelFillsElement", "kind": "ifc_generation_capability", "source_path": "schemas/ifc/capabilities/IFC2X3.json", "source_sha256": "sha256:9b071f0a2ee21de04f834479aa22bfaf85df20ec4f73fbe8db79664fb5b8ba99"}, {"content": {"cross_checks": {"ifcopenshell_pset_adapter": {"property_sets": 317, "simple_property_templates": 1850}}, "generator_version": 1, "ifcopenshell_version": "0.8.5", "outputs": {"declarations.json": {"counts": {"declarations": 980, "entities": 653}, "sha256": "b822174bb9e5541e7f8d3703850b67e1010332ec92e611a992b235e523f9d4fa"}, "property_sets.json": {"counts": {"complex_properties": 6, "property_definitions": 1832, "property_sets": 317, "simple_properties": 1850}, "sha256": "d80fa90e4566d60f8cfa0cd5bd87e72c0074c97e56e13d680cee507acd9ff18e"}}, "schema": "IFC2X3", "source_manifest_sha256": "ea1de62ad5d7007cf8725e2414ac618c2d7e679f8221b9e83eedd864b0c047d9", "sources": {"ifc2x3-tc1-express": {"role": "structural-authority", "sha256": "e18a1b2c3e29f5256904c83378ccad0850f52287a8d0122d149aba4a417fe5e5", "url": "https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/EXPRESS/IFC2X3_TC1.exp"}, "ifc2x3-tc1-html-psd": {"role": "property-set-authority", "sha256": "ba22d66bc961b14a65d393e9a83672c17b646d7cdf2991a242f136b2e7849b6f", "url": "https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/IFC2x3_TC1_HTML_distribution-pset_errata.zip"}, "ifc2x3-tc1-xsd": {"role": "ifcxml-support", "sha256": "e49b60b94bd2ce6aed8486a55bd94e788180109283fb856805995f7a627d1e03", "url": "https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/XML/IFC2X3.xsd"}}}, "evidence_id": "registry:IFC2X3:manifest", "json_pointer": "/", "kind": "ifc_registry_manifest", "source_path": "schemas/ifc/generated/IFC2X3/registry-manifest.json", "source_sha256": "sha256:9b7f6b038235377b7dd451abaec2ab7410e83de25a59bb390ba15d811e2e8871"}]

命名 few-shot 条件推理示例：
[{"few_shot_id": "design-brief-v2.standard-two-storey-building", "input": {"conversation": [{"content": "创建一个两层测试建筑。首层标高0毫米，二层标高3150毫米，每层净高3000毫米，墙厚200毫米，楼板厚150毫米，屋面板厚150毫米。首层有客厅和楼梯间，二层有卧室和楼梯平台。每层都有独立外墙。首层南墙有门，二层南墙有窗，楼梯连接两层。", "role": "user", "turn_id": "turn-user-001"}], "user_request": "创建一个两层测试建筑。首层标高0毫米，二层标高3150毫米，每层净高3000毫米，墙厚200毫米，楼板厚150毫米，屋面板厚150毫米。首层有客厅和楼梯间，二层有卧室和楼梯平台。每层都有独立外墙。首层南墙有门，二层南墙有窗，楼梯连接两层。"}, "output": {"ambiguities": [], "clarification_questions": [], "fact_sources": [{"evidence_refs": ["schema:bim-json-v2:entity", "schema:bim-json-v2:representation", "capability:IFC2X3:IfcBuilding", "capability:IFC2X3:IfcBuildingStorey", "capability:IFC2X3:IfcSpace", "capability:IFC2X3:IfcWall", "capability:IFC2X3:IfcDoor", "capability:IFC2X3:IfcWindow", "capability:IFC2X3:IfcSlab", "capability:IFC2X3:IfcRoof", "capability:IFC2X3:IfcStair"], "path": "/known_facts", "source_turns": ["turn-user-001"]}], "known_facts": {"building": {"floor_slab_thickness_mm": 150, "roof_slab_thickness_mm": 150, "storey_count": 2, "wall_thickness_mm": 200}, "floor_slabs": [{"id": "ground-floor-slab", "storey": "storey-1", "thickness_mm": 150, "top_elevation_mm": 0}, {"id": "first-floor-slab", "storey": "storey-2", "thickness_mm": 150, "top_elevation_mm": 3150}], "roof_slab": {"bottom_elevation_mm": 6150, "id": "roof-slab", "thickness_mm": 150}, "stairs": [{"from_storey": "storey-1", "id": "stair-1", "semantic_requirement": "connects_two_storeys", "to_storey": "storey-2"}], "storeys": [{"doors": [{"host_wall": "storey-1-wall-south", "id": "door-storey-1-south", "location": "center"}], "elevation_mm": 0, "id": "storey-1", "name": "首层", "net_height_mm": 3000, "spaces": [{"id": "space-living", "location": "west", "name": "客厅"}, {"id": "space-stair-hall", "location": "east", "name": "楼梯间"}], "walls": {"exterior": [{"id": "storey-1-wall-south", "side": "south"}, {"id": "storey-1-wall-north", "side": "north"}, {"id": "storey-1-wall-west", "side": "west"}, {"id": "storey-1-wall-east", "side": "east"}]}, "windows": []}, {"doors": [], "elevation_mm": 3150, "id": "storey-2", "name": "二层", "net_height_mm": 3000, "spaces": [{"id": "space-bedroom", "location": "west", "name": "卧室"}, {"id": "space-stair-landing", "location": "east", "name": "楼梯平台"}], "walls": {"exterior": [{"id": "storey-2-wall-south", "side": "south"}, {"id": "storey-2-wall-north", "side": "north"}, {"id": "storey-2-wall-west", "side": "west"}, {"id": "storey-2-wall-east", "side": "east"}]}, "windows": [{"host_wall": "storey-2-wall-south", "id": "window-storey-2-south", "location": "center"}]}]}, "language": "zh-CN", "missing_facts": [], "original_request": "创建一个两层测试建筑。首层标高0毫米，二层标高3150毫米，每层净高3000毫米，墙厚200毫米，楼板厚150毫米，屋面板厚150毫米。首层有客厅和楼梯间，二层有卧室和楼梯平台。每层都有独立外墙。首层南墙有门，二层南墙有窗，楼梯连接两层。", "provenance": {"few_shot_ids": ["design-brief-v2.standard-two-storey-building"], "selected_evidence_ids": ["schema:bim-json-v2:entity", "schema:bim-json-v2:representation", "capability:IFC2X3:IfcBuilding", "capability:IFC2X3:IfcBuildingStorey", "capability:IFC2X3:IfcSpace", "capability:IFC2X3:IfcWall", "capability:IFC2X3:IfcDoor", "capability:IFC2X3:IfcWindow", "capability:IFC2X3:IfcSlab", "capability:IFC2X3:IfcRoof", "capability:IFC2X3:IfcStair"], "source_turns": ["turn-user-001"]}, "schema_version": "text2ifc/design-brief/2.0", "status": "ready", "unsupported_requests": [], "user_corrections": []}, "reasoning_summary": "多层请求应使用一个规范的 known_facts.storeys 数组承载各楼层事实。不要把楼层事实拆成顶层 storey_1/storey_2、spaces_ground/spaces_first，也不要把门窗合并成 generic openings；门窗应放入其宿主墙所在楼层。这里用户已经给出楼层标高、层高、墙厚、楼板和屋面板厚度、空间、门窗和楼梯语义，因此可以进入 ready。", "selection_terms": ["两层", "双层", "二层", "多层", "楼梯", "IfcStair", "storey", "two-storey"]}, {"few_shot_id": "design-brief-v2.complete-room-openings", "input": {"conversation": [{"content": "创建一个6米乘4米、高3米的矩形房间，墙厚300毫米；南墙中央有一扇0.9米乘2.1米的门，北墙中央有一扇1.2米乘1.5米、窗台高0.9米的窗。", "role": "user", "turn_id": "turn-user-001"}], "user_request": "创建一个6米乘4米、高3米的矩形房间，墙厚300毫米；南墙中央有一扇0.9米乘2.1米的门，北墙中央有一扇1.2米乘1.5米、窗台高0.9米的窗。"}, "output": {"ambiguities": [], "clarification_questions": [], "fact_sources": [{"evidence_refs": ["schema:bim-json-v2:entity", "schema:bim-json-v2:representation"], "path": "/known_facts", "source_turns": ["turn-user-001"]}], "known_facts": {"storeys": [{"doors": [{"alignment": "host_centerline", "height_mm": 2100, "host_wall": "wall-south", "id": "door-south", "width_mm": 900}], "elevation_mm": 0, "id": "storey-1", "net_height_mm": 3000, "spaces": [{"bounds": {"x": [0, 6000], "y": [0, 4000]}, "id": "space-room", "shape": "rectangle"}], "walls": {"exterior": [{"height_mm": 3000, "id": "wall-south", "side": "south", "thickness_mm": 300}, {"height_mm": 3000, "id": "wall-north", "side": "north", "thickness_mm": 300}, {"height_mm": 3000, "id": "wall-west", "side": "west", "thickness_mm": 300}, {"height_mm": 3000, "id": "wall-east", "side": "east", "thickness_mm": 300}], "interior": []}, "windows": [{"alignment": "host_centerline", "height_mm": 1500, "host_wall": "wall-north", "id": "window-north", "sill_height_mm": 900, "width_mm": 1200}]}]}, "language": "zh-CN", "missing_facts": [], "original_request": "创建一个6米乘4米、高3米的矩形房间，墙厚300毫米；南墙中央有一扇0.9米乘2.1米的门，北墙中央有一扇1.2米乘1.5米、窗台高0.9米的窗。", "provenance": {"few_shot_ids": ["design-brief-v2.complete-room-openings"], "selected_evidence_ids": ["schema:bim-json-v2:entity", "schema:bim-json-v2:representation", "capability:IFC2X3:IfcSpace", "capability:IFC2X3:IfcWall", "capability:IFC2X3:IfcDoor", "capability:IFC2X3:IfcWindow"], "source_turns": ["turn-user-001"]}, "schema_version": "text2ifc/design-brief/2.0", "status": "ready", "unsupported_requests": [], "user_corrections": []}, "reasoning_summary": "当前请求已给出所要求构件的尺寸、宿主和局部位置。用户没有要求地理定向、门开启方向或窗扇机构；能力与 Schema 证据也不要求这些未请求语义才能表达当前模型，因此不追问。这里的“中央”按普通建筑语言表示构件中心线与宿主墙中心线对齐，不凭空增加距离。", "selection_terms": ["房间", "墙", "门", "窗", "中央", "厚度", "南墙", "北墙"]}, {"few_shot_id": "design-brief-v2.linear-railings", "input": {"conversation": [{"content": "二层中庭北边和西边各设一段直线栏杆。北栏杆从(6000,3000,3300)到(12000,3000,3300)，西栏杆从(6000,0,3300)到(6000,3000,3300)，栏杆高1100毫米，简化实体厚50毫米。", "role": "user", "turn_id": "turn-user-001"}], "user_request": "二层中庭北边和西边各设一段直线栏杆。北栏杆从(6000,3000,3300)到(12000,3000,3300)，西栏杆从(6000,0,3300)到(6000,3000,3300)，栏杆高1100毫米，简化实体厚50毫米。"}, "output": {"ambiguities": [], "clarification_questions": [], "fact_sources": [{"evidence_refs": ["schema:bim-json-v2:entity", "schema:bim-json-v2:representation", "capability:IFC2X3:IfcRailing"], "path": "/known_facts/railings", "source_turns": ["turn-user-001"]}], "known_facts": {"railings": [{"alignment_target": "void-atrium:north-edge", "end_mm": [12000, 3000, 3300], "height_mm": 1100, "id": "railing-atrium-north", "start_mm": [6000, 3000, 3300], "storey": "storey-2", "thickness_mm": 50}, {"alignment_target": "void-atrium:west-edge", "end_mm": [6000, 3000, 3300], "height_mm": 1100, "id": "railing-atrium-west", "start_mm": [6000, 0, 3300], "storey": "storey-2", "thickness_mm": 50}], "storeys": [{"elevation_mm": 0, "id": "storey-1"}, {"elevation_mm": 3300, "id": "storey-2"}]}, "language": "zh-CN", "missing_facts": [], "original_request": "二层中庭北边和西边各设一段直线栏杆。北栏杆从(6000,3000,3300)到(12000,3000,3300)，西栏杆从(6000,0,3300)到(6000,3000,3300)，栏杆高1100毫米，简化实体厚50毫米。", "provenance": {"few_shot_ids": ["design-brief-v2.linear-railings"], "selected_evidence_ids": ["schema:bim-json-v2:entity", "schema:bim-json-v2:representation", "capability:IFC2X3:IfcRailing"], "source_turns": ["turn-user-001"]}, "schema_version": "text2ifc/design-brief/2.0", "status": "ready", "unsupported_requests": [], "user_corrections": []}, "reasoning_summary": "栏杆的楼层、三维中心线端点、高度和简化实体厚度均为用户显式事实，可以保留为顶层 known_facts.railings，不需要让用户编写 ObjectPlacement 或 Representation。", "selection_terms": ["栏杆", "护栏", "中庭", "railing", "guardrail", "start_mm", "end_mm"]}]

动态判断原则

一、逐条保留用户明确说出的事实、否定、未知回答和修正，并让 source_turns 指向真实对话轮次。

二、不要维护固定的项目字段清单。某个未提供事实只有在当前用户明确要求的对象或关系无法依据本次 Schema 与能力证据表达时，才可标记为 blocking。

三、每个 missing_facts、ambiguities、unsupported_requests 和 clarification_questions 项都必须说明当前请求下的 reason；evidence_refs 只能引用本次 EVIDENCE_CATALOG 中真实存在的 evidence_id。

四、用户没有要求、当前生成也不需要的细节，不要因为 IFC 中存在相应概念就追问。few-shot 是条件推理示例，不是默认模板。

五、用户明确要求但能力证据表明不能保真生成的语义，必须保留到 unsupported_requests 并选择 draft_required；禁止丢弃或改写成更简单的对象。

六、不能从已有事实推出的尺寸、位置、方向、楼层、空间、洞口、关系或属性，禁止猜测或采用行业默认值。

七、ready 表示没有 blocking item；needs_clarification 表示存在可由用户回答的 blocker；draft_required 表示用户不知道关键事实或明确语义无法保真生成；blocked 只用于输入证据自身矛盾且无法继续分析。

八、只有你负责撰写用户问题。needs_clarification 时提出一至三个中文关键问题，每个问题通过 targets 指向一个或多个 blocking item；其他状态不得制造无关追问。

九、用户已经回答不知道、暂时不清楚、无法提供，或等价表达某个当前 blocking fact 不可由本轮用户补齐时，必须把该事实保留为 missing_facts 并选择 draft_required；不得继续追问同一个事实，也不得为了通过 Formal 而补默认值。

禁止输出内容

不得输出 BIM JSON 的 entities 或 relationships，不得输出 raw IFC、STEP 文本、STEP ID、IfcCartesianPoint、IfcDirection、IfcOwnerHistory、编译器内部对象、Schema 未声明字段或自创版本号。

最终输出检查

现在只返回一个满足 text2ifc/design-brief/2.0 Schema 的裸 JSON 对象。不要使用 Markdown。不要输出任何反引号字符。不要在对象前后添加任何文字。发送前再次确认首字符是左花括号、末字符是右花括号。

Canonical Design Brief storey structure

1. For every building, including a single-storey building, put floor-local facts inside `known_facts.storeys`, an array of storey objects, except `floor_slabs`, `roof_slab`, and cross-storey `stairs`, which use their dedicated top-level collections under `known_facts`. A single-storey building still has exactly one item in this array. Each storey object should include stable `id`, `name` when available, `elevation_mm`, `net_height_mm`, and floor-local `spaces`, `walls`, `doors`, and `windows` when those facts are present. Each storey `walls` value must use exactly `walls: {exterior: [...], interior: [...]}`. Do not emit sibling `exterior_walls` or `interior_walls` keys. Preserve every wall record inside the matching group.
2. Use `elevation_mm`; do not use `level` as a substitute for elevation. If the user says first floor elevation is 0 mm and second floor elevation is 3150 mm, write `"elevation_mm": 0` and `"elevation_mm": 3150`.
3. Do not create singular top-level `storey`, `space`, `door`, or `window` keys. Do not create top-level `storey_1`, `storey_2`, `spaces_ground`, `spaces_first`, or generic `openings` as the primary structure. These scattered dialects make downstream verification ambiguous. Always use the canonical nested `storeys` array, even for one storey.
4. Put doors and windows inside the storey that owns their host wall. Use exactly `host_wall` for the explicit host-wall id. Do not emit `host_wall_id`, `host`, or `wall` as substitute keys. Do not merge doors and windows into a generic `openings` list. A second-storey window on a second-storey south wall belongs under the second storey and should name a second-storey host wall.
5. Use stable semantic ids in Design Brief facts when the user request is clear, for example `storey-1`, `storey-2`, `storey-1-wall-south`, and `storey-2-wall-south`. These are semantic ids for later BIM JSON generation, not IFC STEP ids.
6. If the request has enough facts for a canonical nested multi-storey Design Brief, return `ready`; do not invent missing dimensions, and do not ask about details that are not required by the requested supported model.
7. Use `known_facts.floor_slabs` when the user explicitly requests or locates floor slabs. Each slab record must preserve a stable `id`, owning `storey`, `top_elevation_mm`, and `thickness_mm`. Use `opening.bounds` for one confirmed opening. Use `openings` as an array when a slab has more than one confirmed opening; preserve a stable opening `id` and `bounds` on every item. Do not merge separate opening rectangles into one union rectangle. Never put `floor_slabs` or `floor_thickness_mm` inside a storey object.
8. Use one `known_facts.roof_slab` object when the user explicitly requests a roof slab. Preserve a stable `id`, `bottom_elevation_mm`, and `thickness_mm`; do not store the global bottom elevation as a storey-local coordinate.
9. Keep confirmed stair geometry in `known_facts.stairs`: stable `id`, `from_storey`, `to_storey`, plan bounds under the literal key `bounds`, not `plan_bounds`, plus `opening_bounds`, `start_elevation_mm`, `end_elevation_mm`, width, run direction, `number_of_risers`, `number_of_treads`, `riser_height_mm`, and `tread_depth_mm` when those facts were supplied. Riser count and tread count are distinct facts; never replace one with the other.
9a. Use `known_facts.railings` for confirmed straight, storey-local guard segments. Each record must preserve a stable `id`, owning `storey`, `start_mm: [x, y, z]`, `end_mm: [x, y, z]`, `height_mm`, and simplified solid `thickness_mm`. Preserve an explicit `alignment_target` when supplied. Do not invent railing endpoints, elevation, height, or thickness. Do not infer posts, balusters, materials, types, or curved paths from the word "railing" alone.
10. Do not collapse explicit slab instances into thickness-only building metadata. `building.floor_slab_thickness_mm` and `building.roof_slab_thickness_mm` may summarize repeated thickness, but they do not replace `floor_slabs` or `roof_slab` records.
11. When the user gives a rectangular global building outline, prefer `building.outline` with numeric `x_min`, `x_max`, `y_min`, and `y_max`. Preserve legacy text bounds only when the source itself is not safely separable into those four confirmed coordinates.
12. When the user gives axis-aligned wall centerline segments, preserve each segment as its own wall record with stable `id`, owning `storey`, numeric `start_mm: [x, y]`, numeric `end_mm: [x, y]`, `thickness_mm`, and `height_mm`. A 90-degree L turn is two independent straight wall records sharing one endpoint, not a single bent or polyline wall. Do not merge adjacent segments or change their order or coordinates.
13. For every confirmed axis-aligned plan rectangle, use exactly `bounds: {"x": [x_min, x_max], "y": [y_min, y_max]}` with millimetre values. Use this shape for spaces, stairs, and slab openings when their bounds were supplied.
14. Use the literal key `polygon` for slab, roof, and building outline point lists. Each point is `[x, y]` in millimetres and a closed polygon repeats its first point as its last point.
15. Use the literal key `connects` for the two space ids of an interior wall. The ids must exactly match space ids in the same storey.
16. Do not emit `bounds_mm`, `polygon_mm`, `connecting_spaces`, or string bounds such as `x=0..4000`. These are non-canonical geometry dialects and make deterministic verification impossible.

Layout fact preservation and conflict handling

1. Do not replace explicit coordinates, bounding rectangles, host-wall ids,
   opening centers, elevations, or stair-opening extents with a derived,
   rounded, relative, or approximate fact. Preserve the explicit value and its
   source turn in `known_facts`.
2. Before returning `ready`, compare every same-storey explicit space rectangle.
   A positive-area intersection is a blocking layout conflict. Record
   `LAYOUT_SPACE_OVERLAP` in the blocking item's reason, do not choose a new
   rectangle, and ask the user to resolve it when that is possible.
3. Before returning `ready`, verify that each explicitly located door or window
   has a host wall on the same storey. For an interior door, its stated center
   must lie on a positive-length shared boundary segment of the named spaces.
   If not, record `DOOR_HOST_NO_SHARED_SEGMENT` in a blocking item's reason;
   do not move the door or substitute another wall.
4. Before returning `ready`, verify that an explicit stair opening does not
   positively overlap an explicitly declared same-storey IfcSpace. If it does,
   record `STAIR_OPENING_SPACE_COLLISION` in a blocking item's reason; do not
   silently delete the opening, stair, or space.
5. Do not assign `host_centerline` to multiple openings on the same host wall.
   If each opening is centered on a different room bay, either split the wall into explicit touching segments and give each opening its own host, or use `center_global_mm` and omit `alignment`. Never emit mutually impossible centerline facts.
6. Use `needs_clarification` for a layout conflict the user can resolve. Use
   `draft_required` only after the user cannot or will not supply the required
   correction. A conflicting layout must never be reported as `ready`.

Schema consistency self-check

1. needs_clarification MUST include 1-3 clarification_questions; never return needs_clarification with an empty clarification_questions array.
2. Every clarification question target MUST reference an existing blocking item id from `missing_facts`, `ambiguities`, or `unsupported_requests`.
3. Do not target a non-blocking item. If an item is not blocking, it may remain recorded, but it must not be the reason for `needs_clarification`.
4. Optional or not-yet-decided items must not consume a clarification question slot unless they block faithful generation of the current requested model. If you ask about an ambiguity, that ambiguity MUST be marked blocking: true; if it remains blocking: false, do not include it in any question targets.
5. Prioritize blocking geometry facts before optional openings or style choices. For example, if height, wall thickness, and floor thickness are missing, ask those before asking whether optional doors/windows should be added.
6. Initial user phrases like not decided or not thought through yet are not the same as an answered unknown. On the first turn, if the fact is user-answerable, use `needs_clarification`; reserve `draft_required` for facts the user already answered as unknown/unimportant/unavailable or for unsupported semantics that cannot be faithfully generated.
7. draft_required and blocked MUST have an empty clarification_questions array. If you still have questions to ask, the status MUST be `needs_clarification`, not `draft_required` or `blocked`.
8. original_request MUST exactly equal CONVERSATION[0].content, including punctuation, typos, trailing symbols, and unusual characters. Never normalize, clean, summarize, translate, or append later answers to original_request.
9. Bind short numeric answers to the immediately preceding assistant question when the transcript makes the target clear. For example, if the assistant asked only for wall thickness and the user answers `300mm`, record it as wall thickness instead of creating a new ambiguity.
10. source_turns MUST use exact turn_id values already present in CONVERSATION. Never renumber a turn, invent a turn id, or change an assistant turn_id into a user turn_id.
11. Every missing_facts and unsupported_requests items MUST include a non-empty `code` string. Use a stable uppercase snake-case code such as `ROOM_DIMENSION_REFERENCE_MISSING`; do not omit `code` when those items have id/path/message/reason.
12. ambiguities items MUST NOT include `code`; the Design Brief 2.0 schema does not allow that field there. Use id/path/message/reason/blocking/evidence_refs/source_turns to describe ambiguity records.
13. Before sending, verify these invariants: `ready` has no blocking item and no questions; `needs_clarification` has at least one blocking item and 1-3 target-valid questions; `draft_required` has no clarification questions and no repeated question for a fact the user said they do not know; every blocking missing_facts or unsupported_requests item has id, code, path, message, reason, blocking, evidence_refs, and source_turns; every blocking ambiguities item has id, path, message, reason, blocking, evidence_refs, and source_turns, and no code field.
