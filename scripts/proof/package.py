"""Byte-preserving Proof relocation with a reversible frozen-layout index.

The index changes storage, never the frozen contract or acceptance decision.
No source deletion, Provider calls or evidence re-curation occur here.
"""
from __future__ import annotations
import gc
import hashlib
from pathlib import Path, PureWindowsPath
import shutil

SCHEMA = "text2ifc/workflow-proof-package/0.1"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def contained(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("expected a relative POSIX path")
    rel = Path(relative)
    if rel.is_absolute() or PureWindowsPath(relative).drive or PureWindowsPath(relative).root or ".." in rel.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    root = Path(root).resolve()
    path = root / relative
    current = path
    while current != root:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError(f"linked evidence path: {relative}")
        current = current.parent
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"path escapes collection: {relative}")
    return path


def capture_bundle(source, collection, key, mapping=None):
    source, collection = Path(source).resolve(), Path(collection).resolve()
    contained(collection, key)
    if source == collection or source.is_relative_to(collection) or collection.is_relative_to(source):
        raise ValueError("source and destination must be separate")
    mapping = mapping or {}
    entries = []
    operations = []
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source).as_posix()
        contained(source, relative)
        if not item.is_file():
            continue
        destination = mapping.get(relative, f"evidence/{key}/{relative}")
        target = contained(collection, destination)
        sha = digest(item)
        if target.exists() and (not target.is_file() or digest(target) != sha):
            raise FileExistsError(f"independent target content: {target}")
        entries.append({"legacy_path": relative, "path": destination,
                        "sha256": sha, "size_bytes": item.stat().st_size})
        operations.append((item, target))
    unknown = set(mapping) - {e["legacy_path"] for e in entries}
    if unknown:
        raise ValueError(f"mapping sources missing: {sorted(unknown)}")
    by_target = {}
    for entry in entries:
        previous = by_target.setdefault(entry["path"], entry["sha256"])
        if previous != entry["sha256"]:
            raise ValueError("conflicting destination bindings")
    for item, target in operations:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also protects against concurrent writers.
            with item.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst)
    bundle = {"id": key, "old_root": source.as_posix(), "entries": entries}
    verify_bundle(collection, bundle)
    return bundle


def verify_bundle(collection, bundle):
    seen = set()
    cache = {}
    total = 0
    for entry in bundle["entries"]:
        legacy = entry["legacy_path"]
        contained(collection, legacy)
        if legacy in seen:
            raise ValueError(f"duplicate legacy path: {legacy}")
        seen.add(legacy)
        path = contained(collection, entry["path"])
        if not path.is_file():
            raise ValueError(f"missing evidence: {entry['path']}")
        actual = cache.setdefault(path, None)
        if actual is None:
            actual = cache[path] = digest(path)
        if path.stat().st_size != entry["size_bytes"] or actual != entry["sha256"]:
            raise ValueError(f"evidence digest mismatch: {entry['path']}")
        total += entry["size_bytes"]
    return {"files": len(seen), "bytes": total}


