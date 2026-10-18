import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from '../vendor/three.module.js';
import {SelectionHighlighter} from '../selection-highlight.mjs';
import {groupModel,formatValue,propertyGroups,unitLabel} from '../inspection-data.mjs';

test('all submeshes get the same unlit, depth-tested highlight without source edits',()=>{
 const root=new T.Group(), a=new T.MeshBasicMaterial({color:0xabcdef}),b=new T.MeshPhongMaterial({color:0x111111,transparent:true,opacity:.1});
 root.add(new T.Mesh(new T.BoxGeometry(),a),new T.Mesh(new T.BoxGeometry(),b));
 const h=new SelectionHighlighter();h.select(root);
 for(const mesh of root.children){assert.equal(mesh.material.color.getHex(),0xd6ac5c);assert.equal(mesh.material.isMeshBasicMaterial,true);assert.equal(mesh.material.opacity,1);assert.equal(mesh.material.depthTest,true);assert.ok(mesh.material.polygonOffsetUnits<0);assert.ok(mesh.renderOrder>0);}
 assert.equal(a.color.getHex(),0xabcdef);assert.equal(b.opacity,.1);h.clear();assert.equal(root.children[0].material,a);assert.equal(root.children[1].material,b);assert.equal(root.children[0].renderOrder,0);
});
test('selection never changes vertex arrays and clears previous selection',()=>{
 const m=new T.Mesh(new T.BoxGeometry(),new T.MeshBasicMaterial()),g=new T.Group();g.add(m);const before=Array.from(m.geometry.attributes.position.array),h=new SelectionHighlighter();h.select(g);h.select(null);assert.deepEqual(Array.from(m.geometry.attributes.position.array),before);assert.equal(h.group,null);
});
test('clearing restores temporarily hidden geometric edge overlays',()=>{
 const m=new T.Mesh(new T.BoxGeometry(),new T.MeshBasicMaterial()),edge=new T.LineSegments();edge.userData.displayOverlay=true;m.add(edge);const g=new T.Group();g.add(m);const h=new SelectionHighlighter();h.select(g);assert.equal(edge.visible,false);h.clear();assert.equal(edge.visible,true);
});
test('tree groups actual classes, keeps non-geometric spatial objects and source counts',()=>{
 const rs=[{id:1,type:'IfcProject',name:'P'},{id:2,type:'IfcBuildingStorey'},{id:3,type:'IfcWall'},{id:4,type:'IfcWall'},{id:5,type:'IfcOpeningElement'}];
 const x=groupModel(rs);assert.equal(x.spatial.find(g=>g.type==='IfcProject').items.length,1);assert.equal(x.elements.find(g=>g.type==='IfcWall').items.length,2);assert.equal(x.elements.find(g=>g.type==='IfcOpeningElement').items.length,1);
});
test('value formatter does not erase false or zero, or render null as zero',()=>{
 assert.equal(formatValue({value:false}),'否');assert.equal(formatValue({value:0}),'0');assert.equal(formatValue(null),'未记录');assert.equal(formatValue({value:'UNKNOWN',label:'IfcLogical'}),'未知');
});
test('unit labels respect explicit prefixed SI units and conversion-based names',()=>{
 assert.equal(unitLabel({Name:{value:'METRE'},Prefix:{value:'MILLI'},UnitType:{value:'LENGTHUNIT'}}),'mm');assert.equal(unitLabel({Name:{value:'SQUARE_METRE'},Prefix:{value:'MILLI'},UnitType:{value:'AREAUNIT'}}),'mm²');assert.equal(unitLabel({Name:{value:'foot'},ConversionFactor:{}}),'foot');
});
test('pset fields and Qto remain separate with units and source IDs',()=>{
 const p=[{expressID:10,Name:{value:'Pset_WallCommon'},HasProperties:[{expressID:11,Name:{value:'LoadBearing'},NominalValue:{value:false}},{Name:{value:'Zero'},NominalValue:{value:0}}]}, {expressID:20,Name:{value:'BaseQuantities'},Quantities:[{expressID:21,Name:{value:'Height'},LengthValue:3.4}]}];
 const groups=propertyGroups(p,{LENGTHUNIT:'m'});assert.equal(groups[0].rows[0].value,'否');assert.equal(groups[0].rows[1].value,'0');assert.equal(groups[1].rows[0].value,'3.4');assert.equal(groups[1].rows[0].unit,'m');assert.equal(groups[1].kind,'Qto');
});
test('explicit property unit overrides project unit without changing numeric value',()=>{
 const p=[{Name:{value:'P'},HasProperties:[{Name:{value:'Width'},NominalValue:{value:1000,label:'IfcLengthMeasure'},Unit:{Name:{value:'METRE'},Prefix:{value:'MILLI'},UnitType:{value:'LENGTHUNIT'}}}]}];
 const row=propertyGroups(p,{LENGTHUNIT:'m'})[0].rows[0];assert.equal(row.value,'1000');assert.equal(row.unit,'mm');
});
test('complex and enumerated values have readable children and never silently vanish',()=>{
 const p=[{Name:{value:'P'},HasProperties:[{Name:{value:'Choice'},EnumerationValues:[{value:'A'},{value:'B'}]},{Name:{value:'Nested'},HasProperties:[{Name:{value:'Rate'},NominalValue:{value:0}}]}]}];
 const rows=propertyGroups(p,{})[0].rows;assert.equal(rows[0].value,'A、B');assert.equal(rows[1].children[0].value,'0');
});
