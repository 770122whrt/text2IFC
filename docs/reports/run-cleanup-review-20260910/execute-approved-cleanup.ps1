$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath('E:\code for project\bimnet').TrimEnd('\')
$reportRoot = Join-Path $taskRoot 'docs\reports\run-cleanup-review-20260910'
$proposalPath = Join-Path $reportRoot 'deletion-proposal.json'
$auth = Get-Content -LiteralPath (Join-Path $reportRoot 'authorization.json') -Encoding UTF8 -Raw | ConvertFrom-Json
if ($auth.status -ne 'approved' -or (Get-FileHash -LiteralPath $proposalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $auth.proposal_sha256) { throw 'Approval binding mismatch' }
$proposal = Get-Content -LiteralPath $proposalPath -Encoding UTF8 -Raw | ConvertFrom-Json
$execution = Get-Content -LiteralPath (Join-Path $taskRoot 'dataset\processed\ifc-presentation-validation\c-shaped-brief-budget-experiment-20260910\live\execution.json') -Encoding UTF8 -Raw | ConvertFrom-Json
if ($execution.status -ne 'completed' -or $execution.arms.Count -ne 2) { throw 'Experiment not completed' }
if ($proposal.targets.Count -ne 12) { throw 'Expected exactly 12 approved targets' }
$branch = git -C $taskRoot branch --show-current
if ($branch -ne 'codex/workflow-dataset-links') { throw 'Wrong branch' }
git -C $taskRoot merge-base --is-ancestor 9dfd91b4 origin/codex/workflow-dataset-links
if ($LASTEXITCODE -ne 0) { throw 'Preservation commit missing from remote tracking ref' }
$tracked = @{}
git -C $taskRoot ls-tree -r --name-only origin/codex/workflow-dataset-links -- dataset/processed/proof/generation | ForEach-Object { $tracked[$_] = $true }
if ($LASTEXITCODE -ne 0) { throw 'Cannot inventory remote Proof tree' }
function Assert-ContainedPlainPath([string] $path) {
    $full = [IO.Path]::GetFullPath($path)
    if (-not $full.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Outside workspace: $full" }
    $cursor = $full
    while ($cursor -ne $taskRoot) {
        $item = Get-Item -LiteralPath $cursor -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point: $cursor" }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}
function Assert-Files([object] $row, [string] $full) {
    $all = @(Get-ChildItem -LiteralPath $full -Recurse -Force)
    foreach ($item in $all) { if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse child: $($item.FullName)" } }
    $actual = @($all | Where-Object { -not $_.PSIsContainer })
    if ($actual.Count -ne $row.files.Count) { throw "File count changed: $full" }
    $expected = @{}
    foreach ($f in $row.files) { $expected[$f.path] = $f }
    foreach ($f in $actual) {
        $rel = $f.FullName.Substring($full.Length + 1).Replace('\', '/')
        if (-not $expected.ContainsKey($rel)) { throw "Unexpected file: $rel" }
        $e = $expected[$rel]
        if ($f.Length -ne $e.bytes -or (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $e.sha256) { throw "Source changed: $($f.FullName)" }
        $stream = [IO.File]::Open($f.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
        $stream.Dispose()
    }
}
$validated = @()
$proofCopies = @{}
$resolvedMappings = @()
$twoRoot = 'dataset/processed/proof/generation/phase6.6/two-storey-community-20260909'
$twoManifest = Get-Content -LiteralPath (Join-Path $taskRoot ($twoRoot + '/review-manifest.json')) -Encoding UTF8 -Raw | ConvertFrom-Json
$twoMapping = @{}
foreach ($entry in $twoManifest.legacy_bundles[0].entries) { $twoMapping[$entry.legacy_path] = $twoRoot + '/' + $entry.path }
foreach ($row in $proposal.targets) {
    if ($row.target -notmatch '^(\.tmp/|dataset/processed/ifc-presentation-validation/)') { throw 'Disallowed deletion root' }
    $full = Assert-ContainedPlainPath (Join-Path $taskRoot $row.target)
    Assert-Files $row $full
    foreach ($f in $row.files) {
        if (-not $row.target.StartsWith('.tmp/')) {
            if ($f.proof_copies.Count -lt 1) { throw 'Missing preserved copy' }
            if ($row.target.EndsWith('/A-revise/runtime')) {
                $copy = 'dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910/evidence/frozen/A-revise/runtime/' + $f.path
            } elseif ($row.target.EndsWith('/B-retain/runtime')) {
                $copy = 'dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910/evidence/frozen/B-retain/runtime/' + $f.path
            } elseif ($row.target.EndsWith('/two-storey-human-review-20260909')) {
                if (-not $twoMapping.ContainsKey($f.path)) { throw 'Missing two-storey manifest mapping' }
                $copy = $twoMapping[$f.path]
            } else { throw 'No case-specific authority mapping' }
            if (-not $tracked.ContainsKey($copy)) { throw "Proof copy not tracked on remote: $copy" }
            $copyFull = Assert-ContainedPlainPath (Join-Path $taskRoot $copy)
            if ((Get-Item -LiteralPath $copyFull).Length -ne $f.bytes -or (Get-FileHash -LiteralPath $copyFull -Algorithm SHA256).Hash.ToLowerInvariant() -ne $f.sha256) { throw "Proof copy differs: $copy" }
            $proofCopies[$copyFull] = $f.sha256
            $resolvedMappings += [pscustomobject]@{old_path=($row.target + '/' + $f.path);new_path=$copy;sha256=$f.sha256}
        }
    }
    $validated += [pscustomobject]@{ target=$row.target; absolute_path=$full; files=$row.files.Count; bytes=($row.files | Measure-Object -Property bytes -Sum).Sum }
}
$pre = [ordered]@{ status='passed'; checked_at=[DateTime]::UtcNow.ToString('o'); proposal_sha256=$auth.proposal_sha256; experiment_finished_at=$execution.finished_at; remote_commit=(git -C $taskRoot rev-parse origin/codex/workflow-dataset-links); source_files=($validated | Measure-Object -Property files -Sum).Sum; canonical_proof_copies=$proofCopies.Count; checks=@('exact source file sets/sizes/SHA256','exclusive-read handle check','no ancestor/child reparse points','absolute paths contained','canonical copies match and remote tree tracks them'); targets=$validated }
$pre | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $reportRoot 'pre-deletion-verification.json') -Encoding UTF8
@{status='verified_before_deletion';note='Case-specific committed authority replaces incidental content-identical copy links in original proposal; approved deletion targets and all source hashes unchanged.';files=$resolvedMappings} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $reportRoot 'canonical-paths.json') -Encoding UTF8
$deleted = @()
try {
    foreach ($row in $proposal.targets) {
        $full = Assert-ContainedPlainPath (Join-Path $taskRoot $row.target)
        Assert-Files $row $full
        Remove-Item -LiteralPath $full -Recurse -Force
        if (Test-Path -LiteralPath $full) { throw "Target remains: $full" }
        $deleted += $row.target
    }
    foreach ($copy in $proofCopies.Keys) {
        if ((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proofCopies[$copy]) { throw "Post-delete Proof change: $copy" }
    }
    $result = [ordered]@{status='completed';finished_at=[DateTime]::UtcNow.ToString('o');deleted_targets=$deleted;files=$pre.source_files;bytes=($validated | Measure-Object -Property bytes -Sum).Sum;canonical_proof_copies_unchanged=$proofCopies.Count;proposal_sha256=$auth.proposal_sha256}
} catch {
    $result = [ordered]@{status='partial_or_failed';finished_at=[DateTime]::UtcNow.ToString('o');deleted_targets=$deleted;error=$_.Exception.Message;proposal_sha256=$auth.proposal_sha256}
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $reportRoot 'deletion-result.json') -Encoding UTF8
    throw
}
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $reportRoot 'deletion-result.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 5
