# Restore the approved development images from the original base and DSH wheels.
[CmdletBinding()]
param([int]$TimeoutSeconds = 3600)
$ErrorActionPreference = 'Stop'
$repairRepo = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$repairArtifacts = Join-Path $repairRepo '.cache/repair-comparison/dsh/artifacts'
$repairLog = Join-Path $repairArtifacts ('restore-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
$repairBase = 'python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e'
$repairCommon = 'text2ifc/repair-tools:py312-ifc085'
$repairFull = 'text2ifc/repair-tools:py312-ifc085-v2'
$repairDsh = 'text2ifc/repair-dsh:0.2.0rc1'
$repairInstaller = Join-Path $repairRepo 'scripts/ifc_repair/repair_comparison/dsh/install-runtime.sh'
$repairWheels = Join-Path $repairArtifacts 'wheels'
$repairStarted = [DateTime]::UtcNow

function Invoke-RepairDocker {
    param([string[]]$Arguments)
    $repairElapsed = ([DateTime]::UtcNow - $repairStarted).TotalSeconds
    if ($repairElapsed -ge $TimeoutSeconds) { throw 'REBUILD_DEADLINE_EXCEEDED' }
    & docker @Arguments 2>&1 | Tee-Object -FilePath $repairLog -Append
    if ($LASTEXITCODE -ne 0) { throw "Docker failed: $($Arguments[0])" }
}

function Install-RepairImage {
    param([string]$ParentImage, [string]$Image, [string]$Mode)
    $repairName = 'repair-restore-' + $Mode + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
    $repairCommand = if ($Mode -eq 'full') {
        '/opt/venv/bin/python -m pip install --disable-pip-version-check openai==2.43.0 jsonschema==4.26.0 lxml==5.4.0 shapely==2.1.2 ifcdiff==0.8.5 && /opt/venv/bin/python -m pip check'
    } else { 'bash /install-runtime.sh ' + $Mode }
    $repairMounts = @('--mount', "type=bind,source=$repairInstaller,target=/install-runtime.sh,readonly")
    if ($Mode -eq 'dsh') { $repairMounts += @('--mount', "type=bind,source=$repairWheels,target=/wheels,readonly") }
    $repairRemaining = [int]($TimeoutSeconds - ([DateTime]::UtcNow - $repairStarted).TotalSeconds)
    Invoke-RepairDocker -Arguments (@('create', '--name', $repairName, '--pull=never', '--user=0:0', '--cpus=4', '--memory=8g', '--pids-limit=256') +
        $repairMounts + @($ParentImage, 'timeout', '--signal=TERM', '--kill-after=15s', [string]$repairRemaining, 'bash', '-c', $repairCommand))
    try {
        Invoke-RepairDocker -Arguments @('start', '--attach', $repairName)
        $repairExit = & docker inspect $repairName --format '{{.State.ExitCode}}'
        if ($LASTEXITCODE -ne 0 -or $repairExit -ne '0') { throw "INSTALLATION_FAILED: $repairExit" }
        Invoke-RepairDocker -Arguments @('commit', '--change', 'ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin',
            '--change', 'USER 10001:10001', '--change', 'WORKDIR /workspace', $repairName, $Image)
    } finally {
        & docker stop --time 2 $repairName 2>&1 | Out-Null
        & docker rm $repairName 2>&1 | Out-Null
    }
}

$repairExpected = @{
    'deepseek_harness_runtime_bin-0.2.0rc1-py3-none-manylinux_2_28_x86_64.whl' = '9f0b02797b48c21314725649de7feb73936a4df7ad20c770fcb4dbf9002864e1'
    'deepseek_harness_sdk-0.2.0rc1-py3-none-any.whl' = '26896976e1536c87266c34ef192c836fe251c0df2f202f31a5add19bcd04e4e5'
}
foreach ($repairWheel in $repairExpected.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $repairWheels $repairWheel) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $repairExpected[$repairWheel]) {
        throw 'ORIGINAL_DSH_WHEEL_REQUIRED'
    }
}
Invoke-RepairDocker -Arguments @('pull', $repairBase)
Install-RepairImage -ParentImage $repairBase -Image $repairCommon -Mode common
Install-RepairImage -ParentImage $repairCommon -Image $repairFull -Mode full
Install-RepairImage -ParentImage $repairCommon -Image $repairDsh -Mode dsh
Invoke-RepairDocker -Arguments @('image', 'inspect', $repairFull, $repairDsh, '--format', '{{.RepoTags}} {{.Id}}')
Write-Output "REPAIR_IMAGES_RESTORED log=$repairLog elapsed=$(([DateTime]::UtcNow - $repairStarted).TotalSeconds)"
