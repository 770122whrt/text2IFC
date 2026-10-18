param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('core', 'retry', 'missing-usage', 'subagent', 'truncated', 'hang', 'compaction')]
    [string]$Case
)
$ErrorActionPreference = 'Stop'
$repairRepo = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$repairRun = Join-Path $repairRepo ".tmp/repair-comparison-isolation/dsh-$Case"
$repairName = "text2ifc-repair-dsh-$Case-native"
$repairVolume = "text2ifc-repair-dsh-$Case-state"

function Invoke-RepairDocker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "docker failed: $($args[0]) ($LASTEXITCODE)" }
}

# Installation is deliberately separate. This entry has no real-model option.
$repairNetwork = Invoke-RepairDocker network inspect text2ifc-repair-offline | ConvertFrom-Json
if (-not $repairNetwork[0].Internal) { throw 'Offline network must be internal' }
Invoke-RepairDocker image inspect text2ifc/repair-dsh:0.2.0rc1 | Out-Null
New-Item -ItemType Directory -Force -Path "$repairRun/workspace" | Out-Null
Invoke-RepairDocker volume create --label text2ifc.experiment=repair-comparison $repairVolume | Out-Null
Invoke-RepairDocker run --rm --pull never --network none --user 0:0 --cap-drop ALL --cap-add CHOWN --security-opt no-new-privileges `
    --cpus 1 --memory 128m --pids-limit 32 `
    --mount "type=volume,source=$repairVolume,target=/state" text2ifc/repair-tools:py312-ifc085 `
    python -c "import os; assert not os.listdir('/state'), 'existing state is not a fresh session'; os.chown('/state',10001,10001)" | Out-Null
Invoke-RepairDocker run -d --pull never --name $repairName --label text2ifc.experiment=repair-comparison `
    --network text2ifc-repair-offline --read-only --cap-drop ALL --security-opt no-new-privileges `
    --env SHELL=/bin/bash --cpus 4 --memory 8g --memory-swap 8g --pids-limit 512 `
    --tmpfs '/tmp:rw,exec,nosuid,size=1g' `
    --mount "type=bind,source=$repairRepo/tests/ifc_repair/repair_comparison/dsh_runtime_probe.py,target=/opt/probe/run.py,readonly" `
    --mount "type=bind,source=$PSScriptRoot/question-bridge.mjs,target=/opt/probe/question-bridge.mjs,readonly" `
    --mount "type=bind,source=$repairRun/workspace,target=/workspace" `
    --mount "type=volume,source=$repairVolume,target=/state" `
    text2ifc/repair-dsh:0.2.0rc1 timeout --signal=TERM --kill-after=5s 150 python /opt/probe/run.py $Case
# The caller checks status, exports evidence, and stops the whole hang container.
# Existing names/volumes are never silently cleaned or treated as fresh sessions.
