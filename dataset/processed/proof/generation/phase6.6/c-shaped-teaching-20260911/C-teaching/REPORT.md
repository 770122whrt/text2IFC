# 三层 C 型教学活动楼

**人工已验收，2026-09-11。** [完整IFC](generated.ifc) · [原始中文请求](request.txt) · [真实澄清](CLARIFICATIONS.md) · [完整对话](conversation.json) · [正式BIM JSON](model.json)。

本次从原始请求和已批准入口澄清开始真实生成，没有复用旧Brief、候选或IFC作为输入，也没有手工修改IFC。`legacy_full`；代码d0c39dc4；请求模型deepseek-v4-flash，响应字段deepseek-flash。

| 阶段 | Input | Output（含推理） | 其中推理 | 总token |
|---|---:|---:|---:|---:|
| Brief | 19715 | 46754 | 35821 | 66469 |
| Generator | 43246 | 39777 | 17184 | 83023 |
| Audit | 62316 | 8912 | 7334 | 71228 |
| 本轮 | 125277 | 95443 | 60339 | 220720 |

[独立IFC检查](independent-ifc-check.json)485项通过；C历史账本累计20次、1,597,750 token，包含失败尝试。新增token与历史累计不能相加重复统计；独立Audit去重实验使用另一份账本。

[整体图片](views/overall.png) · [首层](views/ground-floor.png) · [窗](views/IfcWindow.png) · [门](views/IfcDoor.png) · [原有旋转视图](views/viewer.html)。原生网格64个有表示实体、失败0；图片直接来自IFC，未生成额外概念图或网页。

模型按请求表达C型、墙角、洞口、宿主、材料和部件颜色。原Audit“每层9空间”的口误以独立IFC结果更正为每层3个、全楼9个；真实响应保留原样。

[机器证据入口](evidence/README.md)。本案例证明一次已见场景的真实运行与人工验收通过，不是完整工程合规认证或盲测能力提升。
