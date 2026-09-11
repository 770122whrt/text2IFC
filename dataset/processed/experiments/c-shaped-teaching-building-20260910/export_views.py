"""Read-only native IFC meshes for this evaluation's presentation views."""
import hashlib
import json
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


def main():
    source, output = map(Path, sys.argv[1:3])
    output.mkdir(exist_ok=False)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    model = ifcopenshell.open(str(source))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    products = []
    for product in model.by_type('IfcElement'):
        if product.is_a('IfcOpeningElement') or not product.Representation:
            continue
        shape = ifcopenshell.geom.create_shape(settings, product)
        mesh = shape.geometry
        materials = []
        for material in mesh.materials:
            color = material.diffuse
            transparency = material.transparency
            opacity = 1 - transparency if transparency == transparency else 1
            materials.append([color.r(), color.g(), color.b(), opacity])
        products.append(dict(id=product.GlobalId, name=product.Name, kind=product.is_a(),
            verts=list(mesh.verts), faces=list(mesh.faces), materials=materials,
            material_ids=list(mesh.material_ids), template=ifcopenshell.util.element.get_psets(
                product).get('Pset_text2IFCBasicFilling', {}).get('TemplateId')))

    def bounds(product, axis):
        return min(product['verts'][axis::3]), max(product['verts'][axis::3])

    def write(name, selected, note):
        assert selected, name
        (output / (name + '-mesh.json')).write_text(json.dumps(dict(
            source_sha256=source_hash, products=selected, mesh_failures=[], view_note=note),
            ensure_ascii=False), encoding='utf-8')

    write('overall', products, 'All represented physical products; native IFC meshes and colors.')
    cutaway = [p for p in products if bounds(p, 2)[0] < 9.3 - 1e-5 and not (
        p['kind'].startswith('IfcWall') and (bounds(p, 1)[1] <= .201 or bounds(p, 0)[0] >= 12.999))]
    write('cutaway', cutaway, 'Roof and outer south/east walls hidden for inspection; IFC unchanged.')
    ground = [p for p in products if bounds(p, 2)[0] < 3.0 - 1e-5]
    write('ground-plan', ground, 'Only ground-level products shown from above; IFC unchanged.')
    for name, template in [('window-double', 'window-double-vertical'), ('door', 'door-left')]:
        write(name, [p for p in products if p['template'] == template][:1],
              'One actual IFC filling isolated; native mesh and component colors.')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    print(json.dumps(dict(products=len(products), source_sha256=source_hash)))


if __name__ == '__main__':
    main()
