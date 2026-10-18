from __future__ import annotations

import math

import ifcopenshell
import ifcopenshell.guid
import pytest


@pytest.fixture
def scene_factory():
    def build(path, *, rotated=True, millimetres=False, shared_property=True):
        model = ifcopenshell.file(schema="IFC2X3")
        scale = 1000.0 if millimetres else 1.0
        person = model.createIfcPerson(FamilyName="Offline")
        org = model.createIfcOrganization(Name="Dataset fixture")
        app = model.createIfcApplication(org, "1", "Dataset fixture", "fixture")
        owner = model.createIfcOwnerHistory(model.createIfcPersonAndOrganization(person, org), app, None, "ADDED", None, None, None, 1)

        def root(cls, **kwargs):
            return model.create_entity(cls, GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, **kwargs)

        def axis(xyz, direction=(1.0, 0.0, 0.0)):
            return model.createIfcAxis2Placement3D(model.createIfcCartesianPoint(tuple(float(x) * scale for x in xyz)), model.createIfcDirection((0.0, 0.0, 1.0)), model.createIfcDirection(direction))

        def placement(xyz, parent=None, direction=(1.0, 0.0, 0.0)):
            return model.createIfcLocalPlacement(parent, axis(xyz, direction))

        context = model.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-5, axis((0, 0, 0)), None)
        units = model.createIfcUnitAssignment([model.createIfcSIUnit(None, "LENGTHUNIT", "MILLI" if millimetres else None, "METRE")])
        project = root("IfcProject", Name="Synthetic fixture", RepresentationContexts=[context], UnitsInContext=units)
        site = root("IfcSite", Name="Site", CompositionType="ELEMENT", ObjectPlacement=placement((0, 0, 0)))
        building = root("IfcBuilding", Name="Building", CompositionType="ELEMENT", ObjectPlacement=placement((0, 0, 0), site.ObjectPlacement))
        storey = root("IfcBuildingStorey", Name="Level A", CompositionType="ELEMENT", Elevation=3 * scale, ObjectPlacement=placement((10, 20, 3), building.ObjectPlacement, (0.0, 1.0, 0.0) if rotated else (1.0, 0.0, 0.0)))
        for parent, child in ((project, site), (site, building), (building, storey)):
            root("IfcRelAggregates", RelatingObject=parent, RelatedObjects=[child])

        def box(product, dimensions):
            width, depth, height = dimensions
            profile = model.createIfcRectangleProfileDef("AREA", None, model.createIfcAxis2Placement2D(model.createIfcCartesianPoint((width / 2 * scale, depth / 2 * scale)), None), width * scale, depth * scale)
            solid = model.createIfcExtrudedAreaSolid(profile, axis((0, 0, 0)), model.createIfcDirection((0.0, 0.0, 1.0)), height * scale)
            product.Representation = model.createIfcProductDefinitionShape(None, None, [model.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])])

        wall = root("IfcWall", Name="Host wall", ObjectPlacement=placement((0, 0, 0), storey.ObjectPlacement))
        box(wall, (8.0, 0.15, 3.0))
        products = [wall]
        for cls, xyz, dimensions in (("IfcDoor", (1, 0, 0), (0.9, 0.15, 2.1)), ("IfcDoor", (3, 0, 0), (0.9, 0.15, 2.1)), ("IfcWindow", (5, 0, 1), (1.2, 0.15, 1.4)), ("IfcWindow", (6.5, 0, 1), (1.2, 0.15, 1.4)), ("IfcBeam", (0, 2, 2.7), (4, 0.2, 0.3)), ("IfcBeam", (0, 4, 2.7), (4, 0.2, 0.3)), ("IfcColumn", (0, 2, 0), (0.3, 0.3, 3)), ("IfcColumn", (4, 2, 0), (0.3, 0.3, 3))):
            element = root(cls, Name=f"{cls}-{len(products)}", ObjectPlacement=placement(xyz, storey.ObjectPlacement))
            box(element, dimensions)
            if cls in {"IfcDoor", "IfcWindow"}:
                element.OverallWidth = dimensions[0] * scale
                element.OverallHeight = dimensions[2] * scale
                opening = root("IfcOpeningElement", Name="Opening", ObjectPlacement=placement(xyz, storey.ObjectPlacement))
                box(opening, dimensions)
                root("IfcRelVoidsElement", RelatingBuildingElement=wall, RelatedOpeningElement=opening)
                root("IfcRelFillsElement", RelatingOpeningElement=opening, RelatedBuildingElement=element)
            products.append(element)
        root("IfcRelContainedInSpatialStructure", RelatingStructure=storey, RelatedElements=products)
        doors = model.by_type("IfcDoor")
        for index, group in enumerate(([doors] if shared_property else [[door] for door in doors])):
            prop = model.createIfcPropertySingleValue("IsExternal", None, model.createIfcBoolean(True), None)
            pset = root("IfcPropertySet", Name="Pset_DoorCommon", HasProperties=[prop])
            root("IfcRelDefinesByProperties", RelatingPropertyDefinition=pset, RelatedObjects=group)
        for element in model.by_type("IfcBeam") + model.by_type("IfcColumn") + model.by_type("IfcWindow"):
            prop = model.createIfcPropertySingleValue("Reference", None, model.createIfcIdentifier("original reference"), None)
            pset = root("IfcPropertySet", Name=f"Pset_{element.is_a()[3:]}Common", HasProperties=[prop])
            root("IfcRelDefinesByProperties", RelatingPropertyDefinition=pset, RelatedObjects=[element])
        model.write(str(path))
        return path
    return build
