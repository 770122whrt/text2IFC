# Phase 6.1 Live Mimo Run Report

Generated from trace sidecars. This report is not hand-authored evidence.

## Original Input

```text
请生成一栋三层的小型社区阅读活动楼，输出完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静阅览厅，三层是多功能活动厅，东侧为独立楼梯间。采用 warm-residential 协调风格，浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐。需要真实的窗框、玻璃面板、门框、门扇和楼梯踏步；本次不做光庭、家具、花草、机电、栏杆、复杂五金或外伸装饰。

室内净尺寸东西10米、南北8.4米，外墙厚200毫米。首层、二层、三层完成面标高分别为0、3150、6300毫米，每层净高3000毫米。地坪及两块层间楼板厚150毫米，顶面与所属层完成面齐平；平屋面底标高9300毫米、厚150毫米。地坪、楼板与屋面覆盖外墙外边界。二层和三层楼板各留一个真实穿透的楼梯洞口，不能用完整楼板封住楼梯。各层墙独立建模。

以首层室内西南角为原点，向东为X、向北为Y、向上为Z。每层西侧大厅净范围X=0～7600、Y=0～8400；分隔墙完整占X=7600～7800、Y=0～8400；楼梯间净范围X=7800～10000、Y=0～8400。三层分隔墙都保持这一完整长度，不按小平台的接邻长度缩短，也不重复建墙。每层分隔墙开一樘900宽、2100高的右单开门：首层及三层门中心距室内南边700毫米，二层距南边7650毫米；门底与本层完成面齐平。

两段直跑楼梯都位于X=8200～9400、Y=1500～6900，净宽1200毫米。第一段从首层南端向北升到二层北端，标高0到3150；第二段从二层北端反向向南升到三层南端，标高3150到6300。每段18个踢面、每个高175毫米，18个踏面、进深300毫米；两段分别属于出发楼层并连接上一层。二层及三层楼板洞口平面范围都为X=8000～9600、Y=1500～6900，分别穿透各自的150毫米楼板；屋面不留洞。二层北端Y=6900～8400为换向平台，三层南端Y=0～1500为到达平台。首层建大厅与整间楼梯间两个空间，二层建大厅与北端平台两个空间，三层建大厅与南端平台两个空间；平台的X范围都是7800～10000。共6个空间，不把楼梯洞口当成房间。

首层南墙主入口中心距室内西边3800毫米，宽1200、高2400，左单开，门底与首层地坪齐平。每层南墙两扇双竖面板窗，中心距室内西边分别为1700、5900毫米，宽1800、高1500、窗台高900。每层北墙一扇双竖面板窗，中心距西边3800毫米，宽2400、高1500、窗台高900。每层西墙一扇双竖面板窗，中心距南边4200毫米，宽1800、高1500、窗台高900。每层东墙一扇单面板窗，中心距南边4200毫米，宽900、高1800、窗台高600。窗台均从所属层完成面起算。共4樘门、15扇窗，门窗开口与名义宽高相同并穿透自己的宿主墙。

墙体物理材料为砖；地坪、两块层间楼板和屋面物理材料为混凝土。其他构件不指定物理材料，不要由木色或透明样式推断材料。未指定强度、耐火、承重、热工性能，也未要求共享Type，不要自动补属性或强制合并Type。如果有真实冲突请明确指出，不要悄悄改变尺寸、位置或关系。
```

Source: [design-brief/input.txt](design-brief/input.txt)

## Conversation

