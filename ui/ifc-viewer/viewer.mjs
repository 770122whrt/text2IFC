import {createState,setMode,inspect,clearReference,clearAuxReference,armAuxReference,hiddenIds,hideElement,undoHide,showAll,submitDraft} from '../prototype/core.mjs';
import {coverage,validReference,sourceLabel,compatibleFrame} from './model-contract.mjs';
import * as Three from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {exactBounds,sourceMatches,displayMaterial,attachEdges,fitVisible,checkIfcBytes,loadMessage} from './display-geometry.mjs';
import {buildNativeMeshes} from './native-mesh-adapter.mjs';
import {t,getLanguage,setLanguage,applyTranslations,bindText,onLanguageChange,uiError,errorText} from './i18n.mjs';
import {SelectionHighlighter} from './selection-highlight.mjs';
import {targetRefs,setMulti,pickTarget,removeTarget,clearTargets,TargetHighlighters} from './multi-selection.mjs';
const targetHighlighters=new TargetHighlighters();
import {summarizeDiagnostics,classifyDisplayRecords} from './diagnostics-display.mjs';
import {RepairPanel} from './repair-panel.mjs';
import {pairOffset,findByGuid,validateResultRole,newVisibleObjects} from './model-pair.mjs';
import {LocalExamples} from './local-examples.mjs';
let repairPanel=null,modelPair=null,pairLoading=false,currentExample=null;
import {readModelIndex,readInspection} from './inspection-data.mjs';
import {ModelTree,renderInspection} from './inspection-panel.mjs';
const T={...Three,OrbitControls}, W=globalThis.WebIFC, $=id=>document.getElementById(id);
const reviewParams=new URLSearchParams(location.search);
applyTranslations();
if(reviewParams.get('capture')==='1'){
  const style=document.createElement('style');style.textContent='body>*{visibility:hidden} #canvas,#canvas *{visibility:visible} #canvas{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;z-index:99999;background:linear-gradient(#a4b1ba,#dfe6e9)}';document.head.append(style);
}
let state=createState(),api=null,model=-1,sourceBytes=null,sourceName='',generation=0,records=new Map(),groups=new Map(),pickMeshes=[],bounds=null,report=null,diagnostics=[],unlit=false,contextId=null,loading=false,toastTimer;
const scene=new T.Scene(),root=new T.Group();scene.add(root);
let renderer,cam,controls,highlighted=null,modelIndex=null,propertyRequest=0;
let propertyView=null,lastLoadError=null,initializationError=null,toastValue=null;
const selectionHighlighter=new SelectionHighlighter({through:true});
const modelTree=new ModelTree($('treeContent'),$('treeSearch'),$('treeCount'),{
 select:(id,event)=>selectObject(id,{additive:!!(event?.ctrlKey||event?.metaKey)}),
 visibility:id=>{if(state.mode!=='view'||loading)return;
  if(hiddenIds(state).includes(id))state.hiddenByVersion[state.version]=hiddenIds(state).filter(x=>x!==id);
  else hideElement(state,id);
  update();}
});
let edgesEnabled=true,nativeRequested=false;
scene.add(new T.AmbientLight(0xffffff,1.7));
const key=new T.DirectionalLight(0xffffff,1.0);key.position.set(25,55,30);scene.add(key);
const fill=new T.DirectionalLight(0xffffff,.16);fill.position.set(-40,25,-40);scene.add(fill);
function toast(value){const key={MULTI_TARGET_LIMIT:'multi.limit',MULTI_CLEAR_TO_SINGLE:'multi.single',DUPLICATE_SELECTION_ROLES:'multi.overlap',MULTI_SELECT_MODE_REQUIRED:'multi.mode'}[value?.message];if(key)value=uiError(key);toastValue=value;$('toast').textContent=errorText(value);$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,5000);}
function safe(fn){return (...args)=>Promise.resolve().then(()=>fn(...args)).catch(e=>toast(e));}
function setStatus(text){$('status').removeAttribute('data-i18n');$('status').textContent=text;}
function download(data,name,type){const u=URL.createObjectURL(new Blob([data],{type})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),30000);}
function resetScene(){restoreHighlight();root.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});root.clear();pickMeshes=[];records.clear();groups.clear();root.position.set(0,0,0);}
function render(){if(renderer)renderer.render(scene,cam);}
function resize(){const w=$('canvas').clientWidth,h=$('canvas').clientHeight;if(!renderer||!w||!h)return;renderer.setSize(w,h);const half=(cam.top-cam.bottom)/2;cam.left=-half*w/h;cam.right=half*w/h;cam.updateProjectionMatrix();render();}
// These camera presets only orient the supplied sample. They never transform IFC geometry.
function preset(which='front'){
  if(!bounds||!renderer)return;
  const size=new T.Vector3().subVectors(new T.Vector3(...bounds.max),new T.Vector3(...bounds.min));
  const d=(which==='front'?new T.Vector3(1,.094,0):which==='back'?new T.Vector3(-1,0,0):which==='top'?new T.Vector3(0,1,.00001):new T.Vector3(.374,.214,1)).normalize();
  const radius=size.length()/2,dist=radius*3;cam.up.set(0,1,0);if(which==='top')cam.up.set(-1,0,0);
  cam.position.copy(d.multiplyScalar(dist));controls.target.set(0,0,0);cam.lookAt(controls.target);cam.zoom=1;cam.near=Math.max(.05,dist-radius*1.2);cam.far=dist+radius*1.2;
  cam.updateMatrixWorld(true);const inv=cam.matrixWorldInverse;let minx=Infinity,maxx=-Infinity,miny=Infinity,maxy=-Infinity;
  for(let i=0;i<8;i++){const p=new T.Vector3((i&1?1:-1)*size.x/2,(i&2?1:-1)*size.y/2,(i&4?1:-1)*size.z/2).applyMatrix4(inv);minx=Math.min(minx,p.x);maxx=Math.max(maxx,p.x);miny=Math.min(miny,p.y);maxy=Math.max(maxy,p.y);}
  const aspect=$('canvas').clientWidth/$('canvas').clientHeight,hh=Math.max((maxy-miny)*.56,(maxx-minx)/aspect*.56);cam.top=hh;cam.bottom=-hh;cam.left=-hh*aspect;cam.right=hh*aspect;cam.updateProjectionMatrix();controls.update();render();
}
function pick(clientX,clientY){
  if(!cam)return null;
  const r=renderer.domElement.getBoundingClientRect(),x=(clientX-r.left)/r.width*2-1,y=-(clientY-r.top)/r.height*2+1;
  const a=new T.Vector3(x,y,-1).unproject(cam),b=new T.Vector3(x,y,1).unproject(cam);
  const raycast={ray:new T.Ray(a,b.sub(a).normalize()),near:0,far:Infinity,camera:cam},hits=[];
  root.updateMatrixWorld(true);for(const mesh of pickMeshes)if(mesh.parent.visible)mesh.raycast(raycast,hits);
  hits.sort((a,b)=>a.distance-b.distance);return hits.length?hits[0].object.userData.expressID:null;
}
function restoreHighlight(){selectionHighlighter.clear();targetHighlighters.clear();highlighted=null;}
function highlight(id){const ids=state.multiSelect?targetRefs(state).filter(r=>r.version===state.version).map(r=>r.id):[];if(id!==null)ids.push(id);targetHighlighters.sync(groups,ids,selectionHighlighter.through);highlighted=id;render();}
function selectObject(id,options={}){
 closeContext();if(loading||!records.has(id))return;
 try{pickTarget(state,id,{...options,locked:!!repairPanel?.locked});}catch(e){toast(e);}update();modelTree.reveal(id);
 if(!groups.has(id))toast(uiError('selection.noMesh'));
}
function label(ref){if(!ref)return '';const base=modelPair?.before&&ref.version===modelPair.before.version?modelPair.before.records:records;return sourceLabel(base.get(Number(ref.id)))+((state.hiddenByVersion[ref.version]||[]).includes(ref.id)?t('selection.hiddenSuffix'):'');}
function update(){
  $('viewMode').setAttribute('aria-pressed',String(state.mode==='view'));$('selectMode').setAttribute('aria-pressed',String(state.mode==='select'));
  $('modeHint').textContent=t(state.mode==='view'?'mode.viewHint':state.pickRole==='auxiliary'?'mode.auxHint':'mode.selectHint');
  $('request').readOnly=state.mode==='view'||!!repairPanel?.locked||pairLoading;$('request').value=state.draft;$('submit').textContent=t(state.mode==='view'?'action.enterSelect':'repair.prepare');$('request').placeholder=t(state.mode==='view'?'input.viewPlaceholder':'input.selectPlaceholder');$('submit').disabled=loading||pairLoading||!!repairPanel?.locked||model<0||(modelPair&&state.version!==state.baseVersion)||(state.mode==='select'&&!state.draft.trim());
  $('file').disabled=loading||pairLoading||!!repairPanel?.locked;$('sampleButton').disabled=$('file').disabled;$('throughNote').hidden=!selectionHighlighter.through;
  $('addAux').hidden=state.mode!=='select'||model<0;$('addAux').textContent=t(state.pickRole==='auxiliary'?'action.cancelReference':state.auxReference?'action.replaceReference':'action.addReference');
  for(const [id,ref,name] of [['primaryRef',state.reference,'primaryName'],['auxRef',state.auxReference,'auxName']]){$(id).hidden=!ref;if(ref)$(name).textContent=label(ref);}
  const rec=records.get(Number(state.inspected));$('selection').hidden=!rec;if(rec){$('elementName').textContent=sourceLabel(rec);$('elementType').textContent=`${rec.type} · #${rec.id}`;$('selectionRole').textContent=t(state.reference?.id===state.inspected&&state.reference.version===state.version?'selection.primary':state.auxReference?.id===state.inspected&&state.auxReference.version===state.version?'selection.aux':'selection.inspected');}
  $('property').hidden=!rec||!state.propertiesOpen;
  $('focusSelected').disabled=!rec||!groups.has(rec.id)||hiddenIds(state).includes(rec.id);
  const hidden=new Set(hiddenIds(state));for(const [id,g] of groups)g.visible=!hidden.has(id);$('hiddenCount').textContent=t('display.hiddenCount',{count:hidden.size});$('showAll').disabled=!hidden.size;$('undoHide').disabled=!hidden.size;
  highlight(rec&&!hidden.has(rec.id)?rec.id:null);render();
  modelTree.update({selected:state.inspected,hidden:[...hidden],mode:state.mode,targetIds:targetRefs(state).filter(r=>r.version===state.version).map(r=>r.id),multi:!!state.multiSelect});
  refreshTargets();
  repairPanel?.invalidate();
}
// Prepare a separate model; failures must not destroy the user's active model or draft.
async function buildIfc(buffer,name,{native=false}={}){
  diagnostics=[];
  const start=performance.now(),root=new T.Group(),sourceBytes=new Uint8Array(buffer).slice();
  let model=-1,records=new Map(),groups=new Map(),pickMeshes=[],bounds=null,report=null;
  checkIfcBytes(sourceBytes);
  try{
    model=api.OpenModel(sourceBytes,{COORDINATE_TO_ORIGIN:false,CIRCLE_SEGMENTS:48,ALLOW_INCOMPATIBLE_SCHEMA_ALIASES:false});if(model<0)throw uiError('error.parse');
    const products=[],v=api.GetLineIDsWithType(model,W.IFCPRODUCT,true);
    for(let i=0;i<v.size();i++){const p=api.GetLine(model,v.get(i));const rec={id:p.expressID,type:api.GetNameFromTypeCode(p.type),name:p.Name?.value||null,guid:p.GlobalId?.value||null,representation:!!p.Representation};products.push(rec);records.set(rec.id,rec);}
    const modelIndex=readModelIndex(api,W,model,records);
    let triangleCount=0,placedCount=0;const renderedIds=new Set(),uniqueGeometry=new Set(),palette=new Map(),geometryCache=new Map();
    let nativeInfo=null;
    if(native){
      bindText($('loading'),'loading.native');
      const response=await fetch('./native/native-meshes.json.gz');
      if(!response.ok)throw uiError('error.nativeMissing');
      const bundle=await response.json();
      if(!sourceMatches(sourceBytes,bundle))throw uiError('error.cacheMismatch');
      const built=buildNativeMeshes(T,bundle,records);
      groups=built.groups;pickMeshes=built.meshes;
      for(const [id,g] of groups){root.add(g);renderedIds.add(id);}
      for(const [k,v] of built.palette)palette.set(k,v);
      triangleCount=built.triangles;placedCount=pickMeshes.length;
      nativeInfo={version:bundle.ifcopenshell,settings:bundle.settings,diagnostics:bundle.diagnostics,diagnosticAudit:bundle.diagnostic_audit||null,maxFloatErrorMillimetres:built.maxFloatErrorMetres*1000,exactSourceBytesMatched:true};
    }else api.StreamAllMeshes(model,flat=>{
      const g=new T.Group();g.userData.expressID=flat.expressID;g.name=sourceLabel(records.get(flat.expressID));let triangles=0;
      for(let i=0;i<flat.geometries.size();i++){
        const placed=flat.geometries.get(i);let geometry=geometryCache.get(placed.geometryExpressID);
        if(!geometry){
          const raw=api.GetGeometry(model,placed.geometryExpressID),a=api.GetVertexArray(raw.GetVertexData(),raw.GetVertexDataSize()),ix=api.GetIndexArray(raw.GetIndexData(),raw.GetIndexDataSize());
          if(!ix.length){raw.delete();continue;}
          // Copy WASM-backed memory before releasing the geometry wrapper.
          const position=new Float32Array(a.length/2),normal=new Float32Array(a.length/2);
          for(let j=0,k=0;j<a.length;j+=6,k+=3){position.set(a.subarray(j,j+3),k);normal.set(a.subarray(j+3,j+6),k);}
          geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(position,3));geometry.setAttribute('normal',new T.BufferAttribute(normal,3));geometry.setIndex(new T.BufferAttribute(ix.slice(),1));geometry.computeBoundingBox();geometryCache.set(placed.geometryExpressID,geometry);raw.delete();
        }
        const c=placed.color,color=new T.Color().setRGB(c.x,c.y,c.z);
        const material=displayMaterial([c.x,c.y,c.z,c.w]);
        material.userData.sourceRGBA=[c.x,c.y,c.z,c.w];const mesh=new T.Mesh(geometry,material);mesh.matrix.fromArray(placed.flatTransformation);mesh.matrixAutoUpdate=false;mesh.userData.expressID=flat.expressID;g.add(mesh);pickMeshes.push(mesh);triangles+=geometry.index.count/3;placedCount++;uniqueGeometry.add(placed.geometryExpressID);const k=JSON.stringify(material.userData.sourceRGBA);palette.set(k,(palette.get(k)||0)+1);
      }
      if(triangles){root.add(g);groups.set(flat.expressID,g);renderedIds.add(flat.expressID);triangleCount+=triangles;
        const rec=records.get(flat.expressID);if(rec){g.updateMatrixWorld(true);const b=exactBounds(g);rec.parsedBoundsMetres=[b.min,b.max];rec.triangles=triangles;}
      }
    });
    root.updateMatrixWorld(true);const box=new T.Box3().setFromObject(root,true);bounds={min:box.min.toArray(),max:box.max.toArray()};if(!compatibleFrame(bounds))throw uiError('error.noGeometry');const center=box.getCenter(new T.Vector3());root.position.copy(center).multiplyScalar(-1);root.updateMatrixWorld(true);
    for(const mesh of pickMeshes)attachEdges(mesh);
    const c=coverage(products,renderedIds);
    report={source:{name,bytes:sourceBytes.length,schema:api.GetModelSchema(model),modified:false},parser:{name:'web-ifc',version:api.GetVersion(),build_commit:'a7b53a8b41376993fb2f70cfe85e7a293d43348c',settings:{COORDINATE_TO_ORIGIN:false,CIRCLE_SEGMENTS:48},renderer:'Three.js r'+T.REVISION,colorInterpretation:'web-ifc official example convention: raw RGB passed to linear Three.Color; output sRGB; source alpha retained'},coverage:c,geometry:{renderedProducts:renderedIds.size,placedMeshes:placedCount,uniqueGeometry:uniqueGeometry.size,triangles:triangleCount,parserWorldBoundsMetres:bounds,displayOffsetMetres:center.toArray(),sourceToParserFrame:'web-ifc native coordinate convention; not inferred from screenshots'},materials:[...palette].map(([rgba,count])=>({rgba:JSON.parse(rgba),placedMeshes:count})),diagnostics,parseAndBuildMs:Math.round(performance.now()-start),validation:'not run; mesh coverage is not IFC compliance or full geometric fidelity',sourceProducts:products};
    if(nativeInfo){report.parser={name:'IfcOpenShell',version:nativeInfo.version,settings:nativeInfo.settings,semanticReader:'web-ifc '+api.GetVersion(),renderer:'Three.js r'+T.REVISION};report.native=nativeInfo;report.geometry.sourceToParserFrame='native (x,y,z) to browser (x,z,-y)';report.geometry.uniqueGeometry=null;}
    report.boundsMethod='exact transformed mesh vertices';
    report.display={colourInterpretation:'source RGB treated as sRGB for reference-viewer comparison; IFC values unchanged',transparentFaces:'front-facing surfaces; original alpha retained',edges:'35-degree geometric feature edges, optional',sourceGeometryEdited:false};
    report.inspectionDiagnostics=modelIndex.errors;
    report.displayClassification=classifyDisplayRecords(products,renderedIds);
    return {model,root,sourceBytes,sourceName:name,records,groups,pickMeshes,bounds,report,native,modelIndex};
  }catch(e){
    root.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
    if(model>=0)api.CloseModel(model);
    throw e;
  }
}
async function loadIfc(buffer,name,{native=false,preserveTask=false}={}){
  if(loading||pairLoading)return;
  if(repairPanel?.locked&&!preserveTask)throw uiError('repair.busyModel');
  loading=true;generation++;closeContext();diagnostics=[];lastLoadError=null;
  globalThis.__IFC_READY__=false;globalThis.__IFC_ERROR__=null;
  $('loadNotice').hidden=true;$('file').disabled=true;$('sampleButton').disabled=true;
  $('loading').hidden=false;$('loading').className='loading';bindText($('loading'),'loading.file');update();
  await new Promise(resolve=>setTimeout(resolve,40));
  try{
    const candidate=await buildIfc(buffer,name,{native});
    // Swap only after a valid, finite drawable candidate has been built.
    const oldModel=model;dropPair();resetScene();if(oldModel>=0)api.CloseModel(oldModel);
    ({model,sourceBytes,sourceName,records,groups,pickMeshes,bounds,report,modelIndex}=candidate);
    root.position.copy(candidate.root.position);root.add(...candidate.root.children.slice());
    state=createState();state.version=state.baseVersion=`source-${generation}`;state.hiddenByVersion={[state.version]:[]};
    $('messages').replaceChildren();repairPanel?.reset();currentExample=null;$('exampleBanner').hidden=true;$('resetExample').hidden=true;$('conversation').querySelector('.guide').hidden=false;
    $('properties').replaceChildren();propertyView=null;nativeRequested=native;unlit=false;
    propertyRequest++;modelTree.build(records,groups,name);
    root.traverse(o=>{if(o.userData.displayOverlay)o.visible=edgesEnabled;});
    $('edges').setAttribute('aria-pressed',String(edgesEnabled));
    $('unlit').textContent=t('action.unlit');$('unlit').setAttribute('aria-pressed','false');
    $('modelName').removeAttribute('data-i18n');$('modelName').textContent=name;bindText($('modelInfo'),'display.info',{schema:report.source.schema,size:(sourceBytes.length/1048576).toFixed(2)});
    bindText($('sourceTag'),native?'display.native':'display.webifc');$('saveSource').disabled=false;
    const summary=summarizeDiagnostics(report);
    $('stats').removeAttribute('data-i18n');$('stats').textContent=summary.text;$('stats').dataset.level=summary.level;
    refreshReportText();
    $('report').textContent=JSON.stringify(reviewParams.get('capture')==='1'?report:{...report,sourceProducts:undefined},null,2);
    $('loading').hidden=true;setStatus(summary.text);preset(native?'front':'side');
    globalThis.__IFC_READY__=true;document.body.dataset.ifcReady='true';document.body.dataset.geometryProducts=String(report.geometry.renderedProducts);
  }catch(e){
    globalThis.__IFC_ERROR__=e.message;globalThis.__IFC_READY__=model>=0;
    lastLoadError={name,error:e};const message=loadErrorText();
    $('loading').hidden=model>=0;$('loading').className='loading error';$('loading').removeAttribute('data-i18n');$('loading').textContent=message;
    $('loadNotice').textContent=message;$('loadNotice').hidden=false;setStatus(message);throw e;
  }finally{loading=false;$('file').disabled=false;$('sampleButton').disabled=false;update();}
}
async function properties(){
 if(loading||model<0||!records.has(state.inspected))return;
 const id=state.inspected,version=state.version,request=++propertyRequest;
 state.propertiesOpen=true;propertyView={id,version,pending:true};update();$('properties').textContent=t('property.loading');
 await new Promise(resolve=>setTimeout(resolve,0));
 if(state.version!==version||state.inspected!==id||request!==propertyRequest)return;
 try{
  const data=readInspection(api,model,id,modelIndex);
  if(state.version!==version||state.inspected!==id||request!==propertyRequest)return;
  propertyView={id,version,data};renderInspection($('properties'),records.get(id),data);
 }catch(e){
  if(state.version===version&&state.inspected===id){propertyView={id,version,error:e};$('properties').textContent=t('property.failed',{error:errorText(e)});}
 }
}
function closeContext(){contextId=null;$('context').hidden=true;}
function changeMode(mode){closeContext();setMode(state,mode);update();if(mode==='select')$('request').focus();}
async function submit(){
  if(repairPanel?.locked||pairLoading)return;
  if(modelPair&&state.version!==state.baseVersion){toast(uiError('repair.pairNote'));return;}
  if(state.mode==='view'){changeMode('select');return;}if(!sourceBytes||model<0)throw uiError('error.loadFirst');
  for(const ref of [...targetRefs(state),state.auxReference])if(ref&&!validReference(ref,state.version,records))throw uiError('error.reference');
  $('conversation').querySelector('.guide').hidden=true;
  if(state.multiSelect)$('targetGroup').open=false;
  await repairPanel.prepare();update();
}
function refreshTargets(){
 const refs=targetRefs(state),locked=!!repairPanel?.locked||pairLoading||state.mode!=='select'||state.version!==state.baseVersion;
 $('multiSelect').hidden=state.mode!=='select';$('multiSelect').disabled=locked;$('multiSelect').setAttribute('aria-pressed',String(!!state.multiSelect));
 $('targetGroup').hidden=!state.multiSelect;bindText($('targetCount'),'multi.count',{count:refs.length});
 $('clearTargets').disabled=locked||!refs.length;$('addAux').disabled=locked;$('removeAux').disabled=locked;$('removePrimary').disabled=locked;
 const host=$('targetList');host.replaceChildren();
 for(const ref of refs){const row=document.createElement('div');row.className='target-row';row.dataset.targetId=String(ref.id);const name=document.createElement('button');name.type='button';name.textContent='#'+ref.id+' '+label(ref);name.title=label(ref);name.onclick=()=>{if(modelPair)showPair('before');state.inspected=ref.id;state.propertiesOpen=false;update();modelTree.reveal(ref.id);const g=groups.get(ref.id);if(g?.visible){fitVisible(T,cam,controls,[g],$('canvas').clientWidth/$('canvas').clientHeight);render();}};const remove=document.createElement('button');remove.type='button';remove.textContent='×';remove.setAttribute('aria-label',t('multi.remove',{name:label(ref)}));remove.disabled=locked;remove.onclick=safe(()=>{removeTarget(state,ref.id);update();});row.append(name,remove);host.append(row);}
 if(state.multiSelect&&refs.some(r=>r.id===state.inspected&&r.version===state.version))$('selectionRole').textContent=t('multi.target');
}
function currentBundle(){return {model,sourceBytes,sourceName,records,groups,pickMeshes,bounds,report,modelIndex,native:nativeRequested,nodes:root.children.slice(),offset:root.position.toArray(),version:state.version};}
function disposeBundle(bundle){
 const geometries=new Set(),materials=new Set();for(const n of bundle.nodes||[])n.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)materials.add(o.material);});
 for(const g of geometries)g.dispose();for(const m of materials)m.dispose();if(bundle.model>=0)api.CloseModel(bundle.model);
}
function dropPair(){restoreHighlight();if(modelPair){for(const b of [modelPair.before,modelPair.after])if(b.model!==model)disposeBundle(b);modelPair=null;}$('resultBar').hidden=true;delete document.body.dataset.repairResultReady;}
function refreshPair(){
 refreshExample();
 if(modelPair){const picker=$('newObjectPicker'),value=picker.value;picker.replaceChildren();for(const item of modelPair.added){const option=document.createElement('option');option.value=item.guid;option.textContent=sourceLabel(item);picker.append(option);}if(modelPair.added.some(x=>x.guid===value))picker.value=value;picker.hidden=modelPair.added.length<2;}
 bindText($('resultHint'),modelPair?'repair.pairNote':'guide.noResult');
 if(modelPair)bindText($('baseVersion'),'repair.inputName',{name:modelPair.before.sourceName});else bindText($('baseVersion'),'guide.base');
 $('resultBar').hidden=!modelPair;if(!modelPair)return;
 $('viewBefore').setAttribute('aria-pressed',String(state.version===modelPair.before.version));$('viewAfter').setAttribute('aria-pressed',String(state.version===modelPair.after.version));
 bindText($('viewAfter'),modelPair.role==='history'?'demo.result':modelPair.role==='success'?'repair.after':'repair.candidate');
 bindText($('pairSummary'),'repair.addedCount',{count:modelPair.added.length});$('locateChange').disabled=!modelPair.added.length;$('useResult').disabled=modelPair.role!=='success';
}
function showPair(which){
 if(!modelPair||pairLoading)return;
 const b=modelPair[which],previousGuid=records.get(state.inspected)?.guid;
 restoreHighlight();root.clear();root.add(...b.nodes);root.position.fromArray(modelPair.offset);
 ({model,sourceBytes,sourceName,records,groups,pickMeshes,bounds,report,modelIndex}=b);nativeRequested=false;unlit=false;
 state.version=b.version;state.inspected=findByGuid(records,previousGuid);state.propertiesOpen=false;propertyRequest++;propertyView=null;
 $('properties').replaceChildren();modelTree.build(records,groups,sourceName);
 root.traverse(o=>{if(o.userData.displayOverlay)o.visible=edgesEnabled;});
 $('modelName').textContent=sourceName;bindText($('modelInfo'),'display.info',{schema:report.source.schema,size:(sourceBytes.length/1048576).toFixed(2)});bindText($('sourceTag'),'display.webifc');
 $('report').textContent=JSON.stringify({...report,sourceProducts:undefined,comparison:{sameCoordinates:true,offset:modelPair.offset}},null,2);refreshReportText();refreshPair();update();
}
async function loadTaskResult(artifact,task,prepared){
 const role=validateResultRole(artifact,task);if(pairLoading)return;
 if(modelPair?.artifactId===artifact.artifact_id){showPair('after');return;}
 pairLoading=true;update();const source=modelPair?.before||currentBundle(),offset=pairOffset(source.offset);let before=source,after=null;
 try{
  const data=await repairPanel.client.resource(artifact.download_url);
  // Both sides use the same web-ifc path. Never reuse the sample's native cache for new bytes.
  if(source.native)before=await buildIfc(source.sourceBytes,source.sourceName,{native:false});
  after=await buildIfc(data,role==='history'?'archived-result.ifc':role==='success'?'repaired.ifc':'repaired-candidate.ifc',{native:false});
  before.nodes??=before.root.children.slice();before.offset=offset;before.version=state.baseVersion;
  after.nodes=after.root.children.slice();after.offset=offset;after.version='result-'+task.run_id;
  const previous=modelPair;
  modelPair={before,after,offset,role,artifactId:artifact.artifact_id,taskId:task.task_id,added:newVisibleObjects(before,after)};
  const hidden=(state.hiddenByVersion[before.version]||[]).map(id=>before.records.get(id)?.guid);
  state.hiddenByVersion[after.version]=hidden.map(g=>findByGuid(after.records,g)).filter(id=>id!==null);
  pairLoading=false;showPair('after');
  if(source!==before)disposeBundle(source);if(previous?.after&&previous.after!==after)disposeBundle(previous.after);
  document.body.dataset.repairResultReady=role;
 }catch(error){if(after)disposeBundle(after);if(before!==source)disposeBundle(before);throw error;}
 finally{pairLoading=false;update();}
}
async function restoreTaskSource(bytes,name,prepared){
 await loadIfc(bytes,name,{native:false,preserveTask:true});
 const refs=prepared.references||{},version=refs.targets?.[0]?.view_version||refs.primary?.view_version||refs.auxiliary?.view_version||state.version;
 state.multiSelect=Array.isArray(refs.targets);state.targets=(refs.targets||[]).map(r=>({id:r.step_id,version}));
 state.version=state.baseVersion=version;state.hiddenByVersion={[version]:[]};
 state.reference=refs.primary?{id:refs.primary.step_id,version}:null;state.auxReference=refs.auxiliary?{id:refs.auxiliary.step_id,version}:null;state.draft='';update();
}
async function previewTaskCandidate(candidate){
 if(candidate.candidate_kind&&candidate.candidate_kind!=='target')return false;
 if(modelPair)showPair('before');const id=findByGuid(records,candidate.public_id);
 if(id===null||!groups.has(id))return false;
 state.inspected=id;state.propertiesOpen=false;update();modelTree.reveal(id);const g=groups.get(id);
 if(!g.visible){state.hiddenByVersion[state.version]=hiddenIds(state).filter(x=>x!==id);update();}
 fitVisible(T,cam,controls,[g],$('canvas').clientWidth/$('canvas').clientHeight);render();return true;
}
function locateResultGuid(guid){
 if(modelPair)showPair('after');let id=findByGuid(records,guid);
 if(id===null&&modelPair){showPair('before');id=findByGuid(records,guid);}
 if(id===null||!groups.has(id))return false;
 state.inspected=id;state.propertiesOpen=false;state.hiddenByVersion[state.version]=hiddenIds(state).filter(x=>x!==id);update();modelTree.reveal(id);fitVisible(T,cam,controls,[groups.get(id)],$('canvas').clientWidth/$('canvas').clientHeight);render();return true;
}
function requestSnapshot(){
 const base=modelPair?.before||{sourceBytes,sourceName,records,version:state.baseVersion};
 const ref=x=>x?{id:x.id,guid:base.records.get(Number(x.id))?.guid||null,version:x.version}:null;
 return {bytes:base.sourceBytes,name:base.sourceName,version:state.baseVersion,text:state.draft,primary:state.multiSelect?null:ref(state.reference),auxiliary:ref(state.auxReference),...(state.multiSelect?{targets:targetRefs(state).map(ref)}:{})};
}
repairPanel=new RepairPanel({host:$('repairPanel'),snapshot:requestSnapshot,onRestoreSource:restoreTaskSource,onResult:loadTaskResult,onPreviewCandidate:previewTaskCandidate,onLocateObject:locateResultGuid,onStateChange:()=>{update();refreshPair();},onStarted:(task,prepared,frozen)=>{
  const req={id:++state.counter,text:prepared.user_text,reference:frozen.primary,auxReference:frozen.auxiliary,baseVersion:frozen.version,status:'api_submitted',task_id:task.task_id};
  state.requests.push(req);if(state.draft===frozen.text)state.draft='';
  const box=document.createElement('div');box.className='message';box.dataset.requestId=String(req.id);box.textContent=req.text;
  const note=document.createElement('small');note.textContent=requestNote(req);box.append(note);$('messages').append(box);update();
}});
async function loadLocalExample(item,mode){
 if(repairPanel.locked||loading||pairLoading)throw uiError('repair.busyModel');
 const bytes=await repairPanel.client.resource(item.input_url);
 await loadIfc(bytes,item.id+'-input.ifc',{native:false});
 currentExample={...item,mode};state.draft=item.request;state.mode=mode==='input'?'select':'view';
 $('exampleBanner').hidden=false;$('resetExample').hidden=false;refreshExample();
 if(mode==='history')await loadTaskResult({role:'archived_successful_ifc',artifact_id:'archive-'+item.id,download_url:item.result_url},{evidence_class:item.evidence_class,archived_success:item.archived_success,task_id:'archive-'+item.id,run_id:item.recorded_run},null);
 update();
}
function refreshExample(){
 if(!currentExample)return;
 $('exampleBanner').textContent=(getLanguage()==='en'?currentExample.title_en:currentExample.title)+' · '+t(currentExample.mode==='history'?'demo.history':'demo.keepHistory');
}
new LocalExamples({button:$('examplesButton'),dialog:$('examplesDialog'),client:repairPanel.client,onChoose:safe(loadLocalExample),onError:toast,locked:()=>repairPanel.locked||loading||pairLoading});
$('resetExample').onclick=safe(()=>currentExample&&loadLocalExample(currentExample,'input'));
repairPanel.client.capabilities().then(c=>bindText($('executionHint'),c.execution_enabled?(c.runtime?.mode==='live'?'guide.live':'guide.executionAvailable'):'guide.scope')).catch(()=>bindText($('executionHint'),'guide.apiUnavailable'));
function requestNote(req){
 return t(req.task_id?'repair.started':'request.saved')+(req.reference?t('request.primary',{id:req.reference.id}):'')+(req.auxReference?t('request.aux',{id:req.auxReference.id}):'');
}
function loadErrorText(){
 return t('error.open',{name:lastLoadError.name,error:errorText(lastLoadError.error)})+' '+t(model>=0?'error.kept':'error.choose');
}
function refreshReportText(){
 if(!report)return;
 const summary=summarizeDiagnostics(report);
 $('stats').removeAttribute('data-i18n');$('stats').textContent=summary.text;$('stats').dataset.level=summary.level;
 $('diagnosticSummary').style.whiteSpace='pre-line';$('diagnosticSummary').textContent=summary.detail;
 if(!lastLoadError&&!loading)setStatus(summary.text);
}
function refreshLocale(){
 const propertyScroll=$('property').scrollTop,treeScroll=$('treeContent').scrollTop,conversationScroll=$('conversation').scrollTop;
 $('langZh').setAttribute('aria-pressed',String(getLanguage()==='zh'));$('langEn').setAttribute('aria-pressed',String(getLanguage()==='en'));
 update();refreshReportText();
 $('unlit').textContent=t(unlit?'action.lit':'action.unlit');$('reportButton').textContent=t($('reportPanel').hidden?'action.expandReport':'action.collapseReport');
 for(const req of state.requests){const note=$('messages').querySelector('[data-request-id="'+req.id+'"] small');if(note)note.textContent=requestNote(req);}
 if(propertyView&&propertyView.id===state.inspected&&propertyView.version===state.version){
  if(propertyView.data)renderInspection($('properties'),records.get(propertyView.id),propertyView.data,{preserveExpansion:true});
  else $('properties').textContent=propertyView.error?t('property.failed',{error:errorText(propertyView.error)}):t('property.loading');
 }
 if(lastLoadError){const message=loadErrorText();$('loadNotice').textContent=message;$('loading').textContent=message;setStatus(message);}
 if(initializationError)$('loading').textContent=t('error.init',{error:errorText(initializationError)});
 if(!$('toast').hidden&&toastValue!==null)$('toast').textContent=errorText(toastValue);
 $('property').scrollTop=propertyScroll;$('treeContent').scrollTop=treeScroll;$('conversation').scrollTop=conversationScroll;
}
$('langZh').onclick=()=>setLanguage('zh');$('langEn').onclick=()=>setLanguage('en');onLanguageChange(refreshLocale);refreshLocale();

