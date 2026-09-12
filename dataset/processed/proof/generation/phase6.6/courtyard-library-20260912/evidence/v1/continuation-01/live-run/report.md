# Phase 6.1 Live Mimo Run Report

Generated from trace sidecars. This report is not hand-authored evidence.

## Original Input

```text
请建一座两层的光庭阅读馆，采用完整围合的矩形建筑，中间是露天光庭，二层有连续的围庭回廊。建筑要安静、明亮、有秩序：浅暖灰主体、深灰细窗框、通透的玻璃栏板、少量木色门扇。请建真实的建筑本体，不建花草、家具、文字招牌、设备和复杂五金。下面是我委托设计后确认采用的方案参数，不需要再询问风格、尺寸和布置；若参数相互矛盾或系统确实不能表达，请指出，不要擅自修改。

以外轮廓西南角为原点，东为X正向，北为Y正向，向上为Z正向，以下平面距离单位为米，IFC采用毫米。外轮廓东西24米、南北18米。露天光庭的平面范围为X=8到16、Y=6到12，8米乘6米；从首层地面向天空敞开，二层楼板和屋盖在这里真实开洞，不能只画线、藏板或拿玻璃封顶。首层地面在光庭范围保留。

首层和二层完成面标高为0和3.6米。两层墙高均3.4米。首层楼板底面-0.2米、顶面0米，二层楼板底面3.4米、顶面3.6米；两块板厚200毫米，外轮廓24乘18米。平屋盖底面7米、顶面7.2米，外轮廓同建筑，厚200毫米，光庭洞口与二层的8乘6米洞口对齐。本例屋盖明确用屋面用途的IfcSlab表达，作为一块独立带洞的板，不要求额外IfcRoof容器，也不要重复建两块屋盖。三块板均归属对应的建筑楼层，屋盖归属二层，不另建第三层。二层楼板另有下述楼梯洞口。

每层外墙厚240毫米、全部在建筑外轮廓内。南北外墙各贯通24米，实体Y范围分别0到0.24、17.76到18；东西外墙实体X范围分别0到0.24、23.76到24，Y范围0.24到17.76，四角只相接不相互重叠。

每层阅读房间与围庭交通区之间设四条厚240毫米的分隔墙。南侧分隔墙X=0.24到23.76、Y=3.74到3.98；北侧X相同、Y=14.02到14.26；西侧分隔墙X=5.74到5.98、Y=3.98到14.02；东侧X=18.02到18.26、Y=3.98到14.02。墙端对接，不能重复堆叠。光庭与回廊之间不设通高墙或玻璃幕墙，回廊是有顶半室外空间。屋盖覆盖回廊和房间，只有光庭露天。

每层明确设四个室内功能空间和四段半室外回廊空间，各空间高3.4米：南侧接待与交流区净范围X=0.24到23.76、Y=0.24到3.74；北侧安静阅读区X=0.24到23.76、Y=14.26到17.76；东侧共享阅读区X=18.26到23.76、Y=3.98到14.02；西侧服务与楼梯区X=0.24到5.74、Y=3.98到14.02。南回廊X=5.98到18.02、Y=3.98到6；北回廊X=5.98到18.02、Y=12到14.02；西回廊X=5.98到8、Y=6到12；东回廊X=16到18.02、Y=6到12。回廊四段相连且互不正面积重叠，光庭本身不创建跨层室内空间。西侧空间是包含楼梯的功能区，不能将空间包围楼梯洞口本身误报为实体碰撞。

楼梯位于西侧区内：一条从南向北上升的直跑楼梯连接首层0米与二层3.6米，净宽1.5米，平面X=1到2.5、Y=5到11，共20级，每级180毫米高，水平踏步进深300毫米。二层洞口平面X=1到2.5、Y=5到11，穿透200毫米板。下端候梯区Y=3.98到5，上端平台Y=11到12.6，利用既有楼板，不叠加平台板。梯段两侧设置实体围护墙：X=0.76到1及X=2.5到2.74，Y=3.98到12.6，每层墙高3.4米。首层在东侧楼梯围护墙设宽900毫米、高2100毫米右单开门，中心Y=4.5米；二层在同侧墙设同尺寸左单开门，中心Y=11.8米。门洞距墙端的实心墙至少50毫米，开启方向朝楼梯间外的服务区，不占梯段。楼梯上端可从平台出门经西侧服务区进入回廊。斜向抓握扶手不是本次已实现细节，不要虚构；报告中明确这项限制。

二层回廊靠光庭一侧设四块连续透明玻璃栏板，高1100毫米、厚20毫米，底部在完成面3.6米。南栏板X=7.98到16.02、Y=5.98到6；北栏板X相同、Y=12到12.02；西栏板X=7.98到8、Y=6到12；东栏板X=16到16.02、Y=6到12。四角实体边界相接不重叠，板落在楼板侧。回廊通行带从分隔墙内表面量至栏板通行侧表面，至少2米。玻璃栏板分别为IfcRailing，不做一块横跨光庭的板，不增加立柱和扶手假细节。

各层南、北侧分隔墙各两扇宽1000毫米、高2400毫米的基本单开木门，中心X=7和17米；两侧各自西门左单开、东门右单开。东西侧分隔墙各一扇同尺寸右单开门，中心Y=9米。门底与本层完成面齐平，门扇朝房间一侧开启。首层南外墙另设一扇宽1400毫米、高2600毫米左单开入口门，中心X=12米，二层不复制入口。加上楼梯间两扇门，总计15扇门。每扇门有自己独立的开口、宿主、基本门框和门扇，不使用双扇或推拉门模板。

每层南、北外墙各四扇双竖面板窗，中心X=3、8、16、21米；东外墙两扇双竖面板窗，中心Y=6.5、11.5米；西外墙两扇单面板窗，中心Y=2和16米。双面板窗宽2000毫米、高2400毫米，窗台高600毫米；单面板窗宽1000毫米、高1800毫米，窗台高1200毫米。每层南、北分隔墙各两扇双竖面板窗，中心X=10和14米；东分隔墙两扇、西分隔墙两扇双竖面板窗，中心Y=6.5和11.5米，这八扇内侧窗宽1600毫米、高2100毫米、窗台高900毫米。每层共20窗，总计40窗。窗头均距本层完成面3米，上下层同轴对齐；窗、洞口和宿主墙一一对应，框和玻璃有部件分色。

外墙、分隔墙和楼梯围护墙均采用20毫米砂浆、200毫米混凝土、20毫米砂浆的三层材料，厚度总计240毫米。三块水平板均为180毫米混凝土加20毫米砂浆面层，总厚200毫米。门整体材料为木材；栏板整体材料为玻璃。窗采用基本窗模板的框与玻璃部件样式，不将整窗谎称为纯铝或纯玻璃，也不要求当前合同不能表达的逐部件物理材料附件。

整体现有warm-residential风格，墙面颜色#D8D4CA、窗框和门框#333D40、木门扇#A87950；玻璃保持透明，栏板透明度0.75。板面为浅暖灰，与主体协调。相同用途、相同规格和相同开启方向的门窗明确共享本项目内Type/Style；两组不同宽度的双面板窗不得错误共享同一规格；楼梯围护门与普通房门、入口门分别组织，南北两块同规格栏板可共享，东西两块同规格栏板可共享。不同墙长不强制共享类型。实际Type只在本模型中创建，不引入外部资产。

本例先完成以上完整建筑，不额外添加没有明确位置的梁柱、雨篷、幕墙和饰面构件。名称、楼层、用途及明确内外部属性忠实表达；我没有要求强度、耐火、热工等性能，不要填入这些属性，更不能填零、null或未知。颜色不能用来反证材料。请输出完整IFC2X3并在报告中区分需求符合性、机器检查和未验证的工程合理性，不称为可直接施工或已全面合规。
```

Source: [design-brief/input.txt](design-brief/input.txt)

## Conversation

