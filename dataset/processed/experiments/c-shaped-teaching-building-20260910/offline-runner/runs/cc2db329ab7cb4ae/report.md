# Phase 6.2 Interactive CLI Run Report

Generated from SQLite session records and linked trace artifacts.

## Original Input

```text
请帮我建一栋三层的小型教学活动楼，平面做成向东敞开的C形。重点是清楚、整齐、协调，保留中间开敞空间；这次只建建筑本体，不做景观、家具、栏杆和设备，不把模型当作可直接施工的设计。

尺寸按毫米表达，下面提到的距离也给出米，方便读。以建筑外轮廓西南角为定位原点，往东、往北、往上分别是三个正方向。

建筑外包络东西13.2米、南北16.8米。西侧是一条宽4.8米、贯通南北的交通体量；北翼和南翼各向东伸出8.4米，各宽4.8米。中间东侧留出东西8.4米、南北7.2米的开敞缺口，缺口南边距建筑最南端4.8米。三层的外轮廓完全相同，屋面也跟着C形走，不能拿一个完整矩形把中间缺口盖上，也不加跨缺口的桥。

首层、二层、三层完成面标高分别是0、3.15、6.30米；各层净高3米。楼板厚150毫米，顶面与相应完成面齐平；平屋面底面在9.30米，厚150毫米。各层楼板和屋面采用连续C形轮廓。首层楼板没有楼梯洞口，二、三层按下面的楼梯要求真实开洞。

外墙及内部分隔墙统一厚200毫米，墙体全部落在外轮廓以内。外墙沿C形的八条边布置，相邻墙端部连接但不要重复堆叠。每层只有南、北两个教学活动室，以及西侧一个贯通的交通/楼梯空间，共九个空间。教学室与西侧交通空间之间的分隔墙，都放在距建筑西侧4.6到4.8米这一条带内；南室的分隔墙从南端内墙面延伸到4.8米位置，北室的分隔墙从12米位置延伸到北端内墙面。不要再分小教室。

两个教学室的净空间：南室东西4.8到13.0米、南北0.2到4.6米；北室东西4.8到13.0米、南北12.2到16.6米。交通空间的净范围为东西0.2到4.6米、南北0.2到16.6米。空间高度都取3米，与所属楼层对应。

楼梯放在西侧交通空间内，用两个在平面上并列的直跑梯段联系三层：一层到二层的梯段距建筑西侧0.4到1.6米，南北5.4到10.8米，从南向北上升；二层到三层的梯段距西侧2.8到4.0米，南北范围相同，从北向南上升。两段净宽均1.2米，每段18级、每级高175毫米，踏步水平进深300毫米；标高分别0到3.15米、3.15到6.30米。北侧平台利用二层楼板在南北10.8到12米之间的区域，南侧平台利用三层楼板在4.2到5.4米之间的区域，两处平台东西范围均0.2到4.6米，不另叠加一块实体板。二层楼板洞口只对应第一段，三层只对应第二段，洞口平面范围与各自梯段一致，穿透150毫米楼板。

每层南、北教学室各有一扇900毫米宽、2100毫米高的右单开门，都在上述分隔墙上，门中心分别距建筑南侧2.4米和14.4米，门底与本层完成面平齐。首层另设一扇1200毫米宽、2400毫米高的左单开入口门，位于西外墙中间，中心距南侧8.4米。上层不要复制这个入口门。门都带基本门框和门扇，不加复杂五金。

每层七扇窗：南教学室的南外墙、北教学室的北外墙各两扇，中心距西侧7.2米和10.8米；南教学室朝缺口的墙和北教学室朝缺口的墙各一扇，中心距西侧9米。这六扇窗均宽1800毫米、高1500毫米，采用双竖面板。西外墙再设一扇宽900毫米、高1800毫米的单面板窗，中心距南侧2.4米。所有窗台距本层完成面900毫米，窗洞、窗和宿主墙一一对应，三层上下对齐。不要在东侧两个端墙上额外加窗。

墙体明确采用砖，楼板及屋面明确采用混凝土，其他构件暂不指定物理材料。风格用现有warm-residential协调主题：暖浅墙面、深色细门窗框、通透玻璃和与框分色的门扇。不要为了视觉效果增加别的物理材料、整件颜色覆盖或性能属性。我没有要求共享Type；只保留合法表达所需的最小附件。

这些尺寸与布置是本次希望忠实表达的方案。若有必要事实缺失、输入矛盾、当前系统不支持的表达，或你认为会影响使用的明显几何问题，请先集中指出并澄清，不要自行改尺寸或补构件。最终报告应区分用户要求符合性、确定性检查和尚未验证的工程合理性；没有检测到问题也不能写成全面合规。

```

## Transcript

