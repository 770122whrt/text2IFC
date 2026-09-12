param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'retirement.json') -Encoding UTF8 | ConvertFrom-Json
$tests = Get-Content -LiteralPath (Join-Path $PSScriptRoot $manifest.pytest_manifest) -Encoding UTF8 | ConvertFrom-Json
$proofRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot $manifest.archive))
$proof = Get-Content -LiteralPath (Join-Path $proofRoot 'manifest.json') -Encoding UTF8 | ConvertFrom-Json

function Assert-Contained([string]$Path, [string]$Root) {
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Outside authorized root: $resolved"
    }
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
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) {
        throw "Changed bytes: $Path"
    }
}

$operations = [Collections.Generic.List[object]]::new()
# Real evidence: every source file must either be in the frozen archive or the
# exact rebuildable-cache list. The archive is checked again before removal.
foreach ($source in $manifest.directories) {
    $path = Assert-Contained $source.path (Join-Path $repoRoot 'dataset/processed/ifc-presentation-validation')
    $bundle = @($proof.legacy_bundles | Where-Object id -EQ $source.bundle)
    if ($bundle.Count -ne 1) { throw 'Bundle must resolve exactly once.' }
    $expected = @($bundle[0].entries) + @($source.excluded_cache_files)
    $actual = @(Get-ChildItem -LiteralPath $path -Force -Recurse)
    if (@($actual | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw "Linked source: $path" }
    $files = @($actual | Where-Object { -not $_.PSIsContainer })
    if ($files.Count -ne $expected.Count) { throw "Changed source file set: $path" }
    foreach ($entry in $expected) {
        $item = Assert-Contained (Join-Path $path $entry.legacy_path) $path
        Assert-Bytes $item $entry
    }
    foreach ($entry in $bundle[0].entries) {
        $retained = Assert-Contained (Join-Path $proofRoot $entry.path) $proofRoot
        Assert-Bytes $retained $entry
    }
    $operations.Add(@{path=$path; directory=$true; files=$files.Count; bytes=[long](($files | Measure-Object Length -Sum).Sum); kind='archived_source'})
    Write-Output "Verified archived source: $path"
}
# Test fixtures: bounded path, closed .lock state, no links, unchanged size/count.
# No broad hashing of reproducible pytest files is needed.
foreach ($source in $tests.directories) {
    $path = Assert-Contained $source.path (Join-Path $repoRoot '.tmp')
    if (Test-Path -LiteralPath (Join-Path $path '.lock')) { throw "Test lock present: $path" }
    $actual = @(Get-ChildItem -LiteralPath $path -Force -Recurse)
    if (@($actual | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw "Linked fixture: $path" }
    $files = @($actual | Where-Object { -not $_.PSIsContainer })
    $size = [long](($files | Measure-Object Length -Sum).Sum)
    if ($files.Count -ne $source.file_count -or $size -ne $source.size_bytes) { throw "Changed fixture: $path" }
    $children = @(Get-ChildItem -LiteralPath $path -Force)
    if (@(Compare-Object @($children.Name | Sort-Object) @($source.origin.child | Sort-Object)).Count) {
        throw "Changed pytest children: $path"
    }
    $operations.Add(@{path=$path; directory=$true; files=$files.Count; bytes=$size; kind='rebuildable_pytest'})
    if ($operations.Count % 20 -eq 0) { Write-Output "Verified $($operations.Count) authorized directory targets" }
}
foreach ($source in $manifest.duplicate_scratch_files) {
    $path = Assert-Contained $source.path (Join-Path $repoRoot '.tmp')
    $retained = Assert-Contained (Join-Path $repoRoot $source.retained) $repoRoot
    Assert-Bytes $path $source
    Assert-Bytes $retained $source
    $operations.Add(@{path=$path; directory=$false; files=1; bytes=$source.size_bytes; kind='identical_duplicate'})
}
$precheck = @{status='passed'; operations=$operations.Count; files=($operations | Measure-Object files -Sum).Sum; bytes=($operations | Measure-Object bytes -Sum).Sum}
$precheck | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-precheck.json') -Encoding UTF8
if (-not $Apply) { $precheck | ConvertTo-Json; return }

$results = [Collections.Generic.List[object]]::new()
$index = 0
foreach ($op in $operations) {
    $index++
    try {
        if ($op.directory) { Remove-Item -LiteralPath $op.path -Recurse -Force }
        else { Remove-Item -LiteralPath $op.path -Force }
        if (Test-Path -LiteralPath $op.path) { throw 'Target remains after removal.' }
        $results.Add(@{path=$op.path; status='deleted'; files=$op.files; bytes=$op.bytes; kind=$op.kind})
    } catch {
        $results.Add(@{path=$op.path; status='failed_or_partial'; error=$_.Exception.Message; kind=$op.kind})
        @{status='interrupted'; results=$results} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-result.json') -Encoding UTF8
        throw
    }
    @{status='in_progress'; results=$results} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-result.json') -Encoding UTF8
    if ($index % 10 -eq 0) { Write-Output "Retired $index / $($operations.Count) approved targets" }
}
@{status='completed'; results=$results; deleted_files=($results | Measure-Object files -Sum).Sum; deleted_bytes=($results | Measure-Object bytes -Sum).Sum} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deletion-result.json') -Encoding UTF8
Write-Output 'Approved retirement complete.'
