# Human-readable IFC Proof collections

**Status:** Proposed for implementation after user review
**Scope:** Repair Milestone R1 and Phase 12.1 Plan 07 evidence presentation

## Goal

Make accepted repair evidence understandable and navigable by a person without
opening machine manifests or searching inside `runtime/runs/.../.terminal-bundles`.
The existing accepted machine packages remain immutable evidence authorities.

## Design principles

1. Human reports are the primary navigation surface.
2. Each case exposes its request and relevant IFC files at the case root.
3. Existing curated/raw evidence is not moved, relabelled, or overwritten.
4. Missing `original.ifc` or `repaired.ifc` is explained, never synthesized.
5. Routine validation is proportional to the failure mechanisms introduced by
   the change. Full curator execution is reserved for evidence installation,
   evidence-schema or curator changes, and explicit release audits.

## Collection layout

```text
dataset/processed/proof/
├── repair-milestone-r1/
│   ├── README.md
│   ├── REPORT.md
│   ├── accepted-cases/
│   │   ├── E1/
│   │   │   ├── REPORT.md
│   │   │   ├── request.txt
│   │   │   ├── damaged.ifc
│   │   │   ├── repaired.ifc
│   │   │   └── evidence/
│   │   ├── ...
│   │   └── H4/
│   │       ├── REPORT.md
│   │       ├── request.txt
│   │       ├── damaged.ifc
│   │       ├── NO-REPAIR.md
│   │       └── evidence/
│   └── r1-20260902T152701658266Z-curated/  # machine authority, unchanged
└── phase12-plan07-final/
    ├── README.md
    ├── REPORT.md
    ├── accepted-cases/
    │   ├── complete/
    │   ├── clarification-resume/
    │   ├── window-semantic-canary/
    │   └── program-guard/
    └── uat-20260902T180900748385Z/         # machine/raw authority, unchanged
```

## Case-root contract

Every case root contains only the files a reviewer should see first:

- `REPORT.md`: concise purpose, requested change, outcome, provider call counts,
  L0/L1/L2 or no-output result, evidence boundary, and links to detail;
- `request.txt`: the actual frozen repair request;
- `damaged.ifc`: the IFC received by the repair pipeline;
- `repaired.ifc`: the published repaired IFC for a successful repair;
- `original.ifc`: only where a pre-existing original is legitimate and useful;
- `NO-REPAIR.md`: required instead of `repaired.ifc` for an intentional guard.

Clarification cases may additionally expose `initial-request.txt` and
`clarification-answer.txt` because they are direct human inputs.

## Detailed evidence

`evidence/` keeps compact, review-relevant material rather than duplicating an
entire runtime tree:

- `manifest.json`: case identity, outcome class, IFC roles, and relative links
  to the immutable machine authority;
- `application.json`, `evaluation.json`, and `terminal.json` where applicable;
- `provider-result.json` and `production-boundary.json`;
- `README.md` explaining where the complete provider attempts, prompts, state
  transitions, staging IFC, and raw runtime are retained.

All copied IFC files and compact JSON evidence are byte-identical to their
authority sources. The human collection does not become a second curator or a
replacement acceptance authority.

## R1 evidence semantics

- E1-E4, M1-M3, H1-H3, and A1 expose `damaged.ifc -> repaired.ifc`.
- H4 exposes `damaged.ifc -> NO-REPAIR.md`; absence of repaired output is the
  accepted safety result.
- R1 does not expose `original.ifc`, because its diversity cases have no
  predeclared private pristine/mutation truth. IFCCompare remains N/A.

## Plan 07 evidence semantics

- `complete` and `clarification-resume` expose the pre-existing physical
  original/damaged/repaired files and clearly state that private triplet-audit
  publishability is N/A.
- `window-semantic-canary` exposes damaged/repaired only. A shared pristine
  fixture is not relabelled as case-specific Gold.
- `program-guard` exposes damaged plus `NO-REPAIR.md` and no repaired IFC.

## Human reports

Each collection receives a root `REPORT.md` with:

- an executive conclusion;
- a one-row-per-case matrix with direct repaired-IFC links;
- explicit explanation for H4/program-guard and missing private triplets;
- validation totals and known limitations;
- links to the machine authority for forensic inspection.

The root `dataset/processed/proof/README.md` links these two human collections
before the machine inventories.

## Risk-proportional validation

A small human-layout validator checks only plausible packaging failures:

1. required request/report files exist;
2. expected successful cases expose a non-empty IFC that reopens;
3. guard cases do not expose `repaired.ifc` and include `NO-REPAIR.md`;
4. authority links resolve;
5. IFC roles do not claim a private original where none is lawful.

It does not rehash or recurate every retained runtime artifact. Full curator
validation is triggered only by a new accepted installation, curator/schema
changes, changes affecting evidence semantics, or an explicit release audit.
Behavioral code changes continue to run their relevant failure-family and
end-to-end gates.

## Guidance updates

`AGENTS.md` will require human-first Proof presentation and risk-triggered
validation while retaining fail-closed acceptance boundaries. A memory update
note will record the same preference: do not use broad curator runs as routine
ceremony; validate the mechanisms that can plausibly regress.

## Delivery

Implementation will be committed separately from prior machine evidence,
validated with the focused layout checker plus IFC reopen checks, pushed to the
existing Draft PR, and only then will the PR be updated and merged to `main`.
