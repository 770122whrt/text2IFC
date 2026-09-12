# Publish the text2IFC Repository to GitHub

This guide describes scoped publishing from a Windows checkout. Read
[AGENTS.md](../../AGENTS.md) first; use the current task's authorized branch and
files. This guide does not authorize a main merge, a Provider call, a Full
Preflight, or history rewriting.

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

Choose validation for the change, following the
[takeover guide](agent-takeover.md#6-验证强度如何选择). Documentation-only work needs
link, claim and diff checks; behavioral changes need their applicable tests.
Do not automatically run all tests or a Full Preflight for a push.

```powershell
git diff --check
# For code changes, select the applicable target; prefer the repository venv.
.venv\Scripts\python -m pytest <relevant-test> -q
```

Confirm the current branch and inspect remote changes before staging:

```powershell
git branch --show-current
git worktree list
git fetch origin
git rev-list --left-right --count HEAD...origin/<authorized-branch>
git diff --cached --stat
```

If the remote branch has new commits, inspect them before proceeding. Preserve
unrelated staged and working-tree edits. Stage only the task's explicit files,
review the staged diff, then commit and push to that same authorized branch:

```powershell
git add -- <intended-files>
git diff --cached --check
git diff --cached --stat
git diff --cached -- <intended-files>
git commit -m "<concise description>"
git push origin HEAD:refs/heads/<authorized-branch>
```

`<authorized-branch>` and `<intended-files>` are placeholders, not literal
commands. This does not merge main. Never use `git add -A`, broad normalization,
force push or a reset to make an unrelated dirty checkout look clean.

## Verify the Remote

```powershell
git rev-parse HEAD
git ls-remote --heads origin refs/heads/<authorized-branch>
git rev-list --left-right --count HEAD...origin/<authorized-branch>
git status -sb
git log --oneline --decorate -1
```

The local HEAD and the explicitly targeted remote SHA must match, with 0/0
ahead/behind for that branch. Report main separately; do not claim it contains
work pushed only to a workflow branch.

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
git check-attr filter -- <intended-ifc-file>
git lfs ls-files
```

Do not automatically migrate Git/LFS history or renormalize the whole checkout
to recover a failed push. Preserve the failure, identify the exact affected
files and remote state, and resolve within the user's authorized scope. A
historical first-publish recovery procedure is not permission to rewrite
shared history or alter accepted evidence.

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

First confirm that `gh auth status` succeeds and inspect the helper's actual
error. Use the configured credential helper; do not print credentials or put
tokens into command-line headers. Retry only the intended branch after the
authentication problem is resolved. Do not broaden the upload to all LFS
history or use force push as a credential workaround.

## Historical Initial Publication

The initial repository publication used:

- GitHub repository: `770122whrt/text2IFC`
- Branch: `main`
- Published commit: `94fc54e`
- Git LFS objects: 31
- LFS patterns: `*.ifc`, `*.pdf`, `*.zip`

At that historical checkpoint the remote commit and local tracking branch
matched. These counts and commit are not the current repository state.
