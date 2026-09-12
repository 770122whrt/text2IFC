"""Actual swept solids for a bounded single-material picket railing."""
import json

import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from ifcopenshell.api.geometry import assign_representation, add_shape_aspect
from ifcopenshell.api.pset import add_pset, edit_pset

from text2ifc_contract.basic_railing import resolve_basic_railing
from .verification import IfcValidationIssue


def add_basic_railing_geometry(file, product, representation, context):
    resolved=resolve_basic_railing(representation,product.is_a())
    scale=.001/ifcopenshell.util.unit.calculate_unit_scale(file)
    slope=resolved['rise']/resolved['length'];groups={}
    for role,sections in resolved['sections'].items():
        groups[role]=[]
        for x0,x1,z0,z1,depth in sections:
            points=[(x0,z0+slope*x0),(x1,z0+slope*x1),(x1,z1+slope*x1),(x0,z1+slope*x0),(x0,z0+slope*x0)]
            curve=file.createIfcPolyline([file.createIfcCartesianPoint((x*scale,z*scale)) for x,z in points])
            profile=file.create_entity('IfcArbitraryClosedProfileDef',ProfileType='AREA',OuterCurve=curve)
            position=file.createIfcAxis2Placement3D(file.createIfcCartesianPoint((0.,depth*scale/2,0.)),
                file.createIfcDirection((0.,-1.,0.)),file.createIfcDirection((1.,0.,0.)))
            groups[role].append(file.createIfcExtrudedAreaSolid(profile,position,file.createIfcDirection((0.,0.,1.)),depth*scale))
    shape=file.create_entity('IfcShapeRepresentation',ContextOfItems=context,RepresentationIdentifier='Body',
        RepresentationType='SweptSolid',Items=[item for items in groups.values() for item in items])
    assign_representation(file,product=product,representation=shape)
    for role,items in groups.items():
        if items:add_shape_aspect(file,name=role,items=items,representation=shape,part_of_product=product.Representation)
    pset=add_pset(file,product=product,name='Pset_text2IFCBasicRailing')
    dims={k:resolved[k] for k in ('length','height','depth','rise')}
    edit_pset(file,pset=pset,properties={'TemplateId':resolved['template_id'],'TemplateVersion':resolved['template_version'],
        'DimensionsJson':json.dumps(dims,sort_keys=True),'ParametersJson':json.dumps(resolved['parameters'],sort_keys=True),
        'ParameterSourcesJson':json.dumps(resolved['parameter_sources'],sort_keys=True)})


def verify_basic_railing(model, document, *, verify_placement=True):
    """Compare actual reopened vertices and Body membership to frozen dimensions.

    The template resolver supplies the declared contract, not IFC authoring metadata.
    ShapeAspect names alone cannot satisfy this check: every real solid is meshed.
    """
    identities={}
    for product in model.by_type('IfcProduct'):
        identity=ifcopenshell.util.element.get_psets(product).get('Pset_text2IFCIdentity',{}).get('BimJsonId')
        if identity:identities.setdefault(identity,[]).append(product)
    issues=[];scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    from text2ifc_contract.placement import world_transform_for
    settings=ifcopenshell.geom.settings()
    for record in document.get('entities',[]):
        rep=record.get('attributes',{}).get('Representation',{})
        if rep.get('kind')!='basic_railing':continue
        identity=record['id']
        try:
            matches=identities.get(identity,[])
            if len(matches)!=1 or not matches[0].is_a('IfcRailing'):raise ValueError('Missing or ambiguous railing identity/family.')
            product=matches[0];resolved=resolve_basic_railing(rep,record['ifc_class'])
            metadata=ifcopenshell.util.element.get_psets(product,should_inherit=False).get('Pset_text2IFCBasicRailing',{})
            metadata={k:v for k,v in metadata.items() if k!='id'}
            expected_metadata={'TemplateId':resolved['template_id'],'TemplateVersion':resolved['template_version'],
                'DimensionsJson':json.dumps({k:resolved[k] for k in ('length','height','depth','rise')},sort_keys=True),
                'ParametersJson':json.dumps(resolved['parameters'],sort_keys=True),
                'ParameterSourcesJson':json.dumps(resolved['parameter_sources'],sort_keys=True)}
            if metadata!=expected_metadata:raise ValueError('Railing parameter provenance differs from the frozen input.')
            if verify_placement:
                expected=np.array(world_transform_for(document,identity),dtype=float);expected[:3,3]*=.001
                actual=ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement);actual[:3,3]*=scale
                if not np.allclose(actual,expected,rtol=0,atol=1e-7):raise ValueError('Railing placement differs from frozen input.')
            body=[i for r in product.Representation.Representations if r.RepresentationIdentifier=='Body' for i in r.Items]
            groups={}
            for aspect in product.Representation.HasShapeAspects:
                if aspect.Name in groups:raise ValueError('Duplicate railing aspect.')
                groups[aspect.Name]=[i for r in aspect.ShapeRepresentations for i in r.Items]
            wanted={k:v for k,v in resolved['sections'].items() if v}
            members=[i.id() for items in groups.values() for i in items]
            if set(groups)!=set(wanted) or len(members)!=len(set(members)) or sorted(members)!=sorted(i.id() for i in body):
                raise ValueError('Body/aspect membership does not match the bounded railing.')
            slope=resolved['rise']/resolved['length']
            for role,sections in wanted.items():
                if len(groups[role])!=len(sections):raise ValueError('Railing part count differs from input.')
                actual_vertices=[]
                for item in groups[role]:
                    mesh=ifcopenshell.geom.create_shape(settings,item)
                    vertices=np.asarray(mesh.verts,dtype=float).reshape(-1,3)
                    triangles=vertices[np.asarray(mesh.faces,dtype=int).reshape(-1,3)]
                    volume=abs(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6)
                    actual_vertices.append((sorted({tuple(round(float(v),7) for v in row) for row in vertices}),round(float(volume),9)))
                expected_vertices=[]
                for x0,x1,z0,z1,depth in sections:
                    expected_vertices.append((sorted({(round(x/1000,7),round(y/1000,7),round((z+slope*x)/1000,7))
                        for x in (x0,x1) for y in (-depth/2,depth/2) for z in (z0,z1)}),round((x1-x0)*(z1-z0)*depth/1e9,9)))
                if sorted(actual_vertices)!=sorted(expected_vertices):raise ValueError('Actual railing solids differ from frozen dimensions or gaps.')
        except (AttributeError,KeyError,IndexError,TypeError,ValueError,RuntimeError) as error:
            issues.append(IfcValidationIssue('IFC_BASIC_RAILING_MISMATCH',str(identity),'Representation',str(error)))
    return tuple(issues)
