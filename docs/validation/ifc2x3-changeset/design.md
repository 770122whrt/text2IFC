# Text2IFC IFC2X3 局部 ChangeSet 评估设计

> 状态：离线确定性闭环与一次真实 DeepSeek UAT 均已通过
> 最后更新：2026-07-18
> 第一操作：在直线墙上创建窗洞与窗户
> 设计原则：Window 只是第一个 operation，架构必须支持后续墙洞、门、梁、柱及其他局部修改。

## 1. 文档权威与防漂移规则

本文档是 IFC2X3 局部修改评估的设计权威。实现计划、Schema、Prompt、测试和
实验报告不得静默改变本文档已经确认的边界。

防漂移规则：

1. 每次改变 operation 语义、输入可见性、坐标合同、验收指标或样例，先更新本文档的决策日志。
2. 同目录的 `implementation-prompt.md` 是实施指令，不得覆盖本文档的设计决定。
3. Window 专用字段只能出现在 Window operation 参数中，不能进入公共 ChangeSet envelope。
4. 新构件类型必须通过 operation registry 接入，不得复制整套 Context、Audit、Applicator 和 Comparator。
5. 小型 smoke case 与 BIMNet 适配必须分轨报告，不能用小样例成功替代 BIMNet 兼容性结论。
6. 确定性测试与真实 Provider UAT 必须分别标注，不能互相冒充。

## 2. 已确认的核心决定

### 2.1 总体路线

采用混合式局部修改路线：

```text
damaged.ifc（模型权威）
    │
    ├── Compact Repair Context JSON ──┐
    │                                  │
repair_request.txt ────────────────────┼──> LLM Semantic ChangeSet
                                       │
                                       └──> deterministic Audit
                                                  │
                                                  ▼
                                       operation-specific Applicator
                                                  │
                                                  ▼
                                             repaired.ifc
                                                  │
                                                  ▼
                                     common + operation-specific Compare
```

`damaged.ifc` 始终是模型权威。JSON 用于向 LLM 提供紧凑上下文并表达修改，
不承担整个既有 IFC 的无损重建。

### 2.2 为什么不整模 IFC → BIM JSON → IFC

当前 BIM JSON 2.0 不能无损表达和重新生成任意真实 IFC 中的复杂几何、类型、
材质、连接、样式和其他长尾信息。整模重编译会扩大非目标变化，也会把第一案
变成通用 IFC round-trip 项目。

因此本阶段复用当前 BIM JSON ChangeSet 的治理思想，而不是直接复用它的完整
Candidate 和 Applicator 假设。

### 2.3 验收路线

采用双轨验收：

1. fake/deterministic Provider 驱动的离线闭环进入自动测试；
2. 至少一次真实 Provider 运行作为 UAT 证据。

### 2.4 几何范围

第一阶段只支持直线墙。BIMNet 25 个 IFC2X3 中已经确认存在至少 6 面显式圆弧
Axis 墙，分布于 `px4_2.ifc`、`759.ifc` 和 `vt2_1.ifc`。圆弧墙和可能的
网格近似曲墙进入后续阶段。

第一阶段遇到圆弧、折线、曲线或无法确定的墙体几何时必须返回：

```text
UNSUPPORTED_WALL_GEOMETRY
```

不得自动拉直或近似。

## 3. 阶段目标与非目标

### 3.1 目标

建立一个可扩展的 IFC2X3 局部修改评估闭环：

```text
选择原始 IFC
→ 受控删除目标组件
→ 生成无私有泄漏的修改文本
→ 构建紧凑 IFC 上下文
→ LLM 输出 Semantic ChangeSet
→ Audit
→ Apply
→ Compare
```

首个 operation 证明系统能根据文本，在既有直线墙指定位置创建窗洞和窗户，
同时保持非目标模型不变。

### 3.2 非目标

第一阶段不包括：

