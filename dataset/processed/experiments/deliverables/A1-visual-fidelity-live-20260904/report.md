# A1 Structural Repair Visual-Fidelity Validation

## Result

**PASS** — the current Repair pipeline completed a genuine DeepSeek live call, published a reopened IFC2X3 artifact, preserved the exact requested `IfcBeamType`, preserved the requested structural geometry, and restored the authorized existing appearance instead of producing a default gray beam.

## Public repair request

> 在 00 begane grond 添加一根新的水平直线矩形梁，中心轴从 (25000, 58000, 3000) mm 到 (31000, 58000, 3000) mm，截面宽 500 mm、高 800 mm，并精确复用 GlobalId 为 12jWe1_Rb2cR0ot5ICgwf_、名称为 28_SF_AT_balk vierkant beton:balk vierkant_gen_500x800 (C35/45) 的现有 IfcBeamType。

## Files in this package

| File | Role | SHA256 |
|---|---|---|
| `original.ifc` | Canonical unmodified source input: `dataset/external/ifc-bench/projects/sixty5/str.ifc` | `79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22` |
| `damaged.ifc` | Historical accepted A1 repair-input copy | `79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22` |
| `repaired.ifc` | Final IFC from the genuine live RepairAPI run performed for this visual-fidelity validation | `02492c6a6fa55c6f983a039e9f31d3493011b49f88dafa032152714c28298577` |

### Important original/damaged boundary

A1 is an **additive repair case**. `original.ifc` and `damaged.ifc` are byte-identical by design in this package. The repair condition is that the requested Beam does not yet exist in the input; it is not a benchmark case produced by deleting an entity from a separately frozen pristine Gold IFC.

The historical R1 evidence explicitly states that no case-specific pristine/private Ground Truth was frozen for A1. Therefore, `original.ifc` in this delivery means the **canonical unmodified source input**, not a newly claimed pristine Gold artifact.

## Repair chain validated

```text
original / damaged IFC2X3
        ↓
RepairAPI.start(source, exact public request)
        ↓
source validation + IFC index
        ↓
DeepSeek Stage 1 RepairIntent
        ↓
deterministic Storey / exact-Type resolution
        ↓
DeepSeek Stage 2 ChangeSet draft
        ↓
deterministic Bound ChangeSet + audit
        ↓
Beam operation applicator
        ↓
create_straight_rectangular_member()
        ↓
bind_structural_type()
        ↓
appearance authority resolver
        ├─ Type representation style
        ├─ Type material style
        └─ same-Type reference occurrence appearance
        ↓
postconditions + evaluation + atomic publication
        ↓
independent reopen validation
```

The appearance fallback used in this A1 file is the authorized same-Type reference occurrence material style because the exact `IfcBeamType` itself has no usable `RepresentationMaps` or Type-owned surface style.

## Genuine Provider evidence

- Provider: `deepseek-openai-compatible`
- Model: `deepseek-v4-flash`
- RepairAPI run: `repair-aef5ae0ea9314b2c8c09e4ede121fc07`
- Run status: `succeeded`
- `complete_repair_success`: `true`
- `successful_artifact_publishable`: `true`
- Clarification: none
- Stage-2 provider evidence class: `live`
- Stage-2 transport attempts: `1`

This was not a mock-provider or replay-only acceptance. A zero-network deterministic preflight was completed before the live call.

## Independent reopen checks on `repaired.ifc`

### Exact Type

- `IfcBeamType.GlobalId`: `12jWe1_Rb2cR0ot5ICgwf_`
- Type name: `28_SF_AT_balk vierkant beton:balk vierkant_gen_500x800 (C35/45)`

### New Beam

- `IfcBeam.GlobalId`: `1g5fq_GwLRavtYbIAOQBjh`
- Name: `Text2IFC beam add-beam-1`
- Storey: `00 begane grond`
- Axis start: `(25000, 58000, 3000) mm`
- Axis end: `(31000, 58000, 3000) mm`
- Axis length: `6000 mm`
- Section: rectangle `500 × 800 mm`
- Representation: `SweptSolid`

### Appearance

The exact Type has no direct authoritative style, so the resolver used the unique existing same-Type Beam's authorized material appearance:

- Style/material name: `f2_beton ihwg_C35/45`
- RGB: `(0.000000, 0.384314, 0.525490)`
- Transparency: `0.0`

The new Beam therefore carries the source model's authorized blue/cyan material appearance instead of the previous unstyled gray fallback.

## Determinism and source preservation

- Source SHA256 before live: `79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22`
- Source SHA256 after live: `79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22`
- Source mutation: **none**
- Offline deterministic A1 replay output SHA256: `02492c6a6fa55c6f983a039e9f31d3493011b49f88dafa032152714c28298577`
- Genuine live output SHA256: `02492c6a6fa55c6f983a039e9f31d3493011b49f88dafa032152714c28298577`
- Offline/live output identity: **byte-identical**

## Preflight summary

Before the genuine Provider call, the changed-scope preflight completed:

- Presentation / Generation / Structural Type core tests: `26/26 PASS`
- Dataset-path + structural regression: `39/39 PASS`
- RepairAPI offline E2E + Provider seam: `6/6 PASS`
- IFC presentation offline validator: `PASS`
- Python `compileall`: `PASS`
- Scoped `git diff --check`: `PASS`
- Provider config: `ready`

Temporary pytest basetemp/cache directories and failed-attempt transient outputs were removed after evidence closure; the retained validation evidence is intentionally bounded.
