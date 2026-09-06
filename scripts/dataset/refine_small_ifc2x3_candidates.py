"""Refine semantically meaningful IFC2X3 candidates for main-dataset suitability."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / ".tmp/dataset-acquisition/ifc2x3-small-github-classified.jsonl"
OUTPUT = ROOT / "dataset/manifests/acquisitions/ifc2x3-small-github-refined.jsonl"
REPORT = ROOT / "docs/reports/ifc2x3-small-model-refined-shortlist.md"

NEGATIVE_HINTS = re.compile(
    r"(?:^|/)(?:tests?|tickets?|issues?|bugs?)(?:/|$)|"
    r"wrong[-_ ]geometry|invalid|malformed|segfault|abort|crash|doubleguid|"
    r"japanesechars|unicode|sjis|error|fail(?:ure)?|broken|regression",
    re.I,
)

POSITIVE_HINTS = re.compile(
    r"(?:^|/)(?:examples?|samples?|models?|data)(?:/|$)|"
    r"openhouse|duplex|house|office|project|building|roof|school|clinic|institute|sample",
    re.I,
)


def main() -> int:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    eligible = [
        row for row in rows
        if row.get("status") == "new_candidate"
        and row.get("meaningfulness") in {"meaningful_model", "discipline_model"}
    ]

    by_sha: dict[str, list[dict]] = defaultdict(list)
    for row in eligible:
        by_sha[str(row["sha256"])].append(row)

    refined: list[dict] = []
    for sha, group in by_sha.items():
        group = sorted(group, key=lambda row: (row["size_bytes"], row["repo"], row["path"].casefold()))
        representatives = []
        for row in group:
            combined = f"{row['repo']}/{row['path']}"
            fixture_risk = bool(NEGATIVE_HINTS.search(combined))
            positive_hint = bool(POSITIVE_HINTS.search(combined))
            metrics = row.get("metrics") or {}
            generation_suitable = bool(
                row.get("generation_reference_candidate")
                and not fixture_risk
                and metrics.get("element_count", 0) >= 15
                and metrics.get("key_class_diversity", 0) >= 4
            )
            regression_repo = row.get("repo") == "IfcOpenShell/files"
            main_dataset_suitable = bool(
                not fixture_risk
                and not regression_repo
                and row.get("meaningfulness") in {"meaningful_model", "discipline_model"}
                and metrics.get("element_count", 0) >= 10
                and metrics.get("project_count", 0) >= 1
                and metrics.get("storey_count", 0) >= 1
                and metrics.get("containment_rel_count", 0) >= 1
                and metrics.get("key_class_diversity", 0) >= 2
            )
            enriched = {
                **row,
                "fixture_risk": fixture_risk,
                "positive_model_hint": positive_hint,
                "main_dataset_suitable": main_dataset_suitable,
                "generation_reference_suitable": generation_suitable,
            }
            representatives.append(enriched)

        preferred = sorted(
            representatives,
            key=lambda row: (
                not row["main_dataset_suitable"],
                not row["positive_model_hint"],
                row["fixture_risk"],
                row["repo"],
                row["path"].casefold(),
            ),
        )[0]
        aliases = [f"{row['repo']}:{row['path']}" for row in representatives if row is not preferred]
        preferred["candidate_sha_aliases"] = aliases
        preferred["candidate_exact_duplicate_count"] = len(group) - 1
        refined.append(preferred)

    refined.sort(
        key=lambda row: (
            not row["main_dataset_suitable"],
            not row["generation_reference_suitable"],
            row["size_bytes"],
            row["repo"],
            row["path"].casefold(),
        )
    )
    main = [row for row in refined if row["main_dataset_suitable"]]
    generation = [row for row in main if row["generation_reference_suitable"]]
    repair = [row for row in main if not row["generation_reference_suitable"]]

    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in main),
        encoding="utf-8",
    )

    lines = [
        "# IFC2X3 Small Model Refined Shortlist",
        "",
        "> Main-dataset shortlist after IfcOpenShell semantic screening, candidate-to-candidate SHA deduplication, and fixture-risk filtering.",
        "",
        f"- Unique meaningful/discipline SHA candidates: **{len(refined)}**",
        f"- Main-dataset suitable: **{len(main)}**",
        f"- `<1 MiB` Generation-reference suitable: **{len(generation)}**",
        f"- Other Repair-oriented suitable candidates: **{len(repair)}**",
        "- Machine-readable shortlist: `dataset/manifests/acquisitions/ifc2x3-small-github-refined.jsonl`",
        "",
        "## Generation-reference shortlist",
        "",
        "| Size (MiB) | Elements | Storeys | Classes | Repository | Path | SHA aliases |",
        "| ---: | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for row in generation:
        m = row["metrics"]
        lines.append(
            f"| {row['size_mib']:.3f} | {m['element_count']} | {m['storey_count']} | {m['key_class_diversity']} | `{row['repo']}` | `{row['path']}` | {row['candidate_exact_duplicate_count']} |"
        )

    lines += [
        "",
        "## Other main-dataset candidates",
        "",
        "| Size (MiB) | Type | Elements | Storeys | Classes | Repository | Path |",
        "| ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in repair:
        m = row["metrics"]
        lines.append(
            f"| {row['size_mib']:.3f} | `{row['meaningfulness']}` | {m['element_count']} | {m['storey_count']} | {m['key_class_diversity']} | `{row['repo']}` | `{row['path']}` |"
        )

    lines += [
        "",
        "## Excluded from main dataset",
        "",
        "Candidates classified as single-component, fragment, metadata-only, invalid, obvious bug/ticket/encoding fixtures, or exact candidate duplicates remain discovery evidence only.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "unique_meaningful_sha": len(refined),
        "main_dataset_suitable": len(main),
        "generation_reference_suitable": len(generation),
        "repair_oriented_suitable": len(repair),
        "candidate_duplicate_aliases": sum(row["candidate_exact_duplicate_count"] for row in refined),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
