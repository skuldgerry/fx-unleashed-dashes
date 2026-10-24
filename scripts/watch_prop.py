#!/usr/bin/env python3
"""watch_prop.py - logs every change of value of SimHub properties, with its time.

  python scripts/watch_prop.py --seconds 300 PROP [PROP...]

Reads the properties about 40 times a second through the plugin's API and prints a line whenever one changes.
For seeing how a value really behaves in the sim (for example dcHeadlightFlash while flashing the headlights).
"""
import argparse
import json
import sys
import time
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=300)
    ap.add_argument("props", nargs="+")
    a = ap.parse_args()
    url = "http://127.0.0.1:8899/api/props?names=" + ",".join(a.props)
    last, start, reads = {}, time.time(), 0
    while time.time() - start < a.seconds:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                now = json.loads(r.read().decode("utf-8"))
        except OSError:
            time.sleep(0.5)
            continue
        reads += 1
        for name in a.props:
            v = now.get(name)
            if name not in last or v != last[name]:
                print(f"{time.time() - start:8.3f}s  {name.rsplit('.', 1)[-1]} = {v!r}", flush=True)
                last[name] = v
        time.sleep(0.02)
    print(f"done: {reads} reads in {a.seconds:.0f} s ({reads / a.seconds:.0f} a second)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