- 整模 IFC 无损 JSON round-trip；
- 曲面墙、圆弧墙或折线墙上的开洞；
- 批量修改多个 IFC；
- 门、梁、柱等 operation 的具体实现；
- 任意 IFC4/IFC4X3 写入；
- STEP ID 或 IFC 文件字节级一致；
- 用 LLM 生成 STEP、底层 placement 或几何拓扑对象。

## 4. 样例分层策略

### 4.1 Tier 0：中小型真实外部 smoke case

第一闭环使用：

```text
dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc
```

冻结信息：

| 字段 | 值 |
|---|---|
| Schema | IFC2X3 |
| 文件大小 | 1,292,595 bytes |
| SHA-256 | `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725` |
| Source revision | `595fa90e3af7120d004fcb37a79d8657f1d1c9c2` |
| License | MIT；证据为 submodule 内 `LICENSE` |
| Project / Site / Building | 1 / 1 / 1 |
| Storey | 2 |
| Space | 8 |
| Wall | 18 |
| Opening | 60 |
| Window | 42 |
| Door | 18 |
| 曲墙 | 0 |
| 完整 Window–Opening–Wall 链 | 42 |

首个目标组件：

| 对象 | 值 |
|---|---|
| Wall | `Basic Wall:Outside wall:346660` |
| Wall GlobalId | `1F6umJ5H50aeL3A1As_wTm` |
| Opening GlobalId | `2cXV28XOjE6f6irhW0CO4t` |
| Window GlobalId | `2cXV28XOjE6f6irgi0CO4t` |
| Window 名称 | `M_Fixed:0915 x 1830mm:354395` |
| Window 尺寸 | 915 mm × 1830 mm |
| Wall Axis | `[0,0,0] → [8200,0,0]` mm，两点直线 |
| Wall 尺寸 | 长 8200 mm、厚 200 mm、高 3850 mm |
| Wall Body | `IfcBooleanClippingResult`，基础实体为矩形拉伸体 |
| Opening 墙局部 placement 原点 | `[3500, 100, 305]` mm；这是 Revit authoring anchor，不是洞口中心 |
| Opening 墙局部几何 X 范围 | `[2585, 3500]` mm |
| Opening 几何中心沿墙偏移 | `3042.5` mm；公共 `center_offset_mm` 的权威值 |
| Storey | `Level 1` |
| 同宿主墙 Window 数 | 2 |

同一宿主墙上的另一扇窗位于不同墙局部位置，因此 repair request 必须包含足以
唯一定位目标的墙局部位置。另一洞口的 placement X 为 5315 mm，几何 X 范围为
`[4400, 5315]` mm，因此真实几何中心沿墙局部 X 为 `4857.5` mm。目标墙没有
可用的 `IfcRelSpaceBoundary`，因此第一案使用 Storey、Wall 名称、Wall GlobalId
候选映射和中心偏移联合定位，不能依赖空间名称。

只读几何试验表明，删除目标 Window 和 Opening 后，墙体网格体积从
`5.64422 m³` 增加到 `5.97911 m³`，增量 `0.33489 m³` 正好等于
`0.915 × 1.83 × 0.2`。这证明该样例的目标洞口由语义 Opening/Voids 生效，
删除后墙体确实闭合，适合第一 mutation。

该文件来自固定 revision 的 BIM Whale submodule，规模足以暴露真实外部 IFC 的
命名、类型、属性和 authoring pattern，同时仍适合快速调试。它不是 BIMNet
兼容性证据。样例引用必须绑定上述 SHA-256；源文件不得复制后静默修改。正式
生成评估 case 前，还应为该单文件补充 raw-file/experiment manifest，明确其
evaluation use；这不改变其 `training_eligible: false` 状态。

### 4.2 Tier 1：第二 authoring pattern

Tier 0 通过后，增加一个不同来源或不同 authoring pattern 的 IFC2X3，验证
operation handler 没有写死 BIM Whale 的名称、类型或局部坐标细节。

### 4.3 Tier 2：BIMNet

BIMNet 在独立后续阶段处理：

- 大模型紧凑上下文选择；
- 不同 authoring pattern；
- 复杂几何、类型、材质和关系保持；
- 性能和上下文 token 预算；
- 曲墙能力分类；
- BIMNet 专用兼容性 fix，但不得污染公共 operation 合同。

