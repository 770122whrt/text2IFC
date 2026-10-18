import hashlib
import json
import shutil
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/repair'
result = json.loads((OUT / 'result-live-04.json').read_text(encoding='utf-8'))
authority = OUT / 'runtime-live-04' / result['run_directory'] / result['artifacts']['successful_ifc']
expected = json.loads((OUT / 'evaluator-private/frozen-expectations.json').read_text(encoding='utf-8'))
paths = [OUT / '01-original.ifc', OUT / '02-damaged.ifc', authority]
models = [ifcopenshell.open(str(p)) for p in paths]
guid = expected['target_guid']
def values(model):
    return [{p.Name: {'type': p.NominalValue.is_a(), 'value': p.NominalValue.wrappedValue}
             for p in r.RelatingPropertyDefinition.HasProperties}
            for r in model.by_guid(guid).IsDefinedBy if r.is_a('IfcRelDefinesByProperties')
            and r.RelatingPropertyDefinition.is_a('IfcPropertySet')
            and r.RelatingPropertyDefinition.Name == expected['pset']]
snapshots = [{e.id(): e.to_string() for e in m} for m in models]
base, final = snapshots[1:]
changed = [i for i, s in base.items() if i in final and final[i] != s]
removed = sorted(base.keys() - final.keys())
added = sorted(final.keys() - base.keys())
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
def meshes(model):
    output, errors = {}, []
    for e in model.by_type('IfcElement'):
        if e.is_a('IfcOpeningElement') or not e.Representation:
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, e)
            mesh = shape.geometry
            data = [list(mesh.verts), list(mesh.faces), list(mesh.material_ids),
                    [str(m) for m in mesh.materials]]
            output[e.GlobalId] = hashlib.sha256(json.dumps(data).encode()).hexdigest()
        except Exception as error:
            errors.append({'guid': e.GlobalId, 'error': type(error).__name__})
    return output, errors
geometry = [meshes(m) for m in models]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
observed = [values(m) for m in models]
requested = {k: {'type': 'IfcIdentifier' if isinstance(v, str) else 'IfcBoolean', 'value': v}
             for k, v in expected['properties'].items()}
checks = {
    'schema_ifc2x3': all(m.schema == 'IFC2X3' for m in models),
    'original_hash_frozen': sha(paths[0]) == expected['original_sha256'],
    'damaged_hash_frozen': sha(paths[1]) == expected['damaged_sha256'],
    'dataset_source_immutable': sha(ROOT / 'dataset/external/bimnet/vvo.ifc') == expected['original_sha256'],
    'original_properties_match': observed[0] == [requested],
    'damaged_attachment_absent': observed[1] == [],
    'repaired_direct_properties_match_exact_types': observed[2] == [requested],
    'every_preexisting_step_entity_unchanged': not changed and not removed,
    'all_three_meshes_and_effective_styles_identical': geometry[0][0] == geometry[1][0] == geometry[2][0],
    'all_three_meshes_succeeded': all(not x[1] for x in geometry),
}
report = {'status': 'passed' if all(checks.values()) else 'failed', 'checks': checks,
          'observed_direct_properties': dict(zip(['original', 'damaged', 'repaired'], observed)),
          'authority': authority.relative_to(OUT).as_posix(),
          'sha256': dict(zip(['original', 'damaged', 'repaired'], map(sha, paths))),
          'changed_existing_ids': changed, 'removed_existing_ids': removed,
          'added_entities': [final[i] for i in added],
          'mesh_products_per_file': [len(x[0]) for x in geometry],
          'mesh_errors': [x[1] for x in geometry],
          'limitation': 'Independent verification of one frozen relation-damage case; not a capability metric. Existing public L2 conditional check is not_required and is not relied on for the requested values.'}
(OUT / 'independent-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if all(checks.values()):
    target = OUT / '03-repaired.ifc'
    if target.exists():
        assert sha(target) == sha(authority)
    else:
        shutil.copyfile(authority, target)
print(json.dumps(report, ensure_ascii=False, indent=2))
