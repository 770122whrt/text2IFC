# Phase 6.1 Live Mimo Run Report

Generated from trace sidecars. This report is not hand-authored evidence.

## Original Input

```text
请设计并生成一栋两层的小型社区阅读与活动楼，提供完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静的多功能活动厅，东侧设置独立楼梯间。希望它看起来像一栋完整的小建筑：立面门窗上下对齐、间距均衡，墙体、门窗框和门扇配色协调，有真实的窗框、玻璃、门框、门扇与楼梯踏步。采用 warm-residential 风格，玻璃透明；不要求家具、机电、栏杆、复杂五金或外伸装饰。

建筑内部净尺寸为东西 9 米、南北 8 米，外墙厚 200 毫米。首层完成面标高 0，二层完成面标高 3150，每层室内净高 3000。地坪和二层楼板厚 150；平屋面底标高 6150、厚 150。地坪、楼板和屋面覆盖外墙外边界；二层楼板须留实际楼梯洞口，不能用整块楼板封住楼梯。各层外墙独立，不能跨楼层复用。

以首层室内西南角为原点，向东为 X、向北为 Y、向上为 Z。每层西侧大厅净范围为 X=0～6800、Y=0～8000；分隔墙占 X=6800～7000，东侧楼梯间净范围为 X=7000～9000、Y=0～8000。首层在分隔墙南端开一樘门，中心距室内南边 600；二层在分隔墙北端开一樘门，中心距室内南边 7300，两樘门均宽 900、高 2100，右单开，底面与本层地坪齐平。只生成这一道分隔墙，不把大厅与楼梯間的边界重复建成两道墙。

楼梯沿北向直跑，从首层完成面 0 升到二层完成面 3150，属于首层并连接二层。净宽 1200，平面范围 X=7400～8600、Y=1200～6600，18 级、每级高 175、踏步进深 300。首层南端保留 1200 深的进梯区域，二层北端保留 Y=6600～8000 的平台。二层楼梯洞口范围为 X=7200～8800、Y=1200～6600，洞口穿透楼板。首层为阅览厅和楼梯间各建一个空间，二层为活动厅及北端楼梯平台各建一个空间；洞口不得当成房间。

主入口位于首层南墙，中心距室内西边 3400，宽 1200、高 2400，左单开，门底与地坪齐平。南立面每层各有两扇双竖面板窗，中心距室内西边分别为 1500、5300，均宽 1800、高 1500、窗台高 900；上下层窗中心对齐，首层入口在两窗之间。每层北墙在西侧大厅中部各有一扇宽 2400、高 1500 的双竖面板窗，中心距西边 3400、窗台高 900。每层西墙中央各有一扇宽 1800、高 1500 的双竖面板窗，中心距南边 4000、窗台高 900。每层东墙中央各有一扇宽 900、高 1800 的单面板窗，中心距南边 4000、窗台高 600。窗台高度均从所属楼层完成面算起。总计 3 樘门、10 扇窗，每个开口必须与门窗名义宽高相同并穿透自己的宿主墙，门窗均置于相应楼层。

墙体材料为砖；地坪、二层楼板和屋面材料为混凝土。其他构件不指定物理材料，不要由颜色推断木材或玻璃材料。未提供强度、耐火、承重或热工性能，也没有共享 Type 的要求，不要自动补写这些属性或强制合并 Type。尺寸及空间关系必须满足以上要求；如果有真实冲突，请明确指出，不要静默改变。
```

Source: [design-brief/input.txt](design-brief/input.txt)

## Conversation

