# patch-iracing.ps1 - makes a copy of a dash made for LMU that works in iRacing.
#
#   powershell -File scripts\patch-iracing.ps1 <dash.json> [-Out out\iracing\<id>.json] [-Id <novo-id>]
#
# Why: in SimHub, an NCalc formula that reads a property the game doesn't have gives null (not false), and the plugin
# hides any element whose condition isn't exactly true. An LMU dash has conditions on LMU-only properties
# (mPitState, mVirtualEnergy, mWheelsNN...), so in iRacing some elements stay hidden for good
# (in the Mercedes-AMG GT3: the gear itself).
#
# What changes (only the binds; layout, pictures and credits stay the same):
#   1. LMU properties with an iRacing/SimHub equivalent are swapped (tyre temperatures and pressures, TC2,
#      anti-roll bars, delta, yellow flag per sector);
#   2. the remaining LMU-only properties become isnull([P], neutral value) inside conditions and formulas, so the
#      condition gives true/false instead of null. A value that is just [P] stays as it is: it shows the dash's "empty" text;
#   3. iRacing's session names ("Lone Qualify", "Offline Testing"...) count as Qualify / Practice.
#
# The result goes to out\ (outside git): the original dashes are other people's and aren't copied into dashes\.
param(
    [Parameter(Mandatory = $true)][string]$Dash,
    [string]$Out,
    [string]$Id,
    [string]$Author = 'Rafael Gomes'
)
$ErrorActionPreference = 'Stop'

$raw = 'GameRawData\.'
$tel = 'DataCorePlugin.GameRawData.Telemetry.'
# wheels in LMU/rF2: 01 = FL, 02 = FR, 03 = RL, 04 = RR
$wheel = @{ '01' = 'FrontLeft'; '02' = 'FrontRight'; '03' = 'RearLeft'; '04' = 'RearRight' }

function ToKpa([string]$corner) {
    "if([TyrePressureUnit]='Psi', [TyrePressure$corner]*6.89476, if([TyrePressureUnit]='Bar', [TyrePressure$corner]*100, [TyrePressure$corner]))"
}

# neutral value of each LMU-only property inside a condition: what lights no warning and hides nothing
$neutral = [ordered]@{
    'PlayerNativeTelemetry\.mVirtualEnergy'      = '1'      # full energy: no low-energy warning
    'CurrentPlayer\.mPitState'                   = '0'      # no pit request
    'CurrentPlayer\.mHeadlights'                 = '0'
    'PlayerNativeTelemetry\.mWiperState'         = '0'
    'PlayerNativeTelemetry\.mLiftAndCoastProgress' = '0'
    'PlayerNativeTelemetry\.mTCSlip'             = '0'
    'Data\.mAvgPathWetness'                      = '0'      # dry
    'Data\.mRaining'                             = '0'
    'CurrentPlayerTelemetry\.mFrontTireCompoundIndex' = '0'
    'Graphics\.LightsStage'                      = '0'      # ACC
}

$stats = [ordered]@{ temps = 0; pressures = 0; remapped = 0; isnull = 0; sessions = 0 }

