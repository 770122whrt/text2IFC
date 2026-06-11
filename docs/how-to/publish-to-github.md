# Publish the text2IFC Repository to GitHub

This guide describes the verified publishing workflow for this repository on
Windows. It is intended for contributors and automation agents.

## Repository Requirements

The repository stores IFC datasets and research artifacts. These binary or
large files must use Git LFS:

```gitattributes
*.ifc filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
```

Never commit local dependencies, caches, credentials, or tool session logs.
The repository `.gitignore` excludes `.deps/`, Python caches, `.claude/`, and
`.playwright-mcp/`.

## One-time Setup

GitHub CLI is installed at:

```powershell
G:\software\ghcli\gh.exe
```

Authenticate and configure Git:

```powershell
& 'G:\software\ghcli\gh.exe' auth login
& 'G:\software\ghcli\gh.exe' auth setup-git
& 'G:\software\ghcli\gh.exe' auth status
git lfs install
```

The authenticated account must have write access to
`770122whrt/text2IFC`.

Do not paste access tokens into source files, documentation, terminal logs, or
chat messages.

## Normal Publish Workflow

Inspect the exact scope before staging:

```powershell
git status -sb
git diff --stat
git lfs ls-files
```

Run the relevant tests:

```powershell
$env:PYTHONPATH='.deps\python312'
python -m pytest tests -q
```

Stage, commit, and push:

```powershell
git add <intended-files>
git commit -m "<concise description>"
git push -u origin main
```

Use explicit file paths when unrelated changes are present.

## Verify the Remote

```powershell
& 'G:\software\ghcli\gh.exe' api `
  repos/770122whrt/text2IFC/git/ref/heads/main `
  --jq '.object.sha'

git status -sb
git log --oneline --decorate -1
```

The local `HEAD`, `origin/main`, and GitHub SHA must match.

## Windows Recovery Procedure

### Symptom: Schannel credential error

Example:

```text
SEC_E_NO_CREDENTIALS
```

Confirm GitHub CLI authentication, then use Git's OpenSSL backend for the
operation:

```powershell
git -c http.sslBackend=openssl ls-remote origin
```

Do not disable TLS certificate verification.

### Symptom: Large HTTPS push resets or Git crashes

Examples:

```text
RPC failed
Connection was reset
0xc0000005
The memory could not be read
```

Confirm that IFC, PDF, and ZIP files are tracked by LFS:

```powershell
git check-attr filter -- dataset\ifc\train\1px.ifc
git lfs ls-files
```

If an unpublished commit contains normal Git blobs instead of LFS objects,
migrate only the intended branch:

```powershell
git lfs migrate import `
  --include="*.ifc,*.pdf,*.zip" `
  --include-ref=refs/heads/main `
  --yes
```

This rewrites commit history. Use it only when:

1. The remote is empty, or the affected commit has not been shared.
2. The remote SHA has been checked.
3. A force update will use an exact lease.

Restore working files after migration:

```powershell
git lfs checkout
git add --renormalize .
```

If a crashed Git process leaves `.git\index.lock`, first verify that no Git
process is running:

```powershell
Get-Process | Where-Object { $_.ProcessName -like 'git*' }
```

Delete only the confirmed stale lock:

```powershell
Remove-Item -LiteralPath '.git\index.lock'
```

### Symptom: Credential helper crashes during LFS upload

First confirm that `gh auth status` succeeds. A one-command authorization
header may be derived from the GitHub CLI keyring without printing or
persisting the token:

```powershell
$token = & 'G:\software\ghcli\gh.exe' auth token
$pair = '770122whrt:' + $token.Trim()
$basic = [Convert]::ToBase64String(
  [Text.Encoding]::ASCII.GetBytes($pair)
)

git -c http.sslBackend=openssl `
  -c "http.https://github.com/.extraheader=AUTHORIZATION: Basic $basic" `
  lfs push --all origin main
```

The variables exist only in the current PowerShell process. Do not echo them.

After separately uploading LFS objects, push the Git commit. If history was
rewritten, use an exact force-with-lease:

```powershell
git push `
  --force-with-lease=refs/heads/main:<verified-old-sha> `
  -u origin main
```

Never use an unqualified `--force`.

## Verified Initial Publication

The initial repository publication used:

- GitHub repository: `770122whrt/text2IFC`
- Branch: `main`
- Published commit: `94fc54e`
- Git LFS objects: 31
- LFS patterns: `*.ifc`, `*.pdf`, `*.zip`

The final remote commit and local tracking branch were verified to match.
