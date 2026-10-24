#!/usr/bin/env python3
"""gates_api.py - the four gates (check, fit-bands, verify, render) through the plugin's local API, without fxdash.exe.

  python scripts/gates_api.py DASH.json [--pad 10,20] [--apply-fit]

Needs SimHub open with FX Unleashed (http://127.0.0.1:8899). Nothing goes to the wheel: verify runs on a simulated
screen. Results in out/<id>/ (check.json, verify.json, <id>.png, <id>-demo.png).
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://127.0.0.1:8899/api"


def post(path, body, raw=False):
    req = urllib.request.Request(f"{API}/{path}", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    return data if raw else json.loads(data.decode("utf-8"))


def get(d, name, default=None):
    low = name.lower()
    return next((v for k, v in d.items() if k.lower() == low), default) if isinstance(d, dict) else default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dash")
    ap.add_argument("--pad", default="10,20")
    ap.add_argument("--apply-fit", action="store_true")
    a = ap.parse_args()
    path = Path(a.dash).resolve()
    body = path.read_bytes()
    ident = json.loads(body.decode("utf-8-sig"))["Id"]
    out = ROOT / "out" / ident
    out.mkdir(parents=True, exist_ok=True)
    left, top = a.pad.split(",")
    pad = f"left={left}&top={top}"
    failed = False
    print(f"== {ident}")

    res = post(f"check?{pad}", body)
    (out / "check.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    errors, warnings = get(res, "errors", 0), get(res, "warnings", 0)
    print(f"  check   : {errors} errors, {warnings} warnings")
    for i in get(res, "issues", []) or []:
        print(f"      [{get(i, 'Level')}] {get(i, 'Element')}: {get(i, 'Message')}")
    cost = get(res, "cost", {}) or {}
    print(f"      cost: static ~{get(cost, 'StaticSeconds')} s, RAM {get(cost, 'RamBytes')} B")
    failed |= bool(errors or warnings)

    res = post("fit-bands", body)
    changes = get(res, "changes", []) or []
    print(f"  fit     : {len(changes)} changes" if changes else "  fit     : no changes")
    for c in changes:
        print("      -", c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
    if changes and a.apply_fit and get(res, "elements"):
        d = json.loads(body.decode("utf-8-sig"))
        d["Elements"] = get(res, "elements")
        path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        body = path.read_bytes()
        print("      applied to the file (--apply-fit)")
    elif changes:
        failed = True

    res = post(f"verify?tiles=1&{pad}", body)
    (out / "verify.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    ok = bool(get(res, "Ok"))
    print(f"  verify  : {'OK' if ok else 'FAILED'} (average {get(res, 'AvgBytesPerSecond')} B/s, worst second "
          f"{get(res, 'WorstSecondBytes')} B, flashing updates {get(res, 'FlashingUpdates')})")
    for p in get(res, "Problems", []) or []:
        print("      problem:", p)
    failed |= not ok

    for mode, name in (("preview", f"{ident}.png"), ("demo&seconds=97", f"{ident}-demo.png")):
        (out / name).write_bytes(post(f"render?mode={mode}&tiles=1&{pad}", body, raw=True))
    print(f"  render  : out/{ident}/{ident}.png, out/{ident}/{ident}-demo.png")
    print("RESULT:", "FAILED" if failed else "all OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
