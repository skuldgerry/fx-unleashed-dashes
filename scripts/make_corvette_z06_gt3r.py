#!/usr/bin/env python3
"""make_corvette_z06_gt3r.py - writes dashes/gt3-iracing/corvette-z06-gt3r-iracing.json.

A replica of the "Race" page of the Chevrolet Corvette Z06 GT3.R's display in iRacing, from iRacing's manual (picture
in reference/iracing/, outside git). The background is a picture drawn right here with Pillow (our own work, not a
cut-out of the sim): the chamfered panels, the labels and everything that is fixed in iRacing. Only the values that
change are screen text, each on its panel's plain colour, so it redraws in one step.

As the labels are in the picture, the units (speed, fuel, temperature) are SimHub's when the dash is generated:
changing units in SimHub means generating it again.

Fixed in the picture, as in iRacing (the manual says they aren't used or can't be adjusted): Multi, Map, Page, Wiper,
Dimmer, Func A, Func B, Launch, A/C and Fans, with the values of the manual's picture. Yaw follows the TC (the manual
says it is tied to it).

Differences from the real display:
  - the pressure and temperature boxes have a fixed colour (the real one paints them blue, green or red against the
    tyre's ideal, which the telemetry doesn't give);
  - the light and wiper icons are approximate drawings; the light one lights blue and blinks with the headlight flash
    (dcHeadlightFlash), the wiper one stays dark;
  - the pit limiter warning is a green band with the speed, instead of the whole screen with approach bars;
  - the wheel-lock warnings (a red or orange background per quarter) weren't made;
  - the setting-change popups and the start-up sequence don't come from the manual (which doesn't describe them):
    they are the same in every from-scratch dash, by request.
"""
import base64
import io
import json
import sys
import urllib.request

from dashkit import CORNERS, LABEL, LABEL_H, NUM, NUM_H, PRESSURE_SAMPLES, ROOT, WHITE, Dash, pressure

sys.path.insert(0, str(ROOT / ".deps" / "pylib"))   # Pillow, installed for the project only
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

YELLOW = "#D8D020"
BACK = "#0A0C10"
# panels: (inside colour, rim, label band)
BLUE = ("#123E63", "#3A86C0", "#0C2B46")
GREEN = ("#143F1E", "#3C9A50", "#0D2C15")
PINK = ("#5C1040", "#B03080", "#400B2C")
RED = ("#5A1218", "#B83040", "#3E0C10")
GREYP = ("#3A3D42", "#8A8E96", "#26282C")
DARK = ("#1A1D22", "#555A62", "#101216")
CUT = 8          # corner chamfer
TEXT_GREY = "#B8BCC4"

d = Dash("gt3-iracing", "corvette-z06-gt3r-iracing", "iRacing - Corvette Z06 GT3.R",
         "Replica of the Chevrolet Corvette Z06 GT3.R's Race page in iRacing, made from iRacing's manual. "
         "Panels and labels drawn from scratch, values as screen text.")


def simhub_units():
    """The units SimHub uses now (the plugin's API); without SimHub, metric."""
    names = ["SpeedLocalUnit", "FuelUnit", "TemperatureUnit"]
    try:
        url = "http://127.0.0.1:8899/api/props?names=" + ",".join("DataCorePlugin.GameData.NewData." + n for n in names)
        with urllib.request.urlopen(url, timeout=10) as r:
            got = json.loads(r.read().decode("utf-8"))
        return [got.get("DataCorePlugin.GameData.NewData." + n) for n in names]
    except OSError:
        return ["KMH", "Liters", "Celcius"]


speed_unit, fuel_unit, temp_unit = simhub_units()
SPEED_LABEL = "Speed [mph]" if speed_unit == "MPH" else "Speed [kmh]"
FUEL_LABEL = {"Liters": "Liter/Lap", "Kg": "Kg/Lap"}.get(fuel_unit, "Gallon/Lap")
TEMP_LABEL = "Core Temps [°F]" if temp_unit == "Fahrenheit" else "Core Temps [°C]"

S = 3   # the picture is drawn 3x larger and scaled down, so the chamfers and letters come out smooth
art = Image.new("RGB", (790 * S, 460 * S), BACK)
pen = ImageDraw.Draw(art)


def font(size, weight="SemiBold"):
    f = ImageFont.truetype(r"C:\Windows\Fonts\bahnschrift.ttf", size * S)
    try:
        f.set_variation_by_name(weight)
    except (OSError, ValueError):
        pass
    return f


def write(cx, cy, text, size, color=TEXT_GREY, weight="SemiBold"):
    """Texto fixo na imagem, centrado em (cx, cy)."""
    pen.text((cx * S, cy * S), text, font=font(size, weight), fill=color, anchor="mm")


