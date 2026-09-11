"""Export reopened IFC meshes to an offline, self-contained review page."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


def render(source: Path, output: Path) -> None:
    model = ifcopenshell.open(str(source))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    products, failures = [], []
    for product in model.by_type("IfcElement"):
        if product.is_a("IfcOpeningElement") or not product.Representation:
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            mesh = shape.geometry
            materials = []
            for material in mesh.materials:
                color = material.diffuse
                opacity = 1.0 - material.transparency if material.transparency == material.transparency else 1.0
                materials.append([color.r(), color.g(), color.b(), opacity])
            products.append({"id": product.GlobalId, "name": product.Name or product.is_a(),
                             "kind": product.is_a(), "verts": list(mesh.verts), "faces": list(mesh.faces),
                             "materials": materials, "material_ids": list(mesh.material_ids),
                             "direct_property_sets": ifcopenshell.util.element.get_psets(product, should_inherit=False),
                             "effective_property_sets": ifcopenshell.util.element.get_psets(product),
                             "physical_materials": [m.Name for m in ifcopenshell.util.element.get_materials(product)]})
        except Exception as error:
            failures.append({"id": product.GlobalId, "error": type(error).__name__})
    payload = {"source": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "schema": model.schema, "products": products, "mesh_failures": failures}
    page = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(page)
    print(json.dumps({"output": str(output), "products": len(products), "mesh_failures": failures}))


HTML = r'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>text2IFC · IFC 检查</title>
<style>*{box-sizing:border-box}body{margin:0;color:#26322f;background:#f3f4f0;font:15px system-ui}header{padding:18px 28px;background:#fff;border-bottom:1px solid #d7ded8}h1{font-size:22px;margin:0 0 7px}nav{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:12px 28px}button,select{padding:9px 14px;border:1px solid #b9c8c0;border-radius:6px;background:white;color:#26322f}button:hover{background:#e7eee8}canvas{width:100%;height:calc(100vh - 176px);display:block;cursor:grab}small{color:#63736a}#status{padding:0 28px;font-size:12px}label{display:flex;gap:6px;align-items:center}</style>
<header><h1>text2IFC · 模型检查</h1><small id="meta"></small></header>
<nav><button onclick="setView(-.72,.52)">整体</button><button onclick="setView(0,0)">南立面</button><button onclick="setView(-Math.PI/2,0)">东立面</button><button onclick="setView(.72,1.35)">俯视</button><select id="selection" onchange="fit()"><option value="all">全部构件</option><option value="fillings">全部门窗</option></select><label><input id="walls" type="checkbox" checked onchange="fit()">显示墙体</label><button onclick="saveImage()">保存当前视图</button></nav>
<div id="status"></div><details style="margin:8px 28px"><summary>所选构件的 GUID、材料与属性</summary><pre id="properties" style="white-space:pre-wrap;max-height:240px;overflow:auto"></pre></details><canvas id="view"></canvas>
<script>const data=__DATA__;const canvas=document.getElementById('view'),gl=canvas.getContext('webgl',{antialias:true,preserveDrawingBuffer:true}),select=document.getElementById('selection');let yaw=-.72,pitch=.52,zoom=1,drag=null;
function shader(type,source){let s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec3 position;attribute vec4 color;varying vec4 tint;void main(){gl_Position=vec4(position,1.0);tint=color;}'));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec4 tint;void main(){gl_FragColor=tint;}'));gl.linkProgram(program);gl.useProgram(program);const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);for(let [name,size,offset] of [['position',3,0],['color',4,12]]){let location=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,size,gl.FLOAT,false,28,offset)}
document.getElementById('meta').textContent=data.source+' · '+data.schema+' · '+data.products.length+' 个可见构件 · 拖动旋转，滚轮缩放';
document.getElementById('status').textContent='实际重读 IFC 三角网格与材质样式；未显示空间体积和开口切割体。网格失败：'+data.mesh_failures.length+'。人工审查待确认。';
for(let i=0;i<data.products.length;i++){let p=data.products[i],o=document.createElement('option');o.value=String(i);o.textContent=p.kind+' · '+p.name;select.appendChild(o)}let selectedGuid=decodeURIComponent(location.hash.slice(1));let selectedIndex=data.products.findIndex(p=>p.id===selectedGuid);if(selectedIndex>=0)select.value=String(selectedIndex);
function chosen(){return data.products.filter((p,i)=>(select.value==='all'||select.value==='fillings'&&['IfcDoor','IfcWindow'].includes(p.kind)||select.value===String(i))&&(document.getElementById('walls').checked||!p.kind.startsWith('IfcWall')))}
function project(x,y,z){let u=x*Math.cos(yaw)-y*Math.sin(yaw),d=x*Math.sin(yaw)+y*Math.cos(yaw);return[u,d*Math.sin(pitch)+z*Math.cos(pitch),d*Math.cos(pitch)-z*Math.sin(pitch)]}
function setView(y,p){yaw=y;pitch=p;zoom=1;draw()}function fit(){zoom=1;draw()}
function draw(){document.getElementById('properties').textContent=JSON.stringify(chosen().map(p=>({GUID:p.id,Name:p.name,Class:p.kind,Materials:p.physical_materials,DirectProperties:p.direct_property_sets,EffectiveProperties:p.effective_property_sets})),null,2);let width=canvas.clientWidth,height=canvas.clientHeight;canvas.width=width*devicePixelRatio;canvas.height=height*devicePixelRatio;gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.953,.957,.941,1);gl.depthMask(true);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);let triangles=[],min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
for(let p of chosen()){let points=[];for(let i=0;i<p.verts.length;i+=3){let v=project(...p.verts.slice(i,i+3));points.push(v);for(let k=0;k<3;k++){min[k]=Math.min(min[k],v[k]);max[k]=Math.max(max[k],v[k])}}
for(let i=0;i<p.faces.length;i+=3){let vs=p.faces.slice(i,i+3).map(n=>points[n]),m=p.materials[p.material_ids[i/3]]||[.72,.74,.73,1];triangles.push({vs,m,d:vs.reduce((s,v)=>s+v[2],0)/3})}}
if(!triangles.length)return;let scale=Math.min((width-100)/(max[0]-min[0]||1),(height-70)/(max[1]-min[1]||1))*zoom,center=min.map((v,i)=>(v+max[i])/2);
function batch(items){let vertices=[];for(let t of items){let a=t.vs[1].map((v,i)=>v-t.vs[0][i]),b=t.vs[2].map((v,i)=>v-t.vs[0][i]);let n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],length=Math.hypot(...n)||1;let light=.76+.24*Math.abs((n[0]*.3+n[1]*.7-n[2]*.64)/length);let color=t.m.slice(0,3).map(v=>v*light);for(let v of t.vs)vertices.push((v[0]-center[0])*scale*2/width,(v[1]-center[1])*scale*2/height,(v[2]-center[2])*1.8/(max[2]-min[2]||1),...color,Math.max(0,Math.min(1,t.m[3])))}gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);gl.drawArrays(gl.TRIANGLES,0,vertices.length/7)}
gl.disable(gl.BLEND);batch(triangles.filter(t=>t.m[3]>=.999));gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);batch(triangles.filter(t=>t.m[3]<.999).sort((a,b)=>b.d-a.d));gl.depthMask(true)}
canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-drag[0])*.006;pitch=Math.max(-1.5,Math.min(1.5,pitch+(e.clientY-drag[1])*.006));drag=[e.clientX,e.clientY];draw()};canvas.onpointerup=()=>drag=null;canvas.onwheel=e=>{e.preventDefault();zoom=Math.max(.2,Math.min(8,zoom*Math.exp(-e.deltaY*.001)));draw()};window.onresize=draw;
function saveImage(){let a=document.createElement('a');a.download='text2IFC-view.png';a.href=canvas.toDataURL();a.click()}draw();</script></html>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.source, args.output)