```json
[
  {
    "content": "请建一座两层的光庭阅读馆，采用完整围合的矩形建筑，中间是露天光庭，二层有连续的围庭回廊。建筑要安静、明亮、有秩序：浅暖灰主体、深灰细窗框、通透的玻璃栏板、少量木色门扇。请建真实的建筑本体，不建花草、家具、文字招牌、设备和复杂五金。下面是我委托设计后确认采用的方案参数，不需要再询问风格、尺寸和布置；若参数相互矛盾或系统确实不能表达，请指出，不要擅自修改。\n\n以外轮廓西南角为原点，东为X正向，北为Y正向，向上为Z正向，以下平面距离单位为米，IFC采用毫米。外轮廓东西24米、南北18米。露天光庭的平面范围为X=8到16、Y=6到12，8米乘6米；从首层地面向天空敞开，二层楼板和屋盖在这里真实开洞，不能只画线、藏板或拿玻璃封顶。首层地面在光庭范围保留。\n\n首层和二层完成面标高为0和3.6米。两层墙高均3.4米。首层楼板底面-0.2米、顶面0米，二层楼板底面3.4米、顶面3.6米；两块板厚200毫米，外轮廓24乘18米。平屋盖底面7米、顶面7.2米，外轮廓同建筑，厚200毫米，光庭洞口与二层的8乘6米洞口对齐。本例屋盖明确用屋面用途的IfcSlab表达，作为一块独立带洞的板，不要求额外IfcRoof容器，也不要重复建两块屋盖。三块板均归属对应的建筑楼层，屋盖归属二层，不另建第三层。二层楼板另有下述楼梯洞口。\n\n每层外墙厚240毫米、全部在建筑外轮廓内。南北外墙各贯通24米，实体Y范围分别0到0.24、17.76到18；东西外墙实体X范围分别0到0.24、23.76到24，Y范围0.24到17.76，四角只相接不相互重叠。\n\n每层阅读房间与围庭交通区之间设四条厚240毫米的分隔墙。南侧分隔墙X=0.24到23.76、Y=3.74到3.98；北侧X相同、Y=14.02到14.26；西侧分隔墙X=5.74到5.98、Y=3.98到14.02；东侧X=18.02到18.26、Y=3.98到14.02。墙端对接，不能重复堆叠。光庭与回廊之间不设通高墙或玻璃幕墙，回廊是有顶半室外空间。屋盖覆盖回廊和房间，只有光庭露天。\n\n每层明确设四个室内功能空间和四段半室外回廊空间，各空间高3.4米：南侧接待与交流区净范围X=0.24到23.76、Y=0.24到3.74；北侧安静阅读区X=0.24到23.76、Y=14.26到17.76；东侧共享阅读区X=18.26到23.76、Y=3.98到14.02；西侧服务与楼梯区X=0.24到5.74、Y=3.98到14.02。南回廊X=5.98到18.02、Y=3.98到6；北回廊X=5.98到18.02、Y=12到14.02；西回廊X=5.98到8、Y=6到12；东回廊X=16到18.02、Y=6到12。回廊四段相连且互不正面积重叠，光庭本身不创建跨层室内空间。西侧空间是包含楼梯的功能区，不能将空间包围楼梯洞口本身误报为实体碰撞。\n\n楼梯位于西侧区内：一条从南向北上升的直跑楼梯连接首层0米与二层3.6米，净宽1.5米，平面X=1到2.5、Y=5到11，共20级，每级180毫米高，水平踏步进深300毫米。二层洞口平面X=1到2.5、Y=5到11，穿透200毫米板。下端候梯区Y=3.98到5，上端平台Y=11到12.6，利用既有楼板，不叠加平台板。梯段两侧设置实体围护墙：X=0.76到1及X=2.5到2.74，Y=3.98到12.6，每层墙高3.4米。首层在东侧楼梯围护墙设宽900毫米、高2100毫米右单开门，中心Y=4.5米；二层在同侧墙设同尺寸左单开门，中心Y=11.8米。门洞距墙端的实心墙至少50毫米，开启方向朝楼梯间外的服务区，不占梯段。楼梯上端可从平台出门经西侧服务区进入回廊。斜向抓握扶手不是本次已实现细节，不要虚构；报告中明确这项限制。\n\n二层回廊靠光庭一侧设四块连续透明玻璃栏板，高1100毫米、厚20毫米，底部在完成面3.6米。南栏板X=7.98到16.02、Y=5.98到6；北栏板X相同、Y=12到12.02；西栏板X=7.98到8、Y=6到12；东栏板X=16到16.02、Y=6到12。四角实体边界相接不重叠，板落在楼板侧。回廊通行带从分隔墙内表面量至栏板通行侧表面，至少2米。玻璃栏板分别为IfcRailing，不做一块横跨光庭的板，不增加立柱和扶手假细节。\n\n各层南、北侧分隔墙各两扇宽1000毫米、高2400毫米的基本单开木门，中心X=7和17米；两侧各自西门左单开、东门右单开。东西侧分隔墙各一扇同尺寸右单开门，中心Y=9米。门底与本层完成面齐平，门扇朝房间一侧开启。首层南外墙另设一扇宽1400毫米、高2600毫米左单开入口门，中心X=12米，二层不复制入口。加上楼梯间两扇门，总计15扇门。每扇门有自己独立的开口、宿主、基本门框和门扇，不使用双扇或推拉门模板。\n\n每层南、北外墙各四扇双竖面板窗，中心X=3、8、16、21米；东外墙两扇双竖面板窗，中心Y=6.5、11.5米；西外墙两扇单面板窗，中心Y=2和16米。双面板窗宽2000毫米、高2400毫米，窗台高600毫米；单面板窗宽1000毫米、高1800毫米，窗台高1200毫米。每层南、北分隔墙各两扇双竖面板窗，中心X=10和14米；东分隔墙两扇、西分隔墙两扇双竖面板窗，中心Y=6.5和11.5米，这八扇内侧窗宽1600毫米、高2100毫米、窗台高900毫米。每层共20窗，总计40窗。窗头均距本层完成面3米，上下层同轴对齐；窗、洞口和宿主墙一一对应，框和玻璃有部件分色。\n\n外墙、分隔墙和楼梯围护墙均采用20毫米砂浆、200毫米混凝土、20毫米砂浆的三层材料，厚度总计240毫米。三块水平板均为180毫米混凝土加20毫米砂浆面层，总厚200毫米。门整体材料为木材；栏板整体材料为玻璃。窗采用基本窗模板的框与玻璃部件样式，不将整窗谎称为纯铝或纯玻璃，也不要求当前合同不能表达的逐部件物理材料附件。\n\n整体现有warm-residential风格，墙面颜色#D8D4CA、窗框和门框#333D40、木门扇#A87950；玻璃保持透明，栏板透明度0.75。板面为浅暖灰，与主体协调。相同用途、相同规格和相同开启方向的门窗明确共享本项目内Type/Style；两组不同宽度的双面板窗不得错误共享同一规格；楼梯围护门与普通房门、入口门分别组织，南北两块同规格栏板可共享，东西两块同规格栏板可共享。不同墙长不强制共享类型。实际Type只在本模型中创建，不引入外部资产。\n\n本例先完成以上完整建筑，不额外添加没有明确位置的梁柱、雨篷、幕墙和饰面构件。名称、楼层、用途及明确内外部属性忠实表达；我没有要求强度、耐火、热工等性能，不要填入这些属性，更不能填零、null或未知。颜色不能用来反证材料。请输出完整IFC2X3并在报告中区分需求符合性、机器检查和未验证的工程合理性，不称为可直接施工或已全面合规。\n",
    "question_ids": [],
    "role": "user",
    "turn_id": "turn-user-001"
  }
]
```

Source: [design-brief/conversation.json](design-brief/conversation.json)

## Design Brief Agent

- response_id: `4788f467-4e94-4ab2-b818-9f6f8513c5eb`
- stop_reason: `stop`
- evidence_class: `live`

### Prompt

Source: [design-brief/prompt-rendered.md](design-brief/prompt-rendered.md)

### Raw Model Output

Source: [design-brief/response.raw.json](design-brief/response.raw.json)
Source: [design-brief/model-text.txt](design-brief/model-text.txt)

### Parsed Output

Source: [design-brief/design-brief.json](design-brief/design-brief.json)

