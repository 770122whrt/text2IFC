$ErrorActionPreference = 'Stop'
$registrationDirectory = $PSScriptRoot
$projectDirectory = [IO.Path]::GetFullPath((Join-Path $registrationDirectory '../../..'))
$reviewedPlan = Get-Content -LiteralPath (Join-Path $registrationDirectory 'deletion-plan.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$journalPath = Join-Path $registrationDirectory 'deletion-journal.jsonl'
if (Test-Path -LiteralPath $journalPath) { throw 'Refusing to overwrite an existing deletion journal' }
$allowedDirectories = @(
    [IO.Path]::GetFullPath((Join-Path $projectDirectory 'dataset/external/RVT')),
    [IO.Path]::GetFullPath((Join-Path $projectDirectory 'dataset/external/bim-whale-ifc-samples'))
)
$seenPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($record in $reviewedPlan.files) {
    $resolvedTarget = [IO.Path]::GetFullPath($record.absolute_path)
    $expectedTarget = [IO.Path]::GetFullPath((Join-Path $projectDirectory $record.path))
    if ($resolvedTarget -ne $expectedTarget) { throw "Path disagreement: $resolvedTarget" }
    if (-not $seenPaths.Add($resolvedTarget)) { throw "Duplicate deletion: $resolvedTarget" }
    $inside = $false
    foreach ($allowedDirectory in $allowedDirectories) {
        if ($resolvedTarget.StartsWith($allowedDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { $inside = $true }
    }
    if (-not $inside) { throw "Target outside authorized directories: $resolvedTarget" }
    $item = Get-Item -LiteralPath $resolvedTarget -Force
    if ($item.PSIsContainer) { throw "Directory deletion is not allowed: $resolvedTarget" }
    $checkPath = $resolvedTarget
    while ($checkPath -ne $projectDirectory) {
        $checkItem = Get-Item -LiteralPath $checkPath -Force
        if (($checkItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point: $checkPath" }
        $checkPath = [IO.Path]::GetDirectoryName($checkPath)
    }
    if ($item.Length -ne $record.size_bytes) { throw "Size changed: $resolvedTarget" }
    if ((Get-FileHash -LiteralPath $resolvedTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw "Hash changed: $resolvedTarget" }
}
Write-Output "Preflight verified $($seenPaths.Count) exact files; no recursive deletion."
foreach ($record in $reviewedPlan.files) {
    $resolvedTarget = [IO.Path]::GetFullPath($record.absolute_path)
    if ((Get-FileHash -LiteralPath $resolvedTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw "Hash changed during deletion: $resolvedTarget" }
    Remove-Item -LiteralPath $resolvedTarget -Force
    if (Test-Path -LiteralPath $resolvedTarget) { throw "Deletion did not complete: $resolvedTarget" }
    [ordered]@{ path=$record.path; sha256=$record.sha256; size_bytes=$record.size_bytes; reason=$record.reason; deleted_at_utc=[DateTime]::UtcNow.ToString('o'); status='deleted' } |
        ConvertTo-Json -Compress | Add-Content -LiteralPath $journalPath -Encoding UTF8
}
Write-Output "Deleted $($seenPaths.Count) reviewed files; journal preserved."