## 5. 第一故障注入

mutation 名称：

```text
remove_window_and_opening
```

删除：

- 目标 `IfcWindow`；
- 对应 `IfcRelFillsElement`；
- 对应 `IfcOpeningElement`；
- 对应 `IfcRelVoidsElement`；
- 只能与被删除组件共同存在的直接依赖关系。

保留：

- 宿主墙；
- 墙的 placement、representation、材质、类型和属性；
- 楼层和空间；
- 门及其洞口；
- 其他构件和关系。

mutation 后必须验证：

- IFC 仍为 IFC2X3 且可读取、可保存；
- 墙和非目标构件 GlobalId 不变；
- 目标 Window、Opening、Fills、Voids 不存在；
- 删除目标 Opening 后，几何结果中的墙体目标区域不再保留洞口；
- 原始 IFC 未被原地修改。

## 6. Public/Private 数据边界

### 6.1 Private ground truth

`mutation_manifest.private.json` 可包含：

- 原始 Window、Opening、Wall GlobalId 和 STEP ID；
- 原始完整 placement、orientation 和 representation 摘要；
- 原始关系 ID；
- 原始尺寸、墙局部位置、世界坐标和几何指标；
- 删除前后实体计数；
- 原始文件 SHA-256。

Private 数据不得进入 predicted path 或 Provider 请求。

### 6.2 Public repair specification

Public Spec 中的 `storey.name + target.ifc_class + target.description` 是面向人的
目标墙选择器；`target.local_reference` 记录墙局部轴的参照方式和开洞中心位置。
Public Spec 不直接携带墙 GlobalId。Context Builder 必须用上述选择器在 damaged IFC
中解析出恰好一个候选，然后由 Provider 把该候选的裸 `ifc_global_id` 写入
`scope.target_ids` 和 operation-specific target。零匹配或多匹配都必须停止，不能猜测。
候选可以是目标基类的已注册 IFC 子类，例如 `IfcWallStandardCase` 满足 `IfcWall`。

由 private manifest 经过显式 allowlist 投影产生，可包含：

- 构件类型；
- 楼层名称；
- 墙的人类可理解描述；
- 墙局部参考起点；
- 洞口中心沿墙偏移；
- 窗宽、窗高、窗台高度；
- 保持墙、房间布局和其他构件不变的要求。

这里的尺寸和位置是用户修改要求，不视为答案泄漏。仍禁止暴露原始 Window、
Opening GlobalId、STEP ID 和 gold ChangeSet。

## 7. 紧凑 LLM 上下文

禁止把整个 IFC JSON 输入 LLM。Context Builder 采用 operation-aware 策略：

1. 根据文本确定相关楼层；
2. 只列出该楼层中与 operation 兼容的目标类别；
3. 对第一 operation 只列出直线墙的稳定 ID、GlobalId、名称、局部坐标、尺寸、方向和已有洞口摘要；
4. 设置候选数量和序列化字节/token 上限；
5. 超过上限时使用确定性检索和分页，不静默截断关键目标。

公共 Context 合同不得包含 Window 专用根字段，应使用通用结构：

```json
{
  "schema_version": "text2ifc/ifc-repair-context/0.1",
  "base_model_fingerprint": "sha256:...",
  "request_operation_hints": ["add_window_with_opening_to_wall"],
  "candidate_targets": [],
  "model_constraints": {},
  "context_budget": {}
}
```

`candidate_targets` 的类型化详情由 operation-specific context adapter 提供。

## 8. ChangeSet 公共架构

### 8.1 公共 envelope

所有 IFC repair operation 共用：

- `schema_version`；
- `changeset_id`；
- `base_model_fingerprint`；
- `source_request_hash`；
- `scope`；
- `operations`；
- `evidence_refs`；
- `preconditions`；
- `postconditions`。

### 8.2 Operation registry

每个 operation 注册以下能力：

