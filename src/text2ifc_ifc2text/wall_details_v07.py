"""Versioned IFC2Text detail extension; existing text2IFC and v0.6 are unchanged.

Read an actual single vertical extrusion, not a mesh bbox as a fictitious profile.
Only straight-edged, simple closed bottom profiles are supported in this version.
"""
from __future__ import annotations
import copy
import math
import re
from pathlib import Path
from typing import Any
import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from shapely.geometry import Polygon
from .compact import compact_description, mm1, ring
from .observation import all_items

VERSION = 'text2ifc/ifc2text-wall-detail/0.7'


def read_wall_solid(entity: Any, scale_mm: float) -> dict[str, Any]:
    """Read the unvoided solid's world bottom outline in mm; reject unsupported forms."""
    unsupported = lambda why: {'status':'unsupported','reason':why,'schema_version':VERSION}
    reps = getattr(getattr(entity,'Representation',None),'Representations',()) or ()
    items = [item for rep in reps if rep.RepresentationIdentifier=='Body' for item in rep.Items]
    if len(items)!=1 or items[0].is_a()!='IfcExtrudedAreaSolid':
        return unsupported('REQUIRES_SINGLE_UNCLIPPED_EXTRUSION')
    solid=items[0]; profile=solid.SweptArea
    placement = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
    solid_matrix=placement @ ifcopenshell.util.placement.get_axis2placement(solid.Position)
    direction=np.asarray(solid.ExtrudedDirection.DirectionRatios,dtype=float)
    norm=float(np.linalg.norm(direction))
    if not math.isfinite(norm) or norm<=0:
        return unsupported('INVALID_EXTRUSION_DIRECTION')
    world_direction=solid_matrix[:3,:3] @ (direction/norm)
    if not np.allclose(world_direction[:2],0.,atol=1e-8):
        return unsupported('NON_VERTICAL_EXTRUSION')
    if profile.is_a()=='IfcArbitraryClosedProfileDef':
        if not profile.OuterCurve.is_a('IfcPolyline'):
            return unsupported('CURVED_PROFILE_NOT_SUPPORTED')
        points=[list(p.Coordinates) for p in profile.OuterCurve.Points]
        if not points or any(len(p)!=2 for p in points):
            return unsupported('PROFILE_IS_NOT_2D')
        matrix=solid_matrix
    elif profile.is_a()=='IfcRectangleProfileDef':
        x,y=float(profile.XDim)/2,float(profile.YDim)/2
        points=[[-x,-y],[x,-y],[x,y],[-x,y],[-x,-y]]
        profile_pos=ifcopenshell.util.placement.get_axis2placement(profile.Position) if profile.Position else np.eye(4)
        matrix=solid_matrix @ profile_pos
    else:
        return unsupported('PROFILE_WITH_HOLES_OR_UNSUPPORTED_FORM')
    coords=np.asarray([matrix @ np.asarray([p[0],p[1],0.,1.]) for p in points])[:,:3]*scale_mm
    if not np.all(np.isfinite(coords)) or np.ptp(coords[:,2])>1e-5:
        return unsupported('NON_HORIZONTAL_OR_INVALID_BOTTOM')
    height=float(solid.Depth)*scale_mm
    if not math.isfinite(height) or height<=0:
        return unsupported('INVALID_EXTRUSION_HEIGHT')
    if world_direction[2]<0:
        coords[:,2]-=height
    polygon=Polygon(coords[:,:2])
    if not polygon.is_valid or polygon.area<=1e-8:
        return unsupported('INVALID_PROFILE_POLYGON')
    # Compare whole boundaries, so a notched rectangle with the same bbox is not lost.
    nonrect=polygon.boundary.hausdorff_distance(polygon.minimum_rotated_rectangle.boundary)>.01
    return {'schema_version':VERSION,'status':'supported_vertical_extrusion',
        'source_profile_type':profile.is_a(),'requires_explicit_outline':bool(nonrect),
        'bottom_outline_xy_mm':coords[:,:2].tolist(),'bottom_z_mm':float(coords[0,2]),
        'height_mm':height,'direction':'world_positive_z','coordinate_frame':'world',
        'geometry_role':'wall_solid_before_opening_subtraction','area_mm2':float(polygon.area)}


