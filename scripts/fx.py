#!/usr/bin/env python3
"""fx.py - local tools for making FX Unleashed dashes.

Uses Python's standard library only (3.8+). Subcommands:

  setup                      clones/updates the fx-unleashed repo and builds fxdash
  gates DASH [options]       runs check + fit-bands + verify + render and sums up
  render DASH [OUT.png]      renders only (preview or demo)
  install DASH [--dry-run]   copies the dash into SimHub's Dashes folder
  carids LOG                 pulls the car ids out of the plugin's log lines

Environment variables:
  FXDASH_EXE        path to an fxdash.exe already built (skips setup)
  SIMHUB_INSTALL_PATH  SimHub's folder (default C:\\Program Files (x86)\\SimHub)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPS = ROOT / ".deps"
REPO_DIR = DEPS / "fx-unleashed"
REPO_URL = "https://github.com/fxunleashed/fx-unleashed.git"
CSPROJ = Path("tools") / "fxdash" / "fxdash.csproj"
BUILT_EXE = REPO_DIR / "tools" / "fxdash" / "bin" / "Release" / "net48" / "fxdash.exe"
OUT = ROOT / "out"
DEFAULT_PAD = "10,20"
DEFAULT_SIMHUB = r"C:\Program Files (x86)\SimHub"


# --------------------------------------------------------------------------- util
def simhub_dir() -> Path:
    return Path(os.environ.get("SIMHUB_INSTALL_PATH") or DEFAULT_SIMHUB)


def dashes_install_dir() -> Path:
    return simhub_dir() / "PluginsData" / "Common" / "FXProRpmSync" / "Dashes"


def fxdash_exe() -> Path:
    env = os.environ.get("FXDASH_EXE")
    if env:
        return Path(env)
    return BUILT_EXE


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def fxdash(args: list[str]) -> tuple[int, object, str]:
    """Runs fxdash. Returns (exit code, JSON or None, raw stdout)."""
    exe = fxdash_exe()
    if not exe.exists():
        sys.exit(f"fxdash not found at {exe}\nRun first:  python scripts/fx.py setup")
    cmd = [str(exe), *args, "--simhub", str(simhub_dir())]
    cp = run(cmd)
    data = None
    if cp.stdout.strip():
        try:
            data = json.loads(cp.stdout)
        except json.JSONDecodeError:
            data = None
    if cp.returncode == 2:
        sys.stderr.write((cp.stderr or cp.stdout).strip() + "\n")
    return cp.returncode, data, cp.stdout


def get(d, name, default=None):
    """Case-insensitive access to a JSON dict."""
    if not isinstance(d, dict):
        return default
    low = name.lower()
    for k, v in d.items():
        if k.lower() == low:
            return v
    return default


def dash_id(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    ident = data.get("Id") or path.stem
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", ident):
        sys.exit(f"Invalid Id '{ident}': use lower case, digits and hyphens.")
    return ident


# --------------------------------------------------------------------------- setup
def cmd_setup(_a) -> int:
    if os.environ.get("FXDASH_EXE"):
        print(f"FXDASH_EXE set ({fxdash_exe()}), nothing to build.")
        return 0
    problems = []
    if not shutil.which("git"):
        problems.append("git isn't on the PATH")
    if not shutil.which("dotnet"):
        problems.append("the dotnet SDK isn't on the PATH (install the .NET SDK 8 or later)")
    if not simhub_dir().exists():
        problems.append(f"SimHub not found at {simhub_dir()} (set SIMHUB_INSTALL_PATH)")
    if problems:
        print("Missing requirements:")
        for p in problems:
            print("  -", p)
        return 1

    DEPS.mkdir(exist_ok=True)
    if (REPO_DIR / ".git").exists():
        print("Updating fx-unleashed...")
        cp = run(["git", "-C", str(REPO_DIR), "pull", "--ff-only"])
    else:
        print("Cloning fx-unleashed...")
        cp = run(["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)])
    sys.stdout.write(cp.stdout + cp.stderr)
    if cp.returncode:
        return cp.returncode

    print("Building fxdash (SimHub must not be running)...")
    cp = run(["dotnet", "build", "-c", "Release", str(REPO_DIR / CSPROJ)])
    sys.stdout.write(cp.stdout[-3000:] + cp.stderr[-2000:])
    if cp.returncode or not BUILT_EXE.exists():
        print(f"\nFailed. Expected {BUILT_EXE}. See the output above (usually SimHub's DLLs are missing).")
        return 1
    print(f"\nOK: {BUILT_EXE}")
    return 0


# --------------------------------------------------------------------------- gates
def summarize_check(res) -> tuple[bool, list[str]]:
    lines = []
    ok = bool(get(res, "ok", False))
    lines.append(f"  check   : {'OK' if ok else 'FAILED'}  "
                 f"({get(res, 'errors', 0)} errors, {get(res, 'warnings', 0)} warnings)")
    for i in get(res, "issues", []) or []:
        lvl = get(i, "Level", "")
        if str(lvl).lower() in ("error", "warning", "warn"):
            lines.append(f"      [{lvl}] {get(i, 'Element', '')}: {get(i, 'Message', '')}")
    cost = get(res, "cost", {}) or {}
    if cost:
        lines.append(f"      cost: {get(cost, 'Elements')} elements, "
                     f"{get(cost, 'DynamicElements')} dynamic, "
                     f"static {get(cost, 'StaticBytes')} B (~{get(cost, 'StaticSeconds')} s), "
                     f"RAM {get(cost, 'RamBytes')}/{get(cost, 'RamBudget')} B")
    return ok, lines


def summarize_verify(res) -> tuple[bool, list[str]]:
    ok = bool(get(res, "ok", False))
    lines = [f"  verify  : {'OK' if ok else 'FAILED'}  "
             f"(average {get(res, 'AvgBytesPerSecond')} B/s, worst second {get(res, 'WorstSecondBytes')} B; "
             "the screen's limit ~25600 B/s)"]
    for key in ("Problems", "Notes"):
        for p in get(res, key, []) or []:
            lines.append(f"      {key[:-1] if key == 'Problems' else 'Note'}: {p}")
    if get(res, "RedrawMismatch"):
        lines.append(f"      RedrawMismatch: {get(res, 'RedrawMismatch')}")
    return ok, lines


def cmd_gates(a) -> int:
    dash = Path(a.dash).resolve()
    if not dash.exists():
        sys.exit(f"Doesn't exist: {dash}")
    ident = dash_id(dash)
    out = OUT / ident
    out.mkdir(parents=True, exist_ok=True)
    pad = a.pad or DEFAULT_PAD
    print(f"== {ident}  ({dash.relative_to(ROOT) if ROOT in dash.parents else dash})")
    failed = False

    # 1) check
    code, res, raw = fxdash(["check", str(dash), "--pad", pad])
    (out / "check.json").write_text(raw, encoding="utf-8")
    ok, lines = summarize_check(res) if res is not None else (False, ["  check   : no JSON output"])
    print("\n".join(lines))
    failed |= not ok or code != 0

    # 2) fit-bands (writes only if there are changes)
    fitted = out / f"{ident}.fitted.json"
    if fitted.exists():
        fitted.unlink()
    code, res, raw = fxdash(["fit-bands", str(dash), str(fitted)])
    changes = get(res, "changes", []) or []
    if changes:
        print(f"  fit     : {len(changes)} changes suggested -> {fitted.relative_to(ROOT)}")
        for c in changes[:10]:
            print("      -", c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
        if a.apply_fit and fitted.exists():
            shutil.copyfile(fitted, dash)
            print("      applied to the original file (--apply-fit)")
        else:
            print("      (use --apply-fit to apply them to the original file)")
    else:
        print("  fit     : no changes")

    # 3) verify
    vargs = ["verify", str(dash), "--pad", pad]
    if a.overlays:
        vargs.append("--overlays")
    if a.tiles:
        vargs.append("--tiles")
    if a.demo:
        vargs.append("--demo")
    if a.seconds:
        vargs += ["--seconds", str(a.seconds)]
    code, res, raw = fxdash(vargs)
    (out / "verify.json").write_text(raw, encoding="utf-8")
    ok, lines = summarize_verify(res) if res is not None else (False, ["  verify  : no JSON output"])
    print("\n".join(lines))
    failed |= not ok or code != 0

    # 4) render
    png = out / f"{ident}.png"
    code, _, _ = fxdash(["render", str(dash), str(png), "--pad", pad])
    if code == 0 and png.exists():
        print(f"  render  : {png.relative_to(ROOT)}")
    else:
        print("  render  : FAILED")
        failed = True

    print("\nRESULT:", "FAILED" if failed else "all OK")
    return 1 if failed else 0


def cmd_render(a) -> int:
    dash = Path(a.dash).resolve()
    ident = dash_id(dash)
    (OUT / ident).mkdir(parents=True, exist_ok=True)
    png = Path(a.out) if a.out else OUT / ident / f"{ident}-{a.mode}.png"
    args = ["render", str(dash), str(png), "--mode", a.mode, "--pad", a.pad or DEFAULT_PAD]
    if a.page is not None:
        args += ["--page", str(a.page)]
    if a.mode == "demo":
        args += ["--seconds", str(a.seconds or 5)]
    code, _, raw = fxdash(args)
    print(png if code == 0 else raw)
    return code


# --------------------------------------------------------------------------- install
def cmd_install(a) -> int:
    dash = Path(a.dash).resolve()
    ident = dash_id(dash)
    dest_dir = dashes_install_dir()
    dest = dest_dir / f"{ident}.json"
    print(f"{dash.name} -> {dest}")
    if a.dry_run:
        print("(dry-run, nothing copied)")
        return 0
    if not dest_dir.parent.exists():
        sys.exit(f"The plugin's folder doesn't exist: {dest_dir.parent}\n"
                 "Has SimHub run with the FX Unleashed plugin installed?")
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(dash, dest)
    print("Copied. In SimHub, reload the plugin's dash list.")
    return 0


# --------------------------------------------------------------------------- carids
CAR_RE = re.compile(r"\[FXProRpmSync\]\s+car\s+(?P<key>.+?):\s*(?P<src>[^;]*);")


def cmd_carids(a) -> int:
    path = Path(a.log)
    if not path.exists():
        sys.exit(f"Doesn't exist: {path}")
    seen: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = CAR_RE.search(line)
        if m:
            seen[m["key"].strip()] = m["src"].strip()
    if a.game:
        seen = {k: v for k, v in seen.items() if k.lower().startswith(a.game.lower())}
    if not seen:
        print("No car found in that log.")
        return 1
    for k in sorted(seen):
        print(f'{k}    ({seen[k]})')
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("setup", help="clones and builds fxdash").set_defaults(fn=cmd_setup)

    g = sub.add_parser("gates", help="check + fit-bands + verify + render")
    g.add_argument("dash")
    g.add_argument("--pad")
    g.add_argument("--overlays", action="store_true")
    g.add_argument("--tiles", action="store_true")
    g.add_argument("--demo", action="store_true")
    g.add_argument("--seconds", type=int)
    g.add_argument("--apply-fit", action="store_true")
    g.set_defaults(fn=cmd_gates)

    r = sub.add_parser("render", help="renders to PNG")
    r.add_argument("dash")
    r.add_argument("out", nargs="?")
    r.add_argument("--mode", choices=["preview", "demo"], default="preview")
    r.add_argument("--seconds", type=int)
    r.add_argument("--page", type=int)
    r.add_argument("--pad")
    r.set_defaults(fn=cmd_render)

    i = sub.add_parser("install", help="copies into SimHub")
    i.add_argument("dash")
    i.add_argument("--dry-run", action="store_true")
    i.set_defaults(fn=cmd_install)

    c = sub.add_parser("carids", help="lists car ids from a SimHub log")
    c.add_argument("log")
    c.add_argument("--game", help="filter by the game prefix, e.g. IRacing")
    c.set_defaults(fn=cmd_carids)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
