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

Copy `Firmware/Games/GameMenu.py` to `/lib` as well: every game uses it for
the SEL pause menu. SEL opens Resume / Save / Leave; arcade games save high
scores and Lantern Acre saves its farm to `/lantern_acre.sav`.

The launcher loads one game module only when selected, then clears display
objects, removes that module from memory, and runs garbage collection on exit.

KeyBoy audio uses I2S enable `IO8` and BCLK/LRCLK/DATA pins `IO5`/`IO6`/`IO7`.
The dedicated SEL button is on `IO40`.
Copy `Firmware/Games/KeyBoyAudio.py` to `/lib`; the launcher synthesizes short,
non-blocking tones for game actions without requiring WAV assets.

Copy the code.py file to your CIRCUITPY drive and it should work.

The launcher now includes **Loose Cows**, **Sprite's Journey**, **Aerial Dog
Fight**, **Dungeons CYL**, **Lantern Acre**, **Wildspark**, **Ironbound**, and
**Last Beacon**. Sprite's
Journey is a nine-room platformer: use Left/Right to move, A to jump, and B to
cast a close-range magic burst at the two mini-bosses and final boss. Holding
Up + Down exits to the launcher.

To deploy Sprite's Journey, copy `Firmware/Games/Sprites_Journey/Sprites_Journey.py`
to the CIRCUITPY drive's `/lib` directory along with the other game modules,
then copy `Firmware/code.py` to its root.

Aerial Dog Fight needs no image assets: its aircraft, bullets, and starfield
are compact `displayio` pixel art. Copy
`Firmware/Games/Aerial Dog Fight/AerialDogFight.py` to `/lib` to deploy it.

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
cottage, three unlockable plots, four seasonal crops, and Lantern Market.
D-pad walks, A plants/waters/harvests the highlighted tile, B opens the market,
and SEL pauses. Approach the cottage door and press A to sleep, ship crops,
or check the farm journal. The chest beside the porch also ships your basket;
herbs beside the well provide $2 once per day if you run short of seed money.

A day lasts **eight minutes of active farm time**; menus pause the clock.
Watered crops grow at dawn, and sleeping advances directly to the next day.
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
Turn-based battles offer Strike, elemental Burst, Guard, Bond, Tonic, and Switch;
enemy intent makes charged attacks readable. Clinics heal the party and refill
supplies. D-pad moves, A interacts/confirms, B opens partners or retreats, and
SEL opens the pause/save/field-guide menu.

World and battle scenes retain their sprites between transitions, with small
bitmap strips and reusable menu panels. Legacy saves migrate to the expanded
party format at `/wildspark.sav`. Copy `Firmware/Games/Wildspark/Wildspark.py`
to `/lib/Wildspark/Wildspark.py` in the existing package. See
[Wildspark art, controls, and validation](docs/wildspark/README.md).

Ironbound is an eight-mission turn-based tactics campaign with procedurally
assembled sector terrain, persistent mech upgrades, and an eighth-mission
commander. Copy `Firmware/Games/Ironbound/Ironbound.py` to `/lib`; saves use
`/ironbound.sav`.

Last Beacon is a sprite-based extraction shooter that starts aboard the
**L.B.S. Wayfarer**. Choose one of five contracts, a carbine/scattergun/lancer,
and orbital/sentry/resupply support before deploying. Complete salvage, hive
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

This uses a 1.3" ST7789 display which can be purchased from Adafruit.

### 3D Printed Case ###
Once I receive the next iteration of the board, I will be uploading a usable case here that can be printed on either resin or FDM 3D printers.
A CircuitPython board definition will be coming soon.
