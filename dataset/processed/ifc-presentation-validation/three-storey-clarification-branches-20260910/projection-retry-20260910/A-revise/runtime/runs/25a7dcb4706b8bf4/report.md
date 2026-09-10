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
    "created_at": "2026-09-10T08:27:57+00:00",
    "role": "user",
    "text": "请生成一栋三层的小型社区阅读活动楼，输出完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静阅览厅，三层是多功能活动厅，东侧为独立楼梯间。采用 warm-residential 协调风格，浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐。需要真实的窗框、玻璃面板、门框、门扇和楼梯踏步；本次不做光庭、家具、花草、机电、栏杆、复杂五金或外伸装饰。\n\n室内净尺寸东西10米、南北8.4米，外墙厚200毫米。首层、二层、三层完成面标高分别为0、3150、6300毫米，每层净高3000毫米。地坪及两块层间楼板厚150毫米，顶面与所属层完成面齐平；平屋面底标高9300毫米、厚150毫米。地坪、楼板与屋面覆盖外墙外边界。二层和三层楼板各留一个真实穿透的楼梯洞口，不能用完整楼板封住楼梯。各层墙独立建模。\n\n以首层室内西南角为原点，向东为X、向北为Y、向上为Z。每层西侧大厅净范围X=0～7600、Y=0～8400；分隔墙完整占X=7600～7800、Y=0～8400；楼梯间净范围X=7800～10000、Y=0～8400。三层分隔墙都保持这一完整长度，不按小平台的接邻长度缩短，也不重复建墙。每层分隔墙开一樘900宽、2100高的右单开门：首层及三层门中心距室内南边700毫米，二层距南边7650毫米；门底与本层完成面齐平。\n\n两段直跑楼梯都位于X=8200～9400、Y=1500～6900，净宽1200毫米。第一段从首层南端向北升到二层北端，标高0到3150；第二段从二层北端反向向南升到三层南端，标高3150到6300。每段18个踢面、每个高175毫米，18个踏面、进深300毫米；两段分别属于出发楼层并连接上一层。二层及三层楼板洞口平面范围都为X=8000～9600、Y=1500～6900，分别穿透各自的150毫米楼板；屋面不留洞。二层北端Y=6900～8400为换向平台，三层南端Y=0～1500为到达平台。首层建大厅与整间楼梯间两个空间，二层建大厅与北端平台两个空间，三层建大厅与南端平台两个空间；平台的X范围都是7800～10000。共6个空间，不把楼梯洞口当成房间。\n\n首层南墙主入口中心距室内西边3800毫米，宽1200、高2400，左单开，门底与首层地坪齐平。每层南墙两扇双竖面板窗，中心距室内西边分别为1700、5900毫米，宽1800、高1500、窗台高900。每层北墙一扇双竖面板窗，中心距西边3800毫米，宽2400、高1500、窗台高900。每层西墙一扇双竖面板窗，中心距南边4200毫米，宽1800、高1500、窗台高900。每层东墙一扇单面板窗，中心距南边4200毫米，宽900、高1800、窗台高600。窗台均从所属层完成面起算。共4樘门、15扇窗，门窗开口与名义宽高相同并穿透自己的宿主墙。\n\n墙体物理材料为砖；地坪、两块层间楼板和屋面物理材料为混凝土。其他构件不指定物理材料，不要由木色或透明样式推断材料。未指定强度、耐火、承重、热工性能，也未要求共享Type，不要自动补属性或强制合并Type。如果有真实冲突请明确指出，不要悄悄改变尺寸、位置或关系。",
    "turn_index": 0
  },
  {
    "created_at": "2026-09-10T08:27:57+00:00",
    "role": "assistant",
    "text": "参考 IFC 中，一层通往二层的楼梯接近北端平台时，被上方反向梯段遮挡，局部净空为零。请确认是调整楼梯及关联布局，还是保留原要求并在 Audit 和报告中记录这个问题。",
    "turn_index": 1
  },
  {
    "created_at": "2026-09-10T08:27:57+00:00",
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
  "case_id": "25a7dcb4706b8bf4",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\output.ifc",
  "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4",
  "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\report.md",
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

- [runs/25a7dcb4706b8bf4/session-export.json](runs/25a7dcb4706b8bf4/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-09-10T08:31:52+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "25a7dcb4706b8bf4",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "live",
      "output_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/projection-retry-20260910/A-revise/runtime/runs/25a7dcb4706b8bf4/generator",
      "response_id": "5a128915-d923-422e-a392-460a50004142",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T08:31:52+00:00",
    "event_index": 1,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
      "case_id": "25a7dcb4706b8bf4",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 75,
        "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
        "case_id": "25a7dcb4706b8bf4",
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
            "path": "/known_facts/building/exterior_wall_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 200
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/floor_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
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
            "path": "/known_facts/design_review/accepted_area_change",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "每层大厅减少2.52平方米"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/design_review/decision",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "用户选择调整内部布局以消除参考 IFC 中楼梯局部净空为零的问题，不向外扩建"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/design_review/full_engineering_or_code_review",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": false
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/design_review/scope",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "仅记录本次内部布局修订"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/excluded_elements",
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
            "path": "/known_facts/expected_counts/doors",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 4
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/expected_counts/spaces",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 6
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/expected_counts/stairs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 2
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/expected_counts/storeys",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 3
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/expected_counts/windows",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 15
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
                "id": "slab-ground",
                "openings": [],
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
                "id": "slab-storey-2",
                "openings": [
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
                    "id": "slab-storey-2-opening-stair",
                    "purpose": "stair"
                  }
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
                "id": "slab-storey-3",
                "openings": [
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
                    "id": "slab-storey-3-opening-stair",
                    "purpose": "stair"
                  }
                ],
                "storey": "storey-3",
                "thickness_mm": 150,
                "top_elevation_mm": 6300
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/ifc_schema",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "IFC2X3"
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
            "path": "/known_facts/roof_slab/storey",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "storey-3"
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
                "entity_id": "slab-storey-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "slab-storey-3",
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
                "id": "stair-flight-1",
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
                "opening_host": "slab-storey-2",
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
                "id": "stair-flight-2",
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
                "opening_host": "slab-storey-3",
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
                    "sill_height_mm": 0,
                    "swing_side": "left",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
                    "width_mm": 1200
                  },
                  {
                    "center_global_mm": [
                      7400,
                      700
                    ],
                    "height_mm": 2100,
                    "host_wall": "storey-1-wall-partition",
                    "id": "storey-1-door-partition",
                    "sill_height_mm": 0,
                    "swing_side": "right",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 0,
                "function": "接待阅览厅",
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
                    "name": "接待阅览厅"
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
                          -200,
                          8600
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
                          -200,
                          8600
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 600,
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
                    "width_mm": 900
                  }
                ]
              },
              {
                "doors": [
                  {
                    "center_global_mm": [
                      7400,
                      7650
                    ],
                    "height_mm": 2100,
                    "host_wall": "storey-2-wall-partition",
                    "id": "storey-2-door-partition",
                    "sill_height_mm": 0,
                    "swing_side": "right",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 3150,
                "function": "安静阅览厅",
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
                    "name": "安静阅览厅"
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
                          -200,
                          8600
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
                          -200,
                          8600
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 600,
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
                    "width_mm": 900
                  }
                ]
              },
              {
                "doors": [
                  {
                    "center_global_mm": [
                      7400,
                      700
                    ],
                    "height_mm": 2100,
                    "host_wall": "storey-3-wall-partition",
                    "id": "storey-3-door-partition",
                    "sill_height_mm": 0,
                    "swing_side": "right",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 6300,
                "function": "多功能活动厅",
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
                    "name": "多功能活动厅"
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
                          -200,
                          8600
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
                          -200,
                          8600
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 900,
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
                    "sill_height_mm": 600,
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    },
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
      },
      "fact_count": 36,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T08:31:52+00:00",
    "event_index": 2,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "25a7dcb4706b8bf4",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/projection-retry-20260910/A-revise/runtime/runs/25a7dcb4706b8bf4/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "5a128915-d923-422e-a392-460a50004142",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T08:32:07+00:00",
    "event_index": 3,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "25a7dcb4706b8bf4",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "fb2a81e3fa22bf0a0d476239789c106f3c07f7c21038d2474bf3a0856646c4de",
          "expected-facts.json": "b4c72a90937532b6baff78118fa46486565c039934eb08224be0435f487c8672",
          "generator/candidate.json": "228fdd0b12f9bea2021720d46918d027110e4ddf55bbe7f723ebf90c1cc10f09",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "a96b836da70fc6da4e0fe16818a625c0ebe0be956ba1d5571a0b171ca83cb268",
          "ifc-verification.json": "0cee5734ec38dbd4de90356a4699fdd3bf0a7e2136ae7ec28409c7864a508352",
          "repair/route.json": "61f4db38058de56fc0f35159e03f4e5f5ef9c621d83e75d8d4154468338c88c0",
          "request-semantics.json": "c65b2593855d791b546cb1b146ea73949a99c1358776dc2cd97f74276a97bf66",
          "semantic-coverage.json": "b220c4a31fbef3034f4acf903a213c508831e9e3c65a527cad026b105ea01ba5",
          "semantic-verification.json": "3f242870fded94cb7665da782d458dc6f52e05d6af020a32ba1f8ed77e426d00"
        },
        "candidate_hash": "228fdd0b12f9bea2021720d46918d027110e4ddf55bbe7f723ebf90c1cc10f09",
        "candidate_path": "generator/candidate.json",
        "case_id": "25a7dcb4706b8bf4",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "25a7dcb4706b8bf4",
              "floor_openings": {
                "slab-storey-2-opening-stair": {
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
                  "host_slab_id": "slab-storey-2",
                  "ifc_class": "IfcOpeningElement",
                  "resolved_bim_json_id": "slab-storey-2-opening-stair",
                  "resolved_global_id": "0WKeTbtWbI2O3zqN4nzkr0"
                },
                "slab-storey-3-opening-stair": {
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
                  "host_slab_id": "slab-storey-3",
                  "ifc_class": "IfcOpeningElement",
                  "resolved_bim_json_id": "slab-storey-3-opening-stair",
                  "resolved_global_id": "3VGC770UTOXPgqn7oTcfhU"
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
                },
                "slab-storey-2": {
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
                "slab-storey-3": {
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
                }
              },
              "spaces": {
                "space-storey-1-storey-1-space-hall": {
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
                "space-storey-1-storey-1-space-stairwell": {
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
                "space-storey-2-storey-2-space-hall": {
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
                "space-storey-2-storey-2-space-landing-north": {
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
                "space-storey-3-storey-3-space-hall": {
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
                "space-storey-3-storey-3-space-landing-south": {
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
                "stair-flight-1": {
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
                    "stair-flight-flight-1"
                  ],
                  "has_stepped_profile": true,
                  "wall_intersections": []
                },
                "stair-flight-2": {
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
                    "stair-flight-flight-2"
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
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
                },
                "wall-storey-1-storey-1-wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.2,
                      0.0
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWallStandardCase"
                },
                "wall-storey-2-storey-2-wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      10.0,
                      10.2
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
                },
                "wall-storey-2-storey-2-wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.2,
                      0.0
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWallStandardCase"
                },
                "wall-storey-3-storey-3-wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      10.0,
                      10.2
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
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
                  "ifc_class": "IfcWallStandardCase"
                },
                "wall-storey-3-storey-3-wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.2,
                      0.0
                    ],
                    "y": [
                      -0.20000000000000018,
                      8.600000000000001
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWallStandardCase"
                }
              }
            },
            "success": true
          },
          "repair_history": {
            "case_id": "25a7dcb4706b8bf4",
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
            "source_generator_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/projection-retry-20260910/A-revise/runtime/runs/25a7dcb4706b8bf4/generator",
            "source_generator_response_id": "5a128915-d923-422e-a392-460a50004142",
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
                "entity_id": "slab-storey-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-storey-3",
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
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/doors/0",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-partition",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/doors/1",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-1",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/0",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-2",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/1",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-north",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/2",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-west",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/3",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-east",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/4",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-partition",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/doors/0",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-1",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/0",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-2",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/1",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-north",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/2",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-west",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/3",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-east",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/4",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-3-storey-3-door-partition",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/doors/0",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-1",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/0",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-2",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/1",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-north",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/2",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-west",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/3",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-east",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/4",
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
                "entity_id": "slab-storey-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "slab-storey-3",
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
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/doors/0",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-1-storey-1-door-partition",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/doors/1",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-1",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/0",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-south-2",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/1",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-north",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/2",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-west",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/3",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-1-storey-1-window-east",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/0/windows/4",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-2-storey-2-door-partition",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/doors/0",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-1",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/0",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-south-2",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/1",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-north",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/2",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-west",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/3",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-2-storey-2-window-east",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/1/windows/4",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "door-storey-3-storey-3-door-partition",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/doors/0",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-1",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/0",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-south-2",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/1",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-north",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/2",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-west",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/3",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "window-storey-3-storey-3-window-east",
                "kind": "template",
                "scope": "effective",
                "source_path": "/known_facts/storeys/2/windows/4",
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
            "case_id": "25a7dcb4706b8bf4",
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
                "path": "/known_facts/building/exterior_wall_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 200
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/floor_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
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
                "path": "/known_facts/design_review/accepted_area_change",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "每层大厅减少2.52平方米"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/design_review/decision",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "用户选择调整内部布局以消除参考 IFC 中楼梯局部净空为零的问题，不向外扩建"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/design_review/full_engineering_or_code_review",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": false
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/design_review/scope",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "仅记录本次内部布局修订"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/excluded_elements",
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
                "path": "/known_facts/expected_counts/doors",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 4
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/expected_counts/spaces",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 6
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/expected_counts/stairs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 2
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/expected_counts/storeys",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 3
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/expected_counts/windows",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 15
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
                    "id": "slab-ground",
                    "openings": [],
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
                    "id": "slab-storey-2",
                    "openings": [
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
                        "id": "slab-storey-2-opening-stair",
                        "purpose": "stair"
                      }
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
                    "id": "slab-storey-3",
                    "openings": [
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
                        "id": "slab-storey-3-opening-stair",
                        "purpose": "stair"
                      }
                    ],
                    "storey": "storey-3",
                    "thickness_mm": 150,
                    "top_elevation_mm": 6300
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/ifc_schema",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "IFC2X3"
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
                "path": "/known_facts/roof_slab/storey",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "storey-3"
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
                    "entity_id": "slab-storey-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "slab-storey-3",
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
                    "id": "stair-flight-1",
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
                    "opening_host": "slab-storey-2",
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
                    "id": "stair-flight-2",
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
                    "opening_host": "slab-storey-3",
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
                        "sill_height_mm": 0,
                        "swing_side": "left",
                        "template": {
                          "template_id": "door-left",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
                        "width_mm": 1200
                      },
                      {
                        "center_global_mm": [
                          7400,
                          700
                        ],
                        "height_mm": 2100,
                        "host_wall": "storey-1-wall-partition",
                        "id": "storey-1-door-partition",
                        "sill_height_mm": 0,
                        "swing_side": "right",
                        "template": {
                          "template_id": "door-right",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 0,
                    "function": "接待阅览厅",
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
                        "name": "接待阅览厅"
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
                              -200,
                              8600
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
                              -200,
                              8600
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 600,
                        "template": {
                          "template_id": "window-single",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          7400,
                          7650
                        ],
                        "height_mm": 2100,
                        "host_wall": "storey-2-wall-partition",
                        "id": "storey-2-door-partition",
                        "sill_height_mm": 0,
                        "swing_side": "right",
                        "template": {
                          "template_id": "door-right",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 3150,
                    "function": "安静阅览厅",
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
                        "name": "安静阅览厅"
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
                              -200,
                              8600
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
                              -200,
                              8600
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 600,
                        "template": {
                          "template_id": "window-single",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          7400,
                          700
                        ],
                        "height_mm": 2100,
                        "host_wall": "storey-3-wall-partition",
                        "id": "storey-3-door-partition",
                        "sill_height_mm": 0,
                        "swing_side": "right",
                        "template": {
                          "template_id": "door-right",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 6300,
                    "function": "多功能活动厅",
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
                        "name": "多功能活动厅"
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
                              -200,
                              8600
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
                              -200,
                              8600
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 900,
                        "template": {
                          "template_id": "window-double-vertical",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
                        "sill_height_mm": 600,
                        "template": {
                          "template_id": "window-single",
                          "template_version": "text2ifc/basic-filling/1.0"
                        },
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
        },
        "expected_facts_hash": "b4c72a90937532b6baff78118fa46486565c039934eb08224be0435f487c8672",
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
          "case_id": "25a7dcb4706b8bf4",
          "floor_openings": {
            "slab-storey-2-opening-stair": {
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
              "host_slab_id": "slab-storey-2",
              "ifc_class": "IfcOpeningElement",
              "resolved_bim_json_id": "slab-storey-2-opening-stair",
              "resolved_global_id": "0WKeTbtWbI2O3zqN4nzkr0"
            },
            "slab-storey-3-opening-stair": {
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
              "host_slab_id": "slab-storey-3",
              "ifc_class": "IfcOpeningElement",
              "resolved_bim_json_id": "slab-storey-3-opening-stair",
              "resolved_global_id": "3VGC770UTOXPgqn7oTcfhU"
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
            },
            "slab-storey-2": {
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
            "slab-storey-3": {
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
            }
          },
          "spaces": {
            "space-storey-1-storey-1-space-hall": {
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
            "space-storey-1-storey-1-space-stairwell": {
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
            "space-storey-2-storey-2-space-hall": {
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
            "space-storey-2-storey-2-space-landing-north": {
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
            "space-storey-3-storey-3-space-hall": {
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
            "space-storey-3-storey-3-space-landing-south": {
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
            "stair-flight-1": {
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
                "stair-flight-flight-1"
              ],
              "has_stepped_profile": true,
              "wall_intersections": []
            },
            "stair-flight-2": {
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
                "stair-flight-flight-2"
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
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
            },
            "wall-storey-1-storey-1-wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.2,
                  0.0
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWallStandardCase"
            },
            "wall-storey-2-storey-2-wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  10.0,
                  10.2
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
            },
            "wall-storey-2-storey-2-wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.2,
                  0.0
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWallStandardCase"
            },
            "wall-storey-3-storey-3-wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  10.0,
                  10.2
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
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
              "ifc_class": "IfcWallStandardCase"
            },
            "wall-storey-3-storey-3-wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.2,
                  0.0
                ],
                "y": [
                  -0.20000000000000018,
                  8.600000000000001
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWallStandardCase"
            }
          }
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\output.ifc",
        "success": true
      },
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4",
      "semantic_geometry_expectation": {
        "case_id": "25a7dcb4706b8bf4",
        "complete": true,
        "doors": {},
        "floor_openings": {
          "slab-storey-2-opening-stair": {
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
            "host_slab_id": "slab-storey-2",
            "identity_source": "explicit",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/openings/0"
            ]
          },
          "slab-storey-3-opening-stair": {
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
            "host_slab_id": "slab-storey-3",
            "identity_source": "explicit",
            "source_fact_refs": [
              "/known_facts/floor_slabs/2/openings/0"
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
          },
          "slab-storey-2": {
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
          "slab-storey-3": {
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
          "space-storey-1-storey-1-space-stairwell": {
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
          "space-storey-2-storey-2-space-hall": {
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
          "space-storey-2-storey-2-space-landing-north": {
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
          "space-storey-3-storey-3-space-hall": {
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
          "space-storey-3-storey-3-space-landing-south": {
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
          "stair-flight-1": {
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
              "stair-flight-flight-1"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          },
          "stair-flight-2": {
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
              "stair-flight-flight-2"
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
                -0.2,
                8.6
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
                -0.2,
                8.6
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
                -0.2,
                8.6
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
                -0.2,
                8.6
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
                -0.2,
                8.6
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
                -0.2,
                8.6
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
            "entity_id": "slab-storey-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-storey-3",
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
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/doors/0",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-partition",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/doors/1",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-1",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/0",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-2",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/1",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-north",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/2",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-west",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/3",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-east",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/4",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-partition",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/doors/0",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-1",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/0",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-2",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/1",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-north",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/2",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-west",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/3",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-east",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/4",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-3-storey-3-door-partition",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/doors/0",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-1",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/0",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-2",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/1",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-north",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/2",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-west",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/3",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-east",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/4",
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
            "entity_id": "slab-storey-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "slab-storey-3",
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
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/doors/0",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-1-storey-1-door-partition",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/doors/1",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-1",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/0",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-south-2",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/1",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-north",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/2",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-west",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/3",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-1-storey-1-window-east",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/0/windows/4",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-2-storey-2-door-partition",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/doors/0",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-1",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/0",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-south-2",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/1",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-north",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/2",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-west",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/3",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-2-storey-2-window-east",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/1/windows/4",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "door-storey-3-storey-3-door-partition",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/doors/0",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-1",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/0",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-south-2",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/1",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-north",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/2",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-west",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/3",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "window-storey-3-storey-3-window-east",
            "kind": "template",
            "scope": "effective",
            "source_path": "/known_facts/storeys/2/windows/4",
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
    "created_at": "2026-09-10T08:32:38+00:00",
    "event_index": 4,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "25a7dcb4706b8bf4",
      "evidence_class": "live",
      "output_dir": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/projection-retry-20260910/A-revise/runtime/runs/25a7dcb4706b8bf4",
      "report_path": "dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/projection-retry-20260910/A-revise/runtime/runs/25a7dcb4706b8bf4/report.md",
      "response_id": "3083fb3f-f57b-4f01-8b56-099abffb6b7d",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "event_index": 5,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "25a7dcb4706b8bf4",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\output.ifc",
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4",
      "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\three-storey-clarification-branches-20260910\\projection-retry-20260910\\A-revise\\runtime\\runs\\25a7dcb4706b8bf4\\report.md",
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
    "created_at": "2026-09-10T08:29:38+00:00",
    "kind": "expected_facts",
    "path": "runs/25a7dcb4706b8bf4/expected-facts.json"
  },
  {
    "created_at": "2026-09-10T08:31:52+00:00",
    "kind": "candidate",
    "path": "runs/25a7dcb4706b8bf4/candidate.json"
  },
  {
    "created_at": "2026-09-10T08:31:52+00:00",
    "kind": "semantic_capabilities",
    "path": "runs/25a7dcb4706b8bf4/semantic-capabilities.json"
  },
  {
    "created_at": "2026-09-10T08:31:52+00:00",
    "kind": "semantic_coverage",
    "path": "runs/25a7dcb4706b8bf4/semantic-coverage.json"
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "kind": "issues",
    "path": "runs/25a7dcb4706b8bf4/issues.json"
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "kind": "route_decision",
    "path": "runs/25a7dcb4706b8bf4/route-decision.json"
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "kind": "feedback_rounds",
    "path": "runs/25a7dcb4706b8bf4/feedback-rounds.json"
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "kind": "ifc",
    "path": "runs/25a7dcb4706b8bf4/output.ifc"
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "kind": "report",
    "path": "runs/25a7dcb4706b8bf4/report.md"
  },
  {
    "created_at": "2026-09-10T08:32:54+00:00",
    "kind": "session_export",
    "path": "runs/25a7dcb4706b8bf4/session-export.json"
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
      "description": "参考 IFC 中一层通往二层的梯段接近二层北端换向平台时，与上方反向梯段在同一平面上重叠，局部净空为零。用户在 turn-user-003 确认采用调整内部布局的方案：三层分隔墙西移300毫米至X=7300～7500，两段梯段平面分离为第一段X=7500～8700、第二段X=8800～10000，楼板洞口与分隔墙门随之西移，外轮廓/标高/外墙门窗/材料不变。经模型核对，候选 IFC 的两段梯段平面不再重叠（第一段 bbox x[7.5,8.7]、第二段 bbox x[8.8,10.0]），二层楼板洞口 x[7.5,8.7]、三层楼板洞口 x[8.8,10.0]，与设计简报 /known_facts/stairs 与 /known_facts/floor_slabs 的确认修订一致，确定性几何 Gate 未报告净空冲突。但仅凭模型检查不构成独立的梯段净空/疏散工程验证，因此该潜在净空问题在本审计中标记为未独立验证，未被独立工程复核确认消除。",
      "evidence_paths": [
        "design-review-context.json"
      ],
      "id": "reference-stair-walking-clearance",
      "status": "not_verified"
    }
  ],
  "limitations": [
    "未进行完整建筑规范审查。",
    "未进行独立的梯段净空、疏散或结构工程复核；本审计仅基于已通过的确定性 Gate 与模型几何一致性检查。"
  ],
  "scope": "limited_review_not_code_compliance"
}
```
