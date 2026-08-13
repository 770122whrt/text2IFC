---
phase: 12-beam-and-column-operations
plan: "13"
subsystem: structural-live-uat-evidence
tags: [ifc2x3, beam, column, live-uat, preflight, transcript, redaction, tdd]

requires:
  - phase: 12-12
    provides: Strict source/hash-bound d7n/vvo offline structural Proof matrix
provides:
  - Six-gate machine-verified preflight before live transport construction
  - Redacted attempt-level Stage 1/2 transcript with correction and resume lineage
  - Explicit live-only evidence mode and zero-call fallback rejection
  - Fixed complete, clarification/resume and program-guard structural live cases
  - Official-DeepSeek/default-SDK transport identity enforcement
  - Real RepairAPI-path and cross-family regression protection
affects: [12-14, 12-15, 12-16]

tech-stack:
  added: []
  patterns:
    - Lazy transport construction after independently parsed preflight evidence
    - Hash-bound redacted request/response transcript per Provider attempt

key-files:
  created:
    - scripts/ifc_repair/run_phase12_live_uat.py
    - tests/ifc_repair/test_phase12_live_uat.py
  modified:
    - src/text2ifc_agent/openai_compat.py
    - src/text2ifc_ifc_repair/api.py
    - src/text2ifc_ifc_repair/registry.py
    - src/text2ifc_ifc_repair/semantic_authoring.py
    - src/text2ifc_ifc_repair/operations/window.py
    - prompts/agent/ifc-repair-profiles/occurrence.set-properties.json
    - prompts/agent/registry.json

key-decisions:
  - "The runner owns all six preflight commands and re-parses offline/proof artifacts; callers cannot authorize transport with a green boolean."
  - "Every logical Provider call is chained by case, Stage, ordinal, correction reason and parent attempt without rewriting malformed output."
  - "Synthetic, cached, prerecorded and hand-authored modes block before preflight or transport construction."

patterns-established:
  - "Preflight evidence binds command argv, exit code, stdout/stderr hashes, semantic artifact hashes and a canonical result hash."
  - "Transcript evidence keeps provider/model/token/profile/few-shot identities while recursively redacting secrets and private-Gold material."

requirements-completed: [OPS-03, OPS-04]

duration: multi-session hardening and primary acceptance
completed: 2026-08-13
---

# Phase 12 Plan 13: Live Transcript, Preflight and No-Fallback Contract Summary

**A live-only structural UAT runner now blocks transport behind six machine-verified gates and retains redacted, hash-bound Stage 1/2 attempt lineage without Provider-output aliases.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-08-11T16:11:37Z
- **Completed:** 2026-08-11T16:27:29Z
- **TDD feature:** 1
- **Files created:** 2

## Accomplishments

- Fixed focused, offline matrix, complete IFC-repair suite, compile, diff and
  independent Proof validation as runner-owned preflight commands. A command
  exit of zero is insufficient for the offline and Proof gates: their JSON
  artifacts are independently parsed and hash-bound.
- Delayed transport construction until every gate passes. Each individual gate
  failure, including an exit-zero forged offline/Proof result, produces
  `transport_calls=0`.
- Recorded each logical Provider attempt with case, Stage, Stage ordinal,
  correction reason, lineage, parent attempt, redacted request/response,
  request/response hashes, provider/model, token usage and prompt
  profile/few-shot identities and hashes.
- Preserved malformed noncanonical Provider output as redacted evidence. The
  runner neither aliases nor canonicalizes it; later attempts are explicit
  validation corrections.
- Added fixed complete, clarification/resume and deterministic program-guard
  live programs, plus independent reopen/L0/L1/L2 recomputation for published
  structural outputs.
- Replaced hand-authored case-result tests with external-transport-only tests
  that drive the real `RepairAPI.start` / clarification-resume / application
  path and reopen the resulting IFC2X3 artifact.
- Froze the complete live matrix text/order and damaged source SHA-256 as
  reviewed literals, required the official DeepSeek HTTPS endpoint, and made
  production eligibility require the provider's default OpenAI SDK client;
  injected/replay clients cannot impersonate live evidence.
- Corrected the generic resolved-target projection without family branches,
  retained the full `authorized_semantics` contract, and kept optional schema
  constants from inventing structural `axis.reference` authority.