```text
operation_type
target_ifc_classes
parameter_schema
target_schema
context_adapter
precondition_checker
applicator
postcondition_checker
comparison_adapter
capability_constraints
precondition_names
postcondition_names
```

公共调度器只能依赖该接口，不能导入 Window 专用实现。

### 8.3 第一 operation

```text
add_window_with_opening_to_wall
```

示例：

```json
{
  "schema_version": "text2ifc/ifc-repair-changeset/0.1",
  "changeset_id": "changeset-window-repair-001",
  "base_model_fingerprint": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "source_request_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "scope": {
    "target_ids": ["wall-global-id"],
    "forbidden_ids": []
  },
  "evidence_refs": [
    "spec:/opening",
    "spec:/target/local_reference",
    "context:/candidate_targets/0"
  ],
  "preconditions": [
    "base_model_fingerprint_matches",
    "source_request_hash_matches",
    "target_exists",
    "opening_within_wall",
    "opening_interval_available"
  ],
  "postconditions": [
    "opening_voids_wall",
    "window_fills_opening",
    "requested_geometry_matches"
  ],
  "operations": [
    {
      "operation_id": "operation-window-001",
      "operation_type": "add_window_with_opening_to_wall",
      "target": {
        "wall_global_id": "wall-global-id"
      },
      "parameters": {
        "position": {
          "reference": "wall_local_start",
          "center_offset_mm": 3042.5
        },
        "opening": {
          "width_mm": 915,
          "height_mm": 1830,
          "sill_height_mm": 305
        },
        "window": {
          "fit_opening": true
        }
      },
      "evidence_refs": [
        "spec:/opening",
        "spec:/target/local_reference",
        "context:/candidate_targets/0"
      ]
    }
  ]
}
```

LLM 只负责目标选择和领域参数。IFC placement、representation、OwnerHistory、
GlobalId 和底层关系由确定性代码生成。

## 9. 可扩展 operation 方向

首版只实现 Window，但接口必须能容纳：

| 后续 operation | 目标 | 主要创建或修改内容 |
|---|---|---|
| `add_opening_to_wall` | Wall | Opening + Voids |
| `add_door_with_opening_to_wall` | Wall | Opening + Door + Voids + Fills |
| `add_beam` | Storey/结构目标 | Beam + placement + containment/type |
| `add_column` | Storey/结构目标 | Column + placement + containment/type |
| `remove_component` | Product | 显式依赖闭包删除 |
| `update_component_placement` | Product | 受限 placement 更新 |

这些名称是能力规划，不代表第一阶段已经支持。

不同 operation 可以有不同参数和几何适配器，但必须复用：

- ChangeSet envelope；
- base fingerprint；
- scope 与 forbidden target；
- 事务应用；
- 公共 Audit 汇总；
- preservation report；
- artifact/trace 合同；
- 公共评估报告结构。

## 10. Audit 合同

### 10.1 公共检查

- JSON Schema 和 operation 注册状态；
- IFC Schema；
- base fingerprint；
- target 存在且类别允许；
- scope 和 forbidden target；
- evidence 引用；
- operation 冲突；
- 参数单位和有限数值；
- precondition 可验证性。

### 10.2 Window-specific 检查

- Wall 是支持的直线墙；
- width、height、sill 为正；
- 水平范围在墙长度内；
- 垂直范围在墙高度内；
- 目标区域没有冲突 Opening；
- 墙厚和 Opening 深度可以确定；
- operation 只创建一组 Opening/Window/Voids/Fills。

Audit 输出必须包含结构化 evidence，不能只有 Boolean。

## 11. 事务 Applicator

公共 Applicator 执行：

1. 重新验证 base fingerprint；
2. 打开 damaged IFC 的内存副本；
3. 按顺序分派 operation handler；
4. 记录 created/modified/removed IDs；
5. 执行公共和 operation-specific postconditions；
6. 写入临时文件并重开；
7. 成功后原子发布 `repaired.ifc`；
8. 失败时不产生可被误认成成功结果的输出。

第一 Window handler 创建：