```json
[
  {
    "content": "请设计并生成一栋两层的小型社区阅读与活动楼，提供完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静的多功能活动厅，东侧设置独立楼梯间。希望它看起来像一栋完整的小建筑：立面门窗上下对齐、间距均衡，墙体、门窗框和门扇配色协调，有真实的窗框、玻璃、门框、门扇与楼梯踏步。采用 warm-residential 风格，玻璃透明；不要求家具、机电、栏杆、复杂五金或外伸装饰。\n\n建筑内部净尺寸为东西 9 米、南北 8 米，外墙厚 200 毫米。首层完成面标高 0，二层完成面标高 3150，每层室内净高 3000。地坪和二层楼板厚 150；平屋面底标高 6150、厚 150。地坪、楼板和屋面覆盖外墙外边界；二层楼板须留实际楼梯洞口，不能用整块楼板封住楼梯。各层外墙独立，不能跨楼层复用。\n\n以首层室内西南角为原点，向东为 X、向北为 Y、向上为 Z。每层西侧大厅净范围为 X=0～6800、Y=0～8000；分隔墙占 X=6800～7000，东侧楼梯间净范围为 X=7000～9000、Y=0～8000。首层在分隔墙南端开一樘门，中心距室内南边 600；二层在分隔墙北端开一樘门，中心距室内南边 7300，两樘门均宽 900、高 2100，右单开，底面与本层地坪齐平。只生成这一道分隔墙，不把大厅与楼梯間的边界重复建成两道墙。\n\n楼梯沿北向直跑，从首层完成面 0 升到二层完成面 3150，属于首层并连接二层。净宽 1200，平面范围 X=7400～8600、Y=1200～6600，18 级、每级高 175、踏步进深 300。首层南端保留 1200 深的进梯区域，二层北端保留 Y=6600～8000 的平台。二层楼梯洞口范围为 X=7200～8800、Y=1200～6600，洞口穿透楼板。首层为阅览厅和楼梯间各建一个空间，二层为活动厅及北端楼梯平台各建一个空间；洞口不得当成房间。\n\n主入口位于首层南墙，中心距室内西边 3400，宽 1200、高 2400，左单开，门底与地坪齐平。南立面每层各有两扇双竖面板窗，中心距室内西边分别为 1500、5300，均宽 1800、高 1500、窗台高 900；上下层窗中心对齐，首层入口在两窗之间。每层北墙在西侧大厅中部各有一扇宽 2400、高 1500 的双竖面板窗，中心距西边 3400、窗台高 900。每层西墙中央各有一扇宽 1800、高 1500 的双竖面板窗，中心距南边 4000、窗台高 900。每层东墙中央各有一扇宽 900、高 1800 的单面板窗，中心距南边 4000、窗台高 600。窗台高度均从所属楼层完成面算起。总计 3 樘门、10 扇窗，每个开口必须与门窗名义宽高相同并穿透自己的宿主墙，门窗均置于相应楼层。\n\n墙体材料为砖；地坪、二层楼板和屋面材料为混凝土。其他构件不指定物理材料，不要由颜色推断木材或玻璃材料。未提供强度、耐火、承重或热工性能，也没有共享 Type 的要求，不要自动补写这些属性或强制合并 Type。尺寸及空间关系必须满足以上要求；如果有真实冲突，请明确指出，不要静默改变。",
    "question_ids": [],
    "role": "user",
    "turn_id": "turn-user-001"
  }
]
```

Source: [design-brief/conversation.json](design-brief/conversation.json)

## Design Brief Agent

- response_id: `cbd4a500-48aa-4d1e-9909-f2fb74d5ebc4`
- stop_reason: `None`
- evidence_class: `None`

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

- response_id: `9ff037cc-ec73-4a93-af87-ffb7f59da3c6`
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

