# Plan 12.1-07 Stage 1.5 Post-Fix Six-Failure Evidence Dossier

## Experiment context

- Evaluation run: `post-fix-semantic-20260828T092301205242Z`
- Evidence root: `dataset/processed/ifc-repair-runs/phase12-1-semantic-evaluation/post-fix-semantic-20260828T092301205242Z`
- Evaluation label: `POST_FIX_STAGE15_ACCEPTANCE_EVALUATION`
- Semantic contract: `text2ifc/property-semantic-taxonomy/0.2`
- Prompt: `ifc-property-resolution.v0.2`
- Provider/model: `deepseek-openai-compatible` / `deepseek-v4-flash`
- Retrieval runtime: production BGE-M3 (`BAAI-bge-m3-local/phase12.1`) and Qdrant collection `ifc2x3-property-vector/0.2`
- Total cases: 60
- Strict result: 54/60
- False authorization: 0
- Frozen Stage 1.5 semantic acceptance: **FAILED**
- Failed cases: `n05`, `p12w04`, `p12d04`, `p12m04`, `p12b04`, `p12c04`

> This document does not change the frozen gates or evaluation result. It only
> reconstructs the six failed cases for subsequent review.

The prediction ledger records `prediction_frozen_before_gold=true`; the semantic
report records `gold_opened_after_prediction_persistence=true` and
`ifc_publication_attempted=false`.

## Summary matrix

| case_id | family | Original query | Value | Frozen Gold category | Expected candidate/property | authorize | Retrieval outcome | Provider invoked? | Provider decision | Selected candidate/property | Admissibility outcome | Final actual route | Strict mismatch | Execution authorized? | False authorization? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `n05` | Door | `未知门属性` | `"x"` | `unsupported_unknown_property` → `unsupported` | `null` in fixture | `false` | Top-K persisted, 2 offered | Yes | `clarification_required` | none | not reached; terminal clarification envelope persisted | `property_resolution` → clarification | Expected unsupported; actual clarification | No | No |
| `p12w04` | Window | `窗的防火等级` | `true` | `incompatible_value` → `inadmissible` | `null` in fixture | `false` | Top-K persisted, 3 offered | Yes | `clarification_required` | none | not reached; terminal clarification envelope persisted | `property_resolution` → clarification | Expected deterministic inadmissible; actual clarification | No | No |
| `p12d04` | Door | `door fire rating` | `true` | `incompatible_value` → `inadmissible` | `null` in fixture | `false` | Top-K persisted, 5 offered | Yes | `clarification_required` | none | not reached; terminal clarification envelope persisted | `property_resolution` → clarification | Expected deterministic inadmissible; actual clarification | No | No |
| `p12m04` | Wall | `wall acoustic performance flag` | `true` | `underspecified_supported_property` → `clarification_required` | `null` in fixture | `false` | Top-K persisted, 5 offered | Yes | `unsupported` | none | not reached; terminal unsupported envelope persisted | `property_resolution` → unsupported | Expected clarification; actual unsupported | No | No |
| `p12b04` | Beam | `beam reference code` | `42` | `incompatible_value` → `inadmissible` | `null` in fixture | `false` | Top-K persisted empty | No | not invoked | none | not run | `not_invoked_no_candidates` → unsupported | Expected deterministic inadmissible; actual unsupported after empty Top-K | No | No |
| `p12c04` | Column | `column load bearing` | `"yes"` | `incompatible_value` → `inadmissible` | `null` in fixture | `false` | Top-K persisted, 5 offered | Yes | `unsupported` | none | not reached; terminal unsupported envelope persisted | `property_resolution` → unsupported | Expected deterministic inadmissible; actual unsupported | No | No |

All five Provider calls used the same decision schema,
`text2ifc/ifc-property-rerank-decision/0.1`, with exactly three terminal decision
types: `confirmed`, `clarification_required`, and `unsupported`. They used
`deepseek-v4-flash`, `thinking={"type":"enabled"}`, and `temperature=0`; the
Provider metadata records that temperature was not effective in thinking mode.

## Case `n05`

### A. Original benchmark input

- Case ID: `n05`
- IFC family/class: Door / `IfcDoor`
- Phrase: `未知门属性`
- Requested value: `"x"` (`raw_value_kind=string`)
- Unit: `null`
- Operation/scope: `set_occurrence_properties` / `occurrence_direct`
- Group or role metadata: not recorded in the originating fixture
- Frozen Gold category/route: `unsupported_unknown_property` / `unsupported`
- Frozen Gold property: `null`
- `authorize`: `false`

