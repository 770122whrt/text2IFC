import {exactBounds,displayMaterial} from './display-geometry.mjs';
/** Display native triangle arrays; no IFC geometry reconstruction or solid editing. */
export function buildNativeMeshes(T,bundle,records){
 if(bundle.schema!=='ifc-native-mesh-preview/1')throw Error('Unknown native mesh schema');
 const groups=new Map(),meshes=[],palette=new Map();let triangles=0,maxFloatErrorMetres=0;
 for(const item of bundle.products){
  const record=records.get(item.id);
  if(!record||record.guid!==item.guid||groups.has(item.id))throw Error('Native cache object does not match current IFC');
  const positions=new Float32Array(item.vertices.length*3);
  item.vertices.forEach((p,i)=>{
   if(p.length!==3||!p.every(Number.isFinite))throw Error('Invalid vertex');
   const v=[p[0],p[2],-p[1]];positions.set(v,i*3);
   for(let j=0;j<3;j++)maxFloatErrorMetres=Math.max(maxFloatErrorMetres,Math.abs(positions[i*3+j]-v[j]));
  });
  if(item.faces.length!==item.material_ids.length)throw Error('Invalid face/material map');
  const group=new T.Group();group.userData.expressID=item.id;group.name=record.name||record.type+' #'+item.id;
  for(const mi of new Set(item.material_ids)){
   const indices=[];
   item.faces.forEach((f,i)=>{if(item.material_ids[i]===mi){if(f.length!==3||f.some(x=>!Number.isInteger(x)||x<0||x>=item.vertices.length))throw Error('Invalid triangle');indices.push(...f);}});
   const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(positions,3));g.setIndex(new T.BufferAttribute(new Uint32Array(indices),1));g.computeVertexNormals();g.computeBoundingBox();
   const rgba=item.materials[mi]?.rgba||[.7,.7,.7,1];const mesh=new T.Mesh(g,displayMaterial(rgba));mesh.userData.expressID=item.id;
   // Sharp IFC planes must not be shaded as rounded solids; underlying vertices unchanged.
   mesh.material.flatShading=true;group.add(mesh);meshes.push(mesh);
   const k=JSON.stringify(rgba);palette.set(k,(palette.get(k)||0)+1);
  }
  const box=exactBounds(group);record.parsedBoundsMetres=[box.min,box.max];record.triangles=item.faces.length;
  groups.set(item.id,group);triangles+=item.faces.length;
 }
 return {groups,meshes,palette,triangles,maxFloatErrorMetres};
}
