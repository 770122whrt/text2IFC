"""Independent occupied-Body comparison of source and reconstructed fillings.

Read every actual Body item and its mappings, without consulting the component
extractor, public part catalog, candidate JSON, or recognized-item whitelist.
Boolean union here is evaluator work, not a new authored-geometry capability.
"""
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

from text2ifc_compiler.component_expectations import _mesh, _quantity, _samples, _surface_distance, _topology

VERSION='text2ifc/filling-geometry-compare/1.2'


def _actual_body_mesh(product):
    if product.is_a() not in {'IfcDoor','IfcWindow'}:
        raise ValueError('Expected a door or window occurrence.')
    projects=product.file.by_type('IfcProject')
    if len(projects)!=1 or projects[0].UnitsInContext is None:
        raise ValueError('Exactly one project with explicit units is required.')
    bodies=[r for r in getattr(getattr(product,'Representation',None),'Representations',())
            if r.RepresentationIdentifier=='Body']
    if len(bodies)!=1 or not bodies[0].Items:
        raise ValueError('Exactly one nonempty complete Body is required.')
    reference=ifcopenshell.file(schema=product.file.schema)
    # Retain actual source units during tessellation, including the SI mesher
    # tolerance. Reinterpreting metre coordinates as mm then scaling vertices
    # afterwards would use the wrong curve approximation accuracy.
    reference.add(projects[0])
    solids=[];visited=0
    def rigid(matrix):
        r=matrix[:3,:3]
        if not np.isfinite(matrix).all() or not np.allclose(r.T@r,np.eye(3),atol=1e-9,rtol=0) or not np.isclose(np.linalg.det(r),1.,atol=1e-9,rtol=0):
            raise ValueError('Scaled, reflected or invalid actual placement is not assessed.')
    def position(matrix):
        return reference.createIfcAxis2Placement3D(
            reference.createIfcCartesianPoint(tuple(float(v) for v in matrix[:3,3])),
            reference.createIfcDirection(tuple(float(v) for v in matrix[:3,2])),
            reference.createIfcDirection(tuple(float(v) for v in matrix[:3,0])))
    def walk(item,matrix,stack):
        nonlocal visited
        visited+=1
        if visited>4096 or len(stack)>16 or item.id() in stack:
            raise ValueError('Actual Body mapping expansion is cyclic or exceeds the evaluator limit.')
        rigid(matrix)
        if item.is_a('IfcMappedItem'):
            m=ifcopenshell.util.placement.get_mappeditem_transformation(item)
            for child in item.MappingSource.MappedRepresentation.Items:
                walk(child,matrix@m,(*stack,item.id()))
        elif item.is_a()=='IfcExtrudedAreaSolid':
            # Fresh deep copy per occurrence: mapped repetitions can share the
            # same source solid while occupying different positions.
            solid=ifcopenshell.util.element.copy_deep(reference,item)
            m=matrix@ifcopenshell.util.placement.get_axis2placement(item.Position)
            rigid(m);solid.Position=position(m);solids.append(solid)
        else:
            raise ValueError(f'Complete Body contains {item.is_a()} #{item.id()}; evaluator cannot silently omit it.')
    frame=ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)
    for item in bodies[0].Items:walk(item,frame,())
    if not solids or len(solids)>2048:
        raise ValueError('Actual Body solid count is outside evaluator limits.')
    vertices,faces=_mesh(reference,solids)
    if len(faces)>50000:
        raise ValueError('Actual Body tessellation exceeds the explicit 50000-triangle evaluator limit.')
    return vertices,faces,len(solids)


def compare_filling_geometry(source,candidate):
    """Compare complete occupied geometry in world mm; never mutate either file."""
    result={'schema_version':VERSION,'pass':False,'unassessed':False,
            'linear_tolerance_mm':1.,'numeric_epsilon_mm':1e-6,
            'method':'complete native Body union, world-space surface samples, topology and volume',
            'limits':'Not a continuous Hausdorff certificate; no material/appearance claim from geometry.'}
    try:
        a,af,ac=_actual_body_mesh(source);b,bf,bc=_actual_body_mesh(candidate)
        forward=_surface_distance(_samples(a,af),b[bf]);backward=_surface_distance(_samples(b,bf),a[af])
        aa,av=_quantity(a,af);ba,bv=_quantity(b,bf)
        ta,tb=_topology(a,af),_topology(b,bf)
        result.update(source_solids=ac,candidate_solids=bc,source_triangles=len(af),candidate_triangles=len(bf),
            source_to_candidate_sampled_distance_mm=forward,candidate_to_source_sampled_distance_mm=backward,
            sampled_surface_distance_mm=max(forward,backward),source_topology=list(ta),candidate_topology=list(tb),
            topology_equal=ta==tb,source_volume_mm3=av,candidate_volume_mm3=bv,volume_delta_mm3=abs(av-bv),
            volume_displacement_allowance_mm3=max(aa,ba)*1.)
        result['pass']=max(forward,backward)<=1.+1e-6 and ta==tb and abs(av-bv)<=max(aa,ba)*1.+1e-6
    except (ValueError,TypeError,AttributeError,RuntimeError,IndexError) as error:
        result.update(unassessed=True,reason=str(error))
    return result
