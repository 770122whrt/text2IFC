param(
    [ValidateSet('evidence', 'pytest')][string]$Category,
    [ValidateSet('default', 'elevated')][string]$Context,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$scratchRoot = Join-Path $repoRoot '.tmp'
$presentationRoot = Join-Path $repoRoot 'dataset/processed/ifc-presentation-validation'
$experimentRoot = Join-Path $repoRoot 'dataset/processed/experiments'
$receiptPath = Join-Path $PSScriptRoot 'backup-receipt.json'
if ($Apply) {
    $receipt = Get-Content -LiteralPath $receiptPath -Encoding UTF8 | ConvertFrom-Json
    if (-not $receipt.remote_verified -or -not $receipt.index_bytes_verified) { throw 'Archive backup not verified.' }
}

function Assert-Contained([string]$Path, [string]$Root) {
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Outside authorized root: $resolved" }
    $cursor = $resolved
    while ($cursor -ne $Root) {
        $item = Get-Item -LiteralPath $cursor -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $cursor" }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $resolved
}

function Assert-Bytes([string]$Path, $Entry) {
    if ((Get-Item -LiteralPath $Path -Force).Length -ne $Entry.size_bytes) { throw "Changed size: $Path" }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) { throw "Changed bytes: $Path" }
}

function Get-VerifiedFiles([string]$Path) {
    $items = @(Get-ChildItem -LiteralPath $Path -Force -Recurse)
    if (@($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw "Linked directory: $Path" }
    return @($items | Where-Object { -not $_.PSIsContainer })
}

$targets = [Collections.Generic.List[object]]::new()
if ($Category -eq 'evidence') {
    $archive = Get-Content -LiteralPath (Join-Path $experimentRoot 'development-retirement-20260912.json') -Encoding UTF8 | ConvertFrom-Json
    foreach ($bundle in $archive.bundles) {
        $targets.Add(@{path=(Join-Path $repoRoot $bundle.old_root); kind='archived_source'; data=$bundle})
    }
    $scratch = Get-Content -LiteralPath (Join-Path $experimentRoot 'scratch-retirement-20260912.json') -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in $scratch.entries) { $targets.Add(@{path=$item.path; kind='archived_scratch'; data=$item}) }
} else {
    $plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'scratch-retirement-plan.json') -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in $plan.directories | Where-Object execution_context -EQ $Context) {
        $targets.Add(@{path=$item.path; kind='rebuildable_pytest'; data=$item})
    }
}

$results = [Collections.Generic.List[object]]::new()
$resultPath = Join-Path $PSScriptRoot "deletion-$Category-$Context.json"
if (Test-Path -LiteralPath $resultPath) { throw 'Keep prior execution records; do not overwrite.' }
$index = 0
foreach ($target in $targets) {
    $index++
    $startedDeletion = $false
    try {
        $path = Assert-Contained $target.path $(if ($target.kind -eq 'archived_source') { $presentationRoot } else { $scratchRoot })
        $entry = $target.data
        if ($target.kind -eq 'archived_source') {
            $files = @(Get-VerifiedFiles $path)
            $expected = @($entry.entries) + @($entry.excluded_caches)
            if ($files.Count -ne $expected.Count) { throw "Changed source file set: $path" }
            foreach ($e in $expected) { Assert-Bytes (Assert-Contained (Join-Path $path $e.legacy_path) $path) $e }
            foreach ($e in $entry.entries) { Assert-Bytes (Assert-Contained (Join-Path $repoRoot $e.retained_path) $repoRoot) $e }
            $count = $files.Count
            $bytes = [long](($files | Measure-Object Length -Sum).Sum)
        } elseif ($target.kind -eq 'archived_scratch') {
            Assert-Bytes $path $entry
            $retained = Assert-Contained (Join-Path $repoRoot $entry.retained_path) $repoRoot
            if ($entry.archive_member) {
                # archive-verification.json has checked the exact member bytes;
                # bind that verified ZIP again without hashing unrelated files.
                Assert-Bytes $retained @{size_bytes=$entry.container_bytes; sha256=$entry.container_sha256}
            } else { Assert-Bytes $retained $entry }
            $count = 1
            $bytes = [long]$entry.size_bytes
        } else {
            if (Test-Path -LiteralPath (Join-Path $path '.lock')) { throw "Test lock present: $path" }
            $files = @(Get-VerifiedFiles $path)
            $bytes = [long](($files | Measure-Object Length -Sum).Sum)
            $count = $files.Count
            if ($count -ne $entry.file_count -or $bytes -ne $entry.size_bytes) { throw "Changed fixture: $path" }
            $children = @(Get-ChildItem -LiteralPath $path -Force)
            if (@(Compare-Object @($children.Name | Sort-Object) @($entry.origin.child | Sort-Object)).Count) { throw "Changed pytest children: $path" }
            foreach ($origin in $entry.origin) {
                if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $origin.retained_xml))) { throw "Missing retained JUnit: $($origin.retained_xml)" }
            }
        }
        # Recheck the absolute boundary immediately before every removal.
        $null = Assert-Contained $path $(if ($target.kind -eq 'archived_source') { $presentationRoot } else { $scratchRoot })
        if ($Apply) {
            $startedDeletion = $true
            if ($target.kind -eq 'archived_scratch') { Remove-Item -LiteralPath $path -Force }
            else { Remove-Item -LiteralPath $path -Recurse -Force }
            if (Test-Path -LiteralPath $path) { throw 'Target remains after removal.' }
        }
        $results.Add(@{path=$path; kind=$target.kind; status=$(if ($Apply) { 'deleted' } else { 'verified' }); files=$count; bytes=$bytes})
    } catch {
        $results.Add(@{path=$target.path; kind=$target.kind; status=$(if ($startedDeletion) { 'failed_or_partial' } else { 'preserved_precheck_failed' }); error=$_.Exception.Message})
        Write-Output "Preserved or interrupted: $($target.path) -- $($_.Exception.Message)"
    }
    @{status='in_progress'; results=$results} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    if ($index % 20 -eq 0) { Write-Output "Processed $index / $($targets.Count) $Category targets ($Context)" }
}
$deleted = @($results | Where-Object status -EQ 'deleted')
@{status='completed'; results=$results; deleted_files=[long](($deleted | Measure-Object files -Sum).Sum); deleted_bytes=[long](($deleted | Measure-Object bytes -Sum).Sum)} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
Write-Output "Finished $Category ($Context): $($deleted.Count) targets deleted."
