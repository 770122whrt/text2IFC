"""Verify incoming audit provenance and IFC-Bench legacy counters; no source edits."""
from __future__ import annotations
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from text2ifc_dataset.audit import _tree_stats, _read_ifc_schema

REPORT = ROOT / "dataset/external/_checks/incoming-ifc-audit-20260910"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    canonical = [json.loads(s) for s in (ROOT / "dataset/manifests/ifc-files.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    corpus = ROOT / "dataset/external/ifc-bench"
    old = json.loads((ROOT / "dataset/manifests/external-corpora.json").read_text(encoding="utf-8"))
    old = next(r for r in old["corpora"] if r["corpus_id"] == "ifc-bench")
    count, size, unreadable = _tree_stats(corpus)
    actual = {p.relative_to(corpus).as_posix(): p for p in corpus.rglob("*") if p.is_file() and ".git" not in p.relative_to(corpus).parts}
    # Compare the local checkout to its tracked file inventory, without Git writes.
    process = subprocess.run(["git", "--no-optional-locks", "-C", str(corpus), "ls-files", "-z"], capture_output=True, check=True, timeout=30)
    tracked = set(process.stdout.decode("utf-8").strip("\x00").split("\x00"))
    bench = {"old_record": old, "actual_file_count": count, "actual_size_bytes": size, "unreadable": unreadable,
             "tracked_file_count": len(tracked), "missing_tracked": sorted(tracked - set(actual)),
             "untracked_files": [{"path": k, "size_bytes": actual[k].stat().st_size} for k in sorted(set(actual) - tracked)]}
    ifcs = [p for k, p in actual.items() if k.lower().endswith(".ifc")]
    bench["actual_ifc_count"] = len(ifcs)
    bench["actual_ifc_schemas"] = dict(Counter(_read_ifc_schema(p) for p in ifcs))
    registered = [r for r in canonical if r["source_id"] == "ifc-bench"]
    bench["canonical_records"] = len(registered)
    bench["missing_canonical"] = [r["local_path"] for r in registered if not (ROOT / r["local_path"]).is_file()]
    bench["canonical_ifc2x3_eligible"] = sum(r.get("repair_source_eligible", False) for r in registered)
    bench["physical_ifc_not_canonical_path"] = [p.relative_to(ROOT).as_posix() for p in ifcs if p.relative_to(ROOT).as_posix() not in {r["local_path"] for r in canonical}]
    inventory = json.loads((REPORT / "inventory.json").read_text(encoding="utf-8"))
    metadata = []
    for archive in inventory["archives"]:
        entry = {"archive": archive["name"], "documents": []}
        for item in archive["other_members"]:
            name = item["member"]
            if any(s in name for s in ("REPORT_ZH.md", "README", "dependency_manifest.json", "rvt_manifest.json", "conversion_manifest.json", "validation_summary.json", "batch01_summary.md")) and "text" in item:
                text = item["text"]
                if name.endswith(("rvt_manifest.json", "conversion_manifest.json")):
                    payload = json.loads(text)
                    entry["documents"].append({"member": name, "structure": list(payload) if isinstance(payload, dict) else "list", "sample": str(payload)[:7000]})
                else:
                    entry["documents"].append({"member": name, "text": text})
        metadata.append(entry)
    result = {"ifc_bench": bench, "incoming_provenance": metadata}
    path = REPORT / "reconciliation-before.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