Fixture input and Gold are separate from the later Provider output. The public
query supplied to the prediction phase did not include Gold, expected route, or
`authorize`.

### B. Retrieval stage

- Runtime artifact: candidate set persisted using BGE-M3/Qdrant production
  collection metadata.
- Retrieval invoked: yes.
- Top-K size / empty: 2 / no.
- Threshold or pre-filter details: not recorded in the case artifact.
- Gold expected candidate offered: not applicable; the fixture records
  `expected=null`.

| Rank | Candidate ID | Pset | Property | Score | Applicable class | Offered |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `candidate:1:ifc2x3:Pset_DoorCommon.Reference` | `Pset_DoorCommon` | `Reference` | 0.5235990854 | `IfcDoor` | Yes |
| 2 | `candidate:2:ifc2x3:Pset_DoorCommon.FireRating` | `Pset_DoorCommon` | `FireRating` | 0.4678144091 | `IfcDoor` | Yes |

### C. Stage 1.5 Provider input

The case-specific public query in the rendered prompt was:

```json
{"operation_type":"set_occurrence_properties","property_phrase":"未知门属性","raw_unit":null,"raw_value":"x","raw_value_kind":"string","scope":"occurrence_direct","target_ifc_class":"IfcDoor"}
```

The complete two-candidate set shown above was visible to the Provider. The
rendered prompt required `confirmed` only for one uniquely and directly supported
offered candidate, `clarification_required` for a potentially repairable but
underspecified request, and `unsupported` only when clarification could not
resolve the request. Full prompt evidence is linked under Traceability.

- Template: `ifc-property-resolution.v0.2`
- Template hash: `sha256:cb184d74d316dc441868c8266cccfe6ca06b5eb7598f99c693a8647564d4d0df`
- Model: `deepseek-v4-flash`
- Thinking: `enabled`
- Temperature: 0, recorded as ineffective

### D. Raw Provider output

The persisted response text and parsed response contained the same decision:

```json
{
  "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
  "decision": "clarification_required",
  "selected_candidate_id": null,
  "conflicting_candidate_ids": [
    "candidate:1:ifc2x3:Pset_DoorCommon.Reference",
    "candidate:2:ifc2x3:Pset_DoorCommon.FireRating"
  ],
  "clarification_question": "Your request 'unknown door property' is ambiguous. Which door property do you want to set: Reference or FireRating?"
}
```

- Decision type: `clarification_required`
- Selected candidate: none
- Attempts/retries: 1 / 0
- Token usage: 2,016 prompt + 603 completion = 2,619 total
- Latency: 4,053.5337 ms
- Large transport and reasoning metadata is omitted here; it remains in the raw
  response artifact.

### E. Deterministic admissibility

`not reached`

Because Stage 1.5 returned clarification, no candidate was selected and the
deterministic offered-set, authoritative-record, IFC-class, value-type, unit,
scope, retrieval-floor, or scalar-template checks were executed. The persisted
admissibility envelope records `status=clarification_required` and
`reason_code=PROPERTY_RERANKER_CLARIFICATION`; its false check fields must not be
read as individual failed checks.

### F. Final system outcome

- Actual route/outcome: `property_resolution` / clarification
- Authorized: no
- `ExactPropertyIntent`: not created; no candidate was selected or admitted
- Stage 2 reachable: no; this evaluation-only runner does not run Stage 2
- IFC edit: none; publication was not attempted for the run
- Evaluator classification: clarification
- Frozen expected route: unsupported
- Strict failure reason: terminal route mismatch, clarification versus
  unsupported

### G. Evidence-based observation

The Provider treated an unknown door-property phrase as a potentially
clarifiable choice between the two offered candidates. Frozen Gold required the
terminal unsupported route. The request remained safely unexecuted and did not
produce false authorization.

### Traceability

- Fixture: `tests/fixtures/knowledge/phase10_2_property_retrieval.json`
- Taxonomy: `tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json`
- Query: `cases/n05/public-query.json`
- Retrieval: `cases/n05/offered-top-k.json`
- Prompt: `cases/n05/provider/attempt-001/rendered-prompt.txt`
- Raw/parsed Provider output: `cases/n05/provider/attempt-001/raw-response.json`, `cases/n05/provider/attempt-001/parsed-response.json`
- Provider metadata: `cases/n05/provider/attempt-001/provider-metadata.json`
- Admissibility envelope: `cases/n05/admissibility.json`
- Prediction: `cases/n05/prediction.json`
- Run ledger/report: `prediction-ledger.json`, `semantic-evaluation-report.json`

