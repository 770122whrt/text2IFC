"""Fetch verified IFC2X3 support artifacts into the ignored local cache."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_knowledge.sources import (  # noqa: E402
    download_source,
    inspect_zip_archive,
    load_source_manifest,
    verify_source_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all",
        action="store_true",
        help="also fetch support artifacts not required for registry generation",
    )
    args = parser.parse_args()

    manifest = load_source_manifest(
        ROOT / "schemas" / "ifc" / "IFC2X3_TC1.sources.json"
    )
    selected = [
        source
        for source in manifest.sources
        if source.cache_path and (args.all or source.required_for_generation)
    ]
    for source in selected:
        destination = ROOT / source.cache_path
        if destination.exists():
            verify_source_file(destination, source)
            state = "verified"
        else:
            destination = download_source(source, ROOT)
            state = "downloaded"
        if destination.suffix.lower() == ".zip":
            members = inspect_zip_archive(destination)
            print(f"{state}: {source.id} ({len(members)} archive entries)")
        else:
            print(f"{state}: {source.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