```json
[
  {
    "content": "请生成一栋三层的小型社区阅读活动楼，输出完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静阅览厅，三层是多功能活动厅，东侧为独立楼梯间。采用 warm-residential 协调风格，浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐。需要真实的窗框、玻璃面板、门框、门扇和楼梯踏步；本次不做光庭、家具、花草、机电、栏杆、复杂五金或外伸装饰。\n\n室内净尺寸东西10米、南北8.4米，外墙厚200毫米。首层、二层、三层完成面标高分别为0、3150、6300毫米，每层净高3000毫米。地坪及两块层间楼板厚150毫米，顶面与所属层完成面齐平；平屋面底标高9300毫米、厚150毫米。地坪、楼板与屋面覆盖外墙外边界。二层和三层楼板各留一个真实穿透的楼梯洞口，不能用完整楼板封住楼梯。各层墙独立建模。\n\n以首层室内西南角为原点，向东为X、向北为Y、向上为Z。每层西侧大厅净范围X=0～7600、Y=0～8400；分隔墙完整占X=7600～7800、Y=0～8400；楼梯间净范围X=7800～10000、Y=0～8400。三层分隔墙都保持这一完整长度，不按小平台的接邻长度缩短，也不重复建墙。每层分隔墙开一樘900宽、2100高的右单开门：首层及三层门中心距室内南边700毫米，二层距南边7650毫米；门底与本层完成面齐平。\n\n两段直跑楼梯都位于X=8200～9400、Y=1500～6900，净宽1200毫米。第一段从首层南端向北升到二层北端，标高0到3150；第二段从二层北端反向向南升到三层南端，标高3150到6300。每段18个踢面、每个高175毫米，18个踏面、进深300毫米；两段分别属于出发楼层并连接上一层。二层及三层楼板洞口平面范围都为X=8000～9600、Y=1500～6900，分别穿透各自的150毫米楼板；屋面不留洞。二层北端Y=6900～8400为换向平台，三层南端Y=0～1500为到达平台。首层建大厅与整间楼梯间两个空间，二层建大厅与北端平台两个空间，三层建大厅与南端平台两个空间；平台的X范围都是7800～10000。共6个空间，不把楼梯洞口当成房间。\n\n首层南墙主入口中心距室内西边3800毫米，宽1200、高2400，左单开，门底与首层地坪齐平。每层南墙两扇双竖面板窗，中心距室内西边分别为1700、5900毫米，宽1800、高1500、窗台高900。每层北墙一扇双竖面板窗，中心距西边3800毫米，宽2400、高1500、窗台高900。每层西墙一扇双竖面板窗，中心距南边4200毫米，宽1800、高1500、窗台高900。每层东墙一扇单面板窗，中心距南边4200毫米，宽900、高1800、窗台高600。窗台均从所属层完成面起算。共4樘门、15扇窗，门窗开口与名义宽高相同并穿透自己的宿主墙。\n\n墙体物理材料为砖；地坪、两块层间楼板和屋面物理材料为混凝土。其他构件不指定物理材料，不要由木色或透明样式推断材料。未指定强度、耐火、承重、热工性能，也未要求共享Type，不要自动补属性或强制合并Type。如果有真实冲突请明确指出，不要悄悄改变尺寸、位置或关系。",
    "question_ids": [],
    "role": "user",
    "turn_id": "turn-user-001"
  },
  {
    "content": "参考 IFC 中，一层通往二层的楼梯接近北端平台时，被上方反向梯段遮挡，局部净空为零。请确认是调整楼梯及关联布局，还是保留原要求并在 Audit 和报告中记录这个问题。",
    "question_ids": [
      "design-review-choice"
    ],
    "role": "assistant",
    "turn_id": "turn-assistant-002"
  },
  {
    "content": "我选择调整内部布局，不向外扩建。三层分隔墙均向西移动300毫米，保持200毫米厚，改为X=7300～7500、Y=0～8400。各层大厅净范围改为X=0～7300、Y=0～8400，楼梯间净范围改为X=7500～10000、Y=0～8400。第一段楼梯仍从南向北上升，平面改为X=7500～8700、Y=1500～6900；第二段仍从北向南上升，平面改为X=8800～10000、Y=1500～6900。两段仍各宽1200毫米，18个踢面高175毫米、18个踏面深300毫米，起止标高不变。二层楼板洞口改为X=7500～8700、Y=1500～6900；三层洞口改为X=8800～10000、Y=1500～6900，各自穿透所属楼板，不再保留原位置洞口。二层北端平台及三层南端平台的X范围均改为7500～10000，Y范围不变；首层楼梯间空间同样从X=7500开始。三樘分隔墙门随墙向西移动300毫米，南北位置、宽高及开启侧不变。建筑外轮廓、楼层标高、外墙门窗、材料、配色及其他原要求均不变。我接受每层大厅减少2.52平方米。请保留这次修订记录，Audit 仍须说明未做完整工程和规范审查。",
    "question_ids": [
      "design-review-choice"
    ],
    "role": "user",
    "turn_id": "turn-user-003"
  }
]
```

Source: [design-brief/conversation.json](design-brief/conversation.json)

