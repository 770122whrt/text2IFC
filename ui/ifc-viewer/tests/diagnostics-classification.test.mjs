import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyDisplayRecords,summarizeDiagnostics} from '../diagnostics-display.mjs';

const rec=(id,type,representation=false,children=[])=>({id,type,representation,decompositionChildren:children});
test('spatial containers and verified aggregate geometry are not missing meshes',()=>{
 const rows=[rec(1,'IfcBuilding'),rec(2,'IfcBuildingStorey'),rec(3,'IfcRoof',false,[4]),rec(4,'IfcSlab',true),rec(5,'IfcStair',false,[6]),rec(6,'IfcStairFlight',true),rec(7,'IfcOpeningElement',true)];
 const c=classifyDisplayRecords(rows,new Set([4,6]));
 assert.deepEqual(c.spatial,[1,2]);assert.deepEqual(c.aggregates,[3,5]);assert.deepEqual(c.missing,[]);assert.deepEqual(c.otherWithoutRepresentation,[]);assert.deepEqual(c.displayExcluded,[7]);
});
test('aggregate type alone cannot excuse absent or failed children',()=>{
 const c=classifyDisplayRecords([rec(1,'IfcRoof'),rec(2,'IfcStair',false,[3]),rec(3,'IfcStairFlight',true)],new Set());
 assert.deepEqual(c.aggregates,[]);assert.deepEqual(c.otherWithoutRepresentation,[1]);assert.deepEqual(c.incompleteAggregates,[2]);assert.deepEqual(c.missing,[3]);
});
test('nested aggregate verifies every physical leaf and handles cycles',()=>{
 const c=classifyDisplayRecords([rec(1,'IfcRoof',false,[2]),rec(2,'IfcElementAssembly',false,[3]),rec(3,'IfcSlab',true),rec(4,'IfcStair',false,[5]),rec(5,'IfcElementAssembly',false,[4])],new Set([3]));
 assert.deepEqual(c.aggregates,[1,2]);assert.deepEqual(c.incompleteAggregates,[4,5]);
});
test('optional source geometry is distinct from supplied but unrendered site geometry',()=>{
 const c=classifyDisplayRecords([rec(1,'IfcSite',true),rec(2,'IfcWall')],new Set());
 assert.deepEqual(c.spatial,[]);assert.deepEqual(c.missing,[1]);assert.deepEqual(c.otherWithoutRepresentation,[2]);
});
test('ordinary structure facts live in detail, original parser errors remain visible',()=>{
 const rows=[rec(1,'IfcSite'),rec(2,'IfcRoof',false,[3]),rec(3,'IfcSlab',true)];
 const report={sourceProducts:rows,coverage:{rendered:[3],missing:[],excluded:[],noRepresentation:[1,2]},displayClassification:classifyDisplayRecords(rows,new Set([3])),geometry:{triangles:12,renderedProducts:1},diagnostics:[],native:{diagnostics:{errors:32},diagnosticAudit:{error_count:32,distinct_error_count:1,errors:[{level:'Error',instance:"#1145=IfcMaterial('<Unnamed>')",message:'Failed to convert:',count:32,material_has_representation:false}]}}};
 const s=summarizeDiagnostics(report);assert.match(s.text,/1/);assert.ok(!s.text.includes('32'));assert.ok(!s.text.includes('未验证'));assert.match(s.detail,/32/);assert.match(s.detail,/Error/);assert.match(s.detail,/1145/);assert.match(s.detail,/IfcRoof/);assert.ok(!s.detail.includes('12 个对象没有表示'));
});
