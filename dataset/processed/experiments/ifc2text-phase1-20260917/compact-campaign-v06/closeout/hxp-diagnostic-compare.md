# IFC2Text 诊断比较 v0.1

候选IFC为真实Provider生成并编译后的诊断产物，Generation未通过最终接受；本报告不将文件可打开等同于重建一致。

## 汇总

{"extra": 0, "geometric_deviations": 12, "matched": 66, "material_content_differences": 5, "material_metadata_differences": 41, "missing": 0, "relation_differences": 3}

三条楼层记录均匹配，标高偏差为0。全部66个已支持类别对象获得一对一几何匹配；无缺失/多余，但仍有几何、材料和关系差异。

## 主要差异

### doors
- D001→D001: center Δ=0.0 mm; geometry_outside=True; material_content_diff=False
- D002→D002: center Δ=0.1 mm; geometry_outside=True; material_content_diff=False
- D003→D003: center Δ=0.1 mm; geometry_outside=False; material_content_diff=True
- D004→D004: center Δ=0.0 mm; geometry_outside=True; material_content_diff=True
- D005→D005: center Δ=0.0 mm; geometry_outside=True; material_content_diff=True
- D006→D006: center Δ=0.1 mm; geometry_outside=False; material_content_diff=True
- D007→D007: center Δ=35.6 mm; geometry_outside=True; material_content_diff=True

### openings
- O003→O003: center Δ=0.1 mm; geometry_outside=True; material_content_diff=False

### walls
- W011→W011: center Δ=38.9 mm; geometry_outside=True; material_content_diff=False
- W013→W013: center Δ=49.5 mm; geometry_outside=True; material_content_diff=False
- W015→W015: center Δ=40.8 mm; geometry_outside=True; material_content_diff=False

### windows
- N001→N001: center Δ=0.0 mm; geometry_outside=True; material_content_diff=False
- N002→N002: center Δ=0.1 mm; geometry_outside=True; material_content_diff=False
- N003→N003: center Δ=20.0 mm; geometry_outside=True; material_content_diff=False

## 关系差异

- N001 storey: S02 → S01
- N002 storey: S02 → S01
- N003 storey: S02 → S01

## 未评估与限制

未评估字段记录：34 条。主要来自重建墙体测量方法与源模型不同，不能把未知值当作零误差。

- Equal local assignment costs are flagged, not a proof of globally unique identity.
- Material-content equality excludes reference metadata; it does not prove equal physical layer orientation.
- Projection and bounds do not establish exact 3D shape or traversability.
- A corrected comparison is an evaluator change, not a change or improvement of the reconstructed IFC.
