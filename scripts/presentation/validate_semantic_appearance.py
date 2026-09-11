"""Fresh offline four-template gallery from actual reopened IFC meshes.

This is deterministic regression/demo evidence, never accepted or live Proof.
Existing output directories are refused to preserve previous evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import ifcopenshell.geom
import ifcopenshell.util.element as element
import numpy as np

from text2ifc_compiler import compile_document, open_ifc
from text2ifc_compiler.basic_filling import verify_basic_filling
from text2ifc_compiler.semantic_verification import verify_document_semantics
from text2ifc_contract.basic_filling import VERSION, resolve_basic_filling
from text2ifc_presentation import item_appearance_signatures

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
    "window-single": "单面板窗", "window-double-vertical": "双竖面板窗",
    "door-left": "左单开门", "door-right": "右单开门",
}


def candidate(template):
    value = json.loads((ROOT / "tests/contract_v2/fixtures/complete.json").read_text(encoding="utf-8"))
    wanted = {"project-1", "site-1", "building-1", "storey-1", "wall-1", "opening-1", "door-1"}
    value["entities"] = [record for record in value["entities"] if record["id"] in wanted]
    records = {record["id"]: record for record in value["entities"]}
    value["schema_version"] = "bim-json/2.1"
    value["appearance"] = {"profile": "neutral-architectural", "seed": "offline-four-template-gallery"}
    for record in value["entities"]:
        record["property_sets"] = {}
        record["provenance"] = {"source": "deterministic offline gallery"}
    storey = records["storey-1"]["attributes"]
    storey["Elevation"] = 0
    storey["ObjectPlacement"]["origin"] = [0, 0, 0]
    records["wall-1"]["attributes"]["ObjectPlacement"]["origin"] = [0, 0, 0]
    records["wall-1"]["attributes"]["Representation"]["profile"]["x"] = 2600
    window = template.startswith("window")
    width, height = (1200, 1500) if window else (900, 2100)
    filling = records["door-1"]
    filling["ifc_class"] = "IfcWindow" if window else "IfcDoor"
    filling["attributes"].update(Name=TEMPLATES[template], OverallWidth=width, OverallHeight=height)
    filling["attributes"]["Representation"] = {
        "kind": "basic_filling", "template_id": template, "template_version": VERSION,
        "width": width, "height": height, "depth": 200, "parameters": {},
    }
    opening = records["opening-1"]["attributes"]
    opening["ObjectPlacement"]["origin"] = [0, 0, 900 if window else 0]
    opening["Representation"]["profile"]["x"] = width
    opening["Representation"]["depth"] = height
    return value


def _triangles(product, *, world=True):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, world)
    shape = ifcopenshell.geom.create_shape(settings, product)
    mesh = shape.geometry
    verts = np.array(mesh.verts).reshape(-1, 3)
    faces = np.array(mesh.faces).reshape(-1, 3)
    materials = list(mesh.materials)
    result = []
    for face, index in zip(faces, mesh.material_ids):
        style = materials[index] if 0 <= index < len(materials) else None
        diffuse = style.diffuse if style else None
        color = (diffuse.r(), diffuse.g(), diffuse.b()) if diffuse else (.72, .74, .73)
        alpha = 1.0 - (style.transparency if style and style.transparency == style.transparency else 0.)
        result.append((verts[face], color, alpha))
    return result


def render_svg(products, output, title):
    triangles = [triangle for product in products for triangle in _triangles(product)]
    # Fixed orthographic camera and white background; no aesthetic grading.
    right = np.array([1., .32, 0.])
    up = np.array([-.10, .30, 1.])
    depth = np.cross(right, up)
    projected = [np.column_stack((v @ right, -(v @ up))) for v, _, _ in triangles]
    all_points = np.concatenate(projected)
    low, high = all_points.min(axis=0), all_points.max(axis=0)
    scale = min(820 / (high[0]-low[0]), 580 / (high[1]-low[1]))
    content = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="760" viewBox="0 0 960 760">', '<rect width="960" height="760" fill="#f6f7f5"/>', f'<text x="40" y="40" font-family="sans-serif" font-size="22">{html.escape(title)}</text>']
    order = sorted(range(len(triangles)), key=lambda i: float(triangles[i][0].mean(axis=0) @ depth))
    for index in order:
        _, color, alpha = triangles[index]
        points = (projected[index]-low)*scale + [60, 90]
        rgb = ','.join(str(round(255*float(c))) for c in color)
        coords = ' '.join(f'{x:.2f},{y:.2f}' for x,y in points)
        content.append(f'<polygon points="{coords}" fill="rgb({rgb})" fill-opacity="{alpha:.3f}" stroke="rgb({rgb})" stroke-width="0.25"/>')
    content.append('<text x="40" y="725" font-family="sans-serif" font-size="15">Reopened IFC mesh · fixed orthographic view · offline · pending human review</text></svg>')
    output.write_text('\n'.join(content), encoding='utf-8')


def generate(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    summaries = []
    for template, label in TEMPLATES.items():
        directory = output / template
        directory.mkdir()
        (directory / "evidence").mkdir()
        value = candidate(template)
        record = next(r for r in value["entities"] if r["id"] == "door-1")
        rep = record["attributes"]["Representation"]
        request = f"生成{label}，宽{rep['width']}毫米、高{rep['height']}毫米，墙及开口深200毫米，默认协调风格；不指定材料和性能属性。\n"
        (directory / "request.txt").write_text(request, encoding="utf-8")
        (directory / "candidate.json").write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        result = compile_document(value, directory / "output.ifc")
        if not result.success:
            raise RuntimeError(f"{template}: {result.input_issues} {result.ifc_issues}")
        model = open_ifc(directory / "output.ifc")
        issues = verify_basic_filling(model, value) + verify_document_semantics(model, value)
        if issues:
            raise RuntimeError(str(issues))
        product = model.by_type(record["ifc_class"])[0]
        style = element.get_type(product)
        resolved = resolve_basic_filling(rep, record["ifc_class"])
        role_styles = {}
        for aspect in product.Representation.HasShapeAspects:
            role_styles[aspect.Name] = [signature for shape in aspect.ShapeRepresentations for item in shape.Items for signature in item_appearance_signatures(item)]
        evidence = {"status": "offline_passed", "human_review": "pending_human_review", "provider_calls": 0,
                    "template": resolved, "effective_type": style.OperationType if style else None,
                    "material_count": len(model.by_type("IfcMaterial")), "part_styles": role_styles,
                    "ifc_sha256": hashlib.sha256((directory / "output.ifc").read_bytes()).hexdigest(),
                    "render": "actual reopened IFC triangles; fixed orthographic projection; no artistic image generation"}
        (directory / "evidence/reopened.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        render_svg([model.by_type("IfcWall")[0], product], directory / "overall.svg", f"text2IFC · {label} · 整体")
        render_svg([product], directory / "closeup.svg", f"text2IFC · {label} · 部件近景")
        rows = [f"| {key} | {number} | {resolved['parameter_sources'][key]} |" for key,number in resolved["parameters"].items()]
        report = f"# {label}：离线语义与外观示例\n\n状态：离线自动检查通过；人工视觉审查待进行。不是真实 Provider 运行或 accepted Proof。\n\n{request}\n| 项目 | 请求 | IFC 重读结果 |\n|---|---|---|\n| 名义宽高 | {rep['width']} × {rep['height']} mm | {product.OverallWidth:g} × {product.OverallHeight:g} mm |\n| Type | 无共享要求 | {style.OperationType if style else '未创建'}；门为按实例创建的构造附件 |\n| 材料 | 未指定 | {evidence['material_count']} 个，不从颜色补写 |\n| 性能属性 | 未指定 | 未创建 |\n| 颜色 | 默认协调风格 | neutral-architectural；框与玻璃/门扇按部件分色 |\n| 几何 | 框与面板，开口保持 | 分部件重读网格、体积及尺寸检查通过 |\n\n模板：`{template}`，版本 `{VERSION}`。\n\n| 参数（长度 mm） | 有效值 | 来源 |\n|---|---:|---|\n" + '\n'.join(rows) + "\n\n[请求](request.txt) · [BIM JSON](candidate.json) · [IFC](output.ifc) · [独立检查记录](evidence/reopened.json)\n\n![整体](overall.svg)\n\n![近景](closeup.svg)\n\n图由最终重读 IFC 三角网格投影；固定相机、背景，不能代替实际 viewer 人工审查。\n"
        (directory / "REPORT.md").write_text(report, encoding="utf-8")
        summaries.append(f"- [{label}]({template}/REPORT.md)")
    (output / "REPORT.md").write_text("# text2IFC 基础门窗离线展示\n\n四种模板：自动语义、IFC2X3、网格与参数检查通过；人工视觉审查待进行。无 Provider 调用；没有安装 accepted Proof。\n\n" + '\n'.join(summaries) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(generate(args.output_dir))
