"""Read actual IFC semantics independently of Agent coverage labels and writer APIs."""
from pathlib import Path
import json
import math
from typing import Any, Mapping, Sequence

import ifcopenshell
import ifcopenshell.util.element as element

from .verification import IfcValidationIssue


def _model(value):
    return ifcopenshell.open(str(value)) if isinstance(value, (str, Path)) else value


def _identity(entity):
    return element.get_psets(entity, should_inherit=False).get("Pset_text2IFCIdentity", {}).get("BimJsonId")


def _index(model):
    result = {}
    for entity in model.by_type("IfcObjectDefinition"):
        identity = _identity(entity)
        if identity:
            result.setdefault(identity, []).append(entity)
    return result


def material_value(material):
    if material is None:
        return None
    if material.is_a("IfcMaterial"):
        return {"kind": "single_material", "name": material.Name}
    if material.is_a("IfcMaterialList"):
        return {"kind": "material_list", "materials": [{"name": item.Name} for item in material.Materials]}
    usage = material.is_a("IfcMaterialLayerSetUsage")
    layer_set = material.ForLayerSet if usage else material
    if not layer_set.is_a("IfcMaterialLayerSet"):
        return {"kind": material.is_a()}
    value = {"kind": "material_layer_set_usage" if usage else "material_layer_set", "layer_set_name": layer_set.LayerSetName, "layers": [{"name": layer.Material.Name if layer.Material else None, "thickness": layer.LayerThickness} for layer in layer_set.MaterialLayers]}
    if usage:
        value.update(direction=material.LayerSetDirection, direction_sense=material.DirectionSense, offset_from_reference_line=material.OffsetFromReferenceLine)
    return value


def _types(entity):
    return [r.RelatingType for r in getattr(entity, "IsDefinedBy", ()) if r.is_a("IfcRelDefinesByType")]


def _properties(entity, inherit=False):
    return {name: {k: v for k, v in values.items() if k != "id"} for name, values in element.get_psets(entity, should_inherit=inherit).items() if name != "Pset_text2IFCIdentity"}


def _available_filling_depth(entity):
    """Read available symmetric depth from actual opening/host solids and placements."""
    import numpy as np
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    opening = entity.FillsVoids[0].RelatingOpeningElement
    host = opening.VoidsElements[0].RelatingBuildingElement
    fill_world = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
    depths = []
    for product in (opening, host):
        items = [item for shape in product.Representation.Representations if shape.RepresentationIdentifier == 'Body' for item in shape.Items]
        solid = items[0]
        if len(items) != 1 or not solid.is_a('IfcExtrudedAreaSolid') or not solid.SweptArea.is_a('IfcRectangleProfileDef'):
            raise ValueError('Unsupported host or opening for a basic filling.')
        local = np.linalg.inv(ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)) @ fill_world
        depths.append(float(solid.SweptArea.YDim) - 2 * abs(local[1, 3]))
    return min(depths) * ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000