### Validation and Metrics

Source: [design-brief/validation.json](design-brief/validation.json)
Source: [design-brief/metrics.json](design-brief/metrics.json)

## BIM JSON Generator

- response_id: `c71fd68d-5df7-4e56-91b3-444eb4937315`
- stop_reason: `stop`
- evidence_class: `live`

### Prompt

Source: [generator/prompt-rendered.md](generator/prompt-rendered.md)

### Raw Model Output

Source: [generator/response.raw.json](generator/response.raw.json)
Source: [generator/model-text.txt](generator/model-text.txt)

### Parsed Output

Source: [generator/candidate.json](generator/candidate.json)

### Validation and Metrics

Source: [generator/validation.json](generator/validation.json)
Source: [generator/metrics.json](generator/metrics.json)

## Repair Route

- route: `repair_attempted`
- provider_call_count: `0`
- evidence_class: `deterministic-derived-no-call`

Source: [repair/route.json](repair/route.json)
Source: [repair/repair-attempts.json](repair/repair-attempts.json)
Source: [repair/metrics.json](repair/metrics.json)

## Audit Agent

- response_id: `e6ee79c7-ce98-4caf-96ae-eb3c91b95ae1`
- stop_reason: `stop`
- evidence_class: `live`

### Prompt

Source: [audit/prompt-rendered.md](audit/prompt-rendered.md)

### Raw Model Output

Source: [audit/response.raw.json](audit/response.raw.json)
Source: [audit/model-text.txt](audit/model-text.txt)

### Parsed Output

Source: [audit/audit-report.json](audit/audit-report.json)

### Validation and Metrics

Source: [audit/validation.json](audit/validation.json)
Source: [audit/metrics.json](audit/metrics.json)

