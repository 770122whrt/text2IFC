import * as T from './vendor/three.module.js';

/** Whole-product highlight. Optional translucent pass shows only occluded fragments.
 * Source triangles/materials and raycast targets are never modified by the overlay.
 */
export class SelectionHighlighter {
 constructor({through=false}={}){this.group=null;this.saved=[];this.edges=[];this.overlays=[];this.through=through;}
 setThrough(value){this.through=!!value;for(const o of this.overlays)o.visible=this.through;}
 select(group){
  if(this.group===group)return;
  this.clear();if(!group)return;this.group=group;
  const meshes=[];group.traverse(m=>{if(m.isMesh&&!m.userData.displayOverlay&&!m.userData.selectionOverlay)meshes.push(m);});
  for(const mesh of meshes){
   this.saved.push({mesh,material:mesh.material,order:mesh.renderOrder});
   mesh.material=new T.MeshBasicMaterial({color:0xd6ac5c,side:T.DoubleSide,transparent:false,opacity:1,depthTest:true,depthWrite:true,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-4,toneMapped:false});
   mesh.material.userData.selectionOnly=true;mesh.renderOrder=1000;
   for(const o of mesh.children)if(o.userData.displayOverlay){this.edges.push({object:o,visible:o.visible});o.visible=false;}
   const material=new T.MeshBasicMaterial({color:0xffc44d,side:T.DoubleSide,transparent:true,opacity:.36,depthTest:true,depthFunc:T.GreaterDepth,depthWrite:false,toneMapped:false,forceSinglePass:true});
   const ghost=new T.Mesh(mesh.geometry,material); // shares immutable geometry
   ghost.userData.selectionOverlay=true;ghost.userData.ownsGeometry=false;ghost.raycast=()=>{};ghost.renderOrder=2000;ghost.visible=this.through;mesh.add(ghost);this.overlays.push(ghost);
   const edge=new T.LineSegments(new T.EdgesGeometry(mesh.geometry,35),new T.LineBasicMaterial({color:0xf2ad20,transparent:true,opacity:.9,depthTest:true,depthFunc:T.GreaterDepth,depthWrite:false,toneMapped:false}));
   edge.userData.selectionOverlay=true;edge.userData.ownsGeometry=true;edge.raycast=()=>{};edge.renderOrder=2001;edge.visible=this.through;mesh.add(edge);this.overlays.push(edge);
  }
 }
 clear(){
  for(const o of this.overlays){o.removeFromParent();o.material.dispose();if(o.userData.ownsGeometry)o.geometry.dispose();}
  for(const {mesh,material,order} of this.saved){mesh.material.dispose();mesh.material=material;mesh.renderOrder=order;}
  for(const {object,visible} of this.edges)object.visible=visible;
  this.saved=[];this.edges=[];this.overlays=[];this.group=null;
 }
}
