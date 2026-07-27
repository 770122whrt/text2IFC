# IFC2X3 repair implementation reuse map

> Status: implementation baseline
> Date: 2026-07-17
> Design authority: [`design.md`](design.md)

This map records which existing repository components are reused by the IFC
repair workflow and which responsibilities require a new IFC-native module. It
does not change the contracts in the design authority.

## Confirmed public test seams

Tests exercise behavior through these boundaries:

1. case preparation: source IFC plus mutation recipe to immutable case artifacts;
2. public projection and compact context: private manifest to allowlisted Provider input;
3. IFC repair ChangeSet: JSON document to stable validation diagnostics;
4. operation registry and audit: registered semantic operations to structured evidence;
5. transactional application: audited ChangeSet plus `damaged.ifc` to published `repaired.ifc`;
6. comparison: source, damaged and repaired IFC artifacts to an evaluation report;
7. Provider run: public prompt inputs to parsed predicted ChangeSet and trace evidence.

Internal IFC entity construction helpers are not independent test seams.

## Reuse decisions

| Responsibility | Existing component | Decision |
|---|---|---|
| JSON Schema validation and stable issue shape | `text2ifc_agent.changesets`, `text2ifc_contract.validation.ValidationIssue` | Reuse the validation pattern and issue vocabulary. Create a sibling IFC-repair schema because the base authority is an IFC file rather than a Formal BIM JSON candidate. |
| Base binding and deterministic hashing | `text2ifc_agent.revisions`, `text2ifc_agent.candidate_index` | Reuse canonical hashing ideas. Add byte-level SHA-256 binding for the authoritative IFC artifact. |
| Scope, transaction and preservation governance | `text2ifc_agent.changeset_apply`, `text2ifc_agent.change_scope` | Reuse the governance model and report concepts. Do not reuse the BIM JSON applicator, which validates and mutates a complete candidate document. |
| Prompt identity and rendering | `text2ifc_agent.prompt_registry` and `prompts/agent/registry.json` | Reuse directly after adding a versioned IFC-repair prompt asset and hash entry. |
| Fake, file and live Provider adapters | `text2ifc_agent.providers` | Reuse the Provider boundary and low-level IFC-output guardrail. The repair runner supplies only public artifacts. |
| Live Provider evidence | `text2ifc_agent.live_trace` | Reuse redacted request/response/event trace writing. Add repair-specific artifact manifest and private-input exclusion evidence around it. |
| IFC opening/fill relationship extraction | `text2ifc_extractor.relationships` | Reuse relationship vocabulary and endpoint conventions where applicable. IFC-native inspection remains authoritative. |
| IFC placement and geometry interpretation | `text2ifc_extractor.placement`, `text2ifc_extractor.geometry`, `text2ifc_compiler.verification` | Reuse unit, placement and geometry measurement helpers when their imported-IFC assumptions hold; add straight-wall classification and wall-local basis logic in the repair package. |
| IFC geometry, relationship and identity creation | `text2ifc_compiler.geometry`, `text2ifc_compiler.relationships`, `text2ifc_compiler.identity` | Refactor or reuse small helpers that safely accept an existing IFC model. Do not call the full compiler or rebuild the model. |
| IFC reopen and geometry checks | `text2ifc_compiler.verification` and IfcOpenShell 0.8.5 | Reuse reopen/shape measurement patterns; add operation-specific semantic checks. |
| Atomic artifact writes | `text2ifc_text.splits.atomic_write_text`, existing `os.replace` patterns | Reuse for JSON/text artifacts. IFC publication uses a temporary sibling file, reopen verification and atomic replace. |
| Dataset provenance | `dataset/manifests/external-corpora.json`, `dataset/manifests/raw-files.jsonl` | Add one hash-bound raw-file entry authorizing evaluation use while preserving `training_eligible: false`. |

## New IFC-native responsibilities

The following belong under `src/text2ifc_ifc_repair/` because no existing
component has the correct imported-IFC contract:

- deterministic `remove_window_and_opening` mutation and private manifest;
- explicit private-to-public allowlist projection;
- operation-aware, budgeted IFC repair context;
- shared IFC repair ChangeSet envelope and heterogeneous operation registry;
- common audit dispatcher with structured evidence;
- straight-wall Window operation handler;
- transactional incremental IFC application;
- normalized IFC preservation snapshot and operation-specific comparison;
- deterministic case runner and fake-provider end-to-end orchestration.

## Frozen dependency facts

- Python: repository contract requires 3.12 or newer.
- IfcOpenShell: `0.8.5` from `requirements.txt`, verified in the workspace.
- JSON Schema: Draft 2020-12 through `jsonschema>=4.19,<5`.
- First source artifact SHA-256:
  `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`.
- First source artifact size: `1,292,595` bytes.

## Non-reuse decisions

- Do not serialize the complete imported IFC to BIM JSON for the Provider.
- Do not pass the repaired model through the full BIM JSON compiler.
- Do not import Window-specific code from common registry, audit, apply or
  compare modules.
- Do not treat fake Provider output or a private gold ChangeSet as real UAT.
