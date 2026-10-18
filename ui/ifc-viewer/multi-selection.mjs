/** Viewer selection state, independent of Repair execution and IFC geometry. */
import {inspect} from '../prototype/core.mjs';
import {SelectionHighlighter} from './selection-highlight.mjs';
export function targetRefs(s){return s.multiSelect?(s.targets||[]):s.reference?[s.reference]:[];}
export function setMulti(s,value){
 if(s.mode!=='select'||s.version!==s.baseVersion)throw Error('MULTI_SELECT_MODE_REQUIRED');
 if(value&&!s.multiSelect){s.targets=s.reference?[{...s.reference}]:[];s.reference=null;}
 if(!value&&s.multiSelect){if((s.targets||[]).length>1)throw Error('MULTI_CLEAR_TO_SINGLE');s.reference=s.targets?.[0]||null;s.targets=[];}
 s.multiSelect=!!value;s.pickRole='primary';
}
export function pickTarget(s,id,{additive=false,locked=false}={}){
 if(locked){s.inspected=id;s.propertiesOpen=false;return;}
 if(additive&&!s.multiSelect&&s.mode==='select'&&s.version===s.baseVersion)setMulti(s,true);
 if(!s.multiSelect)return inspect(s,id);
 s.inspected=id;s.propertiesOpen=false;
 if(s.mode!=='select'||s.version!==s.baseVersion)return;
 const refs=s.targets||=[];
 if(s.pickRole==='auxiliary'){
  if(refs.some(r=>r.id===id))throw Error('DUPLICATE_SELECTION_ROLES');
  s.auxReference={id,version:s.baseVersion};s.pickRole='primary';return;
 }
 if(s.auxReference?.id===id&&s.auxReference.version===s.baseVersion)throw Error('DUPLICATE_SELECTION_ROLES');
 const index=refs.findIndex(r=>r.id===id);
 if(index>=0){refs.splice(index,1);s.inspected=null;}
 else {if(refs.length>=16)throw Error('MULTI_TARGET_LIMIT');refs.push({id,version:s.baseVersion});}
}
export function removeTarget(s,id){if(s.mode!=='select')throw Error('MULTI_SELECT_MODE_REQUIRED');if(s.multiSelect)s.targets=(s.targets||[]).filter(r=>r.id!==id);else if(s.reference?.id===id)s.reference=null;if(s.inspected===id)s.inspected=null;}
export function clearTargets(s){if(s.mode!=='select')throw Error('MULTI_SELECT_MODE_REQUIRED');s.targets=[];s.reference=null;s.inspected=null;}

/** One overlay per selected product, never per IFC class. */
export class TargetHighlighters {
 constructor(){this.active=new Map();}
 sync(groups,ids,through){
  const wanted=new Set(ids);
  for(const [id,item] of this.active)if(!wanted.has(id)||item.group!==groups.get(id)||!groups.get(id)?.visible){item.clear();this.active.delete(id);}
  for(const id of wanted){const group=groups.get(id);if(!group?.visible)continue;let item=this.active.get(id);if(!item){item=new SelectionHighlighter({through});item.select(group);this.active.set(id,item);}item.setThrough(through);}
 }
 clear(){for(const item of this.active.values())item.clear();this.active.clear();}
}
