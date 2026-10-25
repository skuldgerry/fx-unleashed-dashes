# Project context

What this project is, how it works and where it stands, so work can pick up in a new session or on another PC.
`CLAUDE.md` at the root points here.

## Setup it was made on

- A **Simagic FX Pro** (800x480 screen) on an Alpha Ultimate base, running the FX Unleashed custom firmware in
  **Unleashed (USB) mode**, with the SimHub plugin (FX Unleashed 0.7.3, now **FX Unleashed Enhanced** on 0.7.6) on SimHub
  9.13.2. Other SimHub plugins alongside: Lovely, Control Mapper, DNRLEDs.
- Target sim: **iRacing** (GT3). Assetto Corsa and Le Mans Ultimate are used too.
- The screen's picture memory (RAM drive) is on.

## Goals

1. **Recreate the real dashes of iRacing's GT3 cars**: what each car shows on its own display, one dash per car.
2. **A default dash** in the spirit of the Lovely Dashboard, for every other car.

### The bug that started it

FX Unleashed ships Redadeg's Mercedes-AMG GT3 dash (a 1:1 conversion of his SimHub dash from lmu-dashboards.com, made for
**Le Mans Ultimate**). In iRacing it **didn't follow gear changes**.

Diagnosis (2026-10-11, static analysis plus SimHub's formula engine, then confirmed on track):
- The gear itself is right: `gearText` comes from `GameData.Gear`, the same in every game.
- What fails is **visibility**. The Mercedes' `GearText` element has the condition
  `ncalc:!([GameRawData.CurrentPlayer.mPitState]=1)`. `mPitState` only exists in LMU; in iRacing SimHub's NCalc returns
  **null** (not false) for any comparison with a property that doesn't exist, and the plugin hides an element whose
  condition isn't exactly true. So in iRacing the gear stays hidden.
- The null rules, checked with `GET /api/eval`: `[P]=1` gives null; `!(...)` of null gives null; `A and [P]=1` gives null
  (false only if `A` is already false); `changed(ms, [P])` gives false; `isnull([P], 0)=1` gives false. The fix is
  `isnull([P], neutral)`.
- The same in the other LMU dashes: Ferrari 296 (50 elements hidden: tyre pressures and temperatures, warnings), Porsche
  911 (27: delta, tyre and energy warnings, pit arrows).
- Also without data in iRacing: virtual energy, TC slip, wipers, headlights, wet track; `[SessionTypeName]='Qualify'` is
  never true (iRacing says "Lone Qualify" / "Open Qualify" / "Offline Testing").
- `scripts/probe-binds.ps1` lists what gives null in a dash; `scripts/patch-iracing.ps1` writes the fixed copy to
  `out/iracing/`.

## How it works

- A dash is JSON (FormatVersion 2-4) for an 800x480 RGB565 screen, default pad 10,20 (usable 790x460). Elements:
  rect / ellipse / box / gradient / image / label / value / bar / deltabar / popup / dim. Binds: keys (`gearText`, `speed`,
  `rpm`...), `prop:`, `ncalc:`, `js:` (restricted). `Visible`, `PreviewVisible`, `ColorBind`/`ColorStops`,
  `Pages`/`PageSets`.
- Per-car key: `"Game | CarId"` (e.g. `IRacing | bmwm4gt3`). In USB mode each car has a list of dashes; the FX Pro shows
  the first. The plugin logs each car as `[FXProRpmSync] car {Game | CarId}: {source}; rev LEDs at ...`.
- Limits: screen link ~25 KB/s; picture memory 384 KB (336 KB usable, 512 B per file).
- Tool: `fxdash` (C#, built with SimHub installed): `check`, `fit-bands`, `verify`, `render`, `import`, `tune`,
  `package`, `bindings`, `schema`. Four gates before a dash is done (`docs/reference/create-dash-SKILL.md`). With SimHub
  open the plugin serves the same checks at `http://127.0.0.1:8899/api` (`scripts/gates_api.py`), no `fxdash.exe` needed.
- Installing a dash: copy `<Id>.json` to `C:\Program Files (x86)\SimHub\PluginsData\Common\FXProRpmSync\Dashes\`.
- The plugin: https://github.com/fxunleashed/fx-unleashed (GPL-3.0). Useful examples in its `tools/dashes/` and
  `Usb/Bundled/`.

## State

### Dashes

| Car (iRacing) | Car id | Dash | How it was made | Driven |
|---|---|---|---|---|
| Mercedes-AMG GT3 | `mercedesamgevogt3` | `lmgt3-mercedes-amg-gt3-iracing` | converted from LMU (Redadeg) | yes, approved |
| Ferrari 296 GT3 | `ferrari296gt3` | `lmgt3-ferrari-296-iracing` | converted | yes, approved |
| Porsche 911 GT3 R (992) | `porsche992rgt3` | `lmgt3-porsche-911-gt3-r-iracing` | converted | yes, approved |
| Ford Mustang GT3 | `fordmustanggt3` | `lmgt3-mustang-iracing` | converted (the plugin's built-in) | yes, approved |
| McLaren 720S GT3 | `mclaren720sgt3` | `lmgt3-mclaren-720s-iracing` | converted, then brought to the car's iRacing display (`scripts/patch_mclaren_720s.py`) | yes |
| Aston Martin Vantage GT3 EVO | `amvantageevogt3` | `lmgt3-aston-martin-iracing` | converted (built-in) | no |
| BMW M4 GT3 | `bmwm4gt3` | `bmw-m4-gt3-iracing` | from scratch, redone from a frame of the sim (the 2024 manual is out of date) | yes |
| Audi R8 LMS EVO II | `audir8lmsevo2gt3` | `audi-r8-lms-gt3-iracing` | from scratch | no (render approved) |
| Lamborghini Huracán GT3 EVO | `lamborghinievogt3` | `lamborghini-huracan-gt3-iracing` | from scratch (day page) | yes |
| Corvette Z06 GT3.R | `chevyvettez06rgt3` | `corvette-z06-gt3r-iracing` | from scratch, drawn background | to confirm |
| any other car | - | `gt-default` | from scratch, based on the Lovely Dashboard's layout | yes; the default dash |

- Car ids come from the plugin's car light database, never invented.
- **Converted**: `scripts/patch-iracing.ps1` swaps the LMU-only properties (see the diagnosis) and marks name and author
  ("iRacing - <car>", "skuldgerry (iRacing) / original: Redadeg"). They live only in `out/iracing/` and in SimHub.
- **From scratch**: one `scripts/make_<car>.py` each, common parts in `scripts/dashkit.py`. They write to `dashes/` (the
  repository version, no third-party material) and, when a logo is in `reference/logos/`, also to `out/local/` (the
  version with the logo, the one installed).
- The from-scratch dashes show setting changes (TC, ABS, brake bias, throttle map where there is one) and a start-up
  sequence with the logo (ignition off / "SYSTEM CHECK"). **Neither comes from iRacing's manuals**, which don't describe
  them: they were asked for. `gt-default` has no start-up sequence (some games don't report the ignition).
- Fonts chosen on the wheel: 94 for labels, 110 for numbers, 90 for the M4's speed.
- Corvette: `check` warns that its background takes ~11 s to draw on a wheel without picture memory.

### Shift lights

- Audit of the ten GT3s, measurements and plan: `docs/rev-lights-plan.md`.
- Since FX Unleashed 0.7.6 the plugin reads iRacing cars' own shift lights from the sim's files (per gear, colour
  stages, the blink, the pit limiter). That covers what was measured here by hand (the McLaren 720S's blue then red and
  blue, the BMW M4's two white dots).
- Measuring in the sim: `scripts/capture_shiftlights.py` records the screen (or only the light bar) with the rpm and gear
  of each frame; `scripts/watch_prop.py` logs every change of a SimHub property.
- Headlight flash in iRacing: `dcHeadlightFlash` is only true for ~70 ms per press. The converted dashes' and the
  Corvette's high-beam icons blink for 2.5 s after each change of it.

### Not in git

`.deps/`, `out/` and `reference/` (see `.gitignore`): the plugin's code, iRacing manuals, brand logos, dashes converted
from other people's work, versions with logos, copies of Lovely Car Data.

## To do

- Corvette: confirm on the wheel; panel highlights if the look is kept; the colour behind the numbers.
- Lamborghini: the shift flash's blue a little darker; night and qualifying pages.
- Aston Martin and Audi: not driven (cars not owned).