Case-relative run artifacts above are under the evidence root recorded in the
experiment context.

## Case `p12w04`

### A. Original benchmark input

- Case ID: `p12w04`
- Group/role/family: `window-fire-rating-wrong-value` / boundary / Window
- IFC class: `IfcWindow`
- Phrase: `窗的防火等级`
- Requested value: `true` (`raw_value_kind=boolean`)
- Unit: `null`
- Operation/scope: `set_occurrence_properties` / `occurrence_direct`
- Frozen Gold category/route: `incompatible_value` / `inadmissible`
- Frozen Gold property: `null`
- `authorize`: `false`

### B. Retrieval stage

- Retrieval invoked: yes.
- Top-K size / empty: 3 / no.
- Threshold or pre-filter details: not recorded in the case artifact.
- Gold expected candidate offered: not applicable; the fixture records
  `expected=null`.

| Rank | Candidate ID | Pset | Property | Score | Applicable class | Offered |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `candidate:1:ifc2x3:Pset_WindowCommon.SmokeStop` | `Pset_WindowCommon` | `SmokeStop` | 0.5029681967 | `IfcWindow` | Yes |
| 2 | `candidate:2:ifc2x3:Pset_FireRatingProperties.IsCombustible` | `Pset_FireRatingProperties` | `IsCombustible` | 0.4942274440 | `IfcElement`, `IfcSpatialStructureElement` | Yes |
| 3 | `candidate:3:ifc2x3:Pset_WindowCommon.IsExternal` | `Pset_WindowCommon` | `IsExternal` | 0.4894022772 | `IfcWindow` | Yes |

### C. Stage 1.5 Provider input

```json
{"operation_type":"set_occurrence_properties","property_phrase":"窗的防火等级","raw_unit":null,"raw_value":true,"raw_value_kind":"boolean","scope":"occurrence_direct","target_ifc_class":"IfcWindow"}
```

The complete three-candidate table above and the common three-option decision
schema were visible in the actual rendered prompt.

- Template/hash: `ifc-property-resolution.v0.2` / `sha256:cb184d74d316dc441868c8266cccfe6ca06b5eb7598f99c693a8647564d4d0df`
- Model/thinking: `deepseek-v4-flash` / enabled
- Temperature: 0, recorded as ineffective

### D. Raw Provider output

```json
{
  "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
  "decision": "clarification_required",
  "selected_candidate_id": null,
  "conflicting_candidate_ids": [
    "candidate:2:ifc2x3:Pset_FireRatingProperties.IsCombustible"
  ],
  "clarification_question": "窗的防火等级通常指耐火极限或防火等级，但候选属性中没有直接对应的FireRating属性。您是指可燃性（IsCombustible）吗？"
}
```

- Decision type: `clarification_required`
- Selected candidate: none
- Attempts/retries: 1 / 0
- Token usage: 2,266 prompt + 2,262 completion = 4,528 total
- Latency: 17,546.1737 ms
- Large transport and reasoning metadata is omitted here and retained in the
  raw response artifact.

### E. Deterministic admissibility

`not reached`

The Provider abstained with clarification before value-type or any other
deterministic admissibility check. The terminal envelope records
`status=clarification_required` and
`reason_code=PROPERTY_RERANKER_CLARIFICATION`.

### F. Final system outcome

- Actual route/outcome: `property_resolution` / clarification
- Authorized: no
- `ExactPropertyIntent`: not created
- Stage 2 reachable: no
- IFC edit: none
- Evaluator classification: clarification
- Frozen expected route: inadmissible
- Strict failure reason: Stage 1.5 abstained before the boolean input could reach
  the frozen deterministic inadmissibility route

### G. Evidence-based observation

The Provider asked whether the user meant `IsCombustible`; it did not select or
authorize that candidate. Frozen Gold required deterministic inadmissibility,
so the safe clarification route still counted as a strict mismatch.

### Traceability

