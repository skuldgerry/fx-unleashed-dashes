# iRacing GT3 shift lights: audit and plan

Made on 2026-10-12: what the car light database said about each car, compared with that car's iRacing manual, and then
with the sim itself.

## State

- **Since FX Unleashed 0.7.6** the plugin reads iRacing cars' own shift lights from the sim's files: each light's rpm and
  colour per gear, colour stages, lights switched off again, the blink frame by frame and the pit limiter's look. For
  iRacing that replaces Lovely Car Data, and it matches what was measured here by hand (below). The rest of this page is
  the record of how it was found.
- **BMW M4 GT3**: measured in the sim, not from the manual (which describes an older version of the car).
  `scripts/capture_shiftlights.py` recorded the light bar over a lap of the Nordschleife, 8460 frames with rpm and gear.
  The bar lights in blocks: 5 green, 5 light blue, all red, and near the limiter two white dots in the middle, 300-400 rpm
  past the red. The 0.7.6 data agrees (2nd gear: red at 6747, the dots at 7147).
- **McLaren 720S GT3**: measured in the sim (2674 frames of the car's dash with rpm and gear). The database was right up to
  all blue; then the bar turns red and blue on every other light (ends red), steady, one step of the car's own light
  spacing after the blue in every gear: +250 rpm in 1st, +203 in 2nd, +181 in 3rd, +150 in 4th, +119 in 5th. The 0.7.6
  data agrees (2nd gear: blue at 7053, red and blue at 7250; measured 7256).
- **Mercedes-AMG**: flash interval tried at 100 ms instead of 300 (in a local copy of the data, `scripts/fix_cardata.py`).
- **Ferrari 296**: whether its shift flash blinks is still to be seen.
- **Lamborghini**: matches; the shift flash's blue could be a little darker.
- **Audi R8 and Aston Martin**: not driven (cars not owned).
- **Lesson**: measure in the sim. Manuals go out of date.

## Where the lights come from

- With "Use the car's real rev lights when known" on, FX Unleashed uses its own car light database first (for iRacing,
  read from the sim since 0.7.6), then **Lovely Car Data** (`github.com/Lovely-Sim-Racing/lovely-car-data`,
  `data/iracing/<carId>.json`, CC BY-NC-SA 4.0), keeping a copy in `SimHub\PluginsData\Common\FXProRpmSync\cars\`.
- Lovely Car Data also feeds the Lovely Dashboard and other wheels and dashes. A fix there fixes it for everyone; they take
  pull requests (with `pre-commit` hooks that validate and format the JSON).
- Its format per car: `ledNumber`, `ledColor` (the first colour is the shift flash's, then one per light), `ledRpm` per
  gear (the first value is the flash rpm, then one per light) and `redlineBlinkInterval` (ms between on and off; 0 =
  steady). The plugin blinks at `1000 / (2 x interval)` times a second.

### What that format can't express

- **Two colours** at the shift point (McLaren 720S).
- **A stage after the shift point** (Corvette: all red at the shift point, blue near the limiter).
- A light that changes colour with the rpm.

The plugin's own iRacing data (0.7.6) expresses all three.

## Audit (database against the iRacing manuals)

| Car | Database | iRacing manual | Difference |
|---|---|---|---|
| Aston Martin Vantage EVO | 8 lights (4 green, 3 yellow, 1 blue); red flash 3.3/s; per gear 6900-6975 | doesn't describe the shift lights | no reference: check on track |
| Audi R8 LMS EVO II | 10 lights (4 green, 2 yellow, 2 orange, 2 red); red flash 2/s at 8050-8340 | "upshift when the final red light in the 10-LED sequence is illuminated" | the manual says shift at the last red light (8000-8190 in the database); the database's flash comes 50-150 rpm later |
| BMW M4 GT3 | 10 lights (5 green, 5 light blue); steady red flash; per gear 6725-7250 | 2 green, 6 yellow, 2 orange, all red at 6800, the same in every gear | **colours and rpm differ**; measured in the sim: see above |
| Corvette Z06 GT3.R | 8 lights (3 green, 2 yellow, 1 orange, 2 red); red flash 1.7/s at 7675 | all red at the shift point; past it, red to blue near the limiter | the blue stage is missing |
| Ferrari 296 GT3 | 6 lights (2 green, 2 yellow, 2 red); red flash 2/s; per gear 7350-7900 | left to right, all red at the shift point; no rpm | the manual doesn't mention blinking |
| Ford Mustang GT3 | 10 lights outside in (8 green, 2 blue in the middle); blue flash 2/s at 8000 (8250 in 6th) | outside in, all blue at the shift point | matches |
| Lamborghini Huracán EVO | 10 lights (4 green, 2 yellow, 4 red) at 6650-8000; steady blue flash at 8000 | 4 green, 2 yellow, 3 red, all blue at 8000 | matches, but for a 10th red light the manual doesn't list |
| McLaren 720S GT3 | 10 lights (2 green, 2 yellow, 2 orange, 2 red, 2 blue); steady blue flash; per gear 6858-8000 | all blue as the shift point nears; **blue and red alternating** at the shift point | the blue and red stage is missing; measured: see above |
| Mercedes-AMG GT3 | 10 lights outside in (green, yellow, red); red flash 1.7/s; per gear 7000-7600 | 2 green 6180, 4 green 6350, 2 yellow 6520, 4 yellow 6690, 2 red 6860, all red blinking 7030 | the database's 3rd gear is exactly the manual's table; the blink exists but is slow |
| Porsche 911 GT3 R (992) | 16 lights outside in (green, yellow, red); blue flash 2/s; per gear 8777-9200 | outside in, green to red; all blue blinking at the shift point | matches |

### Blink rate

| Database interval | Blinks per second | Cars |
|---|---|---|
| 150 ms | 3.3 | Aston Martin |
| 250 ms | 2 | Audi, Ferrari 296, Mustang, Porsche |
| 300 ms | 1.7 | Corvette, Mercedes-AMG |
| 0 | steady | BMW, Lamborghini, McLaren |

At 1.7-2 blinks a second a quick shift barely shows a blink.

## What iRacing gives as telemetry

iRacing publishes four shift-light rpm values per car (`DriverCarSLFirstRPM`, `SLShiftRPM`, `SLLastRPM`, `SLBlinkRPM`) and
the limiter (`DriverCarRedLine`). They are **not** when the car's dash lights come on (Lamborghini: 7300 / 8050 / 8100 /
8150 against 6650-8000 on its dash); they serve as a reference for the limiter and a generic shift point only.

## Method

1. **Measure before changing**, per car, in a test session: log the telemetry values above; record the car's dash on a
   straight, revving slowly in 2nd to 5th (`scripts/capture_shiftlights.py`, with `--bbox` for just the light bar); read
   off when each light comes on in each gear, the colours, whether the flash blinks and how fast.
2. **Try a fix on the wheel first**: the plugin's per-car adjustments (Car tuning) override the database and are undone by
   deleting them.
3. **Propose it to the database**: one car per pull request to Lovely Car Data, with the measurement. Only by decision of
   the repository owner, request by request: it changes the lights of everyone who uses that data.
