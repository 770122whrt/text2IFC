"""Render the exact native mesh arrays, using VTK offscreen. No geometry reconstruction.
Colours come from native IFC surface materials; only camera, light and display styling vary.
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'.python'))
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray


def render_model(folder:Path,width=1396,height=1057,edge=False):
    report=json.loads((folder/'native-report.json').read_text(encoding='utf8'))
    data=np.load(folder/'meshes.npz',allow_pickle=False)
    renderer=vtk.vtkRenderer();renderer.SetBackground(.87,.90,.92);renderer.SetBackground2(.63,.69,.73);renderer.GradientBackgroundOn()
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(width,height);win.SetMultiSamples(0);win.SetAlphaBitPlanes(1);win.AddRenderer(renderer)
    renderer.SetUseDepthPeeling(1);renderer.SetMaximumNumberOfPeels(100);renderer.SetOcclusionRatio(0.0)
    actor_count=0; points_world=[]
    for rec in report['products']:
        key=str(rec['id']);verts=data[key+'_v'];faces=data[key+'_f'];mids=data[key+'_m'];points_world.append(verts)
        for mi in np.unique(mids):
            ff=faces[mids==mi];pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(verts,deep=True))
            cells=vtk.vtkCellArray();packed=np.column_stack((np.full(len(ff),3),ff)).ravel().astype(np.int64)
            cells.SetCells(len(ff),numpy_to_vtkIdTypeArray(packed,deep=True));poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
            normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(45);normals.SplittingOn();normals.ConsistencyOn();normals.AutoOrientNormalsOff()
            mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort());mapper.ScalarVisibilityOff()
            actor=vtk.vtkActor();actor.SetMapper(mapper)
            rgba=rec['materials'][int(mi)]['rgba'] if 0<=mi<len(rec['materials']) else [.7,.7,.7,1]
            prop=actor.GetProperty();prop.SetColor(*rgba[:3]);prop.SetOpacity(rgba[3]);prop.SetAmbient(.38);prop.SetDiffuse(.62);prop.SetSpecular(0);prop.SetInterpolationToPhong()
            renderer.AddActor(actor);actor_count+=1
            if edge:
                edges=vtk.vtkFeatureEdges();edges.SetInputData(poly);edges.BoundaryEdgesOn();edges.FeatureEdgesOn();edges.NonManifoldEdgesOff();edges.ManifoldEdgesOff();edges.SetFeatureAngle(45);edges.ColoringOff()
                em=vtk.vtkPolyDataMapper();em.SetInputConnection(edges.GetOutputPort());em.ScalarVisibilityOff();em.SetResolveCoincidentTopologyToPolygonOffset()
                ea=vtk.vtkActor();ea.SetMapper(em);ea.GetProperty().SetColor(.27,.28,.29);ea.GetProperty().SetOpacity(.2*rgba[3]);ea.GetProperty().SetLineWidth(.6);renderer.AddActor(ea)
    points=np.concatenate(points_world);bmin=points.min(0);bmax=points.max(0);center=(bmin+bmax)/2;distance=np.linalg.norm(bmax-bmin)*3
    camera=renderer.GetActiveCamera();camera.ParallelProjectionOn()
    # Camera only: front has a small downward pitch; side direction is estimated
    # from the two families of parallel roof edges in the supplied screenshot.
    views={'front':(1,0,.094),'side':(.374,-1,.214),'opposite-side':(1,1.05,.55),'back':(-1,0,.1)}
    shots={}
    for name,direction in views.items():
        width,height=(1276,736) if name=='front' else (1396,1057)
        win.SetSize(width,height)
        d=np.asarray(direction,float);d/=np.linalg.norm(d);up=np.array([0,0,1.]);right=np.cross(-d,up);right/=np.linalg.norm(right);vertical=np.cross(right,-d)
        xx=points@right;yy=points@vertical
        focal=center+right*((xx.min()+xx.max())/2-center@right)+vertical*((yy.min()+yy.max())/2-center@vertical)
        camera.SetFocalPoint(*focal);camera.SetPosition(*(focal+d*distance));camera.SetViewUp(*up);camera.SetParallelScale(max(np.ptp(yy)/2,np.ptp(xx)*height/width/2)*1.12);renderer.ResetCameraClippingRange()
        light=vtk.vtkLight();light.SetLightTypeToHeadlight();light.SetIntensity(1);renderer.RemoveAllLights();renderer.AddLight(light)
        win.Render()
        capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
        target=folder/f'{name}{"-edges" if edge else ""}.png';writer=vtk.vtkPNGWriter();writer.SetFileName(str(target));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
        shots[name]={'file':target.name,'camera_position':list(camera.GetPosition()),'focal_point':list(camera.GetFocalPoint()),'parallel_scale':camera.GetParallelScale(),'pixel_size':[width,height],'bytes':target.stat().st_size}
    result={'renderer':win.GetClassName(),'vtk':vtk.vtkVersion.GetVTKVersion(),'actors':actor_count,'source_products':len(report['products']),'source_vertices_modified':False,'edge_overlay':edge,'shots':shots,'depth_peeling_used':bool(renderer.GetLastRenderingUsedDepthPeeling())}
    (folder/f'rendering{"-edges" if edge else ""}.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2));win.Finalize()
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--edges',action='store_true');p.add_argument('--width',type=int,default=1396);p.add_argument('--height',type=int,default=1057);a=p.parse_args();render_model(a.folder,a.width,a.height,a.edges)
