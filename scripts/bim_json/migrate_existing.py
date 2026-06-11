import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_contract.migration import audit_existing_models


def main() -> int:
    source_root = ROOT / "dataset" / "processed"
    output_root = source_root / "bim-json-1.0"
    report = audit_existing_models(source_root, output_root)
    summary = report["summary"]
    print(
        "Migration audit complete: "
        f"{summary['total']} total, "
        f"{summary['converted']} converted, "
        f"{summary['rejected']} rejected."
    )
    print(f"Audit: {output_root / 'migration-audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
