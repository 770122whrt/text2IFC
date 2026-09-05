# Zcode local recovery archives — 2026-09-05

These are preserved historical sources and evidence, not newly accepted Proof.
No archive is an active Python import root. Extract into a **new empty folder**;
never extract over accepted evidence or an active checkout.

| Archive | Preserved content |
| --- | --- |
| `root-evidence.zip` | Root historical runs, genuine success/failure attempts, old Proof, ignored repair runs, and local audit records |
| `worktree-evidence.zip` | `w/` run lineage, failed attempts and Proof; entries retain the original `w/` prefix |
| `refactor-workspace.zip` | Refactored mirror, audit/handoff documents, refactor scripts and `tmp/source-snapshot`; source snapshot is intentionally preserved |
| `ifc-bench-snapshot.zip` | All 170 tracked files materialized at submodule commit `fa301cfbff5bcc0a27a5e8ef7714fea48b123208`, including actual LFS content |
| `bim-whale-ifc-samples-snapshot.zip` | All 59 tracked files at submodule commit `595fa90e3af7120d004fcb37a79d8657f1d1c9c2` |
| `supplemental-evidence.zip` | Ignored JSONfix attempt and compiled evaluation fixture identified by the final coverage pass |

`file-manifest.jsonl` gives original paths, byte counts and SHA-256 for the first
three archives. The two `*-files.json` documents describe submodule snapshots.
`supplemental-files.json` also identifies duplicate-by-content recovery paths
and generated metadata exclusions. ZIP files are stored through Git LFS.

The refactored mirror's production/benchmark split, `text2ifc_proof` extraction,
runner regrouping, and rewritten documentation remain **archived only**. They
have not been made compatible with the later C1–C5/root changes and must not be
described as integrated production code. Its code and source snapshot are
available for a later deliberate adoption. Cache junctions and environment
dependencies must be recreated; the archive alone is not a runnable environment.

The active accepted C1–C5 Proof is at
`dataset/processed/proof/repair-damage-restoration/c1-c5-live-20260904-combined`
in the Zcode checkout. The integration verified all 142 files byte-for-byte
against `w`; it did not curate, regenerate or reassess that accepted Proof.

Recovery procedure:

1. Clone `Zcode` and run `git lfs pull origin Zcode`.
2. Check archive SHA-256 values and the per-file manifests before using data.
3. Unzip historical archives into a new empty recovery directory. Their paths
   are repository-relative; the `w/` tree is a historical source, not a nested
   worktree registration.
4. Initialize submodules normally where upstream is available. If the IFC-bench
   service still fails, extract its snapshot into a separate empty directory
   and verify `ifc-bench-files.json` before materializing a data checkout. The
   snapshot preserves working files, not submodule Git history.

Excluded: real `.env` (owner explicitly declined backup), virtual environments,
dependency/model caches, regenerable target SQLite indices, generated parser
and package metadata, and test temporary directories. Readability limitations
and exact exclusions are recorded in `inventory-exclusions.json`; the overall
deletion decision belongs to the integration report and the owner.
