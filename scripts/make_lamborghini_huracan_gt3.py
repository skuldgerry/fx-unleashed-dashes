#!/usr/bin/env python3
"""make_lamborghini_huracan_gt3.py - writes dashes/gt3-iracing/lamborghini-huracan-gt3-iracing.json.

A replica of the race page (day) of the Lamborghini Huracán GT3 EVO's display in iRacing (Bosch DDU S2), from iRacing's
manual (picture in reference/iracing/, outside git). Shapes and text only: a light background, black text, double-line
frames in each cell's colour and the label breaking the top line, as on the original. The real display is squarer
than the wheel's, so the boxes are stretched in width. The night page and the two qualifying pages weren't made.

Differences from the real display, because of what iRacing gives as telemetry:
  - MAP, EPS, APS and S12 don't work in iRacing (the manual says "inoperable"): fixed text, "1";
  - tgear (gearbox oil) doesn't exist: the cell shows the oil pressure (poil);
  - "fuel used" is the fuel used in the stint, which iRacing doesn't give: the cell shows what is left (fuel);
  - the TC and ABS cells don't light blue when the system acts (the wheel's lights show that);
  - the setting-change popups and the start-up sequence don't come from the manual (which doesn't describe them):
    they are the same in every from-scratch dash, by request.
"""
from dashkit import LABEL, LABEL_H, NUM, NUM_H, WHITE, Dash, text_width

BG, INK, LINE = "#D6D6D6", "#101010", "#303030"
GREEN = "#28A838"
d = Dash("gt3-iracing", "lamborghini-huracan-gt3-iracing", "iRacing - Lamborghini Huracan GT3",
         "Replica of the Lamborghini Huracan GT3 EVO's race page in iRacing, made from iRacing's manual. "
         "Shapes and text only.")
d.add(Type="rect", Name="Background", X=0, Y=0, W=790, H=460, Color=BG)


def cell(name, text, x, y, w, h, bind, fmt="0", samples=("88",), preview="1", line=LINE, fill=None, font=NUM,
         font_h=NUM_H, **kw):
    """A Bosch cell: a double-line frame (2 px, 2 px apart). The label sits inside the box, only the tops of its letters
    crossing the top line, which it breaks (as on the original). Needs 92 px of height."""
    paper = fill or BG
    outer = dict(Type="box", Name=f"{name} frame", X=x, Y=y + 6, W=w, H=h - 6, Color=line, Border=2)
    if fill:
        outer["Fill"] = fill
    d.add(**outer)
    d.add(Type="box", Name=f"{name} inner frame", X=x + 4, Y=y + 10, W=w - 8, H=h - 14, Color=line, Border=2)
    tw = text_width(LABEL, text)
    d.add(Type="rect", Name=f"{name} label gap", X=x + (w - tw) // 2 - 4, Y=y + 6, W=tw + 8, H=6, Color=paper)
    d.label(name, text, x, y, w, color=INK)
    if bind:   # a 12 px margin: a value aligned to one side doesn't touch the line
        d.value(name, bind, fmt, list(samples), preview, x + 12, y + 34, w - 24, h=font_h, font=font, color=INK,
                Background=paper, **kw)
    else:   # fixed text
        d.label(f"{name} fixed", preview, x + 8, y + 34, w - 16, h=font_h, font=font, color=INK)


# ---- row 1: the settings around the gear, each cell with its frame's colour
for name, x, line, bind, preview in (("TC", 14, "#1818D0", "tcLevel", "3"), ("MAP", 108, "#707070", None, "1"),
                                     ("EPS", 202, "#C818C8", None, "1"), ("APS", 492, "#188838", None, "1"),
                                     ("S12", 588, LINE, None, "1"), ("ABS", 684, "#D81818", "absLevel", "3")):
    cell(name, name, x, 2, 90, 92, bind, preview=preview, line=line)
cell("Gear", "gear", 323, 2, 143, 148, "gearText", "text", ["8", "N", "R"], "6", font=19, font_h=92, empty="N")

# ---- row 2: speed (green box) and rpm
cell("Speed", "speed", 169, 154, 246, 92, "speed", samples=["388"], preview="154", line="#107020", fill=GREEN)
cell("RPM", "rpm", 420, 154, 222, 92, "rpm", samples=["18888"], preview="7207")

# ---- row 3: lap time and difference
cell("Lap time", "laptime", 12, 250, 302, 92, "currentLapTime", "laptime", ["8:88.888"], "1:05.410", empty="-:--.---", align="left")
cell("Diff", "diff", 457, 250, 321, 92, "delta", "delta", ["+88.88"], "-0.40", empty="-.--", align="right",
     PositiveColor="#C00000", NegativeColor="#007020")

# ---- row 4: temperatures and fuel
for name, text, x, w, bind in (("Oil pressure", "poil", 12, 146, "ncalc:[OilPressure]"), ("Oil", "toil", 166, 148, "oilTemp"),
                               ("Water", "tmot", 321, 148, "waterTemp")):
    cell(name, text, x, 366, w, 92, bind, samples=["188"], preview="193")
cell("Fuel lap", "fuel lap", 478, 366, 128, 92, "fuelThisLap", "0.0", ["18.8"], "0.0", align="right")
cell("Fuel", "fuel", 612, 366, 166, 92, "fuel", "0.0", ["188.8"], "64.2", align="right")

# ---- pit limiter: a blue band the whole width, over the whole of row 3
d.banner("Pit limiter", "PIT LIMITER", 12, 250, 766, 92, "#1040E0", WHITE, "pitLimiter")

# ---- setting-change popups (over the speed and the rpm) and the start-up sequence
d.popups(169, 154, 473, 92, ["TC", "ABS", "BB", "THR"])
d.startup("LAMBORGHINI", "HURACAN GT3 EVO", logo="lamborghini")

d.save()
