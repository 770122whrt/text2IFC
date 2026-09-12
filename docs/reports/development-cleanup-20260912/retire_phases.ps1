param([ValidateSet('default','elevated')][string]$Context)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$archivePath = Join-Path $repoRoot 'dataset/processed/experiments/phase-history-20260912/manifest.json'
$archive = Get-Content -LiteralPath $archivePath -Encoding UTF8 | ConvertFrom-Json
$inventory = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'phase-inventory-combined.json') -Encoding UTF8 | ConvertFrom-Json
$receipt = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'phase-backup-receipt.json') -Encoding UTF8 | ConvertFrom-Json
if (-not $receipt.remote_verified -or -not $receipt.archive_verified) { throw 'Verified remote phase backup is required.' }
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.manifest_sha256) { throw 'Archive manifest changed.' }
if ($archive.status -ne 'archived_not_deleted' -or $archive.findings.Count) { throw 'Phase archive incomplete or unsafe.' }
foreach ($container in $archive.archives) {
    $path = Join-Path $repoRoot $container.path
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $container.sha256) { throw "Changed container: $path" }
}

function Assert-Path([string]$Path, [string]$Root, [switch]$AllowLeafLink) {
    $resolved = [IO.Path]::GetFullPath($Path)
    if ($resolved -ne $Root -and -not $resolved.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw "Outside approved phase root: $resolved" }
    $cursor = $resolved
    while ($true) {
        $item = Get-Item -LiteralPath $cursor -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and -not ($AllowLeafLink -and $cursor -eq $resolved)) { throw "Linked ancestor: $cursor" }
        if ($cursor -eq $Root) { break }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $resolved
}

$resultPath = Join-Path $PSScriptRoot "deletion-phases-$Context.json"
if (Test-Path -LiteralPath $resultPath) { throw 'Do not overwrite previous deletion results.' }
$retry = @{}
if ($Context -eq 'elevated') {
    $prior = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-phases-default.json') -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $prior.files | Where-Object status -NE 'deleted') { $retry[$entry.path] = $true }
}
$results = [Collections.Generic.List[object]]::new()
$dirResults = [Collections.Generic.List[object]]::new()
$linkResults = [Collections.Generic.List[object]]::new()
foreach ($bundle in $archive.bundles) {
    $root = [IO.Path]::GetFullPath((Join-Path $repoRoot $bundle.old_root))
    $allowedParents = @('dataset/processed/agent-demo','dataset/processed/ifc-repair','dataset/processed/ifc-repair-runs') | ForEach-Object { [IO.Path]::GetFullPath((Join-Path $repoRoot $_)) }
    if ([IO.Path]::GetDirectoryName($root) -notin $allowedParents) { throw "Unexpected phase root: $root" }
    foreach ($entry in @($bundle.entries)+@($bundle.excluded_caches)) {
        $path = [IO.Path]::GetFullPath((Join-Path $root $entry.legacy_path))
        if ($entry.source_context -ne $Context -and -not $retry.ContainsKey($path)) { continue }
        try {
            $path = Assert-Path $path $root
            $item = Get-Item -LiteralPath $path -Force
            if ($item.Length -ne $entry.size_bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Source changed after archiving.' }
            Remove-Item -LiteralPath $path -Force
            $results.Add(@{path=$path; status='deleted'; bytes=$entry.size_bytes})
        } catch { $results.Add(@{path=$path; status='preserved'; error=$_.Exception.Message}) }
    }
    # Enumerated links are test artifacts. Delete only the link entry; never
    # recurse into, clean, or change permissions on its target.
    foreach ($link in $bundle.links) {
        $path = [IO.Path]::GetFullPath((Join-Path $root $link.legacy_path))
        try {
            $path = Assert-Path $path $root -AllowLeafLink
            $item = Get-Item -LiteralPath $path -Force
            if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Expected test link was replaced.' }
            $actual = ([string]@($item.Target)[0]).Replace('\??\','').Replace('\\?\','')
            $expected = ([string]$link.target).Replace('\??\','').Replace('\\?\','')
            if ($actual -ne $expected) { throw 'Test link target changed.' }
            if ($item.Attributes -band [IO.FileAttributes]::Directory) { [IO.Directory]::Delete($path, $false) }
            else { [IO.File]::Delete($path) }
            $linkResults.Add(@{path=$path; status='unlinked'; target=$link.target; target_modified=$false})
        } catch { $linkResults.Add(@{path=$path; status='preserved_or_already_removed'; error=$_.Exception.Message}) }
    }
    # Only remove explicitly inventoried empty directories, deepest first.
    # Files that are new, changed or inaccessible keep their directories alive.
    $inventoryBundle = @($inventory.bundles | Where-Object old_root -EQ $bundle.old_root)[0]
    $directories = @($inventoryBundle.directories | Sort-Object Length -Descending)
    foreach ($relative in $directories) {
        $path = [IO.Path]::GetFullPath((Join-Path $root $relative))
        try {
            if (-not (Test-Path -LiteralPath $path)) { continue }
            $path = Assert-Path $path $root
            if (@(Get-ChildItem -LiteralPath $path -Force).Count) { continue }
            [IO.Directory]::Delete($path, $false)
            $dirResults.Add(@{path=$path; status='empty_directory_deleted'})
        } catch { $dirResults.Add(@{path=$path; status='preserved'; error=$_.Exception.Message}) }
    }
    @{status='in_progress'; files=$results; directories=$dirResults; links=$linkResults} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Output "Processed phase $($bundle.old_root); $($results.Count) file decisions recorded"
}
$deleted = @($results | Where-Object status -EQ 'deleted')
@{status='completed'; files=$results; directories=$dirResults; links=$linkResults; deleted_files=$deleted.Count; deleted_bytes=[long](($deleted | Measure-Object bytes -Sum).Sum)} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
Write-Output "Completed phases ($Context): $($deleted.Count) files deleted."
