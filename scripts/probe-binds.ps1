# probe-binds.ps1 - evaluates every bind of a dash with SimHub's engine (the plugin's local API, read-only).
#
#   powershell -File scripts\probe-binds.ps1 <dash.json> [-Out out\analysis\<name>.probe.json]
#
# For each bind (prop:/ncalc:/js:) and each [Property] used in the formulas, asks SimHub for its current value
# (GET /api/eval and /api/props on http://127.0.0.1:8899). With the sim on track it gives the real values; without a
# game, the last known ones, which is enough to see which properties don't exist in that game (null / error).
param(
    [Parameter(Mandatory = $true)][string]$Dash,
    [string]$Out,
    [string]$Api = 'http://127.0.0.1:8899'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Invoke-Eval([string]$formula) {
    $u = "$Api/api/eval?f=" + [Uri]::EscapeDataString($formula)
    try { return (Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 10).Content | ConvertFrom-Json }
    catch { return [pscustomobject]@{ error = $_.Exception.Message } }
}

$j = Get-Content $Dash -Raw -Encoding UTF8 | ConvertFrom-Json
$game = (Invoke-WebRequest "$Api/api/props?names=DataCorePlugin.CurrentGame,DataCorePlugin.GameRunning,DataCorePlugin.GameData.NewData.CarId" -UseBasicParsing).Content | ConvertFrom-Json

# how many elements use each bind (Bind, ColorBind, Visible, Watch)
$uses = @{}
foreach ($e in $j.Elements) {
    $all = @($e.Bind) + @($e.ColorBind) + @($e.Visible) + @($e.Watch | ForEach-Object { $_.Bind }) | Where-Object { $_ }
    foreach ($b in ($all | Select-Object -Unique)) { $uses[$b] = 1 + [int]$uses[$b] }
}

# the file's "Bindings" list is worked out by the plugin; without it, what the elements use counts
$bindList = if ($j.PSObject.Properties['Bindings'] -and $j.Bindings) { @($j.Bindings) } else { @($uses.Keys) }

$binds = foreach ($b in $bindList) {
    $kind = if ($b -match '^(prop|ncalc|js):') { $Matches[1] } else { 'key' }
    $r = $null
    if ($kind -eq 'prop') {
        $name = $b.Substring(5)
        $v = ((Invoke-WebRequest "$Api/api/props?names=$([Uri]::EscapeDataString($name))" -UseBasicParsing).Content | ConvertFrom-Json).$name
        $r = [pscustomobject]@{ value = $v; type = $(if ($null -eq $v) { 'null' } else { $v.GetType().Name }) }
    }
    elseif ($kind -ne 'key') { $r = Invoke-Eval $b }
    [pscustomobject]@{ bind = $b; kind = $kind; elements = [int]$uses[$b]; value = $r.value; type = $r.type; error = $r.error }
}

# the single properties inside the formulas: [Name] in NCalc, $prop('Name') in JS
$props = @{}
foreach ($b in $bindList) {
    foreach ($m in [regex]::Matches($b, '\[([A-Za-z_][\w\.]*)\]')) { $props[$m.Groups[1].Value] = 1 + [int]$props[$m.Groups[1].Value] }
    foreach ($m in [regex]::Matches($b, "\`$prop\('([^']+)'\)")) { $props[$m.Groups[1].Value] = 1 + [int]$props[$m.Groups[1].Value] }
    if ($b -match '^prop:(.+)$') { $props[$Matches[1]] = 1 + [int]$props[$Matches[1]] }
}
$propRows = foreach ($p in ($props.Keys | Sort-Object)) {
    $r = Invoke-Eval "ncalc:[$p]"
    [pscustomobject]@{ prop = $p; binds = $props[$p]; value = $r.value; type = $r.type; error = $r.error }
}

$result = [pscustomobject]@{ dash = $j.Id; name = $j.Name; game = $game; binds = $binds; props = $propRows }
if (-not $Out) { $Out = "out\analysis\$($j.Id).probe.json" }
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$result | ConvertTo-Json -Depth 6 | Out-File $Out -Encoding utf8

"== $($j.Id)  ($($game.'DataCorePlugin.CurrentGame'), running=$($game.'DataCorePlugin.GameRunning'), car=$($game.'DataCorePlugin.GameData.NewData.CarId'))"
"   binds: $(@($binds).Count)   with an error: $(@($binds | Where-Object error).Count)   null: $(@($binds | Where-Object { -not $_.error -and $_.kind -ne 'key' -and $null -eq $_.value }).Count)"
"   properties: $(@($propRows).Count)   without a value in this game: $(@($propRows | Where-Object { $_.error -or $null -eq $_.value }).Count)"
"   -> $Out"
