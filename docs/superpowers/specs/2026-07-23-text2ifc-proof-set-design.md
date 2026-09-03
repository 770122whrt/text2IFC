# Text2IFC 成功案例 Proof 集设计规范

**日期：** 2026-07-23  
**状态：** 待用户复核  
**适用项目：** text2IFC / bimnet

## 1. 目标

建立一个稳定、可复查、可持续扩展的 Text2IFC 成功案例证明集，集中保存：

1. 用户或测试集提供的原始中文自然语言输入；
2. 经过完整工作流生成并通过验收的 IFC2X3 文件；
3. 输入、输出与原始运行目录之间的来源关系；
4. Text -> BIM JSON -> IFC 的完整生成与审核流程说明。

Proof 集用于人工展示、回归核验和阶段成果交付。它不是训练集，也不替代原始运行目录、实验报告或机器可读评估结果。

## 2. 核心原则

- **复制而非移动：** Proof 集保存已验收成果的副本。原始 IFC、输入清单、运行报告和中间产物保留在原位置，避免历史链接和实验记录失效。
- **只收录成功结果：** 失败尝试、调试版本和未完成人工验收的文件继续保留在各自运行目录，不进入 Proof 集。
- **输入保持原文：** `.input.zh-CN.txt` 必须从对应 JSON 的 `input` 字段以 UTF-8 原样提取，不进行润色、纠错或静默补充。
- **IFC 不重新生成：** 首次整理直接复制已经验收的 IFC 文件，不通过再次运行模型制造新的证明结果。
- **来源可追溯：** 每个案例都必须记录原始输入路径、原始 IFC 路径、哈希、IFC Schema、实体统计和验收证据路径。
- **机密信息隔离：** Proof 文件、报告和来源记录不得包含令牌、认证头、私有 Provider URL 或 `.env` 内容。

## 3. 目录结构

Proof 根目录：

```text
dataset/processed/proof/text2ifc-success-cases/
├── README.md
├── manifest.json
├── TEXT2IFC-WORKFLOW.md
├── stable-01/
│   ├── easy/
│   │   ├── stable-01-easy.input.zh-CN.txt
│   │   ├── stable-01-easy.ifc
│   │   └── provenance.json
│   ├── medium/
│   │   ├── stable-01-medium.input.zh-CN.txt
│   │   ├── stable-01-medium.ifc
│   │   └── provenance.json
│   └── difficult/
│       ├── stable-01-difficult.input.zh-CN.txt
│       ├── stable-01-difficult.ifc
│       └── provenance.json
└── historical-accepted/
    ├── two-storey-final-712/
    │   ├── two-storey-final-712.input.zh-CN.txt
    │   ├── two-storey-final-712.ifc
    │   └── provenance.json
    ├── output-713-success/
    │   ├── output-713-success.input.zh-CN.txt
    │   ├── output-713-success.ifc
    │   └── provenance.json
    └── hard-three-storey-final/
        ├── hard-three-storey-final.input.zh-CN.txt
        ├── hard-three-storey-final.ifc
        └── provenance.json
```

后续成功的 Stable 02、Stable 03 采用相同结构：

```text
stable-02/easy/
stable-02/medium/
stable-02/difficult/
stable-03/easy/
stable-03/medium/
stable-03/difficult/
```

未成功的难度级别不创建空案例目录。

## 4. 首批六个案例的来源映射

### 4.1 Stable 01 Easy

- Proof ID：`stable-01-easy`
- 输入来源：`dataset/processed/agent-demo/phase6.5-wave8-observation/manifests/STD-E-RES-01.json`
- 输入字段：`input`
- IFC 来源：`dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/output.ifc`
- 已确认 IFC：IFC2X3，1 个楼层，1 个空间，4 面墙
- IFC SHA-256：`61de480662bc8bac18d49fe44bbafaa1da7b3a68a002ea286f4dbe700b9253eb`

### 4.2 Stable 01 Medium

