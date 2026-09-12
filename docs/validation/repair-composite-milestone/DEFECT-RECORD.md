# DEFECT RECORD — Mixed-family composite defects (BOTH FIXED)

Two deterministic production defects were found during the offline
full-chain preflight of the Composite Repair Milestone (specification
Section 10.1), both repaired 2026-08-31 under explicit user authorization
for mechanism-level, general fixes (not point-fixes for the test cases).
Genuine Provider execution was STOPPED per Section 10.2 until both were
fixed and the regression gates re-run.

> **Correction note (honest record):** the first version of this record
> stated the root cause as "the live policy-facts call never supplies
> `authorized_semantics`".  That mechanism description was **wrong** —
> `api.py:542-553` passes `ResolvedOperation.to_dict()`, which *does* include
> `authorized_semantics`.  Re-analysis with the real run artifacts gave the
> correct two-part root cause below.  The blocking symptom
> (`BOUND_CHANGESET_INVALID`) was never in doubt; only the mechanism
> attribution is corrected here.

## Symptom

Any ChangeSet mixing a structural operation (`add_beam`/`add_column`) with a
window operation (`add_window_with_opening_to_wall`) fails at deterministic
Stage 2 binding, before any apply/publication and before any Provider output
matters:

```
BOUND_CHANGESET_INVALID:/operations/0/semantic_assignments/0/source_kind
```

Notably the first failing operation is the **structural** one, not the window
one — the envelope is rejected because the structural manifest's vocabulary
cannot be expressed in the negotiated envelope.

## Root cause (two family-specific inconsistencies)

Manifest version is chosen per operation in
`build_semantic_manifest` (`src/text2ifc_ifc_repair/semantic_authoring.py`):

* `use_v02 = any(fact.canonical_source_kind is not None ...)` — a fact-level
  canonical kind upgrades the manifest past v0.1;
* `use_v03 = use_v02 and any(fact.occurrence_scope in {…})` — a scope-name
  check upgrades it to v0.3.

The bound-changeset envelope is then negotiated in
`src/text2ifc_ifc_repair/provider_stage.py:262-268`: all-v0.3 manifests →
0.4 envelope; all-v0.2 → 0.3; anything else → **0.2**.  The three schema
generations use **disjoint source_kind vocabularies**:

* 0.2 enum: raw kinds (`explicit_request`, `surviving_target`,
  `surviving_host`, `surviving_type`, `authorized_type_cohort`,
  `approved_prototype`, `deterministic_policy`);
* 0.3/0.4 enum: canonical kinds (`explicit_value`, `deterministic_derived`,
  `type_inherited`, `approved_occurrence_prototype`, `authorized_type_cohort`).

**Part 1 — the window policy-facts gate.**  The window hook set
`canonical_source_kind` only when the resolved operation carried an
`authorized_occurrence_assignment`
(`operations/window.py:461-465` computed the gate; `window.py:510-514` applied
it).  Live-resolved window operations never carry one, so every window policy
fact kept `canonical_source_kind=None` and the window manifest stayed at
v0.1 with raw kinds.  Siblings are unconditional: `door.py:827`,
`beam.py:606`, `column.py:631` all set `"deterministic_derived"` directly.

**Part 2 — the `use_v03` scope set.**  Even with canonical kinds, the
v0.3 upgrade required an occurrence scope in
`{"door_occurrence", "beam_occurrence", "column_occurrence"}`
(`semantic_authoring.py:326-330`).  Window facts use `"window_occurrence"`
(the `SemanticFact` default), so a window manifest could at best reach v0.2.
History: the set started door-only (phase 11), was extended to beam/column in
12-10 (`b5f27dea`); window — the original v0.1 family — was never added.

**Combined effect (verified on real run artifacts):** structural manifest =
v0.3 (`deterministic_derived`), window manifest = v0.1
(`deterministic_policy`/`surviving_target`) → negotiation falls to the 0.2
envelope → `deterministic_derived` is not in the 0.2 enum →
`BOUND_CHANGESET_INVALID` raised by `changesets.py:218-220` on the first
structural operation.

### Why it stayed latent

