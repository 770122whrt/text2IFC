"""Check presentation and copies, never re-curate or promote scientific evidence."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import ifcopenshell

SCHEMA = "text2ifc/workflow-human-proof/0.1"
EVIDENCE_ROOTS = (
    "dataset/processed/proof", "dataset/processed/ifc-repair",
    "dataset/processed/ifc-repair-runs", "dataset/processed/agent-demo",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def contained(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("expected a nonempty relative path")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes root: {relative}")
    return result


def evidence_path(repo: Path, relative: str, view: Path) -> Path:
    try:
        path = contained(repo, relative)
    except ValueError as exc:
        raise ValueError(f"authority: {exc}") from exc
    if not any(path.is_relative_to((repo / prefix).resolve()) for prefix in EVIDENCE_ROOTS):
        raise ValueError(f"authority outside allowed evidence roots: {relative}")
    if path.is_relative_to(view):
        raise ValueError("authority cannot be its own human view")
    if not path.exists():
        raise ValueError(f"authority missing: {relative}")
    return path


def validate_collection(collection: Path, repo: Path, *, reopen: bool = True) -> dict:
    collection, repo = collection.resolve(), repo.resolve()
    errors: list[str] = []
    opened = checked = 0
    digests: dict[Path, str] = {}
    def sha(path):
        if path not in digests:
            digests[path] = digest(path)
        return digests[path]
    try:
        if not collection.is_relative_to(repo / "dataset/processed/proof"):
            raise ValueError("collection outside repository Proof root")
        manifest = json.loads((collection / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("schema_version") != SCHEMA:
            raise ValueError("unsupported human-view schema")
        if manifest.get("workflow") not in {"repair", "generation"}:
            raise ValueError("unknown workflow")
        cases = manifest["cases"]
        if not isinstance(cases, list):
            raise ValueError("cases must be a list")
    except (OSError, ValueError, KeyError) as exc:
        return {"status": "failed", "errors": [str(exc)], "case_count": 0, "reopened_ifc_count": 0}
    for name in ("README.md", "REPORT.md"):
        if not (collection / name).is_file():
            errors.append(f"missing collection {name}")
    seen = set()
    for case in cases:
        case_id = case.get("case_id")
        try:
            if not case_id or case_id in seen:
                raise ValueError("missing or duplicate case id")
            seen.add(case_id)
            root = contained(collection, case["path"])
            if root == collection:
                raise ValueError("case requires its own directory")
            evidence_path(repo, case["authority"], collection)
            required = ["REPORT.md", "request.txt", "evidence/README.md"]
            artifacts = case["artifacts"]
            if manifest["workflow"] == "repair":
                required.append("02-damaged.ifc")
                if case["outcome"] == "no_output":
                    required.append("NO-REPAIR.md")
                    if any(p.name != "02-damaged.ifc" for p in root.glob("*.ifc")):
                        raise ValueError("no-output case contains extra IFC")
                elif case["outcome"] == "repaired":
                    required.append("03-repaired.ifc")
                    if (root / "NO-REPAIR.md").exists():
                        raise ValueError("repaired case contains NO-REPAIR.md")
                else:
                    raise ValueError("unknown repair outcome")
                if (root / "01-original.ifc").exists():
                    if case.get("original_role") not in {"private_ground_truth", "physical_fixture_non_private_audit"}:
                        raise ValueError("original role must be predeclared")
                    required.append("01-original.ifc")
            else:
                required += ["model.json", "generated.ifc"]
                if any((root / n).exists() for n in ("01-original.ifc", "02-damaged.ifc", "03-repaired.ifc", "NO-REPAIR.md")):
                    raise ValueError("generation must not present a repair triplet")
                json.loads((root / "model.json").read_text(encoding="utf-8"))
            for name in required:
                path = contained(root, name)
                if not path.is_file() or not path.stat().st_size:
                    raise ValueError(f"missing or empty {name}")
                if name in {"request.txt", "model.json"} or name.endswith(".ifc"):
                    if name not in artifacts:
                        raise ValueError(f"no authority binding for {name}")
            for name, relative in artifacts.items():
                path = contained(root, name)
                source = evidence_path(repo, relative["path"] if isinstance(relative, dict) else relative, collection)
                if isinstance(relative, dict):
                    value = json.loads(source.read_text(encoding="utf-8"))[relative["field"]]
                    if not isinstance(value, str):
                        raise ValueError("request projection must be a string")
                    same = path.is_file() and path.read_bytes() == value.encode("utf-8")
                else:
                    same = path.is_file() and source.is_file() and sha(path) == sha(source)
                if not same:
                    raise ValueError(f"copy mismatch: {name}")
                checked += 1
                if path.suffix.lower() == ".ifc" and reopen:
                    model = ifcopenshell.open(str(path))
                    if model.schema != "IFC2X3":
                        raise ValueError(f"IFC2X3 required: {name}")
                    del model
                    gc.collect()
                    opened += 1
            if manifest["status"] == "pending_human_review" and case["status"] != "pending_human_review":
                raise ValueError("review case cannot be promoted by presentation")
        except (OSError, ValueError, KeyError, RuntimeError, TypeError) as exc:
            errors.append(f"{case_id}: {exc}")
    return {"status": "failed" if errors else "passed", "collection_id": manifest["collection_id"],
            "case_count": len(cases), "reopened_ifc_count": opened, "checked_copy_count": checked,
            "scope": "human layout, authority reachability, byte equality and IFC reopen only", "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = validate_collection(args.root, args.repo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result["status"] != "passed"


if __name__ == "__main__":
    raise SystemExit(main())
