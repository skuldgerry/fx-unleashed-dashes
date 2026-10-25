"""dashkit.py - the parts shared by the generators of the from-scratch dashes (make_*.py).

A dash is only the screen's own shapes and text. The fonts are the ones chosen on the wheel: 94 (32 px) for labels,
110 (50 px) for numbers. A box with a label and a value needs 88 px of height (frame 2 + label 32 + value 50 + gap 2 +
frame 2); a box with only a value, 58 px: below that the text's band touches the lines and flickers.
"""
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEL = "DataCorePlugin.GameRawData.Telemetry."

WHITE, BLACK, GREY = "#FFFFFF", "#000000", "#909090"
LABEL, LABEL_H = 94, 32
NUM, NUM_H = 110, 50


def pressure(corner):
    """A tyre's pressure in SimHub's unit, already formatted (text)."""
    p = f"[TyrePressure{corner}]"
    return f"ncalc:if([TyrePressureUnit]='Psi', format({p}, '0.0'), if([TyrePressureUnit]='Kpa', format({p}, '0'), format({p}, '0.00')))"


_widths = {}


def text_width(font, text):
    """Width of a text in one of the screen's fonts, in px (asks the plugin: needs SimHub open)."""
    if text not in _widths:
        url = "http://127.0.0.1:8899/api/fonts?sample=" + urllib.parse.quote(text)
        with urllib.request.urlopen(url, timeout=20) as r:
            _widths[text] = {f["id"]: f["sampleWidth"] for f in json.loads(r.read().decode("utf-8"))}
    return _widths[text][font]


# settings changed on track: label, colour, bind, format, widest texts, what the popup watches.
# The throttle map (dcThrottleShape) only exists in some iRacing cars; where it doesn't, its popup never shows.
SETTINGS = {
    "TC": ("TC", "#00B0FF", "tcLevel", "0", ["88"], "[TCLevel]"),
    "ABS": ("ABS", "#FFD000", "absLevel", "0", ["88"], "[ABSLevel]"),
    "BB": ("BRAKE BIAS", "#FF2020", "brakeBias", "0.0", ["88.8"], "[BrakeBias]"),
    "THR": ("THROTTLE", "#20E040", f"prop:{TEL}dcThrottleShape", "0", ["88"], f"isnull([{TEL}dcThrottleShape], 0)"),
}

PRESSURE_SAMPLES = ["28.8", "1.65", "188"]
CORNERS = (("FL", "FrontLeft"), ("FR", "FrontRight"), ("RL", "RearLeft"), ("RR", "RearRight"))


