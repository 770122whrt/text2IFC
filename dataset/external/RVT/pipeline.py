"""Local RVT acquisition/conversion checks. No source rewrite or automatic admission.

Run with the repository Python 3.12+ environment. All data stays next to this file.
Each conversion attempt gets a new directory; canonical IFC manifests are untouched.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time
import zipfile

BASE = Path(__file__).resolve().parent
MAX_MEMBER_BYTES = 512 * 1024 * 1024


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_new_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")


def safe_target(root: Path, name: str) -> Path:
    name = name.replace("\\", "/")
    parts = PurePosixPath(name).parts
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if (not parts or name.startswith("/") or ":" in name or
            any(p in {".", ".."} or p.endswith((".", " ")) or
                p.split(".")[0].upper() in reserved or
                any(ord(c) < 32 or c in '<>"|?*' for c in p) for p in parts)):
        raise ValueError(f"UNSAFE_MEMBER:{name}")
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"UNSAFE_TARGET:{name}")
    return target


def extract_handoff(base: Path = BASE) -> dict:
    """Validate all package bytes and destinations first; copy without overwriting."""
    base = base.resolve()
    with zipfile.ZipFile(base / "Text2IFC_RVT86_Handoff_Metadata_20260911.zip") as z:
        if z.testzip():
            raise ValueError("METADATA_CRC_FAILURE")
        assets = json.loads(z.read("02_METADATA/RVT_manifest_86_enriched.json"))
        parts = json.loads(z.read("02_METADATA/PARTS_MANIFEST.json"))
        original = json.loads(z.read("02_METADATA/RVT_inventory_86_original.json"))["unique_rvts"]
        dependencies = json.loads(z.read("02_METADATA/crosssource_dependency_manifest.json"))
        metadata_members = [(i, z.read(i)) for i in z.infolist() if not i.is_dir()]
    by_path = {r["package_path"]: r for r in assets}
    if len(by_path) != len(assets) or len({r["sha256"] for r in assets}) != len(assets):
        raise ValueError("DUPLICATE_METADATA_IDENTITY")
    old_by_hash = {r["sha256"]: r for r in original}
    for row in assets:
        previous = old_by_hash.get(row["sha256"])
        if previous is None or any(previous.get(k) != row.get(k) for k in ("inventory_id", "size_bytes", "filename", "source_name")):
            raise ValueError(f"ORIGINAL_METADATA_CONFLICT:{row['inventory_id']}")
    operations = []
    archive_checks = []
    path_keys = set()
    found = set()
    for part in parts["part_files"]:
        archive = safe_target(base, part["filename"])
        if archive.stat().st_size != part["bytes"] or sha256(archive) != part["sha256"]:
            raise ValueError(f"ARCHIVE_HASH_MISMATCH:{archive.name}")
        archive_checks.append({"archive": archive.name, "sha256": part["sha256"], "bytes": part["bytes"]})
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                target = safe_target(base / "extracted", info.filename)
                key = str(target).casefold()
                if key in path_keys or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError(f"UNSAFE_DUPLICATE_OR_LINK:{info.filename}")
                path_keys.add(key)
                if info.file_size > MAX_MEMBER_BYTES:
                    raise ValueError(f"MEMBER_TOO_LARGE:{info.filename}")
                row = by_path.get(info.filename)
                if row is None:
                    raise ValueError(f"UNREGISTERED_MEMBER:{info.filename}")
                with z.open(info) as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if (digest, info.file_size) != (row["sha256"], row["size_bytes"]):
                    raise ValueError(f"RVT_HASH_MISMATCH:{info.filename}")
                if target.exists() and sha256(target) != digest:
                    raise ValueError(f"EXISTING_FILE_CONFLICT:{target}")
                operations.append((archive, info.filename, target, digest))
                found.add(info.filename)
    if found != set(by_path) or len(found) != parts["total_rvt_entries"]:
        raise ValueError("RVT_INVENTORY_INCOMPLETE")
    # Validate metadata destinations too before the first write.
    for info, data in metadata_members:
        target = safe_target(base / "metadata", info.filename)
        if target.exists() and target.read_bytes() != data:
            raise ValueError(f"EXISTING_METADATA_CONFLICT:{target}")
    for archive, member, target, digest in operations:
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z, z.open(member) as src, target.open("xb") as dst:
            while block := src.read(1024 * 1024):
                dst.write(block)
        if sha256(target) != digest:
            raise ValueError(f"EXTRACTED_HASH_MISMATCH:{target}")
    for info, data in metadata_members:
        target = safe_target(base / "metadata", info.filename)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as dst:
                dst.write(data)
    result_assets = []
    for row in assets:
        previous = old_by_hash[row["sha256"]]
        aid = previous.get("asset_id")
        deps = []
        for dep in dependencies:
            if dep["host_asset_id"] != aid:
                continue
            matches = [r for r in assets if r["filename"] == dep["filename"]]
            deps.append({**dep, "host_inventory_id": row["inventory_id"],
                         "current_host_path": "extracted/" + row["package_path"],
                         "matching_inventory_ids": [r["inventory_id"] for r in matches],
                         "presence": "present_runtime_unverified" if len(matches) == 1 else "missing_or_ambiguous"})
        result_assets.append({**row, "legacy_asset_id": aid, "local_path": "extracted/" + row["package_path"],
                              "dependencies": deps, "conversion_status": "not_run",
                              "building_family_status": "needs_grouping_not_independent_by_default"})
    return {"schema_version": "rvt-local-inventory/1.0", "archives": archive_checks,
            "unique_rvt_count": len(assets), "total_rvt_bytes": sum(r["size_bytes"] for r in assets),
            "assets": result_assets}


def validate_ifc(path: Path, *, geometry: bool = True) -> dict:
    """Strict native checks plus all represented products, never a rights grant."""
    import ifcopenshell
    import ifcopenshell.validate
    import ifcopenshell.geom
    result = {"file": str(path.resolve()), "sha256": sha256(path), "bytes": path.stat().st_size,
              "ifcopenshell_version": ifcopenshell.version, "technical_candidate": False,
              "validation_scope": "native_schema_express_and_all_represented_products",
              "blockers": [], "rights_admission": "separate", "rvt_fidelity": "not_verified"}
    with path.open("rb") as stream:
        if b"ISO-10303-21;" not in stream.read(256):
            result["blockers"].append("INVALID_STEP_HEADER")
            return result
    try:
        logger = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(str(path), logger, express_rules=True)
        result["native_findings"] = logger.statements
        result["native_error_count"] = sum(s.get("level") == "error" for s in logger.statements)
        if result["native_error_count"]:
            result["blockers"].append("NATIVE_SCHEMA_OR_EXPRESS_ERRORS")
        f = ifcopenshell.open(path)
        result["schema"] = f.schema
        if f.schema != "IFC2X3":
            result["blockers"].append("NOT_IFC2X3")
        result["entity_count"] = sum(1 for _ in f)
        result["counts"] = {t: len(f.by_type(t)) for t in ("IfcProject", "IfcBuilding", "IfcBuildingStorey", "IfcElement", "IfcWall", "IfcSlab", "IfcRoof", "IfcDoor", "IfcWindow", "IfcPropertySet", "IfcElementQuantity", "IfcMaterial")}
        bodies = [p for p in f.by_type("IfcElement") if p.Representation and not p.is_a("IfcFeatureElement") and any(r.RepresentationIdentifier == "Body" for r in p.Representation.Representations)]
        result["building_body_elements"] = len(bodies)
        if not bodies or not f.by_type("IfcBuilding"):
            result["blockers"].append("NO_BUILDING_BODY")
        if len(f.by_type("IfcProject")) != 1:
            result["blockers"].append("PROJECT_COUNT")
        represented = [p for p in f.by_type("IfcProduct") if p.Representation and any(r.Items for r in p.Representation.Representations)]
        geometry_rows = []
        if geometry:
            settings = ifcopenshell.geom.settings()
            settings.set("use-world-coords", True)
            settings.set("dimensionality", ifcopenshell.ifcopenshell_wrapper.CURVES_SURFACES_AND_SOLIDS)
            for product in represented:
                entry = {"id": product.id(), "guid": product.GlobalId, "type": product.is_a()}
                try:
                    shape = ifcopenshell.geom.create_shape(settings, product)
                    verts = list(shape.geometry.verts)
                    import math
                    if not verts or not all(math.isfinite(v) for v in verts):
                        raise ValueError("EMPTY_OR_NONFINITE_GEOMETRY")
                    entry.update(vertices=len(verts) // 3, triangles=len(shape.geometry.faces) // 3, edges=len(shape.geometry.edges) // 2,
                                 bounds=[[min(verts[i::3]), max(verts[i::3])] for i in range(3)], passed=True)
                except Exception as exc:
                    entry.update(passed=False, error=str(exc))
                geometry_rows.append(entry)
            if any(not r["passed"] for r in geometry_rows):
                result["blockers"].append("GEOMETRY_FAILURES")
        else:
            result["blockers"].append("GEOMETRY_NOT_RUN")
        result["geometry"] = {"represented_products": len(represented), "checked": len(geometry_rows),
                              "failed": sum(not r["passed"] for r in geometry_rows), "products": geometry_rows}
        reopened = ifcopenshell.file.from_string(f.to_string())
        result["memory_roundtrip_reopen"] = reopened.schema == f.schema and sum(1 for _ in reopened) == result["entity_count"]
        if not result["memory_roundtrip_reopen"]:
            result["blockers"].append("ROUNDTRIP_FAILED")
        result["technical_candidate"] = not result["blockers"]
    except Exception as exc:
        result["blockers"].append("VALIDATION_EXCEPTION")
        result["exception"] = f"{type(exc).__name__}: {exc}"
    return result


def conversion_blocker(row: dict, policies: dict) -> str | None:
    if not policies.get(row["source_name"], {}).get("local_conversion_research_supported", False):
        return "source_rights_review_required"
    if row.get("dependencies"):
        return "dependency_resolution_required"
    return None


def ddc_command(executable: Path, source: Path, output: Path) -> list[str]:
    """Use the verified executable help interface, not the obsolete HTML example."""
    config = "FileVersion=ifc2x3; FileType=ifc; LevelOfDetail=high; IfcCommonPropSets=y; BimRvPropSets=y; BaseQuantities=y; MaterialPropSets=y"
    return [str(executable), str(source), "--output", str(output), "--mode", "custom", "--config", config]


def run_attempt(argv_template: list[str], source: Path, attempt: Path, *,
                expected_sha256: str, timeout: int = 180, validation_timeout: int = 180,
                cwd: Path | None = None) -> dict:
    """Execute one subprocess against a copy; preserve failures and reject empty success.

    Templates accept {input} and {output}; a literal original-source argument is
    also replaced with the staged copy. This runner never grants dataset admission.
    """
    source = source.resolve()
    attempt = attempt.resolve()
    if sha256(source) != expected_sha256:
        raise ValueError("SOURCE_HASH_MISMATCH")
    attempt.mkdir(parents=True, exist_ok=False)
    staged = attempt / "input" / source.name
    staged.parent.mkdir()
    shutil.copyfile(source, staged)
    output = attempt / "converted.ifc"
    argv = [str(staged) if v in {"{input}", str(source)} else str(output) if v == "{output}" else v for v in argv_template]
    result = {"argv": argv, "source": str(source), "source_sha256_before": expected_sha256,
              "status": "started", "conversion_completed": False, "technical_candidate": False,
              "dataset_admitted": False}
    write_new_json(attempt / "invocation.json", result)
    started = time.monotonic()
    try:
        with (attempt / "stdout.log").open("xb") as stdout, (attempt / "stderr.log").open("xb") as stderr:
            process = subprocess.Popen(argv, cwd=cwd or attempt, stdout=stdout, stderr=stderr,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # The known wrapper can spawn a child converter. Stop only this
                # recorded process tree, never enumerate or kill unrelated apps.
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=stderr, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process.kill()
                process.wait()
                result["status"] = "converter_timeout"
                code = None
        result["returncode"] = code
        if code is not None:
            if code != 0:
                result["status"] = "converter_failed"
            elif not output.is_file() or not output.stat().st_size:
                result["status"] = "missing_output"
            else:
                result["conversion_completed"] = True
                result["output_sha256"] = sha256(output)
                report = attempt / "validation.json"
                with (attempt / "validation.stdout.log").open("xb") as stdout, (attempt / "validation.stderr.log").open("xb") as stderr:
                    try:
                        checked = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "validate", str(output), "--report", str(report)],
                                                 stdout=stdout, stderr=stderr, timeout=validation_timeout,
                                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                        if report.is_file():
                            validation = json.loads(report.read_text(encoding="utf-8"))
                            result["technical_candidate"] = validation["technical_candidate"] and checked.returncode == 0
                            result["status"] = "technical_candidate" if result["technical_candidate"] else "validation_failed"
                            result["validation_blockers"] = validation["blockers"]
                        else:
                            result["status"] = "validation_process_failed"
                    except subprocess.TimeoutExpired:
                        result["status"] = "validation_timeout"
    except Exception as exc:
        result["status"] = "execution_exception"
        result["exception"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["seconds"] = round(time.monotonic() - started, 3)
        result["source_sha256_after"] = sha256(source)
        result["staged_source_sha256_after"] = sha256(staged) if staged.is_file() else None
        if result["source_sha256_after"] != expected_sha256 or result["staged_source_sha256_after"] != expected_sha256:
            result["status"] = "source_mutation_detected"
            result["technical_candidate"] = False
        write_new_json(attempt / "attempt.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract")
    extract.add_argument("--base", type=Path, default=BASE)
    validate = commands.add_parser("validate")
    validate.add_argument("ifc", type=Path)
    validate.add_argument("--report", type=Path, required=True)
    convert = commands.add_parser("convert")
    convert.add_argument("--ids", nargs="+", required=True)
    convert.add_argument("--run-name", required=True)
    convert.add_argument("--converter", type=Path, required=True)
    convert.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.command == "extract":
        result = extract_handoff(args.base)
        output = args.base / "asset-index.json"
        if output.exists():
            if json.loads(output.read_text(encoding="utf-8")) != result:
                raise ValueError("EXISTING_INDEX_CONFLICT")
        else:
            write_new_json(output, result)
        print(json.dumps({k: v for k, v in result.items() if k != "assets"}))
        return 0
    if args.command == "convert":
        index = json.loads((BASE / "asset-index.json").read_text(encoding="utf-8"))
        assets = {r["inventory_id"]: r for r in index["assets"]}
        if any(aid not in assets for aid in args.ids):
            raise ValueError("UNKNOWN_ASSET_ID")
        if len(args.ids) != len(set(args.ids)):
            raise ValueError("DUPLICATE_ASSET_ID")
        run_root = safe_target(BASE / "runs", args.run_name)
        if run_root.exists():
            raise ValueError("RUN_ALREADY_EXISTS")
        executable = args.converter.resolve(strict=True)
        outcomes = []
        policies = {r["source_name"]: r for r in json.loads((BASE / "review-20260913/source-review.json").read_text(encoding="utf-8"))["sources"]}
        for aid in args.ids:
            row = assets[aid]
            blocker = conversion_blocker(row, policies)
            if blocker:
                outcome = {"inventory_id": aid, "status": blocker, "dependencies": row["dependencies"]}
                write_new_json(run_root / aid / "attempt.json", outcome)
            else:
                outcome = run_attempt(ddc_command(executable, Path("{input}"), Path("{output}")),
                                      BASE / row["local_path"], run_root / aid,
                                      expected_sha256=row["sha256"], timeout=args.timeout, cwd=executable.parent)
                outcome["inventory_id"] = aid
            outcomes.append(outcome)
            print(json.dumps({k: outcome[k] for k in ("inventory_id", "status")}), flush=True)
            if outcome["status"] in {"converter_failed", "execution_exception", "source_mutation_detected", "validation_failed"}:
                break
        write_new_json(run_root / "summary.json", {"requested_ids": args.ids, "outcomes": outcomes,
                                                   "unattempted_ids": args.ids[len(outcomes):]})
        return 0 if all(r["status"] == "technical_candidate" for r in outcomes) else 2
    result = validate_ifc(args.ifc)
    write_new_json(args.report, result)
    print(json.dumps({k: v for k, v in result.items() if k not in {"native_findings", "geometry"}}, default=str))
    return 0 if result["technical_candidate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
