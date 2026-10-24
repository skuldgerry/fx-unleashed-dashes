#!/usr/bin/env python3
"""capture_shiftlights.py - records the sim's screen with the rpm of each frame, to measure the shift lights.

  python scripts/capture_shiftlights.py [--seconds 45] [--wait 900] [--car bmwm4gt3] [--bbox x0,y0,x1,y1] [--fps 8]

--bbox records only that area of the main monitor (the light bar): the files stay small and it can record 20 or more
frames a second for minutes.

Waits (up to --wait seconds) for the car to be on track, then records the main monitor for --seconds, about 8 frames a
second, and for each the rpm, gear and speed read from SimHub (the plugin's API). Everything goes to
out/shiftlights/<car>/: JPEG frames and frames.csv. Records only with the car on track.

To measure: on track, rev slowly in 1st, 2nd and 3rd up to the limiter, with the car's dash in view.
"""
import argparse
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".deps" / "pylib"))   # Pillow, installed for the project only
from PIL import ImageGrab  # noqa: E402

P = "DataCorePlugin.GameData.NewData."
T = "DataCorePlugin.GameRawData.Telemetry."
NAMES = [P + "CarId", P + "Rpms", P + "Gear", P + "SpeedKmh", P + "Throttle", T + "IsOnTrack", "DataCorePlugin.GameRunning"]


def props():
    url = "http://127.0.0.1:8899/api/props?names=" + ",".join(NAMES)
    with urllib.request.urlopen(url, timeout=3) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=45)
    ap.add_argument("--wait", type=float, default=900)
    ap.add_argument("--car")
    ap.add_argument("--bbox", help="x0,y0,x1,y1 on the main monitor")
    ap.add_argument("--fps", type=float, default=8)
    ap.add_argument("--name", help="output folder inside out/shiftlights (default: the car's id)")
    a = ap.parse_args()

    t0 = time.time()
    while True:
        try:
            p = props()
        except OSError:
            p = {}
        on_track = p.get(T + "IsOnTrack") and p.get("DataCorePlugin.GameRunning")
        if on_track and (not a.car or p.get(P + "CarId") == a.car) and (p.get(P + "Rpms") or 0) > 500:
            break
        if time.time() - t0 > a.wait:
            print("the car didn't get on track in time; nothing recorded")
            return 1
        time.sleep(1)

    car = p.get(P + "CarId") or "car"
    out = ROOT / "out" / "shiftlights" / (a.name or car)
    bbox = tuple(int(v) for v in a.bbox.split(",")) if a.bbox else None
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("f*.jpg"):
        old.unlink()
    rows, start, n = [], time.time(), 0
    while time.time() - start < a.seconds:
        tick = time.time()
        try:
            p = props()
        except OSError:
            continue
        im = ImageGrab.grab(bbox=bbox)   # the main monitor, or only the area asked for
        name = f"f{n:04d}.jpg"
        im.save(out / name, "JPEG", quality=90 if bbox else 82)
        rows.append([name, round(tick - start, 3), round(p.get(P + "Rpms") or 0), p.get(P + "Gear"),
                     round(p.get(P + "SpeedKmh") or 0, 1), round(p.get(P + "Throttle") or 0)])
        n += 1
        time.sleep(max(0, 1 / a.fps - (time.time() - tick)))
    with open(out / "frames.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame", "t", "rpm", "gear", "kmh", "throttle"])
        w.writerows(rows)
    print(f"{car}: {n} frames in {a.seconds:.0f} s -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