## Design Brief Agent

- response_id: `922f6800-7e50-4f5e-88d7-334e16551dbc`
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

- response_id: `ded020da-9a46-4f9a-bac6-8e73e08a86b2`
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
- provider_call_count: `1`
- evidence_class: `live`

Source: [repair/route.json](repair/route.json)
Source: [repair/repair-attempts.json](repair/repair-attempts.json)
Source: [repair/metrics.json](repair/metrics.json)

## Audit Agent

- response_id: `86e2cd85-7465-4bf8-abb5-9a57fc4a44e8`
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


## 合理性问题与用户决定

以下为 Audit 的有限审查记录，技术／请求符合性通过不代表合理性或规范通过。
用户保留的已知问题仍然存在；要求修改也不等于已经独立验证修改成功。
[用户决定与参考证据](design-review-context.json) · [Audit 校验](audit/validation.json)

```json
{
  "concerns": [
    {
      "description": "参照 IFC 发现的缺陷：一层通往二层的楼梯接近二层北端平台时，被上方反向梯段遮挡，局部净空为零（两梯段共用同一平面）。用户在 turn-user-003 明确选择修订内部布局：三层分隔墙西移300mm 至 X=7300~7500，两梯段分列 X=7500~8700（第一段，南->北，0->3150）与 X=8800~10000（第二段，北->南，3150->6300），二层洞口改 X=7500~8700、三层洞口改 X=8800~10000。本次候选按该修订建模，两梯段平面已不重叠，参照缺陷不再是几何平面重叠的直接结果。但模型检查本身不构成独立工程或规范净空核算，且该候选当前未通过 IFC 编译/reopen 确定性 gate，因此不能判定为已解决，也不改判为候选几何错误。影响：北端楼梯行走净空在本次交付物中仍属未经独立核实、未闭合的保留风险。",
      "evidence_paths": [
        "design-review-context.json"
      ],
      "id": "reference-stair-walking-clearance",
      "status": "not_verified"
    }
  ],
  "limitations": [
    "未进行完整建筑规范审查。",
    "未进行独立净空、结构与疏散工程核算。"
  ],
  "scope": "limited_review_not_code_compliance"
}
```

