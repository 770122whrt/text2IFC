import {t,uiError} from './i18n.mjs';
import * as T from './vendor/three.module.js';
/** Exact world extents. Do not rotate an already axis-aligned local bounding box. */
export function exactBounds(object){
 object.updateWorldMatrix(true,true);const box=new T.Box3().setFromObject(object,true);
 return {min:box.min.toArray(),max:box.max.toArray()};
}
export function sourceMatches(bytes,bundle){
 if(typeof bundle.source_base64!=='string')return false;
 const original=atob(bundle.source_base64);
 if(original.length!==bytes.length)return false;
 for(let i=0;i<bytes.length;i++)if(bytes[i]!==original.charCodeAt(i))return false;
 return true;
}
/** IFC RGB has no universal screenshot colour profile: the review convention is explicit. */
export function displayMaterial(rgba,{unlit=false,linear=false}={}){
 if(!Array.isArray(rgba)||rgba.length!==4||rgba.some(x=>!Number.isFinite(x)))throw Error('Invalid source RGBA');
 const color=new T.Color().setRGB(...rgba.slice(0,3),linear?T.LinearSRGBColorSpace:T.SRGBColorSpace);
 const options={color,opacity:rgba[3],transparent:rgba[3]<1,depthWrite:rgba[3]>=1,side:rgba[3]<1?T.FrontSide:T.DoubleSide,flatShading:false,forceSinglePass:true};
 const m=unlit?new T.MeshBasicMaterial(options):new T.MeshPhongMaterial({...options,specular:0,shininess:1});
 m.userData.sourceRGBA=rgba.slice();m.userData.colourConvention=linear?'linear-sRGB':'sRGB-review';return m;
}
export function checkIfcBytes(bytes){
 const text=new TextDecoder().decode(bytes.subarray(0,65536));
 if(text.startsWith('version https://git-lfs'))throw uiError('error.lfs');
 if(!text.trimStart().startsWith('ISO-10303-21;'))throw uiError('error.notStep');
 const match=text.match(/FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'/i);
 if(!match)throw uiError('error.schema');
 return match[1].toUpperCase();
}
export function loadMessage(coverage,diagnostics){
 if(coverage.missing.length)return {level:'partial',text:t('display.partial',{missing:coverage.missing.length,rendered:coverage.rendered,expected:coverage.expected})};
 if(diagnostics)return {level:'warning',text:t('display.warning',{count:diagnostics})};
 return {level:'ready',text:t('display.ready',{count:coverage.rendered})};
}
/** Fit visible geometry without changing view orientation or modifying model state. */
export function fitVisible(T,camera,controls,groups,aspect){
 const box=new T.Box3();
 for(const group of groups)if(group.visible){group.updateWorldMatrix(true,true);box.union(new T.Box3().setFromObject(group,true));}
 if(box.isEmpty()||!Number.isFinite(aspect)||aspect<=0)return false;
 const center=box.getCenter(new T.Vector3()),radius=Math.max(box.getSize(new T.Vector3()).length()/2,.001);
 const direction=camera.position.clone().sub(controls.target).normalize();
 const distance=radius*3;camera.position.copy(center).addScaledVector(direction,distance);
 controls.target.copy(center);camera.lookAt(center);camera.zoom=1;camera.updateMatrixWorld(true);
 let maxX=0,maxY=0;
 for(let i=0;i<8;i++){
   const point=new T.Vector3(i&1?box.max.x:box.min.x,i&2?box.max.y:box.min.y,i&4?box.max.z:box.min.z).applyMatrix4(camera.matrixWorldInverse);
   maxX=Math.max(maxX,Math.abs(point.x));maxY=Math.max(maxY,Math.abs(point.y));
 }
 const half=Math.max(maxY,maxX/aspect,.001)*1.12;
 camera.top=half;camera.bottom=-half;camera.left=-half*aspect;camera.right=half*aspect;
 camera.near=Math.max(.0001,distance-radius*1.25);camera.far=distance+radius*1.25;
 camera.updateProjectionMatrix();controls.update();return true;
}
export function attachEdges(mesh){
 const rgba=mesh.material.userData.sourceRGBA;
 if(rgba[3]<1)return; // No invented glass grid or texture.
 const geometry=new T.EdgesGeometry(mesh.geometry,35);
 const line=new T.LineSegments(geometry,new T.LineBasicMaterial({color:0x414141,transparent:true,opacity:.20,depthWrite:false}));
 line.userData.displayOverlay=true;line.raycast=()=>{};mesh.add(line);
 mesh.material.polygonOffset=true;mesh.material.polygonOffsetFactor=1;mesh.material.polygonOffsetUnits=1;
}