Every historical green path was single-family or all-canonical:
single-family structural live case → all v0.3 → 0.4 envelope (passes);
the frozen four-family offline case hand-builds v0.3 legacy manifests
(`run_phase12_offline.py:817-835`), bypassing `build_semantic_manifest` for
door/window; older live window UATs ran the legacy workflow with changeset
schema 0.1.  No `add_window` case had ever passed through the current
0.4-binding public path — the mixed-family composite cases were the first to
reach it.

### Boundary evidence (from the failure family)

| Scenario | Manifest versions | Negotiated envelope | Binding |
| --- | --- | --- | --- |
| structural only (C1) | all v0.3 | 0.4 | PASS |
| structural + door (C2) | all v0.3 | 0.4 | PASS |
| window only | all v0.1 (pre-fix) | 0.2 | PASS |
| **structural + window (C3/C4/C5)** | **v0.3 + v0.1** | **0.2** | **FAIL** |

## Fix (mechanism-level, general)

Two changes, both aligning the window family with its siblings instead of
special-casing any test:

1. `src/text2ifc_ifc_repair/operations/window.py` — `_semantic_policy_facts`
   now sets `canonical_source_kind="deterministic_derived"` unconditionally;
   the unused `canonical_occurrence_contract` gate was removed.
2. `src/text2ifc_ifc_repair/semantic_authoring.py` — the `use_v03` scope set
   now includes `"window_occurrence"`.

After the fix a window manifest is v0.3 (canonical vocabulary), so any
mixed-family changeset negotiates the 0.4 envelope where both structural and
window vocabularies are legal.  The 0.2/0.3/0.4 schemas are untouched — raw
and fabricated kinds remain rejected under 0.3/0.4 (covered by negative
tests), so validation is not weakened.

## Frozen failure family

`tests/ifc_repair/test_mixed_manifest_binding.py` (14 tests, red→green):

* positive: beam+window, column+window, three-family, repeated mixed
  operations all bind at the 0.4 envelope;
* boundary: window-only, beam-only, column-only keep binding;
* negative: fabricated / raw legacy source kinds still fail closed under the
  0.4 envelope;
* cross-scene: varied window geometry keeps binding.

## Verification gates run after the fix

* Failure family: 14/14 green (was 9 red / 5 green pre-fix).
* Regression suites (all green): window application + window semantic
  authoring + semantic authoring + changesets (33), occurrence semantics +
  provider stage + property binding (36), structural atomicity + structural
  Stage 2 + door application + mixed hosted atomicity (36).
* Full gates (recorded in the milestone report): phase12 dataset e2e +
  frozen-proof validation, phase12 live UAT (incl. the four production-path
  cases), the R1 summary suites, and the composite evidence suite.

---

# DEFECT RECORD 2 — Door semantic-role L1 authorization gap (FIXED)

**Found:** 2026-08-31, during the offline full-chain verification of the C5
hero case (8 operations + 2 property intents on `vvo.ifc`), after Defect 1
was fixed.
**Fixed:** 2026-08-31, same day, same user authorization (mechanism-level,
general repair).

## Symptom

C5 ran the full public chain — Stage 1, Stage 1.5 property resolution, Stage
2 binding, apply — but ended `not_publishable`: the whole-model L1 scope
gate rejected two created entities:

```
[created] IfcPropertySet          15Eil9pG1Tcum_GHPJn1kG
[created] IfcRelDefinesByProperties 0oPCdotLvRPedD_MOL8r2S
  -> "Registry policy does not authorize this role/class/effect"
```

Both entities were created by the **door operation's own semantic authoring**
with roles `semantic_door_pset` / `semantic_door_pset_relationship` (the
FireRating property intent on the generated door).

## Root cause

An operation's L1 authorization must cover the full effect space its own
semantic authoring can produce.  The semantic authoring rewrites role names
per occurrence scope (`semantic_authoring.py:1203-1219
_scoped_semantic_role`: `door_occurrence` → prefix `semantic_door_`), and:

* beam/column authorize their family-scoped roles
  (`evaluation_policy.py:402 structural_l1_authorization`:
  `semantic_{family}_pset/quantities/material/classification` + indexed
  variants 2-64 + relation authorizations);
* window authorizes `semantic_pset` + `semantic_opening_quantities`
  (`operations/window.py:246 WINDOW_L1_AUTHORIZATION`);