## Semantic Coverage
Source: [semantic-capabilities.json](semantic-capabilities.json)
Source: [semantic-coverage.json](semantic-coverage.json)
```json
{
  "blocking_facts": [],
  "candidate_entity_count": 173,
  "capability_profile_hash": "sha256:0a5113dd41d99b45f6e4bc3010568236d90dca2a7d3ce8876ddc1b99e4945aed",
  "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.2/1.0",
  "case_id": "3cd339b0be4fd872",
  "custom_property_policy": {
    "counts_as_semantic_support": false,
    "state": "preserved_text_only"
  },
  "facts": [
    {
      "coverage_state": "represented",
      "path": "/known_facts/appearance/profile",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "warm-residential"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/appearance/style_notes",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "安静、明亮、有秩序；浅暖灰主体，深灰细窗框，通透玻璃栏板，少量木色门扇；水平板面浅暖灰，与主体协调"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/floor_slab_thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/id",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "building-guangting-reading-hall"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/model_bounds_note",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "外轮廓东西24000毫米、南北18000毫米；东为X正向、北为Y正向、向上为Z正向"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/name",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "光庭阅读馆"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/x_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 24000
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/x_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 0
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/y_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 18000
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/y_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 0
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/polygon",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        [
          0,
          0
        ],
        [
          24000,
          0
        ],
        [
          24000,
          18000
        ],
        [
          0,
          18000
        ],
        [
          0,
          0
        ]
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/roof_slab_thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/storey_count",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 2
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/units/length",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "MILLIMETRE"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/exclusions",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "不建花草、家具、文字招牌、设备和复杂五金",
        "不建没有明确位置的梁柱、雨篷、幕墙和饰面构件",
        "不设光庭与回廊之间的通高墙或玻璃幕墙",
        "不创建跨越两层的光庭室内空间",
        "不添加门窗强度、耐火、热工等未要求的性能属性",
        "不引入外部Type资产，不建设计未提及的立柱与扶手假细节"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/floor_slabs",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "bottom_elevation_mm": -200,
          "id": "slab-storey-1-floor",
          "ifc_class": "IfcSlab",
          "name": "首层楼板",
          "note": "光庭范围首层地面保留，不设洞口",
          "openings": [],
          "outline": {
            "x_max": 24000,
            "x_min": 0,
            "y_max": 18000,
            "y_min": 0
          },
          "predefined_type": "FLOOR",
          "storey": "storey-1",
          "thickness_mm": 200,
          "top_elevation_mm": 0
        },
        {
          "bottom_elevation_mm": 3400,
          "id": "slab-storey-2-floor",
          "ifc_class": "IfcSlab",
          "name": "二层楼板",
          "openings": [
            {
              "bounds": {
                "x": [
                  8000,
                  16000
                ],
                "y": [
                  6000,
                  12000
                ]
              },
              "id": "slab-storey-2-opening-light-court",
              "name": "露天光庭洞口",
              "usage": "light_court"
            },
            {
              "bounds": {
                "x": [
                  1000,
                  2500
                ],
                "y": [
                  5000,
                  11000
                ]
              },
              "id": "slab-storey-2-opening-stair",
              "name": "楼梯洞口",
              "usage": "stair"
            }
          ],
          "outline": {
            "x_max": 24000,
            "x_min": 0,
            "y_max": 18000,
            "y_min": 0
          },
          "predefined_type": "FLOOR",
          "storey": "storey-2",
          "thickness_mm": 200,
          "top_elevation_mm": 3600
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/plan_constraints",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "derived_wall_ids": [],
          "id": "plan-constraint-storey-1",
          "kind": "inside_wall_envelope",
          "outline_ref": "/known_facts/building/polygon",
          "source_turns": [
            "turn-user-001"
          ],
          "storey_ref": "/known_facts/storeys/0",
          "thickness_mm": 240
        },
        {
          "derived_wall_ids": [],
          "id": "plan-constraint-storey-2",
          "kind": "inside_wall_envelope",
          "outline_ref": "/known_facts/building/polygon",
          "source_turns": [
            "turn-user-001"
          ],
          "storey_ref": "/known_facts/storeys/1",
          "thickness_mm": 240
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/railings",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "alignment_target": "光庭南边缘楼板侧",
          "base_elevation_mm": 3600,
          "bounds": {
            "x": [
              7980,
              16020
            ],
            "y": [
              5980,
              6000
            ]
          },
          "end_mm": [
            16020,
            5990,
            3600
          ],
          "height_mm": 1100,
          "id": "storey-2-railing-court-south",
          "name": "二层南侧玻璃栏板",
          "start_mm": [
            7980,
            5990,
            3600
          ],
          "storey": "storey-2",
          "thickness_mm": 20
        },
        {
          "alignment_target": "光庭北边缘楼板侧",
          "base_elevation_mm": 3600,
          "bounds": {
            "x": [
              7980,
              16020
            ],
            "y": [
              12000,
              12020
            ]
          },
          "end_mm": [
            16020,
            12010,
            3600
          ],
          "height_mm": 1100,
          "id": "storey-2-railing-court-north",
          "name": "二层北侧玻璃栏板",
          "start_mm": [
            7980,
            12010,
            3600
          ],
          "storey": "storey-2",
          "thickness_mm": 20
        },
        {
          "alignment_target": "光庭西边缘楼板侧",
          "base_elevation_mm": 3600,
          "bounds": {
            "x": [
              7980,
              8000
            ],
            "y": [
              6000,
              12000
            ]
          },
          "end_mm": [
            7990,
            12000,
            3600
          ],
          "height_mm": 1100,
          "id": "storey-2-railing-court-west",
          "name": "二层西侧玻璃栏板",
          "start_mm": [
            7990,
            6000,
            3600
          ],
          "storey": "storey-2",
          "thickness_mm": 20
        },
        {
          "alignment_target": "光庭东边缘楼板侧",
          "base_elevation_mm": 3600,
          "bounds": {
            "x": [
              16000,
              16020
            ],
            "y": [
              6000,
              12000
            ]
          },
          "end_mm": [
            16010,
            12000,
            3600
          ],
          "height_mm": 1100,
          "id": "storey-2-railing-court-east",
          "name": "二层东侧玻璃栏板",
          "start_mm": [
            16010,
            6000,
            3600
          ],
          "storey": "storey-2",
          "thickness_mm": 20
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bottom_elevation_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 7000
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/id",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "roof-slab-storey-2"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/ifc_class",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "IfcSlab"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/name",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "屋盖"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/note",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "按用户要求用屋面用途的IfcSlab表达为一块独立带洞的板，不额外创建IfcRoof容器，不重复建两块屋盖"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/opening/bounds/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        8000,
        16000
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/opening/bounds/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        6000,
        12000
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/opening/id",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "roof-opening-light-court"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/opening/name",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "屋盖光庭洞口"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/opening/usage",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "light_court"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/outline/x_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 24000
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/outline/x_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 0
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/outline/y_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 18000
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/outline/y_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 0
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/predefined_type",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "ROOF"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/storey",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "storey-2"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/top_elevation_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 7200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_requirements",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-exterior-south",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-exterior-north",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-exterior-west",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-exterior-east",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-partition-south",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-partition-north",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-partition-west",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-partition-east",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-stair-west",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-1-wall-stair-east",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-exterior-south",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-exterior-north",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-exterior-west",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-exterior-east",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-partition-south",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-partition-north",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-partition-west",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-partition-east",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-stair-west",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "appearance": {
            "color": [
              0.847059,
              0.831373,
              0.792157
            ]
          },
          "entity_id": "storey-2-wall-stair-east",
          "material": {
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "墙体240mm-砂浆20-混凝土200-砂浆20",
            "layers": [
              {
                "name": "砂浆",
                "thickness": 20
              },
              {
                "name": "混凝土",
                "thickness": 200
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -120
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "slab-storey-1-floor",
          "material": {
            "direction": "AXIS3",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "水平板200mm-混凝土180-砂浆20",
            "layers": [
              {
                "name": "混凝土",
                "thickness": 180
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -200
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "slab-storey-2-floor",
          "material": {
            "direction": "AXIS3",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "水平板200mm-混凝土180-砂浆20",
            "layers": [
              {
                "name": "混凝土",
                "thickness": 180
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -200
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "roof-slab-storey-2",
          "material": {
            "direction": "AXIS3",
            "direction_sense": "POSITIVE",
            "kind": "material_layer_set_usage",
            "layer_set_name": "水平板200mm-混凝土180-砂浆20",
            "layers": [
              {
                "name": "混凝土",
                "thickness": 180
              },
              {
                "name": "砂浆",
                "thickness": 20
              }
            ],
            "offset_from_reference_line": -200
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-door-partition-south-west",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-left"
        },
        {
          "entity_id": "storey-1-door-partition-south-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-1-door-partition-north-west",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-left"
        },
        {
          "entity_id": "storey-1-door-partition-north-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-1-door-partition-west",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-1-door-partition-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-1-door-entry-south",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-entry-1400x2600-left"
        },
        {
          "entity_id": "storey-1-door-stair-enclosure-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-stair-900x2100-right"
        },
        {
          "entity_id": "storey-2-door-partition-south-west",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-left"
        },
        {
          "entity_id": "storey-2-door-partition-south-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-2-door-partition-north-west",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-left"
        },
        {
          "entity_id": "storey-2-door-partition-north-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-2-door-partition-west",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-2-door-partition-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-partition-1000x2400-right"
        },
        {
          "entity_id": "storey-2-door-stair-enclosure-east",
          "material": {
            "kind": "single_material",
            "name": "木材"
          },
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            },
            "panel": {
              "color": [
                0.658824,
                0.47451,
                0.313725
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-door-stair-900x2100-left"
        },
        {
          "entity_id": "storey-1-window-exterior-south-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-south-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-south-3",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-south-4",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-north-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-north-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-north-3",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-north-4",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-east-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-east-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-1-window-exterior-west-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-single-1000x1800"
        },
        {
          "entity_id": "storey-1-window-exterior-west-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-single-1000x1800"
        },
        {
          "entity_id": "storey-1-window-partition-south-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-south-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-north-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-north-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-east-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-east-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-west-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-1-window-partition-west-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-exterior-south-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-south-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-south-3",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-south-4",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-north-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-north-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-north-3",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-north-4",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-east-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-east-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-double-2000x2400"
        },
        {
          "entity_id": "storey-2-window-exterior-west-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-single-1000x1800"
        },
        {
          "entity_id": "storey-2-window-exterior-west-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-exterior-single-1000x1800"
        },
        {
          "entity_id": "storey-2-window-partition-south-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-south-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-north-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-north-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-east-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-east-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-west-1",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "entity_id": "storey-2-window-partition-west-2",
          "part_appearance": {
            "frame": {
              "color": [
                0.2,
                0.239216,
                0.25098
              ]
            }
          },
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          },
          "type_id": "type-window-interior-double-1600x2100"
        },
        {
          "appearance": {
            "transparency": 0.75
          },
          "entity_id": "storey-2-railing-court-south",
          "material": {
            "kind": "single_material",
            "name": "玻璃"
          },
          "scope": "direct",
          "source": "user",
          "type_id": "type-railing-glass-south-north"
        },
        {
          "appearance": {
            "transparency": 0.75
          },
          "entity_id": "storey-2-railing-court-north",
          "material": {
            "kind": "single_material",
            "name": "玻璃"
          },
          "scope": "direct",
          "source": "user",
          "type_id": "type-railing-glass-south-north"
        },
        {
          "appearance": {
            "transparency": 0.75
          },
          "entity_id": "storey-2-railing-court-west",
          "material": {
            "kind": "single_material",
            "name": "玻璃"
          },
          "scope": "direct",
          "source": "user",
          "type_id": "type-railing-glass-east-west"
        },
        {
          "appearance": {
            "transparency": 0.75
          },
          "entity_id": "storey-2-railing-court-east",
          "material": {
            "kind": "single_material",
            "name": "玻璃"
          },
          "scope": "direct",
          "source": "user",
          "type_id": "type-railing-glass-east-west"
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/appearance/source_turns",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "turn-user-001"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/appearance/status",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/material/source_turns",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "turn-user-001"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/material/status",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/property/source_turns",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "turn-user-001"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/property/status",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "not_specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/template/source_turns",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "turn-user-001"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/template/status",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/type/source_turns",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "turn-user-001"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/type/status",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/stairs",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "bounds": {
            "x": [
              1000,
              2500
            ],
            "y": [
              5000,
              11000
            ]
          },
          "end_elevation_mm": 3600,
          "from_storey": "storey-1",
          "id": "stair-1",
          "landing_note": "下端候梯区与上端平台利用既有楼板，不叠加平台板",
          "limitations": [
            "斜向抓握扶手不属于本次实现细节，按要求不虚构、不建模"
          ],
          "lower_waiting_area_bounds": {
            "x": [
              1000,
              2500
            ],
            "y": [
              3980,
              5000
            ]
          },
          "name": "西侧直跑楼梯",
          "number_of_risers": 20,
          "number_of_treads": 20,
          "opening_bounds": {
            "x": [
              1000,
              2500
            ],
            "y": [
              5000,
              11000
            ]
          },
          "opening_host": "slab-storey-2-floor",
          "riser_height_mm": 180,
          "run_direction": "south_to_north",
          "start_elevation_mm": 0,
          "to_storey": "storey-2",
          "tread_depth_mm": 300,
          "upper_landing_bounds": {
            "x": [
              1000,
              2500
            ],
            "y": [
              11000,
              12600
            ]
          },
          "width_mm": 1500
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/storeys",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "doors": [
            {
              "center_global_mm": [
                7000,
                3860
              ],
              "handing": "left",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-partition-south",
              "id": "storey-1-door-partition-south-west",
              "name": "首层南侧分隔墙西门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                17000,
                3860
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-partition-south",
              "id": "storey-1-door-partition-south-east",
              "name": "首层南侧分隔墙东门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                7000,
                14140
              ],
              "handing": "left",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-partition-north",
              "id": "storey-1-door-partition-north-west",
              "name": "首层北侧分隔墙西门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                17000,
                14140
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-partition-north",
              "id": "storey-1-door-partition-north-east",
              "name": "首层北侧分隔墙东门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                5860,
                9000
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-partition-west",
              "id": "storey-1-door-partition-west",
              "name": "首层西侧分隔墙门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                18140,
                9000
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-partition-east",
              "id": "storey-1-door-partition-east",
              "name": "首层东侧分隔墙门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                12000,
                120
              ],
              "handing": "left",
              "height_mm": 2600,
              "host_wall": "storey-1-wall-exterior-south",
              "id": "storey-1-door-entry-south",
              "name": "首层南外墙入口门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "width_mm": 1400
            },
            {
              "center_global_mm": [
                2620,
                4500
              ],
              "handing": "right",
              "height_mm": 2100,
              "host_wall": "storey-1-wall-stair-east",
              "id": "storey-1-door-stair-enclosure-east",
              "name": "首层楼梯围护墙东侧门",
              "operation": "single_swing",
              "sill_elevation_mm": 0,
              "swing_direction": "towards_service_area",
              "width_mm": 900
            }
          ],
          "elevation_mm": 0,
          "id": "storey-1",
          "name": "首层",
          "net_height_mm": 3400,
          "spaces": [
            {
              "bounds": {
                "x": [
                  240,
                  23760
                ],
                "y": [
                  240,
                  3740
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-south-reception",
              "name": "南侧接待与交流区",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  240,
                  23760
                ],
                "y": [
                  14260,
                  17760
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-north-quiet-reading",
              "name": "北侧安静阅读区",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  18260,
                  23760
                ],
                "y": [
                  3980,
                  14020
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-east-shared-reading",
              "name": "东侧共享阅读区",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  240,
                  5740
                ],
                "y": [
                  3980,
                  14020
                ]
              },
              "contains_stair": "stair-1",
              "height_mm": 3400,
              "id": "storey-1-space-west-service-stair",
              "name": "西侧服务与楼梯区",
              "note": "该功能区包含楼梯及其洞口，空间包络楼梯洞口本身不视为实体碰撞",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  5980,
                  18020
                ],
                "y": [
                  3980,
                  6000
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-corridor-south",
              "name": "南回廊",
              "space_category": "semi_outdoor"
            },
            {
              "bounds": {
                "x": [
                  5980,
                  18020
                ],
                "y": [
                  12000,
                  14020
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-corridor-north",
              "name": "北回廊",
              "space_category": "semi_outdoor"
            },
            {
              "bounds": {
                "x": [
                  5980,
                  8000
                ],
                "y": [
                  6000,
                  12000
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-corridor-west",
              "name": "西回廊",
              "space_category": "semi_outdoor"
            },
            {
              "bounds": {
                "x": [
                  16000,
                  18020
                ],
                "y": [
                  6000,
                  12000
                ]
              },
              "height_mm": 3400,
              "id": "storey-1-space-corridor-east",
              "name": "东回廊",
              "space_category": "semi_outdoor"
            }
          ],
          "walls": {
            "exterior": [
              {
                "bounds": {
                  "x": [
                    0,
                    24000
                  ],
                  "y": [
                    0,
                    240
                  ]
                },
                "height_mm": 3400,
                "id": "storey-1-wall-exterior-south",
                "name": "首层南外墙",
                "side": "south",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    0,
                    24000
                  ],
                  "y": [
                    17760,
                    18000
                  ]
                },
                "height_mm": 3400,
                "id": "storey-1-wall-exterior-north",
                "name": "首层北外墙",
                "side": "north",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    0,
                    240
                  ],
                  "y": [
                    240,
                    17760
                  ]
                },
                "height_mm": 3400,
                "id": "storey-1-wall-exterior-west",
                "name": "首层西外墙",
                "side": "west",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    23760,
                    24000
                  ],
                  "y": [
                    240,
                    17760
                  ]
                },
                "height_mm": 3400,
                "id": "storey-1-wall-exterior-east",
                "name": "首层东外墙",
                "side": "east",
                "thickness_mm": 240
              }
            ],
            "interior": [
              {
                "bounds": {
                  "x": [
                    240,
                    23760
                  ],
                  "y": [
                    3740,
                    3980
                  ]
                },
                "connects": [
                  "storey-1-space-south-reception",
                  "storey-1-space-west-service-stair",
                  "storey-1-space-corridor-south",
                  "storey-1-space-east-shared-reading"
                ],
                "height_mm": 3400,
                "id": "storey-1-wall-partition-south",
                "name": "首层南侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    240,
                    23760
                  ],
                  "y": [
                    14020,
                    14260
                  ]
                },
                "connects": [
                  "storey-1-space-north-quiet-reading",
                  "storey-1-space-west-service-stair",
                  "storey-1-space-corridor-north",
                  "storey-1-space-east-shared-reading"
                ],
                "height_mm": 3400,
                "id": "storey-1-wall-partition-north",
                "name": "首层北侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    5740,
                    5980
                  ],
                  "y": [
                    3980,
                    14020
                  ]
                },
                "connects": [
                  "storey-1-space-west-service-stair",
                  "storey-1-space-corridor-west"
                ],
                "height_mm": 3400,
                "id": "storey-1-wall-partition-west",
                "name": "首层西侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    18020,
                    18260
                  ],
                  "y": [
                    3980,
                    14020
                  ]
                },
                "connects": [
                  "storey-1-space-east-shared-reading",
                  "storey-1-space-corridor-east"
                ],
                "height_mm": 3400,
                "id": "storey-1-wall-partition-east",
                "name": "首层东侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    760,
                    1000
                  ],
                  "y": [
                    3980,
                    12600
                  ]
                },
                "height_mm": 3400,
                "id": "storey-1-wall-stair-west",
                "name": "首层楼梯围护墙（西）",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    2500,
                    2740
                  ],
                  "y": [
                    3980,
                    12600
                  ]
                },
                "height_mm": 3400,
                "id": "storey-1-wall-stair-east",
                "name": "首层楼梯围护墙（东）",
                "thickness_mm": 240
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                3000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-south",
              "id": "storey-1-window-exterior-south-1",
              "name": "首层南外墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                8000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-south",
              "id": "storey-1-window-exterior-south-2",
              "name": "首层南外墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                16000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-south",
              "id": "storey-1-window-exterior-south-3",
              "name": "首层南外墙双竖面板窗3",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                21000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-south",
              "id": "storey-1-window-exterior-south-4",
              "name": "首层南外墙双竖面板窗4",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                3000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-north",
              "id": "storey-1-window-exterior-north-1",
              "name": "首层北外墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                8000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-north",
              "id": "storey-1-window-exterior-north-2",
              "name": "首层北外墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                16000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-north",
              "id": "storey-1-window-exterior-north-3",
              "name": "首层北外墙双竖面板窗3",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                21000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-north",
              "id": "storey-1-window-exterior-north-4",
              "name": "首层北外墙双竖面板窗4",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                23880,
                6500
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-east",
              "id": "storey-1-window-exterior-east-1",
              "name": "首层东外墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                23880,
                11500
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-exterior-east",
              "id": "storey-1-window-exterior-east-2",
              "name": "首层东外墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                120,
                2000
              ],
              "head_height_mm": 3000,
              "height_mm": 1800,
              "host_wall": "storey-1-wall-exterior-west",
              "id": "storey-1-window-exterior-west-1",
              "name": "首层西外墙单面板窗1",
              "panels": "single",
              "sill_height_mm": 1200,
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                120,
                16000
              ],
              "head_height_mm": 3000,
              "height_mm": 1800,
              "host_wall": "storey-1-wall-exterior-west",
              "id": "storey-1-window-exterior-west-2",
              "name": "首层西外墙单面板窗2",
              "panels": "single",
              "sill_height_mm": 1200,
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                10000,
                3860
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-south",
              "id": "storey-1-window-partition-south-1",
              "name": "首层南侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                14000,
                3860
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-south",
              "id": "storey-1-window-partition-south-2",
              "name": "首层南侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                10000,
                14140
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-north",
              "id": "storey-1-window-partition-north-1",
              "name": "首层北侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                14000,
                14140
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-north",
              "id": "storey-1-window-partition-north-2",
              "name": "首层北侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                18140,
                6500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-east",
              "id": "storey-1-window-partition-east-1",
              "name": "首层东侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                18140,
                11500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-east",
              "id": "storey-1-window-partition-east-2",
              "name": "首层东侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                5860,
                6500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-west",
              "id": "storey-1-window-partition-west-1",
              "name": "首层西侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                5860,
                11500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-west",
              "id": "storey-1-window-partition-west-2",
              "name": "首层西侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            }
          ]
        },
        {
          "doors": [
            {
              "center_global_mm": [
                7000,
                3860
              ],
              "handing": "left",
              "height_mm": 2400,
              "host_wall": "storey-2-wall-partition-south",
              "id": "storey-2-door-partition-south-west",
              "name": "二层南侧分隔墙西门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                17000,
                3860
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-2-wall-partition-south",
              "id": "storey-2-door-partition-south-east",
              "name": "二层南侧分隔墙东门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                7000,
                14140
              ],
              "handing": "left",
              "height_mm": 2400,
              "host_wall": "storey-2-wall-partition-north",
              "id": "storey-2-door-partition-north-west",
              "name": "二层北侧分隔墙西门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                17000,
                14140
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-2-wall-partition-north",
              "id": "storey-2-door-partition-north-east",
              "name": "二层北侧分隔墙东门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                5860,
                9000
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-2-wall-partition-west",
              "id": "storey-2-door-partition-west",
              "name": "二层西侧分隔墙门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                18140,
                9000
              ],
              "handing": "right",
              "height_mm": 2400,
              "host_wall": "storey-2-wall-partition-east",
              "id": "storey-2-door-partition-east",
              "name": "二层东侧分隔墙门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_room",
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                2620,
                11800
              ],
              "handing": "left",
              "height_mm": 2100,
              "host_wall": "storey-2-wall-stair-east",
              "id": "storey-2-door-stair-enclosure-east",
              "name": "二层楼梯围护墙东侧门",
              "operation": "single_swing",
              "sill_elevation_mm": 3600,
              "swing_direction": "towards_service_area",
              "width_mm": 900
            }
          ],
          "elevation_mm": 3600,
          "id": "storey-2",
          "name": "二层",
          "net_height_mm": 3400,
          "spaces": [
            {
              "bounds": {
                "x": [
                  240,
                  23760
                ],
                "y": [
                  240,
                  3740
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-south-reception",
              "name": "南侧接待与交流区",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  240,
                  23760
                ],
                "y": [
                  14260,
                  17760
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-north-quiet-reading",
              "name": "北侧安静阅读区",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  18260,
                  23760
                ],
                "y": [
                  3980,
                  14020
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-east-shared-reading",
              "name": "东侧共享阅读区",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  240,
                  5740
                ],
                "y": [
                  3980,
                  14020
                ]
              },
              "contains_stair": "stair-1",
              "height_mm": 3400,
              "id": "storey-2-space-west-service-stair",
              "name": "西侧服务与楼梯区",
              "note": "该功能区包含楼梯上端平台与楼板洞口，空间包络洞口本身不视为实体碰撞",
              "space_category": "indoor"
            },
            {
              "bounds": {
                "x": [
                  5980,
                  18020
                ],
                "y": [
                  3980,
                  6000
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-corridor-south",
              "name": "南回廊",
              "space_category": "semi_outdoor"
            },
            {
              "bounds": {
                "x": [
                  5980,
                  18020
                ],
                "y": [
                  12000,
                  14020
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-corridor-north",
              "name": "北回廊",
              "space_category": "semi_outdoor"
            },
            {
              "bounds": {
                "x": [
                  5980,
                  8000
                ],
                "y": [
                  6000,
                  12000
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-corridor-west",
              "name": "西回廊",
              "space_category": "semi_outdoor"
            },
            {
              "bounds": {
                "x": [
                  16000,
                  18020
                ],
                "y": [
                  6000,
                  12000
                ]
              },
              "height_mm": 3400,
              "id": "storey-2-space-corridor-east",
              "name": "东回廊",
              "space_category": "semi_outdoor"
            }
          ],
          "walls": {
            "exterior": [
              {
                "bounds": {
                  "x": [
                    0,
                    24000
                  ],
                  "y": [
                    0,
                    240
                  ]
                },
                "height_mm": 3400,
                "id": "storey-2-wall-exterior-south",
                "name": "二层南外墙",
                "side": "south",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    0,
                    24000
                  ],
                  "y": [
                    17760,
                    18000
                  ]
                },
                "height_mm": 3400,
                "id": "storey-2-wall-exterior-north",
                "name": "二层北外墙",
                "side": "north",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    0,
                    240
                  ],
                  "y": [
                    240,
                    17760
                  ]
                },
                "height_mm": 3400,
                "id": "storey-2-wall-exterior-west",
                "name": "二层西外墙",
                "side": "west",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    23760,
                    24000
                  ],
                  "y": [
                    240,
                    17760
                  ]
                },
                "height_mm": 3400,
                "id": "storey-2-wall-exterior-east",
                "name": "二层东外墙",
                "side": "east",
                "thickness_mm": 240
              }
            ],
            "interior": [
              {
                "bounds": {
                  "x": [
                    240,
                    23760
                  ],
                  "y": [
                    3740,
                    3980
                  ]
                },
                "connects": [
                  "storey-2-space-south-reception",
                  "storey-2-space-west-service-stair",
                  "storey-2-space-corridor-south",
                  "storey-2-space-east-shared-reading"
                ],
                "height_mm": 3400,
                "id": "storey-2-wall-partition-south",
                "name": "二层南侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    240,
                    23760
                  ],
                  "y": [
                    14020,
                    14260
                  ]
                },
                "connects": [
                  "storey-2-space-north-quiet-reading",
                  "storey-2-space-west-service-stair",
                  "storey-2-space-corridor-north",
                  "storey-2-space-east-shared-reading"
                ],
                "height_mm": 3400,
                "id": "storey-2-wall-partition-north",
                "name": "二层北侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    5740,
                    5980
                  ],
                  "y": [
                    3980,
                    14020
                  ]
                },
                "connects": [
                  "storey-2-space-west-service-stair",
                  "storey-2-space-corridor-west"
                ],
                "height_mm": 3400,
                "id": "storey-2-wall-partition-west",
                "name": "二层西侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    18020,
                    18260
                  ],
                  "y": [
                    3980,
                    14020
                  ]
                },
                "connects": [
                  "storey-2-space-east-shared-reading",
                  "storey-2-space-corridor-east"
                ],
                "height_mm": 3400,
                "id": "storey-2-wall-partition-east",
                "name": "二层东侧分隔墙",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    760,
                    1000
                  ],
                  "y": [
                    3980,
                    12600
                  ]
                },
                "height_mm": 3400,
                "id": "storey-2-wall-stair-west",
                "name": "二层楼梯围护墙（西）",
                "thickness_mm": 240
              },
              {
                "bounds": {
                  "x": [
                    2500,
                    2740
                  ],
                  "y": [
                    3980,
                    12600
                  ]
                },
                "height_mm": 3400,
                "id": "storey-2-wall-stair-east",
                "name": "二层楼梯围护墙（东）",
                "thickness_mm": 240
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                3000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-south",
              "id": "storey-2-window-exterior-south-1",
              "name": "二层南外墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                8000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-south",
              "id": "storey-2-window-exterior-south-2",
              "name": "二层南外墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                16000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-south",
              "id": "storey-2-window-exterior-south-3",
              "name": "二层南外墙双竖面板窗3",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                21000,
                120
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-south",
              "id": "storey-2-window-exterior-south-4",
              "name": "二层南外墙双竖面板窗4",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                3000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-north",
              "id": "storey-2-window-exterior-north-1",
              "name": "二层北外墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                8000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-north",
              "id": "storey-2-window-exterior-north-2",
              "name": "二层北外墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                16000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-north",
              "id": "storey-2-window-exterior-north-3",
              "name": "二层北外墙双竖面板窗3",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                21000,
                17880
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-north",
              "id": "storey-2-window-exterior-north-4",
              "name": "二层北外墙双竖面板窗4",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                23880,
                6500
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-east",
              "id": "storey-2-window-exterior-east-1",
              "name": "二层东外墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                23880,
                11500
              ],
              "head_height_mm": 3000,
              "height_mm": 2400,
              "host_wall": "storey-2-wall-exterior-east",
              "id": "storey-2-window-exterior-east-2",
              "name": "二层东外墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 600,
              "width_mm": 2000
            },
            {
              "center_global_mm": [
                120,
                2000
              ],
              "head_height_mm": 3000,
              "height_mm": 1800,
              "host_wall": "storey-2-wall-exterior-west",
              "id": "storey-2-window-exterior-west-1",
              "name": "二层西外墙单面板窗1",
              "panels": "single",
              "sill_height_mm": 1200,
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                120,
                16000
              ],
              "head_height_mm": 3000,
              "height_mm": 1800,
              "host_wall": "storey-2-wall-exterior-west",
              "id": "storey-2-window-exterior-west-2",
              "name": "二层西外墙单面板窗2",
              "panels": "single",
              "sill_height_mm": 1200,
              "width_mm": 1000
            },
            {
              "center_global_mm": [
                10000,
                3860
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-south",
              "id": "storey-2-window-partition-south-1",
              "name": "二层南侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                14000,
                3860
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-south",
              "id": "storey-2-window-partition-south-2",
              "name": "二层南侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                10000,
                14140
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-north",
              "id": "storey-2-window-partition-north-1",
              "name": "二层北侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                14000,
                14140
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-north",
              "id": "storey-2-window-partition-north-2",
              "name": "二层北侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                18140,
                6500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-east",
              "id": "storey-2-window-partition-east-1",
              "name": "二层东侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                18140,
                11500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-east",
              "id": "storey-2-window-partition-east-2",
              "name": "二层东侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                5860,
                6500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-west",
              "id": "storey-2-window-partition-west-1",
              "name": "二层西侧分隔墙双竖面板窗1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            },
            {
              "center_global_mm": [
                5860,
                11500
              ],
              "head_height_mm": 3000,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-west",
              "id": "storey-2-window-partition-west-2",
              "name": "二层西侧分隔墙双竖面板窗2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1600
            }
          ]
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/types",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "handing": "left",
          "height_mm": 2400,
          "id": "type-door-partition-1000x2400-left",
          "ifc_class": "IfcDoorStyle",
          "name": "房间门-1000x2400-左单开",
          "operation": "single_swing",
          "purpose": "普通房间门",
          "width_mm": 1000
        },
        {
          "handing": "right",
          "height_mm": 2400,
          "id": "type-door-partition-1000x2400-right",
          "ifc_class": "IfcDoorStyle",
          "name": "房间门-1000x2400-右单开",
          "operation": "single_swing",
          "purpose": "普通房间门",
          "width_mm": 1000
        },
        {
          "handing": "left",
          "height_mm": 2600,
          "id": "type-door-entry-1400x2600-left",
          "ifc_class": "IfcDoorStyle",
          "name": "入口门-1400x2600-左单开",
          "operation": "single_swing",
          "purpose": "建筑入口门",
          "width_mm": 1400
        },
        {
          "handing": "right",
          "height_mm": 2100,
          "id": "type-door-stair-900x2100-right",
          "ifc_class": "IfcDoorStyle",
          "name": "楼梯围护门-900x2100-右单开",
          "operation": "single_swing",
          "purpose": "楼梯围护墙门",
          "width_mm": 900
        },
        {
          "handing": "left",
          "height_mm": 2100,
          "id": "type-door-stair-900x2100-left",
          "ifc_class": "IfcDoorStyle",
          "name": "楼梯围护门-900x2100-左单开",
          "operation": "single_swing",
          "purpose": "楼梯围护墙门",
          "width_mm": 900
        },
        {
          "height_mm": 2400,
          "id": "type-window-exterior-double-2000x2400",
          "ifc_class": "IfcWindowStyle",
          "name": "外窗-双竖面板-2000x2400",
          "panels": "double_vertical",
          "purpose": "外墙双竖面板窗",
          "width_mm": 2000
        },
        {
          "height_mm": 1800,
          "id": "type-window-exterior-single-1000x1800",
          "ifc_class": "IfcWindowStyle",
          "name": "外窗-单面板-1000x1800",
          "panels": "single",
          "purpose": "外墙单面板窗",
          "width_mm": 1000
        },
        {
          "height_mm": 2100,
          "id": "type-window-interior-double-1600x2100",
          "ifc_class": "IfcWindowStyle",
          "name": "内窗-双竖面板-1600x2100",
          "panels": "double_vertical",
          "purpose": "分隔墙内侧窗",
          "width_mm": 1600
        },
        {
          "height_mm": 1100,
          "id": "type-railing-glass-south-north",
          "ifc_class": "IfcRailingType",
          "name": "玻璃栏板-南北同规格",
          "purpose": "二层回廊玻璃栏板",
          "thickness_mm": 20
        },
        {
          "height_mm": 1100,
          "id": "type-railing-glass-east-west",
          "ifc_class": "IfcRailingType",
          "name": "玻璃栏板-东西同规格",
          "purpose": "二层回廊玻璃栏板",
          "thickness_mm": 20
        }
      ]
    }
  ],
  "schema_version": "text2ifc/semantic-coverage/1.0",
  "valid": true
}
```
Source: [semantic-geometry-expectation.json](semantic-geometry-expectation.json)
## Generated IFC Gates

