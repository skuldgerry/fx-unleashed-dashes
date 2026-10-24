#!/usr/bin/env python3
"""make_bmw_m4_gt3.py - writes dashes/gt3-iracing/bmw-m4-gt3-iracing.json.

A replica of the BMW M4 GT3's display in iRacing (the car's Bosch), from a frame of the sim taken on 2026-10-12
(reference/iracing/m4-dash-real.png, outside git). iRacing's 2024 manual describes an earlier display: don't use it.
One page. Drawn with the screen's own shapes and text only, no pictures.

The boxes' positions and widths come from the frame, scaled to the wheel. The heights are 88-90 px instead of the
original's ~84, because the fonts chosen on the wheel (94 for labels, 110 for numbers, 90 for the speed) need 32 + 50 px
plus margins. The gear uses font 11 (128 px, bold), by request.

Differences from the real display, because of what iRacing gives as telemetry:
  - TGEAR (gearbox oil) isn't in the telemetry: the cell shows the oil pressure (POIL);
  - ALS ("AIR") and MAP ("1") don't move in this car in iRacing: fixed text, like the AC and FAN 1 tags;
  - MIN: in the car it seems to be the time elapsed in minutes (0 leaving the pits, next to LAP 0). Here it shows the
    session's minutes; an interpretation, to be confirmed;
  - the tyre pressures only change in the pits (iRacing doesn't give them on track);
  - the fuel boxes are wider than the original's, so the label carries the unit ("[L]");
  - the TC warnings at the sides of the display and the shift lights are LEDs, not part of the dash;
  - the setting-change popups and the start-up sequence don't exist in the car: they are the same in every
    from-scratch dash, by request.

Running this again is the only way to change the dash: don't edit the JSON by hand.
"""
from dashkit import CORNERS, NUM, NUM_H, PRESSURE_SAMPLES, TEL, WHITE, Dash, pressure

# the car's display colours, taken from the frame
ALS_GREY, ALS_CYAN, INK = "#C8C8C8", "#40C0C8", "#101010"
MAP_RED, TC_BLUE, ABS_GREEN = "#C02830", "#2838C8", "#3C9C44"
FAN_YELLOW = "#A8C030"
LIVE_GREEN = "#48C830"      # tyre pressures and gear
MAGENTA = "#D030D0"

d = Dash("gt3-iracing", "bmw-m4-gt3-iracing", "iRacing - BMW M4 GT3",
         "Replica of the BMW M4 GT3's display in iRacing, made from a frame of the sim. Shapes and text only.")


def fuel_label(liters, other):
    """The label with SimHub's fuel unit, like the real display's "[kg]"."""
    texts = [f"{liters}[L]", f"{other}[KG]", f"{other}[GAL]"]
    return (f"ncalc:if([FuelUnit]='Liters','{texts[0]}',if([FuelUnit]='Kg','{texts[1]}','{texts[2]}'))", texts)


def chip(name, text, x, y, w, fill):
    """A fixed tag with a coloured background and black text (AC, FAN 1)."""
    d.add(Type="rect", Name=f"{name} background", X=x, Y=y, W=w, H=36, Color=fill)
    d.label(name, text, x, y + 2, w, color=INK)


# ---- left: pressures (green), fuel, temperatures
d.frame("Tyres", 15, 4, 236, 178)
d.label("Tyres", "TYRE PRESSURE", 17, 7, 232)
d.add(Type="rect", Name="Tyres divider", X=15, Y=40, W=236, H=2, Color=WHITE)
for (n, corner), (x, y) in zip(CORNERS, ((30, 48), (143, 48), (30, 118), (143, 118))):
    d.value(f"P {n}", pressure(corner), "text", PRESSURE_SAMPLES, "1.59", x, y, 92, color=LIVE_GREEN)
