/** Real task UI. API reads never start/resume a run; only explicit writes do. */
import {RepairClient,requestSignature,preparePayload} from './repair-client.mjs';
import {renderResultList} from './result-list.mjs';
import {t,getLanguage,onLanguageChange,bindText} from './i18n.mjs';
const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const label=(tag,key,values)=>{const e=node(tag);bindText(e,key,values);return e;};
export const mergeByKey=(old,added,key)=>[...new Map([...old,...added].map(e=>[e[key],e])).values()].sort((a,b)=>a[key]-b[key]);
export const restorableTaskId=value=>/^task-[a-f0-9]{32}$/.test(value||'')?value:null;
export const candidateAnswerKind=modes=>modes.includes('authorize_prototype')?'authorize_prototype':modes.includes('select_candidate')?'select_candidate':null;
const stageKeys={created:'created',source_validated:'source',index_ready:'index',intent_ready:'intent',targets_resolved:'targets',changeset_ready:'changeset',ifc_repair_scene_grounding:'scene',ifc_repair_intent:'intent',ifc_repair_bound_changeset:'changeset',application:'application',reopen:'reopen',evaluation:'evaluation',succeeded:'succeeded',clarification_required:'clarification_required',audit_failed:'failed',provider_failed:'failed',application_failed:'failed',not_publishable:'failed',cancelled:'cancelled',queued:'queued',running:'running',interrupted:'interrupted'};
const stageText=s=>stageKeys[s]?t('repair.stage.'+stageKeys[s]):s;

