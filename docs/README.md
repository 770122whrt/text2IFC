# Documentation Index

Use this page as the stable entry point for project documentation.

## How-to Guides

- [Publish the text2IFC Repository to GitHub](how-to/publish-to-github.md)
  - Normal push workflow
  - Git LFS rules for IFC, PDF, and ZIP files
  - Windows authentication and upload failure recovery

## Architecture

- [text2IFC Architecture Overview](architecture/text2ifc-overview.md)
  - Target pipeline
  - Current repository capabilities
  - GSD phase boundaries
- [Phase 2.5 BIM JSON 2.0 IFC Semantic Graph Summary](architecture/phase-2-5-summary.md)
  - Completed semantic graph foundation
  - Verified IFC2X3 extraction and compilation boundary
  - Phase 3 handoff constraints
- [Phase 3 Text-to-JSON Dataset and Baseline Summary](architecture/phase-3-summary.md)
  - Scene-family split, formal gold targets, pair counts, baseline, evaluator,
    and E2E demo
- [Text-to-JSON RAG, Fine-tune, and Agent Decision](architecture/text2json-rag-finetune-decision.md)
  - Metric-backed routing for RAG, fine-tuning, multi-turn Agent, and Phase 4
    fidelity work
- [Phase 4 High-fidelity IFC Round Trip Summary](architecture/phase-4-summary.md)
  - Generated IFC correctness gate, all-25 fidelity accounting, and Phase 6
    readiness boundary
- [Phase 5 Multi-turn Clarification Agent Summary](architecture/phase-5-summary.md)
  - Chinese-first clarification Agent, provider boundary, and simple-room IFC
    artifact
- [Phase 6 Multi-agent Design](architecture/phase-6-multiagent-design.md)
  - Prompt registry, Design Brief Agent, BIM JSON Generator, repair mode,
    Audit Agent, and Observer Loop
- [Phase 6 Acceptance and Trace Report](architecture/phase-6-acceptance-and-trace-report.md)
  - Final acceptance criteria, intermediate input/output artifacts, gates, and
    stop-and-report rules
- [Phase 6 phase-local acceptance report](../.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-ACCEPTANCE-TRACE-REPORT.md)
  - Same Phase 6 acceptance topic placed inside the Phase 6 planning folder for
    faster review

## Project Planning

- [Project context](../.planning/PROJECT.md)
- [Requirements](../.planning/REQUIREMENTS.md)
- [Roadmap](../.planning/ROADMAP.md)
- [Current state](../.planning/STATE.md)
- [Phase 1 specification](../.planning/phases/01-bim-json-1-0-contract-and-validator/01-SPEC.md)
- [Phase 1 implementation context](../.planning/phases/01-bim-json-1-0-contract-and-validator/01-CONTEXT.md)
- [Phase 1 research](../.planning/phases/01-bim-json-1-0-contract-and-validator/01-RESEARCH.md)
- [Phase 1 validation strategy](../.planning/phases/01-bim-json-1-0-contract-and-validator/01-VALIDATION.md)
- Phase artifacts live under `.planning/phases/NN-phase-name/`.

## Data and Methodology

- [BIM JSON 1.0 contract reference](reference/bim-json-1.0.md)
- [BIM JSON 2.0 semantic contract reference](reference/bim-json-2.0.md)
- [IFC2X3 generation profile](reference/ifc2x3-generation-profile.md)
- [IFC2X3 knowledge sources and no-fabrication policy](reference/ifc2x3-knowledge-sources.md)
- [Dataset organization](../dataset/data_organization.md)
- [External data source catalog](../dataset/sources/CATALOG.md)
- [Dataset manifest format](../dataset/manifests/README.md)
- [Authorized BIMNet IFC2X3 manifest](../dataset/manifests/bimnet-ifc2x3.jsonl)
- [BIMNet extraction audit](../dataset/processed/bim-json-2.0/extraction-audit.json)
- [BIMNet scene families](../dataset/processed/bim-json-2.0/scene-families.json)
- [Existing methodology notes](methodology.md)
- [IFC2X3 TC1 EXPRESS schema](../schemas/ifc/IFC2X3_TC1.exp)
- [Phase 2.5 BIM JSON 2.0 specification](../.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-SPEC.md)
- [Phase 2.5 implementation context](../.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-CONTEXT.md)

## Document Placement Rules

| Document type | Location |
|---|---|
| Task-oriented instructions | `docs/how-to/` |
| Architecture and design explanation | `docs/architecture/` |
| Dataset reference | `dataset/` |
| GSD project memory | `.planning/` |
| Phase specification and plans | `.planning/phases/NN-phase-name/` |

Add every durable project document to this index.
