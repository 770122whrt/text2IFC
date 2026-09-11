# Phase 6.1 Live Mimo Run Report

Generated from trace sidecars. This report is not hand-authored evidence.

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

Source: [design-brief/input.txt](design-brief/input.txt)

## Conversation

```json
[
  {
    "content": "请帮我建一栋三层的小型教学活动楼，平面做成向东敞开的C形。重点是清楚、整齐、协调，保留中间开敞空间；这次只建建筑本体，不做景观、家具、栏杆和设备，不把模型当作可直接施工的设计。\n\n尺寸按毫米表达，下面提到的距离也给出米，方便读。以建筑外轮廓西南角为定位原点，往东、往北、往上分别是三个正方向。\n\n建筑外包络东西13.2米、南北16.8米。西侧是一条宽4.8米、贯通南北的交通体量；北翼和南翼各向东伸出8.4米，各宽4.8米。中间东侧留出东西8.4米、南北7.2米的开敞缺口，缺口南边距建筑最南端4.8米。三层的外轮廓完全相同，屋面也跟着C形走，不能拿一个完整矩形把中间缺口盖上，也不加跨缺口的桥。\n\n首层、二层、三层完成面标高分别是0、3.15、6.30米；各层净高3米。楼板厚150毫米，顶面与相应完成面齐平；平屋面底面在9.30米，厚150毫米。各层楼板和屋面采用连续C形轮廓。首层楼板没有楼梯洞口，二、三层按下面的楼梯要求真实开洞。\n\n外墙及内部分隔墙统一厚200毫米，墙体全部落在外轮廓以内。外墙沿C形的八条边布置，相邻墙端部连接但不要重复堆叠。每层只有南、北两个教学活动室，以及西侧一个贯通的交通/楼梯空间，共九个空间。教学室与西侧交通空间之间的分隔墙，都放在距建筑西侧4.6到4.8米这一条带内；南室的分隔墙从南端内墙面延伸到4.8米位置，北室的分隔墙从12米位置延伸到北端内墙面。不要再分小教室。\n\n两个教学室的净空间：南室东西4.8到13.0米、南北0.2到4.6米；北室东西4.8到13.0米、南北12.2到16.6米。交通空间的净范围为东西0.2到4.6米、南北0.2到16.6米。空间高度都取3米，与所属楼层对应。\n\n楼梯放在西侧交通空间内，用两个在平面上并列的直跑梯段联系三层：一层到二层的梯段距建筑西侧0.4到1.6米，南北5.4到10.8米，从南向北上升；二层到三层的梯段距西侧2.8到4.0米，南北范围相同，从北向南上升。两段净宽均1.2米，每段18级、每级高175毫米，踏步水平进深300毫米；标高分别0到3.15米、3.15到6.30米。北侧平台利用二层楼板在南北10.8到12米之间的区域，南侧平台利用三层楼板在4.2到5.4米之间的区域，两处平台东西范围均0.2到4.6米，不另叠加一块实体板。二层楼板洞口只对应第一段，三层只对应第二段，洞口平面范围与各自梯段一致，穿透150毫米楼板。\n\n每层南、北教学室各有一扇900毫米宽、2100毫米高的右单开门，都在上述分隔墙上，门中心分别距建筑南侧2.4米和14.4米，门底与本层完成面平齐。首层另设一扇1200毫米宽、2400毫米高的左单开入口门，位于西外墙中间，中心距南侧8.4米。上层不要复制这个入口门。门都带基本门框和门扇，不加复杂五金。\n\n每层七扇窗：南教学室的南外墙、北教学室的北外墙各两扇，中心距西侧7.2米和10.8米；南教学室朝缺口的墙和北教学室朝缺口的墙各一扇，中心距西侧9米。这六扇窗均宽1800毫米、高1500毫米，采用双竖面板。西外墙再设一扇宽900毫米、高1800毫米的单面板窗，中心距南侧2.4米。所有窗台距本层完成面900毫米，窗洞、窗和宿主墙一一对应，三层上下对齐。不要在东侧两个端墙上额外加窗。\n\n墙体明确采用砖，楼板及屋面明确采用混凝土，其他构件暂不指定物理材料。风格用现有warm-residential协调主题：暖浅墙面、深色细门窗框、通透玻璃和与框分色的门扇。不要为了视觉效果增加别的物理材料、整件颜色覆盖或性能属性。我没有要求共享Type；只保留合法表达所需的最小附件。\n\n这些尺寸与布置是本次希望忠实表达的方案。若有必要事实缺失、输入矛盾、当前系统不支持的表达，或你认为会影响使用的明显几何问题，请先集中指出并澄清，不要自行改尺寸或补构件。最终报告应区分用户要求符合性、确定性检查和尚未验证的工程合理性；没有检测到问题也不能写成全面合规。\n",
    "role": "user",
    "turn_id": "turn-user-001"
  },
  {
    "content": "C 型楼首层入口目前正对第一梯段，墙内侧与梯段之间仅约0.2米。是否将入口门沿西墙南移，中心改为距建筑南侧4.2米（原8.4米），保持门尺寸、楼梯、窗及其他要求不变？该位置避开了现有窗和梯段平面范围，后续仍需完整检查。",
    "role": "assistant",
    "turn_id": "turn-assistant-002"
  },
  {
    "content": "入口南移至4.2米（推荐）",
    "role": "user",
    "turn_id": "turn-user-003"
  }
]
```

