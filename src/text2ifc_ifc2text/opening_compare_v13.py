"""Compare actual opening solids in world mm using IfcOpenShell geometry."""
import ifcopenshell.geom
import numpy as np

from text2ifc_compiler.component_expectations import _samples, _surface_distance, _quantity, _topology


def _mesh(product):
    if not product.is_a('IfcOpeningElement'):
        raise ValueError('Expected an opening occurrence.')
    projects=product.file.by_type('IfcProject')
    if len(projects)!=1 or projects[0].UnitsInContext is None:
        raise ValueError('Explicit project units are required.')
    bodies=[r for r in getattr(getattr(product,'Representation',None),'Representations',())
            if r.RepresentationIdentifier=='Body']
    if len(bodies)!=1 or not bodies[0].Items:
        raise ValueError('Exactly one nonempty Body is required.')
    settings=ifcopenshell.geom.settings()
    settings.set('use-world-coords',True)
    settings.set('convert-back-units',False)
    settings.set('context-identifiers',['Body'])
    settings.set('mesher-linear-deflection',.0001)
    # Keep the owning shape alive while copying the wrapped geometry arrays.
    shape=ifcopenshell.geom.create_shape(settings,product)
    vertices=np.array(shape.geometry.verts,dtype=float).reshape(-1,3)*1000.
    faces=np.array(shape.geometry.faces,dtype=int).reshape(-1,3)
    if not len(vertices) or not len(faces) or len(faces)>50000 or not np.isfinite(vertices).all():
        raise ValueError('Opening mesh is empty, invalid or exceeds 50000 triangles.')
    return vertices,faces


def compare_opening_geometry(source,candidate):
    result={'schema_version':'text2ifc/opening-geometry-compare/1.3','pass':False,'unassessed':False,
            'linear_tolerance_mm':1.,'numeric_epsilon_mm':1e-6,
            'method':'IfcOpenShell complete Body world mesh; bidirectional sampled point-to-triangle distance, topology and volume envelope',
            'continuous_hausdorff_certified':False}
    try:
        av,af=_mesh(source);bv,bf=_mesh(candidate)
        distance=max(_surface_distance(_samples(av,af),bv[bf]),_surface_distance(_samples(bv,bf),av[af]))
        ta,tb=_topology(av,af),_topology(bv,bf)
        aa,va=_quantity(av,af);ab,vb=_quantity(bv,bf)
        result.update(sampled_surface_distance_mm=distance,source_topology=list(ta),candidate_topology=list(tb),
                      topology_equal=ta==tb,source_volume_mm3=va,candidate_volume_mm3=vb,
                      volume_delta_mm3=abs(va-vb),volume_displacement_allowance_mm3=max(aa,ab)*1.)
        result['pass']=bool(distance<=1.+1e-6 and ta==tb and abs(va-vb)<=max(aa,ab)*1.+1e-6)
    except (ValueError,TypeError,AttributeError,RuntimeError,IndexError) as error:
        result.update(unassessed=True,reason=str(error))
    return result
