import collections
import hashlib
import json
from pathlib import Path
import ifcopenshell

base = Path(__file__).resolve().parents[1]/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
for branch in ('A-revise', 'B-retain'):
    folder = base/branch
    p = folder/'generated.ifc'
    m = ifcopenshell.open(str(p))
    types = m.by_type('IfcTypeObject')
    rels = m.by_type('IfcRelDefinesByType')
    by_instance = collections.defaultdict(list)
    for r in rels:
        for e in r.RelatedObjects:
            by_instance[e.id()].append(r.RelatingType)
    checks = {
        'only_minimum_four_door_styles': len(types)==4 and all(t.is_a('IfcDoorStyle') for t in types),
        'type_family_pairing': all(r.RelatingType.is_a('IfcDoorStyle') and all(e.is_a('IfcDoor') for e in r.RelatedObjects) for r in rels),
        'one_effective_type_per_door': all(len(by_instance[e.id()])==1 for e in m.by_type('IfcDoor')),
        'no_unsolicited_shared_type_groups': all(len(r.RelatedObjects)==1 for r in rels),
        'no_type_materials': all(not getattr(t, 'HasAssociations', ()) for t in types),
        'no_type_properties': all(not getattr(t, 'HasPropertySets', ()) for t in types),
    }
    result = dict(status='passed' if all(checks.values()) else 'failed', checks=checks,
        basis='Supplemental native IFC relationship inspection; no Agent self-report. Frozen 290-check evaluator unchanged.',
        ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        type_counts=dict(collections.Counter(t.is_a() for t in types)),
        instance_count=len(by_instance))
    with (folder/'independent-type-checks.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    assert result['status']=='passed', result
    print(branch, result['type_counts'], '6 supplemental checks passed')
