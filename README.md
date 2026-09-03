# text2IFC

text2IFC is a research project for generating valid IFC building models from
natural-language requirements. The working architecture uses a validated BIM
JSON representation between language understanding and IFC generation.

## Start Here

- [Documentation index](docs/README.md)
- [Project architecture](docs/architecture/text2ifc-overview.md)
- [GitHub publishing guide](docs/how-to/publish-to-github.md)
- [GSD project context](.planning/PROJECT.md)
- [Roadmap](.planning/ROADMAP.md)

## Current Focus

The active engineering line repairs an existing IFC2X3 model from a public
natural-language request. The Provider proposes intent and a bounded ChangeSet;
deterministic code resolves IFC identities, applies one atomic transaction,
reopens the candidate, and publishes it only after the applicable L0/L1/L2 and
preservation gates pass.

- [IFC repair architecture and roadmap](docs/architecture/ifc-repair-pipeline-status-and-roadmap.md)
- [Phase 12 Plan 07 human Proof review](dataset/processed/proof/ifc-repair-success-cases/PLAN07-REPORT.md)
- [Phase 12 Plan 07 closeout handover](docs/handoffs/phase12-plan07-closeout-handover-2026-09-03.md)
- [IFC repair Proof presentation standard](docs/validation/ifc-repair-proof-format.md)

The Plan 07 human review bundle is intentionally separate from its append-only
machine authority. Repair Milestone R1 has its own evidence collection and is
not folded into the Plan 07 review manifest.
