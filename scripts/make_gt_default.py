#!/usr/bin/env python3
"""make_gt_default.py - writes dashes/default/gt-default.json.

The default dash, for any game and car. Its layout follows the Lovely Dashboard's main screen (Lovely Sim Racing):
tyres on the left, delta / gear / speed in the middle, times and fuel on the right, and the row of settings (TC, TC2,
ABS, BB, MAP) at the bottom. It is drawn from scratch with the screen's own shapes and text only: no pictures,
scripts or properties of the Lovely plugin, only FX Unleashed's keys and generic SimHub properties.

Fonts: the ones chosen on the wheel for the M4 (94 for labels, 110 for numbers).

Running this again is the only way to change the dash: don't edit the JSON by hand.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashes" / "default" / "gt-default.json"

WHITE, GREY, BLACK = "#FFFFFF", "#909090", "#000000"
PURPLE, YELLOW, GREEN, RED, BLUE = "#D040FF", "#FFD000", "#20E040", "#FF2020", "#00B0FF"
LABEL, LABEL_H = 94, 32
NUM, NUM_H = 110, 50

els = []


def add(**e):
    els.append(e)
    return e


def frame(name, x, y, w, h, color=GREY, **kw):
    add(Type="box", Name=f"{name} frame", X=x, Y=y, W=w, H=h, Color=color, Border=2, Radius=10, **kw)


def label(name, text, x, y, w, color=GREY, align="center", **kw):
    add(Type="label", Name=f"{name} label", X=x, Y=y, W=w, H=LABEL_H, Text=text, Font=LABEL, Color=color, Align=align, **kw)


def value(name, bind, fmt, samples, preview, x, y, w, h=NUM_H, font=NUM, color=WHITE, empty="-", align="center", **kw):
    add(Type="value", Name=name, X=x, Y=y, W=w, H=h, Bind=bind, Format=fmt, Font=font, Color=color, Align=align,
        Samples=samples, PreviewText=preview, Empty=empty, **kw)


def pressure(corner):
    p = f"[TyrePressure{corner}]"
    return f"ncalc:if([TyrePressureUnit]='Psi', format({p}, '0.0'), if([TyrePressureUnit]='Kpa', format({p}, '0'), format({p}, '0.00')))"


# ---- top left: the session; flags over it
frame("Session", 12, 4, 238, 56)
value("Session", "sessionTypeName", "text", ["OFFLINE TESTING", "LONE QUALIFY"], "RACE", 16, 16, 230, h=LABEL_H, font=LABEL,
      empty="")

# ---- left: tyres (pressure on top, temperature under it, coloured from cold to hot)
frame("Tyres", 12, 66, 238, 286)
label("Tyres", "TIRES", 16, 70, 230)
TEMP_STOPS = [{"Value": 50, "Color": BLUE}, {"Value": 80, "Color": GREEN}, {"Value": 105, "Color": RED}]
for name, corner, x, y in (("FL", "FrontLeft", 20, 106), ("FR", "FrontRight", 134, 106),
                           ("RL", "RearLeft", 20, 226), ("RR", "RearRight", 134, 226)):
    value(f"P {name}", pressure(corner), "text", ["28.8", "1.65", "188"], "26.6", x, y, 108)
    temp = f"ncalc:[TyreTemperature{corner}]"
    value(f"T {name}", temp, "0", ["188"], "84", x, y + 54, 108, h=LABEL_H, font=LABEL, color=GREEN, ColorBind=temp,
          ColorStops=TEMP_STOPS)

# ---- middle: delta, gear, rpm, speed
frame("Delta", 258, 4, 254, 56, color=PURPLE)
value("Delta", "delta", "delta", ["+88.88"], "-0.07", 262, 7, 246, PositiveColor=RED, NegativeColor=GREEN, empty="-.--")
frame("Gear", 258, 66, 254, 222)
value("Gear", "gearText", "gear", ["8", "N", "R"], "2", 262, 70, 246, h=170, font=103, empty="N")
value("RPM", "rpm", "0", ["18888"], "6085", 262, 242, 246, h=LABEL_H, font=LABEL, color=GREY)
add(Type="bar", Name="RPM bar", X=264, Y=276, W=242, H=8, Bind="rpmPercent", Min=50, Max=100, Color=GREEN, Fill="#202020",
    ColorBind="rpmPercent", ColorStops=[{"Value": 85, "Color": GREEN}, {"Value": 94, "Color": YELLOW}, {"Value": 98, "Color": RED}])
add(Type="box", Name="Speed frame", X=300, Y=294, W=170, H=58, Color=WHITE, Fill=WHITE, Border=2, Radius=10)
value("Speed", "speed", "0", ["388"], "125", 306, 298, 158, color=BLACK, Background=WHITE)

# ---- bottom: settings, each in its own colour
for name, text, x, color, bind, fmt, samples, preview in (
        ("TC", "TC", 12, BLUE, "tcLevel", "0", ["88"], "3"), ("TC2", "TC2", 113, BLUE, "tcCut", "0", ["88"], "0"),
        ("ABS", "ABS", 214, YELLOW, "absLevel", "0", ["88"], "2"),
        ("BB", "BB", 315, RED, "brakeBias", "0.0", ["88.8"], "56.2"),
        ("MAP", "MAP", 416, GREEN, "engineMap", "0", ["88"], "1")):
    frame(name, x, 358, 96, 96, color=color)
    label(name, text, x + 4, 361, 88, color=color)
    value(name, bind, fmt, samples, preview, x + 4, 398, 88, color=color)

# ---- right: position and lap, times, fuel
frame("Race", 520, 4, 258, 92)
for name, text, x, bind, preview in (("Position", "POS", 524, "position", "11"), ("Lap", "LAP", 652, "lap", "7")):
    label(name, text, x, 7, 122)
    value(name, bind, "0", ["188"], preview, x, 42, 122)

frame("Lap times", 520, 102, 258, 188)
for name, text, y, color, bind in (("Predicted", "EST", 110, PURPLE, "predictedLap"),
                                   ("Last lap", "LAST", 170, YELLOW, "lastLapTime"),
                                   ("Best lap", "BEST", 230, GREEN, "bestLapTime")):
    label(name, text, 524, y + 9, 62, align="left")
    value(name, bind, "laptime", ["8:88.888"], "1:44.535", 590, y, 182, color=color, empty="-:--.---")

frame("Fuel lap", 520, 296, 258, 56)
label("Fuel lap", "FUEL/LAP", 524, 308, 130, align="left")
value("Fuel lap", "fuelLastLap", "0.00", ["18.88"], "2.69", 660, 299, 112)
frame("Fuel", 520, 358, 258, 96)
for name, text, x, bind, fmt, samples, preview in (("Fuel", "FUEL", 524, "fuel", "0.0", ["188.8"], "14.0"),
                                                   ("Fuel laps", "LAPS", 652, "fuelRemainingLaps", "0.0", ["88.8"], "5.4")):
    label(name, text, x, 361, 122)
    value(name, bind, fmt, samples, preview, x, 398, 122)

# ---- warnings (they come and go: they cover the whole box, after everything they cover)
def banner(name, text, x, y, w, h, fill, color, cond):
    v = dict(Visible=cond, PreviewVisible=False)
    add(Type="rect", Name=f"{name} background", X=x, Y=y, W=w, H=h, Color=fill, **v)
    add(Type="label", Name=name, X=x + 2, Y=y + (h - LABEL_H) // 2, W=w - 4, H=LABEL_H, Text=text, Font=LABEL, Color=color,
        Align="center", **v)


banner("Pit limiter", "PIT LIMITER", 258, 4, 254, 56, BLUE, WHITE, "pitLimiter")
banner("Yellow flag", "YELLOW FLAG", 12, 4, 238, 56, YELLOW, BLACK, "ncalc:[Flag_Yellow]")
banner("Blue flag", "BLUE FLAG", 12, 4, 238, 56, "#0050FF", WHITE, "ncalc:[Flag_Blue]")

# ---- setting change: for 2 s the new value shows large over the gear. It covers the whole gear and ends above the
#      rpm and the bar: a bar under a popup redraws through it (flickers)
TEL = "DataCorePlugin.GameRawData.Telemetry."
for name, text, color, bind, fmt, samples, preview, watched in (
        ("TC", "TC", BLUE, "tcLevel", "0", ["88"], "3", "[TCLevel]"),
        # TC2 has no common property in SimHub: the popup follows iRacing's (in other games it never shows)
        ("TC2", "TC2", BLUE, "tcCut", "0", ["88"], "0", f"isnull([{TEL}dcTractionControl2], 0)"),
        ("ABS", "ABS", YELLOW, "absLevel", "0", ["88"], "2", "[ABSLevel]"),
        ("BB", "BRAKE BIAS", RED, "brakeBias", "0.0", ["88.8"], "56.2", "[BrakeBias]"),
        ("MAP", "ENGINE MAP", GREEN, "engineMap", "0", ["88"], "1", "[EngineMap]")):
    v = dict(Visible=f"ncalc:changed(2000, {watched})", PreviewVisible=False)
    add(Type="box", Name=f"{name} popup", X=258, Y=66, W=254, H=176, Color=color, Fill="#101418", Border=4, Radius=10, **v)
    add(Type="label", Name=f"{name} popup label", X=264, Y=74, W=242, H=LABEL_H, Text=text, Font=LABEL, Color=color,
        Align="center", **v)
    value(f"{name} popup value", bind, fmt, samples, preview, 264, 112, 242, h=100, font=82, color=WHITE,
          Background="#101418", **v)

dash = {
    "FormatVersion": 2,
    "Id": OUT.stem,
    "Name": "GT default (based on the Lovely Dashboard)",
    "Author": "skuldgerry",
    "Description": "Default dash for any game. Layout after the Lovely Dashboard (Lovely Sim Racing), "
                   "drawn from scratch with shapes and text only.",
    "Elements": els,
}
OUT.write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{OUT.relative_to(ROOT)}: {len(els)} elements")
