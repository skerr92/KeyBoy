# KeyBoy
Home of all things KeyBoy - Games, board files, parts lists, and more!

### NOTICE ###
Licensed under MIT License, see LICENSE for details

### About ###
This repository holds all things for the KeyBoy. 

Currently we just have the EAGLE schematic and board files available, thoguh KiCAD files will be coming soon.

Additionally, the BOM and manufacturing files will be coming once with final design is validated.

Once you have hardware in hand, you will need to put the CircuitPython ESP32-S3 Mini Dev Kit image onto the ESP32-S3 onboard.

From there, copy over the required libraries listed in the code.py under the Firmware directory.

Copy `Firmware/Games/GameMenu.py` to `/lib` as well for the arcade
SEL pause menus. SEL opens Resume / Save / Leave; arcade games save high
scores and Lantern Acre saves its farm to `/lantern_acre.sav`.

The animated arcade launcher has a bevelled pixel logo, twinkling stars,
individual game emblems, and three pages of games. Up/Down selects; Left/Right
changes pages; A launches. Copy `Firmware/Games/KeyBoyLauncher.py` to
`/lib/KeyBoyLauncher.py` when updating `Firmware/code.py`.
The launcher releases its artwork and module before loading a game, then
rebuilds on return with the previous selection. Games are also unloaded on exit.
See [launcher previews and memory fixes](docs/launcher/README.md).

KeyBoy audio uses I2S enable `IO8` and BCLK/LRCLK/DATA pins `IO5`/`IO6`/`IO7`.
The dedicated SEL button is on `IO40`.
Copy `Firmware/Games/KeyBoyAudio.py` to `/lib` and the entire
`Firmware/Games/KeyBoySounds` folder to `/lib/KeyBoySounds`. The audio engine
streams distinct effects and musical cues through three independent voices,
with smooth envelopes and a continuous I2S stream to reduce clicks. See
[audio installation, sound tour, and validation](docs/audio/README.md).

Copy the code.py file to your CIRCUITPY drive and it should work.

The launcher now includes **Loose Cows**, **Sprite's Journey**, **Aerial Dog
Fight**, **Dungeons CYL**, **Lantern Acre**, **Wildspark**, **Ironbound**, and
**Last Beacon**, **Clockwork Courier**, and **Drift Circuit**.

The three arcade games now share `Firmware/Games/KeyBoyArcade.py`; copy it to
`/lib/KeyBoyArcade.py` alongside `GameMenu.py`. They use reusable 4-bit pixel
scenery and retained actors, with cached pause panels.

**Sprite's Journey** has nine collectible rooms, larger characters, guardian
projectiles, ranged magic, three hearts per room, and wings that enable gliding
from room four. Find every spark and defeat the guardian to open each gate.
A jumps (hold to glide), B fires magic, Left/Right moves. Copy its package to
`/lib/Sprites_Journey/`, including `Sprites_Journey.py` and `__init__.py`.

**Aerial Dog Fight** has larger aircraft over a coastal battlefield, twin/rapid
cannons, limited rechargeable boost, repair/loadout choices between sectors,
and a persistent ace with spread attacks. D-pad flies, A fires, B boosts.
Copy `Firmware/Games/Aerial Dog Fight/AerialDogFight.py` to `/lib/AerialDogFight.py`.

**Loose Cows** has illustrated ranch scenery, gold bonus cows, safer whistles,
lasso release, generous early deadlines, and ranch upgrades every three rounds.
A catches/releases, B whistles. Copy its package to `/lib/Loose_Cows/`.
All three support SEL pause and Up + Down to exit; existing best scores stay
compatible. See [arcade previews, controls, and verification](docs/arcade/README.md).

Dungeons CYL is a seven-floor pixel-art escape crawler with themed stonework,
larger animated characters, distinct guardians, torches, supply chests, and
telegraphed enemy attacks. D-pad walks, A swings the sword, hold B to guard,
and SEL pauses or retries the current floor. Defeat the guardian to open each
gate; cross spikes during their safe window. Six hearts, healing supplies,
and full-health floor retries keep the campaign recoverable.

The blocked guardian routes on floors 2 and 5 are repaired, and every floor
has automated start-to-guardian-to-exit completion coverage. Scenery and sprite
atlases stay allocated throughout play; opening a gate changes only its sprite.
Copy `Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py` to
`/lib/Dungeons_CYL.py`. Existing `/dungeons.txt` best scores remain compatible.
See [dungeon previews, controls, and validation](docs/dungeons/README.md).

Lantern Acre is a pixel-art homestead with an animated farmer, a furnished
cottage, six plots across the home farm and Lantern Meadow, four crop types,
and Lantern Market.
D-pad walks, A plants/waters/harvests the highlighted tile, B opens the market,
and SEL pauses. Approach the cottage door and press A to sleep, ship crops,
or check the farm journal. The chest beside the porch also ships your basket;
herbs beside the well provide $2 once per day if you run short of seed money.

A day lasts **four minutes of active farm time**; menus pause the clock.
Watered crops grow at dawn, and sleeping restores the **Season, Day X** morning
card before returning outside. Cross the east footbridge with A to reach the
meadow's three additional plots; buy plot unlocks at the market. The seed shop
offers named packets that grow year-round, seasonal discounts, and a planting
seed selector alongside the original mixed seeds.
Dry crops wait safely, ripe crops keep, and seasons change every eight days.
Crop prices differ; the copper can waters three adjacent crops and the cart
adds $1 per shipped crop. Sleep autosaves; SEL offers explicit save/leave
options and reports write failures (USB programming mode makes saves read-only).
Existing farm saves migrate automatically on the next successful save.

