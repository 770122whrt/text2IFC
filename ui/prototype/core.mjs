/** UI-only state. Workspace requests never run the illustrative examples. */
export const steps = ['读取模型','理解请求','定位与确认','形成修改','应用修改','检查与结果'];
export const cases = Object.freeze({
  window: {title:'墙体新增窗户',target:'wall',request:'在这面墙中央增加一扇宽 1.8 米、高 1.5 米的窗，窗台高 0.9 米。',newId:'new-window'},
  column: {title:'参照柱补建与澄清',target:'column',request:'在这根柱子旁边新增一根相同尺寸的柱。',newId:'new-column'}
});
export function createState() {
  return {mode:'view',inspected:null,reference:null,auxReference:null,pickRole:'primary',hiddenByVersion:{before:[],after:[]},draft:'',version:'before',baseVersion:'before',propertiesOpen:false,requests:[],counter:0,notice:''};
}
export function setMode(s,mode) {
  if (!['view','select'].includes(mode)) throw Error('未知交互模式');
  s.mode=mode;
  if(mode==='view') s.pickRole='primary'; // Cancel picking, preserve saved references.
}
export function inspect(s,id) {
  s.inspected=id; s.propertiesOpen=false; s.notice='';
  if (s.mode==='select' && id) {
    if (s.version!==s.baseVersion) { s.notice='正在查看其他版本，参照未替换。'; return; }
    const slot=s.pickRole==='auxiliary'?'auxReference':'reference';
    const other=slot==='auxReference'?s.reference:s.auxReference;
    if(other?.id===id&&other.version===s.baseVersion) throw Error('该构件已用于另一个参照，请选择不同构件。');
    s[slot]={id,version:s.baseVersion};
    s.pickRole='primary';
  }
}
export function clearReference(s) { s.reference=null; }
export function clearAuxReference(s) { s.auxReference=null;s.pickRole='primary'; }
export function armAuxReference(s) {
  if(s.mode!=='select') throw Error('请先切换到选中提交模式');
  s.pickRole=s.pickRole==='auxiliary'?'primary':'auxiliary';
}
export function hiddenIds(s) {return [...(s.hiddenByVersion?.[s.version]||[])];}
export function hideElement(s,id) {
  if(s.mode!=='view') throw Error('隐藏仅在查看模式使用');
  if(!id) throw Error('请右键点击具体构件');
  s.hiddenByVersion??={before:[],after:[]};
  const items=s.hiddenByVersion[s.version]??=[];
  if(!items.includes(id)) items.push(id);
  if(s.inspected===id){s.inspected=null;s.propertiesOpen=false;}
  s.notice='仅隐藏当前视图；不会删除 IFC 或清除请求参照。';
}
export function undoHide(s) {s.hiddenByVersion?.[s.version]?.pop();s.notice='已撤销上次隐藏。';}
export function showAll(s) {s.hiddenByVersion??={};s.hiddenByVersion[s.version]=[];s.notice='当前版本已显示全部构件。';}

/** Derive card/legend meaning from the actual version-bound reference. */
export function selectionRole(s) {
  if (!s.inspected) return 'none';
  if(s.reference?.id===s.inspected&&s.reference.version===s.version)return 'reference';
  if(s.auxReference?.id===s.inspected&&s.auxReference.version===s.version)return 'auxiliary';
  return 'inspection';
}
export function submitDraft(s) {
  if(s.mode!=='select') throw Error('请切换到选中提交模式');
  if(!s.draft.trim()) throw Error('请先描述修改需求');
  const request={id:++s.counter,text:s.draft,reference:s.reference?{...s.reference}:null,auxReference:s.auxReference?{...s.auxReference}:null,baseVersion:s.baseVersion,status:'pending_backend'};
  s.requests.push(request); s.draft=''; return request;
}
export function setViewVersion(s,version,resultAvailable) {
  if(!['before','after'].includes(version)) throw Error('未知模型版本');
  if(version==='after'&&!resultAvailable) throw Error('尚无修复后结果');
  s.version=version;
  if(version==='before'&&s.inspected?.startsWith('new-')) {
    s.inspected=null; s.propertiesOpen=false; s.notice='该新增对象在修复前不存在。';
  }
}
export function createDemo(key) {
  if(!cases[key]) throw Error('未知演示案例');
  return {scenario:key,mode:'view',inspected:null,reference:null,hiddenByVersion:{before:[],after:[]},propertiesOpen:false,version:'before',status:'ready',step:-1,completed:-1,sequence:0,offset:1.5,previewOffset:null,previewActive:false,answerDraft:'',answers:[],resultAvailable:false,highlight:true,notice:''};
}
export function startDemo(d) {
  if(['running','awaiting_user'].includes(d.status)) throw Error('演示尚未结束');
  const next=createDemo(d.scenario); next.sequence=d.sequence+1;
  Object.assign(d,next,{status:'running',step:0,inspected:cases[d.scenario].target});
}
export function advanceDemo(d) {
  if(d.status!=='running') return;
  d.completed=d.step; d.step++;
  if(d.scenario==='column'&&d.step===2&&!d.answers.length) { d.status='awaiting_user'; return; }
  if(d.step===6) Object.assign(d,{step:5,completed:5,status:'complete',version:'after',resultAvailable:true,previewActive:false});
}
/** Deliberately bounded fixture parser; not an LLM or general IFC placement solver. */
export function parsePlacement(text) {
  const match=String(text).trim().match(/^(?:沿正立面\s*[，,]?\s*)?向(左|右)\s*(?:[，,]?\s*中心间距\s*(?:为|是)?\s*)?(\d+(?:\.\d+)?)\s*(毫米|mm|米|m)\s*[。.]?$/i);
  if(!match) throw Error('示例可识别“向左 1.8 米”或“向右 1800 mm”。其他表达需真实接口，当前不会猜测。');
  const distance=Number(match[2])/(match[3]==='毫米'||match[3].toLowerCase()==='mm'?1000:1);
  if(distance<.3||distance>2.5) throw Error('此示例只预演中心间距 0.3–2.5 米，请调整输入。');
  return match[1]==='左'?distance:-distance;
}
export function setAnswer(d,text) {d.answerDraft=text;d.previewActive=false;d.previewOffset=null;}
export function previewAnswer(d) {
  if(d.status!=='awaiting_user') throw Error('当前没有待回答的问题');
  d.previewOffset=parsePlacement(d.answerDraft);d.previewActive=true;
}
export function sendAnswer(d) {
  if(d.status!=='awaiting_user') throw Error('当前没有待回答的问题');
  d.offset=parsePlacement(d.answerDraft);d.answers.push(d.answerDraft);d.answerDraft='';
  d.previewActive=false;d.previewOffset=null;d.status='running';
}
export function placementText(offset) {return `沿正立面向${offset>=0?'左':'右'} ${Math.abs(offset).toFixed(2).replace(/0$/,'')} 米（中心间距）`;}
export function demoArtifact(d,index) {
  if(index<0||index>d.completed) return null;
  const bodies=[
    {source:'程序化示意建筑',real_ifc_loaded:false},
    {request:cases[d.scenario].request,reference:cases[d.scenario].target},
    {placement:d.scenario==='window'?'墙体中央':placementText(d.offset),user_answers:d.answers},
    {operation:d.scenario==='window'?'新增窗与洞口':'新增矩形柱',placement:d.scenario==='window'?'墙体中央':placementText(d.offset)},
    {geometry_preview:true,actual_ifc_written:false},
    {preview_complete:true,validator_executed:false,provider_calls:0}
  ];
  return {illustrative:true,demo_sequence:d.sequence,stage:steps[index],...bodies[index]};
}