## Semantic Coverage
Source: [semantic-capabilities.json](semantic-capabilities.json)
Source: [semantic-coverage.json](semantic-coverage.json)
```json
{
  "blocking_facts": [],
  "candidate_entity_count": 75,
  "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
  "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
  "case_id": "411166603facdde6",
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
      "value": "浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐；该风格与构件样式由主题及基础门窗模板承载，未要求按整构件数值颜色或透明度覆盖。"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/exterior_wall_thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/id",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "building-community-reading"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/interior_clear_extent_mm/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        0,
        10000
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/interior_clear_extent_mm/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        0,
        8400
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/name",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "小型社区阅读活动楼"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/x_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 10200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/x_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": -200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/y_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 8600
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/y_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": -200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline_polygon",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        [
          -200,
          -200
        ],
        [
          10200,
          -200
        ],
        [
          10200,
          8600
        ],
        [
          -200,
          8600
        ],
        [
          -200,
          -200
        ]
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/storey_count",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 3
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/coordinate_system/origin",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "首层室内西南角"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/coordinate_system/x_axis",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "east"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/coordinate_system/y_axis",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "north"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/coordinate_system/z_axis",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "up"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/coordinate_system/z_zero",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "首层完成面标高0"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/deliverable/file_policy",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "complete_ifc_file"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/deliverable/ifc_schema",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "IFC2X3"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/deliverable/units/length",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "MILLIMETRE"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/excluded_scope",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "光庭",
        "家具",
        "花草",
        "机电",
        "栏杆",
        "复杂五金",
        "外伸装饰"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/floor_slabs",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "bounds": {
            "x": [
              -200,
              10200
            ],
            "y": [
              -200,
              8600
            ]
          },
          "id": "floor-slab-storey-1",
          "name": "首层地坪",
          "openings": [],
          "polygon": [
            [
              -200,
              -200
            ],
            [
              10200,
              -200
            ],
            [
              10200,
              8600
            ],
            [
              -200,
              8600
            ],
            [
              -200,
              -200
            ]
          ],
          "storey": "storey-1",
          "thickness_mm": 150,
          "top_elevation_mm": 0
        },
        {
          "bounds": {
            "x": [
              -200,
              10200
            ],
            "y": [
              -200,
              8600
            ]
          },
          "id": "floor-slab-storey-2",
          "name": "二层楼板",
          "opening": {
            "bounds": {
              "x": [
                7500,
                8700
              ],
              "y": [
                1500,
                6900
              ]
            },
            "id": "slab-opening-storey-2",
            "purpose": "stair-1 penetration",
            "real_penetration": true
          },
          "polygon": [
            [
              -200,
              -200
            ],
            [
              10200,
              -200
            ],
            [
              10200,
              8600
            ],
            [
              -200,
              8600
            ],
            [
              -200,
              -200
            ]
          ],
          "storey": "storey-2",
          "thickness_mm": 150,
          "top_elevation_mm": 3150
        },
        {
          "bounds": {
            "x": [
              -200,
              10200
            ],
            "y": [
              -200,
              8600
            ]
          },
          "id": "floor-slab-storey-3",
          "name": "三层楼板",
          "opening": {
            "bounds": {
              "x": [
                8800,
                10000
              ],
              "y": [
                1500,
                6900
              ]
            },
            "id": "slab-opening-storey-3",
            "purpose": "stair-2 penetration",
            "real_penetration": true
          },
          "polygon": [
            [
              -200,
              -200
            ],
            [
              10200,
              -200
            ],
            [
              10200,
              8600
            ],
            [
              -200,
              8600
            ],
            [
              -200,
              -200
            ]
          ],
          "storey": "storey-3",
          "thickness_mm": 150,
          "top_elevation_mm": 6300
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bottom_elevation_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 9300
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bounds/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        -200,
        10200
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bounds/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        -200,
        8600
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/id",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "roof-slab"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/name",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "平屋面"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/openings",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": []
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/polygon",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        [
          -200,
          -200
        ],
        [
          10200,
          -200
        ],
        [
          10200,
          8600
        ],
        [
          -200,
          8600
        ],
        [
          -200,
          -200
        ]
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 150
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_requirements",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "entity_id": "storey-1-wall-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-west",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-east",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-interior-divider",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-west",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-east",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-interior-divider",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-west",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-east",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-interior-divider",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "floor-slab-storey-1",
          "material": {
            "kind": "single_material",
            "name": "Concrete"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "floor-slab-storey-2",
          "material": {
            "kind": "single_material",
            "name": "Concrete"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "floor-slab-storey-3",
          "material": {
            "kind": "single_material",
            "name": "Concrete"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "roof-slab",
          "material": {
            "kind": "single_material",
            "name": "Concrete"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "door-storey-1-main-entrance",
          "material": {},
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "door-storey-1-divider",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "door-storey-2-divider",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "door-storey-3-divider",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-south-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-south-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-north",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-west",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-east",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-south-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-south-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-north",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-west",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-east",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-south-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-south-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-north",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-west",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-east",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          }
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
      "value": "not_specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/semantic_review/material/source_turns",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "turn-user-001",
        "turn-user-003"
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
      "value": "not_specified"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/stairs",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "bounds": {
            "x": [
              7500,
              8700
            ],
            "y": [
              1500,
              6900
            ]
          },
          "end_elevation_mm": 3150,
          "from_storey": "storey-1",
          "id": "stair-1",
          "number_of_risers": 18,
          "number_of_treads": 18,
          "opening_bounds": {
            "x": [
              7500,
              8700
            ],
            "y": [
              1500,
              6900
            ]
          },
          "riser_height_mm": 175,
          "run_direction": "south_to_north",
          "start_elevation_mm": 0,
          "to_storey": "storey-2",
          "tread_depth_mm": 300,
          "width_mm": 1200
        },
        {
          "bounds": {
            "x": [
              8800,
              10000
            ],
            "y": [
              1500,
              6900
            ]
          },
          "end_elevation_mm": 6300,
          "from_storey": "storey-2",
          "id": "stair-2",
          "number_of_risers": 18,
          "number_of_treads": 18,
          "opening_bounds": {
            "x": [
              8800,
              10000
            ],
            "y": [
              1500,
              6900
            ]
          },
          "riser_height_mm": 175,
          "run_direction": "north_to_south",
          "start_elevation_mm": 3150,
          "to_storey": "storey-3",
          "tread_depth_mm": 300,
          "width_mm": 1200
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
              "bottom_elevation_mm": 0,
              "center_distance_mm": 3800,
              "center_global_mm": [
                3800,
                -100
              ],
              "center_reference": "interior_west_edge",
              "handing": "left_single",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-south",
              "id": "door-storey-1-main-entrance",
              "name": "南墙主入口",
              "sill_height_mm": 0,
              "template_id": "door-left",
              "width_mm": 1200
            },
            {
              "bottom_elevation_mm": 0,
              "center_distance_mm": 700,
              "center_global_mm": [
                7400,
                700
              ],
              "center_reference": "interior_south_edge",
              "handing": "right_single",
              "height_mm": 2100,
              "host_wall": "storey-1-wall-interior-divider",
              "id": "door-storey-1-divider",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "width_mm": 900
            }
          ],
          "elevation_mm": 0,
          "id": "storey-1",
          "name": "首层",
          "net_height_mm": 3000,
          "spaces": [
            {
              "bounds": {
                "x": [
                  0,
                  7300
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-1-space-hall",
              "name": "接待阅览厅大厅"
            },
            {
              "bounds": {
                "x": [
                  7500,
                  10000
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-1-space-stairwell",
              "name": "整间楼梯间"
            }
          ],
          "use": "接待阅览厅",
          "walls": {
            "exterior": [
              {
                "bounds": {
                  "x": [
                    -200,
                    10200
                  ],
                  "y": [
                    -200,
                    0
                  ]
                },
                "height_mm": 3000,
                "id": "storey-1-wall-south",
                "side": "south",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    -200,
                    10200
                  ],
                  "y": [
                    8400,
                    8600
                  ]
                },
                "height_mm": 3000,
                "id": "storey-1-wall-north",
                "side": "north",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    -200,
                    0
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "height_mm": 3000,
                "id": "storey-1-wall-west",
                "side": "west",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    10000,
                    10200
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "height_mm": 3000,
                "id": "storey-1-wall-east",
                "side": "east",
                "thickness_mm": 200
              }
            ],
            "interior": [
              {
                "bounds": {
                  "x": [
                    7300,
                    7500
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "connects": [
                  "storey-1-space-hall",
                  "storey-1-space-stairwell"
                ],
                "duplicate_policy": "single_wall_no_duplicate",
                "height_mm": 3000,
                "id": "storey-1-wall-interior-divider",
                "length_policy": "full_length_no_shortening",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_distance_mm": 1700,
              "center_global_mm": [
                1700,
                -100
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-window-south-1",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 5900,
              "center_global_mm": [
                5900,
                -100
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-window-south-2",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 3800,
              "center_global_mm": [
                3800,
                8500
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-1-wall-north",
              "id": "storey-1-window-north",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 2400
            },
            {
              "center_distance_mm": 4200,
              "center_global_mm": [
                -100,
                4200
              ],
              "center_reference": "interior_south_edge",
              "height_mm": 1500,
              "host_wall": "storey-1-wall-west",
              "id": "storey-1-window-west",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 4200,
              "center_global_mm": [
                10100,
                4200
              ],
              "center_reference": "interior_south_edge",
              "height_mm": 1800,
              "host_wall": "storey-1-wall-east",
              "id": "storey-1-window-east",
              "panel_layout": "single_panel",
              "sill_height_mm": 600,
              "template_id": "window-single",
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "bottom_elevation_mm": 3150,
              "center_distance_mm": 7650,
              "center_global_mm": [
                7400,
                7650
              ],
              "center_reference": "interior_south_edge",
              "handing": "right_single",
              "height_mm": 2100,
              "host_wall": "storey-2-wall-interior-divider",
              "id": "door-storey-2-divider",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "width_mm": 900
            }
          ],
          "elevation_mm": 3150,
          "id": "storey-2",
          "name": "二层",
          "net_height_mm": 3000,
          "spaces": [
            {
              "bounds": {
                "x": [
                  0,
                  7300
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-2-space-hall",
              "name": "安静阅览厅大厅"
            },
            {
              "bounds": {
                "x": [
                  7500,
                  10000
                ],
                "y": [
                  6900,
                  8400
                ]
              },
              "id": "storey-2-space-landing-north",
              "name": "北端换向平台"
            }
          ],
          "use": "安静阅览厅",
          "walls": {
            "exterior": [
              {
                "bounds": {
                  "x": [
                    -200,
                    10200
                  ],
                  "y": [
                    -200,
                    0
                  ]
                },
                "height_mm": 3000,
                "id": "storey-2-wall-south",
                "side": "south",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    -200,
                    10200
                  ],
                  "y": [
                    8400,
                    8600
                  ]
                },
                "height_mm": 3000,
                "id": "storey-2-wall-north",
                "side": "north",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    -200,
                    0
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "height_mm": 3000,
                "id": "storey-2-wall-west",
                "side": "west",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    10000,
                    10200
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "height_mm": 3000,
                "id": "storey-2-wall-east",
                "side": "east",
                "thickness_mm": 200
              }
            ],
            "interior": [
              {
                "bounds": {
                  "x": [
                    7300,
                    7500
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "connects": [
                  "storey-2-space-hall",
                  "storey-2-space-landing-north"
                ],
                "duplicate_policy": "single_wall_no_duplicate",
                "height_mm": 3000,
                "id": "storey-2-wall-interior-divider",
                "length_policy": "full_length_no_shortening",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_distance_mm": 1700,
              "center_global_mm": [
                1700,
                -100
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "storey-2-window-south-1",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 5900,
              "center_global_mm": [
                5900,
                -100
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "storey-2-window-south-2",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 3800,
              "center_global_mm": [
                3800,
                8500
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-2-wall-north",
              "id": "storey-2-window-north",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 2400
            },
            {
              "center_distance_mm": 4200,
              "center_global_mm": [
                -100,
                4200
              ],
              "center_reference": "interior_south_edge",
              "height_mm": 1500,
              "host_wall": "storey-2-wall-west",
              "id": "storey-2-window-west",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 4200,
              "center_global_mm": [
                10100,
                4200
              ],
              "center_reference": "interior_south_edge",
              "height_mm": 1800,
              "host_wall": "storey-2-wall-east",
              "id": "storey-2-window-east",
              "panel_layout": "single_panel",
              "sill_height_mm": 600,
              "template_id": "window-single",
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "bottom_elevation_mm": 6300,
              "center_distance_mm": 700,
              "center_global_mm": [
                7400,
                700
              ],
              "center_reference": "interior_south_edge",
              "handing": "right_single",
              "height_mm": 2100,
              "host_wall": "storey-3-wall-interior-divider",
              "id": "door-storey-3-divider",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "width_mm": 900
            }
          ],
          "elevation_mm": 6300,
          "id": "storey-3",
          "name": "三层",
          "net_height_mm": 3000,
          "spaces": [
            {
              "bounds": {
                "x": [
                  0,
                  7300
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-3-space-hall",
              "name": "多功能活动厅大厅"
            },
            {
              "bounds": {
                "x": [
                  7500,
                  10000
                ],
                "y": [
                  0,
                  1500
                ]
              },
              "id": "storey-3-space-landing-south",
              "name": "南端到达平台"
            }
          ],
          "use": "多功能活动厅",
          "walls": {
            "exterior": [
              {
                "bounds": {
                  "x": [
                    -200,
                    10200
                  ],
                  "y": [
                    -200,
                    0
                  ]
                },
                "height_mm": 3000,
                "id": "storey-3-wall-south",
                "side": "south",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    -200,
                    10200
                  ],
                  "y": [
                    8400,
                    8600
                  ]
                },
                "height_mm": 3000,
                "id": "storey-3-wall-north",
                "side": "north",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    -200,
                    0
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "height_mm": 3000,
                "id": "storey-3-wall-west",
                "side": "west",
                "thickness_mm": 200
              },
              {
                "bounds": {
                  "x": [
                    10000,
                    10200
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "height_mm": 3000,
                "id": "storey-3-wall-east",
                "side": "east",
                "thickness_mm": 200
              }
            ],
            "interior": [
              {
                "bounds": {
                  "x": [
                    7300,
                    7500
                  ],
                  "y": [
                    0,
                    8400
                  ]
                },
                "connects": [
                  "storey-3-space-hall",
                  "storey-3-space-landing-south"
                ],
                "duplicate_policy": "single_wall_no_duplicate",
                "height_mm": 3000,
                "id": "storey-3-wall-interior-divider",
                "length_policy": "full_length_no_shortening",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_distance_mm": 1700,
              "center_global_mm": [
                1700,
                -100
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-3-wall-south",
              "id": "storey-3-window-south-1",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 5900,
              "center_global_mm": [
                5900,
                -100
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-3-wall-south",
              "id": "storey-3-window-south-2",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 3800,
              "center_global_mm": [
                3800,
                8500
              ],
              "center_reference": "interior_west_edge",
              "height_mm": 1500,
              "host_wall": "storey-3-wall-north",
              "id": "storey-3-window-north",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 2400
            },
            {
              "center_distance_mm": 4200,
              "center_global_mm": [
                -100,
                4200
              ],
              "center_reference": "interior_south_edge",
              "height_mm": 1500,
              "host_wall": "storey-3-wall-west",
              "id": "storey-3-window-west",
              "panel_layout": "double_vertical_panels",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_distance_mm": 4200,
              "center_global_mm": [
                10100,
                4200
              ],
              "center_reference": "interior_south_edge",
              "height_mm": 1800,
              "host_wall": "storey-3-wall-east",
              "id": "storey-3-window-east",
              "panel_layout": "single_panel",
              "sill_height_mm": 600,
              "template_id": "window-single",
              "width_mm": 900
            }
          ]
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/units/length",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "MILLIMETRE"
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
  "issues": [
    {
      "code": "COMPILE_REOPEN_FAILED",
      "message": "IFC compilation or reopen verification failed.",
      "path": "/output.ifc"
    }
  ],
  "metrics": {},
  "success": false
}
```

