#!/usr/bin/env python3
"""patch_mclaren_720s.py - brings the converted McLaren 720S GT3 dash close to the car's own display in iRacing.

  python scripts/patch_mclaren_720s.py [--from out/iracing/lmgt3-mclaren-720s-iracing.prev720.json]

The dash is Redadeg's for LMU (scripts/patch-iracing.ps1 writes out/iracing/lmgt3-mclaren-720s-iracing.json). The
car's display in iRacing is different: blue tyres with the pressure in bar and the tyre temperature, ABS in red, water
and battery bottom left, fuel under the tyres. Compared with a frame of the sim on 2026-10-12.

Runs over the file in out/iracing (keeps the original next to it, .prev720.json, and always starts from it). Exits
with an error if the file isn't the one expected. Converted third-party material: it stays in out/ and the local SimHub.

Differences left from the real display (iRacing doesn't give the data): TC2, the engine map and FUNC aren't in this
car's telemetry; nor is the fuel used in the session, so the second field is the laps the fuel lasts. The brake bias
(BB) stays, though it isn't on the real display. Tyre pressure and temperature only update in the pits (an iRacing
limit).
"""
import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "out" / "iracing" / "lmgt3-mclaren-720s-iracing.json"
ORIG = DASH.with_suffix(".prev720.json")
T = "DataCorePlugin.GameRawData.Telemetry."
BLUE, BLUE_TEXT, RED = "#2F6FD0", "#4A9BF0", "#FF3030"

EXPECT = {12: "T_RR", 13: "P_RR", 14: "T_RL", 15: "P_RL", 16: "T_FR", 17: "P_FR", 18: "T_FL", 19: "P_FL", 20: "RR TEMP", 21: "RL TEMP",
          22: "FR TEMP", 23: "FL TEMP", 32: "ABS", 35: "MAP Tag", 36: "MAP", 37: "VE Tag", 38: "VE#", 39: "AT Tag", 40: "SLIP", 41: "CUT Tag",
          42: "TCCUT", 43: "LAP Tag", 44: "LAP", 59: "RectangleItem", 60: "MAPs#", 61: "Brake Bias", 68: "RectangleItem", 69: "CUT#",
          70: "CUT", 71: "RectangleItem", 72: "CUT#", 73: "SLIP", 79: "ARB R#", 80: "ARB R Tag", 81: "ARB F#", 82: "ARB F Tag",
          87: "RR %", 88: "RL %", 89: "FR %", 90: "FL %", 91: "Background", 92: "Icon", 93: "FUEL LOW Tag", 94: "X", 95: "X"}
CORNER = {"RR": ("RearRight", "RR"), "RL": ("RearLeft", "LR"), "FR": ("FrontRight", "RF"), "FL": ("FrontLeft", "LF")}


def plain(e, colour):
    e["Color"] = colour
    e.pop("ColorBind", None)
    e.pop("ColorStops", None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src")
    a = ap.parse_args()
    if a.src:
        src = Path(a.src)
    else:
        if not ORIG.exists():
            shutil.copyfile(DASH, ORIG)
        src = ORIG
    d = json.loads(src.read_text(encoding="utf-8-sig"))
    el = d["Elements"]
    wrong = [f"{i}: {el[i].get('Name') if i < len(el) else None} (expected {n})" for i, n in EXPECT.items() if i >= len(el) or el[i].get("Name") != n]
    if wrong:
        print("the dash isn't the one expected, nothing changed:\n  " + "\n  ".join(wrong))
        return 1

    # tyres: blue as in the car; the pressure in bar (iRacing's, cold) and the tyre's temperature instead of the brakes'
    for i in (20, 21, 22, 23):
        plain(el[i], BLUE)
    for i, key in ((12, "RR"), (14, "RL"), (16, "FR"), (18, "FL")):
        plain(el[i], BLUE_TEXT)
        el[i].update(Bind=f"ncalc:[TyreTemperature{CORNER[key][0]}]", Format="0", Samples=["888"], PreviewText="37")
    for i, key in ((13, "RR"), (15, "RL"), (17, "FR"), (19, "FL")):
        plain(el[i], BLUE_TEXT)
        el[i].update(Bind=f"ncalc:[{T}{CORNER[key][1]}coldPressure]/100", Format="0.00", Samples=["8.88"], PreviewText="1.58")
    # the rear tyres' wear read the front ones'
    el[87]["Bind"] = "ncalc:min([TyreWearRearRight], 99)"
    el[88]["Bind"] = "ncalc:min([TyreWearRearLeft], 99)"

    el[32]["Color"] = RED                                       # ABS in red

    # bottom left: water and battery in place of CUT / SLIP / VE / FUEL
    el[43].update(Name="WATER Tag", Text="WATER", X=33, W=135)
    el[44].update(Name="WATER", X=33, W=135, Bind="ncalc:[WaterTemperature]", Format="0", Samples=["888"], PreviewText="76", Color=BLUE_TEXT,
                  ColorBind="ncalc:if([WaterTemperature]>105,'1',0)", ColorStops=[{"Value": 0.0, "Color": "#FF4A9BF0"}, {"Value": 1.0, "Color": "#FFFF0000"}])
    volts_tag, volts = copy.deepcopy(el[43]), copy.deepcopy(el[44])
    volts_tag.update(Name="VOLTS Tag", Text="VOLTS", X=176, W=135)
    volts.update(Name="VOLTS", X=176, W=135, Bind=f"ncalc:[{T}Voltage]", Format="0.0", Samples=["88.8"], PreviewText="13.8", Color="#FFFFFF")
    volts.pop("ColorBind", None)
    volts.pop("ColorStops", None)

    # under the tyres: fuel (litres) and the laps it lasts, in place of the anti-roll bars (no data)
    el[82].update(Name="FUEL Tag", Text="FUEL", X=491, W=120)
    el[81].update(Name="FUEL L", X=491, W=120, Bind="ncalc:[Fuel]", Format="0.0", Samples=["888.8"], PreviewText="54.2")
    el[80].update(Name="FUEL LAPS Tag", Text="LAPS", X=630, W=120)
    el[79].update(Name="FUEL LAPS", X=630, W=120, Bind="ncalc:[DataCorePlugin.Computed.Fuel_RemainingLaps]", Format="0.0", Samples=["88.8"], PreviewText="24.5")

    # no data in iRacing for this car: engine map, TC2 (CUT), SLIP, virtual energy and their warnings
    gone = {35, 36, 37, 38, 39, 40, 41, 42, 59, 60, 61, 68, 69, 70, 71, 72, 73, 91, 92, 93, 94, 95}
    out = []
    for i, e in enumerate(el):
        if i in gone:
            continue
        out.append(e)
        if i == 44:
            out += [volts_tag, volts]
    d["Elements"] = out
    DASH.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{DASH.relative_to(ROOT)}: {len(el)} -> {len(out)} elements (original in {ORIG.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