- Proof ID：`stable-01-medium`
- 输入来源：`dataset/processed/agent-demo/phase6.5-wave8-observation/manifests/STD-M-OFF-03.json`
- 输入字段：`input`
- IFC 来源：`dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/stable1-medium-716.ifc`
- 已确认 IFC：IFC2X3，1 个楼层，4 个空间，11 面墙
- IFC SHA-256：`06b8b60b034657d78d2c1e8868f8e5d6e4f7fadfa9d123eebc4a3450b1b4b4b7`

### 4.3 Stable 01 Difficult

- Proof ID：`stable-01-difficult`
- 输入来源：`dataset/processed/agent-demo/phase6.5-wave8-observation/manifests/STD-D-MUL-04.json`
- 输入字段：`input`
- IFC 来源：`dataset/processed/agent-demo/phase6.6-difficult-stair-fix-live-64k-explicit-hosts/runs/ba2277d8363bce69/stable1-difficult-716.ifc`
- 已确认 IFC：IFC2X3，2 个楼层，11 个空间，23 面墙
- IFC SHA-256：`8209696eabb12c9b3f2f8daac6124d0f02bfe501913a0b7a769ca7c74892367e`
- 说明：这是完成楼梯穿墙修正后通过人工验收的最终版本。不得使用早期会话 `53df7ac99abf41e8` 中的同名 IFC。

### 4.4 Two Storey Final 712

- Proof ID：`two-storey-final-712`
- 输入来源：`dataset/processed/agent-demo/phase6.5-cases/two-storey-case.json`
- 输入字段：`input`
- IFC 来源：`dataset/processed/agent-demo/phase6.5-easy-accepted/two-storey-final-712.ifc`
- 已确认 IFC：IFC2X3，2 个楼层，4 个空间，8 面墙
- IFC SHA-256：`ffdb0e52506f7bb91ea3fb5c64435614dac852f420d53dfb9db66fe96f682685`

### 4.5 Output 713 Success

- Proof ID：`output-713-success`
- 输入来源：`dataset/processed/agent-demo/phase6.5-cases/medium-two-storey-l-shape.json`
- 输入字段：`input`
- IFC 来源：`dataset/processed/agent-demo/phase6.5-medium-100mm-gap-fix/output713 -success.ifc`
- 已确认 IFC：IFC2X3，2 个楼层，11 个空间，24 面墙
- IFC SHA-256：`237fd65d9e0eea62cc974cdbdab7984947ba9589cc27c516f11085be11de8fda`
- 说明：Proof 中统一使用不含空格的名称 `output-713-success`。

### 4.6 Hard Three Storey Final

- Proof ID：`hard-three-storey-final`
- 输入来源：`dataset/processed/agent-demo/phase6.5-cases/hard-three-storey-l-shape.json`
- 输入字段：`input`
- IFC 来源：`dataset/processed/agent-demo/phase6.5-hard-accepted/hard-three-storey-final.ifc`
- 已确认 IFC：IFC2X3，3 个楼层，18 个空间，48 面墙
- IFC SHA-256：`0404c9f45d61606aceae361d14dbf5c5c130edb3e0521c517808212ddf6959e0`

## 5. Provenance 记录

每个案例的 `provenance.json` 至少包含：

```json
{
  "proof_id": "stable-01-easy",
  "group": "stable-01",
  "difficulty": "easy",
  "language": "zh-CN",
  "input_source": "...",
  "input_field": "input",
  "ifc_source": "...",
  "proof_input": "...",
  "proof_ifc": "...",
  "input_sha256": "...",
  "ifc_sha256": "...",
  "ifc_bytes": 0,
  "ifc_schema": "IFC2X3",
  "entity_counts": {},
  "acceptance_evidence": [],
  "human_uat": {
    "status": "accepted",
    "note": "..."
  }
}
```

根目录 `manifest.json` 汇总全部案例，包含：

- `schema_version`
- `generated_at`
- `collection_id`
- `case_count`
- `cases`

