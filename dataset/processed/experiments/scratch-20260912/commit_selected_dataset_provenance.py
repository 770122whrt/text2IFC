from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    "scripts/dataset/classify_bimdata_source_evidence.py",
    "scripts/dataset/capture_bimdata_package_evidence.py",
    "scripts/dataset/reconcile_bimdata_package_members.py",
    "scripts/dataset/probe_bimdata_source_urls.py",
    "scripts/dataset/build_bimdata_resolution_manifest.py",
    "scripts/dataset/audit_ifc_candidate_provenance.py",
    "dataset/manifests/candidates/source-registry.json",
    "dataset/manifests/candidates/bimdata-rd-source-evidence.jsonl",
    "dataset/manifests/candidates/bimdata-rd-package-evidence.jsonl",
    "dataset/manifests/candidates/bimdata-rd-package-reconciliation.jsonl",
    "dataset/manifests/candidates/bimdata-rd-url-probe.jsonl",
    "dataset/manifests/candidates/bimdata-rd-resolution.jsonl",
    "dataset/manifests/candidates/README.md",
]


def run(args: list[str], *, input_text: str | None = None) -> str:
    if input_text is None:
        result = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.stdout.strip()
    result = subprocess.run(
        args,
        cwd=ROOT,
        input=input_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8").strip()


def ls_tree(tree_hash: str) -> dict[str, tuple[str, str, str]]:
    out = run(["git", "ls-tree", tree_hash])
    entries: dict[str, tuple[str, str, str]] = {}
    for line in out.splitlines():
        if not line:
            continue
        meta, name = line.split("\t", 1)
        mode, obj_type, obj_hash = meta.split(" ", 2)
        entries[name] = (mode, obj_type, obj_hash)
    return entries


def build_tree(base_tree: str | None, updates: dict[str, str]) -> str:
    entries = ls_tree(base_tree) if base_tree else {}
    grouped: dict[str, dict[str, str]] = {}
    direct: dict[str, str] = {}
    for rel, abs_path in updates.items():
        head, sep, tail = rel.partition("/")
        if sep:
            grouped.setdefault(head, {})[tail] = abs_path
        else:
            direct[head] = abs_path

    for name, abs_path in direct.items():
        blob = run(["git", "hash-object", "-w", abs_path])
        entries[name] = ("100644", "blob", blob)

    for dirname, child_updates in grouped.items():
        existing = entries.get(dirname)
        child_base = existing[2] if existing and existing[1] == "tree" else None
        child_tree = build_tree(child_base, child_updates)
        entries[dirname] = ("040000", "tree", child_tree)

    lines = []
    for name in sorted(entries):
        mode, obj_type, obj_hash = entries[name]
        lines.append(f"{mode} {obj_type} {obj_hash}\t{name}")
    return run(["git", "mktree"], input_text="\n".join(lines) + "\n")


head = run(["git", "rev-parse", "HEAD"])
base_tree = run(["git", "rev-parse", f"{head}^{{tree}}"])
updates = {path: str(ROOT / path) for path in PATHS}
for path, abs_path in updates.items():
    if not Path(abs_path).is_file():
        raise SystemExit(f"missing selected path: {path}")
new_tree = build_tree(base_tree, updates)
print(f"HEAD={head}")
print(f"TREE={new_tree}")
print("PATHS")
for path in PATHS:
    print(path)
