# Phase 6.2 Interactive CLI Run Report

Generated from SQLite session records and linked trace artifacts.

## Original Input

```text
请生成一栋三层的小型社区阅读活动楼，输出完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静阅览厅，三层是多功能活动厅，东侧为独立楼梯间。采用 warm-residential 协调风格，浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐。需要真实的窗框、玻璃面板、门框、门扇和楼梯踏步；本次不做光庭、家具、花草、机电、栏杆、复杂五金或外伸装饰。

室内净尺寸东西10米、南北8.4米，外墙厚200毫米。首层、二层、三层完成面标高分别为0、3150、6300毫米，每层净高3000毫米。地坪及两块层间楼板厚150毫米，顶面与所属层完成面齐平；平屋面底标高9300毫米、厚150毫米。地坪、楼板与屋面覆盖外墙外边界。二层和三层楼板各留一个真实穿透的楼梯洞口，不能用完整楼板封住楼梯。各层墙独立建模。

以首层室内西南角为原点，向东为X、向北为Y、向上为Z。每层西侧大厅净范围X=0～7600、Y=0～8400；分隔墙完整占X=7600～7800、Y=0～8400；楼梯间净范围X=7800～10000、Y=0～8400。三层分隔墙都保持这一完整长度，不按小平台的接邻长度缩短，也不重复建墙。每层分隔墙开一樘900宽、2100高的右单开门：首层及三层门中心距室内南边700毫米，二层距南边7650毫米；门底与本层完成面齐平。

两段直跑楼梯都位于X=8200～9400、Y=1500～6900，净宽1200毫米。第一段从首层南端向北升到二层北端，标高0到3150；第二段从二层北端反向向南升到三层南端，标高3150到6300。每段18个踢面、每个高175毫米，18个踏面、进深300毫米；两段分别属于出发楼层并连接上一层。二层及三层楼板洞口平面范围都为X=8000～9600、Y=1500～6900，分别穿透各自的150毫米楼板；屋面不留洞。二层北端Y=6900～8400为换向平台，三层南端Y=0～1500为到达平台。首层建大厅与整间楼梯间两个空间，二层建大厅与北端平台两个空间，三层建大厅与南端平台两个空间；平台的X范围都是7800～10000。共6个空间，不把楼梯洞口当成房间。

首层南墙主入口中心距室内西边3800毫米，宽1200、高2400，左单开，门底与首层地坪齐平。每层南墙两扇双竖面板窗，中心距室内西边分别为1700、5900毫米，宽1800、高1500、窗台高900。每层北墙一扇双竖面板窗，中心距西边3800毫米，宽2400、高1500、窗台高900。每层西墙一扇双竖面板窗，中心距南边4200毫米，宽1800、高1500、窗台高900。每层东墙一扇单面板窗，中心距南边4200毫米，宽900、高1800、窗台高600。窗台均从所属层完成面起算。共4樘门、15扇窗，门窗开口与名义宽高相同并穿透自己的宿主墙。

墙体物理材料为砖；地坪、两块层间楼板和屋面物理材料为混凝土。其他构件不指定物理材料，不要由木色或透明样式推断材料。未指定强度、耐火、承重、热工性能，也未要求共享Type，不要自动补属性或强制合并Type。如果有真实冲突请明确指出，不要悄悄改变尺寸、位置或关系。
```

## Transcript

