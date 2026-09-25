# Lantern Acre

![Farm pixel-art preview](farm.png)

![Cottage pixel-art preview](cottage.png)

![Night lighting preview](night.png)

These 3× nearest-neighbor previews render the game's actual bitmap and sprite
code. Desktop text approximates `terminalio`; hardware uses CircuitPython's
font. The farm preview stages all crops and unlocks all plots to show the art.
A new farm starts with one plot, six seeds, and $18. Previews are development
artifacts and do not need to be copied onto KeyBoy.

## Controls and pacing

- D-pad: walk. The corner marks show the tile affected by A.
- A: plant, water, or harvest. At the front door, enter the cottage.
- B: open the market from anywhere; close a menu.
- SEL: pause, save, or leave. Up + Down exits without saving.
- Cottage: sleep until morning, ship crops, or view the farm journal.
- Porch chest: ship crops. Herbs by the well: collect $2 once per day.

Each day is eight active minutes, starting at 06:00. Dusk begins at 17:00;
night begins at 75% of the day. Time stops inside menus. Sleeping skips to
morning and attempts a save. If unwatered crops remain, sleep asks for a
second A press. Watered crops gain one growth stage each morning; dry crops
wait rather than die. Existing plants retain their crop type across seasons.

| Crop | Watered nights | Sale price |
| --- | --- | --- |
| Turnip | 2 | $5 |
| Bean | 3 | $8 |
| Pumpkin | 4 | $13 |
| Root | 3 | $10 |

Mixed seeds become the current season's crop. Three seeds cost $6. The copper
can waters the current tile and its left/right neighbors. The cart adds $1
per harvested item, including older saved inventory.

## Rendering and verification

Ten 240×20 4-bit terrain strips, a shared crop atlas, a 12-frame 18×24 farmer
atlas, and persistent HUD labels form the farm. The terrain is generated once.
Crops change atlas indices, movement changes TileGrid positions, and small
creek/smoke sprites update at 3 Hz. Menus push/pop their own overlay without
removing the farm. Interior strips and reusable panel backings/labels are
prepared at farm startup. Opening the market, pause menu, or cottage never
allocates a new bitmap. Shared panel atlas strips are 2,128 bytes each; the
largest terrain strip is 2,400 bytes. Terrain and interior use tailored
16-color palettes; panel backings use 2 bits/pixel and the HUD uses 1 bit/pixel.
Crops and the farmer retain their separate 32-color palette.

World palette changes at dusk, night and dawn invalidate world colors once;
normal play never clears the screen or repaints the terrain. These lighting
transitions can require a broad display refresh, unlike normal local updates.
The CircuitPython display driver owns dirty-region merging and SPI transfers.

Run from the repository root:

```sh
python3 tests/test_lantern_acre.py
python3 tools/preview_lantern_acre.py
```

Host tests cover growth/pacing, crop-specific sales, upgrades, map reachability,
atlas bounds, old saves, rejected saves, scene/bitmap retention, walking input,
menu input edges, buffered actions and sleep confirmation. Host display doubles cannot measure
SPI bandwidth or frame rate; a hands-on board playtest remains useful.

Save format `LA2` retains day/time, inventory and its sale value, upgrades,
plots, crop state and daily forage use. Legacy 8-field saves are read without
modifying them. New saves write a temporary sibling before renaming over the
save. Failed writes are reported; save-and-leave stays in the menu on failure.

## Connected-device validation (2026-09-25)

Tested the menu-memory fix on the connected ESP32-S3 running CircuitPython
9.0.0-beta.2 with actual launcher/menu/audio allocations resident. The farm and
all reusable panels initialize in about 7.18 seconds. Ninety successive
cottage/market/pause openings passed with changing inventory/HUD text and
small live allocations deliberately fragmenting the heap. Memory stabilized
around 38,464 bytes free during stress; 44,352 bytes remained after releasing
the artificial fragments. These are stress snapshots, not frame-rate metrics.

The updated module is installed, the existing farm save is byte-for-byte
unchanged, and the launcher was restarted. Seventeen host tests pass,
including bitmap-allocation rejection during repeated menu opening and
bounded backing allocations. Syntax and whitespace checks pass. The earlier
smoke also verified day-72 legacy data, dawn/lighting/crop updates, animation,
and read-only save failure. Successful hardware writes remain untested while
USB programming mode owns the filesystem.