def enrich_wall_details(source: str | Path, facts: dict) -> dict:
    """Append versioned observations without mutating a caller's frozen facts."""
    result=copy.deepcopy(facts)
    model=ifcopenshell.open(str(source))
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)*1000.
    for category,item in all_items(result):
        if category!='walls':continue
        try:
            entity=model.by_guid(item['source_global_id'])
            detail=read_wall_solid(entity,scale)
            # Rectangular solids whose position is not recovered by the old axis
            # expression also need explicit placement; never invent one from bbox.
            if detail['status']=='supported_vertical_extrusion':
                a,b=item.get('axis_start_mm'),item.get('axis_end_mm')
                thickness=item.get('thickness_mm')
                if a is None or b is None or thickness is None or math.hypot(b[0]-a[0],b[1]-a[1])<=0:
                    detail['requires_explicit_outline']=True
                else:
                    length=math.hypot(b[0]-a[0],b[1]-a[1])
                    nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
                    predicted=Polygon([[p[0]+sgn*nx*thickness/2,p[1]+sgn*ny*thickness/2]
                                       for p,sgn in [(a,1),(b,1),(b,-1),(a,-1)]])
                    measured=Polygon(detail['bottom_outline_xy_mm'])
                    detail['requires_explicit_outline'] |= predicted.boundary.hausdorff_distance(measured.boundary)>.2
                ring(detail['bottom_outline_xy_mm'])  # Detect destructive display rounding.
            item['solid_detail']=detail
        except (ValueError,RuntimeError,TypeError) as exc:
            item['solid_detail']={'schema_version':VERSION,'status':'unsupported','reason':type(exc).__name__}
    result['wall_detail_version']=VERSION
    return result


def wall_detail_text(wall: dict) -> str:
    d=wall.get('solid_detail',{})
    if d.get('status')!='supported_vertical_extrusion':
        return '**墙 '+wall['label']+' 的实体轮廓**：本次未提取；原因 '+str(d.get('reason','unavailable'))+'。不以包围盒补造轮廓。'
    return ('**墙 '+wall['label']+' 的实体轮廓**：底面外轮廓（世界XY，mm）'+ring(d['bottom_outline_xy_mm'])+
        '；底面标高 Z='+mm1(d['bottom_z_mm'])+'；沿世界+Z竖直拉伸 '+mm1(d['height_mm'])+'。'+
        '这是同一墙体扣除洞口之前的实体，不新增墙；轴线用于定位宿主，不将本轮廓替换为矩形。已有洞口另按其位置扣除一次。')


def detailed_description(facts: dict, narration: dict | None=None) -> str:
    """Insert exception details after the corresponding wall table, not a second model."""
    text=compact_description(facts,narration)
    floors={s['label']:s for s in facts['storeys']}
    if facts.get('unassigned'):
        floors['UNASSIGNED']=facts['unassigned']
    chunks=re.split(r'(?=^## 楼层 )',text,flags=re.M)
    output=[]
    for chunk in chunks:
        match=re.match(r'## 楼层 ([^｜\n]+)',chunk)
        if match:
            floor=floors.get(match.group(1),{})
            details=[wall_detail_text(w) for w in floor.get('walls',[]) if
                w.get('solid_detail',{}).get('requires_explicit_outline') or
                w.get('solid_detail',{}).get('status')=='unsupported']
            if details:
                lines=chunk.splitlines(); last=None
                for i,line in enumerate(lines):
                    if re.match(r'^\|W\d+\|',line):last=i
                if last is None:raise ValueError('WALL_TABLE_INSERTION_TARGET_MISSING')
                lines[last+1:last+1]=['','\n\n'.join(details),'']
                chunk='\n'.join(lines)+'\n\n'
        output.append(chunk)
    return ''.join(output)