The terrain, sprite atlases, and crop TileGrids stay allocated during play.
Walking changes sprite positions; tending updates only affected tile indices;
menus reuse preallocated panels and labels over the retained farm, avoiding
large allocations when opening the store or pause menu. Dusk/night/dawn recolor the world palette
once per phase, without rebuilding the scene. No image files are needed.
Copy `Firmware/Games/Lantern_Acre/Lantern_Acre.py` to
`/lib/Lantern_Acre/Lantern_Acre.py` in the existing package to deploy it.
See [art previews and validation](docs/lantern-acre/README.md).

Wildspark is a pixel-art creature adventure with six detailed routes, an
animated trainer and traveling companion, and 27 large illustrated creature
forms. Recover relics, earn three sanctuary emblems, and challenge the rival.
Captured families become usable partners with individual HP, XP, and evolution.
Turn-based battles offer Strike, elemental Burst, Guard, Catch, Tonic, Switch,
Weaken, and Flee. Weaken leaves at least 1 HP; Catch succeeds at half HP or less.
All 27 forms can be found on later trails, and the guide provides habitat hints;
enemy intent makes charged attacks readable. Clinics heal the party and refill
supplies. D-pad moves, A interacts/confirms, B opens partners or retreats, and
SEL opens the pause/save/field-guide menu.

World and battle scenes retain their sprites between transitions, with small
bitmap strips and reusable menu panels. Legacy saves migrate to the expanded
party format at `/wildspark.sav`. Copy `Firmware/Games/Wildspark/Wildspark.py`
to `/lib/Wildspark/Wildspark.py` in the existing package. See
[Wildspark art, controls, and validation](docs/wildspark/README.md).

Ironbound is an eight-operation mech tactics campaign with an illustrated refit
bay, animated mechs, cannon/rail loadouts, visible enemy attack plans, and
permanent upgrade choices. Move off marked tiles, counterattack during enemy
recovery, use cover, and manage shield energy, repair kits, and EMP pulses.
Clear hostiles, activate relays or recover cargo, then extract. D-pad moves,
A targets/interacts, B guards, and SEL opens systems and checkpoint saves.

Every mission has legal-action completion coverage with both weapons and each
upgrade path. Scenes and menus retain their small bitmap strips and sprites.
Old `/ironbound.sav` saves migrate to the expanded checkpoint format. Copy
`Firmware/Games/Ironbound/Ironbound.py` to `/lib/Ironbound/Ironbound.py`. See
[Ironbound previews, controls, and validation](docs/ironbound/README.md).

Last Beacon is a sprite-based extraction shooter that starts aboard the
**L.B.S. Wayfarer**. Choose one of eight contracts and one of five weapons, including the new
autocannon and wide-spread breacher,
plus orbital/sentry/resupply/shield/stasis support before deploying. Complete salvage, hive
purge, or uplink objectives, reach the extraction pad to call your shuttle,
then board before its 12-second departure window closes. Each contract also
has a 100–150 second overall deadline; menus pause mission time.

Use D-pad to move and aim, hold A to fire and strafe, B to deploy support, and
SEL to pause. Empty magazines reload automatically; exhausted ammunition
switches to an emergency sidearm. Supply crates restore health/ammunition.
Successful extractions earn credits for armor and weapon refits aboard ship.

Last Beacon retains its terrain, enemies, projectiles and effects throughout
each mission. Only scene transitions replace the background. Copy
`Firmware/Games/Last_Beacon/Last_Beacon.py` to
`/lib/Last_Beacon/Last_Beacon.py` in the existing package. Career saves at
`/last_beacon.sav` migrate from the old campaign format; debrief attempts an
autosave, and ship services provide manual saving with failure feedback.
See [screenshots, controls and validation](docs/last-beacon/README.md).

**Clockwork Courier** adds twelve brass-and-steam delivery puzzles. Push every
power cell onto a dock, unlock the next workshop, and replay for efficiency
medals. D-pad walks/pushes, B undoes, and A or SEL opens the workshop with
restart/save/room selection. Every room is solvable; there is no timer or life
limit. See [Courier art, controls, and verification](docs/clockwork-courier/README.md).

**Drift Circuit** adds three themed racing circuits, three cars with different
handling, rechargeable boost, time records, and a three-race championship.
A accelerates, Left/Right steer, B brakes, Up boosts, Down recovers, and SEL
pauses. Ordered checkpoints prevent false laps; recovery keeps a stranded
car playable. See [racing art, controls, and verification](docs/drift-circuit/README.md).

Both additions use retained scenery, small sprite banks, and cached menu
panels. Copy `ClockworkCourier.py`, `DriftCircuit.py`, and `KeyBoyScenes.py`
from `Firmware/Games/` into `/lib/`, along with the updated launcher and
`code.py`. Their separate saves are `/clockwork.sav` and `/drift_circuit.sav`.
Up + Down exits either game. Existing games and saves remain compatible.

This uses a 1.3" ST7789 display which can be purchased from Adafruit.

### 3D Printed Case ###
Once I receive the next iteration of the board, I will be uploading a usable case here that can be printed on either resin or FDM 3D printers.
A CircuitPython board definition will be coming soon.