def verify_semantic_expectations(ifc_file_or_path, expectations: Sequence[Mapping[str, Any]]) -> tuple[IfcValidationIssue, ...]:
    """Compare frozen request entries; absent:true checks absence, not null equality."""
    indexed = _index(_model(ifc_file_or_path))
    issues = []
    for expected in expectations:
        entity_id = expected.get("entity_id", "")
        kind = expected.get("kind", "")
        actual = None
        present = False
        matches = indexed.get(entity_id, [])
        reason = None
        if len(matches) != 1:
            reason = "Expected exactly one IFC entity with this BIM JSON identity."
        else:
            entity = matches[0]
            scope = expected.get("scope", "effective")
            types = _types(entity)
            if len(types) > 1:
                reason = "More than one effective Type relationship."
            if scope == "inherited":
                entity = types[0] if len(types) == 1 else None
            if scope not in {"direct", "effective", "inherited"}:
                reason = "Unknown semantic expectation scope."
            if kind == "type":
                actual = _identity(types[0]) if len(types) == 1 else None
            elif kind == "material":
                if entity and len([r for r in getattr(entity, "HasAssociations", ())
                                   if r.is_a("IfcRelAssociatesMaterial")]) > 1:
                    reason = "More than one material association on the object."
                actual = material_value(element.get_material(entity, should_inherit=scope == "effective")) if entity else None
                if entity and entity.is_a("IfcWallStandardCase") and expected.get("value", {}).get("kind") == "single_material" and actual and actual.get("kind") == "material_layer_set_usage" and len(actual["layers"]) == 1:
                    actual = {"kind": "single_material", "name": actual["layers"][0]["name"]}
            elif kind == "property":
                values = _properties(entity, scope == "effective").get(expected.get("pset"), {}) if entity else {}
                present = expected.get("property") in values
                actual = values.get(expected.get("property"))
            elif kind == 'appearance':
                from text2ifc_presentation import item_appearance_signatures
                wanted = expected.get('value', {})
                representation = getattr(entity, 'Representation', None)
                items = [item for shape in representation.Representations if shape.RepresentationIdentifier == 'Body' for item in shape.Items] if representation else []
                signatures = [item_appearance_signatures(item) for item in items]
                actual = signatures
                channels = dict(zip(('red','green','blue'), wanted.get('color', [])))
                if 'transparency' in wanted:
                    channels['transparency'] = wanted['transparency']
                colour_valid = 'color' not in wanted or len(wanted['color']) == 3
                if items and channels and colour_valid and set(wanted) <= {'color', 'transparency'} and all(len(values) == 1 and all(
                        math.isclose(values[0][key], value, abs_tol=1e-6)
                        for key, value in channels.items()) for values in signatures):
                    actual = wanted
            elif kind == 'part_appearance':
                from text2ifc_presentation.part_readback import part_request_matches
                wanted = expected.get('value', {})
                if entity and scope != 'inherited' and part_request_matches(entity, wanted):
                    actual = wanted
            elif kind == 'template' and expected.get('value', {}).get('template_id') == 'metal-picket':
                from .basic_railing import verify_basic_railing
                wanted = expected.get('value', {})
                try:
                    metadata = _properties(entity).get('Pset_text2IFCBasicRailing', {})
                    dimensions = json.loads(metadata.get('DimensionsJson', '{}'))
                    rep = {**dimensions, **wanted, 'kind':'basic_railing'}
                    # Use request parameters, not metadata's claim of what the user
                    # specified. The verifier compares actual solids and defaults.
                    if entity.is_a('IfcRailing') and scope != 'inherited' and not verify_basic_railing(
                        entity.file, {'entities':[{'id':entity_id,'ifc_class':'IfcRailing',
                        'attributes':{'Representation':rep}}]}, verify_placement=False):
                        actual = wanted
                except (AttributeError, KeyError, TypeError, ValueError):
                    reason = 'Railing template request cannot be verified from reopened IFC.'
            elif kind == 'template':
                from .basic_filling import verify_basic_filling
                import ifcopenshell.util.unit
                metadata = _properties(entity).get('Pset_text2IFCBasicFilling', {}) if entity else {}
                wanted = expected.get('value', {})
                try:
                    parameters = json.loads(metadata.get('ParametersJson', '{}'))
                    scale = ifcopenshell.util.unit.calculate_unit_scale(entity.file) * 1000
                    actual = {'template_id': metadata.get('TemplateId'), 'template_version': metadata.get('TemplateVersion'), 'parameters': parameters,
                              'width': entity.OverallWidth * scale, 'height': entity.OverallHeight * scale, 'depth':_available_filling_depth(entity)}
                    matches_request = all((all(parameters.get(k) == v for k, v in value.items()) if key == 'parameters' else value <= actual['depth'] + 1e-6 if key == 'depth' else actual.get(key) == value) for key, value in wanted.items())
                    sources = json.loads(metadata.get('ParameterSourcesJson', '{}'))
                    authored = {key:value for key,value in parameters.items() if sources.get(key) == 'user'}
                    rep = {'kind':'basic_filling', **actual, 'parameters':authored, 'depth': wanted.get('depth', parameters['frame_depth'])}
                    # This expectation freezes local template values only. The
                    # mandatory document verifier checks full world placement.
                    if matches_request and not verify_basic_filling(entity.file, {'entities':[{'id':entity_id,'ifc_class':entity.is_a(),'attributes':{'Representation':rep}}]}, verify_placement=False):
                        actual = wanted
                except (AttributeError, IndexError, KeyError, TypeError, ValueError):
                    reason = 'Template request cannot be verified from reopened IFC.'
            else:
                reason = "Unknown semantic expectation kind."
        wanted = expected.get("value")
        okay = (not present if kind == "property" else actual is None) if expected.get("absent") is True else actual == wanted and (present or kind != "property")
        if reason or not okay:
            issues.append(IfcValidationIssue(code="IFC_SEMANTIC_MISMATCH", entity=str(entity_id), attribute=str(kind), message=reason or f"Requested {wanted!r}; reopened IFC contains {actual!r} ({expected.get('scope', 'effective')})."))
    return tuple(issues)