- Fixture: `tests/fixtures/knowledge/phase12_1_property_resolution.json`
- Taxonomy: `tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json`
- Query/retrieval: `cases/p12w04/public-query.json`, `cases/p12w04/offered-top-k.json`
- Prompt: `cases/p12w04/provider/attempt-001/rendered-prompt.txt`
- Raw/parsed response: `cases/p12w04/provider/attempt-001/raw-response.json`, `cases/p12w04/provider/attempt-001/parsed-response.json`
- Provider metadata: `cases/p12w04/provider/attempt-001/provider-metadata.json`
- Admissibility/prediction: `cases/p12w04/admissibility.json`, `cases/p12w04/prediction.json`
- Run ledger/report: `prediction-ledger.json`, `semantic-evaluation-report.json`

## Case `p12d04`

### A. Original benchmark input

- Case ID: `p12d04`
- Group/role/family: `door-fire-rating-wrong-value` / boundary / Door
- IFC class: `IfcDoor`
- Phrase: `door fire rating`
- Requested value: `true` (`raw_value_kind=boolean`)
- Unit: `null`
- Operation/scope: `set_occurrence_properties` / `occurrence_direct`
- Frozen Gold category/route: `incompatible_value` / `inadmissible`
- Frozen Gold property: `null`
- `authorize`: `false`

### B. Retrieval stage

- Retrieval invoked: yes.
- Top-K size / empty: 5 / no.
- Threshold or pre-filter details: not recorded in the case artifact.
- Gold expected candidate offered: not applicable; the fixture records
  `expected=null`.

| Rank | Candidate ID | Pset | Property | Score | Applicable class | Offered |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `candidate:1:ifc2x3:Pset_DoorCommon.FireExit` | `Pset_DoorCommon` | `FireExit` | 0.5314332824 | `IfcDoor` | Yes |
| 2 | `candidate:2:ifc2x3:Pset_DoorCommon.SelfClosing` | `Pset_DoorCommon` | `SelfClosing` | 0.5241191126 | `IfcDoor` | Yes |
| 3 | `candidate:3:ifc2x3:Pset_FireRatingProperties.IsCombustible` | `Pset_FireRatingProperties` | `IsCombustible` | 0.5172031294 | `IfcElement`, `IfcSpatialStructureElement` | Yes |
| 4 | `candidate:4:ifc2x3:Pset_DoorCommon.SmokeStop` | `Pset_DoorCommon` | `SmokeStop` | 0.5041038008 | `IfcDoor` | Yes |
| 5 | `candidate:5:ifc2x3:Pset_DoorCommon.IsExternal` | `Pset_DoorCommon` | `IsExternal` | 0.4879960037 | `IfcDoor` | Yes |

### C. Stage 1.5 Provider input

```json
{"operation_type":"set_occurrence_properties","property_phrase":"door fire rating","raw_unit":null,"raw_value":true,"raw_value_kind":"boolean","scope":"occurrence_direct","target_ifc_class":"IfcDoor"}
```

The complete five-candidate table above and the common three-option decision
schema were visible in the rendered prompt.

- Template/hash: `ifc-property-resolution.v0.2` / `sha256:cb184d74d316dc441868c8266cccfe6ca06b5eb7598f99c693a8647564d4d0df`
- Model/thinking: `deepseek-v4-flash` / enabled
- Temperature: 0, recorded as ineffective

### D. Raw Provider output

```json
{
  "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
  "decision": "clarification_required",
  "selected_candidate_id": null,
  "conflicting_candidate_ids": [
    "candidate:1:ifc2x3:Pset_DoorCommon.FireExit",
    "candidate:3:ifc2x3:Pset_FireRatingProperties.IsCombustible"
  ],
  "clarification_question": "Your query 'door fire rating' is ambiguous. Do you mean the door is a FireExit, or that its combustibility (IsCombustible) should be set?"
}
```

- Decision type: `clarification_required`
- Selected candidate: none
- Attempts/retries: 1 / 0
- Token usage: 2,705 prompt + 2,402 completion = 5,107 total
- Latency: 18,287.7162 ms
- Large transport and reasoning metadata is omitted here and retained in the
  raw response artifact.

### E. Deterministic admissibility

`not reached`

No deterministic checks were reached after the Provider returned clarification.
The terminal envelope records `status=clarification_required` and
`reason_code=PROPERTY_RERANKER_CLARIFICATION`.

### F. Final system outcome

- Actual route/outcome: `property_resolution` / clarification
- Authorized: no
- `ExactPropertyIntent`: not created
- Stage 2 reachable: no
- IFC edit: none
- Evaluator classification: clarification
- Frozen expected route: inadmissible
- Strict failure reason: clarification occurred before the incompatible boolean
  value could reach deterministic inadmissibility