def materialize_bundle(collection, bundle, target):
    target = Path(target)
    if target.exists():
        raise FileExistsError(target)
    if target.resolve().is_relative_to(Path(collection).resolve()):
        raise ValueError("projection must be outside the package")
    verify_bundle(collection, bundle)
    for entry in bundle["entries"]:
        contained(target, entry["legacy_path"])
    target.mkdir(parents=True)
    for entry in bundle["entries"]:
        destination = contained(target, entry["legacy_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        with contained(collection, entry["path"]).open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)


def validate_package(collection, document, *, reopen=True):
    errors = []
    checked = opened = 0
    collection = Path(collection)
    if document.get("schema_version") != SCHEMA:
        errors.append("unsupported package schema")
    for name in ("README.md", "REPORT.md"):
        if not (collection / name).is_file():
            errors.append(f"missing collection {name}")
    seen = set()
    for bundle in document.get("legacy_bundles", []):
        try:
            if bundle["id"] in seen:
                raise ValueError("duplicate bundle id")
            seen.add(bundle["id"])
            verify_bundle(collection, bundle)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(str(exc))
    previous = collection / "evidence/previous-view/manifest.json"
    if previous.exists():
        import json
        old = json.loads(previous.read_text(encoding="utf-8"))
        fields = ("case_id", "status", "outcome", "evidence_mode", "provider_calls", "run_id", "original_role", "ifccompare")
        if old.get("status") != document.get("status") or [{k:c.get(k) for k in fields} for c in old["cases"]] != [{k:c.get(k) for k in fields} for c in document.get("cases", [])]:
            errors.append("migration changed frozen case decisions")
    seen = set()
    for case in document.get("cases", []):
        try:
            if not case.get("case_id") or case["case_id"] in seen:
                raise ValueError("missing or duplicate case id")
            seen.add(case["case_id"])
            root = contained(collection, case["path"])
            if root == collection.resolve():
                raise ValueError("case requires its own directory")
            required = ["REPORT.md", "request.txt", "evidence/README.md"]
            if document.get("workflow") == "repair":
                required.append("02-damaged.ifc")
                if case.get("outcome") == "no_output":
                    required.append("NO-REPAIR.md")
                    if any(p.name != "02-damaged.ifc" for p in root.glob("*.ifc")):
                        raise ValueError("no-output case contains extra IFC")
                elif case.get("outcome") == "repaired":
                    required.append("03-repaired.ifc")
                    if (root / "NO-REPAIR.md").exists():
                        raise ValueError("repaired case contains NO-REPAIR.md")
                else:
                    raise ValueError("unknown repair outcome")
                if (root / "01-original.ifc").exists():
                    required.append("01-original.ifc")
                    if case.get("original_role") not in {"private_ground_truth", "physical_fixture_non_private_audit"}:
                        raise ValueError("original role must be predeclared")
            elif document.get("workflow") == "generation":
                required += ["model.json", "generated.ifc"]
                if any((root / n).exists() for n in ("01-original.ifc", "02-damaged.ifc", "03-repaired.ifc", "NO-REPAIR.md")):
                    raise ValueError("generation must not contain a repair triplet")
            else:
                raise ValueError("unknown workflow")
            authority = contained(collection, case["authority"])
            if not authority.exists():
                raise ValueError("authority missing")
            if document.get("status") == "pending_human_review" and case.get("status") != "pending_human_review":
                raise ValueError("presentation cannot promote pending review")
            for name in required:
                path = contained(root, name)
                if not path.is_file() or path.stat().st_size == 0:
                    raise ValueError(f"missing or empty {name}")
                if name in {"request.txt", "model.json"} or name.endswith(".ifc"):
                    if name not in case["artifacts"]:
                        raise ValueError(f"missing artifact binding: {name}")
            files_index = root / "FILES.json"
            if files_index.exists():
                import json
                files_document = json.loads(files_index.read_text(encoding="utf-8"))
                if files_document.get("schema_version") == "text2ifc/package-artifacts/0.1" and files_document.get("artifacts") != case["artifacts"]:
                    raise ValueError("case FILES differs from collection bindings")
            for name, record in case["artifacts"].items():
                path = contained(root, name)
                if path.stat().st_size != record["size_bytes"] or digest(path) != record["sha256"]:
                    raise ValueError(f"artifact digest mismatch: {name}")
                source = contained(collection, record["source"])
                if "field" in record:
                    import json
                    value = json.loads(source.read_text(encoding="utf-8"))[record["field"]]
                    if not isinstance(value, str) or path.read_bytes() != value.encode("utf-8"):
                        raise ValueError(f"projected source mismatch: {name}")
                elif digest(source) != record["sha256"]:
                    raise ValueError(f"source digest mismatch: {name}")
                bound = any(e["path"] == record["source"] for b in document.get("legacy_bundles", []) for e in b["entries"])
                if not bound:
                    raise ValueError(f"source not in frozen bundle: {name}")
                checked += 1
                if reopen and path.suffix.lower() == ".ifc":
                    import ifcopenshell
                    model = ifcopenshell.open(str(path))
                    if model.schema != "IFC2X3":
                        raise ValueError(f"IFC2X3 required: {name}")
                    del model
                    gc.collect()
                    opened += 1
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            errors.append(f"{case.get('case_id')}: {exc}")
    return {"status": "failed" if errors else "passed", "errors": errors,
            "case_count": len(document.get("cases", [])), "checked_copy_count": checked,
            "reopened_ifc_count": opened, "scope": "package bytes, layout, roles and reopen; frozen curator remains separate"}


def projection_for_validation(collection, workspace):
    """Return a fresh exact legacy layout; caller owns its explicit scratch path.

    Kept on disk for audit and Windows LiteralPath cleanup. No automatic deletion.
    """
    import json
    import uuid
    collection = Path(collection)
    manifest = collection / "manifest.json"
    if not manifest.exists():
        return collection
    document = json.loads(manifest.read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA:
        return collection
    bundles = [b for b in document["legacy_bundles"] if b["id"] == "frozen"]
    if len(bundles) != 1:
        raise ValueError("original validator requires exactly one frozen bundle")
    target = Path(workspace) / (collection.name + "-" + uuid.uuid4().hex)
    materialize_bundle(collection, bundles[0], target)
    return target


def legacy_file(collection, relative, *, bundle_id="frozen"):
    """Resolve and verify one old artifact name without copying a runtime tree."""
    import json
    collection = Path(collection)
    contained(collection, relative)
    document = json.loads((collection / "manifest.json").read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA:
        raise ValueError("expected consolidated package")
    matches = [e for b in document["legacy_bundles"] if b["id"] == bundle_id
               for e in b["entries"] if e["legacy_path"] == relative]
    if len(matches) != 1:
        raise ValueError(f"legacy artifact must resolve exactly once: {relative}")
    entry = matches[0]
    verify_bundle(collection, {"entries": [entry]})
    return contained(collection, entry["path"])
