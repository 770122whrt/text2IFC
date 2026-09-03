# Repair Milestone R1 模型选择与多样性

## 1. 选择边界

模型选择只使用当前公开/local IFC 内容、模型自身 public identities、公开
license/model card 与 IfcOpenShell 可观测信息。没有读取 pristine/original IFC、
mutation recipe、private Gold、deleted GUID、已有 Proof 或 benchmark expected answer。

四个模型均由当前仓库 `.venv` 的 IfcOpenShell 重新打开，schema 均为 `IFC2X3`。
本次只读取，没有生成 repaired IFC。

## 2. 冻结模型

| Model ID | Dataset/source | IFC schema | Storeys | Approx. relevant element counts | Assigned cases | Diversity reason | Previously heavily used? |
|---|---|---:|---:|---|---|---|---|
| `R1-DPX-ARC` | IFC-Bench / buildingSMART Duplex Apartment, CC BY 4.0 | IFC2X3 | 4 | Wall 57; Window 24; Door 14; Opening 50; Beam 8 | E1, H1, H3 | compact multi-Storey residential architecture；meter project units；真实同层 Window 歧义 | no current planning/docs/scripts/tests path references found |
| `R1-WRH-ARC` | IFC-Bench / West Riverside Hospital Architecture, CC BY 3.0 | IFC2X3 | 8 | Wall 1440; Window 131; Door 440; Opening 665; Column 349 | E2, M1, H2 | large hospital；high occurrence density；millimetre project units | no current path references found |
| `R1-S65-STR` | IFC-Bench / Sixty5 Structural, CC BY 4.0 | IFC2X3 | 19 | Wall 299; Opening 1284; Beam 354; Column 387; BeamType 16; ColumnType 109 | E3, M3, A1 | tall structural discipline model；Dutch Storey names；rich existing Type graph | no current path references found |
| `R1-BW-TALL` | BIM Whale IFC Samples / TallBuilding, retained MIT corpus | IFC2X3 | 5 | Wall 24; Window 21; Door 5; Opening 26; no existing Beam/Column | E4, M2, H4 | small synthetic high-rise；clean add-operation surface；different source corpus | no current path references found |

这些模型不是近期 Phase 12 的 `d7n` / `vvo` / LargeBuilding 主 fixture。仓库
source catalog 将 IFC-Bench 用于 evaluation/schema/spatial reasoning research，将
BIM Whale 用于 parser/compiler/geometry robustness research；本冻结包不把它们加入
training，也不改变源许可状态。

## 3. Immutable model identities and reopen evidence

| Model ID | Repository path | Size bytes | SHA-256 | IfcOpenShell reopen | Project unit scale to metre |
|---|---|---:|---|---|---:|
| `R1-DPX-ARC` | `dataset/external/ifc-bench/projects/duplex/arc.ifc` | 1,656,153 | `707a032566dee8e969a44d95509be46d646440e2443624709f8d3ae2b45f4656` | opened; `IFC2X3` | 1.0 |
| `R1-WRH-ARC` | `dataset/external/ifc-bench/projects/west_riverside_hospital/arc_ifc2x3.ifc` | 80,318,141 | `989ace1d52f694ee94d80bd99aa81d0ff3d76cf21f34fcfd00a286ac897ed8a6` | opened; `IFC2X3` | 0.001 |
| `R1-S65-STR` | `dataset/external/ifc-bench/projects/sixty5/str.ifc` | 7,422,441 | `79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22` | opened; `IFC2X3` | 0.001 |
| `R1-BW-TALL` | `dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc` | 616,509 | `9f180a7148bb7bcf43dd80800068553f1c8b189ebe0dc84b6c498061832960d1` | opened; `IFC2X3` | 0.001 |

Source evidence paths：

- `dataset/external/ifc-bench/projects/duplex/license.txt`
- `dataset/external/ifc-bench/projects/west_riverside_hospital/license.txt`
- `dataset/external/ifc-bench/projects/sixty5/license.txt`
- `dataset/sources/CATALOG.md`（BIM Whale pinned corpus + MIT evidence）