try{
  if(!T||!W)throw uiError('error.resources');
  renderer=new T.WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true});renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0x000000,0);$('canvas').append(renderer.domElement);
  cam=new T.OrthographicCamera(-20,20,15,-15,.05,500);cam.position.set(60,20,20);controls=new T.OrbitControls(cam,renderer.domElement);controls.enableDamping=false;controls.screenSpacePanning=true;controls.minZoom=.1;controls.maxZoom=20;controls.addEventListener('change',render);new ResizeObserver(resize).observe($('canvas'));resize();
  let down=null;
  renderer.domElement.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY,button:e.button,moved:false,id:pick(e.clientX,e.clientY)};},true);
  renderer.domElement.addEventListener('pointermove',e=>{if(down&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)down.moved=true;},true);
  renderer.domElement.addEventListener('pointerup',e=>{const d=down;down=null;if(!d||d.moved||d.id===null)return;if(d.button===2){if(state.mode!=='view')return;contextId={id:d.id,version:state.version};$('contextName').textContent=sourceLabel(records.get(d.id));$('context').style.left=Math.max(8,Math.min(e.clientX,innerWidth-250))+'px';$('context').style.top=Math.max(8,Math.min(e.clientY,innerHeight-150))+'px';$('context').hidden=false;$('hide').focus();}else if(d.button===0)selectObject(d.id,{additive:e.ctrlKey||e.metaKey});},true);
  renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());renderer.domElement.addEventListener('pointercancel',()=>{down=null;});
  // Install before Init: Emscripten binds its console callback during initialization.
  for(const fn of ['error','warn','log']){const original=console[fn].bind(console);console[fn]=(...args)=>{const text=args.map(String).join(' ');if(text.includes('[WEB-IFC]'))diagnostics.push({level:fn,message:text});original(...args);};}
  api=new W.IfcAPI();api.SetWasmPath(new URL('./vendor/',import.meta.url).href,true);await api.Init(()=>globalThis.__WASM_URL__||new URL('./vendor/web-ifc.wasm',import.meta.url).href,true);bindText($('loading'),'loading.prompt');bindText($('status'),'loading.ready');globalThis.__PARSER_READY__=true;
  if(reviewParams.get('task')){const restored=await repairPanel.restore(reviewParams.get('task'));if(!restored&&model<0){$('loading').hidden=true;}}
  else if(globalThis.__EMBEDDED_IFC__){await loadIfc(globalThis.__EMBEDDED_IFC__,globalThis.__SOURCE_NAME__||'sample.ifc');}
  else if(reviewParams.get('sample')==='174'){
    const response=await fetch('./sample.ifc');if(!response.ok)throw uiError('error.sampleMissing');
    await loadIfc(await response.arrayBuffer(),'model_174.ifc',{native:reviewParams.get('engine')!=='webifc'});
  }
  if(globalThis.__IFC_READY__){if(!reviewParams.get('task'))preset(reviewParams.get('view')==='side'?'side':'front');document.body.dataset.ifcReady='true';document.body.dataset.geometryProducts=String(report.geometry.renderedProducts);}
}catch(e){initializationError=e;$('loading').hidden=false;$('loading').className='loading error';$('loading').removeAttribute('data-i18n');$('loading').textContent=t('error.init',{error:errorText(e)});globalThis.__IFC_ERROR__=e.message;}
$('file').onchange=safe(async e=>{const f=e.target.files[0];if(!f||loading)return;try{if(f.size>100*1048576)throw uiError('error.fileSize');await loadIfc(await f.arrayBuffer(),f.name);}finally{e.target.value='';}});
$('saveSource').onclick=()=>sourceBytes&&download(sourceBytes,sourceName,'application/x-step');
$('viewMode').onclick=()=>changeMode('view');$('selectMode').onclick=()=>changeMode('select');
$('multiSelect').onclick=safe(()=>{setMulti(state,!state.multiSelect);$('targetGroup').open=state.multiSelect;update();});$('clearTargets').onclick=safe(()=>{clearTargets(state);update();});
$('addAux').onclick=safe(()=>{armAuxReference(state);update();});$('removePrimary').onclick=()=>{clearReference(state);update();};$('removeAux').onclick=()=>{clearAuxReference(state);update();};
$('request').oninput=()=>{state.draft=$('request').value;repairPanel.invalidate();update();};$('submit').onclick=safe(submit);
$('propertiesBtn').onclick=safe(properties);$('closeProperty').onclick=()=>{state.propertiesOpen=false;update();};$('clearInspection').onclick=()=>{state.inspected=null;state.propertiesOpen=false;update();};
$('hide').onclick=safe(()=>{if(contextId&&contextId.version===state.version){hideElement(state,contextId.id);closeContext();update();}});$('undoHide').onclick=()=>{undoHide(state);update();};$('showAll').onclick=()=>{showAll(state);update();};
$('fit').onclick=()=>{if(!bounds)return;if(!fitVisible(T,cam,controls,groups.values(),$('canvas').clientWidth/$('canvas').clientHeight))toast(uiError('display.noVisible'));render();};document.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>preset(b.dataset.camera));
$('reportButton').onclick=()=>{$('reportPanel').hidden=!$('reportPanel').hidden;$('reportButton').textContent=t($('reportPanel').hidden?'action.expandReport':'action.collapseReport');};$('downloadReport').onclick=()=>report&&download(JSON.stringify(report,null,2),'ifc-display-report.json','application/json');
$('unlit').onclick=()=>{
  restoreHighlight();unlit=!unlit;
  for(const mesh of pickMeshes){const old=mesh.material;mesh.material=displayMaterial(old.userData.sourceRGBA,{unlit});mesh.material.flatShading=nativeRequested;old.dispose();}
  $('unlit').textContent=t(unlit?'action.lit':'action.unlit');$('unlit').setAttribute('aria-pressed',String(unlit));highlight(state.inspected);render();
};
$('throughHighlight').onclick=()=>{selectionHighlighter.setThrough(!selectionHighlighter.through);$('throughHighlight').setAttribute('aria-pressed',String(selectionHighlighter.through));update();};
$('viewBefore').onclick=()=>showPair('before');$('viewAfter').onclick=()=>showPair('after');
$('locateChange').onclick=()=>{if(!modelPair?.added.length)return;showPair('after');const item=modelPair.added.find(x=>x.guid===$('newObjectPicker').value)||modelPair.added[0];state.inspected=item.id;state.propertiesOpen=false;update();modelTree.reveal(item.id);const g=groups.get(item.id);if(g&&!g.visible){state.hiddenByVersion[state.version]=hiddenIds(state).filter(x=>x!==item.id);update();}if(g){fitVisible(T,cam,controls,[g],$('canvas').clientWidth/$('canvas').clientHeight);render();}};
$('useResult').onclick=safe(async()=>{if(!modelPair||modelPair.role!=='success'||repairPanel.locked)return;const next=modelPair.after;await loadIfc(next.sourceBytes,next.sourceName,{native:false});});
$('edges').onclick=()=>{restoreHighlight();edgesEnabled=!edgesEnabled;root.traverse(o=>{if(o.userData.displayOverlay)o.visible=edgesEnabled;});$('edges').setAttribute('aria-pressed',String(edgesEnabled));update();};
$('focusSelected').onclick=()=>{const g=groups.get(state.inspected);if(g?.visible){fitVisible(T,cam,controls,[g],$('canvas').clientWidth/$('canvas').clientHeight);render();}};
function toggleTree(show){$('modelTree').hidden=!show;$('treeToggle').setAttribute('aria-expanded',String(show));requestAnimationFrame(resize);}
$('treeToggle').onclick=()=>toggleTree($('modelTree').hidden);
$('closeTree').onclick=()=>toggleTree(false);
if(innerWidth<1150)toggleTree(false);
$('sampleButton').onclick=()=>{location.href='./?sample=174&engine=native';};
document.addEventListener('pointerdown',e=>{if(!$('context').hidden&&!$('context').contains(e.target))closeContext();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeContext();state.inspected=null;state.propertiesOpen=false;update();}if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();safe(submit)();}});
// Read-only snapshots for real-pointer QA; no hidden mutation or Repair execution API.
globalThis.__viewer={displayState:()=>{const edges=[];root.traverse(o=>{if(o.userData.displayOverlay)edges.push(o.visible);});return {edgesEnabled,edgesAgree:edges.every(v=>v===edgesEnabled),loading};},state:()=>structuredClone(state),report:()=>structuredClone(report),camera:()=>({position:cam?.position.toArray(),target:controls?.target.toArray(),zoom:cam?.zoom}),project:(id)=>{const g=groups.get(Number(id));if(!g)return null;const p=new T.Box3().setFromObject(g).getCenter(new T.Vector3()).project(cam),r=renderer.domElement.getBoundingClientRect();return {x:r.left+(p.x+1)*r.width/2,y:r.top+(1-p.y)*r.height/2};},snapshot:()=>({visible:[...groups].filter(([i,g])=>g.visible).map(([i])=>i),records:[...records.values()],renderer:T.REVISION}),sourceSize:()=>sourceBytes?.length,selectionDetails:()=>({targetIds:targetRefs(state).map(r=>r.id),highlightedIds:[...targetHighlighters.active.keys()],through:selectionHighlighter.through}),frame:()=>({displayOffset:root.position.toArray(),comparisonOffset:modelPair?.offset||null,currentVersion:state.version,baseVersion:state.baseVersion,engine:nativeRequested?'native':'webifc'})};
update();