d.cell("Lap fuel", fuel_label("LAP FUEL ", "LAP FUEL "), 15, 184, 205, 90, "fuelLastLap", "0.00", ["18.88"], "0.00")
d.cell("Fuel", fuel_label("FUEL REMAIN", "FUEL REM "), 15, 276, 205, 90, "fuel", "0.00", ["188.88"], "73.23")
for name, text, x, bind in (("Water", "TMOT", 15, "waterTemp"), ("Oil", "TOIL", 92, "oilTemp"),
                            ("Oil pressure", "POIL", 169, "ncalc:[OilPressure]")):
    d.cell(name, text, x, 368, 74, 90, bind, samples=["188"], preview="78")

# ---- middle: gear (green, bold), speed, the AC and FAN tags
d.label("Gear", "GEAR", 300, 8, 154)
d.value("Gear", "gearText", "text", ["8", "N", "R"], "2", 300, 42, 154, h=130, font=11, color=LIVE_GREEN, empty="N")
d.value("Speed", "speed", "0", ["388"], "109", 290, 178, 260, h=84, font=90)
chip("AC", "AC", 226, 328, 70, ALS_CYAN)
chip("Fan", "FAN 1", 300, 328, 92, FAN_YELLOW)

# ---- top cells: ALS grey with its label in cyan and "AIR" in black, MAP red, TC blue, ABS green
d.frame("ALS", 454, 2, 78, 88, fill=ALS_GREY)
d.add(Type="rect", Name="ALS header", X=456, Y=4, W=74, H=32, Color=ALS_CYAN)
d.label("ALS", "ALS", 456, 4, 74, color=INK)
d.label("ALS fixed", "AIR", 456, 36, 74, h=NUM_H, font=NUM, color=INK)
for name, x, fill, bind, preview in (("MAP", 535, MAP_RED, None, "1"), ("TC", 616, TC_BLUE, "tcLevel", "2"),
                                     ("ABS", 697, ABS_GREEN, "absLevel", "4")):
    d.cell(name, name, x, 2, 78, 88, bind, preview=preview, fill=fill)

# ---- right: difference, last lap, best lap
d.cell("Delta", "GAIN/LOSS", 560, 92, 215, 90, "delta", "delta", ["+88.88"], "-0.40", empty="-.--")
d.cell("Last lap", "LAST LAP", 560, 184, 215, 90, "lastLapTime", "laptime", ["8:88.888"], "1:00.000", empty="-:--.---")
d.cell("Best lap", "BEST LAP", 560, 276, 215, 90, "bestLapTime", "laptime", ["8:88.888"], "1:00.000", empty="-:--.---")

# ---- bottom row: tyre, brake bias, lap, minutes
d.cell("Tyre", "TYRE", 284, 368, 194, 90, f"ncalc:'TYRE ' + format([{TEL}PlayerTireCompound]+1, '0')", "text", ["TYRE 8"],
       "TYRE 1", empty="TYRE")
d.cell("Brake bias", "BRKB", 485, 368, 124, 90, "brakeBias", "0.0", ["88.8"], "52.5")
d.cell("Lap", "LAP", 615, 368, 78, 90, "completedLaps", samples=["188"], preview="0")
d.cell("Minutes", "MIN", 698, 368, 77, 90, f"ncalc:truncate([{TEL}SessionTime]/60)", samples=["188"], preview="0")

# ---- pit limiter: the PSL box shows under the cells (the bold gear takes the place on the left)
PIT = dict(Visible="pitLimiter", PreviewVisible=False)
d.add(Type="rect", Name="PSL background", X=458, Y=96, W=98, H=58, Color=MAGENTA, **PIT)
d.add(Type="label", Name="PSL", X=460, Y=100, W=94, H=NUM_H, Text="PSL", Font=NUM, Color=WHITE, Align="center", **PIT)

# ---- setting-change popups (over the speed) and the start-up sequence
d.popups(286, 174, 268, 152, ["TC", "ABS", "BB"])
d.startup("BMW", "M4 GT3", logo="bmw")

d.save()
