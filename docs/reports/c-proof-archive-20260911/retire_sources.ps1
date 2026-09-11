$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$taskBase = Join-Path $taskRoot 'dataset/processed/ifc-presentation-validation'
$proposal = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-proposal.json') -Encoding UTF8 | ConvertFrom-Json
$resultPath = Join-Path $PSScriptRoot 'deletion-result.json'
if (Test-Path -LiteralPath $resultPath) { throw 'Deletion already recorded; refuse repeat' }
if ($proposal.targets.Count -ne 10) { throw 'Unexpected scope' }
# Validate all directories and retained files before the first deletion.
foreach ($target in $proposal.targets) {
    $resolved = (Resolve-Path -LiteralPath $target.absolute_path).Path
    if ($resolved -ne [IO.Path]::GetFullPath((Join-Path $taskRoot $target.path))) { throw 'Source mismatch' }
    if ([IO.Path]::GetDirectoryName($resolved) -ne $taskBase.Replace('/','\')) { throw 'Outside approved parent' }
    $items = @(Get-Item -LiteralPath $resolved) + @(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
    if (@($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Reparse point in source' }
    $files = @($items | Where-Object { -not $_.PSIsContainer })
    if ($files.Count -ne $target.files.Count) { throw 'Source file set changed' }
    foreach ($record in $target.files) {
        $source = Join-Path $resolved $record.relative_path
        if ((Get-Item -LiteralPath $source).Length -ne $record.size_bytes) { throw "Source size changed: $source" }
        if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw "Source changed: $source" }
        if ($record.retained_at) {
            $retained = [IO.Path]::GetFullPath((Join-Path $taskRoot $record.retained_at))
            if (-not ($retained.StartsWith((Join-Path $taskRoot 'dataset/processed/experiments/').Replace('/','\')) -or $retained.StartsWith((Join-Path $taskRoot 'dataset/processed/proof/generation/phase6.6/c-shaped-teaching-20260911/').Replace('/','\')))) { throw 'Retained path outside scope' }
            if ((Get-Item -LiteralPath $retained).Length -ne $record.size_bytes) { throw "Copy size changed: $retained" }
            if ((Get-FileHash -LiteralPath $retained -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw "Copy changed: $retained" }
        } elseif ($record.action -ne 'remove_rebuildable_python_bytecode') { throw 'Unbacked evidence' }
    }
}
$removed = @()
foreach ($target in $proposal.targets) {
    Remove-Item -LiteralPath $target.absolute_path -Recurse -Force
    if (Test-Path -LiteralPath $target.absolute_path) { throw 'Deletion incomplete' }
    $removed += [PSCustomObject]@{ path=$target.path;files=$target.file_count;bytes=$target.bytes;status='removed' }
    [PSCustomObject]@{status='in_progress';removed=$removed} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-progress.json') -Encoding UTF8
}
[PSCustomObject]@{status='completed';date='2026-09-11';source_count=$removed.Count;files=$proposal.file_count;bytes=$proposal.bytes;removed=$removed;proof_and_experiment_evidence_preserved=$true} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
Get-Content -LiteralPath $resultPath -Encoding UTF8
