# text2IFC

text2IFC is a research project for generating valid IFC building models from
natural-language requirements. The working architecture uses a validated BIM
JSON representation between language understanding and IFC generation.

## Start Here

- [First-time Agent and maintainer takeover guide](docs/how-to/agent-takeover.md)
- [Documentation index](docs/README.md)
- [Current execution state](.planning/STATE.md)
- [Foundational architecture and phase history](docs/architecture/text2ifc-overview.md)
- [GitHub publishing guide](docs/how-to/publish-to-github.md)
- [GSD project context](.planning/PROJECT.md)
- [Roadmap](.planning/ROADMAP.md)

## Proof and repository layout

- [Generation and repair Proof](dataset/processed/proof/README.md)
- [Repository slimming proposal](docs/architecture/repository-organization-refactor.md)

## Core Generation Workflow

The project's primary product path is Text -> BIM JSON -> IFC. A DB-backed
Design Brief loop clarifies the user's intent, deterministic code derives
Expected Facts, and a Provider produces a schema-bound BIM JSON candidate.
The candidate must pass semantic coverage, deterministic compilation/reopen
and geometry gates, Audit, and final acceptance before its IFC is accepted.

Generation currently has two explicit strategies: `legacy_full` is the public
CLI default and asks the Generator for one complete document; `staged` builds a
deterministic hierarchy skeleton and composes bounded storey-local and
cross-storey ChangeSets. The system does not select `staged` automatically.

- [Generation workflow and data flow through Phase 6.5](docs/architecture/current-workflow-and-data-flow.md)
- [First-time takeover guide and code map](docs/how-to/agent-takeover.md)
- [BIM JSON 2.0 contract](docs/reference/bim-json-2.0.md)

## Recently Delivered Repair Workflow

Alongside new-model generation, the recently closed repair engineering line
modifies an existing IFC2X3 model from a public natural-language request. The
Provider proposes intent and a bounded ChangeSet;
deterministic code resolves IFC identities, applies one atomic transaction,
reopens the candidate, and publishes it only after the applicable L0/L1/L2 and
preservation gates pass.

- [IFC repair architecture and roadmap](docs/architecture/ifc-repair-pipeline-status-and-roadmap.md)
- [Phase 12 Plan 07 human Proof review](dataset/processed/proof/repair/phase12/plan07-v2/REPORT.md)
- [Phase 12 Plan 07 closeout handover](docs/handoffs/phase12-plan07-closeout-handover-2026-09-03.md)
- [IFC repair Proof presentation standard](docs/validation/ifc-repair-proof-format.md)

The Plan 07 human review bundle is intentionally separate from its append-only
machine authority. Repair Milestone R1 has its own evidence collection and is
not folded into the Plan 07 review manifest.