class Dash:
    def __init__(self, folder, ident, name, description):
        self.out = ROOT / "dashes" / folder / f"{ident}.json"
        self.name, self.description = name, description
        self.els = []
        self.images = {}        # name -> PNG in base64, for image elements
        self.local_images = {}  # the same, for the local version only (logos)

    def add(self, **e):
        self.els.append(e)
        return e

    def frame(self, name, x, y, w, h, color=WHITE, fill=None, radius=0):
        e = dict(Type="box", Name=f"{name} frame", X=x, Y=y, W=w, H=h, Color=color, Border=2)
        if fill:
            e["Fill"] = fill
        if radius:
            e["Radius"] = radius
        self.add(**e)

    def label(self, name, text, x, y, w, h=LABEL_H, font=LABEL, color=WHITE, align="center", **kw):
        self.add(Type="label", Name=f"{name} label", X=x, Y=y, W=w, H=h, Text=text, Font=font, Color=color, Align=align, **kw)

    def text(self, name, bind, texts, x, y, w, color=WHITE, **kw):
        """A label that changes with a formula (SimHub's unit, for example)."""
        self.add(Type="value", Name=f"{name} label", X=x, Y=y, W=w, H=LABEL_H, Bind=bind, Format="text", Font=LABEL,
                 Color=color, Align="center", Samples=texts, PreviewText=texts[0], Empty=texts[0], **kw)

    def value(self, name, bind, fmt, samples, preview, x, y, w, h=NUM_H, font=NUM, color=WHITE, empty="-",
              align="center", **kw):
        self.add(Type="value", Name=name, X=x, Y=y, W=w, H=h, Bind=bind, Format=fmt, Font=font, Color=color,
                 Align=align, Samples=samples, PreviewText=preview, Empty=empty, **kw)

    def cell(self, name, text, x, y, w, h, bind, fmt="0", samples=("88",), preview="1", frame=WHITE, fill=None,
             color=WHITE, label_color=None, **kw):
        """A box with the label on top and the value under it. bind None = fixed text (the `preview`).
        text can be (formula, texts) for a label with a unit."""
        self.frame(name, x, y, w, h, color=frame, fill=fill)
        if fill:
            kw["Background"] = fill
        if isinstance(text, tuple):
            self.text(name, text[0], text[1], x + 2, y + 2, w - 4, color=label_color or color,
                      **({"Background": fill} if fill else {}))
        else:
            self.label(name, text, x + 2, y + 2, w - 4, color=label_color or color)
        if bind:
            self.value(name, bind, fmt, list(samples), preview, x + 2, y + h - 54, w - 4, color=color, **kw)
        else:
            self.label(f"{name} fixed", preview, x + 2, y + h - 54, w - 4, h=NUM_H, font=NUM, color=color)

    def box_value(self, name, x, y, w, h, bind, fmt, samples, preview, frame=WHITE, fill=None, font=NUM, font_h=NUM_H,
                  **kw):
        """A box with only the value, centred."""
        self.frame(name, x, y, w, h, color=frame, fill=fill)
        if fill:
            kw["Background"] = fill
        self.value(name, bind, fmt, list(samples), preview, x + 2, y + (h - font_h) // 2, w - 4, h=font_h, font=font, **kw)

    def banner(self, name, text, x, y, w, h, fill, color, cond, speed=False):
        """A warning that comes and goes: covers the whole area; goes after everything it covers.
        speed = also shows the speed, next to the text."""
        v = dict(Visible=cond, PreviewVisible=False)
        self.add(Type="rect", Name=f"{name} background", X=x, Y=y, W=w, H=h, Color=fill, **v)
        tw = w // 2 if speed else w
        self.add(Type="label", Name=name, X=x + 2, Y=y + (h - NUM_H) // 2, W=tw - 4, H=NUM_H, Text=text, Font=NUM,
                 Color=color, Align="center", **v)
        if speed:
            self.value(f"{name} speed", "speed", "0", ["388"], "60", x + tw, y + (h - NUM_H) // 2, w - tw - 2,
                       color=color, Background=fill, **v)

    def popups(self, x, y, w, h, items):
        """Setting-change popups: for 2 s the new value shows large in the given area, which must cover whole boxes (a
        half-covered value redraws through the popup and flickers) and can't have bars under it.
        items = SETTINGS keys. 150 px high or more puts the label above the value; less, beside it."""
        fill = "#101418"
        for key in items:
            text, color, bind, fmt, samples, watched = SETTINGS[key]
            v = dict(Visible=f"ncalc:changed(2000, {watched})", PreviewVisible=False)
            # a frame of two rectangles: a box without round corners that comes and goes would be a picture
            self.add(Type="rect", Name=f"{key} popup border", X=x, Y=y, W=w, H=h, Color=color, **v)
            self.add(Type="rect", Name=f"{key} popup background", X=x + 4, Y=y + 4, W=w - 8, H=h - 8, Color=fill, **v)
            if h >= 150:
                self.add(Type="label", Name=f"{key} popup label", X=x + 6, Y=y + 8, W=w - 12, H=LABEL_H, Text=text,
                         Font=LABEL, Color=color, Align="center", **v)
                self.value(f"{key} popup value", bind, fmt, samples, samples[0], x + 6, y + 42, w - 12, h=98, font=82,
                           Background=fill, **v)
            else:
                half = (w - 12) // 2
                self.add(Type="label", Name=f"{key} popup label", X=x + 6, Y=y + (h - LABEL_H) // 2, W=half,
                         H=LABEL_H, Text=text, Font=LABEL, Color=color, Align="center", **v)
                self.value(f"{key} popup value", bind, fmt, samples, samples[0], x + 6 + half, y + (h - NUM_H) // 2,
                           half, Background=fill, **v)

    def startup(self, brand, model, logo=None):
        """The start-up sequence, as in the converted dashes: the whole screen with the car while the ignition is off,
        and for 2 s after it comes on.
        logo = the name of a file in reference/logos/<logo>.png (outside git: logos are other people's marks).
        If it exists, the dash is saved in two versions: the repository's, text only, and out/local/'s with the logo,
        which is the one installed (see save).
        Only for games that report the ignition: in one that doesn't, the dash would stay covered."""
        brand_font, brand_h = next(((f, fh) for f, fh in ((47, 112), (19, 90), (90, 80), (99, 64))
                                    if text_width(f, brand) <= 760), (99, 64))
        picture = self._logo(logo) if logo else None
        for key, cond, line, color in (
                ("Ignition off", "ncalc:![EngineIgnitionOn]", "IGNITION OFF", GREY),
                ("Startup", "ncalc:changed(2000, [EngineIgnitionOn]) and [EngineIgnitionOn]", "SYSTEM CHECK", "#30FF40")):
            v = dict(Visible=cond, PreviewVisible=False)
            self.add(Type="rect", Name=f"{key} background", X=0, Y=0, W=790, H=460, Color=BLACK, **v)

            def text(part, y, h, font, what, col=WHITE, variant=None):
                e = self.add(Type="label", Name=f"{key} {part}", X=10, Y=y, W=770, H=h, Text=what, Font=font, Color=col,
                             Align="center", **v)
                if variant:
                    e["_variant"] = variant
            # text only: the brand large, the model and the state
            only = "text" if picture else None
            text("brand", 140 - brand_h // 2, brand_h, brand_font, brand, variant=only)
            text("model", 230, NUM_H, NUM, model, variant=only)
            text("state", 320, LABEL_H, LABEL, line, color, variant=only)
            if picture:   # with a logo: the picture on top, the model and the state under it
                name, w, h = picture
                self.add(Type="image", Name=f"{key} logo", X=(790 - w) // 2, Y=30 + (250 - h) // 2, W=w, H=h, Image=name,
                         MaxColors=32, _variant="logo", **v)
                text("model (logo)", 300, NUM_H, NUM, model, variant="logo")
                text("state (logo)", 376, LABEL_H, LABEL, line, color, variant="logo")

    def _logo(self, key):
        """Reads reference/logos/<key>.png, fits it in 420 x 250 on black and keeps it for the local version."""
        path = ROOT / "reference" / "logos" / f"{key}.png"
        if not path.exists():
            return None
        import io
        import sys
        import base64
        sys.path.insert(0, str(ROOT / ".deps" / "pylib"))   # Pillow, installed for the project only
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        im.thumbnail((420, 250), Image.LANCZOS)
        flat = Image.new("RGB", im.size, BLACK)
        flat.paste(im, mask=im.split()[3])
        buf = io.BytesIO()
        flat.save(buf, "PNG", optimize=True)
        name = f"logo-{key}@{flat.width}x{flat.height}"
        self.local_images[name] = base64.b64encode(buf.getvalue()).decode("ascii")
        return name, flat.width, flat.height

    def _write(self, path, variant):
        """Saves one version's elements: "text" (repository) or "logo" (local)."""
        other = "logo" if variant == "text" else "text"
        els = [{k: v for k, v in e.items() if k != "_variant"} for e in self.els if e.get("_variant") != other]
        d = {"FormatVersion": 2, "Id": self.out.stem, "Name": self.name, "Author": "skuldgerry",
             "Description": self.description, "Elements": els}
        images = dict(self.images, **(self.local_images if variant == "logo" else {}))
        if images:
            d["Images"] = images
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {len(els)} elements")

    def save(self):
        """dashes/<folder>/<id>.json: the repository's version, without third-party material.
        out/local/<id>.json: the same with the logo, when there is one; the one installed in SimHub."""
        self._write(self.out, "text")
        if self.local_images:
            self._write(ROOT / "out" / "local" / self.out.name, "logo")
