# Plan

The detailed state is in `docs/CONTEXT.md`. Here only the fronts and what is left.

## Fronts
1. **iRacing GT3 dashes**: eleven cars with a dash (six converted from LMU, five from scratch). Left: driving the ones not
   driven yet.
2. **Default dash**: `gt-default` (based on the Lovely Dashboard), done and in use.
3. **Shift lights**: `docs/rev-lights-plan.md`. Covered by the plugin since 0.7.6 for iRacing (the sim's own data).
4. **The plugin itself**: now **FX Unleashed Enhanced**, a separate repository (see `docs/PLUGIN-FORK.md`).

## Steps
- [x] Diagnose the AMG (LMU) dash's gear bug in iRacing
- [x] Convert the Mercedes, 296, 911 and Mustang; driven
- [x] Convert the Aston Martin and the McLaren; McLaren brought to its iRacing display
- [x] M4, Audi, Lamborghini and Corvette from scratch
- [x] A default dash after the Lovely Dashboard's layout
- [x] Dashes per car and the default dash set in the plugin
- [x] Audit the ten GT3s' shift lights; measure the M4 and the McLaren in the sim
- [x] Plugin changes: settings backup, a clearer lights editor, play on the wheel, alerts on one button (FX Unleashed Enhanced)
- [ ] Drive the Corvette and the Lamborghini in detail
- [ ] Confirm whether the Ferrari 296's shift flash blinks
- [ ] GT Pro Hub: waiting for a way to talk to it (see `docs/PLUGIN-FORK.md`)
