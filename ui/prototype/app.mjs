import {createState,setMode,inspect,clearReference,clearAuxReference,armAuxReference,hiddenIds,hideElement,undoHide,showAll,selectionRole,submitDraft,setViewVersion,createDemo,startDemo,advanceDemo,setAnswer,previewAnswer,sendAnswer,steps,cases,placementText,demoArtifact} from './core.mjs';
import {createViewer,elements} from './scene.mjs';

const $=id=>document.getElementById(id);
const workspace=createState();
let demo=null,viewer=null,timer=null,toastTimer=null,savedCamera=null,activeDetail=0,pinnedDetail=false;
let detailMode='process',drawKey='',paintQueue=Promise.resolve(),contextTarget=null;
function current(){return demo||workspace;}
function notice(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,5000);}
function safely(fn){try{fn();}catch(e){notice(e.message);}}
function addMessage(who,text,kind='reply') {
  const box=document.createElement('div');box.className='message';
  const label=document.createElement('div');label.className='who';label.textContent=who;
  const content=document.createElement('div');content.className=kind;content.textContent=text;
  box.append(label,content);$('messages').append(box);
}
function renderMessages(){
  $('messages').replaceChildren();
  if(demo){
    addMessage('案例请求 · '+elements[cases[demo.scenario].target].name,cases[demo.scenario].request,'bubble');
    for(const answer of demo.answers)addMessage('你的示例答复',answer,'bubble');
    const message=demo.status==='ready'?'这是独立案例。播放后查看过程，不会执行工作台里的自定义需求。':demo.status==='awaiting_user'?'位置不足以确定，请在下方回答。当前仍是同一个示例。':demo.status==='complete'?'示例完成。通过定位变化与前后切换检查新增几何。':`正在展示：${steps[demo.step]}。`;
    addMessage('演示过程',message);
  } else for(const r of workspace.requests){
    addMessage(`需求 ${r.id} · ${r.reference?elements[r.reference.id]?.name:'未指定参照'} · 输入模型`,r.text,'bubble');
    if(r.auxReference)addMessage('参考构件',elements[r.auxReference.id]?.name||r.auxReference.id);
    addMessage('待执行 · 接口未接入','需求已保存在本页，尚未执行。模型没有改变，也没有生成修复结果。');
  }
  $('emptyState').hidden=!!demo||workspace.requests.length>0;
  $('emptyTitle').textContent=workspace.mode==='view'?'自由查看，\n不会改变请求。':'描述想做的修改。';
  $('emptyCopy').textContent=workspace.mode==='view'?'点击构件只显示名称和高亮。需要修改时，再切换到选中提交。':workspace.reference?`已附上参照：${elements[workspace.reference.id]?.name}。直接使用“这里”或“这面墙”描述即可。`:'可以先点选参照，也可以直接描述目标位置与修改要求。';
}
function describeStep(d,i){
  if(!d)return '提交需求尚未触发真实执行。接入 RepairAPI 后，这里才会按实际事件显示过程与产物。';
  if(i>d.completed)return '这个步骤尚未完成，还没有对应产物。';
  const isWindow=d.scenario==='window';
  return [
    '已准备两层住宅示意场景。没有读取真实 IFC。',
    `案例请求：${cases[d.scenario].request}`,
    isWindow?'参照：一层正面墙体。新增窗的位置：墙体中央。':`参照：入口右侧柱。用户已确认 ${placementText(d.offset)}。`,
    isWindow?'修改摘要：新增 1 扇窗与对应洞口；宽 1.80 米、高 1.50 米，窗台高 0.90 米。':`修改摘要：新增 1 根 0.26 × 0.26 × 2.95 米的柱，${placementText(d.offset)}。`,
    '示例中的新增几何已准备。这里只演示显示变化，没有写出候选 IFC。',
    '案例已展示完毕。可以定位新增构件、切换前后；没有执行 IFC 标准或几何校验。'
  ][i];
}
function renderDetail(){
  $('toggleDetails').textContent=$('processDetail').hidden?'查看详情':'收起详情';
  $('toggleDetails').setAttribute('aria-expanded',String(!$('processDetail').hidden));
  if(detailMode==='source'){
    $('detailTitle').textContent='IFC 源码 · 尚未接入';
    $('detailText').textContent='当前是示意几何，没有真实 IFC 源文件。正式接线后，此处按模型版本定位到构件原文。';
    $('rawDetails').hidden=true;return;
  }
  $('detailTitle').textContent=demo?steps[activeDetail]:'尚无执行过程';
  $('detailText').textContent=describeStep(demo,activeDetail);
  const data=demo?demoArtifact(demo,activeDetail):null;
  $('rawDetails').hidden=!data;
  $('filename').textContent=data?`step-${activeDetail+1}.demo.json · 示意数据`:'';
  $('code').textContent=data?JSON.stringify(data,null,2):'';
  $('copyCode').disabled=!data;
}
function renderGeometry(){
  if(!viewer)return;
  const s=current();
  const state={scenario:demo?.scenario||'window',version:s.version,selected:s.inspected,highlight:demo?.highlight??true,offset:demo?.offset??1.5,previewActive:demo?.previewActive??false,previewOffset:demo?.previewOffset??null,hiddenIds:hiddenIds(s)};
  const key=JSON.stringify(state);if(key===drawKey)return;drawKey=key;
  paintQueue=paintQueue.then(()=>viewer.update(state)).catch(e=>{drawKey='';notice('视图更新失败：'+e.message);});
}
function render(){
  const s=current(),e=elements[s.inspected],waiting=demo?.status==='awaiting_user';
  $('modebar').hidden=!!demo;$('demoBar').hidden=!demo;
  $('demoTitle').textContent=demo?`设计演示 / ${cases[demo.scenario].title}`:'';
  $('modeView').setAttribute('aria-pressed',String(workspace.mode==='view'));
  $('modeSelect').setAttribute('aria-pressed',String(workspace.mode==='select'));
  $('modebar').classList.toggle('select',workspace.mode==='select');
  $('modeHint').textContent=workspace.mode==='view'?'浏览不改参照；右键构件可临时隐藏。':workspace.pickRole==='auxiliary'?'下一次点击添加参考构件，定位参照保持不变。':'点击绑定定位参照；自然语言决定修改动作。';
  $('before').setAttribute('aria-pressed',String(s.version==='before'));
  $('after').setAttribute('aria-pressed',String(s.version==='after'));
  $('after').disabled=!demo?.resultAvailable;
  $('after').title=demo?.resultAvailable?'查看此案例结果':'尚无修复后结果';
  $('modelCaption').textContent=`当前查看：${s.version==='before'?'修复前 / 输入模型':'修复后 / 案例结果'}　·　${demo?'独立演示':'工作台'}`;
  $('selectionCard').hidden=!e;$('canvasHint').hidden=!!e;
  const role=demo?'inspection':selectionRole(workspace);
  const attached=role==='reference',auxAttached=role==='auxiliary';
  $('selectionKind').textContent=attached
    ? (workspace.mode==='view'?'正在查看 · 已保留为请求参照':'已选为请求参照')
    : auxAttached?'参考构件 · 用途由文字说明':(!demo&&workspace.mode==='select'?'仅查看 · 下次点击按当前拾取模式绑定':'正在查看 · 不改变请求参照');
  $('selectionLegend').textContent=attached?'定位参照':auxAttached?'辅助参照':'浏览高亮';
  if(e){$('selectedName').textContent=e.name;$('selectedMeta').textContent=e.type.replace(' · 示意类别','')+' · '+e.floor;}
  $('properties').hidden=!e||!s.propertiesOpen;
  if(e&&s.propertiesOpen){$('propertyRows').replaceChildren();for(const [k,v] of [['名称',e.name],['类别',e.type],['楼层',e.floor],['尺寸',e.size]]){const row=document.createElement('div');row.className='property-row';const a=document.createElement('span'),b=document.createElement('b');a.textContent=k;b.textContent=v;row.append(a,b);$('propertyRows').append(row);}}
  $('highlight').hidden=!demo?.resultAvailable;$('highlight').setAttribute('aria-pressed',String(demo?.highlight??true));$('changeLegend').hidden=!demo?.resultAvailable;
  $('placementLabel').hidden=!demo?.previewActive;
  $('placementLabel').textContent=demo?.previewActive?`位置预览 · ${placementText(demo.previewOffset)} · 尚未应用`:'';
  $('asideTitle').textContent=demo?'案例对话':workspace.mode==='view'?'模型查看':'修改需求';
  $('asideCaption').textContent=demo?'预设案例与工作台草稿独立':workspace.mode==='view'?'浏览不会改变已保留的请求参照':'直接描述，不必先选操作';
  $('reference').hidden=!!demo||!workspace.reference;
  const labelRef=r=>(elements[r.id]?.name||r.id)+((workspace.hiddenByVersion?.[r.version]||[]).includes(r.id)?'（已隐藏）':'');
  if(workspace.reference){$('referenceName').textContent=labelRef(workspace.reference);$('referencePrefix').textContent=workspace.mode==='view'?'已保留定位：':'定位参照：';}
  $('auxReference').hidden=!!demo||!workspace.auxReference;
  if(workspace.auxReference)$('auxReferenceName').textContent=labelRef(workspace.auxReference);
  $('auxActions').hidden=!!demo||workspace.mode!=='select';
  $('addAuxReference').textContent=workspace.pickRole==='auxiliary'?'取消参考拾取':workspace.auxReference?'更换参考构件':'添加参考构件';
  $('addAuxReference').setAttribute('aria-pressed',String(workspace.pickRole==='auxiliary'));
  $('auxHint').textContent=workspace.pickRole==='auxiliary'?'请点击模型中的参考对象；不会替换定位参照。':'尺寸、样式等用途请在文字中说明。';
  const hidden=hiddenIds(s);$('hiddenCount').textContent=`隐藏 ${hidden.length} 项`;
  $('undoHide').disabled=!hidden.length;$('showAll').disabled=!hidden.length;
  $('baseLabel').textContent=demo?'演示基准：案例修复前模型':'下一条需求基于：输入模型（不随浏览切换）';
  $('inputShell').hidden=!!demo&&!waiting;
  $('request').readOnly=!demo&&workspace.mode==='view';
  $('request').disabled=false;
  const value=waiting?demo.answerDraft:workspace.draft;
  if($('request').value!==value)$('request').value=value;
  $('request').placeholder=waiting?'例如：沿正立面向左 1.8 米':workspace.mode==='view'?'切换到选中提交，描述你想做的修改。':'例如：在这面墙上加窗；也可不点选，直接描述。';
  $('request').setAttribute('aria-label',waiting?'回答位置问题':'自然语言需求');
  $('submit').textContent=waiting?'发送回答并继续':workspace.mode==='view'?'切换到选中提交':'提交需求';
  $('submit').disabled=waiting?!demo.answerDraft.trim():workspace.mode==='select'&&!workspace.draft.trim();
  $('inputHint').textContent=waiting?'可先预览位置':workspace.mode==='view'?'草稿保留 · 不会发送':workspace.reference?'参照已附加':'未指定参照也可提交';
  $('composerNote').textContent=demo?'设计演示：补柱位置使用本地规则，无模型调用。':'执行接口尚未接入；提交仅保存在本页，不产生修复结果。';
  $('demoActions').hidden=!demo;
  $('playDemo').hidden=waiting;
  $('playDemo').textContent=demo?.status==='running'?'正在播放…':demo?.status==='complete'?'重播此案例':'播放这个案例';
  $('playDemo').disabled=demo?.status==='running';
  $('previewPlacement').hidden=!waiting;$('previewPlacement').disabled=waiting&&!demo.answerDraft.trim();
  $('demoRequestSummary').hidden=!demo||waiting;
  $('demoRequestSummary').textContent=demo?.status==='complete'?'查看结果后，返回工作台继续编写自己的需求。':demo?.status==='running'?'正在展示既定过程。不会读取或修改你的工作台草稿。':'播放此案例的已知请求，观察前后变化。';
  $('question').hidden=!waiting;$('result').hidden=demo?.status!=='complete';
  if(demo){const win=demo.scenario==='window';$('resultTitle').textContent=win?'新增 1 扇窗户':'新增 1 根柱子';$('resultPosition').textContent=win?'一层正面墙体中央':placementText(demo.offset);$('resultSize').textContent=win?'1.80 × 1.50 m':'0.26 × 0.26 × 2.95 m';}
  $('compareResult').textContent=s.version==='after'?'查看修复前':'查看修复后';
  $('stages').replaceChildren();steps.forEach((title,i)=>{const b=document.createElement('button');b.className='step'+(demo&&i<=demo.completed?' done':'')+(demo&&i===demo.step&&demo.status!=='complete'?' current':'')+(waiting&&i===2?' wait':'');b.title=title;b.setAttribute('aria-label','查看'+title);const n=document.createElement('span');n.className='num';n.textContent=demo&&i<=demo.completed?'✓':String(i+1);const label=document.createElement('span');label.className='label';label.textContent=title;b.append(n,label);b.onclick=()=>{activeDetail=i;pinnedDetail=true;detailMode='process';$('processDetail').hidden=false;$('rawDetails').open=false;renderDetail();};$('stages').append(b);});
  $('progressLabel').textContent=!demo?'暂无执行记录':waiting?'等待位置回答':demo.status==='ready'?'尚未播放':demo.status==='complete'?'示例结束':`示例进行中 · ${steps[demo.step]}`;
  $('statusText').textContent=s.notice||(demo?'演示独立运行 · 返回后恢复工作台':workspace.mode==='view'?'查看模式 · 点击不改变请求参照':'选中提交 · 点选绑定参照，文字描述动作');
  renderMessages();renderDetail();renderGeometry();
}
function closeContext(){contextTarget=null;$('objectMenu').hidden=true;}
function contextClicked(id,x,y){
  closeContext();if(current().mode!=='view'||!id)return;
  contextTarget={id,state:current(),version:current().version};
  $('contextName').textContent=elements[id]?.name||id;
  $('objectMenu').style.left=Math.max(8,Math.min(x,innerWidth-240))+'px';
  $('objectMenu').style.top=Math.max(8,Math.min(y,innerHeight-145))+'px';
  $('objectMenu').hidden=false;$('hideContext').focus();
}
function clicked(id){closeContext();try{if(demo){demo.inspected=id;demo.propertiesOpen=false;}else inspect(workspace,id);}catch(e){notice(e.message);}render();}
function switchMode(mode){closeContext();setMode(workspace,mode);render();if(mode==='select')$('request').focus();}
function openDemo(key){
  closeContext();clearTimeout(timer);if(!demo)savedCamera=viewer?.getCamera();
  demo=createDemo(key);activeDetail=0;pinnedDetail=false;detailMode='process';$('processDetail').hidden=true;$('rawDetails').open=false;$('examples').close();render();viewer?.home();
}
async function exitDemo(){closeContext();clearTimeout(timer);demo=null;pinnedDetail=false;detailMode='process';$('processDetail').hidden=true;render();await paintQueue;if(savedCamera)viewer?.setCamera(savedCamera);$('openExamples').focus();}
function tick(){timer=setTimeout(()=>{if(!demo||demo.status!=='running')return;advanceDemo(demo);if(!pinnedDetail)activeDetail=Math.max(0,demo.completed);render();if(demo.status==='running')tick();else $('chat').scrollTop=$('chat').scrollHeight;},650);}
$('modeView').onclick=()=>switchMode('view');$('modeSelect').onclick=()=>switchMode('select');
$('request').addEventListener('input',()=>{if(demo?.status==='awaiting_user')setAnswer(demo,$('request').value);else if(!demo&&workspace.mode==='select')workspace.draft=$('request').value;render();});
$('submit').onclick=()=>safely(()=>{if(demo){sendAnswer(demo);render();tick();}else if(workspace.mode==='view')switchMode('select');else{submitDraft(workspace);render();$('chat').scrollTop=$('chat').scrollHeight;}});
$('addAuxReference').onclick=()=>safely(()=>{armAuxReference(workspace);render();});
$('removeAuxReference').onclick=()=>{clearAuxReference(workspace);render();};
$('hideContext').onclick=()=>safely(()=>{const target=contextTarget;if(!target||target.state!==current()||target.version!==current().version)return;hideElement(current(),target.id);closeContext();render();$('showAll').focus();});
$('showAll').onclick=()=>{closeContext();showAll(current());render();};
$('undoHide').onclick=()=>{closeContext();undoHide(current());render();};
document.addEventListener('pointerdown',e=>{if(!$('objectMenu').hidden&&!$('objectMenu').contains(e.target))closeContext();});
$('removeReference').onclick=()=>{clearReference(workspace);render();};$('clearInspection').onclick=()=>{current().inspected=null;current().propertiesOpen=false;render();};
$('propertiesBtn').onclick=()=>{current().propertiesOpen=!current().propertiesOpen;render();};$('closeProperties').onclick=()=>{current().propertiesOpen=false;render();};
$('sourceBtn').onclick=()=>{detailMode='source';pinnedDetail=true;$('processDetail').hidden=false;renderDetail();};
$('toggleDetails').onclick=()=>{$('processDetail').hidden=!$('processDetail').hidden;renderDetail();};
$('detailHeight').oninput=()=>{$('processDetail').style.height=$('detailHeight').value+'px';};
$('before').onclick=()=>safely(()=>{closeContext();setViewVersion(current(),'before',!!demo?.resultAvailable);render();});
$('after').onclick=()=>safely(()=>{closeContext();setViewVersion(current(),'after',!!demo?.resultAvailable);render();});
$('compareResult').onclick=()=>{setViewVersion(demo,demo.version==='after'?'before':'after',demo.resultAvailable);render();};
$('highlight').onclick=()=>{if(demo){demo.highlight=!demo.highlight;render();}};
$('fit').onclick=()=>viewer?.home();
$('locateChange').onclick=async()=>{if(!demo?.resultAvailable)return;setViewVersion(demo,'after',true);demo.inspected=cases[demo.scenario].newId;demo.highlight=true;render();await paintQueue;viewer?.focusElement(demo.inspected,demo.offset);};
$('openExamples').onclick=()=>$('examples').showModal();$('closeExamples').onclick=()=>$('examples').close();
$('exitDemo').onclick=exitDemo;document.querySelectorAll('[data-case]').forEach(b=>b.onclick=()=>openDemo(b.dataset.case));
$('playDemo').onclick=()=>safely(()=>{startDemo(demo);pinnedDetail=false;activeDetail=0;render();tick();});
$('previewPlacement').onclick=()=>safely(()=>{previewAnswer(demo);render();});
for(const b of document.querySelectorAll('[data-answer]'))b.onclick=()=>{setAnswer(demo,b.dataset.answer);render();$('request').focus();};
$('copyCode').onclick=async()=>{try{await navigator.clipboard.writeText($('code').textContent);notice('已复制示意数据');}catch{const r=document.createRange();r.selectNodeContents($('code'));getSelection().removeAllRanges();getSelection().addRange(r);notice('已选中内容，可按 Ctrl / ⌘ + C');}};
$('help').onclick=()=>$('about').showModal();$('closeAbout').onclick=()=>$('about').close();
document.addEventListener('keydown',e=>{if($('about').open||$('examples').open)return;if(e.key==='Escape'){if(!$('objectMenu').hidden){closeContext();$('fit').focus();return;}current().inspected=null;current().propertiesOpen=false;render();}if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();$('submit').click();}});
render();try{viewer=await createViewer($('plot'),clicked,contextClicked);renderGeometry();await paintQueue;globalThis.__UI_READY__=true;}catch(e){$('loadError').hidden=false;$('loadError').textContent=e.message;globalThis.__UI_ERROR__=e.message;}
// Read-only snapshots for interaction QA, not an execution or state-mutation API.
globalThis.__preview={state:()=>structuredClone(workspace),demo:()=>demo?structuredClone(demo):null,camera:()=>viewer?.getCamera(),renderer:()=>globalThis.__UI_RENDERER__};