### G. Evidence-based observation

The Provider presented `FireExit` and `IsCombustible` as clarification choices
and did not select either. The request was safely unexecuted, but the terminal
route differed from frozen Gold.

### Traceability

- Fixture: `tests/fixtures/knowledge/phase12_1_property_resolution.json`
- Taxonomy: `tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json`
- Query/retrieval: `cases/p12d04/public-query.json`, `cases/p12d04/offered-top-k.json`
- Prompt: `cases/p12d04/provider/attempt-001/rendered-prompt.txt`
- Raw/parsed response: `cases/p12d04/provider/attempt-001/raw-response.json`, `cases/p12d04/provider/attempt-001/parsed-response.json`
- Provider metadata: `cases/p12d04/provider/attempt-001/provider-metadata.json`
- Admissibility/prediction: `cases/p12d04/admissibility.json`, `cases/p12d04/prediction.json`
- Run ledger/report: `prediction-ledger.json`, `semantic-evaluation-report.json`

## Case `p12m04`

### A. Original benchmark input

- Case ID: `p12m04`
- Group/role/family: `wall-unknown-acoustic` / negative / Wall
- IFC class: `IfcWall`
- Phrase: `wall acoustic performance flag`
- Requested value: `true` (`raw_value_kind=boolean`)
- Unit: `null`
- Operation/scope: `set_occurrence_properties` / `occurrence_direct`
- Frozen v0.2 Gold category/route:
  `underspecified_supported_property` / `clarification_required`
- Earlier fixture route: `clarification_or_unsupported`; v0.2 taxonomy froze the
  strict route as clarification
- Frozen Gold property: `null`
- `authorize`: `false`

### B. Retrieval stage

- Retrieval invoked: yes.
- Top-K size / empty: 5 / no.
- Threshold or pre-filter details: not recorded in the case artifact.
- Gold expected candidate offered: not applicable; the fixture records
  `expected=null`.

| Rank | Candidate ID | Pset | Property | Score | Applicable class | Offered |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `candidate:1:ifc2x3:Pset_WallCommon.Compartmentation` | `Pset_WallCommon` | `Compartmentation` | 0.5034102041 | `IfcWall`, `IfcWallStandardCase` | Yes |
| 2 | `candidate:2:ifc2x3:Pset_WallCommon.Combustible` | `Pset_WallCommon` | `Combustible` | 0.4870684674 | `IfcWall`, `IfcWallStandardCase` | Yes |
| 3 | `candidate:3:ifc2x3:Pset_WallCommon.LoadBearing` | `Pset_WallCommon` | `LoadBearing` | 0.4827513057 | `IfcWall`, `IfcWallStandardCase` | Yes |
| 4 | `candidate:4:ifc2x3:Pset_WallCommon.IsExternal` | `Pset_WallCommon` | `IsExternal` | 0.4805418016 | `IfcWall`, `IfcWallStandardCase` | Yes |
| 5 | `candidate:5:ifc2x3:Pset_WallCommon.ExtendToStructure` | `Pset_WallCommon` | `ExtendToStructure` | 0.4604211701 | `IfcWall`, `IfcWallStandardCase` | Yes |

### C. Stage 1.5 Provider input

```json
{"operation_type":"set_occurrence_properties","property_phrase":"wall acoustic performance flag","raw_unit":null,"raw_value":true,"raw_value_kind":"boolean","scope":"occurrence_direct","target_ifc_class":"IfcWall"}
```

The complete five-candidate table above and the common three-option decision
schema were visible in the rendered prompt.

- Template/hash: `ifc-property-resolution.v0.2` / `sha256:cb184d74d316dc441868c8266cccfe6ca06b5eb7598f99c693a8647564d4d0df`
- Model/thinking: `deepseek-v4-flash` / enabled
- Temperature: 0, recorded as ineffective

### D. Raw Provider output

```json
{
  "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
  "decision": "unsupported",
  "selected_candidate_id": null,
  "conflicting_candidate_ids": [],
  "clarification_question": null
}
```

- Decision type: `unsupported`
- Selected candidate: none
- Unsupported reason field: not present in the decision schema; the persisted
  reasoning remains in `raw-response.json`
- Attempts/retries: 1 / 0
- Token usage: 2,714 prompt + 1,189 completion = 3,903 total
- Latency: 8,820.8228 ms

