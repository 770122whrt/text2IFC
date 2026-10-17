# Repository Guidance

## Navigation and working context

- Use `text2IFC` as the project and product name. `bimnet` may be the local
  checkout directory name; `BIMNet` in dataset or manifest context names a
  data source, not the product.
- At first takeover, use `docs/how-to/agent-takeover.md`, `docs/README.md` and the current `.planning/STATE.md` entry. Read relevant SPEC/active PLAN/VALIDATION and code ranges; consult ROADMAP for milestones and PROJECT for durable constraints. Reuse unchanged context; historical reports do not override current instructions.
- Confirm Git root, branch and working-tree state before editing; refresh on relevant changes. Preserve unrelated work. Phase, Proof and run status are separate facts.
- Read and write project-authored text as UTF-8. In PowerShell, pass `-Encoding UTF8` when reading or writing such files, and preserve Chinese text literally rather than passing it through the default Windows code page.

## Execution and Codex allowance

- Execution details live in `docs/how-to/agent-takeover.md` §5. Scripts/schedulers own batches, waits, polling and log summaries. Codex handles completion, exceptions, clarification and phase decisions, not repeated inspection of unchanged status.
- Filter large logs first. Delegate only bounded work with clear benefit and minimal context; avoid unnecessary full-history inheritance.
- Use low/medium for routine work when controls permit, higher effort temporarily for difficult diagnosis. Rules do not switch models; disclose required UI settings and do not edit global model configuration.
- Separate account allowance, optional Goal counters and experiment API budgets. Never transfer an experiment budget to a Goal. Check allowance at phase boundaries; explain the Goal counting basis and ask for a budget only when needed.
- At ≤20% remaining in any known applicable account window, save a checkpoint and report the remaining allowance and current progress to the user. If the user continues the conversation, continue the dialogue and authorized work without requiring a separate resume confirmation; low allowance alone must not block that continuation. Unknown limits are not zero. If an actual platform limit prevents execution, preserve state and report the concrete limitation. Active work follows its cooperative stop/persistence contract; do not kill it or discard records.

## Change and verification contracts

- Use Python compatible with `pyproject.toml`, preferably the repository `.venv`. Behavioral changes are test-first with the narrowest relevant tests, then any broader gates required by the applicable contract. Offline, focused, skipped or timed-out checks do not establish live or repository-wide success.
- Scoped validation is the default. Reuse sufficient passed checks unless a new change, failure or actual risk requires more. A stage preflight is required at first entry or when admission becomes stale; Full / repository-wide Preflight requires a separate explanation of reason and scope and explicit user approval. Missing or stale admission fails closed and does not automatically trigger Full Preflight.
- Do not rewrite registered or released schema, prompt, or prompt-profile versions; add a new version and update the appropriate registry or hash references and focused tests. Treat accepted, committed proof and run evidence as append-only: do not relabel or silently replace it. Active ignored experiment or UAT workspaces are outside this rule until curated and committed.
- In IFC repair flows, never mutate the source IFC in place. Provider and other public production inputs must exclude the pristine pre-damage benchmark IFC, private Gold, mutation recipes or mappings, deleted identities, and facts derived only from those private sources; introduce them only after repair for evaluation. Synthetic, cached, prerecorded, or hand-authored results must not be reported as live-Provider evidence.

## Agent debugging, capability evaluation, and live-LLM admission

- For Agent/LLM behavior, prompt/schema changes, diagnosis, capability claims or real calls, follow `docs/validation/agent-capability-evaluation.md`. Read relevant sections before acting; phase contracts may strengthen, not weaken it.
- Before product fixes, preserve a red-capable reproduction, localize stage/invariant and freeze positive, negative, boundary and cross-scene siblings (§2). Critical safety fixes may be immediate; one green case is not class-level improvement.
- Capability claims require the protocol's frozen Baseline/Candidate comparison (§3): failures in the denominator, fixed/shared evaluator, group-isolated unseen cases, slices/uncertainty, non-regression and zero-tolerance safety gates. Tests and accepted Proof are not capability metrics.
- Live calls require valid stage admission and every applicable §4 seam/full public API/CLI offline gate. Within an admitted stage, revalidate changed/directly affected paths; failed checks or invalid admission block live calls.
- Live calls show viability/reliability, not system improvement. Preserve every genuine failure. Deterministic live defects return to offline diagnosis and failure-family validation; a revealed case cannot become blind improvement evidence after a fix.

## Proof presentation and proportionate validation

- Follow `docs/validation/ifc-repair-proof-format.md` for accepted IFC repair evidence. Make the human path primary: each accepted case exposes a readable `REPORT.md`, the public `request.txt`, `damaged.ifc`, and either a directly visible `repaired.ifc` or an explicit `NO-REPAIR.md`. Keep full Provider/runtime/Proof detail in its append-only machine authority and link to it from the case.
- Include `original.ifc` only when its role was legitimately established before evaluation, and declare that role explicitly. Never relabel a shared pristine file as case-specific private Ground Truth after seeing the repair.
- Navigation/report edits use focused checks; new human views require layout/reopen/role checks. Production, live acceptance, accepted installation, schema and evidence changes retain their applicable gates. Full curator is required for accepted installation/re-curation, curator/schema/evidence semantics changes or an explicit release contract, not routine iteration; it does not replace diagnosis, independent Proof or human review.
- Risk-proportional validation must never weaken safety or evidence contracts. Missing repaired outputs, repaired files in no-output guards, source mutation, unoffered identities, inadmissible properties, unclear original roles, broken authority paths, or failed applicable Proof gates remain blocking failures.
- Keep one current human results entry linked to machine authority and history. Update each fact at its owning entry; other indexes link there. Do not generate synonymous reports or repeated archives, or copy the same changing totals across documents.

## Proof navigation

- Human Proof entry: `dataset/processed/proof/README.md`; workflow/phase/collection directories are stable across review status changes.
- Approved consolidated packages keep frozen evidence bytes in workflow/phase/collection directories. Their manifest maps legacy paths to current files; do not rewrite frozen evidence or move it again during ordinary presentation maintenance.
- New human views use `scripts/proof/validate_human_views.py`; legacy validators keep their original schema contracts.