def panel(x, y, w, h, style, head=0):
    """A panel with its top-left and bottom-right corners cut, like the Corvette's.
    head = height of the label band, on top."""
    fill, edge, strip = style

    def shape(i):   # o contorno, encolhido i px
        c = CUT
        return [((x + c + i * 0.4) * S, (y + i) * S), ((x + w - i) * S, (y + i) * S),
                ((x + w - i) * S, (y + h - c - i * 0.4) * S), ((x + w - c - i * 0.4) * S, (y + h - i) * S),
                ((x + i) * S, (y + h - i) * S), ((x + i) * S, (y + c + i * 0.4) * S)]
    pen.polygon(shape(0), fill=edge)
    pen.polygon(shape(2), fill=fill)
    if head:
        pen.polygon([((x + CUT + 1) * S, (y + 2) * S), ((x + w - 2) * S, (y + 2) * S), ((x + w - 2) * S, (y + head) * S),
                     ((x + 2) * S, (y + head) * S), ((x + 2) * S, (y + CUT + 1) * S)], fill=strip)
        pen.line([((x + 2) * S, (y + head) * S), ((x + w - 2) * S, (y + head) * S)], fill=edge, width=S)


def box(name, x, y, w, h, style, bind, fmt, samples, preview, font=NUM, font_h=NUM_H, **kw):
    """A panel with only the value, centred and clear of the chamfers."""
    panel(x, y, w, h, style)
    d.value(name, bind, fmt, list(samples), preview, x + CUT, y + (h - font_h) // 2, w - 2 * CUT, h=font_h, font=font,
            Background=style[0], **kw)


def cell(name, text, x, y, w, h, style, bind, fmt="0", samples=("88",), preview="1", head=28, size=17, **kw):
    """A panel with the label (in the picture) in a band on top and the value under it."""
    panel(x, y, w, h, style, head=head)
    write(x + w / 2 + 2, y + head / 2 + 1, text, size)
    d.value(name, bind, fmt, list(samples), preview, x + CUT, y + h - 53, w - 2 * CUT, Background=style[0], **kw)


def small(name, text, x, y, style, bind=None, fixed=None, color=WHITE):
    """A small cell (69 x 58): the label in the picture and a 32 px value; fixed = a fixed value, also in the picture."""
    panel(x, y, 69, 58, style, head=20)
    write(x + 36, y + 11, text, 14)
    if bind:
        d.value(name, bind, "0", ["88"], "3", x + 6, y + 23, 57, h=LABEL_H, font=LABEL, color=color, Background=style[0])
    else:
        write(x + 35, y + 39, fixed, 28, color=color, weight="Bold")


def fixed_cell(text, value, x, y, color):
    """A cell of the bottom-right corner: all fixed, in the function's colour."""
    panel(x, y, 80, 58, DARK, head=24)
    write(x + 41, y + 13, text, 14, color=color)
    write(x + 40, y + 41, value, 22, color=color, weight="Bold")


# MaxColors at the most: on a wheel without picture memory the background is cut down to these colours, and with fewer
# the panels' colours would stop matching the background the screen puts behind the values
d.add(Type="image", Name="Panels", X=0, Y=0, W=790, H=460, Image="panels@790x460", MaxColors=64)

# ---- left: pressures, tyre temperatures, brake bias, laps, settings
for (n, corner), (x, y) in zip(CORNERS, ((12, 2), (120, 2), (12, 62), (120, 62))):
    box(f"P {n}", x, y, 105, 58, BLUE, pressure(corner), "text", PRESSURE_SAMPLES, "23.9")
write(118, 132, TEMP_LABEL, 17)
for (n, corner), (x, y) in zip(CORNERS, ((12, 144), (120, 144), (12, 204), (120, 204))):
    box(f"T {n}", x, y, 105, 58, BLUE, f"ncalc:[TyreTemperature{corner}]", "0", ["188"], "112")
box("Brake bias", 12, 266, 120, 58, DARK, "brakeBias", "0.0", ["88.8"], "54.0")
box("Laps", 136, 266, 89, 58, DARK, "completedLaps", "0", ["188"], "0")
small("TC", "TC", 12, 328, BLUE, bind="tcLevel")
small("Multi", "Multi", 84, 328, GREEN, fixed="1")
small("ABS", "ABS", 156, 328, PINK, bind="absLevel")
small("Yaw", "Yaw", 12, 392, GREYP, bind="tcLevel")
small("Map", "Map", 156, 392, RED, fixed="1")

# ---- gear: white in the forward gears, green in neutral, red in reverse
d.value("Gear", "gearText", "gear", ["8", "N", "R"], "N", 232, 6, 196, h=170, font=103, empty="N", Background=BACK,
        ColorBind="gear", ColorStops=[{"Value": -1, "Color": "#FF2020"}, {"Value": 0, "Color": "#30B020"},
                                      {"Value": 1, "Color": WHITE}])

