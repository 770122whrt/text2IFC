"""Verify Phase 6.1 final live acceptance artifacts."""

from __future__ import annotations

import argparse
import json
import site
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))
USER_SITE = Path(site.getusersitepackages())
try:
    user_site_exists = USER_SITE.exists()
except OSError:
    user_site_exists = False
if user_site_exists or str(USER_SITE) not in sys.path:
    sys.path.append(str(USER_SITE))

import ifcopenshell  # noqa: E402

DEFAULT_ROOT = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "phase6.1-mimo-live"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    result = verify(args.root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


def verify(root: Path) -> dict[str, object]:
    required = {
        "output_ifc": root / "output.ifc",
        "report": root / "report.md",
        "acceptance_metrics": root / "acceptance-metrics.json",
        "geometry_feedback": root / "geometry-feedback.json",
        "ifc_verification": root / "ifc-verification.json",
        "secret_scan": root / "secret-scan.json",
    }
    missing = [
        name for name, path in required.items()
        if not path.is_file()
    ]
    metrics = _read_json(required["acceptance_metrics"]) if not missing else {}
    geometry = _read_json(required["geometry_feedback"]) if not missing else {}
    ifc_verification = _read_json(required["ifc_verification"]) if not missing else {}
    secret_scan = _read_json(required["secret_scan"]) if not missing else {}
    report_text = (
        required["report"].read_text(encoding="utf-8")
        if required["report"].is_file()
        else ""
    )
    output_ifc_reopenable = False
    if required["output_ifc"].is_file():
        try:
            model = ifcopenshell.open(str(required["output_ifc"]))
            output_ifc_reopenable = model.schema == "IFC2X3"
        except Exception:
            output_ifc_reopenable = False
    report_links_final_ifc = "output.ifc" in report_text
    result = {
        "valid": bool(
            not missing
            and output_ifc_reopenable
            and metrics.get("valid") is True
            and metrics.get("compile_reopen_success") is True
            and metrics.get("geometry_success") is True
            and geometry.get("success") is True
            and ifc_verification.get("success") is True
            and secret_scan.get("finding_count") == 0
            and report_links_final_ifc
        ),
        "missing": missing,
        "output_ifc_reopenable": output_ifc_reopenable,
        "geometry_success": geometry.get("success") is True,
        "compile_reopen_success": ifc_verification.get("success") is True,
        "secret_finding_count": secret_scan.get("finding_count"),
        "report_links_final_ifc": report_links_final_ifc,
        "root": str(root),
    }
    return result


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
