"""Check reopened part geometry against frozen public component requirements.

Reference geometry is made only from the public Brief, never from source IFC.
Primitive partition may differ. The comparison uses actual union surfaces,
topology, duplicate-solid checks and a 1 mm sampled surface-distance limit.
"""
import json

import ifcopenshell.geom
import numpy as np

from text2ifc_contract.component_geometry import expanded_parts
from text2ifc_presentation import item_appearance_signatures


def _mesh(model, items):
    solids=[model.add(item) for item in items]
    if not solids: raise ValueError('Part has no solids.')
    merged=solids[0]
    for solid in solids[1:]:
        merged=model.createIfcBooleanResult('UNION',merged,solid)
    settings=ifcopenshell.geom.settings()
    settings.set('mesher-linear-deflection',0.0001)
    shape=ifcopenshell.geom.create_shape(settings,merged)
    vertices=np.asarray(shape.verts,dtype=float).reshape(-1,3)*1000
    faces=np.asarray(shape.faces,dtype=int).reshape(-1,3)
    if not len(vertices) or not len(faces): raise ValueError('Part has empty measured geometry.')
    return vertices,faces


def _topology(vertices, faces):
    points,index=np.unique(np.round(vertices,6),axis=0,return_inverse=True)
    faces=index[faces]
    edges={tuple(sorted((int(a),int(b)))) for f in faces for a,b in zip(f,np.roll(f,-1))}
    parents=list(range(len(points)))
    def root(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for a,b in edges: parents[root(a)]=root(b)
    return len(points)-len(edges)+len(faces),len({root(i) for i in range(len(points))})


def _samples(vertices, faces):
    triangles=vertices[faces]
    return np.unique(np.vstack([vertices,triangles.mean(axis=1),
        (triangles[:,0]+triangles[:,1])/2,(triangles[:,1]+triangles[:,2])/2,
        (triangles[:,2]+triangles[:,0])/2]),axis=0)


def _surface_distance(points, triangles):
    """Exact point-to-triangle minimum, evaluated at deterministic mesh samples."""
    a,b,c=triangles[:,0],triangles[:,1],triangles[:,2]
    u,v=b-a,c-a
    uu=np.einsum('ij,ij->i',u,u);uv=np.einsum('ij,ij->i',u,v);vv=np.einsum('ij,ij->i',v,v)
    normals=np.cross(u,v);normal2=np.einsum('ij,ij->i',normals,normals)
    determinant=uu*vv-uv*uv
    valid=determinant>1e-16
    maximum=0.
    for start in range(0,len(points),16):
        w=points[start:start+16,None,:]-a[None,:,:]
        wu=np.einsum('ptj,tj->pt',w,u);wv=np.einsum('ptj,tj->pt',w,v)
        denominator=np.where(valid,determinant,1.)
        beta=(vv*wu-uv*wv)/denominator;gamma=(uu*wv-uv*wu)/denominator
        inside=valid & (beta>=-1e-10) & (gamma>=-1e-10) & (beta+gamma<=1+1e-10)
        dot=np.einsum('ptj,tj->pt',w,normals)
        distance=np.where(inside,dot*dot/np.where(normal2>0,normal2,1.),np.inf)
        for first,last in ((a,b),(b,c),(c,a)):
            edge=last-first;length2=np.einsum('ij,ij->i',edge,edge)
            delta=points[start:start+16,None,:]-first[None,:,:]
            t=np.clip(np.einsum('ptj,tj->pt',delta,edge)/np.where(length2>0,length2,1.),0,1)
            residual=delta-t[:,:,None]*edge[None,:,:]
            distance=np.minimum(distance,np.einsum('ptj,ptj->pt',residual,residual))
        maximum=max(maximum,float(np.sqrt(distance.min(axis=1)).max()))
    return maximum


def _quantity(vertices,faces):
    # Center first to avoid cancellation for distant source product frames.
    triangles=(vertices-vertices.mean(axis=0))[faces]
    cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    area=float(np.linalg.norm(cross,axis=1).sum()/2)
    volume=abs(float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6))
    return area,volume