Source: [semantic-capabilities.json](semantic-capabilities.json)
Source: [semantic-coverage.json](semantic-coverage.json)
Source: [semantic-geometry-expectation.json](semantic-geometry-expectation.json)
Source: [expected-facts.json](expected-facts.json)
Source: [dynamic-gates.json](dynamic-gates.json)
Source: [gate-summary.json](gate-summary.json)
Source: [route-decision.json](route-decision.json)
Source: [ifc-verification.json](ifc-verification.json)
Source: [geometry-expectation.json](geometry-expectation.json)
Source: [geometry-feedback.json](geometry-feedback.json)

### Geometry Feedback

```json
{
  "expectation_source": "design_brief_expected_facts",
  "issues": [],
  "metrics": {
    "case_id": "3cd339b0be4fd872",
    "floor_openings": {
      "roof-opening-light-court": {
        "bbox": {
          "x": [
            8.0,
            16.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            7.0,
            7.2
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "roof-slab-storey-2",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "roof-opening-light-court",
        "resolved_global_id": "2hC4XahCHPEhnNUkSnulpu"
      },
      "slab-storey-2-opening-light-court": {
        "bbox": {
          "x": [
            8.0,
            16.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.4,
            3.6
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "slab-storey-2-floor",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "slab-storey-2-opening-light-court",
        "resolved_global_id": "2ctQA2XPXIRfrgpg0QrXpQ"
      },
      "slab-storey-2-opening-stair": {
        "bbox": {
          "x": [
            1.0,
            2.5
          ],
          "y": [
            5.0,
            11.0
          ],
          "z": [
            3.4,
            3.6
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "slab-storey-2-floor",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "slab-storey-2-opening-stair",
        "resolved_global_id": "0zthKa4rjOKhRJ4XHOKnm$"
      }
    },
    "products": {
      "storey-2-railing-court-east": {
        "bbox": {
          "x": [
            16.0,
            16.020000000000003
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      },
      "storey-2-railing-court-north": {
        "bbox": {
          "x": [
            7.9799999999999995,
            16.02
          ],
          "y": [
            12.0,
            12.02
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      },
      "storey-2-railing-court-south": {
        "bbox": {
          "x": [
            7.9799999999999995,
            16.02
          ],
          "y": [
            5.98,
            6.0
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      },
      "storey-2-railing-court-west": {
        "bbox": {
          "x": [
            7.98,
            8.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      }
    },
    "roof": {
      "roof-slab-storey-2": {
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            18.0
          ],
          "z": [
            7.0,
            7.2
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "slabs": {
      "slab-storey-1-floor": {
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            18.0
          ],
          "z": [
            -0.2,
            0.0
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "slab-storey-2-floor": {
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            18.0
          ],
          "z": [
            3.4,
            3.6
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "spaces": {
      "space-storey-1-storey-1-space-corridor-east": {
        "bbox": {
          "x": [
            16.0,
            18.02
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-corridor-north": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            12.0,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-corridor-south": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            3.98,
            6.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-corridor-west": {
        "bbox": {
          "x": [
            5.98,
            8.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-east-shared-reading": {
        "bbox": {
          "x": [
            18.26,
            23.76
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-north-quiet-reading": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            14.26,
            17.76
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-south-reception": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            0.24,
            3.74
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-west-service-stair": {
        "bbox": {
          "x": [
            0.24,
            5.74
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-east": {
        "bbox": {
          "x": [
            16.0,
            18.02
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-north": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            12.0,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-south": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            3.98,
            6.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-west": {
        "bbox": {
          "x": [
            5.98,
            8.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-east-shared-reading": {
        "bbox": {
          "x": [
            18.26,
            23.76
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-north-quiet-reading": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            14.26,
            17.76
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-south-reception": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            0.24,
            3.74
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-west-service-stair": {
        "bbox": {
          "x": [
            0.24,
            5.74
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      }
    },
    "stairs": {
      "stair-1": {
        "bbox": {
          "x": [
            1.0,
            2.5
          ],
          "y": [
            5.0,
            11.0
          ],
          "z": [
            0.0,
            3.6
          ]
        },
        "flight_ids": [
          "stair-flight-1"
        ],
        "has_stepped_profile": true,
        "wall_intersections": []
      }
    },
    "wall_set_convention": "primary",
    "walls": {
      "wall-storey-1-storey-1-wall-exterior-east": {
        "axis": "y",
        "bbox": {
          "x": [
            23.759999999999998,
            24.0
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-exterior-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            17.759999999999998,
            18.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-exterior-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            0.24
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-exterior-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.0,
            0.24
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-east": {
        "axis": "y",
        "bbox": {
          "x": [
            18.02,
            18.26
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            14.020000000000001,
            14.26
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            3.7399999999999998,
            3.98
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-west": {
        "axis": "y",
        "bbox": {
          "x": [
            5.74,
            5.98
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-stair-east": {
        "axis": "y",
        "bbox": {
          "x": [
            2.5,
            2.74
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-stair-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.76,
            1.0
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-east": {
        "axis": "y",
        "bbox": {
          "x": [
            23.759999999999998,
            24.0
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            17.759999999999998,
            18.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            0.24
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.0,
            0.24
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-east": {
        "axis": "y",
        "bbox": {
          "x": [
            18.02,
            18.26
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            14.020000000000001,
            14.26
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            3.7399999999999998,
            3.98
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-west": {
        "axis": "y",
        "bbox": {
          "x": [
            5.74,
            5.98
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-stair-east": {
        "axis": "y",
        "bbox": {
          "x": [
            2.5,
            2.74
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-stair-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.76,
            1.0
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      }
    }
  },
  "success": true
}
```

