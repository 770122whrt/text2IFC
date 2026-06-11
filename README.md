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

Phase 1 establishes the stable contract boundary:

```text
BIM JSON 1.0 -> validation -> field-level diagnostics
```

The minimum IFC2X3 compiler is Phase 2. Text-to-JSON is Phase 3, followed by
high-fidelity IFC generation, the clarification agent, and model deployment.
