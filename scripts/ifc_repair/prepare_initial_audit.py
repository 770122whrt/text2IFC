"""Explicit bounded audit inputs; does not generate or inspect full IFC bodies."""
from __future__ import annotations

import json
from pathlib import Path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--versions", nargs="+", default=["v1", "v2"])
    parser.add_argument("--output", type=Path, default=Path(".tmp/ifc-initial-audit-inputs.json"))
    args = parser.parse_args()
    output = args.output
    rows = []
    for version in args.versions:
        root = Path(".tmp/ifc-dataset-prototype-" + version)
        for case in sorted(root.glob("sources/*/cases/case-*/case.json")):
            rows.append({"case_folder": str(case.parent.resolve()), "case_id": version + "/" + case.parent.parent.parent.name + "/" + case.parent.name})
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input_file": str(output), "cases": len(rows)}))