```json
[
  {
    "created_at": "2026-09-10T12:23:13+00:00",
    "role": "user",
    "text": "请生成一栋三层的小型社区阅读活动楼，输出完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静阅览厅，三层是多功能活动厅，东侧为独立楼梯间。采用 warm-residential 协调风格，浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐。需要真实的窗框、玻璃面板、门框、门扇和楼梯踏步；本次不做光庭、家具、花草、机电、栏杆、复杂五金或外伸装饰。\n\n室内净尺寸东西10米、南北8.4米，外墙厚200毫米。首层、二层、三层完成面标高分别为0、3150、6300毫米，每层净高3000毫米。地坪及两块层间楼板厚150毫米，顶面与所属层完成面齐平；平屋面底标高9300毫米、厚150毫米。地坪、楼板与屋面覆盖外墙外边界。二层和三层楼板各留一个真实穿透的楼梯洞口，不能用完整楼板封住楼梯。各层墙独立建模。\n\n以首层室内西南角为原点，向东为X、向北为Y、向上为Z。每层西侧大厅净范围X=0～7600、Y=0～8400；分隔墙完整占X=7600～7800、Y=0～8400；楼梯间净范围X=7800～10000、Y=0～8400。三层分隔墙都保持这一完整长度，不按小平台的接邻长度缩短，也不重复建墙。每层分隔墙开一樘900宽、2100高的右单开门：首层及三层门中心距室内南边700毫米，二层距南边7650毫米；门底与本层完成面齐平。\n\n两段直跑楼梯都位于X=8200～9400、Y=1500～6900，净宽1200毫米。第一段从首层南端向北升到二层北端，标高0到3150；第二段从二层北端反向向南升到三层南端，标高3150到6300。每段18个踢面、每个高175毫米，18个踏面、进深300毫米；两段分别属于出发楼层并连接上一层。二层及三层楼板洞口平面范围都为X=8000～9600、Y=1500～6900，分别穿透各自的150毫米楼板；屋面不留洞。二层北端Y=6900～8400为换向平台，三层南端Y=0～1500为到达平台。首层建大厅与整间楼梯间两个空间，二层建大厅与北端平台两个空间，三层建大厅与南端平台两个空间；平台的X范围都是7800～10000。共6个空间，不把楼梯洞口当成房间。\n\n首层南墙主入口中心距室内西边3800毫米，宽1200、高2400，左单开，门底与首层地坪齐平。每层南墙两扇双竖面板窗，中心距室内西边分别为1700、5900毫米，宽1800、高1500、窗台高900。每层北墙一扇双竖面板窗，中心距西边3800毫米，宽2400、高1500、窗台高900。每层西墙一扇双竖面板窗，中心距南边4200毫米，宽1800、高1500、窗台高900。每层东墙一扇单面板窗，中心距南边4200毫米，宽900、高1800、窗台高600。窗台均从所属层完成面起算。共4樘门、15扇窗，门窗开口与名义宽高相同并穿透自己的宿主墙。\n\n墙体物理材料为砖；地坪、两块层间楼板和屋面物理材料为混凝土。其他构件不指定物理材料，不要由木色或透明样式推断材料。未指定强度、耐火、承重、热工性能，也未要求共享Type，不要自动补属性或强制合并Type。如果有真实冲突请明确指出，不要悄悄改变尺寸、位置或关系。",
    "turn_index": 0
  },
  {
    "created_at": "2026-09-10T12:23:13+00:00",
    "role": "assistant",
    "text": "参考 IFC 中，一层通往二层的楼梯接近北端平台时，被上方反向梯段遮挡，局部净空为零。请确认是调整楼梯及关联布局，还是保留原要求并在 Audit 和报告中记录这个问题。",
    "turn_index": 1
  },
  {
    "created_at": "2026-09-10T12:23:13+00:00",
    "role": "user",
    "text": "我选择调整内部布局，不向外扩建。三层分隔墙均向西移动300毫米，保持200毫米厚，改为X=7300～7500、Y=0～8400。各层大厅净范围改为X=0～7300、Y=0～8400，楼梯间净范围改为X=7500～10000、Y=0～8400。第一段楼梯仍从南向北上升，平面改为X=7500～8700、Y=1500～6900；第二段仍从北向南上升，平面改为X=8800～10000、Y=1500～6900。两段仍各宽1200毫米，18个踢面高175毫米、18个踏面深300毫米，起止标高不变。二层楼板洞口改为X=7500～8700、Y=1500～6900；三层洞口改为X=8800～10000、Y=1500～6900，各自穿透所属楼板，不再保留原位置洞口。二层北端平台及三层南端平台的X范围均改为7500～10000，Y范围不变；首层楼梯间空间同样从X=7500开始。三樘分隔墙门随墙向西移动300毫米，南北位置、宽高及开启侧不变。建筑外轮廓、楼层标高、外墙门窗、材料、配色及其他原要求均不变。我接受每层大厅减少2.52平方米。请保留这次修订记录，Audit 仍须说明未做完整工程和规范审查。",
    "turn_index": 2
  }
]
```

## Design Brief Agent

- [design-brief/input.txt](design-brief/input.txt)
- [design-brief/conversation.json](design-brief/conversation.json)
- [design-brief/prompt-rendered.md](design-brief/prompt-rendered.md)
- [design-brief/request.redacted.json](design-brief/request.redacted.json)
- [design-brief/response.raw.json](design-brief/response.raw.json)
- [design-brief/model-text.txt](design-brief/model-text.txt)
- [design-brief/design-brief.json](design-brief/design-brief.json)
- [design-brief/validation.json](design-brief/validation.json)
- [design-brief/metrics.json](design-brief/metrics.json)

## BIM JSON Generator

- [generator/prompt-rendered.md](generator/prompt-rendered.md)
- [generator/request.redacted.json](generator/request.redacted.json)
- [generator/response.raw.json](generator/response.raw.json)
- [generator/model-text.txt](generator/model-text.txt)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [generator/metrics.json](generator/metrics.json)

## Repair Route

- [repair/route.json](repair/route.json)
- [repair/repair-attempts.json](repair/repair-attempts.json)
- [repair/source-validation.json](repair/source-validation.json)
- [repair/metrics.json](repair/metrics.json)

## Audit Agent

- [audit/prompt-rendered.md](audit/prompt-rendered.md)
- [audit/request.redacted.json](audit/request.redacted.json)
- [audit/response.raw.json](audit/response.raw.json)
- [audit/model-text.txt](audit/model-text.txt)
- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)
- [audit/metrics.json](audit/metrics.json)

## Semantic Coverage

- [semantic-capabilities.json](semantic-capabilities.json)
- [semantic-coverage.json](semantic-coverage.json)
- [semantic-geometry-expectation.json](semantic-geometry-expectation.json)

## Deterministic Gates

