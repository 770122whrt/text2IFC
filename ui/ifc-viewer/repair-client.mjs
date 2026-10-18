/** Framework-neutral HTTP client. No model keys, CLI, shell or automatic mutation retries. */
export class RepairClient {
 constructor({base='/api',fetchImpl=globalThis.fetch?.bind(globalThis)}={}){this.base=base.replace(/\/$/,'');this.fetch=fetchImpl;}
 async call(path,{method='GET',body,signal}={}){
  const form=typeof FormData!=='undefined'&&body instanceof FormData;
  const response=await this.fetch(this.base+path,{method,body:body===undefined?undefined:form?body:JSON.stringify(body),headers:body!==undefined&&!form?{'Content-Type':'application/json'}:{},signal:signal||AbortSignal.timeout(90000),cache:'no-store'});
  let data;try{data=await response.json();}catch{data={};}
  if(!response.ok){const error=Error(data.error?.code||'REPAIR_HTTP_'+response.status);error.code=data.error?.code||'REPAIR_HTTP_'+response.status;error.status=response.status;throw error;}
  return data;
 }
 capabilities(){return this.call('/capabilities');}
 summary(id){return this.call('/repair-tasks/'+encodeURIComponent(id)+'/summary');}
 examples(){return this.call('/examples');}
 example(id){return this.call('/examples/'+encodeURIComponent(id));}
 upload(bytes,name){const form=new FormData();form.append('file',new Blob([bytes],{type:'application/x-step'}),name);return this.call('/ifc-inputs',{method:'POST',body:form});}
 prepare(payload){return this.call('/repair-requests/prepare',{method:'POST',body:payload});}
 start(preparedId,clientId){return this.call('/repair-tasks',{method:'POST',body:{prepared_request_id:preparedId,client_request_id:clientId}});}
 task(id){return this.call('/repair-tasks/'+encodeURIComponent(id));}
 events(id,after=-1,activityAfter=-1){return this.call('/repair-tasks/'+encodeURIComponent(id)+'/events?after='+after+'&activity_after='+activityAfter);}
 prepared(id){return this.call('/repair-requests/'+encodeURIComponent(id));}
 input(id){return this.call('/ifc-inputs/'+encodeURIComponent(id));}
 async resource(url,{text=false}={}){
  if(!url.startsWith('/api/')||url.includes('..'))throw Error('INVALID_ARTIFACT_URL');
  const response=await this.fetch(this.base+url.slice(4),{cache:'no-store',signal:AbortSignal.timeout(120000)});
  if(!response.ok){const e=Error('ARTIFACT_HTTP_'+response.status);e.status=response.status;throw e;}
  return text?response.text():response.arrayBuffer();
 }
 artifacts(id){return this.call('/repair-tasks/'+encodeURIComponent(id)+'/artifacts');}
 answer(id,payload){return this.call('/repair-tasks/'+encodeURIComponent(id)+'/answers',{method:'POST',body:payload});}
}
export function requestSignature(s){return JSON.stringify([s.version,s.text,s.primary||null,s.targets??null,s.auxiliary||null]);}
export function preparePayload(s,inputId,language){
 const ref=x=>{if(!x)return null;if(x.version!==s.version)throw Error('SELECTION_VERSION_MISMATCH');return {step_id:Number(x.id),global_id:x.guid||null,view_version:x.version};};
 return {input_id:inputId,user_text:s.text,language,view_version:s.version,primary:ref(s.primary),auxiliary:ref(s.auxiliary),...(s.targets?{targets:s.targets.map(ref)}:{})};
}
