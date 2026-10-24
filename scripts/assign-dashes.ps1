# assign-dashes.ps1 - adds the iRacing GT3 cars to FX Unleashed, each with its own dash.
#
#   powershell -ExecutionPolicy Bypass -File scripts\assign-dashes.ps1 [-WhatIf] [-Default gt-default]
#
# Writes into the plugin's settings file (Usb.CarDashes). SimHub rewrites that file when it closes, so this only runs
# with SimHub CLOSED; it keeps a copy next to it first (.bak-<date>).
# It never touches a car that already has dashes, or anything else in the settings.
#
# The car ids are those of the car light database the plugin uses (never invented).
param(
    [switch]$WhatIf,
    # id of a dash to make the default dash (first in the list); empty = leave it
    [string]$Default
)
$ErrorActionPreference = 'Stop'

$settings = 'C:\Program Files (x86)\SimHub\PluginsData\Common\FXProRpmSyncPlugin.GeneralSettings.json'
$dashDir = 'C:\Program Files (x86)\SimHub\PluginsData\Common\FXProRpmSync\Dashes'
$cars = [ordered]@{
    'mercedesamgevogt3' = @('Mercedes-AMG GT3 2020', 'lmgt3-mercedes-amg-gt3-iracing')
    'ferrari296gt3'     = @('Ferrari 296 GT3', 'lmgt3-ferrari-296-iracing')
    'porsche992rgt3'    = @('Porsche 911 GT3 R (992)', 'lmgt3-porsche-911-gt3-r-iracing')
    'fordmustanggt3'    = @('Ford Mustang GT3', 'lmgt3-mustang-iracing')
    'bmwm4gt3'          = @('BMW M4 GT3', 'bmw-m4-gt3-iracing')
    'amvantageevogt3'   = @('Aston Martin Vantage GT3 EVO', 'lmgt3-aston-martin-iracing')
    'mclaren720sgt3'    = @('McLaren 720S GT3', 'lmgt3-mclaren-720s-iracing')
    'audir8lmsevo2gt3'  = @('Audi R8 LMS EVO II GT3', 'audi-r8-lms-gt3-iracing')
    'lamborghinievogt3' = @('Lamborghini Huracan GT3 EVO', 'lamborghini-huracan-gt3-iracing')
    'chevyvettez06rgt3' = @('Chevrolet Corvette Z06 GT3.R', 'corvette-z06-gt3r-iracing')
}

if (-not $WhatIf -and (Get-Process SimHubWPF -ErrorAction SilentlyContinue)) {
    throw 'SimHub is open: close it first (it rewrites the settings when it closes). With -WhatIf this only shows what it would do.'
}

$j = Get-Content $settings -Raw -Encoding UTF8 | ConvertFrom-Json
$map = $j.Usb.CarDashes
$changed = $false
foreach ($id in $cars.Keys) {
    $name, $dash = $cars[$id]
    $key = "IRacing | $id"
    if (-not (Test-Path "$dashDir\$dash.json")) { "  dash $dash missing: $name left as it is"; continue }
    $have = $map.PSObject.Properties[$key]
    if ($have -and @($have.Value.Dashes).Count -gt 0) { "  already set: $name -> $(@($have.Value.Dashes) -join ', ')"; continue }
    $entry = [pscustomobject]@{ CarKey = $key; Game = 'IRacing'; CarId = $id; CarName = $name; Dashes = @("c:$dash")
        Current = 0; UpdatedUtc = (Get-Date).ToUniversalTime().ToString('o'); WheelDash = $false; DashId = $null }
    $map | Add-Member -NotePropertyName $key -NotePropertyValue $entry -Force
    "  new:    $name -> $dash"
    $changed = $true
}
if ($Default) {
    if (-not (Test-Path "$dashDir\$Default.json")) { throw "There is no dash $Default" }
    $ref = "c:$Default"
    $list = @($j.Usb.DefaultDashes | Where-Object { $_ -and $_ -ne $ref })
    if (@($j.Usb.DefaultDashes)[0] -ne $ref) {
        $j.Usb.DefaultDashes = @($ref) + $list
        $j.Usb.DefaultCurrent = 0
        "  default: $Default (before: $($list -join ', '))"
        $changed = $true
    } else { "  default: already $Default" }
}

if (-not $changed) { 'Nothing to change.'; return }
if ($WhatIf) { '(-WhatIf: nothing saved)'; return }
$backup = "$settings.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item $settings $backup
[IO.File]::WriteAllText($settings, ($j | ConvertTo-Json -Depth 30), (New-Object Text.UTF8Encoding $false))
"Saved. Copy of the previous file: $backup"