- `IfcOpeningElement`；
- `IfcRelVoidsElement`；
- `IfcWindow`；
- `IfcRelFillsElement`；
- 必要的 placement、representation、containment、type/property 关系。

## 12. 比较与评估

### 12.1 公共指标

- IFC 可读取和可重写；
- Schema 保持；
- operation postconditions；
- 非目标实体增删改；
- 非目标 GlobalId、placement、geometry 和关系漂移；
- 重复组件；
- complete repair success。

### 12.2 Window-specific 指标

- Opening 位于目标墙；
- Window 填充创建的 Opening；
- width、height、sill、洞口中心沿墙偏移和 orientation 误差；
- 目标区域视觉/几何洞口恢复；
- Window 和 Opening 数量无重复。

Comparator 使用公共 normalized semantic snapshot，再由 operation-specific adapter
补充几何指标。不得按字节、STEP ID 或实体顺序比较。

## 13. 产物结构

代码和产物按现有仓库惯例分层，避免创建独立平行项目：

```text
schemas/agent/
  ifc-repair-changeset-0.1.schema.json
  ifc-repair-context-0.1.schema.json

src/text2ifc_ifc_repair/
  context.py
  changesets.py
  registry.py
  audit.py
  apply.py
  compare.py
  operations/
    window.py

scripts/ifc_repair/
  inventory.py
  mutate.py
  run_case.py

tests/ifc_repair/

dataset/processed/ifc-repair/
  sample-selection/
  cases/
```

具体模块名可以在实施计划中微调，但公共接口和职责边界不得漂移。

## 14. 自动测试与真实 UAT

### 14.1 自动测试

至少覆盖：

1. 样例 Header、Hash 和结构冻结；
2. 曲墙拒绝；
3. mutation 确定性和原文件不变；
4. private/public allowlist；
5. 紧凑上下文预算；
6. ChangeSet Schema 和 registry；
7. base fingerprint、scope 和 preconditions；
8. Window handler；
9. repaired IFC 重开；
10. 关系和几何恢复；
11. 非目标保持；
12. 未注册 operation 拒绝；
13. fake Provider 端到端闭环；
14. 新 operation 能通过 registry fixture 接入而无需修改公共调度器。

### 14.2 真实 Provider UAT

真实运行必须保存：

- Prompt ID 和 Hash；
- repair request；
- public context；
- raw response；
- parsed predicted ChangeSet；
- Audit；
- repaired IFC；
- evaluation JSON 和中文报告；
- private artifact 未进入 Provider 输入的证明。

## 15. 实施顺序

```text
文档和合同冻结
→ 小型样例冻结
→ mutation
→ public/private 投影
→ compact context
→ common ChangeSet envelope + registry
→ Window operation Audit/Applicator/Comparator
→ fake Provider E2E
→ 真实 Provider UAT
→ Tier 1 第二 authoring pattern
→ BIMNet 适配与 fix
→ 曲墙及其他 operation
```

## 16. 第一阶段完成标准

- canonical 设计、Schema 和 Prompt 一致；
- 小型无曲墙 IFC 样例和目标组件被冻结；
- Window+Opening mutation 可重复且原文件不变；
- LLM 只接收紧凑 public context；
- predicted ChangeSet 来自 fake 或真实 Provider 路径，而非 private gold 复制；
- Audit、Apply、Compare 闭环；
- repaired IFC 有正确 Opening、Window、Voids 和 Fills；
- 非目标构件无不可接受变化；
- 离线自动测试通过；
- 至少一次真实 Provider UAT 有完整证据；
- 公共 registry 接口没有把架构写死为 Window；
- BIMNet、曲墙、门、梁、柱仍被明确记录为后续能力，未被错误宣称完成。

## 17. 决策日志

### 2026-07-18

- 下一里程碑的终极产品流冻结为：用户提供 existing/damaged IFC 和自然语言需求，
  一个程序完成本地索引、Agent 目标理解、ChangeSet 生成、确定性 IFC 应用和证据发布。