Source: [geometry-feedback.json](geometry-feedback.json)

## Metrics

### Design Brief Agent

```json
{
  "case_id": "411166603facdde6",
  "design_status": "ready",
  "evidence_class": "live",
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "parse_valid": true,
  "question_count": 0,
  "response_id": "922f6800-7e50-4f5e-88d7-334e16551dbc",
  "schema_semantic_valid": true,
  "stage": "design-brief",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 29366,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 16769,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 18218,
    "prompt_tokens": 18218,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    },
    "total_tokens": 47584
  }
}
```

Source: [design-brief/metrics.json](design-brief/metrics.json)

### BIM JSON Generator

```json
{
  "case_id": "411166603facdde6",
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
  "response_id": "ded020da-9a46-4f9a-bac6-8e73e08a86b2",
  "stage": "generate",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 40195,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 25207,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 2176,
    "prompt_cache_miss_tokens": 38686,
    "prompt_tokens": 40862,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 2176
    },
    "total_tokens": 81057
  }
}
```

Source: [generator/metrics.json](generator/metrics.json)

### Repair Route

```json
{
  "case_id": "411166603facdde6",
  "evidence_class": "live",
  "fact_delta_valid": true,
  "geometry_issue_count": 0,
  "prior_attempt_count": 0,
  "provider_call_count": 1,
  "repair_attempt_count": 1,
  "repair_diagnostic_count": 0,
  "repair_source_artifact": "invalid-candidate.json",
  "repaired_artifact": "repaired-candidate.json",
  "route": "repair_attempted",
  "source_document_kind": "invalid_formal",
  "source_document_path": "parsed-output.json",
  "source_generator_contract_valid": false,
  "source_generator_evidence_class": "live",
  "source_generator_response_id": "ded020da-9a46-4f9a-bac6-8e73e08a86b2",
  "stage": "repair",
  "valid": true
}
```

Source: [repair/metrics.json](repair/metrics.json)

### Audit Agent

```json
{
  "case_id": "411166603facdde6",
  "design_review_context_sha256": "8a5f6b38e95e683636a323f90d2c3e137975bd00637e403edcea5e74a2281afc",
  "evidence_class": "live",
  "issue_count": 0,
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "response_id": "86e2cd85-7465-4bf8-abb5-9a57fc4a44e8",
  "route_decision": "generator_regeneration_required",
  "route_owner_stage": "generator",
  "schema_semantic_valid": true,
  "stage": "audit",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 9972,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 8988,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 3328,
    "prompt_cache_miss_tokens": 42319,
    "prompt_tokens": 45647,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 3328
    },
    "total_tokens": 55619
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
