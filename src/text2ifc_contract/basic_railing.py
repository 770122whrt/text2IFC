"""Bounded straight, single-material Generation railing in millimetres."""
from collections.abc import Mapping
from math import ceil, isfinite

from .validation import ValidationIssue

VERSION = "text2ifc/basic-railing/1.0"
DEFAULTS = {"post_width": 40., "max_post_spacing": 1200., "picket_width": 16.,
    "max_clear_gap": 100., "top_rail_height": 40., "bottom_rail_height": 20., "bottom_clearance": 60.}
RANGES = {"post_width": (20, 100), "max_post_spacing": (300, 2000), "picket_width": (10, 40),
    "max_clear_gap": (40, 200), "top_rail_height": (20, 100), "bottom_rail_height": (10, 60), "bottom_clearance": (0, 150)}


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def validate_basic_railing(value, ifc_class, path="/Representation"):
    errors=[]
    def fail(field, message):
        errors.append(ValidationIssue("INVALID_BASIC_RAILING",f"{path}/{field}",message))
    if not isinstance(value,Mapping):
        fail("", "Railing representation must be an object.");return errors
    if ifc_class != "IfcRailing" or value.get("kind") != "basic_railing" or value.get("template_id") != "metal-picket":
        fail("template_id", "This template belongs only to IfcRailing occurrences.")
    if value.get("template_version") != VERSION:
        fail("template_version", "Unregistered railing template version.")
    for field in set(value)-{"kind","template_id","template_version","length","height","depth","rise","parameters"}:
        fail(field,"Unsupported railing field.")
    for field,low,high in [("length",300,20000),("height",700,1600),("depth",20,100)]:
        if not _number(value.get(field)) or not low<=value[field]<=high:
            fail(field,"Dimension is outside this bounded template.")
    rise=value.get("rise",0)
    if not _number(rise) or (_number(value.get("length")) and abs(rise)>value["length"]):
        fail("rise","Rise must be finite and its magnitude cannot exceed horizontal run.")
    supplied=value.get("parameters",{})
    if not isinstance(supplied,Mapping):
        fail("parameters","Parameters must be an object.");return errors
    for field,number in supplied.items():
        if field not in RANGES or not _number(number) or not RANGES[field][0]<=number<=RANGES[field][1]:
            fail(f"parameters/{field}","Unknown or out-of-range railing parameter.")
    if errors:return errors
    p={**DEFAULTS,**supplied}
    if max(p['post_width'],p['picket_width'])>value['depth']:
        fail("depth","Posts and pickets must fit the requested depth; defaults are never shrunk.")
    if p['bottom_clearance']+p['bottom_rail_height']+p['top_rail_height']>=value['height']:
        fail("height","Rail heights must leave a positive clear picket height.")
    if not errors:
        groups=_component_sections(value,p)
        if sum(len(items) for items in groups.values())>512:
            fail("length","The bounded template permits at most 512 solids per railing.")
    return errors


def _component_sections(value,p):
    """Local X/Z sections; z offsets follow the specified base line at every X."""
    length,height=float(value['length']),float(value['height'])
    pw=p['post_width'];span_count=max(1,ceil((length-pw)/p['max_post_spacing']))
    centers=[pw/2+i*(length-pw)/span_count for i in range(span_count+1)]
    posts=[(x-pw/2,x+pw/2,0,height-p['top_rail_height'],pw) for x in centers]
    sections={'Posts':posts,'Pickets':[], 'TopRail':[(0,length,height-p['top_rail_height'],height,float(value['depth']))], 'BottomRail':[]}
    for a,b in zip(posts,posts[1:]):
        left,right=a[1],b[0];available=right-left
        sections['BottomRail'].append((left,right,p['bottom_clearance'],p['bottom_clearance']+p['bottom_rail_height'],float(value['depth'])))
        count=max(0,ceil((available-p['max_clear_gap'])/(p['picket_width']+p['max_clear_gap'])))
        gap=(available-count*p['picket_width'])/(count+1)
        for i in range(count):
            x=left+gap+i*(p['picket_width']+gap)
            sections['Pickets'].append((x,x+p['picket_width'],p['bottom_clearance']+p['bottom_rail_height'],height-p['top_rail_height'],p['picket_width']))
    return sections


def resolve_basic_railing(value, ifc_class="IfcRailing"):
    errors=validate_basic_railing(value,ifc_class)
    if errors:raise ValueError('; '.join(e.message for e in errors))
    supplied=value.get('parameters',{});p={k:float(v) for k,v in {**DEFAULTS,**supplied}.items()}
    dimensions={k:float(value.get(k,0)) for k in ('length','height','depth','rise')}
    return {**value,**dimensions,'parameters':p,
        'parameter_sources':{k:'user' if k in supplied else VERSION+':metal-picket' for k in p},
        'sections':_component_sections(value,p)}
