# Milestones

## v1.0: Supported Text2IFC Baseline

**Shipped:** 2026-07-16
**Phases:** 15
**Plans:** 94
**Requirement outcomes:** 71 validated, 4 deferred later-scope, 1 accepted
technical debt

### Delivered

- Versioned BIM JSON 1.0 and IFC2X3-aligned BIM JSON 2.0 contracts with
  explicit Draft/loss semantics.
- Deterministic IFC2X3 compilation, reopen verification, spatial/relationship
  Gates, and official-source IFC knowledge.
- Provenance-linked and scene-family-isolated Text/BIM JSON dataset plus a
  structured-output baseline and evaluation harness.
- Chinese-first multi-turn clarification and role-isolated Design Brief,
  Generator, Repair, Audit, and Observer workflow.
- Hash-bound Gate/Audit routing, component-scoped ChangeSets, multi-storey
  support, and unrelated-component preservation at 1.0.
- Real-provider Easy/Medium/Difficult acceptance with machine 3/3 and human
  3/3 IFC review.

### Final Verification

- 722 focused regression tests passed.
- Static compilation passed.
- 7 representative IFC2X3 files reopened successfully.
- Planning artifact secret scan found 0 issues across 292 files.
- Milestone audit passed with zero orphaned requirements.

### Accepted Boundaries

- `CLI-08` successful final true-human REPL UAT is deferred.
- `GEO-03`, `GEO-04`, `GEO-05`, and `IFC-06` remain later scope.
- Three-case acceptance is not a repeated-run statistical claim.
- Generalized stair collision and double-leaf door semantics remain future
  work.

### Archives

- [Roadmap](milestones/v1.0-ROADMAP.md)
- [Requirements](milestones/v1.0-REQUIREMENTS.md)
- [Audit](milestones/v1.0-MILESTONE-AUDIT.md)

**Git tag:** `v1.0`

## 已完成任务说明的本地退役（2026-10-17）

已交付 Generation Phase 01–06.7 的重复 PLAN/SUMMARY/RESEARCH/CONTEXT 和旧 Goal Prompt 合计 218 份已从本地退役，阶段 SPEC、VALIDATION、VERIFICATION、验收记录、问题登记及真实实验依据保留。`05.5-04-SUMMARY.md` 是该阶段唯一总结，`06.4-09-PLAN.md` 承担 SPEC 绑定合同，`06.2-SDK-RESEARCH.md` 承担 SDK 采纳/拒绝条件，三者继续保留。原文按[固定 Git 目录](https://github.com/770122whrt/text2IFC/tree/48f32bba4c1976178a97267a98e569080f44063e/.planning/phases)恢复；此项只精简本地任务说明，不改变上方交付、测试或债务结论。
