import {t} from './i18n.mjs';
/** Read-only IFC browsing data. Source labels and values are retained; no model inference. */
export function scalar(x){
 if(x==null)return null;
 if(typeof x!=='object')return x;
 if('value' in x)return scalar(x.value);
 if('_representationValue' in x)return scalar(x._representationValue);
 if('_internalValue' in x)return scalar(x._internalValue);
 return x;
}
export function formatValue(x){
 const value=scalar(x),label=String(x?.name||x?.label||'').toUpperCase();
 if(value==null)return t('value.missing');
 if(value===true)return t('value.yes');if(value===false)return t('value.no');
 if(label.includes('LOGICAL')){if(value==='T'||value==='TRUE')return t('value.yes');if(value==='F'||value==='FALSE')return t('value.no');if(value==='U'||value==='UNKNOWN')return t('value.unknown');}
 if(Array.isArray(value))return value.length?value.map(formatValue).join(t('value.separator')):t('value.emptyList');
 if(typeof value==='number')return Number.isFinite(value)?String(value):t('value.invalid');
 if(typeof value==='object')return value.Name?formatValue(value.Name):value.expressID?'#'+value.expressID:JSON.stringify(value);
 return String(value);
}
export function unitLabel(u){
 if(!u)return '';const name=scalar(u.Name),prefix=scalar(u.Prefix)||'';
 const prefixes={MILLI:'m',CENTI:'c',DECI:'d',KILO:'k',MICRO:'µ',MEGA:'M'};
 const base={METRE:'m',SQUARE_METRE:'m²',CUBIC_METRE:'m³',GRAM:'g',SECOND:'s',RADIAN:'rad',DEGREE_CELSIUS:'°C',KELVIN:'K',NEWTON:'N',PASCAL:'Pa',WATT:'W',AMPERE:'A'};
 if(name)return (prefixes[prefix]??prefix)+(base[name]??name);
 if(u.Elements)return u.Elements.map(e=>unitLabel(e.Unit)+(scalar(e.Exponent)!==1?'^'+scalar(e.Exponent):'')).join('·');
 return u.expressID?t('property.unitRef',{id:u.expressID}):'';
}
const spatial=new Set(['IfcProject','IfcSite','IfcBuilding','IfcBuildingStorey','IfcSpace']);
export function groupModel(records){
 const classes=new Map();for(const r of records){if(!classes.has(r.type))classes.set(r.type,[]);classes.get(r.type).push(r);}
 const groups=[...classes].sort(([a],[b])=>a.localeCompare(b)).map(([type,items])=>({type,items:items.sort((a,b)=>(a.name||'').localeCompare(b.name||'')||a.id-b.id)}));
 return {spatial:groups.filter(g=>spatial.has(g.type)),elements:groups.filter(g=>!spatial.has(g.type))};
}
function quantityUnit(key){return {LengthValue:'LENGTHUNIT',AreaValue:'AREAUNIT',VolumeValue:'VOLUMEUNIT',WeightValue:'MASSUNIT',TimeValue:'TIMEUNIT'}[key];}
function measureUnit(value){const kind=String(value?.name||value?.label||'').toUpperCase();return kind.includes('LENGTH')?'LENGTHUNIT':kind.includes('AREA')?'AREAUNIT':kind.includes('VOLUME')?'VOLUMEUNIT':kind.includes('MASS')?'MASSUNIT':kind.includes('TIME')?'TIMEUNIT':null;}
function propertyRow(p,units){
 const name=formatValue(p.Name),row={name,id:p.expressID||null,value:t('value.missing'),unit:'',children:[]};
 if(p.HasProperties||p.HasQuantities){row.value=t('property.complex');row.children=(p.HasProperties||p.HasQuantities).map(x=>propertyRow(x,units));return row;}
 let raw,unitType;
 if('NominalValue' in p){raw=p.NominalValue;unitType=measureUnit(raw);}
 else if('EnumerationValues' in p)raw=p.EnumerationValues;
 else if('ListValues' in p)raw=p.ListValues;
 else if('UpperBoundValue' in p||'LowerBoundValue' in p){raw=t('property.lowerUpper',{lower:formatValue(p.LowerBoundValue),upper:formatValue(p.UpperBoundValue)})+(p.SetPointValue!=null?t('property.setpoint',{value:formatValue(p.SetPointValue)}):'');unitType=measureUnit(p.LowerBoundValue||p.UpperBoundValue);}
 else if('DefiningValues' in p){raw=`${formatValue(p.DefiningValues)} → ${formatValue(p.DefinedValues)}`;}
 else if(p.PropertyReference)raw=p.PropertyReference;
 else {const key=Object.keys(p).find(k=>/^(Length|Area|Volume|Count|Weight|Time|Number)Value$/.test(k));if(key){raw=p[key];unitType=quantityUnit(key);}else raw=t('property.rawExpression');}
 row.value=formatValue(raw);row.unit=unitLabel(p.Unit)||(unitType?units[unitType]||t('property.noProjectUnit'):'');return row;
}
export function propertyGroups(psets,units={}){
 return (psets||[]).filter(Boolean).map(p=>({id:p.expressID||null,name:formatValue(p.Name),kind:p.Quantities?'Qto':'Pset',rows:(p.HasProperties||p.Quantities||[]).map(x=>propertyRow(x,units))}));
}
function ids(api,model,type){if(!type)return [];const v=api.GetLineIDsWithType(model,type,true);return Array.from({length:v.size()},(_,i)=>v.get(i));}
const handle=h=>typeof h==='number'?h:typeof h?.value==='number'?h.value:h?.expressID;
const append=(map,key,value)=>{if(!map.has(key))map.set(key,[]);if(!map.get(key).includes(value))map.get(key).push(value);};
export function readModelIndex(api,W,model,records){
 const units={},psets=new Map(),types=new Map(),materials=new Map(),containers=new Map(),parents=new Map(),errors=[];
 const read=id=>api.GetLine(model,id);
 for(const id of ids(api,model,W.IFCPROJECT)){const p=read(id);records.set(id,{id,type:'IfcProject',name:scalar(p.Name),guid:scalar(p.GlobalId),representation:false});}
 function relations(type,visit){for(const id of ids(api,model,type)){try{visit(read(id));}catch(e){errors.push({id,message:e.message});}}}
 relations(W.IFCUNITASSIGNMENT,r=>{for(const u of r.Units||[]){const x=api.GetLine(model,handle(u),true);units[scalar(x.UnitType)||'OTHER']=unitLabel(x);}});
 relations(W.IFCRELDEFINESBYPROPERTIES,r=>{for(const h of r.RelatedObjects||[])append(psets,handle(h),handle(r.RelatingPropertyDefinition));});
 relations(W.IFCRELDEFINESBYTYPE,r=>{for(const h of r.RelatedObjects||[])append(types,handle(h),handle(r.RelatingType));});
 relations(W.IFCRELASSOCIATESMATERIAL,r=>{for(const h of r.RelatedObjects||[])append(materials,handle(h),handle(r.RelatingMaterial));});
 relations(W.IFCRELCONTAINEDINSPATIALSTRUCTURE,r=>{for(const h of r.RelatedElements||[])append(containers,handle(h),handle(r.RelatingStructure));});
 relations(W.IFCRELAGGREGATES,r=>{for(const h of r.RelatedObjects||[])append(parents,handle(h),handle(r.RelatingObject));});
 function floors(id,visited=new Set()){
  if(visited.has(id))return [];visited.add(id);const rec=records.get(id);if(rec?.type==='IfcBuildingStorey')return [id];
  return [...new Set([...(containers.get(id)||[]),...(parents.get(id)||[])].flatMap(i=>floors(i,visited)))];
 }
 for(const [id,r] of records){r.storeys=floors(id).map(i=>({id:i,name:records.get(i)?.name||'IfcBuildingStorey #'+i}));r.decompositionChildren=[];if(r.type==='IfcProject')r.displayRole='spatial';}
  for(const [child,ownerIds] of parents)for(const owner of ownerIds){const parent=records.get(owner);if(parent)parent.decompositionChildren.push(child);}
 return {units,psets,types,materials,containers,parents,errors};
}
export function readInspection(api,model,id,index){
 const basic=api.GetLine(model,id),errors=[];
 const deep=i=>{try{return api.GetLine(model,i,true);}catch(e){errors.push({id:i,message:e.message});return null;}};
 const instance=(index.psets.get(id)||[]).map(deep).filter(Boolean);
 const types=(index.types.get(id)||[]).map(i=>{
  const t=api.GetLine(model,i);return {id:i,name:formatValue(t.Name),psets:(t.HasPropertySets||[]).map(h=>deep(handle(h))).filter(Boolean)};
 });
 const materials=[];
 for(const owner of [id,...(index.types.get(id)||[])])for(const mid of index.materials.get(owner)||[]){const x=deep(mid);if(x)materials.push({owner,origin:owner===id?'instance':'type',material:x});}
 return {basic:{Name:basic.Name,Description:basic.Description,GlobalId:basic.GlobalId,Tag:basic.Tag,Elevation:basic.Elevation},instance,types,materials,units:index.units,errors};
}
export function materialRows(entries){
 const rows=[];
 function visit(x,origin,path='',depth=0){
  if(!x||depth>6)return;
  if(x.Material){const m=x.Material;rows.push({name:formatValue(m.Name),value:x.LayerThickness!=null?formatValue(x.LayerThickness):'—',unit:'',origin,id:m.expressID});return;}
  if(x.MaterialLayers){for(const l of x.MaterialLayers)visit(l,origin,path,depth+1);return;}
  if(x.ForLayerSet){visit(x.ForLayerSet,origin,path,depth+1);return;}
  if(x.Materials){for(const m of x.Materials)visit(m,origin,path,depth+1);return;}
  if(x.Name)rows.push({name:formatValue(x.Name),value:'—',unit:'',origin,id:x.expressID});
  else rows.push({name:t('property.materialRef',{id:x.expressID}),value:t('property.rawExpression'),unit:'',origin,id:x.expressID});
 }
 for(const e of entries)visit(e.material,e.origin);return rows;
}
