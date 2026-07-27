# IFC2X3 ChangeSet implementation findings

> Status: active implementation record
> Date: 2026-07-17
> Design authority: [`design.md`](design.md)

This file records implementation evidence that must be reviewed before it can
change the design authority. It is append-only by finding; resolved findings
must retain the original evidence and record the resulting decision.

## IFCR-F001 — Opening placement origin is not its geometric centre

Status: **resolved — accepted 2026-07-17**

The frozen design currently describes the target Opening wall-local placement
origin X as the opening-centre offset:

```text
target placement X = 3500 mm -> documented centre = 3500 mm
second placement X = 5315 mm -> documented centre = 5315 mm
```

IfcOpenShell 0.8.5 geometry inspection of the immutable source shows that the
Revit-authored Opening representation extends in negative wall-local X from
its object placement:

| Opening | Placement X | Wall-local geometric X bounds | Geometric centre |
|---|---:|---:|---:|
| `2cXV28XOjE6f6irhW0CO4t` | 3500.0 mm | [2585.0, 3500.0] mm | 3042.5 mm |
| `2cXV28XOjE6f6irhW0CO7d` | 5315.0 mm | [4400.0, 5315.0] mm | 4857.5 mm |

The target width is 915 mm, so both centres equal `placement_x - 915 / 2`.
The result was calculated from world-coordinate triangulated vertices,
transformed back into the host wall coordinate frame; it is not inferred only
from STEP placement attributes.

### Why this blocks the Window Applicator

`center_offset_mm` is intended to be an authoring-pattern-independent semantic
coordinate. Treating a Revit-specific placement anchor as a centre would shift
the repaired physical opening by 457.5 mm and make geometric comparison against
the source incorrect.

### Recommended resolution

Keep the public operation field named `center_offset_mm`, but change the frozen
target request and gold geometry to the actual centre:

```text
target center_offset_mm = 3042.5
second existing opening centre_offset_mm = 4857.5
```

Retain the original placement origin `3500.0` only in the private mutation
manifest as authoring evidence. The deterministic Applicator may choose any IFC
placement anchor as long as the resulting physical centre satisfies the public
semantic coordinate and the comparator measures geometry in the wall-local
frame.

Alternative (not recommended): rename the public coordinate to a
placement-origin offset. That would leak an authoring convention into the
cross-file ChangeSet contract and make later authoring patterns harder to
support.

No Applicator code depending on this coordinate was written while the finding
was pending.

### Resolution

The user accepted the recommended resolution on 2026-07-17: public repair
semantics and evaluation use the physical wall-local geometric centre. The
target value is `3042.5` mm and the second opening centre is `4857.5` mm.
Placement anchors `3500/5315` remain private authoring evidence only. The
canonical design and implementation prompt were updated before Applicator work
resumed.

## IFCR-F002 — Offline deterministic loop implemented; live UAT configuration absent

Status: **implemented offline; live UAT later passed on 2026-07-18**

The first complete run uses the frozen BIM Whale `LargeBuilding.ifc` sample and
the public geometric-centre contract. It produces a deterministic damaged IFC,
public repair inputs, a fake-Provider ChangeSet, structured Audit, transactional
incremental repair, independent preservation/geometry evaluation, Chinese
report, and artifact manifest.

Measured acceptance evidence:

| Metric | Result |
|---|---:|
| repaired IFC schema | IFC2X3 |
| Window / Opening / Fills / Voids counts | 42 / 60 / 60 / 60 |
| centre / sill / width / height / depth error | 0 mm |
| orientation error | 0° |
| restored void volume | 0.33489 m³ |
| unexpected non-target drift | 0 |
| repeated repaired IFC SHA-256 | identical |

The immutable offline evidence bundle is stored at:

```text
dataset/processed/ifc-repair/cases/large-building-window-repair-001-offline-v1/
```

The live UAT entry point is:

```powershell
.venv\Scripts\python scripts\ifc_repair\run_case.py <output> --mode live
```

Configuration inspection on 2026-07-17 reported that the then-checked API key,
`ANTHROPIC_BASE_URL`, and `TEXT2IFC_MIMO_MODEL` were all absent. No deterministic
or private-gold result was labelled as real Provider evidence. The later
DeepSeek live result is recorded separately in IFCR-F005.

## IFCR-F003 — IFC repair live runner synchronized to DeepSeek configuration

Status: **configured, implemented, and live UAT passed — 2026-07-18**

A redacted inspection of the repository root `.env` established the active
configuration contract:

```text
TEXT2IFC_PROVIDER=deepseek
DEEPSEEK_API_KEY=<configured; secret not recorded>
OPENAI_BASE_URL=https://api.deepseek.com
TEXT2IFC_DEEPSEEK_MODEL=deepseek-v4-flash
TEXT2IFC_DEEPSEEK_MAX_TOKENS=65536
TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS=65536
```

The previous IFC repair CLI incorrectly checked the Mimo Anthropic-compatible
environment and constructed `MimoAgentProvider`. It now:

1. loads `.env` without overriding process-level environment values;
2. reports only the redacted OpenAI-compatible configuration status;
3. constructs `OpenAICompatibleLiveProvider` from the DeepSeek runtime config;
4. saves redacted live request, response and event evidence in addition to raw
   response text, Provider metadata and parsed ChangeSet diagnostics;
5. continues through the same Audit, transactional Applicator and independent
   Comparator as the offline path.

A real DeepSeek UAT was subsequently executed on 2026-07-18. The successful
evidence bundle reports `complete_repair_success: true`; details are recorded
in IFCR-F005 below.

## IFCR-F004 — Provider prompt independent review found target-contract gaps

Status: **implemented, covered by offline contract tests, and exercised by live UAT — 2026-07-18**

An independent read-only subagent review found that the frozen single case can
be resolved from Public Spec plus Context, but the live Prompt was not yet
robust enough for formal UAT:

- Public Spec identifies the target by storey, IFC class and wall name; Context
  provides the candidate `ifc_global_id`, wall basis, dimensions and openings.
- The operation handler requires `target.wall_global_id`, but this target shape
  was absent from the Provider-visible operation contract.
- The Prompt contained no complete Schema-valid ChangeSet example.
- `request:/opening` was used for a pointer into Public Spec even though the
  repair request is plain text.
- `target_id` (`ifc:<GlobalId>`) and `ifc_global_id` (bare GlobalId) were not
  distinguished explicitly.
- IFC metadata embedded in Prompt sections was not labelled as untrusted data.

The implemented repair publishes `target_schema` and allowed condition names,
uses verified `spec:` and `context:` evidence pointers, adds a complete
non-copyable example, rejects ambiguous duplicate target selectors, and adds
prompt-injection guidance. Targeted offline tests cover each binding rule. The
live UAT confirmed that the repaired contract produces an accepted ChangeSet.

## IFCR-F005 — Real DeepSeek Window repair UAT passed

Status: **passed — 2026-07-18**

Evidence directory:

```text
dataset/processed/ifc-repair/cases/large-building-window-repair-001-deepseek-live-20260718-v2/
```

The real `deepseek-v4-flash` response produced one valid
`add_window_with_opening_to_wall` operation targeting the expected bare wall
GlobalId. Provider diagnostics, Audit, transactional application, IFC reopen,
operation-specific comparison and non-target preservation all passed.

Recorded Provider usage was `6381` prompt tokens and `1162` completion tokens
(`7543` total). Geometry comparison reported zero centre, sill, width, height,
depth and orientation error; restored void volume was `0.33489 m3`, matching
the expected volume, with one and only one matching Window/Opening chain.

The first sandboxed attempt was retained separately as `...-v1/` and records
an `APIConnectionError`; it is infrastructure-failure evidence, not a model
failure. The authorized network run is the passing `...-v2/` bundle.

The possible `128k` input-context setting remains deferred for a dedicated
near-limit stress test. This UAT used only `6381` prompt tokens, so it validates
the semantic live path but does not validate 128k context behavior.

## IFCR-F006 — Ground truth direct comparison exposes semantic-fidelity gap

Status: **L1 geometry/relationship repair passed; L2 semantic fidelity incomplete — 2026-07-18**

A direct original `LargeBuilding.ifc` versus `repaired.ifc` comparison was
performed after the successful live UAT. Core class counts, host wall identity,
wall-local opening/window bounds, dimensions, sill, centre, type, storey,
Void/Fills chain and restored volume all match.

The files are not exact reconstructions. The original target chain and its
dependent instance property/quantity/material records account for 29 missing
rooted entities, while the repair creates 4 replacement core entities. The new
Window reuses the correct WindowStyle but does not restore all instance Psets,
quantities, material/classification associations, Name/Tag or authoring
placement/representation. In particular, the resolved
`Pset_WindowCommon.IsExternal` differs (`true` in ground truth and `false` in
the repaired instance).

Therefore `complete_repair_success: true` is valid only for the current L1
geometry-and-relationship contract. It must not be cited as full ground-truth
BIM semantic restoration. The complete pipeline and comparison table are in
`ground-truth-comparison.md`.