* **door authorized only door/fills/type/opening/voids roles** — its L2
  policy even declares `door.pset` as a conditional fact
  (`operations/door.py:237`), so L2 expected psets while L1 rejected them.

Latent for the same reason as Defect 1: no prior case ever put a property
intent on a *created* door (R1 door property cases used the separate
`set_occurrence_properties` operation on existing doors).

## Fix (mechanism-level)

`operations/door.py::_l1_authorization` now authorizes the
`semantic_door_*` role family (pset / pset_relationship / quantities /
quantity_relationship / material_relationship / classification_relationship,
plus indexed variants 2-64 and matching relation authorizations with
`added_endpoint_roles=("door",)`), and — like the window operation, since the
add path creates an opening — `semantic_opening_quantities` /
`semantic_opening_quantity_relationship`.  The exact role/class contract is
unchanged: fabricated roles and wrong classes stay unauthorized.

## Frozen failure family

`tests/ifc_repair/test_door_property_authorization.py` (7 tests):

* mechanism: every `semantic_door_*` role is authorized for both add and
  fill variants; opening-scoped quantities authorized;
* boundary: indexed multi-pset variants 2-64 (65 excluded);
* consistency: the door role set mirrors the structural pattern modulo the
  family prefix (family-drift guard);
* negative: fabricated roles / wrong classes remain unauthorized.

## Verification gates run after the fix

* Failure family: 7/7 green.
* Door regressions: `test_door_application.py`,
  `test_door_resolution.py`, `test_door_geometry_regression.py`,
  `test_mixed_hosted_operation_atomicity.py` — 41/41 green.
* C5 hero case: full public-API chain green (Stage 1 → 1.5 → 2 → apply →
  publication → strict reopen → operation-bound proof → exact-delta
  preservation).

---



# DEFECT RECORDS 3-5 — Live-Provider revealed contract defects (ALL FIXED)

**Found:** 2026-08-31, by re-auditing the genuine DeepSeek live outcomes
(C2-C5) after the user challenged why four positive composite cases ended in
failure without a debug loop.  All three were localized on the frozen live
artifacts, verified programmatically, classified, fixed mechanism-level, and
re-gated before any live retry.  The original failed live attempts remain
preserved unchanged in the proof pack.

## Diagnosis summary

| Case | Terminal status | Failing stage | Root cause | Class |
|---|---|---|---|---|
| C2 / C4 | `clarification_required` (`DOOR_OPERATION_REQUIRED`) | Stage 1.5 door resolution | Published contract taught an output the resolver rejects | Prompt/contract expression defect |
| C3 | `provider_failed` (`DRAFT_AUTHORITY_SCOPE_MISMATCH`) | Stage 2 draft authority check | Ordered strict equality on set-valued fields | Deterministic implementation bug |
| C5 | `clarification_required` (`not_found`) | Target resolution | `tolerance_mm: 0` vs float-precision geometry | Prompt/contract expression defect |

## DEFECT 3 — Door enum contract unreachable as published (C2/C4, FIXED)

**Symptom.** Live DeepSeek correctly extracted the user's explicit
`SINGLE_SWING_LEFT`/`SINGLE_SWING_RIGHT` into
`parameters.door.operation_type` — exactly the shape the published
`door-add-v0.2-complete` few-shot teaches — yet every door operation ended in
`DOOR_OPERATION_REQUIRED` clarification asking for
`operation_type/hinge_side/viewpoint`, which the request had already
answered.

**Root cause (verified on frozen artifacts).**
`door_resolution.py:716-718` accepts an enum direct-pass only when
`door.formal_enum_explicit is true`.  That flag appears nowhere in any
public contract: not in the intent-body schema, not in the door v0.2
profiles' `conditional_slots`/`forbidden_inferences`, not in any published
few-shot (`door-add-v0.2-complete.json` teaches the bare enum).  The only
green paths historically were a hand-authored offline fixture (which wrote
the internal flag directly) and one live batch where the model happened to
emit the flag untaught.  The published contract's own teaching was therefore
deterministically rejected — an unreachable contract path.

