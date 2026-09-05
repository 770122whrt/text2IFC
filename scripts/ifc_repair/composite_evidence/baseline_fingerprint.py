"""Baseline fingerprint mechanism for the Composite Repair Milestone evidence task.

Implements the revision-freeze contract of the composite evidence specification:

* ``snapshot``  - compute a per-file SHA-256 map of the production path set and
  write it to ``docs/validation/repair-composite-milestone/composite-baseline-fingerprint.json``.
* ``record-registry-exception`` - after the single atomic ``prompts/agent/registry.json``
  addition, record the post-edit hash in the fingerprint file.
* ``verify``    - recompute the map and compare it with the stored baseline.  The
  only tolerated difference is ``prompts/agent/registry.json`` matching the
  recorded post-exception hash.  Any other drift exits non-zero with details.

Usage (from repository root, repo venv)::

    python scripts/ifc_repair/composite_evidence/baseline_fingerprint.py snapshot
    python scripts/ifc_repair/composite_evidence/baseline_fingerprint.py record-registry-exception
    python scripts/ifc_repair/composite_evidence/baseline_fingerprint.py verify
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

FINGERPRINT_PATH = (
    REPO_ROOT
    / "docs"
    / "validation"
    / "repair-composite-milestone"
    / "composite-baseline-fingerprint.json"
)

REGISTRY_PATH = "prompts/agent/registry.json"

PRODUCTION_PATH_SET = {
    "src": "dir",
    "schemas": "dir",
    "prompts": "dir",
    "scripts/ifc_repair": "dir-except-composite_evidence",
    "tests/ifc_repair": "dir-except-composite_evidence",
    "pyproject.toml": "file",
    "requirements.txt": "glob:requirements*.txt",
    ".env.example": "file",
}

EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _production_files() -> dict[str, str]:
    """Return {relative_posix_path: sha256} for the production path set."""
    files: dict[str, str] = {}

    def add_file(rel: str) -> None:
        path = REPO_ROOT / rel
        if path.is_file():
            files[rel.replace("\\", "/")] = _sha256(path)

    def walk(rel_dir: str, skip_composite: bool) -> None:
        base = REPO_ROOT / rel_dir
        if not base.is_dir():
            return
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            if path.suffix in EXCLUDED_SUFFIXES:
                continue
            if skip_composite and "composite_evidence" in path.parts:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            files[rel] = _sha256(path)

    walk("src", skip_composite=False)
    walk("schemas", skip_composite=False)
    walk("prompts", skip_composite=False)
    walk("scripts/ifc_repair", skip_composite=True)
    walk("tests/ifc_repair", skip_composite=True)
    add_file("pyproject.toml")
    for req in sorted((REPO_ROOT).glob("requirements*.txt")):
        add_file(req.relative_to(REPO_ROOT).as_posix())
    add_file(".env.example")
    return dict(sorted(files.items()))


def _git_output(args: list[str]) -> str:
    import subprocess

    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _load() -> dict:
    with FINGERPRINT_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save(payload: dict) -> None:
    FINGERPRINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FINGERPRINT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=False)
        handle.write("\n")


def cmd_snapshot() -> int:
    if FINGERPRINT_PATH.exists():
        print(f"ERROR: fingerprint already exists: {FINGERPRINT_PATH}", file=sys.stderr)
        return 2
    files = _production_files()
    payload = {
        "task": "composite-repair-milestone",
        "head_sha": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "production_path_set": sorted(
            [
                "src/**",
                "schemas/**",
                "prompts/**",
                "scripts/ifc_repair/** (excluding composite_evidence/)",
                "tests/ifc_repair/** (excluding composite_evidence/)",
                "pyproject.toml",
                "requirements*.txt",
                ".env.example",
            ]
        ),
        "file_count": len(files),
        "files": files,
        "registry_exception": {
            "path": REGISTRY_PATH,
            "sha256_before": files.get(REGISTRY_PATH),
            "sha256_after": None,
            "applied": False,
        },
    }
    _save(payload)
    print(f"snapshot: {len(files)} files -> {FINGERPRINT_PATH}")
    print(f"COMPOSITE_EVIDENCE_BASE_REVISION={payload['head_sha']}")
    return 0


def cmd_record_registry_exception() -> int:
    payload = _load()
    current = _sha256(REPO_ROOT / REGISTRY_PATH)
    before = payload["registry_exception"]["sha256_before"]
    if current == before:
        print(
            "ERROR: registry.json is unchanged from baseline; nothing to record",
            file=sys.stderr,
        )
        return 2
    payload["registry_exception"]["sha256_after"] = current
    payload["registry_exception"]["applied"] = True
    payload["registry_exception"]["recorded_at_utc"] = _dt.datetime.now(
        _dt.timezone.utc
    ).isoformat()
    _save(payload)
    print(f"registry exception recorded: {REGISTRY_PATH} sha256={current}")
    return 0


def cmd_record_authorized_fix(reference: str) -> int:
    """Record production files changed under explicit user authorization.

    Each recorded fix keeps the baseline hash, the post-fix hash, and the
    authorization reference; verify() then accepts exactly those hashes for
    those files and nothing else.
    """
    payload = _load()
    current = _production_files()
    fixes = payload.setdefault("authorized_fixes", [])
    already = {entry["path"] for entry in fixes}
    changed = []
    for rel, old_hash in payload["files"].items():
        new_hash = current.get(rel)
        if new_hash is not None and new_hash != old_hash and rel not in already:
            changed.append(rel)
    for rel in sorted(changed):
        fixes.append(
            {
                "path": rel,
                "sha256_before": payload["files"][rel],
                "sha256_after": current[rel],
                "authorization_reference": reference,
                "recorded_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            }
        )
    baseline_files = payload["files"]
    added = [
        rel
        for rel in current
        if rel not in baseline_files and rel not in already
    ]
    for rel in sorted(added):
        fixes.append(
            {
                "path": rel,
                "sha256_before": None,
                "sha256_after": current[rel],
                "authorization_reference": reference,
                "recorded_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            }
        )
    if not changed and not added:
        print("no unrecorded production changes")
        return 0
    _save(payload)
    for rel in changed:
        print(f"authorized fix recorded: {rel} ({reference})")
    for rel in added:
        print(f"authorized addition recorded: {rel} ({reference})")
    return 0


def cmd_verify() -> int:
    payload = _load()
    baseline: dict[str, str] = payload["files"]
    current = _production_files()
    exception = payload["registry_exception"]
    reg_path = exception["path"]

    fixes = {
        entry["path"]: entry["sha256_after"]
        for entry in payload.get("authorized_fixes", [])
    }
    fix_baseline = {
        entry["path"]: entry["sha256_before"]
        for entry in payload.get("authorized_fixes", [])
    }

    drift: list[dict[str, str]] = []

    def is_registry(p: str) -> bool:
        return p == reg_path

    for rel, old_hash in baseline.items():
        if rel in fixes:
            # Authorized fix: current content must equal the recorded
            # post-fix hash (no further edits allowed after recording).
            expected = fixes[rel]
            if baseline.get(rel) != fix_baseline.get(rel):
                drift.append({"file": rel, "kind": "baseline_corrupted"})
                continue
            new_hash = current.get(rel)
            if new_hash is None:
                drift.append({"file": rel, "kind": "deleted"})
            elif new_hash != expected:
                drift.append(
                    {
                        "file": rel,
                        "kind": "modified_after_authorized_fix",
                        "expected": expected,
                        "actual": new_hash,
                    }
                )
            continue
        if is_registry(rel):
            allowed = {old_hash}
            if exception.get("sha256_after"):
                allowed.add(exception["sha256_after"])
            new_hash = current.get(rel)
            if new_hash is None:
                drift.append({"file": rel, "kind": "deleted"})
            elif new_hash not in allowed:
                drift.append(
                    {"file": rel, "kind": "modified", "expected": old_hash, "actual": new_hash}
                )
            continue
        new_hash = current.get(rel)
        if new_hash is None:
            drift.append({"file": rel, "kind": "deleted"})
        elif new_hash != old_hash:
            drift.append(
                {"file": rel, "kind": "modified", "expected": old_hash, "actual": new_hash}
            )

    # New files appearing inside the production path set are also drift, except
    # the allowlisted composite_evidence namespaces and the registry exception
    # (registry.json is always present in baseline already).
    for rel in current:
        if rel in baseline:
            continue
        if rel in fixes:
            # Authorized addition: content must equal the recorded hash.
            if current[rel] != fixes[rel]:
                drift.append(
                    {
                        "file": rel,
                        "kind": "modified_after_authorized_fix",
                        "expected": fixes[rel],
                        "actual": current[rel],
                    }
                )
            continue
        drift.append({"file": rel, "kind": "added"})

    if drift:
        print(f"DRIFT DETECTED ({len(drift)} entr{'y' if len(drift) == 1 else 'ies'}):")
        for item in drift:
            print(json.dumps(item, ensure_ascii=False))
        return 1
    print(f"verify: CLEAN ({len(baseline)} production files match baseline)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["snapshot", "verify", "record-registry-exception", "record-authorized-fix"],
    )
    parser.add_argument("--reference", default=None, help="authorization reference for record-authorized-fix")
    args = parser.parse_args()
    if args.command == "snapshot":
        return cmd_snapshot()
    if args.command == "record-registry-exception":
        return cmd_record_registry_exception()
    if args.command == "record-authorized-fix":
        if not args.reference:
            print("ERROR: --reference is required", file=sys.stderr)
            return 2
        return cmd_record_authorized_fix(args.reference)
    return cmd_verify()


if __name__ == "__main__":
    raise SystemExit(main())
