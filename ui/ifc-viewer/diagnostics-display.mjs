import {t} from './i18n.mjs';
import {loadMessage} from './display-geometry.mjs';
const spatialTypes=new Set(['IfcProject','IfcSite','IfcBuilding','IfcBuildingStorey']);
const auxiliaryTypes=new Set(['IfcOpeningElement','IfcSpace','IfcAnnotation']);

/** IFC2X3: optional Representation and actual aggregation are separate from missing meshes.
 * Never excuse a missing supplied representation just because the type is spatial/aggregate.
 */
export function classifyDisplayRecords(records,renderedIds){
 const rows=Array.from(records instanceof Map?records.values():records),byId=new Map(rows.map(r=>[r.id,r]));
 const rendered=renderedIds instanceof Set?renderedIds:new Set(renderedIds);
 const out={spatial:[],aggregates:[],incompleteAggregates:[],otherWithoutRepresentation:[],missing:[],displayExcluded:[],direct:[]};
 function represented(id,trail=new Set()){
  if(trail.has(id))return false;const r=byId.get(id);if(!r)return false;
  if(auxiliaryTypes.has(r.type))return true;
  if(rendered.has(id))return true;
  if(r.representation)return false;
  const children=r.decompositionChildren||[];if(!children.length)return false;
  const next=new Set(trail);next.add(id);
  return children.some(c=>!auxiliaryTypes.has(byId.get(c)?.type))&&children.every(c=>represented(c,next));
 }
 for(const r of rows){
  let kind;
  if(auxiliaryTypes.has(r.type)){out.displayExcluded.push(r.id);kind='auxiliary';}
  else if(rendered.has(r.id)){out.direct.push(r.id);kind='geometry';}
  else if(r.representation){out.missing.push(r.id);kind='missing';}
  else if(spatialTypes.has(r.type)){out.spatial.push(r.id);kind='spatial';}
  else if((r.decompositionChildren||[]).length){const ok=represented(r.id);out[ok?'aggregates':'incompleteAggregates'].push(r.id);kind=ok?'aggregate':'incomplete_aggregate';}
  else {out.otherWithoutRepresentation.push(r.id);kind='no_direct_representation';}
  r.displayRole=kind; // Display metadata only; never written back to IFC.
 }
 return out;
}

export function summarizeDiagnostics(report){
 const coverage=report.coverage,details=report.native?.diagnosticAudit;
 const count=report.native?report.native.diagnostics.errors:report.diagnostics.length;
 const result=loadMessage(coverage,count);
 const classification=report.displayClassification;
 const knownMaterials=count>0&&details?.error_count===count&&details.errors?.length>0&&details.errors.every(e=>e.instance?.includes('=IfcMaterial('));
 const incomplete=classification?.incompleteAggregates.length||0;
 if(!coverage.missing.length&&!incomplete&&knownMaterials)result.text=t('display.materialCompact',{count:report.geometry.renderedProducts,unique:details.distinct_error_count});
 if(incomplete){result.level='warning';result.text=t('display.aggregateIncompleteSummary',{count:incomplete});}
 const byId=new Map((report.sourceProducts||[]).map(x=>[x.id,x]));
 const classes=ids=>{const counts=new Map();for(const id of ids){const type=byId.get(typeof id==='number'?id:id.id)?.type||id.type||'Unknown';counts.set(type,(counts.get(type)||0)+1);}return [...counts].map(([k,v])=>k+' × '+v).join('、');};
 const lines=[t('display.meshCount',{count:report.geometry.renderedProducts,triangles:report.geometry.triangles.toLocaleString()})];
 if(classification){
  if(classification.spatial.length)lines.push(t('display.spatialNormal',{count:classification.spatial.length,items:classes(classification.spatial)}));
  if(classification.aggregates.length)lines.push(t('display.aggregateNormal',{count:classification.aggregates.length,items:classes(classification.aggregates)}));
  if(incomplete)lines.push(t('display.aggregateIncomplete',{ids:classification.incompleteAggregates.join(', ')}));
  if(classification.otherWithoutRepresentation.length)lines.push(t('display.otherNoRepresentation',{items:classes(classification.otherWithoutRepresentation)}));
 }else if(coverage.noRepresentation.length)lines.push(t('display.noRepDetail',{items:classes(coverage.noRepresentation)}));
 if(coverage.excluded.length)lines.push(t('display.auxiliaryPolicy',{items:classes(coverage.excluded)}));
 for(const item of details?.errors||[]){
  lines.push(t('display.materialDetail',{message:item.message,count:item.count,instances:item.instance}));
  if(item.material_has_representation===false)lines.push(t('display.materialOptional'));
 }
 if(details?.style_audit)lines.push(t('display.materialAssignment',{explicit:details.style_audit.products_with_explicit_style,total:details.style_audit.rendered_products,missing:details.style_audit.unassigned_triangles}));
 if(coverage.missing.length)lines.push(t('display.missing',{ids:coverage.missing.join(', ')}));
 lines.push(t('display.scopeBrief'));
 return {...result,classification,detail:lines.join('\n\n')};
}
