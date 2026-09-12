"""Read-only review views from the final IFC; no added geometry or recolouring."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.presentation.render_ifc_review import render


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ifc", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--image-python", required=True)
    args = parser.parse_args()
    before = hashlib.sha256(args.ifc.read_bytes()).hexdigest()
    args.output.mkdir(exist_ok=False)
    render(args.ifc, args.output / "viewer.html")
    page = (args.output / "viewer.html").read_text(encoding="utf-8")
    payload = json.loads(page.split("<script>const data=", 1)[1].split(";const canvas=", 1)[0])
    assert not payload["mesh_failures"], payload["mesh_failures"]
    products = payload["products"]
    roof = lambda p: p["kind"] in {"IfcSlab", "IfcRoof"} and min(p["verts"][2::3]) >= 6.99
    views = {
        "overall": (products, "全部可网格化实体；使用源 IFC 的材料颜色和透明度。", False),
        "courtyard-roof-hidden": (
            [p for p in products if not roof(p)],
            "仅在此视图隐藏屋盖，显示真实光庭、二层回廊及栏板；IFC 文件未修改。", False),
        "upper-floor-plan": (
            [p for p in products if min(p["verts"][2::3]) >= 3.39 and not roof(p)],
            "二层俯视；隐藏屋盖及起点低于二层楼板底的构件，非新增几何。", True),
        "ground-floor-plan": (
            [p for p in products if min(p["verts"][2::3]) < 3.39],
            "首层俯视；隐藏二层和屋盖，保留实际楼梯。", True),
    }
    for kind in ("IfcWindow", "IfcDoor", "IfcRailing"):
        selected = [p for p in products if p["kind"] == kind]
        if selected:
            views[kind] = (selected[:1], "隔离一个真实构件；保留原始几何及 IFC 样式。", False)
    renderer = ROOT / "dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909/render_png.py"
    records = []
    for name, (items, note, plan) in views.items():
        assert items, name
        mesh = args.output / (name + "-mesh.json")
        mesh.write_text(json.dumps({**payload, "products": items, "view_note": note}, ensure_ascii=False), encoding="utf-8")
        extra = ["--pitch", "1.57079632679", "--yaw", "0"] if plan else []
        subprocess.run([args.image_python, str(renderer), str(mesh), str(args.output / (name + ".png")), *extra], check=True)
        records.append({"view": name, "note": note, "products": len(items)})
    assert before == hashlib.sha256(args.ifc.read_bytes()).hexdigest()
    (args.output / "views.json").write_text(json.dumps({"ifc_sha256": before, "mesh_failures": [], "views": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