Source: [geometry-feedback.json](geometry-feedback.json)

## Metrics

### Design Brief Agent

```json
{
  "case_id": "3cd339b0be4fd872",
  "design_status": "ready",
  "evidence_class": "live",
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "parse_valid": true,
  "question_count": 0,
  "response_id": "4788f467-4e94-4ab2-b818-9f6f8513c5eb",
  "schema_semantic_valid": true,
  "semantic_repair": {
    "evidence_class": "live",
    "issues": [],
    "response_id": "63d31b9b-b2bc-45fa-9400-15d518b8e529",
    "status": "corrected",
    "valid": true
  },
  "stage": "design-brief",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 51470,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 30080,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 22540,
    "prompt_tokens": 22540,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    },
    "total_tokens": 74010
  }
}
```

Source: [design-brief/metrics.json](design-brief/metrics.json)

### BIM JSON Generator

```json
{
  "case_id": "3cd339b0be4fd872",
  "classification": "formal",
  "contract_status": "formal",
  "contract_valid": true,
  "evidence_class": "live",
  "generator_call_index": 1,
  "has_generation_feedback": false,
  "issue_count": 0,
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "parse_valid": true,
  "repaired_candidate_promoted": true,
  "response_id": "c71fd68d-5df7-4e56-91b3-444eb4937315",
  "stage": "generate",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 57611,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 23947,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 59758,
    "prompt_tokens": 59758,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    },
    "total_tokens": 117369
  }
}
```