function Patch-Formula([string]$f, [bool]$isCondition) {
    if ($f -notmatch '^ncalc:') { return $f }
    $o = $f

    # 0. headlights: iRacing doesn't give the lights' state, but it gives the headlight flash (dcHeadlightFlash).
    #    Measured on 2026-10-12: the value is only on for about 70 ms per button press, so the high-beam icon blinks
    #    for 2.5 s after each change of it (changed) instead of following the value. 2 = high beams in LMU, so the
    #    dipped beams (=1) never light.
    #    (Also catches a dash already converted: the property inside isnull(..., 0) or an earlier version of this.)
    $f = $f -replace 'isnull\(\[(?:DataCorePlugin\.)?GameRawData\.CurrentPlayer\.mHeadlights\], 0\)', '[GameRawData.CurrentPlayer.mHeadlights]'
    $f = $f -replace "\(if\((?:changed\(\d+, )?isnull\(\[[\w\.]+dcHeadlightFlash\], 0\)\)? and blink\('flasher', \d+, true\), 2, 0\)\)", '[GameRawData.CurrentPlayer.mHeadlights]'
    $n = [regex]::Matches($f, '\[(?:DataCorePlugin\.)?GameRawData\.CurrentPlayer\.mHeadlights\]').Count
    if ($n) {
        $stats.remapped += $n
        $f = [regex]::Replace($f, '\[(?:DataCorePlugin\.)?GameRawData\.CurrentPlayer\.mHeadlights\]',
            "(if(changed(2500, isnull([${tel}dcHeadlightFlash], 0)) and blink('flasher', 150, true), 2, 0))")
    }

    # 1a. tyre temperature: ((average of the 3 inner layers + carcass) / 2) - 273.15  ->  SimHub's (degC)
    $f = [regex]::Replace($f,
        '\(\(\(\(\[(?:DataCorePlugin\.)?GameRawData\.CurrentPlayerTelemetry\.mWheels\d\d\.mTireInnerLayerTemperature01\][\s\S]*?mWheels(\d\d)\.mTireCarcassTemperature\]\)\s*/2\)\s*-\s*273\.15',
        { param($m) $script:stats.temps++; "[TyreTemperature$($wheel[$m.Groups[1].Value])]" })
    # 1b. tyre pressure (kPa in LMU)
    $f = [regex]::Replace($f, '\[(?:DataCorePlugin\.)?GameRawData\.CurrentPlayerTelemetry\.mWheels(\d\d)\.mPressure\]',
        { param($m) $script:stats.pressures++; '(' + (ToKpa $wheel[$m.Groups[1].Value]) + ')' })
    # 1c. direct equivalents
    $map = [ordered]@{
        "\[(?:DataCorePlugin\.)?${raw}PlayerNativeTelemetry\.mTCCut\]"        = "[${tel}dcTractionControl2]"
        "\[(?:DataCorePlugin\.)?${raw}PlayerNativeTelemetry\.mFrontAntiSway\]" = "[${tel}dcAntiRollFront]"
        "\[(?:DataCorePlugin\.)?${raw}PlayerNativeTelemetry\.mRearAntiSway\]"  = "[${tel}dcAntiRollRear]"
        "\[(?:DataCorePlugin\.)?${raw}\w+\.mDeltaBest\]"                       = '[PersistantTrackerPlugin.SessionBestLiveDeltaSeconds]'
        # rear brake bias (a 0-1 fraction in LMU): what the front leaves
        "\[(?:DataCorePlugin\.)?${raw}CurrentPlayerTelemetry\.mRearBrakeBias\]" = '((100-[BrakeBias])/100)'
        # yellow flag in the car's sector: iRacing doesn't give it per sector, SimHub's yellow it is
        "if\(\[(?:DataCorePlugin\.)?${raw}Data\.mSectorFlag0\d\]=1,1,0\)"      = 'if([Flag_Yellow]=1,1,0)'
    }
    foreach ($k in $map.Keys) {
        $n = [regex]::Matches($f, $k).Count
        if ($n) { $stats.remapped += $n; $f = [regex]::Replace($f, $k, $map[$k]) }
    }

    # 2. what is left LMU-only: isnull(..., neutral). A value that is just the property stays as it is (shows "empty").
    $bare = $f -match '^ncalc:\s*\[[^\[\]]+\]\s*(\*\s*[\d\.]+)?\s*$'
    if ($isCondition -or -not $bare) {
        foreach ($k in $neutral.Keys) {
            $f = [regex]::Replace($f, "(?<!isnull\()\[(?:DataCorePlugin\.)?${raw}$k\]",
                { param($m) $script:stats.isnull++; "isnull($($m.Value), $($neutral[$k]))" })
        }
        # TC2 and the anti-roll bars don't exist in every iRacing car
        $f = [regex]::Replace($f, "(?<!isnull\()\[$([regex]::Escape($tel))dc(TractionControl2|AntiRollFront|AntiRollRear)\]",
            { param($m) $script:stats.isnull++; "isnull($($m.Value), 0)" })
        $f = [regex]::Replace($f, '(?<!isnull\()\[lmuDataPlugin\.[^\]]+\]',
            { param($m) $script:stats.isnull++; "isnull($($m.Value), 0)" })
    }

    # 3. iRacing's session names
    $q = "([SessionTypeName]='Qualify' or [SessionTypeName]='Lone Qualify' or [SessionTypeName]='Open Qualify')"
    $p = "([SessionTypeName]='Practice' or [SessionTypeName]='Offline Testing' or [SessionTypeName]='Lone Practice' or [SessionTypeName]='Warmup')"
    $n = [regex]::Matches($f, "\[SessionTypeName\]\s*=\s*'(Qualify|Practice)'").Count
    if ($n -and $f -notmatch "Lone Qualify|Offline Testing") {   # already converted: don't widen again
        $stats.sessions += $n
        $f = [regex]::Replace($f, "\[SessionTypeName\]\s*=\s*'Qualify'", $q)
        $f = [regex]::Replace($f, "\[SessionTypeName\]\s*=\s*'Practice'", $p)
    }
    return $f
}