- Closed the Phase 12 structural-material cross-family regression: strict
  single-material authority remains limited to Beam/Column scopes, while the
  frozen Window contract still supports exact explicit material labels and a
  bounded set of multiple authorized material relationships through L1 audit.

## TDD Gate Evidence

### RED

- **Commit:** `f86ff29c` — `test(12-13): add failing live transcript contract tests`
- **Command:** `python -m pytest tests/ifc_repair/test_phase12_live_uat.py -q`
- **Observed:** `14 failed in 1.03s`.
- **Expected failure:** every test failed because
  `scripts/ifc_repair/run_phase12_live_uat.py` did not yet exist. There were no
  test syntax, collection or fixture failures.

### GREEN

- **Commit:** `3bbdc0ff` — `feat(12-13): gate and preserve live structural transcripts`
- **Focused result:** `14 passed in 2.09s` after implementation.
- **Final live/provider/profile/window focused result:** `67 passed in 56.82s`.
- **Cross-family real IFC regression result:** `25 passed in 84.73s`.
- **OpenAI-compatible provider regression result:** `31 passed in 1.42s`.
- **Complete IFC-repair suite:** `874 passed, 1 skipped in 1223.37s`.
- **Compile:** target runner and test passed `compileall`.
- **Diff:** repository `git diff --check` passed.
- **Network:** no live CLI, DeepSeek request or other real network transport was
  invoked; all call-count tests used the injected mock transport.

The mandatory RED commit precedes the GREEN commit. No REFACTOR commit was
needed.

## Frozen Mock Call Matrix

| Case | Stage 1 | Stage 2 | Lineage result |
|---|---:|---:|---|
| complete | 2 | 2 | Invalid noncanonical Stage 1 and Stage 2 output retained, then explicit correction attempts |
| clarification/resume | 2 | 1 | Initial Stage 1, bounded answer, resumed Stage 1, then Stage 2 |
| program-guard | 1 | 0 | Stable unsupported terminal result; later calls prohibited |

The aggregate test transcript contains exactly eight logical Provider calls:
five Stage 1 and three Stage 2.

## Preflight Contract

Each check records its exact argv, exit code, status/reason, stdout and stderr
SHA-256, artifact paths/hashes/sizes when present, and a canonical result hash:

1. focused Phase 12 live-runner tests;
2. complete Phase 12 offline matrix with a parsed `matrix_complete=true`
   `run-summary.json`;
3. the complete `tests/ifc_repair` suite;
4. `compileall` over source, tests and scripts;
5. `git diff --check`;
6. independent success-case collection validation with a parsed passed result
   bound to the collection manifest and case count.

Transport construction occurs only after the complete preflight manifest is
green. Synthetic, cached, prerecorded and hand-authored evidence modes are
rejected before even running preflight.

## Redaction and Provider Evidence

- Secret-key, authorization, credential and token-bearing fields use the
  existing Provider redaction path.
- Private/Gold/original/mutation/deleted-object keys and private canary values
  are replaced with `[REDACTED_PRIVATE]`.
- Provider label, model, safe token counters, profile IDs/versions/hashes,
  few-shot IDs/hashes and request/response SHA-256 remain machine-visible.
- Bad structural keys such as `beam_start` and `beam_axis` remain exactly in
  the failed response evidence and never become canonical `axis` fields.

## Task Commits

1. **RED public-seam behavior tests** — `f86ff29c` (`test`)
2. **GREEN preflight-gated transcript runner** — `3bbdc0ff` (`feat`)

## Files Created

- `tests/ifc_repair/test_phase12_live_uat.py` — mock-transport tests for all
  preflight, evidence-mode, redaction, correction and lineage contracts.
- `scripts/ifc_repair/run_phase12_live_uat.py` — live-only structural runner,
  delayed Provider factory, six-gate preflight, attempt transcript and strict
  published-output recomputation.

## Decisions Made

- Preflight authority comes only from commands executed by the runner and
  their recomputed evidence, never from a caller-supplied boolean or cached
  verdict.
- A correction is another visible Provider attempt linked to the rejected
  response; malformed structural keys are not compatibility-normalized.
- Logical Stage calls are counted separately from lower-level connection retry
  metadata so accepted Proof can state both facts without conflation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Allowed an external Proof manifest to be hash-bound**

- **Found during:** GREEN focused verification.
- **Issue:** The first implementation required every evidence artifact to be
  under the preflight directory, but the independently validated Proof
  manifest correctly lives under its separate collection root.
