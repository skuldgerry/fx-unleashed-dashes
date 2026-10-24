#!/usr/bin/env python3
"""add_startup_logo.py - gives a converted dash the start-up sequence of the from-scratch dashes, with the car's logo.

  python scripts/add_startup_logo.py out/iracing/lmgt3-mustang-iracing.json --logo ford-performance --brand FORD --model "MUSTANG GT3"

The from-scratch dashes (scripts/dashkit.py, Dash.startup) show a whole screen with the car while the ignition is off and
for 2 s after it comes on: the logo, the model and "IGNITION OFF" / "SYSTEM CHECK". This adds the same to a dash made
elsewhere (the LMU conversions in out/iracing/), on top of everything else, so every car looks the same at start-up.

The logo is reference/logos/<logo>.png (outside git: car makers' logos are their marks). The result therefore stays in
out/ and the local SimHub, like the converted dashes themselves. Running it again replaces what an earlier run added
(elements named "Startup ..." / "Ignition off ..." and the logo picture). Without the logo file nothing is changed.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashkit import ROOT, Dash  # noqa: E402

KEYS = ("Ignition off ", "Startup ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dash")
    ap.add_argument("--logo", required=True, help="name of reference/logos/<logo>.png")
    ap.add_argument("--brand", required=True, help="the brand, shown large when there is no logo")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", help="where to write (default: over the input)")
    a = ap.parse_args()

    src = Path(a.dash)
    if not (ROOT / "reference" / "logos" / f"{a.logo}.png").exists():
        print(f"reference/logos/{a.logo}.png is missing: nothing changed")
        return 1
    d = json.loads(src.read_text(encoding="utf-8-sig"))

    # what the from-scratch dashes draw, built by the same code
    kit = Dash("tmp", "tmp", "tmp", "tmp")
    kit.startup(a.brand, a.model, logo=a.logo)
    added = [{k: v for k, v in e.items() if k != "_variant"} for e in kit.els if e.get("_variant") != "text"]

    # an earlier run's elements and picture go first
    images = d.get("Images") or {}
    d["Elements"] = [e for e in d["Elements"] if not str(e.get("Name", "")).startswith(KEYS)]
    for name in list(images):
        if name.startswith(f"logo-{a.logo}@") or (name.startswith("logo-") and name not in kit.local_images):
            images.pop(name)
    images.update(kit.local_images)
    d["Images"] = images
    d["Elements"] += added   # last: drawn over everything

    out = Path(a.out) if a.out else src
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{out}: {len(added)} start-up elements added, logo {a.logo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