function Patch-List($v, [bool]$isCondition) {
    if ($null -eq $v) { return $null }
    if ($v -is [string]) { return (Patch-Formula $v $isCondition) }
    return , @($v | ForEach-Object { Patch-Formula $_ $isCondition })
}

$j = Get-Content $Dash -Raw -Encoding UTF8 | ConvertFrom-Json
$oldId = $j.Id
if (-not $Id) { $Id = ($oldId -replace '^lib-', '' -replace '-iracing$', '') + '-iracing' }

foreach ($e in $j.Elements) {
    if ($e.PSObject.Properties['Visible'] -and $null -ne $e.Visible) { $e.Visible = Patch-List $e.Visible $true }
    if ($e.Bind) { $e.Bind = Patch-Formula $e.Bind $false }
    if ($e.ColorBind) { $e.ColorBind = Patch-Formula $e.ColorBind $true }
    if ($e.PSObject.Properties['Watch'] -and $e.Watch) { foreach ($w in $e.Watch) { if ($w.Bind) { $w.Bind = Patch-Formula $w.Bind $false } } }
}

$j.Id = $Id
# the name and author say this version is ours; the original's credit stays in the author, Source and description
$j.Name = "iRacing - " + ($j.Name -replace '^(iRacing - )+', '' -replace '^LMGT3 ', '' -replace ' \(iRacing\)$', '')
if ($j.Author -and $j.Author -notmatch [regex]::Escape($Author)) { $j.Author = "$Author (iRacing) / original: $($j.Author)" }
elseif (-not $j.Author) { $j | Add-Member -NotePropertyName Author -NotePropertyValue "$Author (iRacing)" -Force }
$note = "iRacing: LMU-only properties swapped or made neutral (scripts/patch-iracing.ps1). "
$oldNote = "iRacing: propriedades exclusivas do LMU trocadas ou neutralizadas (scripts/patch-iracing.ps1). "   # earlier copies
if ("$($j.Description)".StartsWith($oldNote)) { $j.Description = "$($j.Description)".Substring($oldNote.Length) }
if (-not "$($j.Description)".StartsWith($note)) { $j.Description = $note + $j.Description }
$j.PSObject.Properties.Remove('Bindings')   # worked out by the plugin from the elements

if (-not $Out) { $Out = "out\iracing\$Id.json" }
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
# no BOM: the plugin reads UTF-8
[IO.File]::WriteAllText((Join-Path (Get-Location) $Out), ($j | ConvertTo-Json -Depth 12 -Compress), (New-Object Text.UTF8Encoding $false))

"== $oldId -> $Id"
"   tyre temps: $($stats.temps)   tyre pressures: $($stats.pressures)   direct equivalents: $($stats.remapped)   isnull: $($stats.isnull)   session names: $($stats.sessions)"
"   -> $Out ($([Math]::Round((Get-Item $Out).Length / 1KB)) KB)"