Source: [generator/metrics.json](generator/metrics.json)

### Repair Route

```json
{
  "assessment_scope": {
    "geometry_feedback_supplied": false,
    "geometry_issue_count_basis": "supplied_feedback_only",
    "geometry_pass_certified": false,
    "interpretation": "This route assesses generator validation and only the geometry issues supplied to this invocation. Zero issues/no_repair_needed is not a geometry pass. Current compile/reopen/geometry gates remain authoritative."
  },
  "case_id": "3cd339b0be4fd872",
  "evidence_class": "deterministic-derived-no-call",
  "fact_delta_valid": null,
  "geometry_issue_count": 0,
  "prior_attempt_count": 0,
  "provider_call_count": 0,
  "repair_attempt_count": 1,
  "repair_diagnostic_count": 0,
  "repair_source_artifact": "invalid-candidate.json",
  "repaired_artifact": "repaired-candidate.json",
  "route": "repair_attempted",
  "source_document_kind": "invalid_formal",
  "source_document_path": "parsed-output.json",
  "source_generator_contract_valid": false,
  "source_generator_evidence_class": "live",
  "source_generator_response_id": "c71fd68d-5df7-4e56-91b3-444eb4937315",
  "stage": "repair",
  "valid": true
}
```

Source: [repair/metrics.json](repair/metrics.json)