- response_id: `e3565687-0369-4121-8576-4905196a48b4`
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
  "candidate_entity_count": 51,
  "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
  "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
  "case_id": "5cd2006f0891913f",
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
      "path": "/known_facts/building/interior_clear_bounds/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        0,
        9000
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/interior_clear_bounds/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        0,
        8000
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/storey_count",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 2
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
              9200
            ],
            "y": [
              -200,
              8200
            ]
          },
          "id": "ground-slab",
          "storey": "storey-1",
          "thickness_mm": 150,
          "top_elevation_mm": 0
        },
        {
          "bounds": {
            "x": [
              -200,
              9200
            ],
            "y": [
              -200,
              8200
            ]
          },
          "id": "second-floor-slab",
          "opening": {
            "bounds": {
              "x": [
                7200,
                8800
              ],
              "y": [
                1200,
                6600
              ]
            }
          },
          "storey": "storey-2",
          "thickness_mm": 150,
          "top_elevation_mm": 3150
        }
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bottom_elevation_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 6150
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bounds/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        -200,
        9200
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/bounds/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        -200,
        8200
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
          "entity_id": "ground-slab",
          "material": {
            "kind": "single_material",
            "name": "混凝土"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "second-floor-slab",
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
          "entity_id": "door-ground-main",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "door-ground-partition",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "door-second-partition",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-ground-south-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-ground-south-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-ground-north-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-ground-west-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-ground-east-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-single",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-second-south-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-second-south-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-second-north-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-second-west-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "window-second-east-1",
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
              7400,
              8600
            ],
            "y": [
              1200,
              6600
            ]
          },
          "end_elevation_mm": 3150,
          "from_storey": "storey-1",
          "id": "stair-1",
          "number_of_risers": 18,
          "opening_bounds": {
            "x": [
              7200,
              8800
            ],
            "y": [
              1200,
              6600
            ]
          },
          "riser_height_mm": 175,
          "run_direction": "north",
          "start_elevation_mm": 0,
          "to_storey": "storey-2",
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
              "center_x_from_west_inner_edge_mm": 3400,
              "height_mm": 2400,
              "host_wall": "storey-1-wall-south",
              "id": "door-ground-main",
              "single_leaf": "left",
              "width_mm": 1200
            },
            {
              "center_y_from_south_inner_edge_mm": 600,
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition",
              "id": "door-ground-partition",
              "single_leaf": "right",
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
                  6800
                ],
                "y": [
                  0,
                  8000
                ]
              },
              "id": "space-reading-lobby",
              "name": "接待阅览厅"
            },
            {
              "bounds": {
                "x": [
                  7000,
                  9000
                ],
                "y": [
                  0,
                  8000
                ]
              },
              "id": "space-stair-hall-1",
              "name": "楼梯间"
            }
          ],
          "walls": {
            "exterior": [
              {
                "id": "storey-1-wall-south",
                "side": "south",
                "thickness_mm": 200
              },
              {
                "id": "storey-1-wall-north",
                "side": "north",
                "thickness_mm": 200
              },
              {
                "id": "storey-1-wall-west",
                "side": "west",
                "thickness_mm": 200
              },
              {
                "id": "storey-1-wall-east",
                "side": "east",
                "thickness_mm": 200
              }
            ],
            "interior": [
              {
                "connects": [
                  "space-reading-lobby",
                  "space-stair-hall-1"
                ],
                "id": "storey-1-wall-partition",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_x_from_west_inner_edge_mm": 1500,
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "window-ground-south-1",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_x_from_west_inner_edge_mm": 5300,
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "window-ground-south-2",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_x_from_west_inner_edge_mm": 3400,
              "height_mm": 1500,
              "host_wall": "storey-1-wall-north",
              "id": "window-ground-north-1",
              "sill_height_mm": 900,
              "width_mm": 2400
            },
            {
              "center_y_from_south_inner_edge_mm": 4000,
              "height_mm": 1500,
              "host_wall": "storey-1-wall-west",
              "id": "window-ground-west-1",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_y_from_south_inner_edge_mm": 4000,
              "height_mm": 1800,
              "host_wall": "storey-1-wall-east",
              "id": "window-ground-east-1",
              "sill_height_mm": 600,
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "center_y_from_south_inner_edge_mm": 7300,
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition",
              "id": "door-second-partition",
              "single_leaf": "right",
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
                  6800
                ],
                "y": [
                  0,
                  8000
                ]
              },
              "id": "space-activity-hall",
              "name": "多功能活动厅"
            },
            {
              "bounds": {
                "x": [
                  7000,
                  9000
                ],
                "y": [
                  6600,
                  8000
                ]
              },
              "id": "space-stair-platform-2",
              "name": "北端楼梯平台"
            }
          ],
          "walls": {
            "exterior": [
              {
                "id": "storey-2-wall-south",
                "side": "south",
                "thickness_mm": 200
              },
              {
                "id": "storey-2-wall-north",
                "side": "north",
                "thickness_mm": 200
              },
              {
                "id": "storey-2-wall-west",
                "side": "west",
                "thickness_mm": 200
              },
              {
                "id": "storey-2-wall-east",
                "side": "east",
                "thickness_mm": 200
              }
            ],
            "interior": [
              {
                "connects": [
                  "space-activity-hall",
                  "space-stair-platform-2"
                ],
                "id": "storey-2-wall-partition",
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_x_from_west_inner_edge_mm": 1500,
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "window-second-south-1",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_x_from_west_inner_edge_mm": 5300,
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "window-second-south-2",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_x_from_west_inner_edge_mm": 3400,
              "height_mm": 1500,
              "host_wall": "storey-2-wall-north",
              "id": "window-second-north-1",
              "sill_height_mm": 900,
              "width_mm": 2400
            },
            {
              "center_y_from_south_inner_edge_mm": 4000,
              "height_mm": 1500,
              "host_wall": "storey-2-wall-west",
              "id": "window-second-west-1",
              "sill_height_mm": 900,
              "width_mm": 1800
            },
            {
              "center_y_from_south_inner_edge_mm": 4000,
              "height_mm": 1800,
              "host_wall": "storey-2-wall-east",
              "id": "window-second-east-1",
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
        "opening-second-floor-slab-stair"
      ],
      "message": "Expected component 'opening-second-floor-slab-stair' was not found in the IFC.",
      "path": "/floor_openings/opening-second-floor-slab-stair",
      "source_fact_refs": [
        "/known_facts/floor_slabs/1/openings/0"
      ]
    },
    {
      "actual": {
        "reason": "shared_boundary_not_unique_or_wall_thickness_missing"
      },
      "code": "GEOMETRY_EXPECTATION_INCOMPLETE",
      "message": "Required geometry could not be derived from confirmed facts.",
      "path": "/known_facts/storeys/0/walls/interior/0",
      "source_fact_refs": [
        "/known_facts/storeys/0/spaces/0",
        "/known_facts/storeys/0/spaces/1",
        "/known_facts/storeys/0/walls/interior/0"
      ]
    },
    {
      "actual": {
        "reason": "shared_boundary_not_unique_or_wall_thickness_missing"
      },
      "code": "GEOMETRY_EXPECTATION_INCOMPLETE",
      "message": "Required geometry could not be derived from confirmed facts.",
      "path": "/known_facts/storeys/1/walls/interior/0",
      "source_fact_refs": [
        "/known_facts/storeys/1/spaces/0",
        "/known_facts/storeys/1/spaces/1",
        "/known_facts/storeys/1/walls/interior/0"
      ]
    }
  ],
  "metrics": {
    "case_id": "5cd2006f0891913f",
    "expectation_complete": false,
    "floor_openings": {},
    "products": {},
    "roof": {
      "roof-slab": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            9.2
          ],
          "y": [
            -0.20000000000000018,
            8.2
          ],
          "z": [
            6.15,
            6.300000000000001
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "slabs": {
      "ground-slab": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            9.2
          ],
          "y": [
            -0.20000000000000018,
            8.2
          ],
          "z": [
            -0.15,
            0.0
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "second-floor-slab": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            9.2
          ],
          "y": [
            -0.20000000000000018,
            8.2
          ],
          "z": [
            3.0,
            3.15
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "spaces": {
      "space-storey-1-space-reading-lobby": {
        "bbox": {
          "x": [
            0.0,
            6.8
          ],
          "y": [
            0.0,
            8.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-space-stair-hall-1": {
        "bbox": {
          "x": [
            7.0,
            9.0
          ],
          "y": [
            0.0,
            8.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-space-activity-hall": {
        "bbox": {
          "x": [
            0.0,
            6.8
          ],
          "y": [
            0.0,
            8.0
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-space-stair-platform-2": {
        "bbox": {
          "x": [
            7.0,
            9.0
          ],
          "y": [
            6.6,
            8.0
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      }
    },
    "stairs": {
      "stair-1": {
        "bbox": {
          "x": [
            7.4,
            8.6
          ],
          "y": [
            1.2,
            6.6000000000000005
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
      }
    },
    "unresolved_expectation_count": 2,
    "wall_set_convention": "primary",
    "walls": {}
  },
  "success": false
}
```

Source: [geometry-feedback.json](geometry-feedback.json)

## Metrics

### Design Brief Agent

```json
{
  "design_status": "ready",
  "finish_reason": "stop",
  "model": "deepseek-v4-flash",
  "parse_valid": true,
  "prompt_template_hash": "sha256:5980fd3098a237d24e03adb7467f70cc18f1efe176076e5d0e63e1972e36f81d",
  "prompt_template_id": "design-brief.v2.2",
  "question_count": 0,
  "response_id": "cbd4a500-48aa-4d1e-9909-f2fb74d5ebc4",
  "schema_semantic_valid": true,
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 33719,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 28459,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 16384,
    "prompt_cache_miss_tokens": 107,
    "prompt_tokens": 16491,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 16384
    },
    "total_tokens": 50210
  }
}
```

Source: [design-brief/metrics.json](design-brief/metrics.json)

### BIM JSON Generator

```json
{
  "case_id": "5cd2006f0891913f",
  "classification": "formal",
  "contract_status": "formal",
  "contract_valid": true,
  "evidence_class": "live",
  "generator_call_index": 1,
  "has_generation_feedback": false,
  "issue_count": 0,
  "model": "deepseek-v4-flash",
  "normalization_diagnostics": [],
  "parse_valid": true,
  "response_id": "9ff037cc-ec73-4a93-af87-ffb7f59da3c6",
  "stage": "generate",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 48955,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 35535,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 24576,
    "prompt_cache_miss_tokens": 7085,
    "prompt_tokens": 31661,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 24576
    },
    "total_tokens": 80616
  }
}
```

Source: [generator/metrics.json](generator/metrics.json)

### Repair Route

```json
{
  "case_id": "5cd2006f0891913f",
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
  "source_generator_response_id": "9ff037cc-ec73-4a93-af87-ffb7f59da3c6",
  "stage": "repair",
  "valid": true
}
```

Source: [repair/metrics.json](repair/metrics.json)

### Audit Agent

```json
{
  "case_id": "5cd2006f0891913f",
  "evidence_class": "live",
  "issue_count": 0,
  "model": "deepseek-v4-flash",
  "normalization_diagnostics": [],
  "response_id": "e3565687-0369-4121-8576-4905196a48b4",
  "route_decision": "generator_regeneration_required",
  "route_owner_stage": "generator",
  "schema_semantic_valid": true,
  "stage": "audit",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 13868,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 13377,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 26064,
    "prompt_tokens": 26064,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    },
    "total_tokens": 39932
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