**Fix (mechanism-level).** Published the full conditional contract as
`door.add-with-opening.v0.3` / `door.fill-existing-opening.v0.3` (new
registered profile versions; v0.2 files untouched), whose slot contract
teaches: enum + `door.formal_enum_explicit: true`, OR `hinge_side` +
`viewpoint`.  The four v0.3 few-shots per family mirror this.  `door.py`
now selects the v0.3 profiles.  The resolver itself is unchanged — enums
without confirmation still clarify (the safety boundary did not move; the
contract now teaches the reachable path).

**Frozen failure family.** `tests/ifc_repair/test_published_contract_reachability.py`
(23 tests): every published v0.3 few-shot teaching an enum teaches the
confirmation; the profiles are registered and selected; contract-shaped
payloads resolve for add and fill; boundary unchanged (bare enum still
clarifies, unsupported enums still fail closed, the flag alone authorizes
nothing).

## DEFECT 4 — Draft-authority set fields compared with order sensitivity (C3, FIXED)

**Symptom.** C3 Stage 2 draft rejected twice with
`DRAFT_AUTHORITY_SCOPE_MISMATCH` although the draft contained exactly the
authorized identifiers.

**Root cause (verified programmatically on the frozen attempt).** The
deterministic authority builds `scope.target_ids` / `evidence_refs` as
`sorted(set(...))` (`provider_stage.py:365-382`) and the draft schema
declares them `uniqueItems: true`, but `_require_exact_draft_authority`
compared them with strict ordered list equality (`changesets.py:241`).  The
Provider returned the same two identifiers in operation order
(storey, wall) instead of sorted order (wall, storey) — set-equal,
order-different, rejected.  The correction feedback named only the error
code, never the expected value, so the retry could not converge.  C1 passed
only because a single target has no ordering freedom.

**Fix (mechanism-level).** `changesets.py` now compares these collections
with set semantics (`_identifier_set_equal`: recursive over scope mapping,
order-insensitive with strict length check for lists).  Identifier drift,
duplication, shape change, and every operation-level mismatch still fail
closed.

**Frozen failure family.** `tests/ifc_repair/test_draft_authority_set_semantics.py`
(10 tests: 4 reordering positives including the exact C3 shape, plus
scope-extra/missing/duplicate and evidence-extra/missing/duplicate
negatives).

## DEFECT 5 — Zero-tolerance geometry contract vs float-precision IFC (C5, FIXED)

**Symptom.** C5 door and window wall target queries resolved `not_found`
although the walls exist and match the request to three decimals.

**Root cause (measured on the C5 input index).** The two walls measure
`3581.70079330354` mm (height) and `-2213.70079330354` mm (elevation);
the request (and the frozen case) state `3581.7` / `-2213.701`.  The live
Stage 1 copied those rounded values with `tolerance_mm: 0`, so
`abs(actual - value) <= 0` fails at a 0.0008 mm delta.  Nothing in the
published contract warned that stored IFC geometry carries sub-millimetre
float precision and that `tolerance_mm: 0` can never match a rounded user
value.  (The offline fixture passes only because it hand-writes
`tolerance_mm: 1.0` defaults.)

**Fix (mechanism-level, contract publication).** Both v0.3 door profiles
(and the same rule added to the window profile slot contract — see below)
now state: geometry constraints must use `tolerance_mm >= 1.0`, never 0,
with the reason, and `tolerance_mm of 0` is listed in
`forbidden_inferences`.  The resolver itself is unchanged (a genuinely
exact-value query with tolerance 0 still works and should).

**Frozen failure family.** Covered inside
`test_published_contract_reachability.py` (the profile publication
assertions) plus a measured differential recorded here: the same production
index on `C5/02-input.ifc` resolves both walls once tolerance is >= 1
(the 0.0008 mm delta is recorded above).

## Window profile parity (same rule family)

The window add-with-opening profile shares the geometry-constraint
contract surface, so the tolerance rule was published there as well
(slot contract wording) — the same unreachable-contract class would
otherwise remain one family away.

## Verification gates run after all three fixes

* New failure families: 10/10 + 23/23 green.
* Door resolution/application: 23/23 green; profile/request-stage
  suites green (fixtures updated from v0.2 to v0.3 ids).
* phase12 live UAT: 101/101 green.
* R1 audit + phase12 success cases + prior failure families
  (`test_mixed_manifest_binding`, `test_door_property_authorization`)
  re-run green.
