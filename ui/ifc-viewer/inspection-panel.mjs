import {t,bindText} from './i18n.mjs';
import {groupModel,formatValue,propertyGroups,materialRows} from './inspection-data.mjs';
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};

/** Simple grouped model browser using native details/buttons for keyboard access. */
export class ModelTree {
 constructor(host,search,count,callbacks){this.host=host;this.search=search;this.count=count;this.callbacks=callbacks;this.rows=new Map();this.groups=[];search.addEventListener('input',()=>this.filter());}
 build(records,meshes,name){
  this.host.replaceChildren();this.rows.clear();this.groups=[];this.meshes=meshes;this.search.value='';
  this.host.append(el('div',name,'tree-model-name'));
  const grouped=groupModel([...records.values()]);
  const add=(category,parent)=>{
   const node=el('details',null,'tree-category'),sum=el('summary');sum.append(el('span',category.type),el('span','('+category.items.length+')','tree-count'));node.append(sum);node.dataset.type=category.type;
   for(const r of category.items){
    const row=el('div',null,'tree-leaf');row.dataset.id=String(r.id);row.dataset.search=[r.name,r.type,r.guid,'#'+r.id].filter(Boolean).join(' ').toLowerCase();
    const select=el('button',r.name||r.type+' #'+r.id,'tree-select');select.type='button';select.title=`${r.type} · #${r.id}\n${r.name||t('value.unnamed')}\n${r.guid||''}`;
    select.onclick=event=>this.callbacks.select(r.id,event);
    const status=el('span','','tree-item-status');const visibility=el('button','◉','tree-visibility');visibility.type='button';visibility.title=t('action.hide');visibility.onclick=()=>this.callbacks.visibility(r.id);
    row.append(select,el('span','#'+r.id,'tree-id'),status,visibility);node.append(row);this.rows.set(r.id,{row,select,status,visibility,rec:r});
   }
   parent.append(node);this.groups.push(node);
  };
  grouped.spatial.forEach(g=>add(g,this.host));
  const elements=el('details',null,'tree-elements');elements.open=true;const heading=el('summary');bindText(heading,'tree.elements',{count:grouped.elements.length});elements.append(heading);this.host.append(elements);
  grouped.elements.forEach(g=>add(g,elements));this.elements=elements;this.filter();
 }
 filter(){
  const q=this.search.value.trim().toLowerCase();let count=0;
  for(const {row} of this.rows.values()){row.hidden=q&&!row.dataset.search.includes(q);if(!row.hidden)count++;}
  for(const node of this.groups){const visible=[...node.querySelectorAll('.tree-leaf')].some(r=>!r.hidden);node.hidden=!visible;if(q&&visible)node.open=true;}
  if(this.elements)this.elements.hidden=![...this.elements.querySelectorAll('.tree-leaf')].some(r=>!r.hidden);
  bindText(this.count,q?'tree.found':'tree.total',{count,total:this.rows.size});
 }
 update({selected,hidden,mode,targetIds=[],multi=false}){
  const hs=new Set(hidden);
  for(const [id,x] of this.rows){x.row.classList.toggle('target-picked',multi&&targetIds.includes(id));x.select.dataset.picked=String(multi&&targetIds.includes(id));}
  for(const {select,rec} of this.rows.values())select.title=`${rec.type} · #${rec.id}\n${rec.name||t('value.unnamed')}\n${rec.guid||''}`;
  for(const [id,x] of this.rows){const drawable=this.meshes.has(id),isHidden=hs.has(id);x.row.classList.toggle('active',selected===id);x.select.setAttribute('aria-pressed',String(selected===id));x.visibility.hidden=!drawable;x.visibility.disabled=mode!=='view';x.visibility.textContent=isHidden?'○':'◉';x.visibility.title=t(mode!=='view'?'tree.switchView':isHidden?'action.show':'action.hide');x.visibility.setAttribute('aria-label',x.visibility.title+' '+(x.rec.name||'#'+id));x.status.textContent=isHidden?t('tree.hidden'):!drawable?t(['IfcOpeningElement','IfcSpace','IfcAnnotation'].includes(x.rec.type)?'tree.auxiliary':x.rec.representation?'tree.noMesh':'tree.noGeometry'):'';if(!drawable){const key={spatial:'tree.spatialRecord',aggregate:'tree.aggregateRecord',incomplete_aggregate:'tree.aggregateGap',no_direct_representation:'tree.noDirectShape'}[x.rec.displayRole];if(key)x.status.textContent=t(key);}x.status.title=['IfcOpeningElement','IfcSpace','IfcAnnotation'].includes(x.rec.type)?t('tree.auxiliaryHint'):x.status.textContent;}
 }
 reveal(id){const x=this.rows.get(id);if(!x||x.row.hidden)return;let p=x.row.parentElement;while(p&&p!==this.host){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement;}x.row.scrollIntoView({block:'nearest'});}
}
function table(rows){
 const result=el('table',null,'property-table');const body=el('tbody');result.append(body);
 function add(row,depth=0){const tr=el('tr');if(row.id)tr.dataset.sourceId=String(row.id);const th=el('th',row.name),td=el('td',row.value+(row.unit?' '+row.unit:''));th.scope='row';th.style.paddingLeft=(8+depth*12)+'px';if(row.id)th.title=t('property.sourceId',{id:row.id});tr.append(th,td);body.append(tr);for(const child of row.children||[])add(child,depth+1);}
 rows.forEach(r=>add(r));return result;
}
function section(host,title,content,open=false){const d=el('details',null,'property-section');d.open=open;d.append(el('summary',title),content);host.append(d);return d;}
export function renderInspection(host,rec,data,{preserveExpansion=false}={}){
 const open=preserveExpansion?[...host.querySelectorAll('details')].map(d=>d.open):null;
 const scroll=host.parentElement?.scrollTop||0;
 host.replaceChildren();
 const basics=el('dl',null,'property-basics');
 const basicRows=[[t('property.name'),rec.name||t('value.unnamed')],[t('property.class'),rec.type],['STEP ID','#'+rec.id],['GlobalId',rec.guid||t('value.missing')],[t('property.storey'),(rec.storeys||[]).map(s=>s.name).join(t('value.separator'))||t('value.missing')]];
 if(data.basic.Description!=null)basicRows.push([t('property.description'),formatValue(data.basic.Description)]);
 if(data.basic.Elevation!=null)basicRows.push([t('property.elevation'),formatValue(data.basic.Elevation)+' '+(data.units.LENGTHUNIT||'')]);
 for(const [k,v] of basicRows)basics.append(el('dt',k),el('dd',v));host.append(basics);
 host.append(el('p',t('property.sourceNote'),'muted'));
 const ig=propertyGroups(data.instance,data.units);host.append(el('h4',t('property.instance')));
 if(!ig.length)host.append(el('p',t('property.noInstance'),'muted'));
 ig.forEach((g,i)=>section(host,`${g.kind} · ${g.name}（${g.rows.length}）`,table(g.rows),/Common$/.test(g.name)||g.kind==='Qto'||ig.length===1));
 host.append(el('h4',t('property.type')));
 if(!data.types.length)host.append(el('p',t('property.noType'),'muted'));
 for(const type of data.types){const box=el('div');box.append(el('p',`${type.name} · #${type.id}`,'muted'));for(const g of propertyGroups(type.psets,data.units))section(box,`${g.kind} · ${g.name}（${g.rows.length}）`,table(g.rows),false);if(!type.psets.length)box.append(el('p',t('property.typeNoSets'),'muted'));section(host,'Type · '+type.name,box,false);}
 const material=materialRows(data.materials).map(r=>({...r,name:t(r.origin==='instance'?'property.instanceOrigin':'property.typeOrigin')+' · '+r.name,value:r.value==='—'?t('property.linked'):t('property.thickness',{value:r.value}),unit:r.value==='—'?'':data.units.LENGTHUNIT||t('property.noLengthUnit')}));
 if(material.length)section(host,t('property.materials',{count:material.length}),table(material),false);
 const units=Object.entries(data.units).map(([name,value])=>({name,value}));if(units.length)section(host,t('property.units'),table(units),false);
 if(data.errors.length)host.append(el('p',t('property.errors',{count:data.errors.length}),'property-error'));
 const raw=section(host,t('property.raw'),el('pre',JSON.stringify(data,null,2)),false);raw.id='rawProperty';
 if(open){[...host.querySelectorAll('details')].forEach((d,i)=>{if(i<open.length)d.open=open[i];});if(host.parentElement)host.parentElement.scrollTop=scroll;}
}