Source: [design-brief/conversation.json](design-brief/conversation.json)

## Design Brief Agent

- response_id: `49ac8c08-6883-44dd-b121-cd274fcac2f2`
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

- response_id: `92582d84-d330-4419-8e51-a8c9da5f0fea`
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

- response_id: `da4e8bd9-d19f-46fa-80a3-66fbd5e9add9`
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
  "candidate_entity_count": 111,
  "capability_profile_hash": "sha256:051dd624f853807e94cce4c82e43370c59c8b679e09a998dc69e17b2e3f9de71",
  "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.1/1.0",
  "case_id": "9b00e53444a948e7",
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
      "path": "/known_facts/appearance/seed",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "c-shape-teaching-building-3f"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/appearance/style_notes",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "暖浅墙面、深色细门窗框、通透玻璃、门扇与框分色；不新增其他物理材料、整件颜色覆盖或性能属性"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/axes/east",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "+X"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/axes/north",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "+Y"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/axes/up",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "+Z"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/envelope/x_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 13200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/envelope/x_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 0
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/envelope/y_max",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 16800
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/envelope/y_min",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 0
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/name",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "三层小型教学活动楼"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/no_bridge_across_notch",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": true
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/notch/bounds/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        4800,
        13200
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/notch/bounds/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        4800,
        12000
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/notch/open_to",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "east"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/notch/south_edge_offset_from_south_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 4800
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/origin",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "建筑外轮廓西南角"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/outline/polygon",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        [
          0,
          0
        ],
        [
          13200,
          0
        ],
        [
          13200,
          4800
        ],
        [
          4800,
          4800
        ],
        [
          4800,
          12000
        ],
        [
          13200,
          12000
        ],
        [
          13200,
          16800
        ],
        [
          0,
          16800
        ],
        [
          0,
          0
        ]
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/roof_follows_c_shape",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": true
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/shape",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "C 形，向东敞开，中部缺口保持开敞"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/storey_count",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 3
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/storeys_identical_outline",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": true
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/wall_thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 200
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/west_circulation_bar/bounds/x",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        0,
        4800
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/building/west_circulation_bar/bounds/y",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        0,
        16800
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/floor_slabs",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        {
          "id": "slab-storey-1-floor",
          "openings": [],
          "shape": "continuous_c",
          "storey": "storey-1",
          "thickness_mm": 150,
          "top_elevation_mm": 0,
          "top_flush_with_finish_level": true
        },
        {
          "id": "slab-storey-2-floor",
          "openings": [
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
              "for_stair": "stair-flight-1",
              "id": "opening-storey-2-flight-1",
              "penetrates_thickness_mm": 150
            }
          ],
          "shape": "continuous_c",
          "storey": "storey-2",
          "thickness_mm": 150,
          "top_elevation_mm": 3150,
          "top_flush_with_finish_level": true
        },
        {
          "id": "slab-storey-3-floor",
          "openings": [
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
              "for_stair": "stair-flight-2",
              "id": "opening-storey-3-flight-2",
              "penetrates_thickness_mm": 150
            }
          ],
          "shape": "continuous_c",
          "storey": "storey-3",
          "thickness_mm": 150,
          "top_elevation_mm": 6300,
          "top_flush_with_finish_level": true
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
      "path": "/known_facts/roof_slab/follows_c_outline",
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
      "path": "/known_facts/roof_slab/no_slab_over_notch",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": true
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/shape",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": "continuous_c"
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/roof_slab/thickness_mm",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": 150
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/scope/excluded",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "景观",
        "家具",
        "栏杆",
        "设备",
        "跨缺口连桥",
        "二层及三层入口门复制"
      ]
    },
    {
      "coverage_state": "represented",
      "path": "/known_facts/scope/included",
      "reason": "Fact is inside the current supported semantic profile.",
      "value": [
        "楼板",
        "屋面",
        "外墙",
        "内部分隔墙",
        "楼梯梯段与楼板平台",
        "门",
        "窗"
      ]
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
          "entity_id": "storey-1-wall-southwing-east",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-notch-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-notch-west",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-notch-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-northwing-east",
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
          "entity_id": "storey-1-wall-partition-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-1-wall-partition-north",
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
          "entity_id": "storey-2-wall-southwing-east",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-notch-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-notch-west",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-notch-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-northwing-east",
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
          "entity_id": "storey-2-wall-partition-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-2-wall-partition-north",
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
          "entity_id": "storey-3-wall-southwing-east",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-notch-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-notch-west",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-notch-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-northwing-east",
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
          "entity_id": "storey-3-wall-partition-south",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "storey-3-wall-partition-north",
          "material": {
            "kind": "single_material",
            "name": "Brick"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "slab-storey-1-floor",
          "material": {
            "kind": "single_material",
            "name": "Concrete"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "slab-storey-2-floor",
          "material": {
            "kind": "single_material",
            "name": "Concrete"
          },
          "scope": "direct",
          "source": "user"
        },
        {
          "entity_id": "slab-storey-3-floor",
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
          "entity_id": "storey-1-door-south-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-door-north-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-door-entrance",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-left",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-door-south-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-door-north-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-door-south-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "door-right",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-door-north-classroom",
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
          "entity_id": "storey-1-window-north-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-north-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-notch-south-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-1-window-notch-north-classroom",
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
          "entity_id": "storey-2-window-north-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-north-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-notch-south-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-2-window-notch-north-classroom",
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
          "entity_id": "storey-3-window-north-1",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-north-2",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-notch-south-classroom",
          "scope": "direct",
          "source": "user",
          "template": {
            "template_id": "window-double-vertical",
            "template_version": "text2ifc/basic-filling/1.0"
          }
        },
        {
          "entity_id": "storey-3-window-notch-north-classroom",
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
              400,
              1600
            ],
            "y": [
              5400,
              10800
            ]
          },
          "clear_width_mm": 1200,
          "end_elevation_mm": 3150,
          "from_storey": "storey-1",
          "id": "stair-flight-1",
          "landing": {
            "bounds": {
              "x": [
                200,
                4600
              ],
              "y": [
                10800,
                12000
              ]
            },
            "elevation_mm": 3150,
            "id": "landing-north",
            "separate_solid_slab": false,
            "slab": "slab-storey-2-floor"
          },
          "number_of_risers": 18,
          "opening_bounds": {
            "x": [
              400,
              1600
            ],
            "y": [
              5400,
              10800
            ]
          },
          "opening_host_slab": "slab-storey-2-floor",
          "riser_height_mm": 175,
          "run_direction": "south_to_north",
          "start_elevation_mm": 0,
          "to_storey": "storey-2",
          "tread_depth_mm": 300
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
          "clear_width_mm": 1200,
          "end_elevation_mm": 6300,
          "from_storey": "storey-2",
          "id": "stair-flight-2",
          "landing": {
            "bounds": {
              "x": [
                200,
                4600
              ],
              "y": [
                4200,
                5400
              ]
            },
            "elevation_mm": 6300,
            "id": "landing-south",
            "separate_solid_slab": false,
            "slab": "slab-storey-3-floor"
          },
          "number_of_risers": 18,
          "opening_bounds": {
            "x": [
              2800,
              4000
            ],
            "y": [
              5400,
              10800
            ]
          },
          "opening_host_slab": "slab-storey-3-floor",
          "riser_height_mm": 175,
          "run_direction": "north_to_south",
          "start_elevation_mm": 3150,
          "to_storey": "storey-3",
          "tread_depth_mm": 300
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
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                4700,
                2400
              ],
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-south",
              "id": "storey-1-door-south-classroom",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "type": "single_leaf_right",
              "width_mm": 900
            },
            {
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                4700,
                14400
              ],
              "height_mm": 2100,
              "host_wall": "storey-1-wall-partition-north",
              "id": "storey-1-door-north-classroom",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "type": "single_leaf_right",
              "width_mm": 900
            },
            {
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                100,
                4200
              ],
              "corrected_by": "turn-user-003",
              "height_mm": 2400,
              "host_wall": "storey-1-wall-west",
              "id": "storey-1-door-entrance",
              "only_on_storey": "storey-1",
              "sill_height_mm": 0,
              "template_id": "door-left",
              "type": "single_leaf_left",
              "width_mm": 1200
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
                  4800,
                  13000
                ],
                "y": [
                  200,
                  4600
                ]
              },
              "function": "teaching_activity_room",
              "height_mm": 3000,
              "id": "storey-1-space-south-classroom",
              "name": "南教学活动室"
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
              "function": "teaching_activity_room",
              "height_mm": 3000,
              "id": "storey-1-space-north-classroom",
              "name": "北教学活动室"
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
              "function": "circulation_and_stair",
              "height_mm": 3000,
              "id": "storey-1-space-circulation",
              "name": "交通/楼梯空间"
            }
          ],
          "walls": {
            "exterior": [
              {
                "end_mm": [
                  13100,
                  100
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-south",
                "side": "south",
                "start_mm": [
                  100,
                  100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  4700
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-southwing-east",
                "side": "east_of_south_wing",
                "start_mm": [
                  13100,
                  100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  4700,
                  4700
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-notch-south",
                "side": "notch_south",
                "start_mm": [
                  13100,
                  4700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  4700,
                  12100
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-notch-west",
                "side": "notch_west",
                "start_mm": [
                  4700,
                  4700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  12100
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-notch-north",
                "side": "notch_north",
                "start_mm": [
                  4700,
                  12100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  16700
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-northwing-east",
                "side": "east_of_north_wing",
                "start_mm": [
                  13100,
                  12100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  100,
                  16700
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-north",
                "side": "north",
                "start_mm": [
                  13100,
                  16700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  100,
                  100
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-west",
                "side": "west",
                "start_mm": [
                  100,
                  16700
                ],
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
                "connects": [
                  "storey-1-space-south-classroom",
                  "storey-1-space-circulation"
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-partition-south",
                "partition_band_from_west_mm": [
                  4600,
                  4800
                ],
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
                "connects": [
                  "storey-1-space-north-classroom",
                  "storey-1-space-circulation"
                ],
                "height_mm": 3000,
                "id": "storey-1-wall-partition-north",
                "partition_band_from_west_mm": [
                  4600,
                  4800
                ],
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                7200,
                100
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-window-south-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10800,
                100
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-south",
              "id": "storey-1-window-south-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                7200,
                16700
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-north",
              "id": "storey-1-window-north-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10800,
                16700
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-north",
              "id": "storey-1-window-north-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                9000,
                4700
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-notch-south",
              "id": "storey-1-window-notch-south-classroom",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                9000,
                12100
              ],
              "height_mm": 1500,
              "host_wall": "storey-1-wall-notch-north",
              "id": "storey-1-window-notch-north-classroom",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                100,
                2400
              ],
              "height_mm": 1800,
              "host_wall": "storey-1-wall-west",
              "id": "storey-1-window-west",
              "panels": "single",
              "sill_height_mm": 900,
              "template_id": "window-single",
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                4700,
                2400
              ],
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-south",
              "id": "storey-2-door-south-classroom",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "type": "single_leaf_right",
              "width_mm": 900
            },
            {
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                4700,
                14400
              ],
              "height_mm": 2100,
              "host_wall": "storey-2-wall-partition-north",
              "id": "storey-2-door-north-classroom",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "type": "single_leaf_right",
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
                  4800,
                  13000
                ],
                "y": [
                  200,
                  4600
                ]
              },
              "function": "teaching_activity_room",
              "height_mm": 3000,
              "id": "storey-2-space-south-classroom",
              "name": "南教学活动室"
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
              "function": "teaching_activity_room",
              "height_mm": 3000,
              "id": "storey-2-space-north-classroom",
              "name": "北教学活动室"
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
              "function": "circulation_and_stair",
              "height_mm": 3000,
              "id": "storey-2-space-circulation",
              "name": "交通/楼梯空间"
            }
          ],
          "walls": {
            "exterior": [
              {
                "end_mm": [
                  13100,
                  100
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-south",
                "side": "south",
                "start_mm": [
                  100,
                  100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  4700
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-southwing-east",
                "side": "east_of_south_wing",
                "start_mm": [
                  13100,
                  100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  4700,
                  4700
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-notch-south",
                "side": "notch_south",
                "start_mm": [
                  13100,
                  4700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  4700,
                  12100
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-notch-west",
                "side": "notch_west",
                "start_mm": [
                  4700,
                  4700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  12100
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-notch-north",
                "side": "notch_north",
                "start_mm": [
                  4700,
                  12100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  16700
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-northwing-east",
                "side": "east_of_north_wing",
                "start_mm": [
                  13100,
                  12100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  100,
                  16700
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-north",
                "side": "north",
                "start_mm": [
                  13100,
                  16700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  100,
                  100
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-west",
                "side": "west",
                "start_mm": [
                  100,
                  16700
                ],
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
                "connects": [
                  "storey-2-space-south-classroom",
                  "storey-2-space-circulation"
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-partition-south",
                "partition_band_from_west_mm": [
                  4600,
                  4800
                ],
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
                "connects": [
                  "storey-2-space-north-classroom",
                  "storey-2-space-circulation"
                ],
                "height_mm": 3000,
                "id": "storey-2-wall-partition-north",
                "partition_band_from_west_mm": [
                  4600,
                  4800
                ],
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                7200,
                100
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "storey-2-window-south-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10800,
                100
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-south",
              "id": "storey-2-window-south-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                7200,
                16700
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-north",
              "id": "storey-2-window-north-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10800,
                16700
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-north",
              "id": "storey-2-window-north-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                9000,
                4700
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-notch-south",
              "id": "storey-2-window-notch-south-classroom",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                9000,
                12100
              ],
              "height_mm": 1500,
              "host_wall": "storey-2-wall-notch-north",
              "id": "storey-2-window-notch-north-classroom",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                100,
                2400
              ],
              "height_mm": 1800,
              "host_wall": "storey-2-wall-west",
              "id": "storey-2-window-west",
              "panels": "single",
              "sill_height_mm": 900,
              "template_id": "window-single",
              "width_mm": 900
            }
          ]
        },
        {
          "doors": [
            {
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                4700,
                2400
              ],
              "height_mm": 2100,
              "host_wall": "storey-3-wall-partition-south",
              "id": "storey-3-door-south-classroom",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "type": "single_leaf_right",
              "width_mm": 900
            },
            {
              "bottom_flush_with_finish_floor": true,
              "center_global_mm": [
                4700,
                14400
              ],
              "height_mm": 2100,
              "host_wall": "storey-3-wall-partition-north",
              "id": "storey-3-door-north-classroom",
              "sill_height_mm": 0,
              "template_id": "door-right",
              "type": "single_leaf_right",
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
                  4800,
                  13000
                ],
                "y": [
                  200,
                  4600
                ]
              },
              "function": "teaching_activity_room",
              "height_mm": 3000,
              "id": "storey-3-space-south-classroom",
              "name": "南教学活动室"
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
              "function": "teaching_activity_room",
              "height_mm": 3000,
              "id": "storey-3-space-north-classroom",
              "name": "北教学活动室"
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
              "function": "circulation_and_stair",
              "height_mm": 3000,
              "id": "storey-3-space-circulation",
              "name": "交通/楼梯空间"
            }
          ],
          "walls": {
            "exterior": [
              {
                "end_mm": [
                  13100,
                  100
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-south",
                "side": "south",
                "start_mm": [
                  100,
                  100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  4700
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-southwing-east",
                "side": "east_of_south_wing",
                "start_mm": [
                  13100,
                  100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  4700,
                  4700
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-notch-south",
                "side": "notch_south",
                "start_mm": [
                  13100,
                  4700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  4700,
                  12100
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-notch-west",
                "side": "notch_west",
                "start_mm": [
                  4700,
                  4700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  12100
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-notch-north",
                "side": "notch_north",
                "start_mm": [
                  4700,
                  12100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  13100,
                  16700
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-northwing-east",
                "side": "east_of_north_wing",
                "start_mm": [
                  13100,
                  12100
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  100,
                  16700
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-north",
                "side": "north",
                "start_mm": [
                  13100,
                  16700
                ],
                "thickness_mm": 200
              },
              {
                "end_mm": [
                  100,
                  100
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-west",
                "side": "west",
                "start_mm": [
                  100,
                  16700
                ],
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
                "connects": [
                  "storey-3-space-south-classroom",
                  "storey-3-space-circulation"
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-partition-south",
                "partition_band_from_west_mm": [
                  4600,
                  4800
                ],
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
                "connects": [
                  "storey-3-space-north-classroom",
                  "storey-3-space-circulation"
                ],
                "height_mm": 3000,
                "id": "storey-3-wall-partition-north",
                "partition_band_from_west_mm": [
                  4600,
                  4800
                ],
                "thickness_mm": 200
              }
            ]
          },
          "windows": [
            {
              "center_global_mm": [
                7200,
                100
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-south",
              "id": "storey-3-window-south-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10800,
                100
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-south",
              "id": "storey-3-window-south-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                7200,
                16700
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-north",
              "id": "storey-3-window-north-1",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                10800,
                16700
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-north",
              "id": "storey-3-window-north-2",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                9000,
                4700
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-notch-south",
              "id": "storey-3-window-notch-south-classroom",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                9000,
                12100
              ],
              "height_mm": 1500,
              "host_wall": "storey-3-wall-notch-north",
              "id": "storey-3-window-notch-north-classroom",
              "panels": "double_vertical",
              "sill_height_mm": 900,
              "template_id": "window-double-vertical",
              "width_mm": 1800
            },
            {
              "center_global_mm": [
                100,
                2400
              ],
              "height_mm": 1800,
              "host_wall": "storey-3-wall-west",
              "id": "storey-3-window-west",
              "panels": "single",
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
      "actual": {
        "x": [
          4.6000000000000005,
          4.8
        ],
        "y": [
          5.2,
          12.600000000000001
        ],
        "z": [
          0.0,
          3.0
        ]
      },
      "code": "WALL_SEGMENT_MISMATCH",
      "entity_ids": [
        "wall-storey-1-storey-1-wall-notch-west"
      ],
      "expected": {
        "x": [
          4.6,
          4.8
        ],
        "y": [
          4.7,
          12.1
        ],
        "z": [
          0.0,
          3.0
        ]
      },
      "message": "Wall 'wall-storey-1-storey-1-wall-notch-west' world bounding box is outside tolerance.",
      "path": "/walls/storey-1-wall-notch-west",
      "source_fact_refs": [
        "/known_facts/walls/3"
      ]
    },
    {
      "actual": {
        "x": [
          4.6000000000000005,
          4.8
        ],
        "y": [
          5.2,
          12.600000000000001
        ],
        "z": [
          3.15,
          6.15
        ]
      },
      "code": "WALL_SEGMENT_MISMATCH",
      "entity_ids": [
        "wall-storey-2-storey-2-wall-notch-west"
      ],
      "expected": {
        "x": [
          4.6,
          4.8
        ],
        "y": [
          4.7,
          12.1
        ],
        "z": [
          3.15,
          6.15
        ]
      },
      "message": "Wall 'wall-storey-2-storey-2-wall-notch-west' world bounding box is outside tolerance.",
      "path": "/walls/storey-2-wall-notch-west",
      "source_fact_refs": [
        "/known_facts/walls/13"
      ]
    },
    {
      "actual": {
        "x": [
          4.6000000000000005,
          4.8
        ],
        "y": [
          5.2,
          12.600000000000001
        ],
        "z": [
          6.3,
          9.3
        ]
      },
      "code": "WALL_SEGMENT_MISMATCH",
      "entity_ids": [
        "wall-storey-3-storey-3-wall-notch-west"
      ],
      "expected": {
        "x": [
          4.6,
          4.8
        ],
        "y": [
          4.7,
          12.1
        ],
        "z": [
          6.3,
          9.3
        ]
      },
      "message": "Wall 'wall-storey-3-storey-3-wall-notch-west' world bounding box is outside tolerance.",
      "path": "/walls/storey-3-wall-notch-west",
      "source_fact_refs": [
        "/known_facts/walls/23"
      ]
    },
    {
      "code": "ROOM_ENCLOSURE_OPEN",
      "message": "Expected wall geometry does not form the required room enclosure.",
      "path": "/walls"
    },
    {
      "actual": {
        "reason": "floor_slab_geometry_missing"
      },
      "code": "GEOMETRY_EXPECTATION_INCOMPLETE",
      "message": "Required geometry could not be derived from confirmed facts.",
      "path": "/known_facts/floor_slabs/0",
      "source_fact_refs": []
    },
    {
      "actual": {
        "reason": "floor_slab_geometry_missing"
      },
      "code": "GEOMETRY_EXPECTATION_INCOMPLETE",
      "message": "Required geometry could not be derived from confirmed facts.",
      "path": "/known_facts/floor_slabs/1",
      "source_fact_refs": []
    },
    {
      "actual": {
        "reason": "floor_slab_geometry_missing"
      },
      "code": "GEOMETRY_EXPECTATION_INCOMPLETE",
      "message": "Required geometry could not be derived from confirmed facts.",
      "path": "/known_facts/floor_slabs/2",
      "source_fact_refs": []
    }
  ],
  "metrics": {
    "case_id": "9b00e53444a948e7",
    "expectation_complete": false,
    "floor_openings": {},
    "products": {},
    "roof": {},
    "slabs": {},
    "spaces": {
      "space-storey-1-storey-1-space-circulation": {
        "bbox": {
          "x": [
            0.2,
            4.6000000000000005
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
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-north-classroom": {
        "bbox": {
          "x": [
            4.8,
            13.0
          ],
          "y": [
            12.200000000000001,
            16.6
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-south-classroom": {
        "bbox": {
          "x": [
            4.8,
            13.0
          ],
          "y": [
            0.2,
            4.6000000000000005
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-circulation": {
        "bbox": {
          "x": [
            0.2,
            4.6000000000000005
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
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-north-classroom": {
        "bbox": {
          "x": [
            4.8,
            13.0
          ],
          "y": [
            12.200000000000001,
            16.6
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-south-classroom": {
        "bbox": {
          "x": [
            4.8,
            13.0
          ],
          "y": [
            0.2,
            4.6000000000000005
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-storey-3-space-circulation": {
        "bbox": {
          "x": [
            0.2,
            4.6000000000000005
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
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-storey-3-space-north-classroom": {
        "bbox": {
          "x": [
            4.8,
            13.0
          ],
          "y": [
            12.200000000000001,
            16.6
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-storey-3-space-south-classroom": {
        "bbox": {
          "x": [
            4.8,
            13.0
          ],
          "y": [
            0.2,
            4.6000000000000005
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
          "stair-flight-flight-1"
        ],
        "has_stepped_profile": true,
        "wall_intersections": []
      },
      "stair-flight-2": {
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
          "stair-flight-flight-2"
        ],
        "has_stepped_profile": true,
        "wall_intersections": []
      }
    },
    "unresolved_expectation_count": 3,
    "wall_set_convention": "primary",
    "walls": {
      "wall-storey-1-storey-1-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.10000000000000053,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-northwing-east": {
        "axis": "y",
        "bbox": {
          "x": [
            13.0,
            13.2
          ],
          "y": [
            12.1,
            16.7
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-notch-north": {
        "axis": "x",
        "bbox": {
          "x": [
            4.7,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-notch-south": {
        "axis": "x",
        "bbox": {
          "x": [
            4.7,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-notch-west": {
        "axis": "y",
        "bbox": {
          "x": [
            4.6000000000000005,
            4.8
          ],
          "y": [
            5.2,
            12.600000000000001
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-north": {
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-south": {
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.10000000000000053,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-southwing-east": {
        "axis": "y",
        "bbox": {
          "x": [
            13.0,
            13.2
          ],
          "y": [
            0.09999999999999964,
            4.7
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
            0.0,
            0.2
          ],
          "y": [
            0.09999999999999964,
            16.700000000000003
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.10000000000000053,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-northwing-east": {
        "axis": "y",
        "bbox": {
          "x": [
            13.0,
            13.2
          ],
          "y": [
            12.1,
            16.7
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-notch-north": {
        "axis": "x",
        "bbox": {
          "x": [
            4.7,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-notch-south": {
        "axis": "x",
        "bbox": {
          "x": [
            4.7,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-notch-west": {
        "axis": "y",
        "bbox": {
          "x": [
            4.6000000000000005,
            4.8
          ],
          "y": [
            5.2,
            12.600000000000001
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-north": {
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-south": {
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.10000000000000053,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-southwing-east": {
        "axis": "y",
        "bbox": {
          "x": [
            13.0,
            13.2
          ],
          "y": [
            0.09999999999999964,
            4.7
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
            0.0,
            0.2
          ],
          "y": [
            0.09999999999999964,
            16.700000000000003
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.10000000000000053,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-northwing-east": {
        "axis": "y",
        "bbox": {
          "x": [
            13.0,
            13.2
          ],
          "y": [
            12.1,
            16.7
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-notch-north": {
        "axis": "x",
        "bbox": {
          "x": [
            4.7,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-notch-south": {
        "axis": "x",
        "bbox": {
          "x": [
            4.7,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-notch-west": {
        "axis": "y",
        "bbox": {
          "x": [
            4.6000000000000005,
            4.8
          ],
          "y": [
            5.2,
            12.600000000000001
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-partition-north": {
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-partition-south": {
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.10000000000000053,
            13.100000000000001
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
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-southwing-east": {
        "axis": "y",
        "bbox": {
          "x": [
            13.0,
            13.2
          ],
          "y": [
            0.09999999999999964,
            4.7
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
            0.0,
            0.2
          ],
          "y": [
            0.09999999999999964,
            16.700000000000003
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
  "success": false
}
```

Source: [geometry-feedback.json](geometry-feedback.json)

## Metrics

### Design Brief Agent

```json
{
  "case_id": "9b00e53444a948e7",
  "design_status": "ready",
  "evidence_class": "live",
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "parse_valid": true,
  "question_count": 0,
  "response_id": "49ac8c08-6883-44dd-b121-cd274fcac2f2",
  "schema_semantic_valid": true,
  "stage": "design-brief",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 40578,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 30077,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 2432,
    "prompt_cache_miss_tokens": 16345,
    "prompt_tokens": 18777,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 2432
    },
    "total_tokens": 59355
  }
}
```

Source: [design-brief/metrics.json](design-brief/metrics.json)

### BIM JSON Generator

```json
{
  "case_id": "9b00e53444a948e7",
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
  "response_id": "92582d84-d330-4419-8e51-a8c9da5f0fea",
  "stage": "generate",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 48731,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 26052,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 42876,
    "prompt_tokens": 42876,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    },
    "total_tokens": 91607
  }
}
```

Source: [generator/metrics.json](generator/metrics.json)

### Repair Route

```json
{
  "case_id": "9b00e53444a948e7",
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
  "source_generator_response_id": "92582d84-d330-4419-8e51-a8c9da5f0fea",
  "stage": "repair",
  "valid": true
}
```

Source: [repair/metrics.json](repair/metrics.json)

### Audit Agent

```json
{
  "case_id": "9b00e53444a948e7",
  "design_review_context_sha256": null,
  "evidence_class": "live",
  "issue_count": 0,
  "model": "deepseek-flash",
  "normalization_diagnostics": [],
  "response_id": "da4e8bd9-d19f-46fa-80a3-66fbd5e9add9",
  "route_decision": "generator_regeneration_required",
  "route_owner_stage": "generator",
  "schema_semantic_valid": true,
  "stage": "audit",
  "stop_reason": "stop",
  "strict_output_contract_valid": true,
  "usage": {
    "completion_tokens": 3187,
    "completion_tokens_details": {
      "accepted_prediction_tokens": null,
      "audio_tokens": null,
      "reasoning_tokens": 1137,
      "rejected_prediction_tokens": null
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 62131,
    "prompt_tokens": 62131,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    },
    "total_tokens": 65318
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