### E. Deterministic admissibility

`not reached`

The Provider returned unsupported without selecting a candidate. The terminal
envelope records `status=unsupported` and
`reason_code=PROPERTY_RERANKER_UNSUPPORTED`; individual deterministic checks
were not reached.

### F. Final system outcome

- Actual route/outcome: `property_resolution` / unsupported
- Authorized: no
- `ExactPropertyIntent`: not created
- Stage 2 reachable: no
- IFC edit: none
- Evaluator classification: unsupported
- Frozen expected route: clarification_required
- Strict failure reason: terminal unsupported versus frozen clarification

### G. Evidence-based observation

The Provider found none of the five offered Wall candidates semantically
applicable and returned unsupported. Frozen v0.2 Gold classified the request as
underspecified but potentially clarifiable. Both routes abstained, and no false
authorization occurred.

### Traceability

- Fixture: `tests/fixtures/knowledge/phase12_1_property_resolution.json`
- Taxonomy: `tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json`
- Query/retrieval: `cases/p12m04/public-query.json`, `cases/p12m04/offered-top-k.json`
- Prompt: `cases/p12m04/provider/attempt-001/rendered-prompt.txt`
- Raw/parsed response: `cases/p12m04/provider/attempt-001/raw-response.json`, `cases/p12m04/provider/attempt-001/parsed-response.json`
- Provider metadata: `cases/p12m04/provider/attempt-001/provider-metadata.json`
- Admissibility/prediction: `cases/p12m04/admissibility.json`, `cases/p12m04/prediction.json`
- Run ledger/report: `prediction-ledger.json`, `semantic-evaluation-report.json`

## Case `p12b04`

### A. Original benchmark input

- Case ID: `p12b04`
- Group/role/family: `beam-reference-wrong-value` / boundary / Beam
- IFC class: `IfcBeam`
- Phrase: `beam reference code`
- Requested value: `42` (`raw_value_kind=integer`)
- Unit: `null`
- Operation/scope: `set_occurrence_properties` / `occurrence_direct`
- Frozen Gold category/route: `incompatible_value` / `inadmissible`
- Frozen Gold property: `null`
- `authorize`: `false`

### B. Retrieval stage

- Retrieval invoked: yes.
- Runtime status: no infrastructure error was recorded.
- Top-K size / empty: 0 / yes.
- Offered candidate IDs/Psets/properties: none.
- Raw candidates before threshold/filtering: not recorded.
- Threshold/filter result: the final candidate set was empty; per-candidate
  rejection details were not recorded.
- Gold expected candidate offered: not applicable; the fixture records
  `expected=null`.

| Rank | Candidate ID | Pset | Property | Score | Applicable class | Offered |
| ---: | --- | --- | --- | ---: | --- | --- |
| — | none | — | — | — | — | No |

### C. Stage 1.5 Provider input

Provider was not invoked because the persisted candidate set was empty. The
prediction records `route=not_invoked_no_candidates`,
`classification=not_invoked`, and
`admissibility_reason_code=PROPERTY_RETRIEVAL_EMPTY`.

There is no rendered prompt, Provider request, or Provider configuration
artifact for this case. The query supplied to retrieval was:

```json
{"operation_type":"set_occurrence_properties","property_phrase":"beam reference code","raw_unit":null,"raw_value":42,"raw_value_kind":"integer","scope":"occurrence_direct","target_ifc_class":"IfcBeam"}
```

### D. Raw Provider output

Not present because Provider was not invoked.

- Attempts/retries: 0 / 0
- Token usage: not recorded
- Latency: 0 ms for the non-invoked Provider stage

### E. Deterministic admissibility

`not reached`

No `admissibility.json` exists for this case. With no offered or selected
candidate, offered-set membership, authoritative equality, class applicability,
value type, unit, scope, retrieval floor, and scalar template were not checked.

### F. Final system outcome

- Actual route/outcome: `not_invoked_no_candidates` / unsupported
- Authorized: no
- `ExactPropertyIntent`: not created
- Stage 2 reachable: no
- IFC edit: none
- Evaluator classification: unsupported
- Frozen expected route: inadmissible
- Strict failure reason: the empty candidate set prevented Stage 1.5 and the
  frozen deterministic inadmissibility path; evaluator terminal outcome was
  unsupported

### G. Evidence-based observation

