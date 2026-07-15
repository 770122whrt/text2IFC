# Phase 6.5 Hard Full Trace Archive

`full-trace.zip` preserves the complete accepted real-DeepSeek session
`999d210c233b1c34` before its original worktree output directory is removed.

Archive facts:

- compressed size: approximately 2.73 MB;
- entries: 304 directory/file entries;
- uncompressed files: 301;
- uncompressed size: approximately 28.58 MB;
- SHA-256: `1d1a3c59034edcbaaf530588e57af72f8fa8f44d1b30eba9ec84ce68d16773a3`;
- source artifact scan: 0 secret findings across 296 scannable files;
- includes `output.ifc`, `report.md`, Design Brief raw response, staged package
  prompts/responses, three ChangeSet rounds, Gate/Audit evidence, metrics,
  progress events, and the session export.

The normal review entry points remain the uncompressed files beside this
archive: `report.md`, `candidate.json`, `feedback-rounds.json`,
`geometry-feedback.json`, and `hard-three-storey-final.ifc`. The ZIP is a
forensic backup for links in `report.md` that refer to detailed sidecars.

To inspect it on Windows without changing the repository:

```powershell
Expand-Archive full-trace.zip -DestinationPath phase6.5-hard-full-trace
```

The archive is evidence, not an input fixture and not a provider replay used
to satisfy live acceptance.
