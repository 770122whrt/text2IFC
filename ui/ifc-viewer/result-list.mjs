import {t,getLanguage} from './i18n.mjs';
const opNames={fill_existing_opening_with_door:['在现有洞口补门','Fill existing opening with door'],add_window_with_opening_to_wall:['新增窗与洞口','Add window and opening'],add_door_to_existing_opening:['补门','Add door'],add_column:['新增柱','Add column']};
export function renderResultList(host,summary,onLocate){
 if(!summary?.available)return;
 const box=document.createElement('section');box.id='operationResults';
 const h=document.createElement('h4');h.textContent=t('result.title');box.append(h);
 const total=document.createElement('p');total.textContent=t('result.itemCount',{passed:summary.published_operations,total:summary.operation_total});box.append(total);
 for(const row of summary.rows||[]){
  const card=document.createElement('div');card.className='operation-result';card.dataset.operationId=row.operation_id;
  const title=document.createElement('strong');title.textContent=opNames[row.operation_type]?.[getLanguage()==='zh'?0:1]||row.operation_type;
  const status=document.createElement('p');status.textContent=t(row.status==='published'?'result.passed':row.status==='applied_not_published'?'result.applied':'result.pending');card.append(title,status);
  for(const category of ['created','modified'])for(const obj of row[category]||[]){
   const line=document.createElement('div');line.className='result-object';
   const name=document.createElement('span');name.textContent=t('result.'+category)+' · '+(obj.name||obj.ifc_class)+' #'+obj.step_id;
   const button=document.createElement('button');button.type='button';button.textContent=t('result.locate');button.dataset.resultGuid=obj.global_id;button.onclick=()=>onLocate(obj.global_id);line.append(name,button);card.append(line);
  }
  box.append(card);
 }
 host.append(box);
}