Retrieval persisted an empty offered set, so Stage 1.5 was not invoked. The case
remained safely unexecuted, but it reached unsupported instead of the frozen
inadmissible route. The semantic report does not classify this case as an
infrastructure failure or false authorization.

### Why was Top-K empty?

- Query: `beam reference code`, target `IfcBeam`, integer value `42`, no unit,
  occurrence scope.
- Retrieval request: recorded in `public-query.json` and repeated above.
- Post-fix candidate set: empty.
- Earlier accepted offline retrieval ledger for the same public case also
  records an empty final candidate set.
- Persisted artifacts elsewhere demonstrate that the corpus can surface
  `Pset_BeamCommon.LoadBearing` and `Pset_BeamCommon.IsExternal`; they do not
  establish which raw candidates, if any, were considered for this query before
  filtering.
- The frozen case fixture records `expected=null`, so it does not designate an
  expected inadmissible property candidate whose presence in the authoritative
  corpus can be checked from Gold.
- Raw pre-threshold candidates, score-floor decisions, value-compatibility
  rejections, and per-candidate filter reasons were not persisted for this case.

Why zero candidates survived: **insufficient evidence to determine from
persisted artifacts**.

The current evidence is therefore insufficient to determine why the expected
deterministic inadmissibility path was not reached without rerunning or adding
new instrumentation, neither of which is part of this task.

### Traceability

- Fixture: `tests/fixtures/knowledge/phase12_1_property_resolution.json`
- Taxonomy: `tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json`
- Query/retrieval: `cases/p12b04/public-query.json`, `cases/p12b04/offered-top-k.json`
- Prediction: `cases/p12b04/prediction.json`
- Run ledger/report: `prediction-ledger.json`, `semantic-evaluation-report.json`
- Earlier persisted retrieval comparison:
  `dataset/processed/ifc-repair-runs/phase12-live/preflight-20260826T130321658243Z/preflight/property-retrieval-evaluation/property-retrieval-ledger.json`
- Prompt, raw response, parsed response, Provider metadata, and admissibility
  artifacts: not present because Stage 1.5 was not invoked

## Case `p12c04`

### A. Original benchmark input

- Case ID: `p12c04`
- Group/role/family: `column-loadbearing-wrong-value` / boundary / Column
- IFC class: `IfcColumn`
- Phrase: `column load bearing`
- Requested value: `"yes"` (`raw_value_kind=string`)
- Unit: `null`
- Operation/scope: `set_occurrence_properties` / `occurrence_direct`
- Frozen Gold category/route: `incompatible_value` / `inadmissible`
- Frozen Gold property: `null`
- `authorize`: `false`

### B. Retrieval stage

- Retrieval invoked: yes.
- Top-K size / empty: 5 / no.
- Threshold or pre-filter details: not recorded in the case artifact.
- Gold expected candidate offered: not applicable; the fixture records
  `expected=null`.

| Rank | Candidate ID | Pset | Property | Score | Applicable class | Offered |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `candidate:1:ifc2x3:Pset_ColumnCommon.Reference` | `Pset_ColumnCommon` | `Reference` | 0.5308372426 | `IfcColumn` | Yes |
| 2 | `candidate:2:ifc2x3:Pset_ColumnCommon.FireRating` | `Pset_ColumnCommon` | `FireRating` | 0.4874320938 | `IfcColumn` | Yes |
| 3 | `candidate:3:ifc2x3:Pset_ReinforcementBarPitchOfColumn.Reference` | `Pset_ReinforcementBarPitchOfColumn` | `Reference` | 0.4842087719 | `IfcColumn` | Yes |
| 4 | `candidate:4:ifc2x3:Pset_QuantityTakeOff.Reference` | `Pset_QuantityTakeOff` | `Reference` | 0.4783702861 | `IfcElement` | Yes |
| 5 | `candidate:5:ifc2x3:Pset_Risk.NatureOfRisk` | `Pset_Risk` | `NatureOfRisk` | 0.4714226177 | `IfcObject` | Yes |

### C. Stage 1.5 Provider input

```json
{"operation_type":"set_occurrence_properties","property_phrase":"column load bearing","raw_unit":null,"raw_value":"yes","raw_value_kind":"string","scope":"occurrence_direct","target_ifc_class":"IfcColumn"}
```

The complete five-candidate table above and the common three-option decision
schema were visible in the rendered prompt.

