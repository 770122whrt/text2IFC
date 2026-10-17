# 请求与 IFC 语义核对

本报告独立重开 IFC 读取有效值。性能属性为用户设计要求或声明，不代表实测或认证。

| 构件 / 作用域 | 请求项 | 请求值 | IFC 读回值 | 结果 |
|---|---|---|---|---|
| wall-south / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| wall-north / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| wall-west / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| wall-east / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| slab-ground / direct | material | {"kind": "single_material", "name": "混凝土"} | null | 未满足 |
| door-south / direct | template | {"parameters": {}, "template_id": "door-left", "template_version": "text2ifc/basic-filling/1.0"} | null | 未满足 |
| window-east / direct | template | {"parameters": {}, "template_id": "window-double-vertical", "template_version": "text2ifc/basic-filling/1.0"} | null | 未满足 |
| window-west / direct | template | {"parameters": {}, "template_id": "window-single", "template_version": "text2ifc/basic-filling/1.0"} | null | 未满足 |
| wall-south / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| wall-north / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| wall-west / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| wall-east / direct | material | {"kind": "single_material", "name": "砖"} | null | 未满足 |
| slab-ground / direct | material | {"kind": "single_material", "name": "混凝土"} | null | 未满足 |
| door-south / direct | template | {"parameters": {}, "template_id": "door-left", "template_version": "text2ifc/basic-filling/1.0"} | null | 未满足 |
| window-east / direct | template | {"parameters": {}, "template_id": "window-double-vertical", "template_version": "text2ifc/basic-filling/1.0"} | null | 未满足 |
| window-west / direct | template | {"parameters": {}, "template_id": "window-single", "template_version": "text2ifc/basic-filling/1.0"} | null | 未满足 |

阻断详情：

- {"code": "UNREQUESTED_MATERIAL", "message": "配色或模板不能补写未经请求授权的材料。", "path": "/entities/wall-storey-1-wall-south/materials"}
- {"code": "UNREQUESTED_MATERIAL", "message": "配色或模板不能补写未经请求授权的材料。", "path": "/entities/wall-storey-1-wall-north/materials"}
- {"code": "UNREQUESTED_MATERIAL", "message": "配色或模板不能补写未经请求授权的材料。", "path": "/entities/wall-storey-1-wall-west/materials"}
- {"code": "UNREQUESTED_MATERIAL", "message": "配色或模板不能补写未经请求授权的材料。", "path": "/entities/wall-storey-1-wall-east/materials"}

人工主题/代表性 Proof 视觉审查：待审；普通运行的自动交付状态与人工审查分别记录。