* Composite evidence suite re-run green.
* `compileall` clean; baseline fingerprint updated (authorized-fix
  records for the changed production files and the new prompt assets).


---

# RETRY OUTCOME (2026-08-31, after all gates green + fingerprint CLEAN)

Same-case genuine live retry via `run_composite.py --execute-genuine`
(16 real DeepSeek calls):

| Case | Before fix | After fix |
|---|---|---|
| C1 | succeeded | succeeded (reproduced) |
| C2 | clarification_required / DOOR_OPERATION_REQUIRED | **succeeded** (full publication) |
| C3 | provider_failed / DRAFT_AUTHORITY_SCOPE_MISMATCH ×2 | **succeeded** (bound first try) |
| C4 | clarification_required / DOOR_OPERATION_REQUIRED | not_publishable / window volume-preservation — see below |
| C5 | clarification_required / not_found (tolerance 0) | **succeeded** (8 ops + 2 properties, strict gates pass) |
| C5-N | unsupported | unsupported (reproduced: zero mutation, zero Stage 2) |

C4 is the single remaining failure and is a **frozen-case defect, not a
product defect**: the fixture's window offset was re-frozen to 16000 mm
(solid region) during case freezing, but the frozen request text still says
5000 mm.  The Provider executed the request text and hit the recessed zone
documented in `composite-model-selection.md`; `l1.window.volume-preservation`
failed closed exactly as at freezing time.  The failure is preserved as-is
(the frozen case is not rewritten in place).

Allowed claims per the capability protocol:
* Defects 3-5: **bug fixed** (with frozen failure families and full
  regression gates);
* Retry: **same-case retry reliability evidence** for the repaired
  configuration (C2/C3/C5 now succeed genuinely; revealed cases are
  regression evidence only, not blind improvement evidence);
* No system-capability claim is made from these runs.


---

# DEFECT RECORD 6 — Semantic-bundle claims not propagated to production evidence (FIXED)

**Found:** 2026-09-01, during the C1-C5 damage-restoration live rerun with
property restoration (user-directed strict per-case IFCcompare audit).
**Fixed:** 2026-09-01, same day, mechanism-level under the same authorization
chain as Defects 3-5.

## Symptom

A live Provider expressing restoration properties through
``semantic_bundle_refs`` (a bundle of claims referenced by operations) failed
at production-evidence build with ``AUTHORIZED_PROPERTY_CLAIM_MISMATCH``,
although the property authority itself resolved successfully and was attached
to ``authorized_semantics``.

## Root cause

``resolve_repair_intent`` expands bundle references into the resolution-local
operation copy (``resolution_flow.py`` via ``expand_semantic_bundles``), but
``build_production_evidence`` receives the ORIGINAL intent whose operations
still carry empty ``property_intents`` plus the bundle references.  The
claim-authority matcher (``production_evidence.py``) finds no matching claim
and fails closed.  The bundle form is a published intent-schema feature, so
the whole path was unreachable end to end.

## Fix (mechanism-level)

``request_stage.canonicalize_semantic_bundle_claims`` now inlines bundle
claims into their referencing operations immediately after intent
construction (operation-local values win; bundle order stable; unknown
references remain a hard error; canonical form visible to every downstream
consumer — evidence builder, durable property coordinator, resolution flow).

## Frozen failure family

``tests/ifc_repair/test_semantic_bundle_claim_propagation.py`` (5 tests:
inline canonicalization, local override, natural-language routing, unknown
reference fail-closed, claim-authority matching).

## Verification gates

Failure family 5/5 green; intent v07/v08 + occurrence semantics + property
family E2E + request stage regressions 46/46 green; baseline fingerprint
records the ``request_stage.py`` change under
``semantic-bundle-claim-propagation``; verify CLEAN.

## Related user-audit finding (same session)

The strict per-case audit also found a frozen-case defect: the two sixty5
beams were frozen with storey "03 derde verdieping" while the originals live
on storey "12 twaalfde verdieping" (restored 28.32 m low).  The freeze was
corrected and the ladder re-executed; the audit script
(``composite-evidence-audit/audit_all_cases.py``) now re-verifies storey
identity, world geometry, opening refills, host walls, section orientation
and property loss on every case.
