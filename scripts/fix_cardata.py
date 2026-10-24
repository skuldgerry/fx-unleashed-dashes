#!/usr/bin/env python3
"""fix_cardata.py - corrects iRacing cars' shift lights in the local copy of Lovely Car Data.

  python scripts/fix_cardata.py            applies the corrections
  python scripts/fix_cardata.py --restore  puts the original files back

Since FX Unleashed 0.7.6 the plugin reads iRacing cars' shift lights from the sim's own files first, so for iRacing this
only matters with an older plugin, or for a car missing from that data. Kept as the record of the measurements.

FX Unleashed reads each car's lights from SimHub/PluginsData/Common/FXProRpmSync/cars/iracing_<carId>.json, a copy of
Lovely Car Data that it downloads again when it is more than 7 days old. For the correction to stay, the corrected file
is saved with a 2099 date (the plugin always sees it as recent). To go back: --restore, or delete the file (the plugin
downloads it again).

The originals go to reference/cardata/original/ and the corrected ones to reference/cardata/iracing/ (outside git: they
are derived from Lovely Car Data, CC BY-NC-SA 4.0), ready to propose to the database. See docs/rev-lights-plan.md.

The plugin reads the file when the car loads: after running this, leave the car and get in again.
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\FXProRpmSync\cars")
ORIGINAL = ROOT / "reference" / "cardata" / "original"
FIXED = ROOT / "reference" / "cardata" / "iracing"
YEAR_2099 = 4070908800   # 2099-01-01 UTC


def bmw_m4(d):
    """Measured in the sim on 2026-10-12 (scripts/capture_shiftlights.py): a lap of the Nordschleife, 8460 frames of the
    light bar at 15 a second, each with its rpm and gear; only the full-throttle ones count.
    The car's bar doesn't light one LED at a time: the 5 greens come on together, then the 5 blues, then all red, and
    near the limiter it goes out but for 2 white dots in the middle. The database's colours were right (5 green, 5 light
    blue); its rpm weren't: it lit one LED at a time from 4800 and put the red at 6725-7250, on top of the limiter.

        gear   green    blue    red      white dots
        1st    ~5400    6050    ~6620    -          (few frames)
        2nd     5955    6335     6605    ~7000
        3rd     5950    6265     6590    ~6920
        4th     6120    6405     6675    ~6900
        5th     6070    6305     6550    -          (didn't get there)
        6th    <6360   >6780       ?     -          (only 112 frames, all green)

    6th is an estimate: green 6350, blue 6800, red 7050. Neutral and reverse take 1st's.
    The white dots don't fit the format (a single shift colour); FX Unleashed 0.7.6 shows them from the sim's data.
    iRacing's 2024 manual (green, yellow, orange, red at 6800) describes an earlier version of the car.
    12 positions, the 3rd and the 10th empty (the bar's two gaps)."""
    def row(green, blue, red):
        return [red, green, green, 0, green, green, green, blue, blue, blue, 0, blue, blue]
    gears = {"1": row(5400, 6050, 6620), "2": row(5955, 6335, 6605), "3": row(5950, 6265, 6590),
             "4": row(6120, 6405, 6675), "5": row(6070, 6305, 6550), "6": row(6350, 6800, 7050)}
    gears["R"] = gears["N"] = gears["1"]
    d["redlineBlinkInterval"] = 0
    d["ledRpm"] = [{g: list(gears.get(g, gears["3"])) for g in d["ledRpm"][0]}]


def mercedes_amg(d):
    """The rpm match iRacing's manual ("All Red Flashing - 7030 rpm"). Only the rhythm: 300 ms gave 1.7 blinks a second,
    which a quick shift never shows. 100 ms = 5 a second.
    The car's real rhythm isn't in the manual: it's a choice, to tune on track."""
    d["redlineBlinkInterval"] = 100


FIXES = {"bmwm4gt3": bmw_m4, "mercedesamgevogt3": mercedes_amg}

# A lead on the wheel's copy only, in rpm (negative = earlier): the wheel's lights arrive a moment after the sim's
# (telemetry and USB), and revving up that shows as "the sim gets there first". Not in the version to propose to Lovely
# Car Data, which keeps the car's values.
WHEEL_OFFSET = {}


def shifted(d, offset):
    """Every rpm of every gear moved by `offset` (the 0s, unused LEDs, stay 0)."""
    c = json.loads(json.dumps(d))
    c["ledRpm"] = [{g: [v + offset if v > 0 else 0 for v in row] for g, row in gears.items()} for gears in c["ledRpm"]]
    return c


def dump(d):
    """One gear per line, as Lovely Car Data's files are."""
    text = json.dumps(d, indent=2)
    out, row = [], None
    for line in text.split("\n"):
        s = line.strip()
        if row is None and s.endswith("[") and not s.endswith("[{") and '"ledRpm"' not in s:
            row = [line.rstrip()]
        elif row is not None:
            row.append(s)
            if s.startswith("]"):
                out.append(row[0] + "".join(row[1:]))
                row = None
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def main():
    restore = "--restore" in sys.argv
    ORIGINAL.mkdir(parents=True, exist_ok=True)
    FIXED.mkdir(parents=True, exist_ok=True)
    for car, fix in FIXES.items():
        name = f"iracing_{car}.json"
        live, keep = CACHE / name, ORIGINAL / name
        if restore:
            if keep.exists():
                shutil.copyfile(keep, live)   # dated now: the plugin treats it as an ordinary copy again
                print(f"{car}: original put back")
            continue
        if not keep.exists():
            if not live.exists():
                print(f"{car}: not in the plugin's cache (drive the car once first)")
                continue
            shutil.copyfile(live, keep)
        d = json.loads(keep.read_text(encoding="utf-8-sig"))
        fix(d)
        text = dump(d)
        json.loads(text)
        (FIXED / f"{car}.json").write_text(text, encoding="utf-8")
        offset = WHEEL_OFFSET.get(car, 0)
        live.write_text(dump(shifted(d, offset)) if offset else text, encoding="utf-8")
        os.utime(live, (YEAR_2099, YEAR_2099))
        print(f"{car}: corrected" + (f", {offset:+d} rpm on the wheel" if offset else ""))


if __name__ == "__main__":
    main()