`manifest.json` 的案例记录引用各自的 `provenance.json`，同时保留关键哈希和状态，方便脚本快速验证。

## 6. 后续 Stable 案例准入条件

后续 Stable 02、Stable 03 或更多批次只有同时满足以下条件，才能复制到 Proof 集：

1. 模型输出为 Formal BIM JSON 2.0，而不是 Draft；
2. 通过 JSON Schema、语义规则和案例 expected facts 检查；
3. Generator 的分阶段输出完整；
4. 确定性 Gate 通过，Audit 不得覆盖 Gate 的阻断结果；
5. 若发生修复，修复必须通过显式 ChangeSet 完成并保留记录；
6. 成功编译为 IFC2X3，并能由 IfcOpenShell 重新打开；
7. 通过编译后几何、空间关系、宿主关系和属性检查；
8. 适用时，事实保留率达到 `1.0`；
9. 机器可读报告、Provider 往返证据和审核结论完整；
10. 产物 Secret Scan 结果为 0；
11. 需要人工判断的视觉与空间关系已经完成人工 UAT。

准入失败的运行不得进入 Proof 集，也不得通过改名伪装为最终结果。

## 7. Text2IFC Workflow 文档范围

`TEXT2IFC-WORKFLOW.md` 应用通俗中文说明以下链路：

```text
自然语言输入
  -> Design Brief 与事实提取
  -> 缺失事实诊断
  -> 多轮澄清或 Draft
  -> Formal BIM JSON 2.0
  -> Schema / 语义 / Expected Facts 验证
  -> 分阶段 Generator
  -> 确定性 Gate
  -> 有界修复与 ChangeSet
  -> Audit
  -> IFC2X3 编译
  -> IFC 重开与编译后验证
  -> 报告、Secret Scan 与人工 UAT
  -> Proof 集准入
```

文档必须明确三类职责：

- **Agent：** 理解自然语言、生成语义事实、提出澄清问题和建议修复；
- **Schema/Gate/Compiler：** 掌握结构、约束和编译的最终确定权；
- **Audit：** 提供独立复核意见，但不能绕过确定性失败。

还必须明确：

- 模型不直接输出 STEP/IFC 文本；
- 模型不生成 `IfcCartesianPoint`、`IfcDirection`、`IfcOwnerHistory` 等编译器级对象；
- 系统不静默补尺寸、楼层、空间、洞口、宿主关系或位置；
- 缺少必要事实时保留 Draft，并通过每轮 1-3 个中文问题继续澄清；
- IFC 只在 Formal BIM JSON 2.0 验证通过后生成。

## 8. 验证要求

Proof 集实现后至少执行：

1. 六个输入文件与来源 JSON `input` 字段逐字一致；
2. 六个 IFC 文件与来源 IFC 的 SHA-256 一致；
3. 六个 IFC 均能由 IfcOpenShell 打开，Schema 为 IFC2X3；
4. `manifest.json` 与全部 `provenance.json` 可被 JSON 解析；
5. 清单中的路径全部存在；
6. 清单中的文件大小、哈希和实体统计与实际文件一致；
7. Proof 根目录执行 Secret Scan，结果为 0；
8. README 能从案例名称定位到输入、IFC 和来源记录。

## 9. 非目标

本次整理不包括：

- 重新调用真实模型；
- 重新生成或修改六个已经验收的 IFC；
- 把失败运行包装成成功案例；
- 删除、移动或重命名原始运行产物；
- 把 Proof 集直接作为微调训练集；
- 为了统一外观而改写用户原始自然语言输入。

## 10. 完成定义

当以下条件全部满足时，方案 A 的首次整理完成：

- 六个已验收案例全部进入约定目录；
- 每个案例同时具有原始中文输入、IFC 和 provenance；
- 根清单与 README 完整；
- `TEXT2IFC-WORKFLOW.md` 能清楚说明从输入到 Proof 准入的全过程；
- 自动验证全部通过；
- 后续 Stable 成功案例具有明确、可复用的收录规则。
