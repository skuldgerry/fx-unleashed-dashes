#!/usr/bin/env python3
"""make_profile.py - my FX Unleashed setup as a file anyone can import (About > Backup > Import settings).

  python scripts/make_profile.py --from-simhub   # refresh profile/skuldgerry.fxsettings.json from this PC's settings
  python scripts/make_profile.py                 # build out/release/skuldgerry.fxsettings.zip (settings + this repo's dashes)

The file is what the plugin's own export writes (SettingsTransfer.Export): the settings without what belongs to one PC
and one wheel. On top of that, for sharing:
  - the light preset gets a neutral name;
  - dashes per car point only at dashes of this repository (cars on any other dash are left out, so they use the default
    dash), and the old id of the default dash becomes gt-default;
  - no screensavers of mine: my pictures and GIFs are left out (only the plugin's built-in ones can be picked or take
    turns), and the driver number screensaver's card goes back to its default (it has my name).
The zip carries this repository's dashes, so an import brings them too; it goes into a release of this repository
(out/ is not in git). An import replaces the settings of whoever
imports it (the plugin keeps a copy of theirs first).
"""
import argparse
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "profile"
NAME = "skuldgerry"
SIMHUB_SETTINGS = Path(r"C:\Program Files (x86)\SimHub\PluginsData\Common\FXProRpmSyncPlugin.GeneralSettings.json")
PLUGIN = "0.7.61"
PRESET_NAME = "skuldgerry"
RENAMED_DASHES = {"lovely-default": "gt-default"}
# the plugin's own screensavers (IdleScreens: the logo, the clock, the painted ones, the driver number)
BUILT_IN_SAVERS = {"logo", "clock", "lights-out", "rev-sweep", "pit-board", "chequered", "driver-number"}
# custom alerts' notes as shared (by the alert's name); the rest go as written
SHARED_NOTES = {
    "Flash": "Blinks the flasher button while the car flashes its lights (iRacing's dcHeadlightFlash, held 2.5 s)",
    "Mic Pulse": "Pulses the voice button while someone is talking on iRacing's radio",
}

# SettingsTransfer.ThisPcOnly, plus Usb.TurnedOffSimHubDevice (top level and per wheel)
THIS_PC_ONLY = [
    "Originals", "ScreensOriginals", "Base.Originals",
    "Usb.FirmwareConfirmed", "Usb.ScreenFlashes", "Usb.ScreenCheck", "Usb.ScreenCheckWhen", "Usb.ScreenFirmwareAck",
    "Usb.ScreenRamDrive", "Usb.ScreenRam",
    "SimProUrl", "Updates.Repo", "Usb.LibraryUrl", "Usb.DesignerServer", "Usb.DesignerPort",
    "UnleashedAccepted", "Usb.LibraryTermsAccepted", "Usb.LibraryInstalled", "Usb.LastSession",
    "Updates.LastCheckUtc", "Updates.SkippedVersion",
    "Usb.TurnedOffSimHubDevice",
]


def our_dashes():
    return {p.stem: p for p in (ROOT / "dashes").rglob("*.json")}


def strip(s):
    for path in THIS_PC_ONLY:
        *parents, last = path.split(".")
        o = s
        for p in parents:
            o = o.get(p) if isinstance(o, dict) else None
        if isinstance(o, dict):
            o.pop(last, None)
    for w in (s.get("Usb", {}).get("Wheels") or {}).values():
        if isinstance(w, dict):
            w.pop("TurnedOffSimHubDevice", None)


def dash_ref(ref, ours):
    """'c:<id>' kept (renamed if needed) when the dash is in this repo, else None."""
    if not isinstance(ref, str) or not ref.startswith("c:"):
        return None
    dash_id = RENAMED_DASHES.get(ref[2:], ref[2:])
    return "c:" + dash_id if dash_id in ours else None


def from_simhub():
    s = json.loads(SIMHUB_SETTINGS.read_text(encoding="utf-8-sig"))
    strip(s)
    usb = s.get("Usb", {})
    ours = our_dashes()

    for p in usb.get("UserLights") or []:
        if p.get("Id") == usb.get("LightPreset"):
            p["Name"] = PRESET_NAME
        for a in p.get("Alerts") or []:
            if a.get("Note") and a.get("Name") in SHARED_NOTES:
                a["Note"] = SHARED_NOTES[a["Name"]]

    usb["DefaultDashes"] = [r for r in (dash_ref(r, ours) for r in usb.get("DefaultDashes") or []) if r] or ["c:gt-default"]
    usb["DefaultCurrent"] = 0
    kept = {}
    for car, d in (usb.get("CarDashes") or {}).items():
        refs = [r for r in (dash_ref(r, ours) for r in d.get("Dashes") or []) if r]
        if refs:
            d["Dashes"], d["Current"], d["DashId"] = refs, 0, None
            kept[car] = d
    usb["CarDashes"] = kept

    # screensavers: only the built-in ones; the driver number's card as new
    usb["Savers"] = []
    if usb.get("SaverId") not in BUILT_IN_SAVERS:
        usb["SaverId"] = "logo"
    usb["SaverRotation"] = [i for i in usb.get("SaverRotation") or [] if i in BUILT_IN_SAVERS and i != usb["SaverId"]]
    usb.pop("Driver", None)

    export = {"Format": "fx-unleashed-settings", "FormatVersion": 1, "SettingsVersion": s.get("SettingsVersion", 0),
              "Plugin": PLUGIN, "ExportedUtc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "Settings": s}
    OUT.mkdir(exist_ok=True)
    out = OUT / f"{NAME}.fxsettings.json"
    out.write_text(json.dumps(export, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{out.relative_to(ROOT)}: preset '{PRESET_NAME}', {len(kept)} cars with their own dash")


def build_zip():
    src = OUT / f"{NAME}.fxsettings.json"
    export = json.loads(src.read_text(encoding="utf-8"))
    usb = export["Settings"].get("Usb", {})
    used = {r[2:] for r in usb.get("DefaultDashes", [])}
    used |= {r[2:] for d in usb.get("CarDashes", {}).values() for r in d.get("Dashes", [])}
    ours = our_dashes()
    out = ROOT / "out" / "release" / f"{NAME}.fxsettings.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("settings.fxsettings.json", src.read_bytes())
        for dash_id in sorted(used):
            z.write(ours[dash_id], f"Dashes/{dash_id}.json")
    print(f"{out.relative_to(ROOT)}: settings + {len(used)} dashes ({', '.join(sorted(used))})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-simhub", action="store_true", help="refresh the settings file from this PC's SimHub first")
    a = ap.parse_args()
    if a.from_simhub:
        from_simhub()
    build_zip()
    return 0


if __name__ == "__main__":
    sys.exit(main())
