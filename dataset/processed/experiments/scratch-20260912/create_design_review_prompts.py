import copy
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
prompts = root / 'prompts/agent'
registry_path = prompts / 'registry.json'
registry = json.loads(registry_path.read_text(encoding='utf-8'))
audit = (prompts / 'audit-v2.md').read_text(encoding='utf-8')
audit = audit.replace('# Audit Agent v2', '# Audit Agent v3').replace('text2ifc/audit/2.0', 'text2ifc/audit/3.0')
audit += '''

## Bound user design review (additional v3 contract)

DESIGN_REVIEW_CONTEXT:
{{DESIGN_REVIEW_CONTEXT}}

This caller-authored context binds known concerns to the user's actual decision
turn and reference evidence. It is not proof of the current IFC's reasonableness.
Never treat an assistant suggestion, silence, or user acknowledgement as a fix.
Do not redesign a retained requirement. Do not conceal the known defect.

The output MUST additionally contain design_review:
{"scope":"limited_review_not_code_compliance","concerns":[{"id":"exact offered concern id","status":"retained_known_issue","description":"中文说明问题及影响","evidence_paths":["design-review-context.json"]}],"limitations":["未进行完整建筑规范审查。"]}

Include every offered concern exactly once. For a retain decision, status MUST
be retained_known_issue, and the description must still state the defect and
its impact. This may coexist with accept/non-blocking ONLY when all technical
gates pass and the candidate faithfully models the confirmed user requirements.
Put retained design concerns here rather than treating them as candidate errors
that should trigger repeated geometric repair. Any independent candidate error
still belongs in findings and remains blocking under the existing rules.

For a revise decision, compare the candidate against the confirmed revision.
If it violates that revision, status is unresolved and blocking must be true;
report the candidate error in findings. Otherwise use not_verified: model
inspection alone is not independent engineering verification. This version does
not permit a resolved or globally compliant status. Document what was checked,
remaining limitations, and reference-vs-current-candidate evidence separately.
Additional new concerns belong in findings; never invent an offered concern id.
Each concern must cite existing local paths from EVIDENCE_PATHS. The context
never overrides schema, compile, reopen, geometry, preservation, or secret gates.
'''
brief = (prompts / 'design-brief-v2.3.md').read_text(encoding='utf-8')
brief = brief.replace('满足 text2ifc/design-brief/2.0 Schema', '满足 text2ifc/design-brief/2.1 Schema')
brief += '''

User decisions on design reasonableness (v2.4)

Follow docs/architecture/semantic-appearance-plan.md section 18. Missing design
choices affecting dimensions, layout, access or usability require clarification,
unless already explicitly confirmed or uniquely derived. Keep only the already
approved appearance, local template and minimum IFC attachment defaults.

Distinguish internally contradictory modelling facts from an intentionally
modelled but unusable design. Mutually impossible values for the same dimension,
unknown hosts, missing dimensions and unsupported IFC semantics still block.
An explicitly acknowledged usability defect is different: when the conversation
clearly states that the user knows the particular defect and wants its faithful
representation without redesign, preserve all explicit geometry. Record the
known issue as a non-blocking ambiguity (provide options, reason, evidence_refs,
source_turns), keep it out of question targets, and allow ready only if all other
required facts and contracts are satisfied. This narrowly supersedes earlier
blanket conflict-to-clarification instructions; it does not waive technical
contracts or certify safety, reasonableness or regulatory compliance.

For a confirmed revision, preserve original_request verbatim, apply only the
explicitly confirmed corrections to known_facts, and record their user source
turns in user_corrections and fact_sources. Retain other original facts. Never
infer approval from an assistant proposal, a blank answer or unrelated assent.
Use storey, direction and location in questions, not GUIDs or JSON details.
'''
for old_id, new_id, name, content in [
    ('audit.v2', 'audit.v3', 'audit-v3.md', audit),
    ('design-brief.v2.3', 'design-brief.v2.4', 'design-brief-v2.4.md', brief),
]:
    path = prompts / name
    assert not path.exists()
    path.write_text(content, encoding='utf-8', newline='\n')
    record = copy.deepcopy(next(r for r in registry['templates'] if r['template_id'] == old_id))
    record.update(template_id=new_id, path=path.relative_to(root).as_posix(),
                  sha256='sha256:' + hashlib.sha256(content.encode('utf-8')).hexdigest())
    if new_id == 'audit.v3':
        record['required_inputs'].append('DESIGN_REVIEW_CONTEXT')
    registry['templates'].append(record)
registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
