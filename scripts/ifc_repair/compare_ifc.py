"""Compare IFC files with official IfcDiff plus optional cross-GUID mappings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from text2ifc_ifc_repair.compare import (  # noqa: E402
    compare_ifc_with_ifcdiff,
    compare_mapped_elements,
)
from text2ifc_ifc_repair.occurrence_fidelity import (  # noqa: E402
    compare_window_occurrences,
)


def _mapping(value: str) -> dict[str, str]:
    parts = value.split(":", maxsplit=2)
    if len(parts) != 3 or not all(parts):
        raise argparse.ArgumentTypeError(
            "mapping must be ROLE:BEFORE_GLOBAL_ID:AFTER_GLOBAL_ID"
        )
    return {
        "role": parts[0],
        "before_global_id": parts[1],
        "after_global_id": parts[2],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare an original/before IFC with a repaired/after IFC and "
            "optionally emit mapped Window occurrence diagnostics."
        )
    )
    parser.add_argument("before", type=Path, help="Original or before IFC")
    parser.add_argument("after", type=Path, help="Repaired or after IFC")
    parser.add_argument("--output", type=Path, help="Full-model JSON output")
    parser.add_argument(
        "--window-mapping",
        type=Path,
        help=(
            "JSON mapping file with original_window_global_id, "
            "repaired_window_global_id, optional deleted_window_name, "
            "authorization_ledger and required_fact_keys"
        ),
    )
    parser.add_argument(
        "--occurrence-json-output",
        type=Path,
        help="Complete Window/Opening occurrence comparison JSON output",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Concise human-readable Window comparison Markdown output",
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help=(
            "Exit non-zero for semantic/geometry occurrence failure; "
            "authoring-only differences remain non-blocking"
        ),
    )
    parser.add_argument(
        "--mapping",
        action="append",
        default=[],
        type=_mapping,
        metavar="ROLE:BEFORE_GUID:AFTER_GUID",
    )
    parser.add_argument(
        "--relationship",
        action="append",
        dest="relationships",
        choices=(
            "attributes",
            "geometry",
            "type",
            "property",
            "container",
            "aggregate",
            "classification",
        ),
    )
    parser.add_argument("--shallow", action="store_true")
    parser.add_argument("--filter-elements")
    args = parser.parse_args()

    relationships = args.relationships or [
        "attributes",
        "geometry",
        "type",
        "property",
        "container",
        "aggregate",
        "classification",
    ]
    report = {
        "official_model_diff": compare_ifc_with_ifcdiff(
            args.before,
            args.after,
            relationships=relationships,
            is_shallow=args.shallow,
            filter_elements=args.filter_elements,
        ),
        "mapped_element_diff": (
            compare_mapped_elements(
                args.before,
                args.after,
                mappings=args.mapping,
            )
            if args.mapping
            else None
        ),
    }
    occurrence_report = None
    if args.window_mapping is not None:
        mappings = _load_window_mappings(args.window_mapping)
        occurrence_report = {
            "schema_version": "text2ifc/window-occurrence-comparison-set/0.1",
            "original_ifc": str(args.before.resolve()),
            "repaired_ifc": str(args.after.resolve()),
            "windows": [
                {
                    "deleted_window_name": item.get("deleted_window_name"),
                    "original_window_global_id": item[
                        "original_window_global_id"
                    ],
                    "repaired_window_global_id": item[
                        "repaired_window_global_id"
                    ],
                    "report": compare_window_occurrences(
                        args.before,
                        args.after,
                        original_window_global_id=item[
                            "original_window_global_id"
                        ],
                        repaired_window_global_id=item[
                            "repaired_window_global_id"
                        ],
                        authorization_ledger=item.get(
                            "authorization_ledger", ()
                        ),
                        required_fact_keys=item.get("required_fact_keys"),
                        complete_replication=bool(
                            item.get("complete_replication", True)
                        ),
                    ),
                }
                for item in mappings
            ],
        }
        report["occurrence_comparison"] = occurrence_report
    serialized = json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True
    )
    if args.output is None:
        print(serialized)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(
            json.dumps(
                {"status": "completed", "output": str(args.output.resolve())},
                ensure_ascii=False,
            )
        )
    if occurrence_report is not None:
        occurrence_json = (
            args.occurrence_json_output
            or (
                args.output.with_name(
                    f"{args.output.stem}-occurrence.json"
                )
                if args.output is not None
                else None
            )
        )
        if occurrence_json is not None:
            occurrence_json.parent.mkdir(parents=True, exist_ok=True)
            occurrence_json.write_text(
                json.dumps(
                    occurrence_report,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        if args.markdown_output is not None:
            args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_output.write_text(
                _occurrence_markdown(occurrence_report),
                encoding="utf-8",
            )
        if args.blocking and any(
            not item["report"]["occurrence_fidelity_success"]
            for item in occurrence_report["windows"]
        ):
            return 2
    return 0


def _load_window_mappings(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("windows") if isinstance(payload, dict) else payload
    if not isinstance(values, list) or not values:
        raise ValueError("WINDOW_MAPPING_LIST_REQUIRED")
    required = {
        "original_window_global_id",
        "repaired_window_global_id",
    }
    result = []
    seen_original: set[str] = set()
    seen_repaired: set[str] = set()
    for index, item in enumerate(values):
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError(f"WINDOW_MAPPING_INVALID:{index}")
        original = str(item["original_window_global_id"])
        repaired = str(item["repaired_window_global_id"])
        if original in seen_original or repaired in seen_repaired:
            raise ValueError(f"WINDOW_MAPPING_DUPLICATE:{index}")
        seen_original.add(original)
        seen_repaired.add(repaired)
        result.append({**item, **{
            "original_window_global_id": original,
            "repaired_window_global_id": repaired,
        }})
    return result


def _occurrence_markdown(report: dict) -> str:
    lines = [
        "# Window / Opening Occurrence Comparison",
        "",
        "| Deleted name | Original Window GUID | Repaired Window GUID | Facts | Matched | Missing text | Unsupported | Wrong | Ownership-only | Geometry | Semantic | Occurrence | Authoring exactness |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for item in report["windows"]:
        detail = item["report"]
        counts = detail["counts"]
        lines.append(
            "| {name} | `{original}` | `{repaired}` | {total} | {matched} | "
            "{missing} | {unsupported} | {wrong} | {ownership} | {geometry} | "
            "{semantic} | {occurrence} | {authoring} |".format(
                name=item.get("deleted_window_name") or "—",
                original=item["original_window_global_id"],
                repaired=item["repaired_window_global_id"],
                total=detail["detail_total"],
                matched=counts["matched"],
                missing=counts["not_in_user_text"],
                unsupported=counts["unsupported_authoring"],
                wrong=counts["wrong_value"],
                ownership=counts["ownership_only"],
                geometry=detail["geometry_relationship_success"],
                semantic=detail["semantic_fidelity_success"],
                occurrence=detail["occurrence_fidelity_success"],
                authoring=detail["authoring_exactness"],
            )
        )
    lines.extend(
        [
            "",
            "Status fields: `geometry_relationship_success`, "
            "`semantic_fidelity_success`, `occurrence_fidelity_success`, "
            "`authoring_exactness`.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
