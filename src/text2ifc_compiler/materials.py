"""Explicit material attachments, created per object without name-based merging."""
from ifcopenshell.api.material.add_material import add_material
from ifcopenshell.api.material.add_material_set import add_material_set
from ifcopenshell.api.material.add_layer import add_layer
from ifcopenshell.api.material.assign_material import assign_material


def apply_material_assignment(model, entity, assignment):
    kind = assignment["kind"]
    if kind == "single_material":
        assign_material(model, products=[entity], type="IfcMaterial", material=add_material(model, name=assignment["name"]))
        return
    if kind == "material_list":
        # Preserve the source sequence and multiplicity. These are not layers,
        # and same-named entries are not merged into a shared material identity.
        material = model.create_entity("IfcMaterialList", Materials=[
            add_material(model, name=item["name"]) for item in assignment["materials"]])
        assign_material(model, products=[entity], type="IfcMaterialList", material=material)
        return
    layers = add_material_set(model, name=assignment["layer_set_name"], set_type="IfcMaterialLayerSet")
    for data in assignment["layers"]:
        layer = add_layer(model, layer_set=layers, material=add_material(model, name=data["name"]))
        layer.LayerThickness = float(data["thickness"])
    if kind == "material_layer_set":
        assign_material(model, products=[entity], type="IfcMaterialLayerSet", material=layers)
        return
    assign_material(model, products=[entity], type="IfcMaterialLayerSetUsage", material=layers)
    usage = next(r.RelatingMaterial for r in entity.HasAssociations if r.is_a("IfcRelAssociatesMaterial"))
    usage.LayerSetDirection = assignment["direction"]
    usage.DirectionSense = assignment["direction_sense"]
    usage.OffsetFromReferenceLine = float(assignment["offset_from_reference_line"])
