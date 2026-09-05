"""Build a Markdown size index for canonical IFC2X3 source files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES_PATH = ROOT / "dataset/manifests/ifc-files.jsonl"
OUTPUT_PATH = ROOT / "docs/reports/ifc2x3-dataset-size-index.md"
MIB = 1024 * 1024

BINS = (
    ("G0 / Generation reference (<1 MiB)", 0, 1),
    ("R1 / Small (1–3 MiB)", 1, 3),
    ("R2 / Compact (3–10 MiB)", 3, 10),
    ("R3 / Normal (10–30 MiB)", 10, 30),
    ("S1 / Stress-medium (30–60 MiB)", 30, 60),
    ("S2 / Stress-heavy (60–100 MiB)", 60, 100),
    ("Approved >100 MiB", 100, float("inf")),
)


def load_ifc2x3() -> list[dict]:
    rows: list[dict] = []
    for line in FILES_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("declared_schema") == "IFC2X3":
            rows.append(row)
    return rows


def main() -> int:
    rows = load_ifc2x3()
    lines = [
        "# IFC2X3 Dataset Size Index",
        "",
        "> Physical storage remains organized by source under `dataset/external/`. This document is only a size-oriented index; it does not move or duplicate IFC files.",
        "",
        "## Current certified inventory",
        "",
        f"- Canonical IFC2X3: **{len(rows)}**",
        f"- `<1 MiB`: **{sum(row['size_bytes'] < MIB for row in rows)}**",
        f"- `<3 MiB`: **{sum(row['size_bytes'] < 3 * MIB for row in rows)}**",
        f"- `<10 MiB`: **{sum(row['size_bytes'] < 10 * MIB for row in rows)}**",
        "- Technical admission authority: `dataset/manifests/ifc2x3-certified.jsonl`",
        "- Canonical file authority: `dataset/manifests/ifc-files.jsonl`",
        "",
        "## Size classes",
        "",
    ]

    for title, lower_mib, upper_mib in BINS:
        subset = sorted(
            (
                row
                for row in rows
                if lower_mib * MIB <= row["size_bytes"] < upper_mib * MIB
            ),
            key=lambda row: (row["size_bytes"], row["local_path"].casefold()),
        )
        lines.extend(
            [
                f"### {title}",
                "",
                f"Count: **{len(subset)}**",
                "",
                "| Size (MiB) | Source | Relative path |",
                "| ---: | --- | --- |",
            ]
        )
        for row in subset:
            lines.append(
                f"| {row['size_bytes'] / MIB:.3f} | `{row['source_id']}` | `{row['local_path']}` |"
            )
        lines.append("")

    lines.extend(
        [
            "## Usage guidance",
            "",
            "- `<1 MiB`: highest-priority Generation reference candidates; also useful for fast Repair cases.",
            "- `1–10 MiB`: primary Repair benchmark pool.",
            "- `10–30 MiB`: secondary Repair complexity pool.",
            "- `30–100 MiB`: stress/performance pool; do not preferentially expand this range.",
            "- `>100 MiB`: retain only after explicit human review. Currently approved exceptions remain in the source-organized dataset.",
            "",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT_PATH.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
