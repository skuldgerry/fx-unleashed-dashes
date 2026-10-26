# Changes to the FX Unleashed plugin

Written on 2026-10-12 as the work list for changing the plugin itself; kept as the record of what was asked and why. The
work now lives in its own repository, **FX Unleashed Enhanced** (a fork of
[fxunleashed/fx-unleashed](https://github.com/fxunleashed/fx-unleashed), GPL-3.0), whose `CHANGES-ENHANCED.md` lists what
is in it. This repository holds only dashes and tools.

## Context

- **Plugin**: FX Unleashed, a SimHub plugin in C# (net48) with a WPF interface built in code. Started from 0.7.3, now
  following 0.7.6.
- **Names that never change**: the DLL `User.FXProRpmSync.dll` and the class `FXProRpmSyncPlugin` (SimHub keys plugin
  activation and bindings on them). The name shown is free: "FX Unleashed Enhanced".
- **The plugin's own rules** (its `CLAUDE.md`): settings only move forward (`SettingsVersion` + `SettingsMigration.cs`),
  the interface is visual, nothing may throw out of `Init`, never any Simagic binary or firmware.
- **Building**: `dotnet build -c Release -p:DeployToSimHub=false` with SimHub installed; offline checks with
  `tools/UsbTest`.

## What was asked, and where it stands

| # | Request | State |
|---|---|---|
| 5 | Settings backup and import, to keep a copy or move to another PC | done: About > Backup |
| 3 | Make clear that "Your lights" is the look while driving, and where the rest is | done: subtitle and links to every part |
| 4 | Surface hidden behaviours: encoder setting levels, "Hold still", "Side lights dark", rev bar extras, the per-car nudge actions | done: levels as a switch of their own, notes on the effect, play buttons with info, bindings in the rev editor |
| 2 | Try a light mode on the wheel without driving | done: play / stop on every part of the editor, "Show on the wheel"; upstream 0.7.4 added a play-once preview, both kept |
| 1 | The headlight-flash button lights when the sim really flashes | done: alerts on single buttons (picked on a drawing of the wheel) and a hold time after the condition; the FX Pro's usual button map built in |
| 6 | Shift-light stages the light data can't express (McLaren 720S, Corvette Z06, the M4's white dots) | done: the M4 and 720S use their measured lights before 0.7.6's game data (which keeps only each light's first colour); stages past the shift point for any car in Car tuning |

## Done in 0.7.61

| Request | Where it is |
|---|---|
| Import a zip of dashes | the Dashes tab's Import a file and dropping onto the tab take a zip; each dash in it is checked like a file (`Usb/DashShare.cs` Unzip) |
| A colour of their own for buttons and encoders while driving | Your lights › Buttons / Encoders › Own colours: picked on the wheel drawing per part; the group's effect in that colour (the encoders' levels dim low, full high) or an effect of their own; the blink after a setting change kept (`OwnColor`, `LightEngine.ApplyOwnColors`) |
| A driver number screensaver like the Lovely Dashboard's idle screen | built in (Idle & sleep): number and name each switched on and in its colour; a line under it with a running light or a breath; the Enhanced logo with neither (`DriverNumberSaver`, `DriverCard`) |
| Alerts with no colour, notes, long conditions | an alert's palette offers No colour (the lights keep theirs and blink); a note per custom alert; the condition in a bigger box |
| Any colour | colour fields have a picker (saturation and brightness, hue) next to the ready colours |

Seen on the wheel in testing: the driver number's line first ran along the screen's top row (its position was only
worked out while painting, and art from the cache isn't painted again); fixed before the release.

## Later

- **Each car's real wheel colours (needs a small database; the most work).** For each car, the colours of the real car's
  wheel by zone of the wheel (top buttons, the sides, the encoders, the bottom...), taken from pictures and manuals of
  the real wheel, put on the same zones of the FX Pro: a visual thing only, steady by default or a gentle effect that
  keeps the colours (pulse), for the feeling of sitting in the real car. Not a 1:1 copy (the wheels' buttons differ),
  and the own colours still apply on top. Builds on the per-car presets (`UsbSettings.CarLights`); the data would be a
  JSON per car (zone → colour), with car ids taken from the plugin's log as for the dashes, never invented.
  Not by what each button does: the plugin can't know which FX Pro button is the pit limiter or the radio. That would
  need a menu to say it, or reading SimHub's Control Mapper, which could be odd where it is driven by an Arduino.
- **iRacing's radio:** `RadioTransmitCarIdx` (who is talking, -1 for nobody) is what the voice button alert reads; still
  to measure in a session how quickly it follows the talking and whether it counts every frequency listened to.
Measured in iRacing on 2026-10-12: `dcHeadlightFlash` is true for only about 70 ms per press and doesn't follow the light
sequence, so an alert that follows the value is a single frame. The hold time is what makes it usable.

The rule asked for the high-beam icon on dashes (any game): the icon shows the high beams' state and, while the flash
lasts, blinks the *opposite* way (beams off: blinks on; beams on: blinks off); the button press only starts the blink.
iRacing has no telemetry for the headlight state, so there the icon always starts dark.

## Study: the Simagic GT Pro Hub

**Question**: can the same be done for other Simagic devices, starting with the GT Pro Hub (8 RGB buttons, two RGB rotary
encoders, a 9-light rev bar, no screen; wireless to the base, USB-C for updates)?

**Checked on a hub (2026-10-13), read-only**:
- SimPro lists it as `GTC`, type wheel, `product_uuid` `0000000002040000`, app V1.3.1. Its preset has `rpm_lights` with
  9 lights (same format as the FX Pro's), `led_buttons` (8), `encoders` (2) and `leds` (2), each with SimPro's
  telemetry effects (ABS active, TC active, pit limiter); no screen.
- On the base its USB-C enumerates nothing (cable known good): it only talks by radio, and its buttons arrive through
  the base's controller (VID 0483, PID 0522).
- Off the base, on USB alone, it shows up as "GTC Wheel" with the FX Pro's own VID/PID (0483/0529) and the same serial;
  the plugin reads its app version over the FX Pro's protocol and refuses it (USB mode needs 1.3.11). Same family of
  devices.
- FX Unleashed's custom firmware is the FX Pro's alone (its app 1.3.11 changed; the GT Neo and the FX need none). What the
  FX Pro got in its build 6 (USB working with the wheel on the base) plus the lights would be needed for the hub, and that
  takes the firmware key, which only FX Unleashed's authors have.

**Possible without firmware**: the plugin's standard mode through SimPro's local API. A user reported (Discord,
2026-10-13) that it almost works already: the plugin takes the hub for an FX Pro and sends 15 lights, the hub uses the
first 9. The fix in the plugin would be to recognise `0000000002040000` and lay the pattern over 9 lights. Not done: on
hold until there is news from the community. To check before using SimPro for the button colours: whether each push is
saved to the device's flash (the dash part is).
