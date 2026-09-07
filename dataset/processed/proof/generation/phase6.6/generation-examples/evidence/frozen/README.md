# Text2IFC 成功案例 Proof 集

这里集中保存已经通过机器检查和人工验收的 Text2IFC 案例。每个案例包含：

- 一份 UTF-8 中文原始输入；
- 一份可由 IfcOpenShell 打开的 IFC2X3 文件；
- 一份记录来源、哈希、实体数量和验收证据的 `provenance.json`。

Proof 集使用副本，不移动或删除原始运行产物。实验详情仍以 provenance 指向的原始目录为准。

## 首批案例

| 案例 | 难度 | 楼层 | 空间 | 墙 | IFC |
| --- | --- | ---: | ---: | ---: | --- |
| Stable 01 Easy | easy | 1 | 1 | 4 | [stable-01-easy.ifc](stable-01/easy/stable-01-easy.ifc) |
| Stable 01 Medium | medium | 1 | 4 | 11 | [stable-01-medium.ifc](stable-01/medium/stable-01-medium.ifc) |
| Stable 01 Difficult | difficult | 2 | 11 | 23 | [stable-01-difficult.ifc](stable-01/difficult/stable-01-difficult.ifc) |
| Two Storey Final 712 | historical | 2 | 4 | 8 | [two-storey-final-712.ifc](historical-accepted/two-storey-final-712/two-storey-final-712.ifc) |
| Output 713 Success | historical | 2 | 11 | 24 | [output-713-success.ifc](historical-accepted/output-713-success/output-713-success.ifc) |
| Hard Three Storey Final | historical | 3 | 18 | 48 | [hard-three-storey-final.ifc](historical-accepted/hard-three-storey-final/hard-three-storey-final.ifc) |

输入文本与来源记录位于每个 IFC 的同级目录。机器可读总索引见 [manifest.json](manifest.json)。

## 生成链路

[TEXT2IFC-WORKFLOW.md](TEXT2IFC-WORKFLOW.md) 说明自然语言如何经过多 Agent、确定性代码检查和 IFC 编译成为最终文件，并明确哪些步骤调用 LLM 接口，哪些步骤由普通代码完成。

## 后续 Stable 批次

后续 Stable 02、Stable 03 使用 `stable-02/<difficulty>/`、`stable-03/<difficulty>/` 结构。只有同时满足以下条件的最终产物才可进入 Proof：

1. Formal BIM JSON 2.0 通过 Schema 与语义验证；
2. Generator、Gate、Audit、修复和 Provider 证据完整；
3. IFC2X3 编译、重开、几何和关系检查通过；
4. Secret Scan 为 0；
5. 需要人工判断的视觉结果完成人工 UAT。

失败、Draft、被 Gate 阻断或尚未人工确认的结果继续留在原始运行目录，不在 Proof 中创建占位案例。
