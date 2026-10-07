"""Private review images from the real world-coordinate meshes in VIEW.html.

Requires Pillow and NumPy. This only draws horizontal mesh sections; it never
edits IFC, substitutes for the independent validator, or accepts a review.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = Path('C:/Windows/Fonts/msyh.ttc')
RED = '#c33e36'
BLUE = '#166ab1'
INK = '#213745'
GREY = '#85949c'


def text(draw, pos, value, *, size=23, color=INK):
    draw.text(pos, value, font=ImageFont.truetype(str(FONT), size), fill=color)


def center(mesh):
    return np.mean(np.asarray(mesh['bounds']), axis=1)


def segments(mesh, z, normal_axis=2, display_axes=(0,1)):
    vertices = np.asarray(mesh['vertices'], dtype=float).reshape(-1, 3)
    triangles = vertices[np.asarray(mesh['faces'], dtype=int).reshape(-1, 3)]
    triangles = triangles[(triangles[:, :, normal_axis].min(axis=1) < z) & (triangles[:, :, normal_axis].max(axis=1) > z)]
    for triangle in triangles:
        points = []
        for a, b in [(triangle[0],triangle[1]), (triangle[1],triangle[2]), (triangle[2],triangle[0])]:
            if (a[normal_axis] - z) * (b[normal_axis] - z) < 0:
                point=a+(b-a)*((z-a[normal_axis])/(b[normal_axis]-a[normal_axis]))
                points.append(point[list(display_axes)])
            elif abs(a[normal_axis] - z) < 1e-9:
                points.append(a[list(display_axes)])
        if len(points) >= 2:
            yield points[0], points[1]


def panel(draw, area, meshes, data, target, reference, limits, z, caption, damaged, normal_axis=2, display_axes=(0,1)):
    x0,y0,x1,y1 = area
    draw.rectangle(area, fill='#f8fafc', outline='#c7d1d8', width=2)
    text(draw, (x0+14,y0+10), caption, size=26)
    left,top,right,bottom = x0+65,y0+62,x1-30,y1-43
    xmin,xmax,ymin,ymax = limits
    scale = min((right-left)/(xmax-xmin), (bottom-top)/(ymax-ymin))
    cx,cy = (left+right)/2,(top+bottom)/2
    wx,wy = (xmin+xmax)/2,(ymin+ymax)/2

    def project(p):
        return (cx + (p[0]-wx)*scale, cy - (p[1]-wy)*scale)

    step = 1 if max(xmax-xmin,ymax-ymin) < 15 else 2
    for x in np.arange(np.ceil(xmin/step)*step,xmax,step):
        a,b = project((x,ymin)),project((x,ymax))
        draw.line([a,b], fill='#e1e7ec', width=1)
        text(draw, (a[0]-16,bottom+5), f'{x:g}', size=16, color='#586d78')
    for y in np.arange(np.ceil(ymin/step)*step,ymax,step):
        a,b = project((xmin,y)),project((xmax,y))
        draw.line([a,b], fill='#e1e7ec', width=1)
        text(draw, (x0+10,a[1]-10), f'{0 if abs(y)<1e-8 else y:g}', size=16, color='#586d78')
    text(draw, (right-75,y0+19), 'XYZ'[display_axes[0]]+' / m →', size=16)
    text(draw, (x0+10,top-19), 'XYZ'[display_axes[1]]+' / m', size=16)

    def layer(guid, mesh, color, width):
        if mesh['class'] in {'IfcOpeningElement','IfcSlab','IfcRoof','IfcCovering'}:
            return
        if mesh['bounds'][display_axes[0]][1] < xmin or mesh['bounds'][display_axes[0]][0] > xmax or mesh['bounds'][display_axes[1]][1] < ymin or mesh['bounds'][display_axes[1]][0] > ymax:
            return
        for a,b in segments(mesh,z,normal_axis,display_axes):
            # Clip line segments to the plot rectangle, without changing geometry.
            p,q = np.asarray(project(a)),np.asarray(project(b))
            delta = q-p
            t0,t1 = 0.0,1.0
            for lo,hi,axis in [(left,right,0),(top,bottom,1)]:
                if abs(delta[axis]) < 1e-12:
                    if not lo <= p[axis] <= hi:
                        break
                else:
                    l,h = sorted(((lo-p[axis])/delta[axis],(hi-p[axis])/delta[axis]))
                    t0,t1 = max(t0,l),min(t1,h)
                    if t0 > t1:
                        break
            else:
                draw.line([tuple(p+t0*delta),tuple(p+t1*delta)],fill=color,width=width)

    for guid,mesh in meshes.items():
        if guid not in data['targets'] and guid not in data['refs']:
            layer(guid,mesh,GREY,2)
    for guid in data['refs']:
        if guid in meshes:
            layer(guid,meshes[guid],BLUE,4)
    for guid in data['targets']:
        if guid in meshes:
            layer(guid,meshes[guid],RED,4)
    p = project(center(target)[list(display_axes)])
    if damaged:
        draw.line([(p[0]-10,p[1]),(p[0]+10,p[1])],fill=RED,width=2)
        draw.line([(p[0],p[1]-10),(p[0],p[1]+10)],fill=RED,width=2)
    label = '删除位置（十字为标注）' if damaged else '损伤目标'
    text(draw, (min(max(p[0]+12,left),right-270),max(top,p[1]-36)), label, size=19, color=RED)
    if reference['bounds'][normal_axis][0] <= z <= reference['bounds'][normal_axis][1]:
        r = project(center(reference)[list(display_axes)])
        text(draw, (min(max(r[0]+12,left),right-170),min(max(top,r[1]+12),bottom-26)), '保留参照', size=19, color=BLUE)
    else:
        text(draw, (left, bottom-30), f'参照在另一标高 Z={center(reference)[2]:.3f} m；请在三维查看器中查看', size=18, color=BLUE)


def render(case):
    html = (case/'VIEW.html').read_text(encoding='utf-8')
    data = json.loads(re.search(r'<script id="ifc-data" type="application/json">(.*?)</script>',html,re.S).group(1))
    assert data['audit']['removed_target_absent_in_d']
    assert data['audit']['reference_geometry_unchanged']
    rows = len(data['targets'])
    image = Image.new('RGB',(1800,170+rows*600),'white')
    draw = ImageDraw.Draw(image)
    text(draw,(25,15),data['title']+' · 局部水平剖切对照',size=31)
    text(draw,(25,65),'红：G 中被删对象；D 的红十字仅标注位置。蓝：保留参照。灰：其他构件。',size=23)
    text(draw,(25,104),'来自真实 IFC 世界坐标网格；两侧同尺度。省略楼板／屋顶，不显示原材质。仅供人工审题。',size=21)
    for row,guid in enumerate(data['targets']):
        target = data['before']['meshes'][guid]
        candidates = [data['before']['meshes'][g] for g in data['refs'] if data['before']['meshes'][g]['class'] == target['class']]
        reference = min(candidates,key=lambda m:np.linalg.norm(center(m)[:2]-center(target)[:2]))
        xy = np.asarray([center(target)[:2],center(reference)[:2]])
        lo,hi = xy.min(axis=0)-1.4,xy.max(axis=0)+1.4
        span = hi-lo
        if span[0]/span[1] < 1.64:
            padding = (span[1]*1.64-span[0])/2
            lo[0]-=padding
            hi[0]+=padding
        else:
            padding = (span[0]/1.64-span[1])/2
            lo[1]-=padding
            hi[1]+=padding
        limits = (lo[0],hi[0],lo[1],hi[1])
        z = float(center(target)[2])
        y = 155+row*600
        kind = '门' if target['class']=='IfcDoor' else '窗'
        c = center(target)
        text(draw,(25,y),f'目标 {row+1} · {kind}；网格包围盒中心 X={c[0]:.3f}，Y={c[1]:.3f} m；剖切 Z={z:.3f} m',size=23)
        panel(draw,(25,y+43,885,y+575),data['before']['meshes'],data,target,reference,limits,z,'G · 损坏前',False)
        panel(draw,(915,y+43,1775,y+575),data['after']['meshes'],data,target,reference,limits,z,'D · 损坏后',True)
    output = case/'REVIEW.png'
    image.save(output)
    Image.open(output).verify()
    print(json.dumps({'case':case.name,'image':str(output),'dimensions':image.size,'targets':rows,'ifc_changed':False},ensure_ascii=False))


def render_elevation(case):
    html=(case/'VIEW.html').read_text(encoding='utf-8')
    data=json.loads(re.search(r'<script id="ifc-data" type="application/json">(.*?)</script>',html,re.S).group(1))
    target=data['before']['meshes'][data['target']]
    reference=data['before']['meshes'][data['refs'][0]]
    checks=json.loads((case/'private/checks.json').read_text(encoding='utf8'))
    host=checks['targets'][0]['wall_guid']
    x=float(center(target)[0])
    points=np.asarray([center(target)[[1,2]],center(reference)[[1,2]]])
    lo,hi=points.min(axis=0)-[1.05,1.5],points.max(axis=0)+[1.05,1.5]
    span=hi-lo
    if span[0]/span[1]<1.64:
        padding=(span[1]*1.64-span[0])/2
        lo[0]-=padding;hi[0]+=padding
    else:
        padding=(span[0]/1.64-span[1])/2
        lo[1]-=padding;hi[1]+=padding
    image=Image.new('RGB',(1800,810),'white')
    draw=ImageDraw.Draw(image)
    text(draw,(25,15),data['title']+' · 目标墙立面放大',size=31)
    text(draw,(25,64),'900 × 500 mm 小窗；D 已删除窗及洞口，墙体恢复连续实体。',size=25)
    text(draw,(25,106),f'真实 IFC 网格剖切 X={x:.4f} m；横轴 Y，竖轴 Z。仅显示宿主墙、目标与保留参照。',size=22)
    text(draw,(25,145),'红：G 中被删窗；D 红十字仅标注位置。蓝：保留窗。灰：墙体。两侧同尺度。',size=22)
    keep={host,data['target'],*data['refs']}
    limits=(lo[0],hi[0],lo[1],hi[1])
    for key,area,caption,damaged in [('before',(25,198,885,775),'G · 损坏前',False),('after',(915,198,1775,775),'D · 损坏后',True)]:
        meshes={g:m for g,m in data[key]['meshes'].items() if g in keep}
        panel(draw,area,meshes,data,target,reference,limits,x,caption,damaged,normal_axis=0,display_axes=(1,2))
    output=case/'REVIEW-ELEVATION.png'
    image.save(output)
    Image.open(output).verify()
    print(json.dumps({'case':case.name,'image':str(output),'dimensions':image.size,'ifc_changed':False},ensure_ascii=False))


if __name__=='__main__':
    for folder in sorted(ROOT.glob('formal-*')):
        render(folder)
