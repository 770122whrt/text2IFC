"""Reconstruct a frozen bundle for its original validator, without changing Proof.

Example: python scripts/proof/materialize_frozen_bundle.py --root <collection>
         --bundle frozen --destination .tmp/r1-frozen
Then pass that destination to the applicable original offline validator.
The destination must not exist; this command never deletes files.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from scripts.proof.package import materialize_bundle, SCHEMA
except ModuleNotFoundError:
    from package import materialize_bundle, SCHEMA


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads((args.root / "manifest.json").read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA:
        parser.error("expected a consolidated package")
    bundles = [b for b in document["legacy_bundles"] if b["id"] == args.bundle]
    if len(bundles) != 1:
        parser.error("bundle id must resolve exactly once")
    materialize_bundle(args.root, bundles[0], args.destination)
    print(json.dumps({"status": "materialized", "files": len(bundles[0]["entries"]),
                      "destination": str(args.destination.resolve()),
                      "validation": "not run; use the original frozen validator"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