- **Fix:** Preflight-local artifacts retain relative paths; independently
  configured external artifacts retain normalized absolute paths. Both are
  hashed and size-bound identically.
- **Files modified:** `scripts/ifc_repair/run_phase12_live_uat.py`
- **Verification:** focused suite changed from `6 passed / 8 failed` to
  `14 passed`; final combined suite passed 57 tests.
- **Committed in:** `3bbdc0ff`

**2. [Rule 1 - Bug] Bound structural policy targets without losing semantic authority**

- **Found during:** real `RepairAPI` complete/clarification path tests.
- **Issue:** resolved operations carried one generic `target_global_id`, while
  Beam/Column policy facts require the registered `storey_global_id` target;
  reconstructing a narrow operation document would also discard
  `authorized_semantics` and regress Window authoring.
- **Fix:** project the resolved identity through the operation registry's
  single required `*_global_id` contract, starting from the complete resolved
  operation document.
- **Scope:** deterministic program projection only; no Provider-output alias,
  fallback, or compatibility normalization was added.

**3. [Rule 1 - Bug] Preserved frozen Window material semantics**

- **Found during:** full-suite and adversarial Standards review.
- **Issue:** the Phase 12 structural single-material preflight was applied to
  every occurrence scope and rejected valid Window Type cohorts containing
  Glass and Sash. The second Window material relationship also lacked bounded
  L1 role authorization.
- **Fix:** enforce structural material cardinality only for Beam/Column scopes;
  retain exact public-resource or explicit-request material authority for
  Window; authorize Window material relationship roles 2 through 64 and test
  them through real `apply_changeset` audit.
- **Verification:** Window semantic/application, LargeBuilding and five-Window
  VVO regression tests pass; Beam/Column conflict and uniqueness tests remain
  green.

**4. [Rule 1 - Security] Prevented injected clients from impersonating DeepSeek**

- **Found during:** final two-axis review.
- **Issue:** an exact provider class with official DeepSeek labels/URL could
  still contain an injected replay client.
- **Fix:** provider construction records whether the default SDK client was
  used; production live eligibility requires that identity in addition to the
  exact provider/config/HTTPS endpoint checks.
- **Verification:** official endpoint plus injected client is blocked before
  the executor or any transport call.

---

**Total deviations:** 4 auto-fixed issues (3 correctness, 1 security).
**Impact on plan:** All changes are required to make the frozen 12-13 live
contract executable through the real public workflow without weakening
Beam/Column authority or redesigning Door/Window behavior.

## Issues Encountered

- Git emitted a read-only global-ignore warning for
  `C:\Users\rt do believe\.config\git\ignore`; it did not affect staging,
  commits, status, tests or verification.

## Known Stubs

None in the 12-13 runner. The created runner has a real delayed live-Provider
factory and real RepairAPI/strict-reopen execution path; production-path tests
replace only the external Provider transport. Preservation and private-Gold
isolation acceptance remain explicitly `pending_plan_12_14` and cannot be
claimed by the 12-13 result.

## Scope and Security

- Threats T12-02 and T12-14 are addressed by selected-profile capture,
  recursive evidence redaction, live-only mode and zero-call preflight failure.
- No Door/Window workflow, geometry threshold, Ground Truth boundary or
  Storey policy was redesigned. The only Window policy change restores its
  already-frozen exact multi-material relationship contract after a Phase 12
  structural regression.
- No Phase 12-14/15/16 or Phase 13 work was included in this checkpoint.
- OPS-03/OPS-04 are copied from plan frontmatter for traceability; milestone
  closure remains pending real Provider execution and final Phase 12 closure.

## User Setup Required

None for Plan 12-13. Real Provider credentials are intentionally not exercised
by this mock-transport contract plan.

## Next Plan Readiness

Plan 12-13 supplies the transcript/preflight/no-fallback seam needed by later
live Proof work. Final acceptance and any 12-14 continuation remain owned by
the parent orchestrator.

## Self-Check: PASSED

- Both created code/test files and this SUMMARY exist.
- RED `f86ff29c` and GREEN `3bbdc0ff` exist in the required order.
- Fresh final verification passed 874 tests with one documented skip, target
  compile and repository diff checks; final Spec and Standards reviews both
  returned GREEN with no HIGH/MEDIUM findings.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-12*
