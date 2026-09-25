# Wildspark

![Mothwood exploration](mothwood.png)

![Turn-based battle](battle.png)

A six-route creature adventure with a traveling companion, nine creature
families, 27 illustrated forms, three sanctuary emblems, and a rival finale.
These previews render the actual game bitmaps at 3× nearest-neighbor scale;
desktop text approximates the board's `terminalio` font.

## Playing

- D-pad: walk; navigate battle commands and menus.
- A: interact with a clinic, shrine, sanctuary or trail; search tall grass;
  confirm a battle action. Actions pressed during a step wait until arrival.
- B: choose your traveling partner; retreat from a battle; close a menu.
- SEL: pause, open the field guide, save, or leave. Battle pause offers controls
  and retreat. Up + Down exits without saving.

Choose Cindle (Ember), Bublet (Tide), or Buddy (Grove) when starting a new save.
Recover each route's glowing southern relic before taking the eastern trail.
Win sanctuary challenges on routes 2, 4, and 6 to earn emblems. All three
emblems unlock the rival at the sanctuary. The clinic restores every partner
and refills three tonics. Exploration continues after becoming champion.

Tall grass encounters follow six grass steps, with a grace period after
battle; A can deliberately search. Blocked movement does not count as a step.
Each captured family becomes a usable partner with its own level, HP, and XP.
Bonds with an already-owned family preserve that partner's progress.

## Battles

| Action | Effect |
| --- | --- |
| Strike | Reliable neutral damage; gain one focus, up to three. |
| Burst | Spend two focus on stronger elemental damage. |
| Guard | Gain one focus and reduce the next attack to one third. |
| Bond | Recruit a wild creature at half health or less; bosses resist bonding. |
| Tonic | Restore up to 18 HP, consuming one of three clinic-refilled tonics. |
| Switch | Select another healthy companion. |

Ember beats Grove, Grove beats Tide, and Tide beats Ember. Strong matchups
apply 1.5× damage; resisted attacks apply 0.75×. Enemies alternate a strike,
a charging turn, and a stronger burst. The intent above the enemy tells you
when to guard. Invalid actions consume neither resources nor turns. Switching
normally uses a turn, but replacing a fainted partner is free. If everyone
faints, the party recovers at full health. Retreating remains available.

Victories and successful bonds grant XP to the active partner. Forms evolve
at levels 4 and 8; the level cap is 30. The field guide tracks discovered forms.

![Final forms](forms-3.png)

Additional previews: [first forms](forms-1.png), [middle forms](forms-2.png),
[coastal trail](coast.png), [Moonglade](moonglade.png), and
[partner selection](partners.png).

## Rendering and saves

The 18×24 trainer has twelve directional walking frames; companions follow
behind. Battle creatures have two 48×48 breathing frames. Static scenery uses
small 4-bit bitmap strips. Walking moves existing sprites; battle idle updates
only frame indices. Route/battle transitions build new scenery, while menu
backings and labels are reused. Only the currently selected menu portrait is
replaced. The display driver controls dirty-region merging and SPI transfers;
these changes do not imply a measured frame rate or transfer count.

`WS2` saves store the party, active companion, XP, discovered forms, relics,
emblems, supplies, and finale completion. Existing seven-field saves migrate
in memory, preserving their active creature and campaign progress. Original
saves did not record captured species, so those cannot be reconstructed.
Saves write `/wildspark.tmp` before renaming to `/wildspark.sav`. USB read-only
or full-disk failures are reported. Save from SEL; emblem/finale wins also
attempt a save. Leaving does not silently save.

Copy `Firmware/Games/Wildspark/Wildspark.py` into the existing package at
`/lib/Wildspark/Wildspark.py`. No artwork files or extra libraries are needed.

## Verification

```sh
python3 tests/test_wildspark.py
python3 tools/preview_wildspark.py
```

Twenty-three host tests cover save migration and rejection, party persistence,
combat costs and turn order, fainting/switching, evolution, reachable landmarks,
all route gates and the finale, buffered walking input, retained scenery,
menu input edges, and 27 distinct forms. Lantern Acre's 17 and Last Beacon's
25 regression tests also pass. Syntax and whitespace checks pass.

### Connected ESP32-S3 (2026-09-25)

With CircuitPython 9.0.0-beta.2 and the actual launcher/display/audio allocations
resident, 18 repeated world → portrait menu → battle → pause menu transitions
passed. The run exercised all six route palettes, every family and evolution
portrait, combat updates, and read-only save failure. The first world build
took 2.29 seconds, with 94,112 bytes free after collection. Battle memory
stabilized around 77,792–78,176 bytes; the final world had 87,824 bytes free.

The installed source matches the repository, the existing save is byte-for-byte
unchanged, and the launcher restarted successfully. This is automated hardware
smoke/stress coverage, not a frame-rate benchmark or a hands-on balance test.
Successful writable-mode hardware saves remain untested while USB owns the
filesystem; serialization and migration are covered by host tests.