# ---- right: rpm, speed, fuel per lap
box("RPM", 436, 4, 209, 92, DARK, "rpm", "0", ["8888"], "1947", font=90, font_h=80, color=YELLOW)
cell("Speed", SPEED_LABEL, 648, 4, 130, 92, DARK, "speed", samples=["388"], preview="0", color=YELLOW)
cell("Fuel lap", FUEL_LABEL, 648, 100, 130, 92, DARK, "fuelLastLap", "0.00", ["8.88"], "0.00", color=YELLOW)

# ---- middle: difference and prediction on the left, last and best lap on the right
box("Split", 232, 200, 200, 58, DARK, "delta", "delta", ["+88.88"], "-0.40", empty="-.--",
    PositiveColor="#FF3030", NegativeColor="#30FF40")
box("Last lap", 436, 200, 209, 58, DARK, "lastLapTime", "laptime", ["8:88.888"], "1:00.000", color=YELLOW,
    empty="-:--.---")
box("Predicted", 232, 262, 200, 58, DARK, "predictedLap", "laptime", ["8:88.888"], "1:00.000", empty="-:--.---")
box("Best lap", 436, 262, 209, 58, DARK, "bestLapTime", "laptime", ["8:88.888"], "1:00.000", empty="-:--.---")

# ---- light and wiper icons (dark), right of the times
ICON = "#4A4E56"
def headlight(p, ox, oy, color):
    """The headlight icon (four strokes and the lens), its top-left corner at (ox, oy)."""
    for k in range(4):
        p.line([((ox + 4) * S, (oy + 12 + k * 9) * S), ((ox + 26) * S, (oy + 12 + k * 9) * S)], fill=color, width=2 * S)
    p.pieslice([((ox + 22) * S, (oy + 4) * S), ((ox + 68) * S, (oy + 48) * S)], -90, 90, outline=color, width=2 * S)
    p.line([((ox + 45) * S, (oy + 4) * S), ((ox + 45) * S, (oy + 48) * S)], fill=color, width=2 * S)


headlight(pen, 668, 200, ICON)
# aceso (azul) e a piscar quando se fazem sinais de luzes
lit = Image.new("RGB", (72 * S, 52 * S), BACK)
headlight(ImageDraw.Draw(lit), 0, 0, "#3C9CFF")
buf = io.BytesIO()
lit.resize((72, 52), Image.LANCZOS).save(buf, "PNG", optimize=True)
d.images["headlight-on@72x52"] = base64.b64encode(buf.getvalue()).decode("ascii")
# iRacing only sets dcHeadlightFlash for about 70 ms per press (measured): it blinks for 2.5 s after each change of it
FLASHER = ("ncalc:changed(2500, isnull([DataCorePlugin.GameRawData.Telemetry.dcHeadlightFlash], 0)) "
           "and blink('flasher', 150, true)")

pen.arc([(676 * S, 268 * S), (740 * S, 332 * S)], 215, 325, fill=ICON, width=2 * S)   # limpa-vidros: o vidro
pen.line([(708 * S, 312 * S), (690 * S, 276 * S)], fill=ICON, width=2 * S)             # e a escova
pen.line([(686 * S, 300 * S), (730 * S, 300 * S)], fill=ICON, width=2 * S)

# ---- bottom-right corner: functions iRacing doesn't use, fixed
for text, value, x, y, color in (("Page", "1", 446, 330, "#E03070"), ("Wiper", "1", 530, 330, "#3090E0"),
                                 ("Dimmer", "4", 614, 330, "#D8D020"), ("Func A", "1", 698, 330, "#E08030"),
                                 ("Launch", "11", 614, 392, "#30C040"), ("Func B", "1", 698, 392, WHITE)):
    fixed_cell(text, value, x, y, color)
for text, value, x, color in (("A/C", "Auto", 486, "#3090E0"), ("Fans", "On", 570, "#E03030")):
    write(x, 408, text, 20, color=color)
    write(x, 434, value, 20, color=color)

d.add(Type="image", Name="Headlight flash", X=668, Y=200, W=72, H=52, Image="headlight-on@72x52", MaxColors=8,
      Visible=FLASHER, PreviewVisible=False)

# ---- pit limiter: a green band with the speed, over the corner of fixed functions (only picture under it)
d.banner("Pit limiter", "PIT LIMITER", 232, 328, 546, 124, "#20A030", WHITE, "pitLimiter", speed=True)

# ---- setting-change popups (over the four times) and the start-up sequence
d.popups(232, 200, 413, 120, ["TC", "ABS", "BB"])
d.startup("CORVETTE", "Z06 GT3.R", logo="corvette")

buf = io.BytesIO()
art.resize((790, 460), Image.LANCZOS).save(buf, "PNG", optimize=True)
d.images["panels@790x460"] = base64.b64encode(buf.getvalue()).decode("ascii")
d.save()