```json
[
  {
    "created_at": "2026-09-10T13:36:50+00:00",
    "role": "user",
    "text": "请帮我建一栋三层的小型教学活动楼，平面做成向东敞开的C形。重点是清楚、整齐、协调，保留中间开敞空间；这次只建建筑本体，不做景观、家具、栏杆和设备，不把模型当作可直接施工的设计。\n\n尺寸按毫米表达，下面提到的距离也给出米，方便读。以建筑外轮廓西南角为定位原点，往东、往北、往上分别是三个正方向。\n\n建筑外包络东西13.2米、南北16.8米。西侧是一条宽4.8米、贯通南北的交通体量；北翼和南翼各向东伸出8.4米，各宽4.8米。中间东侧留出东西8.4米、南北7.2米的开敞缺口，缺口南边距建筑最南端4.8米。三层的外轮廓完全相同，屋面也跟着C形走，不能拿一个完整矩形把中间缺口盖上，也不加跨缺口的桥。\n\n首层、二层、三层完成面标高分别是0、3.15、6.30米；各层净高3米。楼板厚150毫米，顶面与相应完成面齐平；平屋面底面在9.30米，厚150毫米。各层楼板和屋面采用连续C形轮廓。首层楼板没有楼梯洞口，二、三层按下面的楼梯要求真实开洞。\n\n外墙及内部分隔墙统一厚200毫米，墙体全部落在外轮廓以内。外墙沿C形的八条边布置，相邻墙端部连接但不要重复堆叠。每层只有南、北两个教学活动室，以及西侧一个贯通的交通/楼梯空间，共九个空间。教学室与西侧交通空间之间的分隔墙，都放在距建筑西侧4.6到4.8米这一条带内；南室的分隔墙从南端内墙面延伸到4.8米位置，北室的分隔墙从12米位置延伸到北端内墙面。不要再分小教室。\n\n两个教学室的净空间：南室东西4.8到13.0米、南北0.2到4.6米；北室东西4.8到13.0米、南北12.2到16.6米。交通空间的净范围为东西0.2到4.6米、南北0.2到16.6米。空间高度都取3米，与所属楼层对应。\n\n楼梯放在西侧交通空间内，用两个在平面上并列的直跑梯段联系三层：一层到二层的梯段距建筑西侧0.4到1.6米，南北5.4到10.8米，从南向北上升；二层到三层的梯段距西侧2.8到4.0米，南北范围相同，从北向南上升。两段净宽均1.2米，每段18级、每级高175毫米，踏步水平进深300毫米；标高分别0到3.15米、3.15到6.30米。北侧平台利用二层楼板在南北10.8到12米之间的区域，南侧平台利用三层楼板在4.2到5.4米之间的区域，两处平台东西范围均0.2到4.6米，不另叠加一块实体板。二层楼板洞口只对应第一段，三层只对应第二段，洞口平面范围与各自梯段一致，穿透150毫米楼板。\n\n每层南、北教学室各有一扇900毫米宽、2100毫米高的右单开门，都在上述分隔墙上，门中心分别距建筑南侧2.4米和14.4米，门底与本层完成面平齐。首层另设一扇1200毫米宽、2400毫米高的左单开入口门，位于西外墙中间，中心距南侧8.4米。上层不要复制这个入口门。门都带基本门框和门扇，不加复杂五金。\n\n每层七扇窗：南教学室的南外墙、北教学室的北外墙各两扇，中心距西侧7.2米和10.8米；南教学室朝缺口的墙和北教学室朝缺口的墙各一扇，中心距西侧9米。这六扇窗均宽1800毫米、高1500毫米，采用双竖面板。西外墙再设一扇宽900毫米、高1800毫米的单面板窗，中心距南侧2.4米。所有窗台距本层完成面900毫米，窗洞、窗和宿主墙一一对应，三层上下对齐。不要在东侧两个端墙上额外加窗。\n\n墙体明确采用砖，楼板及屋面明确采用混凝土，其他构件暂不指定物理材料。风格用现有warm-residential协调主题：暖浅墙面、深色细门窗框、通透玻璃和与框分色的门扇。不要为了视觉效果增加别的物理材料、整件颜色覆盖或性能属性。我没有要求共享Type；只保留合法表达所需的最小附件。\n\n这些尺寸与布置是本次希望忠实表达的方案。若有必要事实缺失、输入矛盾、当前系统不支持的表达，或你认为会影响使用的明显几何问题，请先集中指出并澄清，不要自行改尺寸或补构件。最终报告应区分用户要求符合性、确定性检查和尚未验证的工程合理性；没有检测到问题也不能写成全面合规。\n",
    "turn_index": 0
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
  "case_id": "cc2db329ab7cb4ae",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\output.ifc",
  "output_dir": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae",
  "report_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\report.md",
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

- [runs/cc2db329ab7cb4ae/session-export.json](runs/cc2db329ab7cb4ae/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-09-10T13:36:51+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "cc2db329ab7cb4ae",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "unit_test_fixture",
      "output_dir": "dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/offline-runner/runs/cc2db329ab7cb4ae/generator",
      "response_id": "response-package-2",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T13:36:51+00:00",
    "event_index": 1,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
      "case_id": "cc2db329ab7cb4ae",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 111,
        "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
        "case_id": "cc2db329ab7cb4ae",
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
            "path": "/known_facts/building/id",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "building-community-reading"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 13200
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
            "value": 16800
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_count",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 3
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/floor_slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds": {
                  "x": [
                    0,
                    13200
                  ],
                  "y": [
                    0,
                    16800
                  ]
                },
                "id": "slab-1",
                "storey": "storey-1",
                "thickness_mm": 150,
                "top_elevation_mm": 0
              },
              {
                "bounds": {
                  "x": [
                    0,
                    13200
                  ],
                  "y": [
                    0,
                    16800
                  ]
                },
                "id": "slab-2",
                "opening": {
                  "bounds": {
                    "x": [
                      400,
                      1600
                    ],
                    "y": [
                      5400,
                      10800
                    ]
                  },
                  "id": "floor-opening-2",
                  "real_through_opening": true
                },
                "storey": "storey-2",
                "thickness_mm": 150,
                "top_elevation_mm": 3150
              },
              {
                "bounds": {
                  "x": [
                    0,
                    13200
                  ],
                  "y": [
                    0,
                    16800
                  ]
                },
                "id": "slab-3",
                "opening": {
                  "bounds": {
                    "x": [
                      2800,
                      4000
                    ],
                    "y": [
                      5400,
                      10800
                    ]
                  },
                  "id": "floor-opening-3",
                  "real_through_opening": true
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
              0,
              13200
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/bounds/y",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              0,
              16800
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
                "entity_id": "wall-1-south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-west",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-east_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-east_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-courtyard_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-courtyard_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-spine",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-partition_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-1-partition_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "slab-1",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "ifcwindow-1-0",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-1",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-2",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-3",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-4",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-5",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-6",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-0",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-1",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-entry",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-2-south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-west",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-east_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-east_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-courtyard_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-courtyard_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-spine",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-partition_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-2-partition_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "slab-2",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "ifcwindow-2-0",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-1",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-2",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-3",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-4",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-5",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-6",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-2-0",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-2-1",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-3-south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-west",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-east_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-east_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-courtyard_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-courtyard_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-spine",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-partition_south",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "wall-3-partition_north",
                "material": {
                  "kind": "single_material",
                  "name": "砖"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "slab-3",
                "material": {
                  "kind": "single_material",
                  "name": "混凝土"
                },
                "scope": "direct",
                "source": "user"
              },
              {
                "entity_id": "ifcwindow-3-0",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-1",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-2",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-3",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-4",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-5",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-6",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-3-0",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-3-1",
                "scope": "direct",
                "source": "user",
                "template": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
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
                    400,
                    1600
                  ],
                  "y": [
                    5400,
                    10800
                  ]
                },
                "end_elevation_mm": 3150,
                "from_storey": "storey-1",
                "id": "stair-1",
                "number_of_risers": 18,
                "number_of_treads": 18,
                "riser_height_mm": 175,
                "start_elevation_mm": 0,
                "to_storey": "storey-2",
                "tread_depth_mm": 300,
                "width_mm": 1200
              },
              {
                "bounds": {
                  "x": [
                    2800,
                    4000
                  ],
                  "y": [
                    5400,
                    10800
                  ]
                },
                "end_elevation_mm": 6300,
                "from_storey": "storey-2",
                "id": "stair-2",
                "number_of_risers": 18,
                "number_of_treads": 18,
                "riser_height_mm": 175,
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
                      4700.0,
                      2400
                    ],
                    "height_mm": 2100,
                    "host_wall": "wall-1-partition_south",
                    "id": "ifcdoor-1-0",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  },
                  {
                    "center_global_mm": [
                      4700.0,
                      14400
                    ],
                    "height_mm": 2100,
                    "host_wall": "wall-1-partition_north",
                    "id": "ifcdoor-1-1",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  },
                  {
                    "center_global_mm": [
                      100.0,
                      8400
                    ],
                    "height_mm": 2400,
                    "host_wall": "wall-1-west",
                    "id": "ifcdoor-1-entry",
                    "sill_height_mm": 0,
                    "template_id": "door-left",
                    "width_mm": 1200
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        4800,
                        13000
                      ],
                      "y": [
                        200,
                        4600
                      ]
                    },
                    "id": "space-1-0"
                  },
                  {
                    "bounds": {
                      "x": [
                        4800,
                        13000
                      ],
                      "y": [
                        12200,
                        16600
                      ]
                    },
                    "id": "space-1-1"
                  },
                  {
                    "bounds": {
                      "x": [
                        200,
                        4600
                      ],
                      "y": [
                        200,
                        16600
                      ]
                    },
                    "id": "space-1-2"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "bounds": {
                        "x": [
                          0,
                          13200
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          0,
                          13200
                        ],
                        "y": [
                          16600,
                          16800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          0,
                          200
                        ],
                        "y": [
                          200,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-west",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          13000,
                          13200
                        ],
                        "y": [
                          200,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-east_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          13000,
                          13200
                        ],
                        "y": [
                          12000,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-east_north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4800,
                          13000
                        ],
                        "y": [
                          4600,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-courtyard_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4800,
                          13000
                        ],
                        "y": [
                          12000,
                          12200
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-courtyard_north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          4800,
                          12000
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-spine",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          200,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-partition_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          12000,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-1-partition_north",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_global_mm": [
                      7200,
                      100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-1-south",
                    "id": "ifcwindow-1-0",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      10800,
                      100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-1-south",
                    "id": "ifcwindow-1-1",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      7200,
                      16700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-1-north",
                    "id": "ifcwindow-1-2",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      10800,
                      16700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-1-north",
                    "id": "ifcwindow-1-3",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      9000,
                      4700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-1-courtyard_south",
                    "id": "ifcwindow-1-4",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      9000,
                      12100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-1-courtyard_north",
                    "id": "ifcwindow-1-5",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      100.0,
                      2400
                    ],
                    "height_mm": 1800,
                    "host_wall": "wall-1-west",
                    "id": "ifcwindow-1-6",
                    "sill_height_mm": 900,
                    "template_id": "window-single",
                    "width_mm": 900
                  }
                ]
              },
              {
                "doors": [
                  {
                    "center_global_mm": [
                      4700.0,
                      2400
                    ],
                    "height_mm": 2100,
                    "host_wall": "wall-2-partition_south",
                    "id": "ifcdoor-2-0",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  },
                  {
                    "center_global_mm": [
                      4700.0,
                      14400
                    ],
                    "height_mm": 2100,
                    "host_wall": "wall-2-partition_north",
                    "id": "ifcdoor-2-1",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 3150,
                "id": "storey-2",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        4800,
                        13000
                      ],
                      "y": [
                        200,
                        4600
                      ]
                    },
                    "id": "space-2-0"
                  },
                  {
                    "bounds": {
                      "x": [
                        4800,
                        13000
                      ],
                      "y": [
                        12200,
                        16600
                      ]
                    },
                    "id": "space-2-1"
                  },
                  {
                    "bounds": {
                      "x": [
                        200,
                        4600
                      ],
                      "y": [
                        200,
                        16600
                      ]
                    },
                    "id": "space-2-2"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "bounds": {
                        "x": [
                          0,
                          13200
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          0,
                          13200
                        ],
                        "y": [
                          16600,
                          16800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          0,
                          200
                        ],
                        "y": [
                          200,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-west",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          13000,
                          13200
                        ],
                        "y": [
                          200,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-east_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          13000,
                          13200
                        ],
                        "y": [
                          12000,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-east_north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4800,
                          13000
                        ],
                        "y": [
                          4600,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-courtyard_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4800,
                          13000
                        ],
                        "y": [
                          12000,
                          12200
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-courtyard_north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          4800,
                          12000
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-spine",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          200,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-partition_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          12000,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-2-partition_north",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_global_mm": [
                      7200,
                      100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-2-south",
                    "id": "ifcwindow-2-0",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      10800,
                      100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-2-south",
                    "id": "ifcwindow-2-1",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      7200,
                      16700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-2-north",
                    "id": "ifcwindow-2-2",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      10800,
                      16700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-2-north",
                    "id": "ifcwindow-2-3",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      9000,
                      4700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-2-courtyard_south",
                    "id": "ifcwindow-2-4",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      9000,
                      12100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-2-courtyard_north",
                    "id": "ifcwindow-2-5",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      100.0,
                      2400
                    ],
                    "height_mm": 1800,
                    "host_wall": "wall-2-west",
                    "id": "ifcwindow-2-6",
                    "sill_height_mm": 900,
                    "template_id": "window-single",
                    "width_mm": 900
                  }
                ]
              },
              {
                "doors": [
                  {
                    "center_global_mm": [
                      4700.0,
                      2400
                    ],
                    "height_mm": 2100,
                    "host_wall": "wall-3-partition_south",
                    "id": "ifcdoor-3-0",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  },
                  {
                    "center_global_mm": [
                      4700.0,
                      14400
                    ],
                    "height_mm": 2100,
                    "host_wall": "wall-3-partition_north",
                    "id": "ifcdoor-3-1",
                    "sill_height_mm": 0,
                    "template_id": "door-right",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 6300,
                "id": "storey-3",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        4800,
                        13000
                      ],
                      "y": [
                        200,
                        4600
                      ]
                    },
                    "id": "space-3-0"
                  },
                  {
                    "bounds": {
                      "x": [
                        4800,
                        13000
                      ],
                      "y": [
                        12200,
                        16600
                      ]
                    },
                    "id": "space-3-1"
                  },
                  {
                    "bounds": {
                      "x": [
                        200,
                        4600
                      ],
                      "y": [
                        200,
                        16600
                      ]
                    },
                    "id": "space-3-2"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "bounds": {
                        "x": [
                          0,
                          13200
                        ],
                        "y": [
                          0,
                          200
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          0,
                          13200
                        ],
                        "y": [
                          16600,
                          16800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          0,
                          200
                        ],
                        "y": [
                          200,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-west",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          13000,
                          13200
                        ],
                        "y": [
                          200,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-east_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          13000,
                          13200
                        ],
                        "y": [
                          12000,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-east_north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4800,
                          13000
                        ],
                        "y": [
                          4600,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-courtyard_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4800,
                          13000
                        ],
                        "y": [
                          12000,
                          12200
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-courtyard_north",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          4800,
                          12000
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-spine",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          200,
                          4800
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-partition_south",
                      "thickness_mm": 200
                    },
                    {
                      "bounds": {
                        "x": [
                          4600,
                          4800
                        ],
                        "y": [
                          12000,
                          16600
                        ]
                      },
                      "height_mm": 3000,
                      "id": "wall-3-partition_north",
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "center_global_mm": [
                      7200,
                      100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-3-south",
                    "id": "ifcwindow-3-0",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      10800,
                      100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-3-south",
                    "id": "ifcwindow-3-1",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      7200,
                      16700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-3-north",
                    "id": "ifcwindow-3-2",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      10800,
                      16700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-3-north",
                    "id": "ifcwindow-3-3",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      9000,
                      4700.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-3-courtyard_south",
                    "id": "ifcwindow-3-4",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      9000,
                      12100.0
                    ],
                    "height_mm": 1500,
                    "host_wall": "wall-3-courtyard_north",
                    "id": "ifcwindow-3-5",
                    "sill_height_mm": 900,
                    "template_id": "window-double-vertical",
                    "width_mm": 1800
                  },
                  {
                    "center_global_mm": [
                      100.0,
                      2400
                    ],
                    "height_mm": 1800,
                    "host_wall": "wall-3-west",
                    "id": "ifcwindow-3-6",
                    "sill_height_mm": 900,
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
      "fact_count": 26,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T13:36:52+00:00",
    "event_index": 2,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "cc2db329ab7cb4ae",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/offline-runner/runs/cc2db329ab7cb4ae/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "response-package-2",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T13:37:15+00:00",
    "event_index": 3,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "cc2db329ab7cb4ae",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "93b4b417e3df3f6ed2b68686e269497ef9361757315e38a3d7ea1c6bf72a7d1d",
          "expected-facts.json": "93904e1fc589fdd797dbb779234a5118053b5087cc269fe40b01119c4995a164",
          "generator/candidate.json": "fd4b1b557a5cfa460bf12df5e95bab88c35de23aad29fb2a104f1f5423319918",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "db4aae3e15fd7e0b88d20018e7db1e82ed86a935f1fa24da4c757e04a2b99e9f",
          "ifc-verification.json": "dd69be2446c56f454846664c5e414f7b1a840624ddd7763a4e8c6819eb8bbe15",
          "repair/route.json": "7fc62a757a5bccebf0161b0a949fa2443553be49191368538a3f85fa26df16aa",
          "request-semantics.json": "f60db5e5d55c11f338e5c9dbfd5600ce800f67c18bcc9e6042ed0675aea180f5",
          "semantic-coverage.json": "48eea23942a93c920846f8a69d70fce8197017f0f85509e4e5449edcc764ec3c",
          "semantic-verification.json": "72d701b6878780daa800eb2d3087b6d41ebd8f9033d088e3725e87172ade5862"
        },
        "candidate_hash": "fd4b1b557a5cfa460bf12df5e95bab88c35de23aad29fb2a104f1f5423319918",
        "candidate_path": "generator/candidate.json",
        "case_id": "cc2db329ab7cb4ae",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "cc2db329ab7cb4ae",
              "floor_openings": {
                "floor-opening-2": {
                  "bbox": {
                    "x": [
                      0.4,
                      1.6
                    ],
                    "y": [
                      5.3999999999999995,
                      10.8
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "binding_basis": "explicit_identity",
                  "host_slab_id": "slab-2",
                  "ifc_class": "IfcOpeningElement",
                  "resolved_bim_json_id": "floor-opening-2",
                  "resolved_global_id": "0r3jaqozvMVvrgpwVOteNB"
                },
                "floor-opening-3": {
                  "bbox": {
                    "x": [
                      2.8,
                      4.0
                    ],
                    "y": [
                      5.3999999999999995,
                      10.8
                    ],
                    "z": [
                      6.15,
                      6.300000000000001
                    ]
                  },
                  "binding_basis": "explicit_identity",
                  "host_slab_id": "slab-3",
                  "ifc_class": "IfcOpeningElement",
                  "resolved_bim_json_id": "floor-opening-3",
                  "resolved_global_id": "3k9B9Hp5vKpAg6Gt5XeqVP"
                }
              },
              "products": {},
              "roof": {
                "roof-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      16.8
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
                "slab-1": {
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      16.8
                    ],
                    "z": [
                      -0.15,
                      0.0
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "slab-2": {
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      16.8
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "slab-3": {
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      16.8
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
                "space-1-0": {
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      0.19999999999999973,
                      4.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-1-1": {
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      12.2,
                      16.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-1-2": {
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.6
                    ],
                    "y": [
                      0.20000000000000107,
                      16.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-2-0": {
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      0.19999999999999973,
                      4.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-2-1": {
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      12.2,
                      16.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-2-2": {
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.6
                    ],
                    "y": [
                      0.20000000000000107,
                      16.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-3-0": {
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      0.19999999999999973,
                      4.6
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-3-1": {
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      12.2,
                      16.6
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-3-2": {
                  "bbox": {
                    "x": [
                      0.19999999999999973,
                      4.6
                    ],
                    "y": [
                      0.20000000000000107,
                      16.6
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
                      0.4,
                      1.6
                    ],
                    "y": [
                      5.4,
                      10.8
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
                      2.8000000000000003,
                      4.0
                    ],
                    "y": [
                      5.4,
                      10.8
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
                "wall-1-courtyard_north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      12.0,
                      12.2
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-courtyard_south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      4.6000000000000005,
                      4.8
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-east_north": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      13.0,
                      13.2
                    ],
                    "y": [
                      12.0,
                      16.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-east_south": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      13.0,
                      13.2
                    ],
                    "y": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      16.599999999999998,
                      16.8
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-partition_north": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      12.0,
                      16.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-partition_south": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-spine": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      4.800000000000001,
                      12.0
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-1-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      0.0,
                      0.2
                    ],
                    "y": [
                      0.20000000000000107,
                      16.6
                    ],
                    "z": [
                      0.0,
                      3.0
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-courtyard_north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      12.0,
                      12.2
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-courtyard_south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      4.6000000000000005,
                      4.8
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-east_north": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      13.0,
                      13.2
                    ],
                    "y": [
                      12.0,
                      16.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-east_south": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      13.0,
                      13.2
                    ],
                    "y": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      16.599999999999998,
                      16.8
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-partition_north": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      12.0,
                      16.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-partition_south": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-spine": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      4.800000000000001,
                      12.0
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-2-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      0.0,
                      0.2
                    ],
                    "y": [
                      0.20000000000000107,
                      16.6
                    ],
                    "z": [
                      3.15,
                      6.15
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-courtyard_north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      12.0,
                      12.2
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-courtyard_south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.800000000000001,
                      13.0
                    ],
                    "y": [
                      4.6000000000000005,
                      4.8
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-east_north": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      13.0,
                      13.2
                    ],
                    "y": [
                      12.0,
                      16.6
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-east_south": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      13.0,
                      13.2
                    ],
                    "y": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-north": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      16.599999999999998,
                      16.8
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-partition_north": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      12.0,
                      16.6
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-partition_south": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      0.19999999999999973,
                      4.800000000000001
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      13.200000000000001
                    ],
                    "y": [
                      0.0,
                      0.2
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-spine": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      4.6000000000000005,
                      4.8
                    ],
                    "y": [
                      4.800000000000001,
                      12.0
                    ],
                    "z": [
                      6.3,
                      9.3
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-3-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      0.0,
                      0.2
                    ],
                    "y": [
                      0.20000000000000107,
                      16.6
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
            "case_id": "cc2db329ab7cb4ae",
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
            "source_generator_dir": "dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/offline-runner/runs/cc2db329ab7cb4ae/generator",
            "source_generator_response_id": "response-package-2",
            "valid": true,
            "validation_issue_count": 0
          },
          "request_semantics": {
            "basis": "request expectations independently compared with reopened IFC before atomic publication",
            "expectations": [
              {
                "entity_id": "wall-1-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-east_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-east_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-courtyard_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-courtyard_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-spine",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-partition_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-partition_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "slab-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "ifcwindow-1-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-5",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-6",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-entry",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-2-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-east_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-east_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-courtyard_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-courtyard_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-spine",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-partition_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-partition_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "slab-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "ifcwindow-2-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-5",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-6",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/38",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-2-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/39",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-2-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/40",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-3-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/41",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/42",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/43",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-east_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/44",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-east_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/45",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-courtyard_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/46",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-courtyard_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/47",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-spine",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-partition_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-partition_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "slab-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "ifcwindow-3-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-5",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-6",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-3-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-3-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "roof-slab",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "wall-1-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/0",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/1",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/2",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-east_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/3",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-east_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/4",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-courtyard_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/5",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-courtyard_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/6",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-spine",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/7",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-partition_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/8",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-1-partition_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/9",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "slab-1",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/10",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "ifcwindow-1-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/11",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/12",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/13",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/14",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/15",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-5",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/16",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-1-6",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/17",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/18",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/19",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-1-entry",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/20",
                "value": {
                  "template_id": "door-left",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-2-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/21",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/22",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/23",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-east_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/24",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-east_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/25",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-courtyard_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/26",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-courtyard_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/27",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-spine",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/28",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-partition_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/29",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-2-partition_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/30",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "slab-2",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/31",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "ifcwindow-2-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/32",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/33",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/34",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/35",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/36",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-5",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/37",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-2-6",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/38",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-2-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/39",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-2-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/40",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "wall-3-south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/41",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/42",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-west",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/43",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-east_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/44",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-east_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/45",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-courtyard_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/46",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-courtyard_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/47",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-spine",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/48",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-partition_south",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/49",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "wall-3-partition_north",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/50",
                "value": {
                  "kind": "single_material",
                  "name": "砖"
                }
              },
              {
                "entity_id": "slab-3",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/51",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
                }
              },
              {
                "entity_id": "ifcwindow-3-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/52",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/53",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-2",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/54",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-3",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/55",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-4",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/56",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-5",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/57",
                "value": {
                  "template_id": "window-double-vertical",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcwindow-3-6",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/58",
                "value": {
                  "template_id": "window-single",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-3-0",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/59",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "ifcdoor-3-1",
                "kind": "template",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/60",
                "value": {
                  "template_id": "door-right",
                  "template_version": "text2ifc/basic-filling/1.0"
                }
              },
              {
                "entity_id": "roof-slab",
                "kind": "material",
                "scope": "direct",
                "source_path": "/known_facts/semantic_requirements/61",
                "value": {
                  "kind": "single_material",
                  "name": "混凝土"
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
            "candidate_entity_count": 111,
            "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
            "case_id": "cc2db329ab7cb4ae",
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
                "path": "/known_facts/building/id",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "building-community-reading"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 13200
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
                "value": 16800
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_count",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 3
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/floor_slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds": {
                      "x": [
                        0,
                        13200
                      ],
                      "y": [
                        0,
                        16800
                      ]
                    },
                    "id": "slab-1",
                    "storey": "storey-1",
                    "thickness_mm": 150,
                    "top_elevation_mm": 0
                  },
                  {
                    "bounds": {
                      "x": [
                        0,
                        13200
                      ],
                      "y": [
                        0,
                        16800
                      ]
                    },
                    "id": "slab-2",
                    "opening": {
                      "bounds": {
                        "x": [
                          400,
                          1600
                        ],
                        "y": [
                          5400,
                          10800
                        ]
                      },
                      "id": "floor-opening-2",
                      "real_through_opening": true
                    },
                    "storey": "storey-2",
                    "thickness_mm": 150,
                    "top_elevation_mm": 3150
                  },
                  {
                    "bounds": {
                      "x": [
                        0,
                        13200
                      ],
                      "y": [
                        0,
                        16800
                      ]
                    },
                    "id": "slab-3",
                    "opening": {
                      "bounds": {
                        "x": [
                          2800,
                          4000
                        ],
                        "y": [
                          5400,
                          10800
                        ]
                      },
                      "id": "floor-opening-3",
                      "real_through_opening": true
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
                  0,
                  13200
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/bounds/y",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  0,
                  16800
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
                    "entity_id": "wall-1-south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-west",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-east_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-east_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-courtyard_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-courtyard_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-spine",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-partition_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-1-partition_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "slab-1",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "ifcwindow-1-0",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-1-1",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-1-2",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-1-3",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-1-4",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-1-5",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-1-6",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-1-0",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-1-1",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-1-entry",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-left",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "wall-2-south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-west",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-east_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-east_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-courtyard_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-courtyard_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-spine",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-partition_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-2-partition_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "slab-2",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "ifcwindow-2-0",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-2-1",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-2-2",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-2-3",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-2-4",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-2-5",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-2-6",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-2-0",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-2-1",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "wall-3-south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-west",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-east_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-east_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-courtyard_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-courtyard_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-spine",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-partition_south",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "wall-3-partition_north",
                    "material": {
                      "kind": "single_material",
                      "name": "砖"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "slab-3",
                    "material": {
                      "kind": "single_material",
                      "name": "混凝土"
                    },
                    "scope": "direct",
                    "source": "user"
                  },
                  {
                    "entity_id": "ifcwindow-3-0",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-3-1",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-3-2",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-3-3",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-3-4",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-3-5",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-double-vertical",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcwindow-3-6",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "window-single",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-3-0",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
                  },
                  {
                    "entity_id": "ifcdoor-3-1",
                    "scope": "direct",
                    "source": "user",
                    "template": {
                      "template_id": "door-right",
                      "template_version": "text2ifc/basic-filling/1.0"
                    }
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
                        400,
                        1600
                      ],
                      "y": [
                        5400,
                        10800
                      ]
                    },
                    "end_elevation_mm": 3150,
                    "from_storey": "storey-1",
                    "id": "stair-1",
                    "number_of_risers": 18,
                    "number_of_treads": 18,
                    "riser_height_mm": 175,
                    "start_elevation_mm": 0,
                    "to_storey": "storey-2",
                    "tread_depth_mm": 300,
                    "width_mm": 1200
                  },
                  {
                    "bounds": {
                      "x": [
                        2800,
                        4000
                      ],
                      "y": [
                        5400,
                        10800
                      ]
                    },
                    "end_elevation_mm": 6300,
                    "from_storey": "storey-2",
                    "id": "stair-2",
                    "number_of_risers": 18,
                    "number_of_treads": 18,
                    "riser_height_mm": 175,
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
                          4700.0,
                          2400
                        ],
                        "height_mm": 2100,
                        "host_wall": "wall-1-partition_south",
                        "id": "ifcdoor-1-0",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      },
                      {
                        "center_global_mm": [
                          4700.0,
                          14400
                        ],
                        "height_mm": 2100,
                        "host_wall": "wall-1-partition_north",
                        "id": "ifcdoor-1-1",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      },
                      {
                        "center_global_mm": [
                          100.0,
                          8400
                        ],
                        "height_mm": 2400,
                        "host_wall": "wall-1-west",
                        "id": "ifcdoor-1-entry",
                        "sill_height_mm": 0,
                        "template_id": "door-left",
                        "width_mm": 1200
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            4800,
                            13000
                          ],
                          "y": [
                            200,
                            4600
                          ]
                        },
                        "id": "space-1-0"
                      },
                      {
                        "bounds": {
                          "x": [
                            4800,
                            13000
                          ],
                          "y": [
                            12200,
                            16600
                          ]
                        },
                        "id": "space-1-1"
                      },
                      {
                        "bounds": {
                          "x": [
                            200,
                            4600
                          ],
                          "y": [
                            200,
                            16600
                          ]
                        },
                        "id": "space-1-2"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              13200
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              13200
                            ],
                            "y": [
                              16600,
                              16800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              200
                            ],
                            "y": [
                              200,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-west",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              13000,
                              13200
                            ],
                            "y": [
                              200,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-east_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              13000,
                              13200
                            ],
                            "y": [
                              12000,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-east_north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4800,
                              13000
                            ],
                            "y": [
                              4600,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-courtyard_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4800,
                              13000
                            ],
                            "y": [
                              12000,
                              12200
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-courtyard_north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              4800,
                              12000
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-spine",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              200,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-partition_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              12000,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-1-partition_north",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          7200,
                          100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-1-south",
                        "id": "ifcwindow-1-0",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10800,
                          100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-1-south",
                        "id": "ifcwindow-1-1",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          7200,
                          16700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-1-north",
                        "id": "ifcwindow-1-2",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10800,
                          16700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-1-north",
                        "id": "ifcwindow-1-3",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          9000,
                          4700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-1-courtyard_south",
                        "id": "ifcwindow-1-4",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          9000,
                          12100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-1-courtyard_north",
                        "id": "ifcwindow-1-5",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          100.0,
                          2400
                        ],
                        "height_mm": 1800,
                        "host_wall": "wall-1-west",
                        "id": "ifcwindow-1-6",
                        "sill_height_mm": 900,
                        "template_id": "window-single",
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          4700.0,
                          2400
                        ],
                        "height_mm": 2100,
                        "host_wall": "wall-2-partition_south",
                        "id": "ifcdoor-2-0",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      },
                      {
                        "center_global_mm": [
                          4700.0,
                          14400
                        ],
                        "height_mm": 2100,
                        "host_wall": "wall-2-partition_north",
                        "id": "ifcdoor-2-1",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 3150,
                    "id": "storey-2",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            4800,
                            13000
                          ],
                          "y": [
                            200,
                            4600
                          ]
                        },
                        "id": "space-2-0"
                      },
                      {
                        "bounds": {
                          "x": [
                            4800,
                            13000
                          ],
                          "y": [
                            12200,
                            16600
                          ]
                        },
                        "id": "space-2-1"
                      },
                      {
                        "bounds": {
                          "x": [
                            200,
                            4600
                          ],
                          "y": [
                            200,
                            16600
                          ]
                        },
                        "id": "space-2-2"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              13200
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              13200
                            ],
                            "y": [
                              16600,
                              16800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              200
                            ],
                            "y": [
                              200,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-west",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              13000,
                              13200
                            ],
                            "y": [
                              200,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-east_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              13000,
                              13200
                            ],
                            "y": [
                              12000,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-east_north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4800,
                              13000
                            ],
                            "y": [
                              4600,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-courtyard_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4800,
                              13000
                            ],
                            "y": [
                              12000,
                              12200
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-courtyard_north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              4800,
                              12000
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-spine",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              200,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-partition_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              12000,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-2-partition_north",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          7200,
                          100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-2-south",
                        "id": "ifcwindow-2-0",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10800,
                          100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-2-south",
                        "id": "ifcwindow-2-1",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          7200,
                          16700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-2-north",
                        "id": "ifcwindow-2-2",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10800,
                          16700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-2-north",
                        "id": "ifcwindow-2-3",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          9000,
                          4700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-2-courtyard_south",
                        "id": "ifcwindow-2-4",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          9000,
                          12100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-2-courtyard_north",
                        "id": "ifcwindow-2-5",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          100.0,
                          2400
                        ],
                        "height_mm": 1800,
                        "host_wall": "wall-2-west",
                        "id": "ifcwindow-2-6",
                        "sill_height_mm": 900,
                        "template_id": "window-single",
                        "width_mm": 900
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "center_global_mm": [
                          4700.0,
                          2400
                        ],
                        "height_mm": 2100,
                        "host_wall": "wall-3-partition_south",
                        "id": "ifcdoor-3-0",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      },
                      {
                        "center_global_mm": [
                          4700.0,
                          14400
                        ],
                        "height_mm": 2100,
                        "host_wall": "wall-3-partition_north",
                        "id": "ifcdoor-3-1",
                        "sill_height_mm": 0,
                        "template_id": "door-right",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 6300,
                    "id": "storey-3",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            4800,
                            13000
                          ],
                          "y": [
                            200,
                            4600
                          ]
                        },
                        "id": "space-3-0"
                      },
                      {
                        "bounds": {
                          "x": [
                            4800,
                            13000
                          ],
                          "y": [
                            12200,
                            16600
                          ]
                        },
                        "id": "space-3-1"
                      },
                      {
                        "bounds": {
                          "x": [
                            200,
                            4600
                          ],
                          "y": [
                            200,
                            16600
                          ]
                        },
                        "id": "space-3-2"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              13200
                            ],
                            "y": [
                              0,
                              200
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              13200
                            ],
                            "y": [
                              16600,
                              16800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              200
                            ],
                            "y": [
                              200,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-west",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              13000,
                              13200
                            ],
                            "y": [
                              200,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-east_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              13000,
                              13200
                            ],
                            "y": [
                              12000,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-east_north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4800,
                              13000
                            ],
                            "y": [
                              4600,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-courtyard_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4800,
                              13000
                            ],
                            "y": [
                              12000,
                              12200
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-courtyard_north",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              4800,
                              12000
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-spine",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              200,
                              4800
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-partition_south",
                          "thickness_mm": 200
                        },
                        {
                          "bounds": {
                            "x": [
                              4600,
                              4800
                            ],
                            "y": [
                              12000,
                              16600
                            ]
                          },
                          "height_mm": 3000,
                          "id": "wall-3-partition_north",
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "center_global_mm": [
                          7200,
                          100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-3-south",
                        "id": "ifcwindow-3-0",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10800,
                          100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-3-south",
                        "id": "ifcwindow-3-1",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          7200,
                          16700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-3-north",
                        "id": "ifcwindow-3-2",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          10800,
                          16700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-3-north",
                        "id": "ifcwindow-3-3",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          9000,
                          4700.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-3-courtyard_south",
                        "id": "ifcwindow-3-4",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          9000,
                          12100.0
                        ],
                        "height_mm": 1500,
                        "host_wall": "wall-3-courtyard_north",
                        "id": "ifcwindow-3-5",
                        "sill_height_mm": 900,
                        "template_id": "window-double-vertical",
                        "width_mm": 1800
                      },
                      {
                        "center_global_mm": [
                          100.0,
                          2400
                        ],
                        "height_mm": 1800,
                        "host_wall": "wall-3-west",
                        "id": "ifcwindow-3-6",
                        "sill_height_mm": 900,
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
        "expected_facts_hash": "93904e1fc589fdd797dbb779234a5118053b5087cc269fe40b01119c4995a164",
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
                "candidate_id": "ifcdoor-1-0",
                "collection": "doors",
                "expected_id": "ifcdoor-1-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcdoor-1-1",
                "collection": "doors",
                "expected_id": "ifcdoor-1-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcdoor-1-entry",
                "collection": "doors",
                "expected_id": "ifcdoor-1-entry",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcdoor-2-0",
                "collection": "doors",
                "expected_id": "ifcdoor-2-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcdoor-2-1",
                "collection": "doors",
                "expected_id": "ifcdoor-2-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcdoor-3-0",
                "collection": "doors",
                "expected_id": "ifcdoor-3-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcdoor-3-1",
                "collection": "doors",
                "expected_id": "ifcdoor-3-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-1-0",
                "collection": "spaces",
                "expected_id": "space-1-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-1-1",
                "collection": "spaces",
                "expected_id": "space-1-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-1-2",
                "collection": "spaces",
                "expected_id": "space-1-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-2-0",
                "collection": "spaces",
                "expected_id": "space-2-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-2-1",
                "collection": "spaces",
                "expected_id": "space-2-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-2-2",
                "collection": "spaces",
                "expected_id": "space-2-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-3-0",
                "collection": "spaces",
                "expected_id": "space-3-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-3-1",
                "collection": "spaces",
                "expected_id": "space-3-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-3-2",
                "collection": "spaces",
                "expected_id": "space-3-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-south",
                "collection": "walls",
                "expected_id": "wall-1-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-north",
                "collection": "walls",
                "expected_id": "wall-1-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-west",
                "collection": "walls",
                "expected_id": "wall-1-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-east_south",
                "collection": "walls",
                "expected_id": "wall-1-east_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-east_north",
                "collection": "walls",
                "expected_id": "wall-1-east_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-courtyard_south",
                "collection": "walls",
                "expected_id": "wall-1-courtyard_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-courtyard_north",
                "collection": "walls",
                "expected_id": "wall-1-courtyard_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-spine",
                "collection": "walls",
                "expected_id": "wall-1-spine",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-partition_south",
                "collection": "walls",
                "expected_id": "wall-1-partition_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-1-partition_north",
                "collection": "walls",
                "expected_id": "wall-1-partition_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-south",
                "collection": "walls",
                "expected_id": "wall-2-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-north",
                "collection": "walls",
                "expected_id": "wall-2-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-west",
                "collection": "walls",
                "expected_id": "wall-2-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-east_south",
                "collection": "walls",
                "expected_id": "wall-2-east_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-east_north",
                "collection": "walls",
                "expected_id": "wall-2-east_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-courtyard_south",
                "collection": "walls",
                "expected_id": "wall-2-courtyard_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-courtyard_north",
                "collection": "walls",
                "expected_id": "wall-2-courtyard_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-spine",
                "collection": "walls",
                "expected_id": "wall-2-spine",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-partition_south",
                "collection": "walls",
                "expected_id": "wall-2-partition_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-2-partition_north",
                "collection": "walls",
                "expected_id": "wall-2-partition_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-south",
                "collection": "walls",
                "expected_id": "wall-3-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-north",
                "collection": "walls",
                "expected_id": "wall-3-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-west",
                "collection": "walls",
                "expected_id": "wall-3-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-east_south",
                "collection": "walls",
                "expected_id": "wall-3-east_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-east_north",
                "collection": "walls",
                "expected_id": "wall-3-east_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-courtyard_south",
                "collection": "walls",
                "expected_id": "wall-3-courtyard_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-courtyard_north",
                "collection": "walls",
                "expected_id": "wall-3-courtyard_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-spine",
                "collection": "walls",
                "expected_id": "wall-3-spine",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-partition_south",
                "collection": "walls",
                "expected_id": "wall-3-partition_south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-3-partition_north",
                "collection": "walls",
                "expected_id": "wall-3-partition_north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-0",
                "collection": "windows",
                "expected_id": "ifcwindow-1-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-1",
                "collection": "windows",
                "expected_id": "ifcwindow-1-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-2",
                "collection": "windows",
                "expected_id": "ifcwindow-1-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-3",
                "collection": "windows",
                "expected_id": "ifcwindow-1-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-4",
                "collection": "windows",
                "expected_id": "ifcwindow-1-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-5",
                "collection": "windows",
                "expected_id": "ifcwindow-1-5",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-1-6",
                "collection": "windows",
                "expected_id": "ifcwindow-1-6",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-0",
                "collection": "windows",
                "expected_id": "ifcwindow-2-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-1",
                "collection": "windows",
                "expected_id": "ifcwindow-2-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-2",
                "collection": "windows",
                "expected_id": "ifcwindow-2-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-3",
                "collection": "windows",
                "expected_id": "ifcwindow-2-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-4",
                "collection": "windows",
                "expected_id": "ifcwindow-2-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-5",
                "collection": "windows",
                "expected_id": "ifcwindow-2-5",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-2-6",
                "collection": "windows",
                "expected_id": "ifcwindow-2-6",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-0",
                "collection": "windows",
                "expected_id": "ifcwindow-3-0",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-1",
                "collection": "windows",
                "expected_id": "ifcwindow-3-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-2",
                "collection": "windows",
                "expected_id": "ifcwindow-3-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-3",
                "collection": "windows",
                "expected_id": "ifcwindow-3-3",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-4",
                "collection": "windows",
                "expected_id": "ifcwindow-3-4",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-5",
                "collection": "windows",
                "expected_id": "ifcwindow-3-5",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "ifcwindow-3-6",
                "collection": "windows",
                "expected_id": "ifcwindow-3-6",
                "match_basis": "exact_brief_id"
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
            "applicability": "not_applicable",
            "basis": "expected facts contain fewer than two unique explicit storey names",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_name_consistency",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "skipped"
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
          "case_id": "cc2db329ab7cb4ae",
          "floor_openings": {
            "floor-opening-2": {
              "bbox": {
                "x": [
                  0.4,
                  1.6
                ],
                "y": [
                  5.3999999999999995,
                  10.8
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "binding_basis": "explicit_identity",
              "host_slab_id": "slab-2",
              "ifc_class": "IfcOpeningElement",
              "resolved_bim_json_id": "floor-opening-2",
              "resolved_global_id": "0r3jaqozvMVvrgpwVOteNB"
            },
            "floor-opening-3": {
              "bbox": {
                "x": [
                  2.8,
                  4.0
                ],
                "y": [
                  5.3999999999999995,
                  10.8
                ],
                "z": [
                  6.15,
                  6.300000000000001
                ]
              },
              "binding_basis": "explicit_identity",
              "host_slab_id": "slab-3",
              "ifc_class": "IfcOpeningElement",
              "resolved_bim_json_id": "floor-opening-3",
              "resolved_global_id": "3k9B9Hp5vKpAg6Gt5XeqVP"
            }
          },
          "products": {},
          "roof": {
            "roof-slab": {
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  16.8
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
            "slab-1": {
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  16.8
                ],
                "z": [
                  -0.15,
                  0.0
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "slab-2": {
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  16.8
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "slab-3": {
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  16.8
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
            "space-1-0": {
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  0.19999999999999973,
                  4.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-1-1": {
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  12.2,
                  16.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-1-2": {
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.6
                ],
                "y": [
                  0.20000000000000107,
                  16.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-2-0": {
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  0.19999999999999973,
                  4.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-2-1": {
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  12.2,
                  16.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-2-2": {
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.6
                ],
                "y": [
                  0.20000000000000107,
                  16.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-3-0": {
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  0.19999999999999973,
                  4.6
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-3-1": {
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  12.2,
                  16.6
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-3-2": {
              "bbox": {
                "x": [
                  0.19999999999999973,
                  4.6
                ],
                "y": [
                  0.20000000000000107,
                  16.6
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
                  0.4,
                  1.6
                ],
                "y": [
                  5.4,
                  10.8
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
                  2.8000000000000003,
                  4.0
                ],
                "y": [
                  5.4,
                  10.8
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
            "wall-1-courtyard_north": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  12.0,
                  12.2
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-courtyard_south": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  4.6000000000000005,
                  4.8
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-east_north": {
              "axis": "y",
              "bbox": {
                "x": [
                  13.0,
                  13.2
                ],
                "y": [
                  12.0,
                  16.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-east_south": {
              "axis": "y",
              "bbox": {
                "x": [
                  13.0,
                  13.2
                ],
                "y": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-north": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  16.599999999999998,
                  16.8
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-partition_north": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  12.0,
                  16.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-partition_south": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-spine": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  4.800000000000001,
                  12.0
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-1-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  0.0,
                  0.2
                ],
                "y": [
                  0.20000000000000107,
                  16.6
                ],
                "z": [
                  0.0,
                  3.0
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-courtyard_north": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  12.0,
                  12.2
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-courtyard_south": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  4.6000000000000005,
                  4.8
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-east_north": {
              "axis": "y",
              "bbox": {
                "x": [
                  13.0,
                  13.2
                ],
                "y": [
                  12.0,
                  16.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-east_south": {
              "axis": "y",
              "bbox": {
                "x": [
                  13.0,
                  13.2
                ],
                "y": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-north": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  16.599999999999998,
                  16.8
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-partition_north": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  12.0,
                  16.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-partition_south": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-spine": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  4.800000000000001,
                  12.0
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-2-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  0.0,
                  0.2
                ],
                "y": [
                  0.20000000000000107,
                  16.6
                ],
                "z": [
                  3.15,
                  6.15
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-courtyard_north": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  12.0,
                  12.2
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-courtyard_south": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.800000000000001,
                  13.0
                ],
                "y": [
                  4.6000000000000005,
                  4.8
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-east_north": {
              "axis": "y",
              "bbox": {
                "x": [
                  13.0,
                  13.2
                ],
                "y": [
                  12.0,
                  16.6
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-east_south": {
              "axis": "y",
              "bbox": {
                "x": [
                  13.0,
                  13.2
                ],
                "y": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-north": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  16.599999999999998,
                  16.8
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-partition_north": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  12.0,
                  16.6
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-partition_south": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  0.19999999999999973,
                  4.800000000000001
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  13.200000000000001
                ],
                "y": [
                  0.0,
                  0.2
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-spine": {
              "axis": "y",
              "bbox": {
                "x": [
                  4.6000000000000005,
                  4.8
                ],
                "y": [
                  4.800000000000001,
                  12.0
                ],
                "z": [
                  6.3,
                  9.3
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-3-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  0.0,
                  0.2
                ],
                "y": [
                  0.20000000000000107,
                  16.6
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
      "ifc_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae",
      "semantic_geometry_expectation": {
        "case_id": "cc2db329ab7cb4ae",
        "complete": true,
        "doors": {},
        "floor_openings": {
          "floor-opening-2": {
            "bbox": {
              "x": [
                0.4,
                1.6
              ],
              "y": [
                5.4,
                10.8
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "bbox_issue_code": "FLOOR_OPENING_BBOX_MISMATCH",
            "host_slab_id": "slab-2",
            "identity_source": "explicit",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/opening"
            ]
          },
          "floor-opening-3": {
            "bbox": {
              "x": [
                2.8,
                4.0
              ],
              "y": [
                5.4,
                10.8
              ],
              "z": [
                6.15,
                6.3
              ]
            },
            "bbox_issue_code": "FLOOR_OPENING_BBOX_MISMATCH",
            "host_slab_id": "slab-3",
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
                0.0,
                13.2
              ],
              "y": [
                0.0,
                16.8
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
          "slab-1": {
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                0.0,
                16.8
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
          "slab-2": {
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                0.0,
                16.8
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [
              "wall-1-courtyard_north",
              "wall-1-courtyard_south",
              "wall-1-east_north",
              "wall-1-east_south",
              "wall-1-north",
              "wall-1-partition_north",
              "wall-1-partition_south",
              "wall-1-south",
              "wall-1-spine",
              "wall-1-west"
            ],
            "source_fact_refs": [
              "/known_facts/floor_slabs/1"
            ]
          },
          "slab-3": {
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                0.0,
                16.8
              ],
              "z": [
                6.15,
                6.3
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [
              "wall-2-courtyard_north",
              "wall-2-courtyard_south",
              "wall-2-east_north",
              "wall-2-east_south",
              "wall-2-north",
              "wall-2-partition_north",
              "wall-2-partition_south",
              "wall-2-south",
              "wall-2-spine",
              "wall-2-west"
            ],
            "source_fact_refs": [
              "/known_facts/floor_slabs/2"
            ]
          }
        },
        "source": "design_brief_expected_facts",
        "spaces": {
          "space-1-0": {
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                0.2,
                4.6
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
          "space-1-1": {
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                12.2,
                16.6
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
          "space-1-2": {
            "bbox": {
              "x": [
                0.2,
                4.6
              ],
              "y": [
                0.2,
                16.6
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/2"
            ],
            "storey_id": "storey-1"
          },
          "space-2-0": {
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                0.2,
                4.6
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
          "space-2-1": {
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                12.2,
                16.6
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
          "space-2-2": {
            "bbox": {
              "x": [
                0.2,
                4.6
              ],
              "y": [
                0.2,
                16.6
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/1/spaces/2"
            ],
            "storey_id": "storey-2"
          },
          "space-3-0": {
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                0.2,
                4.6
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
          "space-3-1": {
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                12.2,
                16.6
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
          },
          "space-3-2": {
            "bbox": {
              "x": [
                0.2,
                4.6
              ],
              "y": [
                0.2,
                16.6
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/2/spaces/2"
            ],
            "storey_id": "storey-3"
          }
        },
        "stairs": {
          "stair-1": {
            "bbox": {
              "x": [
                0.4,
                1.6
              ],
              "y": [
                5.4,
                10.8
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
                2.8,
                4.0
              ],
              "y": [
                5.4,
                10.8
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
          "wall-1-courtyard_north": {
            "axis": "x",
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                12.0,
                12.2
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-courtyard_north",
            "source_fact_refs": [
              "/known_facts/walls/6"
            ]
          },
          "wall-1-courtyard_south": {
            "axis": "x",
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                4.6,
                4.8
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-courtyard_south",
            "source_fact_refs": [
              "/known_facts/walls/5"
            ]
          },
          "wall-1-east_north": {
            "axis": "y",
            "bbox": {
              "x": [
                13.0,
                13.2
              ],
              "y": [
                12.0,
                16.6
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-east_north",
            "source_fact_refs": [
              "/known_facts/walls/4"
            ]
          },
          "wall-1-east_south": {
            "axis": "y",
            "bbox": {
              "x": [
                13.0,
                13.2
              ],
              "y": [
                0.2,
                4.8
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-east_south",
            "source_fact_refs": [
              "/known_facts/walls/3"
            ]
          },
          "wall-1-north": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                16.6,
                16.8
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-north",
            "source_fact_refs": [
              "/known_facts/walls/1"
            ]
          },
          "wall-1-partition_north": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                12.0,
                16.6
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-partition_north",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/1"
            ]
          },
          "wall-1-partition_south": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                0.2,
                4.8
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-partition_south",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/0"
            ]
          },
          "wall-1-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-south",
            "source_fact_refs": [
              "/known_facts/walls/0"
            ]
          },
          "wall-1-spine": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                4.8,
                12.0
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-spine",
            "source_fact_refs": [
              "/known_facts/walls/7"
            ]
          },
          "wall-1-west": {
            "axis": "y",
            "bbox": {
              "x": [
                0.0,
                0.2
              ],
              "y": [
                0.2,
                16.6
              ],
              "z": [
                0.0,
                3.0
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-1-west",
            "source_fact_refs": [
              "/known_facts/walls/2"
            ]
          },
          "wall-2-courtyard_north": {
            "axis": "x",
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                12.0,
                12.2
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-courtyard_north",
            "source_fact_refs": [
              "/known_facts/walls/16"
            ]
          },
          "wall-2-courtyard_south": {
            "axis": "x",
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                4.6,
                4.8
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-courtyard_south",
            "source_fact_refs": [
              "/known_facts/walls/15"
            ]
          },
          "wall-2-east_north": {
            "axis": "y",
            "bbox": {
              "x": [
                13.0,
                13.2
              ],
              "y": [
                12.0,
                16.6
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-east_north",
            "source_fact_refs": [
              "/known_facts/walls/14"
            ]
          },
          "wall-2-east_south": {
            "axis": "y",
            "bbox": {
              "x": [
                13.0,
                13.2
              ],
              "y": [
                0.2,
                4.8
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-east_south",
            "source_fact_refs": [
              "/known_facts/walls/13"
            ]
          },
          "wall-2-north": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                16.6,
                16.8
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-north",
            "source_fact_refs": [
              "/known_facts/walls/11"
            ]
          },
          "wall-2-partition_north": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                12.0,
                16.6
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-partition_north",
            "source_fact_refs": [
              "/known_facts/storeys/1/walls/interior/1"
            ]
          },
          "wall-2-partition_south": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                0.2,
                4.8
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-partition_south",
            "source_fact_refs": [
              "/known_facts/storeys/1/walls/interior/0"
            ]
          },
          "wall-2-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-south",
            "source_fact_refs": [
              "/known_facts/walls/10"
            ]
          },
          "wall-2-spine": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                4.8,
                12.0
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-spine",
            "source_fact_refs": [
              "/known_facts/walls/17"
            ]
          },
          "wall-2-west": {
            "axis": "y",
            "bbox": {
              "x": [
                0.0,
                0.2
              ],
              "y": [
                0.2,
                16.6
              ],
              "z": [
                3.15,
                6.15
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-2-west",
            "source_fact_refs": [
              "/known_facts/walls/12"
            ]
          },
          "wall-3-courtyard_north": {
            "axis": "x",
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                12.0,
                12.2
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-courtyard_north",
            "source_fact_refs": [
              "/known_facts/walls/26"
            ]
          },
          "wall-3-courtyard_south": {
            "axis": "x",
            "bbox": {
              "x": [
                4.8,
                13.0
              ],
              "y": [
                4.6,
                4.8
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-courtyard_south",
            "source_fact_refs": [
              "/known_facts/walls/25"
            ]
          },
          "wall-3-east_north": {
            "axis": "y",
            "bbox": {
              "x": [
                13.0,
                13.2
              ],
              "y": [
                12.0,
                16.6
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-east_north",
            "source_fact_refs": [
              "/known_facts/walls/24"
            ]
          },
          "wall-3-east_south": {
            "axis": "y",
            "bbox": {
              "x": [
                13.0,
                13.2
              ],
              "y": [
                0.2,
                4.8
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-east_south",
            "source_fact_refs": [
              "/known_facts/walls/23"
            ]
          },
          "wall-3-north": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                16.6,
                16.8
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-north",
            "source_fact_refs": [
              "/known_facts/walls/21"
            ]
          },
          "wall-3-partition_north": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                12.0,
                16.6
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-partition_north",
            "source_fact_refs": [
              "/known_facts/storeys/2/walls/interior/1"
            ]
          },
          "wall-3-partition_south": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                0.2,
                4.8
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-partition_south",
            "source_fact_refs": [
              "/known_facts/storeys/2/walls/interior/0"
            ]
          },
          "wall-3-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                13.2
              ],
              "y": [
                0.0,
                0.2
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-south",
            "source_fact_refs": [
              "/known_facts/walls/20"
            ]
          },
          "wall-3-spine": {
            "axis": "y",
            "bbox": {
              "x": [
                4.6,
                4.8
              ],
              "y": [
                4.8,
                12.0
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-spine",
            "source_fact_refs": [
              "/known_facts/walls/27"
            ]
          },
          "wall-3-west": {
            "axis": "y",
            "bbox": {
              "x": [
                0.0,
                0.2
              ],
              "y": [
                0.2,
                16.6
              ],
              "z": [
                6.3,
                9.3
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-3-west",
            "source_fact_refs": [
              "/known_facts/walls/22"
            ]
          }
        },
        "windows": {}
      },
      "semantic_verification": {
        "basis": "request expectations independently compared with reopened IFC before atomic publication",
        "expectations": [
          {
            "entity_id": "wall-1-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-east_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-east_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-courtyard_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-courtyard_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-spine",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-partition_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-partition_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "slab-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "ifcwindow-1-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-5",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-6",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-1-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-1-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-1-entry",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "wall-2-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-east_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-east_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-courtyard_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-courtyard_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-spine",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-partition_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-partition_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "slab-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "ifcwindow-2-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-5",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-6",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/38",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-2-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/39",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-2-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/40",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "wall-3-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/41",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/42",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/43",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-east_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/44",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-east_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/45",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-courtyard_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/46",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-courtyard_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/47",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-spine",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-partition_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-partition_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "slab-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "ifcwindow-3-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-5",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-6",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-3-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-3-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "roof-slab",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "wall-1-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/0",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/1",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/2",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-east_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/3",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-east_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/4",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-courtyard_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/5",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-courtyard_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/6",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-spine",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/7",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-partition_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/8",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-1-partition_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/9",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "slab-1",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/10",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "ifcwindow-1-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/11",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/12",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/13",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/14",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/15",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-5",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/16",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-1-6",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/17",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-1-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/18",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-1-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/19",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-1-entry",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/20",
            "value": {
              "template_id": "door-left",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "wall-2-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/21",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/22",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/23",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-east_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/24",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-east_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/25",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-courtyard_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/26",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-courtyard_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/27",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-spine",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/28",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-partition_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/29",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-2-partition_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/30",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "slab-2",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/31",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "ifcwindow-2-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/32",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/33",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/34",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/35",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/36",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-5",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/37",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-2-6",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/38",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-2-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/39",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-2-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/40",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "wall-3-south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/41",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/42",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-west",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/43",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-east_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/44",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-east_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/45",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-courtyard_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/46",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-courtyard_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/47",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-spine",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/48",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-partition_south",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/49",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "wall-3-partition_north",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/50",
            "value": {
              "kind": "single_material",
              "name": "砖"
            }
          },
          {
            "entity_id": "slab-3",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/51",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
            }
          },
          {
            "entity_id": "ifcwindow-3-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/52",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/53",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-2",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/54",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-3",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/55",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-4",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/56",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-5",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/57",
            "value": {
              "template_id": "window-double-vertical",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcwindow-3-6",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/58",
            "value": {
              "template_id": "window-single",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-3-0",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/59",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "ifcdoor-3-1",
            "kind": "template",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/60",
            "value": {
              "template_id": "door-right",
              "template_version": "text2ifc/basic-filling/1.0"
            }
          },
          {
            "entity_id": "roof-slab",
            "kind": "material",
            "scope": "direct",
            "source_path": "/known_facts/semantic_requirements/61",
            "value": {
              "kind": "single_material",
              "name": "混凝土"
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
    "created_at": "2026-09-10T13:37:17+00:00",
    "event_index": 4,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "cc2db329ab7cb4ae",
      "evidence_class": "unit_test_fixture",
      "output_dir": "dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/offline-runner/runs/cc2db329ab7cb4ae",
      "report_path": "dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/offline-runner/runs/cc2db329ab7cb4ae/report.md",
      "response_id": "response-package-3",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "event_index": 5,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "cc2db329ab7cb4ae",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\output.ifc",
      "output_dir": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae",
      "report_path": "dataset\\processed\\ifc-presentation-validation\\c-shaped-teaching-building-20260910\\offline-runner\\runs\\cc2db329ab7cb4ae\\report.md",
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
    "created_at": "2026-09-10T13:36:50+00:00",
    "kind": "expected_facts",
    "path": "runs/cc2db329ab7cb4ae/expected-facts.json"
  },
  {
    "created_at": "2026-09-10T13:36:51+00:00",
    "kind": "candidate",
    "path": "runs/cc2db329ab7cb4ae/candidate.json"
  },
  {
    "created_at": "2026-09-10T13:36:51+00:00",
    "kind": "semantic_capabilities",
    "path": "runs/cc2db329ab7cb4ae/semantic-capabilities.json"
  },
  {
    "created_at": "2026-09-10T13:36:51+00:00",
    "kind": "semantic_coverage",
    "path": "runs/cc2db329ab7cb4ae/semantic-coverage.json"
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "kind": "issues",
    "path": "runs/cc2db329ab7cb4ae/issues.json"
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "kind": "route_decision",
    "path": "runs/cc2db329ab7cb4ae/route-decision.json"
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "kind": "feedback_rounds",
    "path": "runs/cc2db329ab7cb4ae/feedback-rounds.json"
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "kind": "ifc",
    "path": "runs/cc2db329ab7cb4ae/output.ifc"
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "kind": "report",
    "path": "runs/cc2db329ab7cb4ae/report.md"
  },
  {
    "created_at": "2026-09-10T13:37:40+00:00",
    "kind": "session_export",
    "path": "runs/cc2db329ab7cb4ae/session-export.json"
  }
]
```