- Template/hash: `ifc-property-resolution.v0.2` / `sha256:cb184d74d316dc441868c8266cccfe6ca06b5eb7598f99c693a8647564d4d0df`
- Model/thinking: `deepseek-v4-flash` / enabled
- Temperature: 0, recorded as ineffective

### D. Raw Provider output

```json
{
  "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
  "decision": "unsupported",
  "selected_candidate_id": null,
  "conflicting_candidate_ids": [],
  "clarification_question": null
}
```

- Decision type: `unsupported`
- Selected candidate: none
- Unsupported reason field: not present in the decision schema; the persisted
  reasoning remains in `raw-response.json`
- Attempts/retries: 1 / 0
- Token usage: 2,697 prompt + 1,681 completion = 4,378 total
- Latency: 13,056.9197 ms

### E. Deterministic admissibility

`not reached`

The Provider returned unsupported without selecting a candidate. The terminal
envelope records `status=unsupported` and
`reason_code=PROPERTY_RERANKER_UNSUPPORTED`; individual deterministic checks
were not reached.

### F. Final system outcome

- Actual route/outcome: `property_resolution` / unsupported
- Authorized: no
- `ExactPropertyIntent`: not created
- Stage 2 reachable: no
- IFC edit: none
- Evaluator classification: unsupported
- Frozen expected route: inadmissible
- Strict failure reason: the Provider abstained before the string value could
  reach the frozen deterministic inadmissibility route

### G. Evidence-based observation

The offered Top-K contained no `LoadBearing` candidate, and the Provider
returned unsupported without selecting another property. Frozen Gold required
the incompatible value to reach deterministic inadmissibility. No execution or
false authorization occurred.

### Traceability

- Fixture: `tests/fixtures/knowledge/phase12_1_property_resolution.json`
- Taxonomy: `tests/fixtures/knowledge/phase12_1_property_semantic_taxonomy_v0_2.json`
- Query/retrieval: `cases/p12c04/public-query.json`, `cases/p12c04/offered-top-k.json`
- Prompt: `cases/p12c04/provider/attempt-001/rendered-prompt.txt`
- Raw/parsed response: `cases/p12c04/provider/attempt-001/raw-response.json`, `cases/p12c04/provider/attempt-001/parsed-response.json`
- Provider metadata: `cases/p12c04/provider/attempt-001/provider-metadata.json`
- Admissibility/prediction: `cases/p12c04/admissibility.json`, `cases/p12c04/prediction.json`
- Run ledger/report: `prediction-ledger.json`, `semantic-evaluation-report.json`

## Cross-case comparison

| Case | Expected | Actual | Retrieval issue? | Provider semantic mismatch? | Admissibility reached? | Safe abstention? | False authorization? | Main observed difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `n05` | unsupported | clarification | No persisted retrieval error; 2 candidates offered | Yes, relative to frozen route | No | Yes | No | Unknown property was treated as clarifiable |
| `p12w04` | inadmissible | clarification | No persisted retrieval error; expected property is `null` | Provider stopped at clarification | No | Yes | No | Value incompatibility was never deterministically checked |
| `p12d04` | inadmissible | clarification | No persisted retrieval error; expected property is `null` | Provider stopped at clarification | No | Yes | No | Value incompatibility was never deterministically checked |
| `p12m04` | clarification | unsupported | No persisted retrieval error; 5 candidates offered | Yes, strict terminal-route mismatch | No | Yes | No | Potentially clarifiable request was classified unsupported |
| `p12b04` | inadmissible | unsupported | Empty offered Top-K; cause not persisted | Provider not invoked | No | Yes | No | Empty candidate set bypassed Stage 1.5 and deterministic value rejection |
| `p12c04` | inadmissible | unsupported | Offered Top-K lacked `LoadBearing` | Provider stopped at unsupported | No | Yes | No | Value incompatibility was never deterministically checked |

This comparison is descriptive only. It does not define a new acceptance matrix
or alter any frozen gate.

## Appendix: observed v0.1 versus v0.2 failure profile

### v0.1 first pass

- Strict result: 59/60
- False authorization: 1
- Recorded failure: `n06` semantic overreach

### v0.2 post-fix

- Strict result: 54/60
- False authorization: 0
- Recorded failures: six strict route mismatches documented above

The only dimension asserted by this comparison is the recorded change in false
authorization, from one to zero, together with the observed change in strict
route mismatches. It does not reinterpret the v0.2 semantic acceptance, which
remains **FAILED**.
