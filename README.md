# FX Unleashed dashes

My dashes for the **Simagic FX Pro**'s screen, for the [FX Unleashed](https://github.com/fxunleashed/fx-unleashed)
SimHub plugin (or [FX Unleashed Enhanced](https://github.com/skuldgerry/fx-unleashed-enhanced)) in Unleashed mode, and my
plugin profile.

- **iRacing GT3 replicas**: what each car shows on its own display, one dash per car.
- **A default dash** for every other car and game, laid out after the Lovely Dashboard's main screen.
- **My profile**: my plugin setup (lights, alerts, a dash per car) as one file to import.

> An independent project, not affiliated with Simagic, FX Unleashed, Lovely Sim Racing or iRacing. Simagic, FX Pro,
> iRacing and the car makers' names are trademarks of their owners, used only to say what the dashes are for.

## The dashes

| | |
|---|---|
| ![BMW M4 GT3](docs/images/bmw-m4-gt3-iracing.png) | ![Chevrolet Corvette Z06 GT3.R](docs/images/corvette-z06-gt3r-iracing.png) |
| **BMW M4 GT3** | **Chevrolet Corvette Z06 GT3.R** |
| ![Lamborghini Huracán GT3 EVO](docs/images/lamborghini-huracan-gt3-iracing.png) | ![Audi R8 LMS GT3 EVO II](docs/images/audi-r8-lms-gt3-iracing.png) |
| **Lamborghini Huracán GT3 EVO** | **Audi R8 LMS GT3 EVO II** |
| ![Default dash](docs/images/gt-default.png) | |
| **Default dash**: any game and car | |

What they add to the cars' own displays:

- **Setting changes**: changing TC, ABS, brake bias (and the throttle map where the car has one) shows the new value large
  for 2 seconds.
- **Start-up**: the car's name while the ignition is off and for 2 seconds after it comes on.
- **Pit limiter**: a clear band with the speed.

## Install

Everything is in the **[Releases](https://github.com/skuldgerry/fx-unleashed-dashes/releases)**.

- **Dashes**: download one `.fxdash.json`, or the pack with all of them. In the plugin's **Dashes** tab press
  **Import a file…** and pick them, or drop them onto the tab (FX Unleashed Enhanced 0.7.61 takes the pack as it is;
  otherwise unzip it first). Then pick a dash for a car there.
- **My profile**: download `skuldgerry.fxsettings.zip` and import it with **About > Backup > Import settings…** (FX
  Unleashed Enhanced 0.7.61 or later); it is applied the next time SimHub starts. It brings the light preset `skuldgerry`
  (based on Neon Tokyo) with its alerts, buttons and encoders in colours of their own, the headlight flash and voice
  button alerts, and all the dashes above, each iRacing GT3 on its own dash. It **replaces your current settings**: export
  yours from the same card first if you want to go back.

## Credits

- [FX Unleashed](https://github.com/fxunleashed/fx-unleashed) by ziadkadry99 (GPL-3.0): the plugin and the dash format;
  `docs/reference/` and `templates/example-gt.json` are copied from it.
- The default dash's layout follows the [Lovely Dashboard](https://github.com/Lovely-Sim-Racing) by Lovely Sim Racing;
  no part of it is used.

## License

[MIT](LICENSE). The copies from FX Unleashed (`docs/reference/`, `templates/example-gt.json`) stay under its GPL-3.0.

By [skuldgerry](https://github.com/skuldgerry).