def verify_document_semantics(ifc_file_or_path, document) -> tuple[IfcValidationIssue, ...]:
    model = _model(ifc_file_or_path)
    indexed = _index(model)
    types = {entity_id: r["attributes"]["RelatingType"] for r in document["relationships"] if r["ifc_class"] == "IfcRelDefinesByType" for entity_id in r["attributes"]["RelatedObjects"]}
    expected = []
    issues = []
    for record in document["entities"]:
        entity_id = record["id"]
        rep = record.get('attributes', {}).get('Representation', {})
        expected.append({"entity_id": entity_id, "kind": "type", "value": types.get(entity_id)})
        matches = indexed.get(entity_id, [])
        if len(matches) != 1:
            continue
        entity = matches[0]
        if entity_id not in types and _types(entity):
            attached = _types(entity)
            operation = {'door-left':'SINGLE_SWING_LEFT', 'door-right':'SINGLE_SWING_RIGHT'}.get(rep.get('template_id'))
            legal_attachment = rep.get('kind') == 'basic_filling' and len(attached) == 1 and operation and attached[0].is_a('IfcDoorStyle') and attached[0].OperationType == operation and not _identity(attached[0]) and attached[0].Name == f'text2IFC construction attachment {entity_id}' and not attached[0].HasPropertySets and not attached[0].HasAssociations and not attached[0].RepresentationMaps
            if not legal_attachment:
                issues.append(IfcValidationIssue('IFC_SEMANTIC_MISMATCH', entity_id, 'type', 'Unrequested Type attachment.'))
        actual_properties = _properties(entity)
        # Compiler-owned provenance is checked by its own geometry/presentation contracts.
        for name in ("Pset_text2IFCBasicFilling", "Pset_text2IFCAppearance"):
            actual_properties.pop(name, None)
        if document.get('schema_version') in {'bim-json/2.3', 'bim-json/2.4', 'bim-json/2.5', 'bim-json/2.6'} and rep.get('kind') == 'basic_railing':
            # The dedicated verifier checks this construction metadata and every
            # actual solid; it is not an authored performance property set.
            actual_properties.pop('Pset_text2IFCBasicRailing', None)
        wanted_properties = {name: values for name, values in record.get("property_sets", {}).items() if values}
        if actual_properties != wanted_properties:
            issues.append(IfcValidationIssue("IFC_SEMANTIC_MISMATCH", entity_id, "property_sets", f"Authored direct properties {wanted_properties!r}; IFC contains {actual_properties!r}."))
        assignments = record.get("materials", [])
        if record["ifc_class"] == "IfcWallStandardCase" and not assignments:
            continue
        wanted = assignments[0] if assignments else None
        if record["ifc_class"] == "IfcWallStandardCase" and wanted and wanted["kind"] == "single_material":
            material = element.get_material(entity, should_inherit=False)
            layers = material.ForLayerSet.MaterialLayers if material and material.is_a("IfcMaterialLayerSetUsage") else []
            if len(layers) != 1 or layers[0].Material.Name != wanted["name"]:
                issues.append(IfcValidationIssue("IFC_SEMANTIC_MISMATCH", entity_id, "material", "StandardCase single material layer does not match requested material."))
        else:
            expected.append({"entity_id": entity_id, "kind": "material", "scope": "direct", "value": wanted})
    return tuple(issues) + verify_semantic_expectations(model, expected)
