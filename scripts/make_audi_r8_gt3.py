#!/usr/bin/env python3
"""make_audi_r8_gt3.py - writes dashes/gt3-iracing/audi-r8-lms-gt3-iracing.json.

A replica of the Audi R8 LMS EVO II GT3's display in iRacing (Bosch DDU S2 Plus), from iRacing's manual (picture in
reference/iracing/, outside git): one page, no popups. Shapes and text only. The real display is squarer than the
wheel's, so the boxes are stretched in width; the order and the rows are the original's.

Differences from the real display, because of what iRacing gives as telemetry:
  - tgear (gearbox oil) doesn't exist: the cell shows the oil pressure (poil);
  - "fuel total" is the fuel used in the stint, which iRacing doesn't give: the cell shows what is left (fuel);
  - "TC lon" uses iRacing's second TC if the car has one, else repeats the TC;
  - the two "100" next to the ABS (front and rear intervention, fixed at 100 % in iRacing) are fixed text;
  - the pressure and temperature boxes don't change colour (the real one paints them against the tyre's ideal);
  - the pit limiter warning is always green (the real one turns red over the limit);
  - the setting-change popups and the start-up sequence don't come from the manual (which doesn't describe them):
    they are the same in every from-scratch dash, by request.
"""
from dashkit import CORNERS, GREY, LABEL, PRESSURE_SAMPLES, TEL, WHITE, Dash, pressure

d = Dash("gt3-iracing", "audi-r8-lms-gt3-iracing", "iRacing - Audi R8 LMS GT3",
         "Replica of the Audi R8 LMS EVO II GT3's display in iRacing, made from iRacing's manual. Shapes and text only.")

# ---- row 1: pressures, gear, TC, ABS, tyre temperatures
for (n, corner), (x, y) in zip(CORNERS, ((14, 4), (172, 4), (14, 94), (172, 94))):
    d.box_value(f"P {n}", x, y, 154, 88, pressure(corner), "text", PRESSURE_SAMPLES, "23.9")
d.frame("Gear", 333, 4, 134, 178)
d.label("Gear", "gear", 335, 6, 130)
d.value("Gear", "gearText", "gear", ["8", "N", "R"], "1", 335, 44, 130, h=124, font=117, empty="N")
d.cell("TC lat", "TC lat", 485, 4, 104, 88, "tcLevel", preview="3")
d.cell("TC lon", "TC lon", 485, 94, 104, 88, f"ncalc:isnull([{TEL}dcTractionControl2], [TCLevel])", preview="3")
d.cell("ABS", "ABS", 599, 4, 88, 88, "absLevel", preview="3")
for i, y in enumerate((4, 49)):
    d.frame(f"ABS share {i}", 695, y, 83, 43)
    d.label(f"ABS share {i}", "100", 697, y + 5, 79)
for (n, corner), (x, y) in zip(CORNERS, ((599, 94), (691, 94), (599, 139), (691, 139))):
    d.box_value(f"T {n}", x, y, 87, 43, f"ncalc:[TyreTemperature{corner}]", "0", ["188"], "112", font=LABEL, font_h=32)

# ---- row 2: rpm, brake bias, speed
d.box_value("RPM", 16, 196, 184, 66, "rpm", "0", ["18888"], "1945")
d.cell("Brake bias", "brakebal", 421, 184, 162, 90, "brakeBias", "0.0", ["88.8"], "60.0")
d.cell("Speed", "speed", 595, 184, 183, 90, "speed", samples=["388"], preview="14")

# ---- row 3: lap time, lap, difference
d.cell("Lap time", "lap time", 14, 276, 296, 90, "currentLapTime", "laptime", ["8:88.888"], "1:00.000", empty="-:--.---")
d.cell("Lap", "lap", 322, 276, 144, 90, "completedLaps", samples=["188"], preview="0")
d.cell("Diff", "diff", 478, 276, 300, 90, "delta", "delta", ["+88.88"], "-0.40", empty="-.--",
       PositiveColor="#FF3030", NegativeColor="#30FF40")

# ---- row 4: temperatures and fuel
for name, text, x, bind in (("Oil pressure", "poil", 12, "ncalc:[OilPressure]"), ("Oil", "toil", 166, "oilTemp"),
                            ("Water", "tmot", 320, "waterTemp")):
    d.cell(name, text, x, 368, 150, 90, bind, samples=["188"], preview="170")
d.cell("Fuel lap", "fuel lap", 478, 368, 120, 90, "fuelThisLap", "0.0", ["18.8"], "0.0")
d.cell("Fuel", "fuel", 606, 368, 172, 90, "fuel", "0.0", ["188.8"], "13.7")

# ---- pit limiter: a green box with the speed, in row 2's free space
d.banner("Pit limiter", "PIT", 206, 186, 208, 86, "#20A030", WHITE, "pitLimiter", speed=True)

# ---- setting-change popups (over the gear and the two TCs) and the start-up sequence
d.popups(333, 4, 256, 178, ["TC", "ABS", "BB", "THR"])
d.startup("AUDI", "R8 LMS GT3 EVO II", logo="audi")

d.save()