`dataset/manifests/raw-files.jsonl` 当前没有这四个 external path 的逐文件记录。
本冻结包用 source-submodule path、project license 和冻结 SHA 形成 execution identity；
不把这一点隐瞒成已完成的 training admission。它不影响当前 evaluation-only selection，
但未来若要复制模型出 submodule 或进入训练集，必须先补 provenance admission。

## 4. Public target bindings

| Role | Model | IFC class | GlobalId | Tag | Storey | Public name/type |
|---|---|---|---|---|---|---|
| E1 Window | R1-DPX-ARC | IfcWindow | `1hOSvn6df7F8_7GcBWlRRL` | `147051` | Level 1 | `M_Fixed:750mm x 2200mm...` |
| H1 Window | R1-DPX-ARC | IfcWindow | `1hOSvn6df7F8_7GcBWlRLx` | `146885` | Level 1 | `M_Fixed:750mm x 2200mm...` |
| E2 Door | R1-WRH-ARC | IfcDoor | `3JlX9$$_PCKBNpDob64$5M` | `439207` | Level 4 | `M_Single-Flush:0915 x 2032mm_Wood...` |
| M1 Door | R1-WRH-ARC | IfcDoor | `3JlX9$$_PCKBNpDob64$4w` | `439243` | Level 4 | same public door family, different occurrence |
| H2 Door | R1-WRH-ARC | IfcDoor | `1jI3nV6Sn2LfeyEYxROCeh` | `468036` | Level 4 | same dimensions, distinct Type identity |
| H2 Wall | R1-WRH-ARC | IfcWall | `2HaS6zNOX8xOGjmaNi_r5s` | `187497` | Level 4 | exterior metal panel wall |
| E3 Beam | R1-S65-STR | IfcBeam | `1BpQ2K66f13Pyv1xzN7BBN` | `738548` | 00 begane grond | L150×150×12 beam occurrence |
| E4 Wall | R1-BW-TALL | IfcWallStandardCase | `0ZBert7zf3GhThdO12NKAr` | `358471` | Level 1 | outside wall |
| A1 reused Type | R1-S65-STR | IfcBeamType | `12jWe1_Rb2cR0ot5ICgwf_` | N/A | model-wide | rectangular concrete 500×800 Type |

## 5. H3 natural clarification evidence

Initial public query：Level 2、IfcWindow、type name `819mm x 759mm`。生产
`resolve_target` 返回 `ambiguous`；前五个 offered candidates（同分 75）为：

| Stable GlobalId | Tag | Name |
|---|---|---|
| `1hOSvn6df7F8_7GcBWlS1M` | 149736 | M_Casement:819mm x 759mm... |
| `1hOSvn6df7F8_7GcBWlS2V` | 149537 | M_Fixed:819mm x 759mm... |
| `1hOSvn6df7F8_7GcBWlS4Q` | 149924 | M_Fixed:819mm x 759mm... |
| `1hOSvn6df7F8_7GcBWlSga` | 147994 | M_Fixed:819mm x 759mm... |
| `1hOSvn6df7F8_7GcBWlSnC` | 148722 | M_Fixed:819mm x 759mm... |

冻结的 intended answer 是 GlobalId `1hOSvn6df7F8_7GcBWlS2V`，而不是候选
rank/token。resume 时仍必须验证该 identity 属于当前 offered set。

## 6. Add-operation geometry safety

所有坐标均冻结为 Storey-local millimetres。它们不从 private truth 推导。

- Duplex Level 1 当前可测 Beam axis bbox：x 266.61–8533.39，
  y -17523–-277，z 3100 mm。H1 使用 y=-20000，避免 existing same-axis overlap。
- Sixty5 ground Storey 当前可测 structural axes bbox：x 16552–19128，
  y 50825–55070，z 1254–3060 mm。M3/A1 使用 x≥25000 或 y=58000/60000。
- TallBuilding 没有现有 Beam/Column；M2/H4 分别使用不同 Storey 和不同 y axis。
- 每个选定 Storey 恰有一个 `IfcRelContainedInSpatialStructure` containment relation，
  满足当前 structural precondition。

这只证明参数不是已知同轴冲突；真正 applicator、reopen、L0/L1/L2 仍必须等人工
批准后在 genuine run 中验证。