- [acceptance-metrics.json](acceptance-metrics.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [secret-scan.json](secret-scan.json)

```json
{
  "case_id": "6b4c8ce023e02a07",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\output.ifc",
  "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07",
  "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Revision and ChangeSet History

```json
{
  "issues": [],
  "reason": "No candidate revision sidecar exists for this legacy run.",
  "status": "not_applicable"
}
```


## Final Artifacts

- [output.ifc](output.ifc)
- [candidate.json](candidate.json)
- [report.md](report.md)

## Session Export

- [runs/6b4c8ce023e02a07/session-export.json](runs/6b4c8ce023e02a07/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-09-10T12:26:41+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "6b4c8ce023e02a07",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "live",
      "output_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/A-revise/runtime/runs/6b4c8ce023e02a07/generator",
      "response_id": "269e7f68-67e7-4777-abb9-59cf9b235687",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T12:26:42+00:00",
    "event_index": 1,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
      "case_id": "6b4c8ce023e02a07",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 75,
        "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
        "case_id": "6b4c8ce023e02a07",
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
            "value": "浅暖色墙面配深色细框、玻璃透明、入口清楚、门窗上下对齐；主题配色为构件级协调默认，不覆盖物理材料，也不构成构件级颜色/透明度数值覆盖"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/floor_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/id",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "building-community-reading"
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
            "path": "/known_facts/building/roof_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_count",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 3
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/units",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "MILLIMETRE"
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
                "covers_exterior_wall_outer_boundary": true,
                "id": "slab-ground",
                "name": "首层地坪",
                "openings": [],
                "storey": "storey-1",
                "thickness_mm": 150,
                "top_elevation_mm": 0,
                "top_flush_with_storey_finish": true
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
                "covers_exterior_wall_outer_boundary": true,
                "id": "slab-2-floor",
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
                  "id": "slab-2-opening-stair",
                  "real_through_opening": true
                },
                "storey": "storey-2",
                "thickness_mm": 150,
                "top_elevation_mm": 3150,
                "top_flush_with_storey_finish": true
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
                "covers_exterior_wall_outer_boundary": true,
                "id": "slab-3-floor",
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
                  "id": "slab-3-opening-stair",
                  "real_through_opening": true
                },
                "storey": "storey-3",
                "thickness_mm": 150,
                "top_elevation_mm": 6300,
                "top_flush_with_storey_finish": true
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
            "path": "/known_facts/roof_slab/covers_exterior_wall_outer_boundary",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": true
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/flat_roof",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": true
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
                "entity_id": "slab-ground",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "slab-2-floor",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "slab-3-floor",
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
                "entity_id": "door-1-main-entrance",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-1-partition",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-2-partition",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-3-partition",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-1-south-a",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-1-south-b",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-1-north",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-1-west",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-1-east",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-2-south-a",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-2-south-b",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-2-north",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-2-west",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-2-east",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-3-south-a",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-3-south-b",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-3-north",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-3-west",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-3-east",
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
                "name": "第一段直跑楼梯",
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
                "owning_storey": "storey-1",
                "riser_height_mm": 175,
                "run_direction": "南端起步、向北上升",
                "start_elevation_mm": 0,
                "straight_flight": true,
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
                "name": "第二段直跑楼梯",
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
                "owning_storey": "storey-2",
                "riser_height_mm": 175,
                "run_direction": "北端起步、反向南上升",
                "start_elevation_mm": 3150,
                "straight_flight": true,
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
                    "bottom_at_storey_finish": true,
                    "center_global_mm": [
                      3800,
                      -100
                    ],
                    "hand": "left",
                    "height_mm": 2400,
                    "host_wall": "storey-1-wall-south",
                    "id": "door-1-main-entrance",
                    "name": "首层南墙主入口",
                    "sill_height_mm": 0,
                    "template_id": "door-left",
                    "width_mm": 1200
                  },
                  {
                    "bottom_at_storey_finish": true,
                    "center_from_interior_south_mm": 700,
                    "center_global_mm": [
                      7400,
                      700
                    ],
                    "hand": "right",
                    "height_mm": 2100,
                    "host_wall": "storey-1-wall-partition",
                    "id": "door-1-partition",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "name": "首层接待阅览厅",
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
                    "id": "space-1-hall",
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
                    "id": "space-1-stair-room",
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
                          7300,
                          7500
                        ],
                        "y": [
                          0,
                          8400
                        ]
                      },
                      "connects": [
                        "space-1-hall",
                        "space-1-stair-room"
                      ],
                      "full_length_required": true,
                      "height_mm": 3000,
                      "id": "storey-1-wall-partition",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_from_interior_west_mm": 1700,
                    "center_global_mm": [
                      1700,
                      -100
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-1-wall-south",
                    "id": "window-1-south-a",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_west_mm": 5900,
                    "center_global_mm": [
                      5900,
                      -100
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-1-wall-south",
                    "id": "window-1-south-b",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_west_mm": 3800,
                    "center_global_mm": [
                      3800,
                      8500
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-1-wall-north",
                    "id": "window-1-north",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 2400
                  },
                  {
                    "center_from_interior_south_mm": 4200,
                    "center_global_mm": [
                      -100,
                      4200
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-1-wall-west",
                    "id": "window-1-west",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_south_mm": 4200,
                    "center_global_mm": [
                      10100,
                      4200
                    ],
                    "height_mm": 1800,
                    "host_wall": "storey-1-wall-east",
                    "id": "window-1-east",
                    "sill_height_mm": 600,
                    "template_id": "window-single",
                    "width_mm": 900
                  }
                ]
              },
              {
                "doors": [
                  {
                    "bottom_at_storey_finish": true,
                    "center_from_interior_south_mm": 7650,
                    "center_global_mm": [
                      7400,
                      7650
                    ],
                    "hand": "right",
                    "height_mm": 2100,
                    "host_wall": "storey-2-wall-partition",
                    "id": "door-2-partition",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 3150,
                "id": "storey-2",
                "name": "二层安静阅览厅",
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
                    "id": "space-2-hall",
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
                    "id": "space-2-platform-north",
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
                          7300,
                          7500
                        ],
                        "y": [
                          0,
                          8400
                        ]
                      },
                      "connects": [
                        "space-2-hall",
                        "space-2-platform-north"
                      ],
                      "full_length_required": true,
                      "height_mm": 3000,
                      "id": "storey-2-wall-partition",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_from_interior_west_mm": 1700,
                    "center_global_mm": [
                      1700,
                      -100
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-2-wall-south",
                    "id": "window-2-south-a",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_west_mm": 5900,
                    "center_global_mm": [
                      5900,
                      -100
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-2-wall-south",
                    "id": "window-2-south-b",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_west_mm": 3800,
                    "center_global_mm": [
                      3800,
                      8500
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-2-wall-north",
                    "id": "window-2-north",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 2400
                  },
                  {
                    "center_from_interior_south_mm": 4200,
                    "center_global_mm": [
                      -100,
                      4200
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-2-wall-west",
                    "id": "window-2-west",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_south_mm": 4200,
                    "center_global_mm": [
                      10100,
                      4200
                    ],
                    "height_mm": 1800,
                    "host_wall": "storey-2-wall-east",
                    "id": "window-2-east",
                    "sill_height_mm": 600,
                    "template_id": "window-single",
                    "width_mm": 900
                  }
                ]
              },
              {
                "doors": [
                  {
                    "bottom_at_storey_finish": true,
                    "center_from_interior_south_mm": 700,
                    "center_global_mm": [
                      7400,
                      700
                    ],
                    "hand": "right",
                    "height_mm": 2100,
                    "host_wall": "storey-3-wall-partition",
                    "id": "door-3-partition",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 6300,
                "id": "storey-3",
                "name": "三层多功能活动厅",
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
                    "id": "space-3-hall",
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
                    "id": "space-3-platform-south",
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
                          7300,
                          7500
                        ],
                        "y": [
                          0,
                          8400
                        ]
                      },
                      "connects": [
                        "space-3-hall",
                        "space-3-platform-south"
                      ],
                      "full_length_required": true,
                      "height_mm": 3000,
                      "id": "storey-3-wall-partition",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_from_interior_west_mm": 1700,
                    "center_global_mm": [
                      1700,
                      -100
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-3-wall-south",
                    "id": "window-3-south-a",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_west_mm": 5900,
                    "center_global_mm": [
                      5900,
                      -100
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-3-wall-south",
                    "id": "window-3-south-b",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_west_mm": 3800,
                    "center_global_mm": [
                      3800,
                      8500
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-3-wall-north",
                    "id": "window-3-north",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 2400
                  },
                  {
                    "center_from_interior_south_mm": 4200,
                    "center_global_mm": [
                      -100,
                      4200
                    ],
                    "height_mm": 1500,
                    "host_wall": "storey-3-wall-west",
                    "id": "window-3-west",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_from_interior_south_mm": 4200,
                    "center_global_mm": [
                      10100,
                      4200
                    ],
                    "height_mm": 1800,
                    "host_wall": "storey-3-wall-east",
                    "id": "window-3-east",
                    "sill_height_mm": 600,
                    "template_id": "window-single",
                    "width_mm": 900
                  }
                ]
              }
            ]
          }
        ],
        "schema_version": "text2ifc/semantic-coverage/1.0",
        "valid": true
      },
      "fact_count": 35,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T12:26:42+00:00",
    "event_index": 2,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "6b4c8ce023e02a07",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/A-revise/runtime/runs/6b4c8ce023e02a07/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "269e7f68-67e7-4777-abb9-59cf9b235687",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T12:26:57+00:00",
    "event_index": 3,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "6b4c8ce023e02a07",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "64ba541bdcadf582890e4868ddb5d579f8e5ee1e4729f748014b92ecd972f90e",
          "expected-facts.json": "7c8b4f6868df86bb9a2800c33fffb33e010ccc5df49ff24d2ebd3956e7c8246f",
          "generator/candidate.json": "4307f3e366c2426e00b2d258a3c0149164ef1178c1e773537df2ad7b89d7a672",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "683be1b690e36ce9d5e3e67a90d6e4b6ef744d2807c7758faf292efac67b9fba",
          "ifc-verification.json": "6682f3b2571327819b03fc3b5c1d2510b0ece17b9b8a0216a72a215fc03f9a42",
          "repair/route.json": "51d308784a8eae918e78e222b604220c442a1c7f73774774d137282249a70ea4",
          "request-semantics.json": "b5bcaf2a87e32e33790d05716e0714ccd01beca36d534263d54f1af07a149f00",
          "semantic-coverage.json": "bfd621d467c27af8f496e4a9cc671c1c38829dae714a66fc17a22f5f7b80839d",
          "semantic-verification.json": "8249d0faf3d39d380a89c5f169d08beaa42998e50abf2b5a0d6d3a77b63d496e"
        },
        "candidate_hash": "4307f3e366c2426e00b2d258a3c0149164ef1178c1e773537df2ad7b89d7a672",
        "candidate_path": "generator/candidate.json",
        "case_id": "6b4c8ce023e02a07",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "6b4c8ce023e02a07",
              "floor_openings": {
                "slab-2-opening-stair": {
                  "bbox": {
                    "x": [
                      7.5,
                      8.7
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
                  "binding_basis": "explicit_identity",
                  "host_slab_id": "slab-2-floor",
                  "ifc_class": "IfcOpeningElement",
                  "resolved_bim_json_id": "slab-2-opening-stair",
                  "resolved_global_id": "3yJXyx64vR29o9_0jBgP1x"
                },
                "slab-3-opening-stair": {
                  "bbox": {
                    "x": [
                      8.8,
                      10.0
                    ],
                    "y": [
                      1.5,
                      6.9
                    ],
                    "z": [
                      6.15,
                      6.300000000000001
                    ]
                  },
                  "binding_basis": "explicit_identity",
                  "host_slab_id": "slab-3-floor",
                  "ifc_class": "IfcOpeningElement",
                  "resolved_bim_json_id": "slab-3-opening-stair",
                  "resolved_global_id": "02F6JPumPPnBs3NSjutSdN"
                }
              },
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
                "slab-2-floor": {
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
                "slab-3-floor": {
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
                      6.15,
                      6.300000000000001
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "slab-ground": {
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
                }
              },
              "spaces": {
                "space-storey-1-space-1-hall": {
                  "bbox": {
                    "x": [
                      0.0,
                      7.3
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
                "space-storey-1-space-1-stair-room": {
                  "bbox": {
                    "x": [
                      7.5,
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
                "space-storey-2-space-2-hall": {
                  "bbox": {
                    "x": [
                      0.0,
                      7.3
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
                "space-storey-2-space-2-platform-north": {
                  "bbox": {
                    "x": [
                      7.5,
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
                "space-storey-3-space-3-hall": {
                  "bbox": {
                    "x": [
                      0.0,
                      7.3
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
                "space-storey-3-space-3-platform-south": {
                  "bbox": {
                    "x": [
                      7.5,
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
              "stairs": {
                "stair-1": {
                  "bbox": {
                    "x": [
                      7.5,
                      8.7
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
                  "flight_ids": [
                    "stair-flight-1"
                  ],
                  "has_stepped_profile": true,
                  "wall_intersections": []
                },
                "stair-2": {
                  "bbox": {
                    "x": [
                      8.8,
                      10.0
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
                  "flight_ids": [
                    "stair-flight-2"
                  ],
                  "has_stepped_profile": true,
                  "wall_intersections": []
                }
              },
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
                      7.300000000000001,
                      7.5
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
                      7.300000000000001,
                      7.5
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
                      7.300000000000001,
                      7.5
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
            "success": true
          },
          "repair_history": {
            "case_id": "6b4c8ce023e02a07",
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
            "source_generator_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/A-revise/runtime/runs/6b4c8ce023e02a07/generator",
            "source_generator_response_id": "269e7f68-67e7-4777-abb9-59cf9b235687",
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
                "entity_id": "slab-ground",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-2-floor",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-3-floor",
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
                "entity_id": "door-storey-1-door-1-main-entrance",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-door-1-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-door-2-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-3-door-3-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-south-a",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-south-b",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-south-a",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-south-b",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-south-a",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-south-b",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-east",
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
                "entity_id": "slab-ground",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-2-floor",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-3-floor",
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
                "entity_id": "door-storey-1-door-1-main-entrance",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-door-1-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-door-2-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-3-door-3-partition",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-south-a",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-south-b",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-window-1-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-south-a",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-south-b",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-window-2-east",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-south-a",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-south-b",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-north",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-west",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-window-3-east",
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
            "case_id": "6b4c8ce023e02a07",
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
                "value": "浅暖色墙面配深色细框、玻璃透明、入口清楚、门窗上下对齐；主题配色为构件级协调默认，不覆盖物理材料，也不构成构件级颜色/透明度数值覆盖"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/floor_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/id",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "building-community-reading"
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
                "path": "/known_facts/building/roof_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_count",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 3
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/units",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "MILLIMETRE"
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
                    "covers_exterior_wall_outer_boundary": true,
                    "id": "slab-ground",
                    "name": "首层地坪",
                    "openings": [],
                    "storey": "storey-1",
                    "thickness_mm": 150,
                    "top_elevation_mm": 0,
                    "top_flush_with_storey_finish": true
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
                    "covers_exterior_wall_outer_boundary": true,
                    "id": "slab-2-floor",
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
                      "id": "slab-2-opening-stair",
                      "real_through_opening": true
                    },
                    "storey": "storey-2",
                    "thickness_mm": 150,
                    "top_elevation_mm": 3150,
                    "top_flush_with_storey_finish": true
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
                    "covers_exterior_wall_outer_boundary": true,
                    "id": "slab-3-floor",
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
                      "id": "slab-3-opening-stair",
                      "real_through_opening": true
                    },
                    "storey": "storey-3",
                    "thickness_mm": 150,
                    "top_elevation_mm": 6300,
                    "top_flush_with_storey_finish": true
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
                "path": "/known_facts/roof_slab/covers_exterior_wall_outer_boundary",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": true
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/flat_roof",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": true
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
                    "entity_id": "slab-ground",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "slab-2-floor",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "slab-3-floor",
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
                    "entity_id": "door-1-main-entrance",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "door-1-partition",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "door-2-partition",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "door-3-partition",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-1-south-a",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-1-south-b",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-1-north",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-1-west",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-1-east",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-2-south-a",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-2-south-b",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-2-north",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-2-west",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-2-east",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-3-south-a",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-3-south-b",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-3-north",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-3-west",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "window-3-east",
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
                    "name": "第一段直跑楼梯",
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
                    "owning_storey": "storey-1",
                    "riser_height_mm": 175,
                    "run_direction": "南端起步、向北上升",
                    "start_elevation_mm": 0,
                    "straight_flight": true,
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
                    "name": "第二段直跑楼梯",
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
                    "owning_storey": "storey-2",
                    "riser_height_mm": 175,
                    "run_direction": "北端起步、反向南上升",
                    "start_elevation_mm": 3150,
                    "straight_flight": true,
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
                        "bottom_at_storey_finish": true,
                        "center_global_mm": [
                          3800,
                          -100
                        ],
                        "hand": "left",
                        "height_mm": 2400,
                        "host_wall": "storey-1-wall-south",
                        "id": "door-1-main-entrance",
                        "name": "首层南墙主入口",
                        "sill_height_mm": 0,
                        "template_id": "door-left",
                        "width_mm": 1200
                      },
                      {
                        "bottom_at_storey_finish": true,
                        "center_from_interior_south_mm": 700,
                        "center_global_mm": [
                          7400,
                          700
                        ],
                        "hand": "right",
                        "height_mm": 2100,
                        "host_wall": "storey-1-wall-partition",
                        "id": "door-1-partition",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "name": "首层接待阅览厅",
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
                        "id": "space-1-hall",
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
                        "id": "space-1-stair-room",
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
                              7300,
                              7500
                            ],
                            "y": [
                              0,
                              8400
                            ]
                          },
                          "connects": [
                            "space-1-hall",
                            "space-1-stair-room"
                          ],
                          "full_length_required": true,
                          "height_mm": 3000,
                          "id": "storey-1-wall-partition",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_from_interior_west_mm": 1700,
                        "center_global_mm": [
                          1700,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-south",
                        "id": "window-1-south-a",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_west_mm": 5900,
                        "center_global_mm": [
                          5900,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-south",
                        "id": "window-1-south-b",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_west_mm": 3800,
                        "center_global_mm": [
                          3800,
                          8500
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-north",
                        "id": "window-1-north",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 2400
                      },
                      {
                        "center_from_interior_south_mm": 4200,
                        "center_global_mm": [
                          -100,
                          4200
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-1-wall-west",
                        "id": "window-1-west",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_south_mm": 4200,
                        "center_global_mm": [
                          10100,
                          4200
                        ],
                        "height_mm": 1800,
                        "host_wall": "storey-1-wall-east",
                        "id": "window-1-east",
                        "sill_height_mm": 600,
                        "template_id": "window-single",
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "bottom_at_storey_finish": true,
                        "center_from_interior_south_mm": 7650,
                        "center_global_mm": [
                          7400,
                          7650
                        ],
                        "hand": "right",
                        "height_mm": 2100,
                        "host_wall": "storey-2-wall-partition",
                        "id": "door-2-partition",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 3150,
                    "id": "storey-2",
                    "name": "二层安静阅览厅",
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
                        "id": "space-2-hall",
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
                        "id": "space-2-platform-north",
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
                              7300,
                              7500
                            ],
                            "y": [
                              0,
                              8400
                            ]
                          },
                          "connects": [
                            "space-2-hall",
                            "space-2-platform-north"
                          ],
                          "full_length_required": true,
                          "height_mm": 3000,
                          "id": "storey-2-wall-partition",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_from_interior_west_mm": 1700,
                        "center_global_mm": [
                          1700,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-south",
                        "id": "window-2-south-a",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_west_mm": 5900,
                        "center_global_mm": [
                          5900,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-south",
                        "id": "window-2-south-b",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_west_mm": 3800,
                        "center_global_mm": [
                          3800,
                          8500
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-north",
                        "id": "window-2-north",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 2400
                      },
                      {
                        "center_from_interior_south_mm": 4200,
                        "center_global_mm": [
                          -100,
                          4200
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-2-wall-west",
                        "id": "window-2-west",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_south_mm": 4200,
                        "center_global_mm": [
                          10100,
                          4200
                        ],
                        "height_mm": 1800,
                        "host_wall": "storey-2-wall-east",
                        "id": "window-2-east",
                        "sill_height_mm": 600,
                        "template_id": "window-single",
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "bottom_at_storey_finish": true,
                        "center_from_interior_south_mm": 700,
                        "center_global_mm": [
                          7400,
                          700
                        ],
                        "hand": "right",
                        "height_mm": 2100,
                        "host_wall": "storey-3-wall-partition",
                        "id": "door-3-partition",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 6300,
                    "id": "storey-3",
                    "name": "三层多功能活动厅",
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
                        "id": "space-3-hall",
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
                        "id": "space-3-platform-south",
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
                              7300,
                              7500
                            ],
                            "y": [
                              0,
                              8400
                            ]
                          },
                          "connects": [
                            "space-3-hall",
                            "space-3-platform-south"
                          ],
                          "full_length_required": true,
                          "height_mm": 3000,
                          "id": "storey-3-wall-partition",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_from_interior_west_mm": 1700,
                        "center_global_mm": [
                          1700,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-south",
                        "id": "window-3-south-a",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_west_mm": 5900,
                        "center_global_mm": [
                          5900,
                          -100
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-south",
                        "id": "window-3-south-b",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_west_mm": 3800,
                        "center_global_mm": [
                          3800,
                          8500
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-north",
                        "id": "window-3-north",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 2400
                      },
                      {
                        "center_from_interior_south_mm": 4200,
                        "center_global_mm": [
                          -100,
                          4200
                        ],
                        "height_mm": 1500,
                        "host_wall": "storey-3-wall-west",
                        "id": "window-3-west",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_from_interior_south_mm": 4200,
                        "center_global_mm": [
                          10100,
                          4200
                        ],
                        "height_mm": 1800,
                        "host_wall": "storey-3-wall-east",
                        "id": "window-3-east",
                        "sill_height_mm": 600,
                        "template_id": "window-single",
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
        "expected_facts_hash": "7c8b4f6868df86bb9a2800c33fffb33e010ccc5df49ff24d2ebd3956e7c8246f",
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
                "candidate_id": "door-storey-1-door-1-main-entrance",
                "collection": "doors",
                "expected_id": "door-1-main-entrance",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-1-door-1-partition",
                "collection": "doors",
                "expected_id": "door-1-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-2-door-2-partition",
                "collection": "doors",
                "expected_id": "door-2-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "door-storey-3-door-3-partition",
                "collection": "doors",
                "expected_id": "door-3-partition",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-space-1-hall",
                "collection": "spaces",
                "expected_id": "space-1-hall",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-1-space-1-stair-room",
                "collection": "spaces",
                "expected_id": "space-1-stair-room",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-space-2-hall",
                "collection": "spaces",
                "expected_id": "space-2-hall",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-2-space-2-platform-north",
                "collection": "spaces",
                "expected_id": "space-2-platform-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-3-space-3-hall",
                "collection": "spaces",
                "expected_id": "space-3-hall",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "space-storey-3-space-3-platform-south",
                "collection": "spaces",
                "expected_id": "space-3-platform-south",
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
                "candidate_id": "window-storey-1-window-1-south-a",
                "collection": "windows",
                "expected_id": "window-1-south-a",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-window-1-south-b",
                "collection": "windows",
                "expected_id": "window-1-south-b",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-window-1-north",
                "collection": "windows",
                "expected_id": "window-1-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-window-1-west",
                "collection": "windows",
                "expected_id": "window-1-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-1-window-1-east",
                "collection": "windows",
                "expected_id": "window-1-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-window-2-south-a",
                "collection": "windows",
                "expected_id": "window-2-south-a",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-window-2-south-b",
                "collection": "windows",
                "expected_id": "window-2-south-b",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-window-2-north",
                "collection": "windows",
                "expected_id": "window-2-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-window-2-west",
                "collection": "windows",
                "expected_id": "window-2-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-2-window-2-east",
                "collection": "windows",
                "expected_id": "window-2-east",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-window-3-south-a",
                "collection": "windows",
                "expected_id": "window-3-south-a",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-window-3-south-b",
                "collection": "windows",
                "expected_id": "window-3-south-b",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-window-3-north",
                "collection": "windows",
                "expected_id": "window-3-north",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-window-3-west",
                "collection": "windows",
                "expected_id": "window-3-west",
                "match_basis": "canonical_entity_id"
              },
              {
                "candidate_id": "window-storey-3-window-3-east",
                "collection": "windows",
                "expected_id": "window-3-east",
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
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "geometry",
            "source_paths": [
              "geometry-feedback.json"
            ],
            "status": "passed"
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
        "overall_status": "passed",
        "schema_version": "text2ifc/gate-summary/1.0"
      },
      "geometry_feedback": {
        "expectation_source": "design_brief_expected_facts",
        "issues": [],
        "metrics": {
          "case_id": "6b4c8ce023e02a07",
          "floor_openings": {
            "slab-2-opening-stair": {
              "bbox": {
                "x": [
                  7.5,
                  8.7
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
              "binding_basis": "explicit_identity",
              "host_slab_id": "slab-2-floor",
              "ifc_class": "IfcOpeningElement",
              "resolved_bim_json_id": "slab-2-opening-stair",
              "resolved_global_id": "3yJXyx64vR29o9_0jBgP1x"
            },
            "slab-3-opening-stair": {
              "bbox": {
                "x": [
                  8.8,
                  10.0
                ],
                "y": [
                  1.5,
                  6.9
                ],
                "z": [
                  6.15,
                  6.300000000000001
                ]
              },
              "binding_basis": "explicit_identity",
              "host_slab_id": "slab-3-floor",
              "ifc_class": "IfcOpeningElement",
              "resolved_bim_json_id": "slab-3-opening-stair",
              "resolved_global_id": "02F6JPumPPnBs3NSjutSdN"
            }
          },
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
            "slab-2-floor": {
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
            "slab-3-floor": {
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
                  6.15,
                  6.300000000000001
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "slab-ground": {
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
            }
          },
          "spaces": {
            "space-storey-1-space-1-hall": {
              "bbox": {
                "x": [
                  0.0,
                  7.3
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
            "space-storey-1-space-1-stair-room": {
              "bbox": {
                "x": [
                  7.5,
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
            "space-storey-2-space-2-hall": {
              "bbox": {
                "x": [
                  0.0,
                  7.3
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
            "space-storey-2-space-2-platform-north": {
              "bbox": {
                "x": [
                  7.5,
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
            "space-storey-3-space-3-hall": {
              "bbox": {
                "x": [
                  0.0,
                  7.3
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
            "space-storey-3-space-3-platform-south": {
              "bbox": {
                "x": [
                  7.5,
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
          "stairs": {
            "stair-1": {
              "bbox": {
                "x": [
                  7.5,
                  8.7
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
              "flight_ids": [
                "stair-flight-1"
              ],
              "has_stepped_profile": true,
              "wall_intersections": []
            },
            "stair-2": {
              "bbox": {
                "x": [
                  8.8,
                  10.0
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
              "flight_ids": [
                "stair-flight-2"
              ],
              "has_stepped_profile": true,
              "wall_intersections": []
            }
          },
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
                  7.300000000000001,
                  7.5
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
                  7.300000000000001,
                  7.5
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
                  7.300000000000001,
                  7.5
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
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\output.ifc",
        "success": true
      },
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07",
      "semantic_geometry_expectation": {
        "case_id": "6b4c8ce023e02a07",
        "complete": true,
        "doors": {},
        "floor_openings": {
          "slab-2-opening-stair": {
            "bbox": {
              "x": [
                7.5,
                8.7
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
            "host_slab_id": "slab-2-floor",
            "identity_source": "explicit",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/opening"
            ]
          },
          "slab-3-opening-stair": {
            "bbox": {
              "x": [
                8.8,
                10.0
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
            "host_slab_id": "slab-3-floor",
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
          "slab-2-floor": {
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
          "slab-3-floor": {
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
          },
          "slab-ground": {
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
          }
        },
        "source": "design_brief_expected_facts",
        "spaces": {
          "space-storey-1-space-1-hall": {
            "bbox": {
              "x": [
                0.0,
                7.3
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
          "space-storey-1-space-1-stair-room": {
            "bbox": {
              "x": [
                7.5,
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
          "space-storey-2-space-2-hall": {
            "bbox": {
              "x": [
                0.0,
                7.3
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
          "space-storey-2-space-2-platform-north": {
            "bbox": {
              "x": [
                7.5,
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
          "space-storey-3-space-3-hall": {
            "bbox": {
              "x": [
                0.0,
                7.3
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
          "space-storey-3-space-3-platform-south": {
            "bbox": {
              "x": [
                7.5,
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
          "stair-1": {
            "bbox": {
              "x": [
                7.5,
                8.7
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
              "stair-flight-1"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          },
          "stair-2": {
            "bbox": {
              "x": [
                8.8,
                10.0
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
              "stair-flight-2"
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
                7.3,
                7.5
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
                7.3,
                7.5
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
                7.3,
                7.5
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
            "entity_id": "slab-ground",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-2-floor",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-3-floor",
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
            "entity_id": "door-storey-1-door-1-main-entrance",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-door-1-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-door-2-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-3-door-3-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-south-a",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-south-b",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-south-a",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-south-b",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-south-a",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-south-b",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-east",
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
            "entity_id": "slab-ground",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-2-floor",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-3-floor",
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
            "entity_id": "door-storey-1-door-1-main-entrance",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-door-1-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-door-2-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-3-door-3-partition",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-south-a",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-south-b",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-window-1-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-south-a",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-south-b",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-window-2-east",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-south-a",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-south-b",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-north",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-west",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-window-3-east",
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
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T12:27:37+00:00",
    "event_index": 4,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "6b4c8ce023e02a07",
      "evidence_class": "live",
      "output_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/A-revise/runtime/runs/6b4c8ce023e02a07",
      "report_path": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/A-revise/runtime/runs/6b4c8ce023e02a07/report.md",
      "response_id": "9ca6481b-0c82-4486-8708-3c88183fd5ff",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T12:27:52+00:00",
    "event_index": 5,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "6b4c8ce023e02a07",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\output.ifc",
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07",
      "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\failure-recovery-rerun-20260910\\A-revise\\runtime\\runs\\6b4c8ce023e02a07\\report.md",
      "secret_finding_count": 0,
      "stage": "final-acceptance",
      "valid": true
    }
  }
]
```

### Artifact Index

```json
[
  {
    "created_at": "2026-09-10T12:24:51+00:00",
    "kind": "expected_facts",
    "path": "runs/6b4c8ce023e02a07/expected-facts.json"
  },
  {
    "created_at": "2026-09-10T12:26:41+00:00",
    "kind": "candidate",
    "path": "runs/6b4c8ce023e02a07/candidate.json"
  },
  {
    "created_at": "2026-09-10T12:26:41+00:00",
    "kind": "semantic_capabilities",
    "path": "runs/6b4c8ce023e02a07/semantic-capabilities.json"
  },
  {
    "created_at": "2026-09-10T12:26:42+00:00",
    "kind": "semantic_coverage",
    "path": "runs/6b4c8ce023e02a07/semantic-coverage.json"
  },
  {
    "created_at": "2026-09-10T12:27:52+00:00",
    "kind": "issues",
    "path": "runs/6b4c8ce023e02a07/issues.json"
  },
  {
    "created_at": "2026-09-10T12:27:52+00:00",
    "kind": "route_decision",
    "path": "runs/6b4c8ce023e02a07/route-decision.json"
  },
  {
    "created_at": "2026-09-10T12:27:52+00:00",
    "kind": "feedback_rounds",
    "path": "runs/6b4c8ce023e02a07/feedback-rounds.json"
  },
  {
    "created_at": "2026-09-10T12:27:52+00:00",
    "kind": "ifc",
    "path": "runs/6b4c8ce023e02a07/output.ifc"
  },
  {
    "created_at": "2026-09-10T12:27:52+00:00",
    "kind": "report",
    "path": "runs/6b4c8ce023e02a07/report.md"
  },
  {
    "created_at": "2026-09-10T12:27:53+00:00",
    "kind": "session_export",
    "path": "runs/6b4c8ce023e02a07/session-export.json"
  }
]
```


## 合理性问题与用户决定

以下为 Audit 的有限审查记录，技术／请求符合性通过不代表合理性或规范通过。
用户保留的已知问题仍然存在；要求修改也不等于已经独立验证修改成功。
[用户决定与参考证据](design-review-context.json) · [Audit 校验](audit/validation.json)

```json
{
  "concerns": [
    {
      "description": "参考模型显示一层通往二层的第一段梯段在接近二层北端平台处被上方反向的第二段梯段遮挡、局部净空为零；用户在 turn-user-003 明确选择调整内部布局而不保留该缺陷，要求两段梯段平面东西并列。当前候选已按该修订实现：第一段楼梯 stair-1 及其梯段 stair-flight-1 位于 X=7500~8700、Y=1500~6900（标高 0~3150），第二段楼梯 stair-2 及其梯段 stair-flight-2 位于 X=8800~10000、Y=1500~6900（标高 3150~6300），二层楼板洞口 slab-2-opening-stair 随第一段、三层楼板洞口 slab-3-opening-stair 随第二段，两段梯段在平面上不再重叠，上层楼板在梯段上方按洞口真实穿透而非完整封闭；确定性几何 gate（geometry-feedback.json）报告 success=true 且无净空相关 issue。本次仅做候选与已确认修订的一致性检查，未做独立工程净空验算（无独立人体/疏散净空计算、无规范核对），故不判定为已解决或合规，仅记为未独立验证。",
      "evidence_paths": [
        "design-review-context.json",
        "reference-review.json",
        "geometry-feedback.json",
        "generator/candidate.json"
      ],
      "id": "reference-stair-walking-clearance",
      "status": "not_verified"
    }
  ],
  "limitations": [
    "未进行完整建筑规范审查。",
    "未对楼梯净空、疏散、结构、热工、耐火做独立工程验算，仅核对几何与已确认语义是否落位。",
    "确定性 gate 通过仅代表模式、编译、重开、几何与语义覆盖一致，不代表工程合理性。"
  ],
  "scope": "limited_review_not_code_compliance"
}
```
