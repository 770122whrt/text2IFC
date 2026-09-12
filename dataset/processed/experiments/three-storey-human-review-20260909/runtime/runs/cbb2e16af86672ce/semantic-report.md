# 请求与 IFC 语义核对

本报告独立重开 IFC 读取有效值。性能属性为用户设计要求或声明，不代表实测或认证。

| 构件 / 作用域 | 请求项 | 请求值 | IFC 读回值 | 结果 |
|---|---|---|---|---|
| wall-storey-1-storey-1-wall-south / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-north / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-west / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-east / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-partition / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-south / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-north / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-west / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-east / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-partition / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-south / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-north / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-west / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-east / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-partition / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| floor-slab-ground / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| floor-slab-2 / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| floor-slab-3 / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| roof-slab / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| door-storey-1-storey-1-door-partition / effective | template | {"template_id": "door-right", "template_version": "text2ifc/basic-filling/1.0"} | {"ParameterSourcesJson": "{\"frame_depth\": \"text2ifc/basic-filling/1.0:door-right\", \"frame_width\": \"text2ifc/basic-filling/1.0:door-right\", \"panel_thickness\": \"text2ifc/basic-filling/1.0:door-right\"}", "ParametersJson": "{\"frame_depth\": 60.0, \"frame_width\": 50.0, \"panel_thickness\": 40.0}", "TemplateId": "door-right", "TemplateVersion": "text2ifc/basic-filling/1.0", "id": 1341} | 通过 |
| door-storey-2-storey-2-door-partition / effective | template | {"template_id": "door-right", "template_version": "text2ifc/basic-filling/1.0"} | {"ParameterSourcesJson": "{\"frame_depth\": \"text2ifc/basic-filling/1.0:door-right\", \"frame_width\": \"text2ifc/basic-filling/1.0:door-right\", \"panel_thickness\": \"text2ifc/basic-filling/1.0:door-right\"}", "ParametersJson": "{\"frame_depth\": 60.0, \"frame_width\": 50.0, \"panel_thickness\": 40.0}", "TemplateId": "door-right", "TemplateVersion": "text2ifc/basic-filling/1.0", "id": 1383} | 通过 |
| door-storey-3-storey-3-door-partition / effective | template | {"template_id": "door-right", "template_version": "text2ifc/basic-filling/1.0"} | {"ParameterSourcesJson": "{\"frame_depth\": \"text2ifc/basic-filling/1.0:door-right\", \"frame_width\": \"text2ifc/basic-filling/1.0:door-right\", \"panel_thickness\": \"text2ifc/basic-filling/1.0:door-right\"}", "ParametersJson": "{\"frame_depth\": 60.0, \"frame_width\": 50.0, \"panel_thickness\": 40.0}", "TemplateId": "door-right", "TemplateVersion": "text2ifc/basic-filling/1.0", "id": 1425} | 通过 |
| wall-storey-1-storey-1-wall-south / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-north / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-west / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-east / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-1-storey-1-wall-partition / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-south / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-north / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-west / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-east / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-2-storey-2-wall-partition / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-south / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-north / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-west / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-east / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| wall-storey-3-storey-3-wall-partition / direct | material | {"kind": "single_material", "name": "brick"} | {"kind": "single_material", "name": "brick"} | 通过 |
| floor-slab-ground / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| floor-slab-2 / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| floor-slab-3 / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| roof-slab / direct | material | {"kind": "single_material", "name": "concrete"} | {"kind": "single_material", "name": "concrete"} | 通过 |
| door-storey-1-storey-1-door-partition / effective | template | {"template_id": "door-right", "template_version": "text2ifc/basic-filling/1.0"} | {"ParameterSourcesJson": "{\"frame_depth\": \"text2ifc/basic-filling/1.0:door-right\", \"frame_width\": \"text2ifc/basic-filling/1.0:door-right\", \"panel_thickness\": \"text2ifc/basic-filling/1.0:door-right\"}", "ParametersJson": "{\"frame_depth\": 60.0, \"frame_width\": 50.0, \"panel_thickness\": 40.0}", "TemplateId": "door-right", "TemplateVersion": "text2ifc/basic-filling/1.0", "id": 1341} | 通过 |
| door-storey-2-storey-2-door-partition / effective | template | {"template_id": "door-right", "template_version": "text2ifc/basic-filling/1.0"} | {"ParameterSourcesJson": "{\"frame_depth\": \"text2ifc/basic-filling/1.0:door-right\", \"frame_width\": \"text2ifc/basic-filling/1.0:door-right\", \"panel_thickness\": \"text2ifc/basic-filling/1.0:door-right\"}", "ParametersJson": "{\"frame_depth\": 60.0, \"frame_width\": 50.0, \"panel_thickness\": 40.0}", "TemplateId": "door-right", "TemplateVersion": "text2ifc/basic-filling/1.0", "id": 1383} | 通过 |
| door-storey-3-storey-3-door-partition / effective | template | {"template_id": "door-right", "template_version": "text2ifc/basic-filling/1.0"} | {"ParameterSourcesJson": "{\"frame_depth\": \"text2ifc/basic-filling/1.0:door-right\", \"frame_width\": \"text2ifc/basic-filling/1.0:door-right\", \"panel_thickness\": \"text2ifc/basic-filling/1.0:door-right\"}", "ParametersJson": "{\"frame_depth\": 60.0, \"frame_width\": 50.0, \"panel_thickness\": 40.0}", "TemplateId": "door-right", "TemplateVersion": "text2ifc/basic-filling/1.0", "id": 1425} | 通过 |

人工主题/代表性 Proof 视觉审查：待审；普通运行的自动交付状态与人工审查分别记录。