def component_request_problem(product, representation):
    """Return a specific mismatch, or None. This never mutates the product model."""
    from .bootstrap import build_ifc_v2
    from .component_geometry import ASPECT_VERSION
    from text2ifc_contract.component_geometry import validate_components
    from text2ifc_contract.schema import load_schema_v26
    from jsonschema import Draft202012Validator
    try:
        if product is None or product.is_a() not in {'IfcDoor','IfcWindow'}:
            return 'Component target is not a door/window occurrence.'
        schema=load_schema_v26()
        validator=Draft202012Validator({'$defs':schema['$defs'],'$ref':'#/$defs/componentGeometry'})
        if not validator.is_valid(representation) or validate_components(representation,product.is_a(),'/components'):
            return 'Frozen component request is invalid.'
        parts=expanded_parts(representation)
        aspects=list(product.Representation.HasShapeAspects)
        if len(aspects)!=len(parts) or {a.Name for a in aspects}!={p['id'] for p in parts}:
            return 'Requested part identities or counts are different.'
        public_document={'schema_version':'bim-json/2.6','entities':[
            {'id':'reference-project','ifc_class':'IfcProject','attributes':{'Name':'Public component reference'}},
            {'id':'reference-product','ifc_class':product.is_a(),'attributes':{'Representation':representation}}],
            'relationships':[]}
        reference=build_ifc_v2(public_document).ifc_file
        expected_product=reference.by_type(product.is_a())[0]
        expected_aspects={a.Name:a for a in expected_product.Representation.HasShapeAspects}
        actual_aspects={a.Name:a for a in aspects}
        owned=[]
        for part in parts:
            aspect=actual_aspects[part['id']]
            if json.loads(aspect.Description)!={'version':ASPECT_VERSION,'role':part['role']}:
                return f"Part role changed: {part['id']}."
            actual_items=[i for s in aspect.ShapeRepresentations for i in s.Items]
            wanted_items=[i for s in expected_aspects[part['id']].ShapeRepresentations for i in s.Items]
            owned.extend(i.id() for i in actual_items)
            signatures=set()
            for item in actual_items:
                mesh,_faces=_mesh(reference,[item])
                signature=np.unique(np.round(mesh,6),axis=0).tobytes()
                if signature in signatures: return f"Duplicate solid occupancy in {part['id']}."
                signatures.add(signature)
                if 'appearance' in part:
                    styles=item_appearance_signatures(item);wanted=part['appearance']
                    channels=[*wanted['color'],wanted['transparency']]
                    if len(styles)!=1 or not np.allclose([styles[0][k] for k in ('red','green','blue','transparency')],channels,atol=1e-6,rtol=0):
                        return f"Requested part display changed: {part['id']}."
            a,af=_mesh(reference,wanted_items);b,bf=_mesh(reference,actual_items)
            if _topology(a,af)!=_topology(b,bf): return f"Part topology changed: {part['id']}."
            distance=max(_surface_distance(_samples(a,af),b[bf]),_surface_distance(_samples(b,bf),a[af]))
            if distance>1.+1e-6: return f"Part {part['id']} sampled surface difference is {distance:.6g} mm (limit 1 mm)."
            aa,av=_quantity(a,af);ba,bv=_quantity(b,bf)
            if abs(av-bv)>max(aa,ba)*1.+1e-6:
                return f"Part volume difference exceeds the 1 mm surface-displacement envelope: {part['id']}."
        body=[i.id() for s in product.Representation.Representations if s.RepresentationIdentifier=='Body' for i in s.Items]
        if len(owned)!=len(set(owned)) or len(body)!=len(set(body)) or set(owned)!=set(body):
            return 'Part ownership does not cover the complete Body exactly once.'
    except (AttributeError,KeyError,TypeError,ValueError,RuntimeError) as exc:
        return f'Cannot measure component request against actual IFC: {exc}'
    return None
