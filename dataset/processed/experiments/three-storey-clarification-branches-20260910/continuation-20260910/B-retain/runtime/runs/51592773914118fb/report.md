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
    "content": "我已知悉两段反向楼梯在同一平面相互遮挡，接近二层北端平台处局部净空为零，无法作为正常通行楼梯使用。本分支用于忠实建模和问题展示，请仍严格按原始请求中的尺寸、位置、方向、洞口与关系生成，不要移动楼梯或修改大厅、分隔墙、门窗来消除这个问题。请在 Audit 和交付报告中保留问题位置、影响以及我的保留决定，不得写成合理性或建筑规范检查通过。其他原要求不变。",
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

- response_id: `199c507b-6cc2-4b49-a741-4d23f3aee7c5`
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

- response_id: `c5a38d05-4e9a-4724-a6a1-69da4696519f`
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

- route: `no_repair_needed`
- provider_call_count: `0`
- evidence_class: `live-derived-no-call`

Source: [repair/route.json](repair/route.json)
Source: [repair/repair-attempts.json](repair/repair-attempts.json)
Source: [repair/metrics.json](repair/metrics.json)

## Audit Agent

- response_id: `1b95aa8c-0696-4efc-9d58-d15056b67f6b`
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
      "description": "两段反向直跑楼梯共用同一平面范围 X=8200～9400、Y=1500～6900：第一段自首层南端向北升至标高 3150 抵达二层北端换向平台，其正上方为反向的第二段梯段（标高 3150～6300），因此接近二层北端换向平台（Y=6900～8400）处局部净空为零，该位置不能作为正常通行楼梯使用（通行缺陷）。用户在 turn-user-003 已明确知悉该缺陷并选择保留，要求严格按原始请求的尺寸、位置、方向、洞口与关系生成，不移动楼梯，不修改大厅、分隔墙、门窗来消除问题；本模型仅为忠实建模与问题展示。此处仅记录该保留问题的位置与影响，不表示合理性或建筑规范检查通过，也不作为触发重复几何修复的候选错误。",
      "evidence_paths": [
        "design-review-context.json"
      ],
      "id": "reference-stair-walking-clearance",
      "status": "retained_known_issue"
    }
  ],
  "limitations": [
    "未进行完整建筑规范审查。",
    "保留问题的判定基于用户决定与参考审查上下文，不构成对当前 IFC 通行净空、疏散或结构合理性的验证。",
    "本审计仅确认确定性 gate 与语义证据的一致性，不替代独立工程复核。"
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
  "case_id": "51592773914118fb",
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
          "id": "floor-slab-ground",
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
          "opening": {
            "bounds": {
              "x": [
                8000,
                9600
              ],
              "y": [
                1500,
                6900
              ]
            },
            "id": "floor-slab-storey-2-opening-stair"
          },
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
          "opening": {
            "bounds": {
              "x": [
                8000,
                9600
              ],
              "y": [
                1500,
                6900
              ]
            },
            "id": "floor-slab-storey-3-opening-stair"
          },
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
      "path": "/known_facts/roof_slab/openings",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": []
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
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-north",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-west",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-east",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-partition",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-south",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-north",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-west",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-east",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-partition",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-south",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-north",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-west",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-east",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-partition",
          "material": {
            "kind": "single_material",
            "name": "砖"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "floor-slab-ground",
          "material": {
            "kind": "single_material",
            "name": "混凝土"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "floor-slab-storey-2",
          "material": {
            "kind": "single_material",
            "name": "混凝土"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "floor-slab-storey-3",
          "material": {
            "kind": "single_material",
            "name": "混凝土"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "roof-slab",
          "material": {
            "kind": "single_material",
            "name": "混凝土"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-door-main-entrance",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-door-partition",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-door-partition",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-door-partition",
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
      "path": "/known_facts/stairs",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "bounds": {
            "x": [
              8200,
              9400
            ],
            "y": [
              1500,
              6900
            ]
          },
          "end_elevation_mm": 3150,
          "from_storey": "storey-1",
          "id": "stair-1-flight",
          "name": "第一段直跑楼梯",
          "number_of_risers": 18,
          "number_of_treads": 18,
          "opening_bounds": {
            "x": [
              8000,
              9600
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
              8200,
              9400
            ],
            "y": [
              1500,
              6900
            ]
          },
          "end_elevation_mm": 6300,
          "from_storey": "storey-2",
          "id": "stair-2-flight",
          "name": "第二段直跑楼梯（反向）",
          "number_of_risers": 18,
          "number_of_treads": 18,
          "opening_bounds": {
            "x": [
              8000,
              9600
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
              "center_global_mm": [
                3800,
                -100
              ],
              "height_mm": 2400,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-door-main-entrance",
              "name": "南墙主入口",
              "panels": "single",
              "sill_height_mm": 0,
              "swing": "left",
              "width_mm": 1200
            },
            {
              "center_global_mm": [
                7700,
                700
              ],
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition",
              "id": "storey-1-door-partition",
              "name": "分隔墙门",
              "panels": "single",
              "sill_height_mm": 0,
              "swing": "right",
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
                  7600
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-1-space-hall",
              "name": "接待阅览厅"
            },
            {
              "bounds": {
                "x": [
                  7800,
                  10000
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-1-space-stairwell",
              "name": "楼梯间"
            }
          ],
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
                    7600,
                    7800
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
                "height_mm": 3000,
                "id": "storey-1-wall-partition",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                1700,
                -100
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-window-south-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                5900,
                -100
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-window-south-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                3800,
                8500
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-north",
              "id": "storey-1-window-north",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 2400
            },
            {
              "center_global_mm": [
                -100,
                4200
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-west",
              "id": "storey-1-window-west",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10100,
                4200
              ],
              "height_mm": 1800,
              "host_wall": "storey-1-wall-east",
              "id": "storey-1-window-east",
              "panels": "single",
              "sill_height_mm": 600,
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "center_global_mm": [
                7700,
                7650
              ],
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition",
              "id": "storey-2-door-partition",
              "name": "分隔墙门",
              "panels": "single",
              "sill_height_mm": 0,
              "swing": "right",
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
                  7600
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-2-space-hall",
              "name": "安静阅览厅"
            },
            {
              "bounds": {
                "x": [
                  7800,
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
                    7600,
                    7800
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
                "height_mm": 3000,
                "id": "storey-2-wall-partition",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                1700,
                -100
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "storey-2-window-south-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                5900,
                -100
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "storey-2-window-south-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                3800,
                8500
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-north",
              "id": "storey-2-window-north",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 2400
            },
            {
              "center_global_mm": [
                -100,
                4200
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-west",
              "id": "storey-2-window-west",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10100,
                4200
              ],
              "height_mm": 1800,
              "host_wall": "storey-2-wall-east",
              "id": "storey-2-window-east",
              "panels": "single",
              "sill_height_mm": 600,
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "center_global_mm": [
                7700,
                700
              ],
              "height_mm": 2100,
              "host_wall": "storey-3-wall-partition",
              "id": "storey-3-door-partition",
              "name": "分隔墙门",
              "panels": "single",
              "sill_height_mm": 0,
              "swing": "right",
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
                  7600
                ],
                "y": [
                  0,
                  8400
                ]
              },
              "id": "storey-3-space-hall",
              "name": "多功能活动厅"
            },
            {
              "bounds": {
                "x": [
                  7800,
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
                    7600,
                    7800
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
                "height_mm": 3000,
                "id": "storey-3-wall-partition",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                1700,
                -100
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-south",
              "id": "storey-3-window-south-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                5900,
                -100
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-south",
              "id": "storey-3-window-south-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                3800,
                8500
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-north",
              "id": "storey-3-window-north",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 2400
            },
            {
              "center_global_mm": [
                -100,
                4200
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-west",
              "id": "storey-3-window-west",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10100,
                4200
              ],
              "height_mm": 1800,
              "host_wall": "storey-3-wall-east",
              "id": "storey-3-window-east",
              "panels": "single",
              "sill_height_mm": 600,
              "width_mm": 900
            }
          ]
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
  "issues": [
    {
      "code": "MISSING_STAIR_OPENING",
      "entity_ids": [
        "floor-slab-storey-2-opening-stair"
      ],
      "message": "No opening satisfies the frozen identity/host/bounds obligation.",
      "path": "/floor_openings/floor-slab-storey-2-opening-stair",
      "source_fact_refs": [
        "/known_facts/floor_slabs/1/opening"
      ]
    },
    {
      "code": "MISSING_STAIR_OPENING",
      "entity_ids": [
        "floor-slab-storey-3-opening-stair"
      ],
      "message": "No opening satisfies the frozen identity/host/bounds obligation.",
      "path": "/floor_openings/floor-slab-storey-3-opening-stair",
      "source_fact_refs": [
        "/known_facts/floor_slabs/2/opening"
      ]
    },
    {
      "code": "MISSING_STAIR_FLIGHT",
      "entity_ids": [
        "stair-1-flight",
        "stair-flight-1-flight"
      ],
      "message": "Expected stair 'stair-1-flight' has no checkable IfcStairFlight.",
      "path": "/stairs/stair-1-flight",
      "source_fact_refs": [
        "/known_facts/stairs/0"
      ]
    },
    {
      "code": "MISSING_STAIR_FLIGHT",
      "entity_ids": [
        "stair-2-flight",
        "stair-flight-2-flight"
      ],
      "message": "Expected stair 'stair-2-flight' has no checkable IfcStairFlight.",
      "path": "/stairs/stair-2-flight",
      "source_fact_refs": [
        "/known_facts/stairs/1"
      ]
    }
  ],
  "metrics": {
    "case_id": "51592773914118fb",
    "floor_openings": {},
    "products": {},
    "roof": {
      "roof-slab": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            9.3,
            9.450000000000001
          ]
        },
        "ifc_class": "IfcRoof"
      }
    },
    "slabs": {
      "floor-slab-ground": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            -0.15,
            0.0
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "floor-slab-storey-2": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            3.0,
            3.15
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "floor-slab-storey-3": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            6.150000000000001,
            6.300000000000002
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "spaces": {
      "space-storey-1-storey-1-space-hall": {
        "bbox": {
          "x": [
            0.0,
            7.6000000000000005
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-stairwell": {
        "bbox": {
          "x": [
            7.8,
            10.0
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-hall": {
        "bbox": {
          "x": [
            0.0,
            7.6000000000000005
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-landing-north": {
        "bbox": {
          "x": [
            7.8,
            10.0
          ],
          "y": [
            6.9,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-storey-3-space-hall": {
        "bbox": {
          "x": [
            0.0,
            7.6000000000000005
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-storey-3-space-landing-south": {
        "bbox": {
          "x": [
            7.8,
            10.0
          ],
          "y": [
            0.0,
            1.5
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcSpace"
      }
    },
    "stairs": {},
    "wall_set_convention": "primary",
    "walls": {
      "wall-storey-1-storey-1-wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            10.0,
            10.2
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-1-storey-1-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            8.4,
            8.6
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-1-storey-1-wall-partition": {
        "axis": "y",
        "bbox": {
          "x": [
            7.6000000000000005,
            7.8
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-1-storey-1-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.2,
            0.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-1-storey-1-wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.2,
            0.0
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-2-storey-2-wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            10.0,
            10.2
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-2-storey-2-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            8.4,
            8.6
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-2-storey-2-wall-partition": {
        "axis": "y",
        "bbox": {
          "x": [
            7.6000000000000005,
            7.8
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-2-storey-2-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.2,
            0.0
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-2-storey-2-wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.2,
            0.0
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-3-storey-3-wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            10.0,
            10.2
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-3-storey-3-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            8.4,
            8.6
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-3-storey-3-wall-partition": {
        "axis": "y",
        "bbox": {
          "x": [
            7.6000000000000005,
            7.8
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-3-storey-3-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.2,
            0.0
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-storey-3-storey-3-wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.2,
            0.0
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWall"
      }
    }
  },
  "success": false
}
```

Source: [geometry-feedback.json](geometry-feedback.json)

## Revision and ChangeSet History

- evidence_status: `bound`
- revision_id: `revision-01`
- candidate_hash: `sha256:9c687f89f5c1c2cb71c30768ee60131e8173c4863125ffc49f9348d92a2e5c2e`
- expected_facts_hash: `sha256:f407589f213b63a92e416535c7844fe9e042161160335e5ff8e7a61926651a13`
- changed_ids: `['stair-flight-1', 'stair-flight-2']`
- dependency_ids: `['aggregate-stair-1', 'aggregate-stair-2', 'void-floor-slab-storey-2-opening-stair', 'void-floor-slab-storey-3-opening-stair']`
- source_issue_ids: `['issue_audit_0001_01', 'issue_audit_0001_02', 'issue_audit_0001_03', 'issue_audit_0001_04', 'issue_audit_0002_01', 'issue_audit_0002_02', 'issue_audit_0002_03', 'issue_audit_0002_04', 'issue_deterministic_gate_0001', 'issue_deterministic_gate_0002']`

### Preservation

```json
{
  "changed_ids": [
    "stair-flight-1",
    "stair-flight-2"
  ],
  "dependency_ids": [
    "aggregate-stair-1",
    "aggregate-stair-2",
    "void-floor-slab-storey-2-opening-stair",
    "void-floor-slab-storey-3-opening-stair"
  ],
  "forbidden_drift_ids": [],
  "schema_version": "text2ifc/component-preservation/1.0",
  "unchanged_ids": [
    "aggregate-stair-1",
    "aggregate-stair-2",
    "building-1",
    "door-storey-1-storey-1-door-main-entrance",
    "door-storey-1-storey-1-door-partition",
    "door-storey-2-storey-2-door-partition",
    "door-storey-3-storey-3-door-partition",
    "fill-storey-1-door-main-entrance",
    "fill-storey-1-door-partition",
    "fill-storey-1-window-east",
    "fill-storey-1-window-north",
    "fill-storey-1-window-south-1",
    "fill-storey-1-window-south-2",
    "fill-storey-1-window-west",
    "fill-storey-2-door-partition",
    "fill-storey-2-window-east",
    "fill-storey-2-window-north",
    "fill-storey-2-window-south-1",
    "fill-storey-2-window-south-2",
    "fill-storey-2-window-west",
    "fill-storey-3-door-partition",
    "fill-storey-3-window-east",
    "fill-storey-3-window-north",
    "fill-storey-3-window-south-1",
    "fill-storey-3-window-south-2",
    "fill-storey-3-window-west",
    "floor-slab-ground",
    "floor-slab-storey-2",
    "floor-slab-storey-3",
    "opening-floor-slab-storey-2-opening-stair",
    "opening-floor-slab-storey-3-opening-stair",
    "opening-storey-1-door-main-entrance",
    "opening-storey-1-door-partition",
    "opening-storey-1-window-east",
    "opening-storey-1-window-north",
    "opening-storey-1-window-south-1",
    "opening-storey-1-window-south-2",
    "opening-storey-1-window-west",
    "opening-storey-2-door-partition",
    "opening-storey-2-window-east",
    "opening-storey-2-window-north",
    "opening-storey-2-window-south-1",
    "opening-storey-2-window-south-2",
    "opening-storey-2-window-west",
    "opening-storey-3-door-partition",
    "opening-storey-3-window-east",
    "opening-storey-3-window-north",
    "opening-storey-3-window-south-1",
    "opening-storey-3-window-south-2",
    "opening-storey-3-window-west",
    "project-1",
    "roof-slab",
    "site-1",
    "space-storey-1-storey-1-space-hall",
    "space-storey-1-storey-1-space-stairwell",
    "space-storey-2-storey-2-space-hall",
    "space-storey-2-storey-2-space-landing-north",
    "space-storey-3-storey-3-space-hall",
    "space-storey-3-storey-3-space-landing-south",
    "stair-1",
    "stair-2",
    "storey-1",
    "storey-2",
    "storey-3",
    "void-floor-slab-storey-2-opening-stair",
    "void-floor-slab-storey-3-opening-stair",
    "void-storey-1-door-main-entrance",
    "void-storey-1-door-partition",
    "void-storey-1-window-east",
    "void-storey-1-window-north",
    "void-storey-1-window-south-1",
    "void-storey-1-window-south-2",
    "void-storey-1-window-west",
    "void-storey-2-door-partition",
    "void-storey-2-window-east",
    "void-storey-2-window-north",
    "void-storey-2-window-south-1",
    "void-storey-2-window-south-2",
    "void-storey-2-window-west",
    "void-storey-3-door-partition",
    "void-storey-3-window-east",
    "void-storey-3-window-north",
    "void-storey-3-window-south-1",
    "void-storey-3-window-south-2",
    "void-storey-3-window-west",
    "wall-storey-1-storey-1-wall-east",
    "wall-storey-1-storey-1-wall-north",
    "wall-storey-1-storey-1-wall-partition",
    "wall-storey-1-storey-1-wall-south",
    "wall-storey-1-storey-1-wall-west",
    "wall-storey-2-storey-2-wall-east",
    "wall-storey-2-storey-2-wall-north",
    "wall-storey-2-storey-2-wall-partition",
    "wall-storey-2-storey-2-wall-south",
    "wall-storey-2-storey-2-wall-west",
    "wall-storey-3-storey-3-wall-east",
    "wall-storey-3-storey-3-wall-north",
    "wall-storey-3-storey-3-wall-partition",
    "wall-storey-3-storey-3-wall-south",
    "wall-storey-3-storey-3-wall-west",
    "window-storey-1-storey-1-window-east",
    "window-storey-1-storey-1-window-north",
    "window-storey-1-storey-1-window-south-1",
    "window-storey-1-storey-1-window-south-2",
    "window-storey-1-storey-1-window-west",
    "window-storey-2-storey-2-window-east",
    "window-storey-2-storey-2-window-north",
    "window-storey-2-storey-2-window-south-1",
    "window-storey-2-storey-2-window-south-2",
    "window-storey-2-storey-2-window-west",
    "window-storey-3-storey-3-window-east",
    "window-storey-3-storey-3-window-north",
    "window-storey-3-storey-3-window-south-1",
    "window-storey-3-storey-3-window-south-2",
    "window-storey-3-storey-3-window-west"
  ],
  "unrelated_component_count": 105,
  "unrelated_component_preservation_rate": 1.0
}
```

### ChangeSet 1

- changeset_id: `changeset-revision-01-stair-flight-name-storey-alignment`
- source_issue_ids: `['issue_audit_0001_01', 'issue_audit_0001_02', 'issue_audit_0001_03', 'issue_audit_0001_04', 'issue_audit_0002_01', 'issue_audit_0002_02', 'issue_audit_0002_03', 'issue_audit_0002_04', 'issue_deterministic_gate_0001', 'issue_deterministic_gate_0002']`

```json
[
  {
    "changes": {
      "/attributes/Name": "首层第一段直跑楼梯梯段"
    },
    "evidence_refs": [
      "issue_deterministic_gate_0001:/attributes/Name"
    ],
    "op": "update_entity",
    "operation_id": "operation-stair-flight-1-name",
    "target_component_hash": "sha256:d68ef017101fece8330c0e4053aead51a4cff5182bca4c6793c5f30ae81adae0",
    "target_id": "stair-flight-1"
  },
  {
    "changes": {
      "/attributes/Name": "二层第二段直跑楼梯梯段"
    },
    "evidence_refs": [
      "issue_deterministic_gate_0002:/attributes/Name"
    ],
    "op": "update_entity",
    "operation_id": "operation-stair-flight-2-name",
    "target_component_hash": "sha256:d323984b9f34722912a1e7887ad44fbb027607b411fc9aca8b0f943e04783a96",
    "target_id": "stair-flight-2"
  }
]
```

Source: [changeset-round-01/changeset.json](changeset-round-01/changeset.json)

### Allowed Scope 1

```json
{
  "allowed_paths": {
    "aggregate-stair-1": [
      "/attributes"
    ],
    "aggregate-stair-2": [
      "/attributes"
    ],
    "floor-slab-storey-2": [
      "/attributes"
    ],
    "floor-slab-storey-3": [
      "/attributes"
    ],
    "opening-floor-slab-storey-2-opening-stair": [
      "/attributes"
    ],
    "opening-floor-slab-storey-3-opening-stair": [
      "/attributes"
    ],
    "stair-1": [
      "/attributes"
    ],
    "stair-2": [
      "/attributes"
    ],
    "stair-flight-1": [
      "/attributes"
    ],
    "stair-flight-2": [
      "/attributes"
    ],
    "void-floor-slab-storey-2-opening-stair": [
      "/attributes"
    ],
    "void-floor-slab-storey-3-opening-stair": [
      "/attributes"
    ]
  },
  "base_revision_id": "revision-00",
  "dependencies": [
    {
      "dependency_id": "void-floor-slab-storey-2-opening-stair",
      "reason": "IfcRelVoidsElement references an allowed component.",
      "relationship_type": "IfcRelVoidsElement",
      "target_id": "floor-slab-storey-2"
    },
    {
      "dependency_id": "void-floor-slab-storey-3-opening-stair",
      "reason": "IfcRelVoidsElement references an allowed component.",
      "relationship_type": "IfcRelVoidsElement",
      "target_id": "floor-slab-storey-3"
    },
    {
      "dependency_id": "aggregate-stair-1",
      "reason": "IfcRelAggregates references an allowed component.",
      "relationship_type": "IfcRelAggregates",
      "target_id": "stair-1"
    },
    {
      "dependency_id": "aggregate-stair-2",
      "reason": "IfcRelAggregates references an allowed component.",
      "relationship_type": "IfcRelAggregates",
      "target_id": "stair-2"
    }
  ],
  "entity_ids": [
    "floor-slab-storey-2",
    "floor-slab-storey-3",
    "opening-floor-slab-storey-2-opening-stair",
    "opening-floor-slab-storey-3-opening-stair",
    "stair-1",
    "stair-2",
    "stair-flight-1",
    "stair-flight-2"
  ],
  "forbidden_ids": [
    "building-1",
    "door-storey-1-storey-1-door-main-entrance",
    "door-storey-1-storey-1-door-partition",
    "door-storey-2-storey-2-door-partition",
    "door-storey-3-storey-3-door-partition",
    "fill-storey-1-door-main-entrance",
    "fill-storey-1-door-partition",
    "fill-storey-1-window-east",
    "fill-storey-1-window-north",
    "fill-storey-1-window-south-1",
    "fill-storey-1-window-south-2",
    "fill-storey-1-window-west",
    "fill-storey-2-door-partition",
    "fill-storey-2-window-east",
    "fill-storey-2-window-north",
    "fill-storey-2-window-south-1",
    "fill-storey-2-window-south-2",
    "fill-storey-2-window-west",
    "fill-storey-3-door-partition",
    "fill-storey-3-window-east",
    "fill-storey-3-window-north",
    "fill-storey-3-window-south-1",
    "fill-storey-3-window-south-2",
    "fill-storey-3-window-west",
    "floor-slab-ground",
    "opening-storey-1-door-main-entrance",
    "opening-storey-1-door-partition",
    "opening-storey-1-window-east",
    "opening-storey-1-window-north",
    "opening-storey-1-window-south-1",
    "opening-storey-1-window-south-2",
    "opening-storey-1-window-west",
    "opening-storey-2-door-partition",
    "opening-storey-2-window-east",
    "opening-storey-2-window-north",
    "opening-storey-2-window-south-1",
    "opening-storey-2-window-south-2",
    "opening-storey-2-window-west",
    "opening-storey-3-door-partition",
    "opening-storey-3-window-east",
    "opening-storey-3-window-north",
    "opening-storey-3-window-south-1",
    "opening-storey-3-window-south-2",
    "opening-storey-3-window-west",
    "project-1",
    "roof-slab",
    "site-1",
    "space-storey-1-storey-1-space-hall",
    "space-storey-1-storey-1-space-stairwell",
    "space-storey-2-storey-2-space-hall",
    "space-storey-2-storey-2-space-landing-north",
    "space-storey-3-storey-3-space-hall",
    "space-storey-3-storey-3-space-landing-south",
    "storey-1",
    "storey-2",
    "storey-3",
    "void-storey-1-door-main-entrance",
    "void-storey-1-door-partition",
    "void-storey-1-window-east",
    "void-storey-1-window-north",
    "void-storey-1-window-south-1",
    "void-storey-1-window-south-2",
    "void-storey-1-window-west",
    "void-storey-2-door-partition",
    "void-storey-2-window-east",
    "void-storey-2-window-north",
    "void-storey-2-window-south-1",
    "void-storey-2-window-south-2",
    "void-storey-2-window-west",
    "void-storey-3-door-partition",
    "void-storey-3-window-east",
    "void-storey-3-window-north",
    "void-storey-3-window-south-1",
    "void-storey-3-window-south-2",
    "void-storey-3-window-west",
    "wall-storey-1-storey-1-wall-east",
    "wall-storey-1-storey-1-wall-north",
    "wall-storey-1-storey-1-wall-partition",
    "wall-storey-1-storey-1-wall-south",
    "wall-storey-1-storey-1-wall-west",
    "wall-storey-2-storey-2-wall-east",
    "wall-storey-2-storey-2-wall-north",
    "wall-storey-2-storey-2-wall-partition",
    "wall-storey-2-storey-2-wall-south",
    "wall-storey-2-storey-2-wall-west",
    "wall-storey-3-storey-3-wall-east",
    "wall-storey-3-storey-3-wall-north",
    "wall-storey-3-storey-3-wall-partition",
    "wall-storey-3-storey-3-wall-south",
    "wall-storey-3-storey-3-wall-west",
    "window-storey-1-storey-1-window-east",
    "window-storey-1-storey-1-window-north",
    "window-storey-1-storey-1-window-south-1",
    "window-storey-1-storey-1-window-south-2",
    "window-storey-1-storey-1-window-west",
    "window-storey-2-storey-2-window-east",
    "window-storey-2-storey-2-window-north",
    "window-storey-2-storey-2-window-south-1",
    "window-storey-2-storey-2-window-south-2",
    "window-storey-2-storey-2-window-west",
    "window-storey-3-storey-3-window-east",
    "window-storey-3-storey-3-window-north",
    "window-storey-3-storey-3-window-south-1",
    "window-storey-3-storey-3-window-south-2",
    "window-storey-3-storey-3-window-west"
  ],
  "relationship_ids": [
    "aggregate-stair-1",
    "aggregate-stair-2",
    "void-floor-slab-storey-2-opening-stair",
    "void-floor-slab-storey-3-opening-stair"
  ],
  "schema_version": "text2ifc/change-scope/1.0",
  "scope_id": "scope-revision-01",
  "source_issue_ids": [
    "issue_audit_0001_01",
    "issue_audit_0001_02",
    "issue_audit_0001_03",
    "issue_audit_0001_04",
    "issue_audit_0002_01",
    "issue_audit_0002_02",
    "issue_audit_0002_03",
    "issue_audit_0002_04",
    "issue_deterministic_gate_0001",
    "issue_deterministic_gate_0002"
  ]
}
```

Source: [changeset-round-01/change-scope.json](changeset-round-01/change-scope.json)

### Revision Gates

```json
{
  "gate_results": {
    "candidate_hash": "sha256:9c687f89f5c1c2cb71c30768ee60131e8173c4863125ffc49f9348d92a2e5c2e",
    "deterministic_gates": {
      "case_id": "51592773914118fb",
      "compile_reopen_success": true,
      "deterministic_gates_passed": false,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "fb2a81e3fa22bf0a0d476239789c106f3c07f7c21038d2474bf3a0856646c4de",
          "expected-facts.json": "f407589f213b63a92e416535c7844fe9e042161160335e5ff8e7a61926651a13",
          "generator/candidate.json": "9c687f89f5c1c2cb71c30768ee60131e8173c4863125ffc49f9348d92a2e5c2e",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "a47a123e0a2f23950cfc00418373806a0ab56ea4395dfde4236878b101070294",
          "ifc-verification.json": "78e6468e1933a1884349e7684535c440ccccd126c4582d027cd63936167c5db9",
          "repair/route.json": "edf4429e6d483b15015c0bdfccf6c032316e41ea9cd58caba5721d98e00b5bdf",
          "request-semantics.json": "cb705d605ef430207ae1e03732ddc19acb3dadf8f39aa5bb89694e39e71b7d50",
          "semantic-coverage.json": "b7084edcbb218e1fb438159f6a9be853215cc945774c982d3aa7f82bc2feda0b",
          "semantic-verification.json": "5b7ac9a188a8e11f11c079ca7716ac35e053d18b0f1c4b60380c4a2a7a0c5035"
        },
        "candidate_hash": "9c687f89f5c1c2cb71c30768ee60131e8173c4863125ffc49f9348d92a2e5c2e",
        "candidate_path": "generator/candidate.json",
        "case_id": "51592773914118fb",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\continuation-20260910\\B-retain\\runtime\\runs\\51592773914118fb\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [
              {
                "code": "MISSING_STAIR_OPENING",
                "entity_ids": [
                  "floor-slab-storey-2-opening-stair"
                ],
                "message": "No opening satisfies the frozen identity/host/bounds obligation.",
                "path": "/floor_openings/floor-slab-storey-2-opening-stair",
                "source_fact_refs": [
                  "/known_facts/floor_slabs/1/opening"
                ]
              },
              {
                "code": "MISSING_STAIR_OPENING",
                "entity_ids": [
                  "floor-slab-storey-3-opening-stair"
                ],
                "message": "No opening satisfies the frozen identity/host/bounds obligation.",
                "path": "/floor_openings/floor-slab-storey-3-opening-stair",
                "source_fact_refs": [
                  "/known_facts/floor_slabs/2/opening"
                ]
              },
              {
                "code": "MISSING_STAIR_FLIGHT",
                "entity_ids": [
                  "stair-1-flight",
                  "stair-flight-1-flight"
                ],
                "message": "Expected stair 'stair-1-flight' has no checkable IfcStairFlight.",
                "path": "/stairs/stair-1-flight",
                "source_fact_refs": [
                  "/known_facts/stairs/0"
                ]
              },
              {
                "code": "MISSING_STAIR_FLIGHT",
                "entity_ids": [
                  "stair-2-flight",
                  "stair-flight-2-flight"
                ],
                "message": "Expected stair 'stair-2-flight' has no checkable IfcStairFlight.",
                "path": "/stairs/stair-2-flight",
                "source_fact_refs": [
                  "/known_facts/stairs/1"
                ]
              }
            ],
            "metrics": {
              "case_id": "51592773914118fb",
              "floor_openings": {},
              "products": {},
              "roof": {
                "roof-slab": {
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      9.3,
                      9.450000000000001
                    ]
                  },
                  "ifc_class": "IfcRoof"
                }
              },
              "slabs": {
                "floor-slab-ground": {
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      -0.15,
                      0.0
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "floor-slab-storey-2": {
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "floor-slab-storey-3": {
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      6.150000000000001,
                      6.300000000000002
                    ]
                  },
                  "ifc_class": "IfcSlab"
                }
              },
              "spaces": {
                "space-storey-1-storey-1-space-hall": {
                  "bbox": {
                    "x": [
                      0.0,
                      7.6000000000000005
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-storey-1-storey-1-space-stairwell": {
                  "bbox": {
                    "x": [
                      7.8,
                      10.0
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-storey-2-storey-2-space-hall": {
                  "bbox": {
                    "x": [
                      0.0,
                      7.6000000000000005
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-storey-2-storey-2-space-landing-north": {
                  "bbox": {
                    "x": [
                      7.8,
                      10.0
                    ],
                    "y": [
                      6.9,
                      8.4
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-storey-3-storey-3-space-hall": {
                  "bbox": {
                    "x": [
                      0.0,
                      7.6000000000000005
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-storey-3-storey-3-space-landing-south": {
                  "bbox": {
                    "x": [
                      7.8,
                      10.0
                    ],
                    "y": [
                      0.0,
                      1.5
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcSpace"
                }
              },
              "stairs": {},
              "wall_set_convention": "primary",
              "walls": {
                "wall-storey-1-storey-1-wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      10.0,
                      10.2
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      8.4,
                      8.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-partition": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      7.6000000000000005,
                      7.8
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.2,
                      0.0
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-1-storey-1-wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.2,
                      0.0
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      10.0,
                      10.2
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      8.4,
                      8.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-partition": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      7.6000000000000005,
                      7.8
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.2,
                      0.0
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-2-storey-2-wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.2,
                      0.0
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-3-storey-3-wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      10.0,
                      10.2
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-3-storey-3-wall-north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      8.4,
                      8.6
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-3-storey-3-wall-partition": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      7.6000000000000005,
                      7.8
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-3-storey-3-wall-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      -0.20000000000000018,
                      10.2
                    ],
                    "y": [
                      -0.2,
                      0.0
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-storey-3-storey-3-wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.2,
                      0.0
                    ],
                    "y": [
                      0.0,
                      8.4
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                }
              }
            },
            "success": false
          },
          "repair_history": {
            "case_id": "51592773914118fb",
            "fact_delta": null,
            "geometry_issue_count": 0,
            "provider_call_count": 0,
            "repair_attempts": [],
            "repair_diagnostics": [],
            "repair_source_artifact": "candidate.json",
            "route": "no_repair_needed",
            "schema_version": "text2ifc/repair-route/1.0",
            "source_document_kind": "candidate",
            "source_document_path": "candidate.json",
            "source_generator_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/continuation-20260910/B-retain/runtime/runs/51592773914118fb/generator",
            "source_generator_response_id": "c5a38d05-4e9a-4724-a6a1-69da4696519f",
            "valid": true,
            "validation_issue_count": 0
          },
          "request_semantics": {
            "basis": "request expectations independently compared with reopened IFC before atomic publication",
            "expectations": [
              {
                "entity_id": "wall-storey-1-storey-1-wall-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-partition",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-partition",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-partition",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "floor-slab-ground",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "floor-slab-storey-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "floor-slab-storey-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "roof-slab",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-main-entrance",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-3-storey-3-door-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-1-storey-1-wall-partition",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-2-storey-2-wall-partition",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-east",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-storey-3-storey-3-wall-partition",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "floor-slab-ground",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "floor-slab-storey-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "floor-slab-storey-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "roof-slab",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-main-entrance",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-3-storey-3-door-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              }
            ],
            "issues": [],
            "schema_version": "text2ifc/request-semantic-verification/1.0",
            "valid": true
          },
          "schema_validation": {
            "issue_count": 0,
            "issues": [],
            "valid": true
          },
          "semantic_coverage": {
            "blocking_facts": [],
            "candidate_entity_count": 75,
            "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
            "case_id": "51592773914118fb",
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
                    "id": "floor-slab-ground",
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
                    "opening": {
                      "bounds": {
                        "x": [
                          8000,
                          9600
                        ],
                        "y": [
                          1500,
                          6900
                        ]
                      },
                      "id": "floor-slab-storey-2-opening-stair"
                    },
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
                    "opening": {
                      "bounds": {
                        "x": [
                          8000,
                          9600
                        ],
                        "y": [
                          1500,
                          6900
                        ]
                      },
                      "id": "floor-slab-storey-3-opening-stair"
                    },
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
                "path": "/known_facts/roof_slab/openings",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": []
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
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-1-wall-north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-1-wall-west",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-1-wall-east",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-1-wall-partition",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-2-wall-south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-2-wall-north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-2-wall-west",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-2-wall-east",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-2-wall-partition",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-3-wall-south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-3-wall-north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-3-wall-west",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-3-wall-east",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-3-wall-partition",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "floor-slab-ground",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "floor-slab-storey-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "floor-slab-storey-3",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "roof-slab",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "storey-1-door-main-entrance",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-1-door-partition",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-2-door-partition",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "storey-3-door-partition",
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
                "path": "/known_facts/stairs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds": {
                      "x": [
                        8200,
                        9400
                      ],
                      "y": [
                        1500,
                        6900
                      ]
                    },
                    "end_elevation_mm": 3150,
                    "from_storey": "storey-1",
                    "id": "stair-1-flight",
                    "name": "第一段直跑楼梯",
                    "number_of_risers": 18,
                    "number_of_treads": 18,
                    "opening_bounds": {
                      "x": [
                        8000,
                        9600
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
                        8200,
                        9400
                      ],
                      "y": [
                        1500,
                        6900
                      ]
                    },
                    "end_elevation_mm": 6300,
                    "from_storey": "storey-2",
                    "id": "stair-2-flight",
                    "name": "第二段直跑楼梯（反向）",
                    "number_of_risers": 18,
                    "number_of_treads": 18,
                    "opening_bounds": {
                      "x": [
                        8000,
                        9600
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
                        "center_global_mm": [
                          3800,
                          -100
                        ],
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-south",
                        "id": "storey-1-door-main-entrance",
                        "name": "南墙主入口",
                        "panels": "single",
                        "sill_height_mm": 0,
                        "swing": "left",
                        "width_mm": 1200
                      },
                      {
                        "center_global_mm": [
                          7700,
                          700
                        ],
                        "height_mm": 2100,
                        "host_wall": "storey-1-wall-partition",
                        "id": "storey-1-door-partition",
                        "name": "分隔墙门",
                        "panels": "single",
                        "sill_height_mm": 0,
                        "swing": "right",
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
                            7600
                          ],
                          "y": [
                            0,
                            8400
                          ]
                        },
                        "id": "storey-1-space-hall",
                        "name": "接待阅览厅"
                      },
                      {
                        "bounds": {
                          "x": [
                            7800,
                            10000
                          ],
                          "y": [
                            0,
                            8400
                          ]
                        },
                        "id": "storey-1-space-stairwell",
                        "name": "楼梯间"
                      }
                    ],
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
                              7600,
                              7800
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
                          "height_mm": 3000,
                          "id": "storey-1-wall-partition",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          1700,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-south",
                        "id": "storey-1-window-south-1",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          5900,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-south",
                        "id": "storey-1-window-south-2",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          3800,
                          8500
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-north",
                        "id": "storey-1-window-north",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 2400
                      },
                      {
                        "center_global_mm": [
                          -100,
                          4200
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-west",
                        "id": "storey-1-window-west",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10100,
                          4200
                        ],
                        "height_mm": 1800,
                        "host_wall": "storey-1-wall-east",
                        "id": "storey-1-window-east",
                        "panels": "single",
                        "sill_height_mm": 600,
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          7700,
                          7650
                        ],
                        "height_mm": 2100,
                        "host_wall": "storey-2-wall-partition",
                        "id": "storey-2-door-partition",
                        "name": "分隔墙门",
                        "panels": "single",
                        "sill_height_mm": 0,
                        "swing": "right",
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
                            7600
                          ],
                          "y": [
                            0,
                            8400
                          ]
                        },
                        "id": "storey-2-space-hall",
                        "name": "安静阅览厅"
                      },
                      {
                        "bounds": {
                          "x": [
                            7800,
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
                              7600,
                              7800
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
                          "height_mm": 3000,
                          "id": "storey-2-wall-partition",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          1700,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-south",
                        "id": "storey-2-window-south-1",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          5900,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-south",
                        "id": "storey-2-window-south-2",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          3800,
                          8500
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-north",
                        "id": "storey-2-window-north",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 2400
                      },
                      {
                        "center_global_mm": [
                          -100,
                          4200
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-west",
                        "id": "storey-2-window-west",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10100,
                          4200
                        ],
                        "height_mm": 1800,
                        "host_wall": "storey-2-wall-east",
                        "id": "storey-2-window-east",
                        "panels": "single",
                        "sill_height_mm": 600,
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          7700,
                          700
                        ],
                        "height_mm": 2100,
                        "host_wall": "storey-3-wall-partition",
                        "id": "storey-3-door-partition",
                        "name": "分隔墙门",
                        "panels": "single",
                        "sill_height_mm": 0,
                        "swing": "right",
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
                            7600
                          ],
                          "y": [
                            0,
                            8400
                          ]
                        },
                        "id": "storey-3-space-hall",
                        "name": "多功能活动厅"
                      },
                      {
                        "bounds": {
                          "x": [
                            7800,
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
                              7600,
                              7800
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
                          "height_mm": 3000,
                          "id": "storey-3-wall-partition",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          1700,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-south",
                        "id": "storey-3-window-south-1",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          5900,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-south",
                        "id": "storey-3-window-south-2",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          3800,
                          8500
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-north",
                        "id": "storey-3-window-north",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 2400
                      },
                      {
                        "center_global_mm": [
                          -100,
                          4200
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-west",
                        "id": "storey-3-window-west",
                        "panels": "double_vertical",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10100,
                          4200
                        ],
                        "height_mm": 1800,
                        "host_wall": "storey-3-wall-east",
                        "id": "storey-3-window-east",
                        "panels": "single",
                        "sill_height_mm": 600,
                        "width_mm": 900
                      }
                    ]
                  }
                ]
              }
            ],
            "schema_version": "text2ifc/semantic-coverage/1.0",
            "valid": true
          }
        },
        "expected_facts_hash": "f407589f213b63a92e416535c7844fe9e042161160335e5ff8e7a61926651a13",
        "expected_facts_path": "expected-facts.json",
        "gates": [
          {
            "applicability": "applicable",
            "basis": "generator validation sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "bim_json_validation",
            "source_paths": [
              "generator/validation.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected-facts total_counts compared with candidate entities",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_entity_completeness",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected storey and host-wall facts compared with candidate placement/void-fill graph",
            "entity_matches": [
              {
                "candidate_id": "door-storey-1-storey-1-door-main-entrance",
                "collection": "doors",
                "expected_id": "storey-1-door-main-entrance",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-1-storey-1-door-partition",
                "collection": "doors",
                "expected_id": "storey-1-door-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-2-storey-2-door-partition",
                "collection": "doors",
                "expected_id": "storey-2-door-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-3-storey-3-door-partition",
                "collection": "doors",
                "expected_id": "storey-3-door-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-hall",
                "collection": "spaces",
                "expected_id": "storey-1-space-hall",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-storey-1-space-stairwell",
                "collection": "spaces",
                "expected_id": "storey-1-space-stairwell",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-hall",
                "collection": "spaces",
                "expected_id": "storey-2-space-hall",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-storey-2-space-landing-north",
                "collection": "spaces",
                "expected_id": "storey-2-space-landing-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-3-storey-3-space-hall",
                "collection": "spaces",
                "expected_id": "storey-3-space-hall",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-3-storey-3-space-landing-south",
                "collection": "spaces",
                "expected_id": "storey-3-space-landing-south",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-south",
                "collection": "walls",
                "expected_id": "storey-1-wall-south",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-north",
                "collection": "walls",
                "expected_id": "storey-1-wall-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-west",
                "collection": "walls",
                "expected_id": "storey-1-wall-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-east",
                "collection": "walls",
                "expected_id": "storey-1-wall-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-1-storey-1-wall-partition",
                "collection": "walls",
                "expected_id": "storey-1-wall-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-south",
                "collection": "walls",
                "expected_id": "storey-2-wall-south",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-north",
                "collection": "walls",
                "expected_id": "storey-2-wall-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-west",
                "collection": "walls",
                "expected_id": "storey-2-wall-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-east",
                "collection": "walls",
                "expected_id": "storey-2-wall-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-2-storey-2-wall-partition",
                "collection": "walls",
                "expected_id": "storey-2-wall-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-3-storey-3-wall-south",
                "collection": "walls",
                "expected_id": "storey-3-wall-south",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-3-storey-3-wall-north",
                "collection": "walls",
                "expected_id": "storey-3-wall-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-3-storey-3-wall-west",
                "collection": "walls",
                "expected_id": "storey-3-wall-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-3-storey-3-wall-east",
                "collection": "walls",
                "expected_id": "storey-3-wall-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "wall-storey-3-storey-3-wall-partition",
                "collection": "walls",
                "expected_id": "storey-3-wall-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-window-south-1",
                "collection": "windows",
                "expected_id": "storey-1-window-south-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-window-south-2",
                "collection": "windows",
                "expected_id": "storey-1-window-south-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-window-north",
                "collection": "windows",
                "expected_id": "storey-1-window-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-window-west",
                "collection": "windows",
                "expected_id": "storey-1-window-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-storey-1-window-east",
                "collection": "windows",
                "expected_id": "storey-1-window-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-window-south-1",
                "collection": "windows",
                "expected_id": "storey-2-window-south-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-window-south-2",
                "collection": "windows",
                "expected_id": "storey-2-window-south-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-window-north",
                "collection": "windows",
                "expected_id": "storey-2-window-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-window-west",
                "collection": "windows",
                "expected_id": "storey-2-window-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-storey-2-window-east",
                "collection": "windows",
                "expected_id": "storey-2-window-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-storey-3-window-south-1",
                "collection": "windows",
                "expected_id": "storey-3-window-south-1",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-storey-3-window-south-2",
                "collection": "windows",
                "expected_id": "storey-3-window-south-2",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-storey-3-window-north",
                "collection": "windows",
                "expected_id": "storey-3-window-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-storey-3-window-west",
                "collection": "windows",
                "expected_id": "storey-3-window-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-storey-3-window-east",
                "collection": "windows",
                "expected_id": "storey-3-window-east",
                "match_basis": "canonical_entity_id"
              }
            ],
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_containment",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "explicit component storey labels compared with placement-derived ownership",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_name_consistency",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected opening/fill obligations compared with IfcRelVoidsElement and IfcRelFillsElement",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_opening_fill",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "semantic coverage sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "semantic_coverage",
            "source_paths": [
              "semantic-coverage.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "independent reopened IFC/request comparison",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "request_semantics",
            "source_paths": [
              "semantic-verification.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "IFC compile/reopen sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "ifc_compile_reopen",
            "source_paths": [
              "ifc-verification.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "geometry feedback sidecar",
            "issue_codes": [
              "MISSING_STAIR_FLIGHT",
              "MISSING_STAIR_OPENING"
            ],
            "issue_count": 4,
            "issues": [
              {
                "code": "MISSING_STAIR_OPENING",
                "message": "No opening satisfies the frozen identity/host/bounds obligation.",
                "path": "/floor_openings/floor-slab-storey-2-opening-stair"
              },
              {
                "code": "MISSING_STAIR_OPENING",
                "message": "No opening satisfies the frozen identity/host/bounds obligation.",
                "path": "/floor_openings/floor-slab-storey-3-opening-stair"
              },
              {
                "code": "MISSING_STAIR_FLIGHT",
                "message": "Expected stair 'stair-1-flight' has no checkable IfcStairFlight.",
                "path": "/stairs/stair-1-flight"
              },
              {
                "code": "MISSING_STAIR_FLIGHT",
                "message": "Expected stair 'stair-2-flight' has no checkable IfcStairFlight.",
                "path": "/stairs/stair-2-flight"
              }
            ],
            "name": "geometry",
            "source_paths": [
              "geometry-feedback.json"
            ],
            "status": "failed"
          },
          {
            "applicability": "applicable",
            "basis": "repair route is no_repair_needed",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "repair_route",
            "source_paths": [
              "repair/route.json"
            ],
            "status": "passed"
          }
        ],
        "overall_status": "failed",
        "schema_version": "text2ifc/gate-summary/1.0"
      },
      "geometry_feedback": {
        "expectation_source": "design_brief_expected_facts",
        "issues": [
          {
            "code": "MISSING_STAIR_OPENING",
            "entity_ids": [
              "floor-slab-storey-2-opening-stair"
            ],
            "message": "No opening satisfies the frozen identity/host/bounds obligation.",
            "path": "/floor_openings/floor-slab-storey-2-opening-stair",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/opening"
            ]
          },
          {
            "code": "MISSING_STAIR_OPENING",
            "entity_ids": [
              "floor-slab-storey-3-opening-stair"
            ],
            "message": "No opening satisfies the frozen identity/host/bounds obligation.",
            "path": "/floor_openings/floor-slab-storey-3-opening-stair",
            "source_fact_refs": [
              "/known_facts/floor_slabs/2/opening"
            ]
          },
          {
            "code": "MISSING_STAIR_FLIGHT",
            "entity_ids": [
              "stair-1-flight",
              "stair-flight-1-flight"
            ],
            "message": "Expected stair 'stair-1-flight' has no checkable IfcStairFlight.",
            "path": "/stairs/stair-1-flight",
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          },
          {
            "code": "MISSING_STAIR_FLIGHT",
            "entity_ids": [
              "stair-2-flight",
              "stair-flight-2-flight"
            ],
            "message": "Expected stair 'stair-2-flight' has no checkable IfcStairFlight.",
            "path": "/stairs/stair-2-flight",
            "source_fact_refs": [
              "/known_facts/stairs/1"
            ]
          }
        ],
        "metrics": {
          "case_id": "51592773914118fb",
          "floor_openings": {},
          "products": {},
          "roof": {
            "roof-slab": {
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  9.3,
                  9.450000000000001
                ]
              },
              "ifc_class": "IfcRoof"
            }
          },
          "slabs": {
            "floor-slab-ground": {
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  -0.15,
                  0.0
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "floor-slab-storey-2": {
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "floor-slab-storey-3": {
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  6.150000000000001,
                  6.300000000000002
                ]
              },
              "ifc_class": "IfcSlab"
            }
          },
          "spaces": {
            "space-storey-1-storey-1-space-hall": {
              "bbox": {
                "x": [
                  0.0,
                  7.6000000000000005
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-storey-1-storey-1-space-stairwell": {
              "bbox": {
                "x": [
                  7.8,
                  10.0
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-storey-2-storey-2-space-hall": {
              "bbox": {
                "x": [
                  0.0,
                  7.6000000000000005
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-storey-2-storey-2-space-landing-north": {
              "bbox": {
                "x": [
                  7.8,
                  10.0
                ],
                "y": [
                  6.9,
                  8.4
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-storey-3-storey-3-space-hall": {
              "bbox": {
                "x": [
                  0.0,
                  7.6000000000000005
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-storey-3-storey-3-space-landing-south": {
              "bbox": {
                "x": [
                  7.8,
                  10.0
                ],
                "y": [
                  0.0,
                  1.5
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcSpace"
            }
          },
          "stairs": {},
          "wall_set_convention": "primary",
          "walls": {
            "wall-storey-1-storey-1-wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  10.0,
                  10.2
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-north": {
              "axis": "x",
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  8.4,
                  8.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-partition": {
              "axis": "y",
              "bbox": {
                "x": [
                  7.6000000000000005,
                  7.8
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.2,
                  0.0
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-1-storey-1-wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.2,
                  0.0
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  10.0,
                  10.2
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-north": {
              "axis": "x",
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  8.4,
                  8.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-partition": {
              "axis": "y",
              "bbox": {
                "x": [
                  7.6000000000000005,
                  7.8
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.2,
                  0.0
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-2-storey-2-wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.2,
                  0.0
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-3-storey-3-wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  10.0,
                  10.2
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-3-storey-3-wall-north": {
              "axis": "x",
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  8.4,
                  8.6
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-3-storey-3-wall-partition": {
              "axis": "y",
              "bbox": {
                "x": [
                  7.6000000000000005,
                  7.8
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-3-storey-3-wall-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  -0.20000000000000018,
                  10.2
                ],
                "y": [
                  -0.2,
                  0.0
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-storey-3-storey-3-wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.2,
                  0.0
                ],
                "y": [
                  0.0,
                  8.4
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            }
          }
        },
        "success": false
      },
      "geometry_success": false,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\continuation-20260910\\B-retain\\runtime\\runs\\51592773914118fb\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\continuation-20260910\\B-retain\\runtime\\runs\\51592773914118fb\\output.ifc",
        "success": true
      },
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\continuation-20260910\\B-retain\\runtime\\runs\\51592773914118fb",
      "semantic_geometry_expectation": {
        "case_id": "51592773914118fb",
        "complete": true,
        "doors": {},
        "floor_openings": {
          "floor-slab-storey-2-opening-stair": {
            "bbox": {
              "x": [
                8.0,
                9.6
              ],
              "y": [
                1.5,
                6.9
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "bbox_issue_code": "FLOOR_OPENING_BBOX_MISMATCH",
            "host_slab_id": "floor-slab-storey-2",
            "identity_source": "explicit",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/opening"
            ]
          },
          "floor-slab-storey-3-opening-stair": {
            "bbox": {
              "x": [
                8.0,
                9.6
              ],
              "y": [
                1.5,
                6.9
              ],
              "z": [
                6.15,
                6.3
              ]
            },
            "bbox_issue_code": "FLOOR_OPENING_BBOX_MISMATCH",
            "host_slab_id": "floor-slab-storey-3",
            "identity_source": "explicit",
            "source_fact_refs": [
              "/known_facts/floor_slabs/2/opening"
            ]
          }
        },
        "products": {},
        "roof": {
          "roof-slab": {
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                8.6
              ],
              "z": [
                9.3,
                9.45
              ]
            },
            "datum": "roof_bottom",
            "source_fact_refs": [
              "/known_facts/roof_slab"
            ]
          }
        },
        "schema_version": "text2ifc/design-geometry-expectation/1.1",
        "slabs": {
          "floor-slab-ground": {
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                8.6
              ],
              "z": [
                -0.15,
                0.0
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [],
            "source_fact_refs": [
              "/known_facts/floor_slabs/0"
            ]
          },
          "floor-slab-storey-2": {
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                8.6
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [
              "wall-storey-1-storey-1-wall-east",
              "wall-storey-1-storey-1-wall-north",
              "wall-storey-1-storey-1-wall-partition",
              "wall-storey-1-storey-1-wall-south",
              "wall-storey-1-storey-1-wall-west"
            ],
            "source_fact_refs": [
              "/known_facts/floor_slabs/1"
            ]
          },
          "floor-slab-storey-3": {
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                8.6
              ],
              "z": [
                6.15,
                6.3
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [
              "wall-storey-2-storey-2-wall-east",
              "wall-storey-2-storey-2-wall-north",
              "wall-storey-2-storey-2-wall-partition",
              "wall-storey-2-storey-2-wall-south",
              "wall-storey-2-storey-2-wall-west"
            ],
            "source_fact_refs": [
              "/known_facts/floor_slabs/2"
            ]
          }
        },
        "source": "design_brief_expected_facts",
        "spaces": {
          "space-storey-1-storey-1-space-hall": {
            "bbox": {
              "x": [
                0.0,
                7.6
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/0"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-1-storey-1-space-stairwell": {
            "bbox": {
              "x": [
                7.8,
                10.0
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/1"
            ],
            "storey_id": "storey-1"
          },
          "space-storey-2-storey-2-space-hall": {
            "bbox": {
              "x": [
                0.0,
                7.6
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/0"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-2-storey-2-space-landing-north": {
            "bbox": {
              "x": [
                7.8,
                10.0
              ],
              "y": [
                6.9,
                8.4
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/1"
            ],
            "storey_id": "storey-2"
          },
          "space-storey-3-storey-3-space-hall": {
            "bbox": {
              "x": [
                0.0,
                7.6
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/2/spaces/0"
            ],
            "storey_id": "storey-3"
          },
          "space-storey-3-storey-3-space-landing-south": {
            "bbox": {
              "x": [
                7.8,
                10.0
              ],
              "y": [
                0.0,
                1.5
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/2/spaces/1"
            ],
            "storey_id": "storey-3"
          }
        },
        "stairs": {
          "stair-1-flight": {
            "bbox": {
              "x": [
                8.2,
                9.4
              ],
              "y": [
                1.5,
                6.9
              ],
              "z": [
                0.0,
                3.15
              ]
            },
            "bbox_issue_code": "STAIR_BBOX_MISMATCH",
            "flight_ids": [
              "stair-flight-1-flight"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          },
          "stair-2-flight": {
            "bbox": {
              "x": [
                8.2,
                9.4
              ],
              "y": [
                1.5,
                6.9
              ],
              "z": [
                3.15,
                6.3
              ]
            },
            "bbox_issue_code": "STAIR_BBOX_MISMATCH",
            "flight_ids": [
              "stair-flight-2-flight"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/1"
            ]
          }
        },
        "tolerance": 0.05,
        "units": "METRE",
        "unresolved": [],
        "walls": {
          "wall-storey-1-storey-1-wall-east": {
            "axis": "y",
            "bbox": {
              "x": [
                10.0,
                10.2
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-east",
            "source_fact_refs": [
              "/known_facts/walls/3"
            ]
          },
          "wall-storey-1-storey-1-wall-north": {
            "axis": "x",
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                8.4,
                8.6
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-north",
            "source_fact_refs": [
              "/known_facts/walls/1"
            ]
          },
          "wall-storey-1-storey-1-wall-partition": {
            "axis": "y",
            "bbox": {
              "x": [
                7.6,
                7.8
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-partition",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/0"
            ]
          },
          "wall-storey-1-storey-1-wall-south": {
            "axis": "x",
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                0.0
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-south",
            "source_fact_refs": [
              "/known_facts/walls/0"
            ]
          },
          "wall-storey-1-storey-1-wall-west": {
            "axis": "y",
            "bbox": {
              "x": [
                -0.2,
                0.0
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-1-wall-west",
            "source_fact_refs": [
              "/known_facts/walls/2"
            ]
          },
          "wall-storey-2-storey-2-wall-east": {
            "axis": "y",
            "bbox": {
              "x": [
                10.0,
                10.2
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-east",
            "source_fact_refs": [
              "/known_facts/walls/8"
            ]
          },
          "wall-storey-2-storey-2-wall-north": {
            "axis": "x",
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                8.4,
                8.6
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-north",
            "source_fact_refs": [
              "/known_facts/walls/6"
            ]
          },
          "wall-storey-2-storey-2-wall-partition": {
            "axis": "y",
            "bbox": {
              "x": [
                7.6,
                7.8
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-partition",
            "source_fact_refs": [
              "/known_facts/storeys/1/walls/interior/0"
            ]
          },
          "wall-storey-2-storey-2-wall-south": {
            "axis": "x",
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                0.0
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-south",
            "source_fact_refs": [
              "/known_facts/walls/5"
            ]
          },
          "wall-storey-2-storey-2-wall-west": {
            "axis": "y",
            "bbox": {
              "x": [
                -0.2,
                0.0
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-2-wall-west",
            "source_fact_refs": [
              "/known_facts/walls/7"
            ]
          },
          "wall-storey-3-storey-3-wall-east": {
            "axis": "y",
            "bbox": {
              "x": [
                10.0,
                10.2
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-3-wall-east",
            "source_fact_refs": [
              "/known_facts/walls/13"
            ]
          },
          "wall-storey-3-storey-3-wall-north": {
            "axis": "x",
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                8.4,
                8.6
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-3-wall-north",
            "source_fact_refs": [
              "/known_facts/walls/11"
            ]
          },
          "wall-storey-3-storey-3-wall-partition": {
            "axis": "y",
            "bbox": {
              "x": [
                7.6,
                7.8
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-3-wall-partition",
            "source_fact_refs": [
              "/known_facts/storeys/2/walls/interior/0"
            ]
          },
          "wall-storey-3-storey-3-wall-south": {
            "axis": "x",
            "bbox": {
              "x": [
                -0.2,
                10.2
              ],
              "y": [
                -0.2,
                0.0
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-3-wall-south",
            "source_fact_refs": [
              "/known_facts/walls/10"
            ]
          },
          "wall-storey-3-storey-3-wall-west": {
            "axis": "y",
            "bbox": {
              "x": [
                -0.2,
                0.0
              ],
              "y": [
                0.0,
                8.4
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/storey-3-wall-west",
            "source_fact_refs": [
              "/known_facts/walls/12"
            ]
          }
        },
        "windows": {}
      },
      "semantic_verification": {
        "basis": "request expectations independently compared with reopened IFC before atomic publication",
        "expectations": [
          {
            "entity_id": "wall-storey-1-storey-1-wall-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-partition",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-partition",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-partition",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "floor-slab-ground",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "floor-slab-storey-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "floor-slab-storey-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "roof-slab",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-main-entrance",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-3-storey-3-door-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-1-storey-1-wall-partition",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-2-storey-2-wall-partition",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-east",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-storey-3-storey-3-wall-partition",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "floor-slab-ground",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "floor-slab-storey-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "floor-slab-storey-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "roof-slab",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-main-entrance",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-3-storey-3-door-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          }
        ],
        "issues": [],
        "schema_version": "text2ifc/request-semantic-verification/1.0",
        "valid": true
      },
      "stage": "candidate-gates",
      "valid": false
    },
    "revision_id": "revision-01"
  },
  "issues": [],
  "plan": {
    "changed_ids": [
      "stair-flight-1",
      "stair-flight-2"
    ],
    "dependency_ids": [
      "aggregate-stair-1",
      "aggregate-stair-2",
      "void-floor-slab-storey-2-opening-stair",
      "void-floor-slab-storey-3-opening-stair"
    ],
    "global_gates": [
      "bim_json_schema",
      "bim_json_semantics",
      "relationship_integrity",
      "expected_fact_coverage",
      "unrelated_component_preservation",
      "ifc_compile",
      "ifc_reopen",
      "generated_ifc_geometry",
      "audit",
      "secret_scan"
    ],
    "global_gates_mandatory": true,
    "local_gates": [
      "stair_vertical_connection",
      "storey_ownership"
    ],
    "mode": "final_acceptance",
    "preservation": {
      "changed_ids": [
        "stair-flight-1",
        "stair-flight-2"
      ],
      "dependency_ids": [
        "aggregate-stair-1",
        "aggregate-stair-2",
        "void-floor-slab-storey-2-opening-stair",
        "void-floor-slab-storey-3-opening-stair"
      ],
      "forbidden_drift_ids": [],
      "schema_version": "text2ifc/component-preservation/1.0",
      "unchanged_ids": [
        "aggregate-stair-1",
        "aggregate-stair-2",
        "building-1",
        "door-storey-1-storey-1-door-main-entrance",
        "door-storey-1-storey-1-door-partition",
        "door-storey-2-storey-2-door-partition",
        "door-storey-3-storey-3-door-partition",
        "fill-storey-1-door-main-entrance",
        "fill-storey-1-door-partition",
        "fill-storey-1-window-east",
        "fill-storey-1-window-north",
        "fill-storey-1-window-south-1",
        "fill-storey-1-window-south-2",
        "fill-storey-1-window-west",
        "fill-storey-2-door-partition",
        "fill-storey-2-window-east",
        "fill-storey-2-window-north",
        "fill-storey-2-window-south-1",
        "fill-storey-2-window-south-2",
        "fill-storey-2-window-west",
        "fill-storey-3-door-partition",
        "fill-storey-3-window-east",
        "fill-storey-3-window-north",
        "fill-storey-3-window-south-1",
        "fill-storey-3-window-south-2",
        "fill-storey-3-window-west",
        "floor-slab-ground",
        "floor-slab-storey-2",
        "floor-slab-storey-3",
        "opening-floor-slab-storey-2-opening-stair",
        "opening-floor-slab-storey-3-opening-stair",
        "opening-storey-1-door-main-entrance",
        "opening-storey-1-door-partition",
        "opening-storey-1-window-east",
        "opening-storey-1-window-north",
        "opening-storey-1-window-south-1",
        "opening-storey-1-window-south-2",
        "opening-storey-1-window-west",
        "opening-storey-2-door-partition",
        "opening-storey-2-window-east",
        "opening-storey-2-window-north",
        "opening-storey-2-window-south-1",
        "opening-storey-2-window-south-2",
        "opening-storey-2-window-west",
        "opening-storey-3-door-partition",
        "opening-storey-3-window-east",
        "opening-storey-3-window-north",
        "opening-storey-3-window-south-1",
        "opening-storey-3-window-south-2",
        "opening-storey-3-window-west",
        "project-1",
        "roof-slab",
        "site-1",
        "space-storey-1-storey-1-space-hall",
        "space-storey-1-storey-1-space-stairwell",
        "space-storey-2-storey-2-space-hall",
        "space-storey-2-storey-2-space-landing-north",
        "space-storey-3-storey-3-space-hall",
        "space-storey-3-storey-3-space-landing-south",
        "stair-1",
        "stair-2",
        "storey-1",
        "storey-2",
        "storey-3",
        "void-floor-slab-storey-2-opening-stair",
        "void-floor-slab-storey-3-opening-stair",
        "void-storey-1-door-main-entrance",
        "void-storey-1-door-partition",
        "void-storey-1-window-east",
        "void-storey-1-window-north",
        "void-storey-1-window-south-1",
        "void-storey-1-window-south-2",
        "void-storey-1-window-west",
        "void-storey-2-door-partition",
        "void-storey-2-window-east",
        "void-storey-2-window-north",
        "void-storey-2-window-south-1",
        "void-storey-2-window-south-2",
        "void-storey-2-window-west",
        "void-storey-3-door-partition",
        "void-storey-3-window-east",
        "void-storey-3-window-north",
        "void-storey-3-window-south-1",
        "void-storey-3-window-south-2",
        "void-storey-3-window-west",
        "wall-storey-1-storey-1-wall-east",
        "wall-storey-1-storey-1-wall-north",
        "wall-storey-1-storey-1-wall-partition",
        "wall-storey-1-storey-1-wall-south",
        "wall-storey-1-storey-1-wall-west",
        "wall-storey-2-storey-2-wall-east",
        "wall-storey-2-storey-2-wall-north",
        "wall-storey-2-storey-2-wall-partition",
        "wall-storey-2-storey-2-wall-south",
        "wall-storey-2-storey-2-wall-west",
        "wall-storey-3-storey-3-wall-east",
        "wall-storey-3-storey-3-wall-north",
        "wall-storey-3-storey-3-wall-partition",
        "wall-storey-3-storey-3-wall-south",
        "wall-storey-3-storey-3-wall-west",
        "window-storey-1-storey-1-window-east",
        "window-storey-1-storey-1-window-north",
        "window-storey-1-storey-1-window-south-1",
        "window-storey-1-storey-1-window-south-2",
        "window-storey-1-storey-1-window-west",
        "window-storey-2-storey-2-window-east",
        "window-storey-2-storey-2-window-north",
        "window-storey-2-storey-2-window-south-1",
        "window-storey-2-storey-2-window-south-2",
        "window-storey-2-storey-2-window-west",
        "window-storey-3-storey-3-window-east",
        "window-storey-3-storey-3-window-north",
        "window-storey-3-storey-3-window-south-1",
        "window-storey-3-storey-3-window-south-2",
        "window-storey-3-storey-3-window-west"
      ],
      "unrelated_component_count": 105,
      "unrelated_component_preservation_rate": 1.0
    },
    "revision_binding": {
      "candidate_hash": "sha256:9c687f89f5c1c2cb71c30768ee60131e8173c4863125ffc49f9348d92a2e5c2e",
      "expected_facts_hash": "sha256:f407589f213b63a92e416535c7844fe9e042161160335e5ff8e7a61926651a13",
      "revision_id": "revision-01"
    },
    "schema_version": "text2ifc/revision-gate-plan/1.0",
    "skipped_local_gates": [
      "opening_filling_relationships",
      "opening_filling_geometry",
      "wall_host_geometry",
      "room_enclosure",
      "slab_wall_vertical_alignment"
    ]
  },
  "schema_version": "text2ifc/revision-gate-evidence/1.0",
  "valid": true
}
```

Source: [revision-gates.json](revision-gates.json)

## Metrics

### Design Brief Agent

```json
{
  "case_id": "51592773914118fb",
  "design_status": "ready",
  "evidence_class": "live",
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "parse_valid": true,
  "question_count": 0,
  "response_id": "199c507b-6cc2-4b49-a741-4d23f3aee7c5",
  "schema_semantic_valid": true,
  "stage": "design-brief",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 20063,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 11924,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 1920,
    "prompt_cache_miss_tokens": 14865,
    "prompt_tokens": 16785,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 1920
    },
    "total_tokens": 36848
  }
}
```

Source: [design-brief/metrics.json](design-brief/metrics.json)

### BIM JSON Generator

```json
{
  "case_id": "51592773914118fb",
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
  "response_id": "c5a38d05-4e9a-4724-a6a1-69da4696519f",
  "stage": "generate",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 36257,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 21665,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 1792,
    "prompt_cache_miss_tokens": 34218,
    "prompt_tokens": 36010,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 1792
    },
    "total_tokens": 72267
  }
}
```

Source: [generator/metrics.json](generator/metrics.json)

### Repair Route

```json
{
  "case_id": "51592773914118fb",
  "evidence_class": "live-derived-no-call",
  "fact_delta_valid": null,
  "geometry_issue_count": 0,
  "prior_attempt_count": 0,
  "provider_call_count": 0,
  "repair_attempt_count": 0,
  "repair_diagnostic_count": 0,
  "repair_source_artifact": "candidate.json",
  "repaired_artifact": null,
  "route": "no_repair_needed",
  "source_document_kind": "candidate",
  "source_document_path": "candidate.json",
  "source_generator_contract_valid": true,
  "source_generator_evidence_class": "live",
  "source_generator_response_id": "c5a38d05-4e9a-4724-a6a1-69da4696519f",
  "stage": "repair",
  "valid": true
}
```

Source: [repair/metrics.json](repair/metrics.json)

### Audit Agent

```json
{
  "case_id": "51592773914118fb",
  "design_review_context_sha256": "ee8c00986708b096e67017a4fd3ccada0f3ecccea46c7d5ed78248bcc598635a",
  "evidence_class": "live",
  "issue_count": 0,
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "response_id": "1b95aa8c-0696-4efc-9d58-d15056b67f6b",
  "route_decision": "generator_regeneration_required",
  "route_owner_stage": "generator",
  "schema_semantic_valid": true,
  "stage": "audit",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 6229,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 4943,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 11264,
    "prompt_cache_miss_tokens": 73682,
    "prompt_tokens": 84946,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 11264
    },
    "total_tokens": 91175
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

### Revision and Package Evidence

- [candidate-revision.json](candidate-revision.json)
- [component-preservation.json](component-preservation.json)
- [revision-gates.json](revision-gates.json)
- [changeset-round-01/change-scope.json](changeset-round-01/change-scope.json)
- [changeset-round-01/changeset.json](changeset-round-01/changeset.json)