export class RepairPanel {
 constructor({host,snapshot,onStarted=()=>{},onRestoreSource=async()=>{},onResult=async()=>{},onPreviewCandidate=async()=>false,onLocateObject=()=>{},onStateChange=()=>{},client=new RepairClient()}){
  Object.assign(this,{host,snapshot,onStarted,onRestoreSource,onResult,onPreviewCandidate,onLocateObject,onStateChange,client,busy:false,prepared:null,task:null,timer:null,cache:null,error:null,epoch:0,events:[],activity:[],files:[],cursor:-1,activityCursor:-1});
  this.off=onLanguageChange(()=>this.render());
 }
 get locked(){return this.busy||!!this.task?.busy||this.task?.status==='clarification_required';}
 remember(){
  if(!this.task)return;
  const url=new URL(location.href);url.searchParams.set('task',this.task.task_id);history.replaceState(null,'',url);
  try{sessionStorage.setItem('text2ifc.lastTask',this.task.task_id);}catch{}
 }
 invalidate(){if(this.prepared&&!this.task&&requestSignature(this.snapshot())!==this.signature){this.prepared=null;this.error='REPAIR_REQUEST_CHANGED';this.render();}}
 async prepare(){
  if(this.locked)return;
  const current=this.snapshot();if(!current.bytes||!current.text.trim())return;
  const epoch=++this.epoch;this.signature=requestSignature(current);this.busy=true;this.error=null;this.prepared=null;this.task=null;this.fileView=null;this.resultLoaded=null;this.events=[];this.activity=[];this.files=[];this.cursor=-1;this.activityCursor=-1;clearTimeout(this.timer);this.render();
  try{
   await this.client.capabilities();
   if(!this.cache||this.cache.version!==current.version||this.cache.bytes!==current.bytes){const input=await this.client.upload(current.bytes,current.name);if(epoch!==this.epoch)return;this.cache={version:current.version,bytes:current.bytes,input};}
   const result=await this.client.prepare(preparePayload(current,this.cache.input.input_id,getLanguage()));
   if(epoch!==this.epoch)return;
   if(this.signature!==requestSignature(this.snapshot()))throw Error('REPAIR_REQUEST_CHANGED');
   this.prepared=result;this.frozen=current;this.startId=crypto.randomUUID();
  }catch(error){if(epoch===this.epoch)this.error=error.code||error.message||'REPAIR_API_UNAVAILABLE';}
  finally{if(epoch===this.epoch){this.busy=false;this.render();}}
 }
 async start(){
  if(this.busy||!this.prepared?.execution_enabled)return;
  if(this.signature!==requestSignature(this.snapshot())){this.invalidate();return;}
  const epoch=this.epoch;this.busy=true;this.render();
  try{const task=await this.client.start(this.prepared.prepared_request_id,this.startId);if(epoch!==this.epoch)return;this.task=task;this.remember();this.onStarted(task,this.prepared,this.frozen);await this.poll();}
  catch(error){if(epoch===this.epoch)this.error=error.code||error.message;}
  finally{if(epoch===this.epoch){this.busy=false;this.render();}}
 }
 async restore(id){
  id=restorableTaskId(id);if(!id)return false;
  const epoch=++this.epoch;this.busy=true;this.restoring=true;this.error=null;this.render();
  try{
   const task=await this.client.task(id),prepared=await this.client.prepared(task.prepared_request_id),input=await this.client.input(prepared.input_id);
   if(epoch!==this.epoch)return false;
   await this.onRestoreSource(await this.client.resource(input.download_url),input.source_name,prepared);
   if(epoch!==this.epoch)return false;
   this.prepared=prepared;this.task=task;this.frozen=this.snapshot();this.signature=requestSignature(this.frozen);this.events=[];this.activity=[];this.cursor=-1;this.activityCursor=-1;this.files=[];this.resultLoaded=null;this.onStarted(task,prepared,this.frozen);this.remember();await this.poll();return true;
  }catch(error){this.error=error.code||error.message;return false;}
  finally{if(epoch===this.epoch){this.busy=false;this.restoring=false;this.render();}}
 }
 async poll(){
  if(!this.task)return;
  const epoch=this.epoch,id=this.task.task_id;clearTimeout(this.timer);
  try{
   const task=await this.client.task(id),events=await this.client.events(id,this.cursor,this.activityCursor),files=await this.client.artifacts(id),summary=task.busy?null:await this.client.summary(id);
   if(epoch!==this.epoch||id!==this.task?.task_id)return;
   this.task=task;this.events=mergeByKey(this.events,events.events||[],'event_seq');this.activity=mergeByKey(this.activity,events.activity||[],'activity_seq');this.cursor=events.cursor;this.activityCursor=events.activity_cursor??this.activityCursor;this.files=files.artifacts;this.resultSummary=summary;this.error=null;
   const final=this.files.find(x=>x.role==='successful_ifc');
   if(task.successful_artifact_publishable&&final&&this.resultLoaded!==final.artifact_id){
    this.resultLoaded=final.artifact_id;
    try{await this.onResult(final,task,this.prepared);}catch(error){this.displayError=error.code||error.message;this.resultLoaded=null;}
   }
   if(this.task.busy)this.timer=setTimeout(()=>this.poll(),1000);
  }catch(error){if(epoch!==this.epoch)return;this.error=error.code||error.message;if(this.task?.busy)this.timer=setTimeout(()=>this.poll(),1500);}
  if(epoch===this.epoch)this.render();
 }
 async answer(answer){
  if(this.busy||!this.task?.clarification)return;
  this.busy=true;this.error=null;const epoch=this.epoch,q=this.task.clarification;
  const content=JSON.stringify([q.clarification_id,this.task.state_version,answer]);
  if(this.answerContent!==content){this.answerContent=content;this.answerId=crypto.randomUUID();}
  this.render();
  try{const task=await this.client.answer(this.task.task_id,{clarification_id:q.clarification_id,expected_state_version:this.task.state_version,answer,client_answer_id:this.answerId});if(epoch!==this.epoch)return;this.task=task;await this.poll();}
  catch(error){if(epoch===this.epoch)this.error=error.code||error.message;}
  finally{if(epoch===this.epoch){this.busy=false;this.render();}}
 }
 async previewCandidate(candidate){
  const key=this.task?.clarification?.clarification_id;this.previewedToken=candidate.token;
  try{this.previewMessage=await this.onPreviewCandidate(candidate,this.task)?t('repair.previewLocated'):t('repair.previewTextOnly');}
  catch{this.previewMessage=t('repair.previewTextOnly');}
  if(key===this.task?.clarification?.clarification_id)this.render();
 }
 async openArtifact(file){
  const epoch=this.epoch;this.fileView={id:file.artifact_id,name:file.relative_path||file.name,loading:true};this.render();
  try{
   if(file.size_bytes>4*1024*1024)throw Error('ARTIFACT_TOO_LARGE_FOR_INLINE_VIEW');
   let text=await this.client.resource(file.download_url,{text:true});
   if(file.name.endsWith('.json'))text=JSON.stringify(JSON.parse(text),null,2);
   if(epoch===this.epoch)this.fileView={id:file.artifact_id,name:file.relative_path||file.name,text};
  }catch(error){if(epoch===this.epoch)this.fileView={id:file.artifact_id,name:file.name,text:error.code||error.message};}
  if(epoch===this.epoch)this.render();
 }
 render(){
  const scroll=this.host.parentElement?.scrollTop;
  const open=new Map([...this.host.querySelectorAll('details[data-key]')].map(d=>[d.dataset.key,d.open]));
  const active=document.activeElement,focusKey=this.host.contains(active)?active.dataset.focusKey:null;
  const selection=focusKey&&typeof active.selectionStart==='number'?[active.selectionStart,active.selectionEnd]:null;
  const qkey=this.task?.clarification?this.task.run_id+':'+this.task.clarification.clarification_id:null;
  const draft=qkey===this.shownQuestion?(this.host.querySelector('textarea')?.value??this.answerDraft??''):'';
  if(qkey!==this.shownQuestion){this.previewedToken=null;this.previewMessage=null;}
  this.shownQuestion=qkey;this.answerDraft=draft;
  this.host.hidden=!(this.busy||this.error||this.prepared||this.task);this.host.replaceChildren();
  if(this.host.hidden){this.onStateChange();return;}
  this.host.append(label('h3',this.task?'repair.task':'repair.preview'));
  if(this.busy)this.host.append(label('p',this.task?'repair.started':'repair.preparing'));
  if(this.error)this.host.append(label('p',this.error==='REPAIR_REQUEST_CHANGED'?'repair.stale':'repair.failed',{code:this.error}));
  if(this.prepared){
   if(this.prepared.execution_mode==='offline_fixture')this.host.append(label('p','repair.offline'));
   if(!this.task)this.host.append(label('p',this.prepared.execution_enabled?'repair.ready':'repair.disabled'));
   for(const [key,title,text] of [['selection','repair.details',this.prepared.selection_context_text||t('repair.none')],['input','repair.full',this.prepared.effective_repair_text]]){
    const d=node('details');d.dataset.key=key;d.open=open.get(key)??(key==='selection'&&!this.task);d.append(label('summary',title),node('pre',text));this.host.append(d);
   }
   if(!this.task){const b=label('button','repair.start');b.type='button';b.id='repairStart';b.disabled=this.busy||!this.prepared.execution_enabled;b.onclick=()=>this.start();this.host.append(b);}
  }
  if(this.task){
   this.host.append(label('p','repair.status',{status:stageText(this.task.status)}),node('small',this.task.run_id));
   if(this.task.reason_code)this.host.append(node('p',this.task.reason_code));
   if(!this.task.busy)renderResultList(this.host,this.resultSummary,this.onLocateObject);
   const timeline=node('details');timeline.dataset.key='timeline';timeline.open=open.get('timeline')??true;timeline.append(label('summary','repair.boundaries'));
   const progress=node('ol');for(const e of this.events){const li=node('li',stageText(e.stage));if(e.clarification)li.append(node('p',e.clarification.question));if(e.answer?.detail)li.append(node('p',e.answer.detail));progress.append(li);}timeline.append(progress);
   const calls=node('details');calls.dataset.key='calls';calls.open=open.get('calls')??false;calls.append(label('summary','repair.attemptDetails'));
   for(const e of this.activity){const line=node('p',stageText(e.stage)+' · '+t('repair.action.'+e.action)+(e.attempt?' · '+t('repair.attempt',{n:e.attempt}):''));line.className='repair-activity';calls.append(line);}timeline.append(calls);this.host.append(timeline);
   const q=this.task.clarification;
   if(q){
    this.host.append(node('p',q.question,'repair-question'));const modes=q.answer_modes||[];
    if(modes.includes('add_detail')){const input=node('textarea');input.id='repairAnswer';input.dataset.focusKey='answer';input.value=draft;input.setAttribute('aria-label',t('repair.answer'));input.oninput=()=>this.answerDraft=input.value;const send=label('button','repair.sendAnswer');send.id='repairSendAnswer';send.disabled=this.busy;send.onclick=()=>{if(input.value.trim())this.answer({kind:'add_detail',detail:input.value});};this.host.append(input,send);}
    const kind=candidateAnswerKind(modes);
    for(const c of q.candidates||[]){
     const card=node('div',c.name||c.public_id,'repair-candidate');card.append(node('small',[c.ifc_class,c.storey,c.position].filter(Boolean).join(' · ')));
     const preview=label('button','repair.previewCandidate');preview.disabled=this.busy;preview.onclick=()=>this.previewCandidate(c);card.append(preview);
     if(kind){const pick=label('button',kind==='authorize_prototype'?'repair.authorize':'repair.pick');pick.disabled=this.busy||this.previewedToken!==c.token;pick.onclick=()=>this.answer(kind==='authorize_prototype'?{kind,candidate_token:c.token,authorized:true}:{kind,candidate_token:c.token});card.append(pick);}
     this.host.append(card);
    }
    if(this.previewMessage)this.host.append(node('p',this.previewMessage));
    if(q.property_preview){const d=node('details');d.dataset.key='property-preview';d.open=open.get('property-preview')??true;d.append(label('summary','repair.propertyPreview'));const table=node('table');for(const [key,value] of Object.entries(q.property_preview)){if(key==='preview_hash')continue;const tr=node('tr');tr.append(node('th',key),node('td',typeof value==='object'?JSON.stringify(value,null,2):String(value)));table.append(tr);}d.append(table);this.host.append(d);}
    for(const [kind,key] of [['confirm_property','repair.confirmProperty'],['reject_property','repair.rejectProperty'],['cancel','repair.cancel']])if(modes.includes(kind)){const b=label('button',key);b.disabled=this.busy;b.onclick=()=>this.answer(kind==='cancel'?{kind}:{kind,preview_hash:q.property_preview?.preview_hash});this.host.append(b);}
   }
   if(this.files.length){
    const all=node('details');all.dataset.key='artifacts';all.open=open.get('artifacts')??false;all.append(label('summary','repair.artifacts'));
    for(const f of this.files){if(!f.download_url.startsWith('/api/repair-tasks/'))continue;const row=node('div',undefined,'artifact-row');
     if(/\.(json|txt|md)$/.test(f.name)){const b=node('button',f.relative_path||f.name);b.onclick=()=>this.openArtifact(f);row.append(b);}
     else {const a=node('a',f.name+' · '+f.role);a.href=f.download_url;a.setAttribute('download','');row.append(a);}
     if(f.role==='diagnostic_candidate'){const b=label('button','repair.showDiagnostic');b.onclick=()=>this.onResult(f,this.task,this.prepared).catch(e=>{this.displayError=e.message;this.render();});row.append(b);}all.append(row);
    }this.host.append(all);
   }
   if(this.fileView){const d=node('details');d.open=true;d.append(node('summary',this.fileView.name),node('pre',this.fileView.loading?t('repair.loadingFile'):this.fileView.text));this.host.append(d);}
   if(this.displayError)this.host.append(label('p','repair.displayFailed',{code:this.displayError}));
   if(this.error||this.displayError){const retry=label('button','repair.reload');retry.onclick=()=>this.poll();this.host.append(retry);}
  }
  if(scroll!==undefined)this.host.parentElement.scrollTop=scroll;
  if(focusKey){const el=this.host.querySelector('[data-focus-key="'+focusKey+'"]');if(el){el.focus({preventScroll:true});if(selection)el.setSelectionRange(...selection);}}
  this.onStateChange();
 }
 reset({forget=true}={}){
  if(this.restoring)return;clearTimeout(this.timer);this.epoch++;this.prepared=null;this.task=null;this.error=null;this.cache=null;this.busy=false;this.fileView=null;this.displayError=null;this.events=[];this.activity=[];this.files=[];this.cursor=-1;this.activityCursor=-1;this.resultLoaded=null;
  if(forget){try{sessionStorage.removeItem('text2ifc.lastTask');const url=new URL(location.href);url.searchParams.delete('task');history.replaceState(null,'',url);}catch{}}
  this.render();
 }
}