### Audit Agent

```json
{
  "case_id": "3cd339b0be4fd872",
  "design_review_context_sha256": null,
  "evidence_class": "live",
  "issue_count": 0,
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "response_id": "e6ee79c7-ce98-4caf-96ae-eb3c91b95ae1",
  "route_decision": "accept",
  "route_owner_stage": "none",
  "schema_semantic_valid": true,
  "stage": "audit",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 9465,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 7524,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 1024,
    "prompt_cache_miss_tokens": 113253,
    "prompt_tokens": 114277,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 1024
    },
    "total_tokens": 123742
  },
  "valid": true
}
```

Source: [audit/metrics.json](audit/metrics.json)

## Source Sidecars

### Design Brief Agent

- [design-brief/input.txt](design-brief/input.txt)
- [design-brief/conversation.json](design-brief/conversation.json)
- [design-brief/prompt-rendered.md](design-brief/prompt-rendered.md)
- [design-brief/request.redacted.json](design-brief/request.redacted.json)
- [design-brief/response.raw.json](design-brief/response.raw.json)
- [design-brief/model-text.txt](design-brief/model-text.txt)
- [design-brief/design-brief.json](design-brief/design-brief.json)
- [design-brief/validation.json](design-brief/validation.json)
- [design-brief/metrics.json](design-brief/metrics.json)

### BIM JSON Generator

- [generator/prompt-rendered.md](generator/prompt-rendered.md)
- [generator/response.raw.json](generator/response.raw.json)
- [generator/model-text.txt](generator/model-text.txt)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [generator/metrics.json](generator/metrics.json)

### Repair Route

- [repair/route.json](repair/route.json)
- [repair/repair-attempts.json](repair/repair-attempts.json)
- [repair/metrics.json](repair/metrics.json)

### Audit Agent

- [audit/prompt-rendered.md](audit/prompt-rendered.md)
- [audit/response.raw.json](audit/response.raw.json)
- [audit/model-text.txt](audit/model-text.txt)
- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)
- [audit/metrics.json](audit/metrics.json)

### Generated IFC Gates

- [semantic-capabilities.json](semantic-capabilities.json)
- [semantic-coverage.json](semantic-coverage.json)
- [semantic-geometry-expectation.json](semantic-geometry-expectation.json)
- [expected-facts.json](expected-facts.json)
- [dynamic-gates.json](dynamic-gates.json)
- [gate-summary.json](gate-summary.json)
- [route-decision.json](route-decision.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-expectation.json](geometry-expectation.json)
- [geometry-feedback.json](geometry-feedback.json)