- GUID、Name/Tag/type、楼层、轴网/空间、方位、关系和几何均为有效目标证据；
  `Name` 只作为可解释别名，不作为全局唯一主键。冲突或歧义必须澄清/停止。
- L1 geometry/relationship 与 L2 semantic fidelity 都是正式修复的强制门槛。
  L3 authoring/identity exactness 只记录为未来问题，v1.1 不做兼容或能力声明。
- 真实 DeepSeek UAT 已通过，证据目录为
  `dataset/processed/ifc-repair/cases/large-building-window-repair-001-deepseek-live-20260718-v2/`。
  Provider 实际使用 `6381` 个输入 token、`1162` 个输出 token；ChangeSet、Audit、事务
  Applicator、Comparator 和 preservation checks 全部通过。
- `128k` 上下文上限保留为本次成功测试后的讨论项；当前配置仍维持输入 `65536`、
  输出 `65536`。在构造接近上限的上下文压力测试并确认 Provider 实际 tokenizer 行为前，
  不将一次仅使用 `6381` 输入 token 的成功样例解释为 `128k` 已验证。
- 以仓库根目录 `.env` 为当前运行配置权威，确认活动 Provider 为 DeepSeek
  OpenAI-compatible 路径，而不是 Mimo Anthropic-compatible 路径。
- IFC repair live runner 使用 `DEEPSEEK_API_KEY`、`OPENAI_BASE_URL`、
  `TEXT2IFC_DEEPSEEK_MODEL`、`TEXT2IFC_DEEPSEEK_MAX_TOKENS` 与
  `TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS`；配置检查和证据
  输出不得泄露 key 或完整 endpoint。
- 配置就绪不等于 UAT 通过。只有真实模型响应经过 ChangeSet 校验、Audit、事务
  Applicator 和独立 Comparator 后，才能标记为 live UAT 成功。
- DeepSeek live 调用的最大输入预算和最大输出预算均固定为 `65536 tokens`。
  输出预算通过 Provider 参数传递；输入预算在调用前用公开、记录在案的估算器执行
  硬性检查，超限时不得发起网络请求。
- Operation Registry 必须向 Provider 暴露 operation-specific `target_schema`；首个
  Window operation 明确要求 `target.wall_global_id`，其值和 `scope.target_ids` 都使用
  `candidate_targets[index].ifc_global_id`，不得使用带 `ifc:` 前缀的 `target_id`。
- Provider evidence 引用统一使用 `spec:` 和 `context:` 命名空间，并验证 JSON Pointer
  确实存在。旧的 `request:/opening` 不再用于指代 Public Spec。
- Prompt 必须包含一个完整 envelope 示例，明确示例值不可复制；还必须把 repair
  request、Public Spec、Context 和 IFC metadata 声明为不可信数据而非额外指令。
- 同楼层同名同类目标如果不能唯一匹配，Context Builder 必须确定性拒绝，不能依赖
  候选排序让模型猜测。

### 2026-07-17

- 根据源 IFC 的世界坐标三角网格回投墙局部坐标，确认 Opening placement X
  `3500` 不是洞口中心；目标洞口真实几何中心为 `3042.5` mm，第二洞口中心为
  `4857.5` mm。
- 用户确认公共 `center_offset_mm` 以真实几何中心为准。原 placement X
  `3500/5315` 只保留在 private manifest，不能进入跨 authoring pattern 的
  ChangeSet 坐标语义。

### 2026-07-16

- 选择混合式 IFC authority + compact JSON context + semantic ChangeSet 路线。
- 采用离线 deterministic 闭环加一次真实 Provider UAT。
- 从保留 Opening 的 mutation 改为同时删除 Window 和 Opening，再由文本要求创建。
- 第一阶段仅支持直线墙；BIMNet 已确认存在圆弧墙，后续单独支持。
- 首个 smoke sample 改为 BIM Whale `LargeBuilding.ifc`；它是中小型真实外部
  IFC，不属于 BIMNet，BIMNet 仍延后单独适配。
- Window 只是首个 operation；公共接口必须支持墙洞、门、梁、柱等后续修改。
