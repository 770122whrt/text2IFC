# Repository Guidance

## First-time project takeover

- Use `text2IFC` as the project and product name. `bimnet` may be the local
  checkout directory name; `BIMNet` in dataset or manifest context names a
  data source, not the product.
- Before non-trivial work, read `docs/how-to/agent-takeover.md`, then use
  `docs/README.md` as the documentation entry point.
- Use `.planning/STATE.md` for the current execution position,
  `.planning/ROADMAP.md` for milestone and phase status, and
  `.planning/PROJECT.md` for durable project constraints rather than current
  progress.
- For phase-scoped work, read the applicable SPEC, active PLAN and VALIDATION.
  For Agent/LLM behavior or any real Provider call, read
  `docs/validation/agent-capability-evaluation.md` before acting.
- Before editing, confirm the Git root, branch and working-tree state. Preserve
  unrelated work, and keep phase status, Proof-collection status and individual
  run status as separate facts.

## Authority and navigation

- When project context, architecture, planning, or document placement matters, start with `docs/README.md`. Use `.planning/PROJECT.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md` for project constraints, milestone context, and current execution state. For phase-scoped work, follow the applicable SPEC, active PLAN(s), and VALIDATION artifacts when present. Treat reports and completed or superseded plans as historical evidence, not current execution instructions.
- Read and write project-authored text as UTF-8. In PowerShell, pass `-Encoding UTF8` when reading or writing such files, and preserve Chinese text literally rather than passing it through the default Windows code page.

## Change and verification contracts

- Use a Python version compatible with `pyproject.toml`, preferring the repository `.venv` when available. For behavioral changes, work test-first and run the narrowest relevant pytest target during iteration; then run the broader gates required by the applicable plan or validation contract. Do not claim live-Provider or repository-wide success from an offline, focused, skipped, or timed-out run.
- Use three validation levels instead of repeatedly escalating every change: scoped validation is the default for ordinary iteration; a stage-scoped preflight is required when first entering a new execution stage or when that stage's admission has become stale; repository-wide or otherwise Full Preflight is a separate escalation that requires explaining the reason and scope to the user and receiving explicit approval before it is run. Missing or stale admission must fail closed and must not automatically trigger Full Preflight.
- Do not rewrite registered or released schema, prompt, or prompt-profile versions; add a new version and update the appropriate registry or hash references and focused tests. Treat accepted, committed proof and run evidence as append-only: do not relabel or silently replace it. Active ignored experiment or UAT workspaces are outside this rule until curated and committed.
- In IFC repair flows, never mutate the source IFC in place. Provider and other public production inputs must exclude the pristine pre-damage benchmark IFC, private Gold, mutation recipes or mappings, deleted identities, and facts derived only from those private sources; introduce them only after repair for evaluation. Synthetic, cached, prerecorded, or hand-authored results must not be reported as live-Provider evidence.

## Agent debugging, capability evaluation, and live-LLM admission

- For any Agent/LLM behavioral change, prompt or schema change, failure diagnosis, capability claim, or real-Provider run, first read and follow `docs/validation/agent-capability-evaluation.md`. It is the cross-phase protocol; an active SPEC/PLAN/VALIDATION may add stricter requirements but must not weaken it.
- A single failing example becoming green proves only that example's bug is fixed. Before changing product behavior, preserve a red-capable reproduction, localize the failing stage and violated invariant, and freeze a related failure family with sibling positive, negative, boundary, and cross-scene cases. Critical one-off safety bugs may be fixed immediately, but must not be reported as class-level or system-level capability improvement without the broader evidence required by the protocol.
- Claim class-level or system-level improvement only from a frozen Baseline-versus-Candidate comparison that includes failures in the denominator, keeps the evaluator fixed or re-scores both sides with the same evaluator, uses group-isolated unseen cases, reports capability slices and uncertainty, and passes non-regression plus zero-tolerance safety gates. Regression tests and accepted Proof artifacts are necessary evidence, not capability metrics.
- Before any real LLM/Provider call, require a valid admission for the current execution stage. On first entry to that stage, build the admission from stage-seam tests plus the complete public API/CLI path offline with deterministic fake or frozen-replay Provider behavior, covering complete, clarification/resume, ambiguous or unsupported, malformed/truncated Provider output, deterministic binding, apply/compile, atomic rollback, source immutability, private-Gold isolation, reopen, L0/L1/L2/preservation, terminal publication, and relevant persistence/recovery behavior. Later ordinary fixes within the same admitted stage use scoped revalidation of the changed and directly affected paths rather than automatically repeating the full stage preflight. Any failed applicable check blocks the live call; a missing or stale admission blocks without silently launching Full Preflight.
- A live call is viability or reliability evidence only; it does not replace offline stage/full-chain testing or by itself prove capability improvement. Preserve every genuine failed attempt. If live execution exposes a deterministic defect, return to the offline debug and failure-family loop before another acceptance attempt; do not patch against the revealed case and reuse that same case as blind improvement evidence.

## Proof presentation and proportionate validation

- Follow `docs/validation/ifc-repair-proof-format.md` for accepted IFC repair evidence. Make the human path primary: each accepted case exposes a readable `REPORT.md`, the public `request.txt`, `damaged.ifc`, and either a directly visible `repaired.ifc` or an explicit `NO-REPAIR.md`. Keep full Provider/runtime/Proof detail in its append-only machine authority and link to it from the case.
- Include `original.ifc` only when its role was legitimately established before evaluation, and declare that role explicitly. Never relabel a shared pristine file as case-specific private Ground Truth after seeing the repair.
- Choose validation from the plausible failure introduced by the change. Report or navigation-only edits do not require a universal curator pass. A new human view requires the focused layout/reopen/role checks; production behavior, live acceptance, accepted installation, schema or evidence-semantic changes still require their applicable stronger gates.
- Run the full curator when installing or re-curating an accepted run, changing curator/schema/evidence semantics, or when an applicable frozen release contract explicitly requires it. Do not use curator frequency as a substitute for focused diagnosis, independent Proof, or human review.
- Risk-proportional validation must never weaken safety or evidence contracts. Missing repaired outputs, repaired files in no-output guards, source mutation, unoffered identities, inadmissible properties, unclear original roles, broken authority paths, or failed applicable Proof gates remain blocking failures.
