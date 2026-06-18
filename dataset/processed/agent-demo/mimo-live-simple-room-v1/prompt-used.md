# Mimo BIM JSON Prompt v1

你是 text2IFC 的中文优先 BIM JSON 生成 Agent。你的任务是把用户的自然语言建筑描述转换为 BIM JSON 2.0。BIM JSON 2.0 是自然语言和 IFC2X3 编译器之间的语义层合同，不是原始 IFC STEP 文件。

## 输出合同

只输出一个完整 JSON 对象。不要输出解释、分析过程、Markdown、代码块、前后缀文本或多余注释。

根对象必须包含这些字段：

- `schema_version`: 固定为 `"bim-json/2.0"`
- `ifc_schema`: 固定为 `"IFC2X3"`
- `units`: 至少包含 `{ "length": "MILLIMETRE" }`
- `entities`: 用户有意义的 IFC 实体数组
- `relationships`: 用户显式表达或 BIM JSON 语义层需要表达的关系数组
- `provenance`: 来源记录

每个 `entities` 条目必须包含：

- `id`
- `ifc_class`
- `attributes`
- `property_sets`
- `provenance`

每个 `relationships` 条目必须包含：

- `id`
- `ifc_class`
- `attributes`
- `provenance`

## 语义边界

可以输出 `IfcProject`、`IfcSite`、`IfcBuilding`、`IfcBuildingStorey`、`IfcSpace`、`IfcWall`、`IfcWallStandardCase`、`IfcDoor`、`IfcWindow`、`IfcOpeningElement`、`IfcRelVoidsElement`、`IfcRelFillsElement` 等 BIM JSON 语义层对象。

不要输出 IFC STEP 文本。不要输出 IFC 文件内容。不要输出编译器自动生成的低层对象，例如 `IfcCartesianPoint`、`IfcDirection`、`IfcOwnerHistory`、STEP ID、`IfcLocalPlacement` 的底层资源对象或几何表示资源对象。位置、几何和关系只放在 BIM JSON 的语义字段中。

## 几何和位置

长度单位使用毫米。用户给出米时必须换算为毫米，例如 6m 写成 `6000`。

有空间时，优先生成 `IfcSpace`，并用 `Representation` 表达空间平面轮廓和高度。构件需要 `ObjectPlacement` 时，使用父级相对语义位置：

```json
{
  "relative_to": "storey-1",
  "origin": [0, 0, 0],
  "axis": [0, 0, 1],
  "ref_direction": [1, 0, 0]
}
```

矩形构件优先使用：

```json
{
  "kind": "extruded_profile",
  "profile": { "kind": "rectangle", "x": 6000, "y": 200 },
  "depth": 3000,
  "direction": [0, 0, 1]
}
```

门窗洞口需要语义关系：

- `IfcRelVoidsElement`: 墙体和洞口
- `IfcRelFillsElement`: 洞口和门窗

## 缺失信息

不要静默编造必要尺寸、楼层、空间、构件位置、洞口位置、门窗尺寸或属性。

如果用户请求缺少完成 Formal BIM JSON 必需的信息，并且 `VALIDATION_FEEDBACK` 也不能补足，请输出 Draft Envelope，而不是 Formal BIM JSON。Draft 必须列出 `missing_facts` 和 `clarification_targets`。如果用户信息足够，请输出 Formal BIM JSON。

## 参考和修复规则

`REFERENCE_JSON` 是合法结构参考，不是必须逐字复制的结果。你可以复用它的字段形状、实体组织、ID 风格、关系写法和单位写法。用户描述优先于参考 JSON。

`VALIDATION_FEEDBACK` 是上一轮校验失败原因。生成结果时必须修复这些问题，尤其是不要把普通尺寸 JSON 或片段 JSON 当成最终输出。

## 输入

USER_REQUEST:

????????????????6???4???3??????????200??????????900????2100??????????????????1200????1500?????????900???

REFERENCE_JSON:

{
  "entities": [
    {
      "attributes": {
        "Name": "Text2IFC Demo Project"
      },
      "id": "project-1",
      "ifc_class": "IfcProject",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "Site",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "project-1"
        }
      },
      "id": "site-1",
      "ifc_class": "IfcSite",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "Building",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "site-1"
        }
      },
      "id": "building-1",
      "ifc_class": "IfcBuilding",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Elevation": 0,
        "Name": "Level 1",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "building-1"
        }
      },
      "id": "storey-1",
      "ifc_class": "IfcBuildingStorey",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "InteriorOrExteriorSpace": "INTERNAL",
        "Name": "Room",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "storey-1"
        },
        "Representation": {
          "depth": 3000,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "polygon",
            "points": [
              [
                0,
                0
              ],
              [
                6000,
                0
              ],
              [
                6000,
                4000
              ],
              [
                0,
                4000
              ],
              [
                0,
                0
              ]
            ]
          }
        }
      },
      "id": "space-1",
      "ifc_class": "IfcSpace",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "wall-south",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "storey-1"
        },
        "Representation": {
          "depth": 3000,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 6000,
            "y": 200
          }
        }
      },
      "id": "wall-south",
      "ifc_class": "IfcWall",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "wall-north",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            4000,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "storey-1"
        },
        "Representation": {
          "depth": 3000,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 6000,
            "y": 200
          }
        }
      },
      "id": "wall-north",
      "ifc_class": "IfcWall",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "wall-west",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "storey-1"
        },
        "Representation": {
          "depth": 3000,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 4000,
            "y": 200
          }
        }
      },
      "id": "wall-west",
      "ifc_class": "IfcWall",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "wall-east",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            6000,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "storey-1"
        },
        "Representation": {
          "depth": 3000,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 4000,
            "y": 200
          }
        }
      },
      "id": "wall-east",
      "ifc_class": "IfcWall",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "opening-door-1",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            2550,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "wall-south"
        },
        "Representation": {
          "depth": 2100,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 900,
            "y": 200
          }
        }
      },
      "id": "opening-door-1",
      "ifc_class": "IfcOpeningElement",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "Door",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "opening-door-1"
        },
        "OverallHeight": 2100,
        "OverallWidth": 900,
        "Representation": {
          "depth": 2100,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 900,
            "y": 100
          }
        }
      },
      "id": "door-1",
      "ifc_class": "IfcDoor",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "opening-window-1",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            2400,
            0,
            900
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "wall-north"
        },
        "Representation": {
          "depth": 1500,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 1200,
            "y": 200
          }
        }
      },
      "id": "opening-window-1",
      "ifc_class": "IfcOpeningElement",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "Name": "Window",
        "ObjectPlacement": {
          "axis": [
            0,
            0,
            1
          ],
          "origin": [
            0,
            0,
            0
          ],
          "ref_direction": [
            1,
            0,
            0
          ],
          "relative_to": "opening-window-1"
        },
        "OverallHeight": 1500,
        "OverallWidth": 1200,
        "Representation": {
          "depth": 1500,
          "direction": [
            0,
            0,
            1
          ],
          "kind": "extruded_profile",
          "profile": {
            "kind": "rectangle",
            "x": 1200,
            "y": 100
          }
        }
      },
      "id": "window-1",
      "ifc_class": "IfcWindow",
      "property_sets": {},
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    }
  ],
  "ifc_schema": "IFC2X3",
  "provenance": {
    "source": "phase-5-scripted-demo"
  },
  "relationships": [
    {
      "attributes": {
        "RelatedOpeningElement": "opening-door-1",
        "RelatingBuildingElement": "wall-south"
      },
      "id": "void-door-1",
      "ifc_class": "IfcRelVoidsElement",
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "RelatedBuildingElement": "door-1",
        "RelatingOpeningElement": "opening-door-1"
      },
      "id": "fill-door-1",
      "ifc_class": "IfcRelFillsElement",
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "RelatedOpeningElement": "opening-window-1",
        "RelatingBuildingElement": "wall-north"
      },
      "id": "void-window-1",
      "ifc_class": "IfcRelVoidsElement",
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    },
    {
      "attributes": {
        "RelatedBuildingElement": "window-1",
        "RelatingOpeningElement": "opening-window-1"
      },
      "id": "fill-window-1",
      "ifc_class": "IfcRelFillsElement",
      "provenance": {
        "source": "phase-5-scripted-demo"
      }
    }
  ],
  "schema_version": "bim-json/2.0",
  "units": {
    "length": "MILLIMETRE"
  }
}


VALIDATION_FEEDBACK:

{
  "content_types": [
    "text",
    "thinking"
  ],
  "entity_count": 0,
  "http_status": 200,
  "issues": [
    {
      "code": "REQUIRED_FIELD",
      "message": "Required field 'entities' is missing.",
      "path": "/entities"
    },
    {
      "code": "REQUIRED_FIELD",
      "message": "Required field 'ifc_schema' is missing.",
      "path": "/ifc_schema"
    },
    {
      "code": "UNSUPPORTED_FIELD",
      "message": "Field 'length' is not supported.",
      "path": "/length"
    },
    {
      "code": "REQUIRED_FIELD",
      "message": "Required field 'provenance' is missing.",
      "path": "/provenance"
    },
    {
      "code": "REQUIRED_FIELD",
      "message": "Required field 'relationships' is missing.",
      "path": "/relationships"
    },
    {
      "code": "REQUIRED_FIELD",
      "message": "Required field 'schema_version' is missing.",
      "path": "/schema_version"
    },
    {
      "code": "REQUIRED_FIELD",
      "message": "Required field 'units' is missing.",
      "path": "/units"
    }
  ],
  "model": "mimo-v2.5-pro",
  "provider": "mimo",
  "relationship_count": 0,
  "request_text": "?????????????6???4???3????????????????0.9??2.1????????????1.2??1.5?????0.9??",
  "response_bytes": 2674,
  "schema_version": "text2ifc/mimo-live-simple-room-v1",
  "stage": "validation",
  "stop_reason": "end_turn",
  "success": false,
  "validation_issue_count": 7
}


## 最终回答

只输出一个完整 JSON 对象。
