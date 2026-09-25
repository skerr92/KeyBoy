# CondensedContext

## Context Freshness

- Last Verified Commit: `a8f38fb`
- Current HEAD: `a8f38fb`
- Status: partial — game-library work is implemented but uncommitted.
- Files requiring verification: `Firmware/code.py`, `Firmware/Games/Sprites_Journey/Sprites_Journey.py`, `Firmware/Games/Aerial Dog Fight/AerialDogFight.py`, `Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py`, `Firmware/Games/Lantern_Acre/Lantern_Acre.py`, `Firmware/Games/Last_Beacon/Last_Beacon.py`, `Firmware/Games/Wildspark/Wildspark.py` (host/device verified in working tree; not committed).

## Current Focus

- Dungeons Can You Leave upgrade complete: repaired blocked maps and verified all seven floors are achievable, with richer sprites/art and deliberate shield combat.
- Preserve the approved Lantern Acre, Last Beacon, and Wildspark upgrades and existing saves/high scores.

## Handoff

- Dungeons: levels 2/5 had disconnected guardians behind wall (8,9); opened both. Connected pre-gate side passages on levels 4/6/7. All walkable tiles and gameplay landmarks now reachable with exit locked; gates reachable after guardian defeat.
- New 16×22 directional/interpolated hero, seven 24×28 guardian variants, themed stonework, torches, supplies, animated traps, telegraphed enemy attacks, sword cooldowns, hold-B guard, six hearts, +2 healing between floors, same-floor death/pause retries.
- Twelve retained 4-bit terrain strips and small sprite atlases (max bitmap 2,268 bytes); cached menu labels/backings. Gameplay and gate opening never rebuild terrain. Native floor builds ~3.64–3.97 seconds.
- 18 Dungeons host tests pass, including seven-floor completion using real combat/AI/movement/trap rules, every tile's reachability, campaign/finale/retry flow, pause timing, and bitmap retention. 65 Lantern/Wildspark/Last Beacon regressions plus syntax/whitespace pass.
- Actual ESP32-S3 completed all seven floors twice at full health with launcher/audio resident. Free heap 65,744–67,168 bytes, identical per-floor values in the second campaign. Read-only save failure verified. Source installed at `/lib/Dungeons_CYL.py`, source/device hashes match, existing best-score file unchanged, launcher restarted.
- Controls, seven floor previews and hardware details: `docs/dungeons/README.md`. Regenerate with `python3 tools/preview_dungeons.py`; test with `python3 tests/test_dungeons.py`.
- Next useful step: hands-on combat feel feedback. Work remains uncommitted; successful writable-mode hardware saves are untested while USB owns the filesystem.

## Stable Facts

- `Firmware/code.py` owns display/button initialization and the game selector.
- Inputs are active-low `DigitalInOut` values; 240×240 display has `rotation=0`.

## Decisions

- Use code-native pixel art rather than raster assets: it is smaller, deterministic, and needs no image loader or additional files.
- Ship nine single-screen levels, with mini-bosses in levels 3 and 6 and the final boss in level 9.
- Replace Aerial Dog Fight's incomplete GIF-based scaffold with code-generated top-down aircraft and game loop.
- Dungeons CYL has seven repaired, fully connected floors; guardian defeat opens the exit sprite. Cardinal BFS pursuit, fixed-target attack windups, guard/recovery combat, timed spike windows, preserved-at-full-health supplies, six hearts and full-health same-floor retries. Existing integer best-floor file `/dungeons.txt` stays compatible, written via temporary file/rename with failure feedback. Terrain/menu art remains resident through normal play.
- Lantern Acre uses small static 4-bit terrain/interior strips, 32-color crop/farmer atlases, 1-bit HUD and preallocated 2-bit dual-skin menu atlas strips. Reuse one panel/label set for cottage/market/pause; collect before setup. Opening menus allocates no bitmap, avoiding fragmented-heap failures.
- User preference: richer sprite art, larger character, usable house, slower days, and no routine full-screen reconstruction. Movement/tending retain all farm objects; only dusk/night/dawn recolor the world palette (broad refresh at phase transitions).
- Lantern Acre days last 480 active seconds; menus freeze time. Cottage sleep advances growth and attempts save; crop values vary, copper can waters a row of three, cart adds $1/item, daily herbs prevent bankruptcy.
- Lantern Acre LA2 saves preserve basket value and forage state; load legacy 8-field saves transactionally and clamp overage ripe plants. Write temporary save before rename; UI reports failure rather than claiming success.
- Standardize SEL (IO40) pause menus with high-score persistence, and give Lantern Acre full farm-state persistence.
- Wildspark: retained 4-bit scenery strips and two-frame 48px creatures; scene rebuilds only at route/battle transitions. Reuse menu backings/labels; keep one selected portrait. Nine usable party families evolve at levels 4/8; Ember > Grove > Tide > Ember, focus-powered bursts and telegraphed enemy attacks. Six relics gate trails, emblems gate routes 2/4/6, then rival finale. WS2 persists party/XP/guide/relics/supplies; legacy seven-field saves preserve active creature/campaign but cannot recover unrecorded old species.
- Load selected games lazily and evict the game and shared pause-menu modules from `sys.modules` after exit; run `gc.collect()` after clearing display objects.
- Expand Loose Cows into round-based corral herding with lassoing, limited whistles, obstacles, quotas, lives, and combo scoring.
- Add Ironbound, a lightweight procedural turn-based tactics campaign that particularly suits the forthcoming ESP32-S3.
- Last Beacon starts aboard the Wayfarer: choose any of five contracts, carbine/scattergun/lancer, and orbital/sentry/resupply. Complete objectives, call extraction at E, survive 18 seconds, board within 12 seconds; overall deadlines 100–150s and menus freeze all clocks.
- Combat uses cover collision, held-A strafe/aim assist, magazines/auto reload/fallback sidearm, supply caches, invulnerability and limited support. Extraction-only credits fund three armor/power refit levels.
- Last Beacon LB2 stores contract/loadout, credits, cleared mask and refits. Legacy progress/power migrate; extra old support charges convert to $20 each. Debrief autosaves, ship services save manually, read-only failures are explicit; no mid-operation saves.
- Keep Last Beacon ship/terrain in <=2.3 KB static 4-bit strips, shared sprite atlases, 1-bit panels and bounded pools; avoid large contiguous background allocations. Target 33ms frame budget subtracts work time instead of adding a fixed sleep.
- Split the game launcher into two readable pages.
- Integrate lightweight synthesized I2S effects using IO8 enable and IO5/IO6/IO7 audio signals found on the connected CIRCUITPY board.
- Connected test board reports CircuitPython 9.0.0-beta.2 on ESP32-S3-DevKitM-1-N8; launcher uses `display.root_group` for that runtime.

## File Map

- `Firmware/code.py`: launcher/menu.
- `Firmware/Games/Sprites_Journey/Sprites_Journey.py`: game runtime, art, stages, and collision.
- `Firmware/Games/Aerial Dog Fight/AerialDogFight.py`: top-down dogfight, generated planes, waves, and ace battle.
- `Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py`: dungeon art, repaired maps, shield combat/AI, gate progression, retries, best-score compatibility. `tests/dungeons_host.py`, `tests/test_dungeons.py`: display adapter and 18 behavioral/completion tests. `tools/preview_dungeons.py`, `docs/dungeons/`: seven-floor previews and controls/validation.
- `Firmware/Games/Lantern_Acre/Lantern_Acre.py`: self-contained pixel art, retained farm, movement, cottage/market/pause, timed days, crop economy and save migration.
- `tests/lantern_host.py`, `tests/test_lantern_acre.py`: display doubles/PNG renderer and 17 behavioral checks.
- `tools/preview_lantern_acre.py`, `docs/lantern-acre/`: reproducible art previews, controls, rendering limits and board validation.
- `Firmware/Games/GameMenu.py`: shared SEL pause overlay and high-score helper.
- `Firmware/Games/Loose_Cows/Loose_Cows.py`: escalating corral-herding game using existing rancher/cow art.
- `Firmware/Games/Wildspark/Wildspark.py`: Wildspark art, exploration/party, tactical battles, relic/emblem campaign, evolution, WS2 persistence. `tests/test_wildspark.py` / `tests/wildspark_host.py`: 23 behavior checks using shared display doubles. `tools/preview_wildspark.py`, `docs/wildspark/`: actual-art previews and controls/validation.
- `Firmware/Games/Ironbound/Ironbound.py`: seeded eight-mission mech tactics campaign with upgrades and saves.
- `Firmware/Games/Last_Beacon/Last_Beacon.py`: standalone ship/loadout, art, pooled combat, mission/extraction state machine, refits and career persistence.
- `tests/beacon_host.py`, `tests/test_last_beacon.py`: shared display double integration and 25 behavior/retention tests.
- `tools/preview_last_beacon.py`, `docs/last-beacon/`: actual-art previews and player/validation documentation.
- `Firmware/Games/KeyBoyAudio.py`: shared cached I2S tone effects passed into all games by the launcher.

## Validation Memory

- Dungeons upgrade (2026-09-25): 18 host tests; real ESP32-S3 completes all 7 floors twice without damage using guard/trap timing, no HP edits/teleports. Free heap matches per floor across runs (65,744–67,168 bytes), ~3.64–3.97s builds. Read-only save failure, installed source equality, score preservation, and launcher restart verified. Other three games: 65 regressions pass.

- Lantern menu fix (2026-09-25): 17 host tests, actual 90-cycle fragmented-memory menu stress pass; ~38,464 bytes free during stress, 44,352 after releasing fragments. Preallocated panels take ~7.18s at startup. Source installed, save unchanged. Supersedes earlier large-bitmap menu design.
- Wildspark overhaul (2026-09-25): 23 host tests, syntax/whitespace pass; real ESP32-S3 18-cycle world/battle/portrait-menu stress passes, all 27 forms and read-only save failure exercised. World build ~2.29s; battle free memory stable ~78 KB, final world 87,824 bytes. Deployed source matches, save unchanged. Last Beacon 25 regressions pass.

- Last Beacon (2026-09-25): 25 host checks pass; Lantern Acre 15 regression checks pass; syntax and whitespace pass. Connected ESP32-S3 smoke validates all five contracts/extraction, ship/refit/field overlays, actor pool stress, save migration and read-only failure. Small bitmap strips resolved contiguous allocation failures; ~90 KB heap free after collection. Source installed, old save unchanged. Detailed final figures in `docs/last-beacon/README.md`.

- Lantern Acre (2026-09-25): 15 host tests, host syntax and whitespace checks pass; real ESP32-S3/CircuitPython 9.0.0-beta.2 smoke with launcher/audio resident passes, source/deployment bytes match, original save unchanged. Initial 8-bit menu/interior allocations exhausted heap; fixed with low-bit-depth palettes and pre-menu collection. No measured SPI/frame-rate benchmark.

- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/code.py`: passed.
- `git diff --check`: passed.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/Aerial Dog Fight/AerialDogFight.py Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/code.py`: passed.
- Removed obsolete `Enemy Jet.gif`, `Fighter Jet.gif`, and `Fighter Jet.bmp`; the dogfight module no longer uses image assets.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py`: passed; all authored maps are 13×12.
- Dungeon reachability check: all seven guardian and exit tiles are reachable from their floor start.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/Lantern_Acre/Lantern_Acre.py Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py Firmware/Games/Aerial Dog Fight/AerialDogFight.py Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/code.py`: passed.
- `git diff --check`: passed after Lantern Acre integration.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/GameMenu.py Firmware/Games/Lantern_Acre/Lantern_Acre.py Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py Firmware/Games/Aerial Dog Fight/AerialDogFight.py Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/Games/Loose_Cows/Loose_Cows.py Firmware/code.py`: passed after SEL/menu integration.
- `git diff --check`: passed after animated-launcher integration.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/GameMenu.py Firmware/Games/Wildspark/Wildspark.py Firmware/Games/Lantern_Acre/Lantern_Acre.py Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py Firmware/Games/Aerial Dog Fight/AerialDogFight.py Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/Games/Loose_Cows/Loose_Cows.py Firmware/code.py`: passed after Wildspark integration.
- `git diff --check`: passed after Wildspark integration.
- Same full host syntax command and `git diff --check`: passed after lazy loading/unloading integration.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/Loose_Cows/Loose_Cows.py Firmware/Games/GameMenu.py Firmware/code.py`: passed after Loose Cows redesign; `git diff --check` passed.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/GameMenu.py Firmware/Games/Ironbound/Ironbound.py Firmware/Games/Wildspark/Wildspark.py Firmware/Games/Lantern_Acre/Lantern_Acre.py Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py Firmware/Games/Aerial Dog Fight/AerialDogFight.py Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/Games/Loose_Cows/Loose_Cows.py Firmware/code.py`: passed after Ironbound integration; `git diff --check` passed.
- `PYTHONPYCACHEPREFIX=/private/tmp/keyboy-pycache python3 -m py_compile Firmware/Games/GameMenu.py Firmware/Games/Last_Beacon/Last_Beacon.py Firmware/Games/Ironbound/Ironbound.py Firmware/Games/Wildspark/Wildspark.py Firmware/Games/Lantern_Acre/Lantern_Acre.py Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py Firmware/Games/Aerial Dog Fight/AerialDogFight.py Firmware/Games/Sprites_Journey/Sprites_Journey.py Firmware/Games/Loose_Cows/Loose_Cows.py Firmware/code.py`: passed after Last Beacon and launcher pagination; `git diff --check` passed.
- Same full host syntax command plus `Firmware/Games/KeyBoyAudio.py`: passed after I2S audio integration; `git diff --check` passed.
- Deployed to `/Volumes/CIRCUITPY`: all game modules/packages, `GameMenu.py`, `KeyBoyAudio.py`, and `code.py`; deployed `code.py` SHA-1 matched repository source after copy.
- Fixed CircuitPython positional-only `__import__` call and added an input-release guard before menu navigation; host syntax check and `git diff --check` passed, then deployed with matching SHA-1.
- Corrected SEL from IO12 to the schematic's IO40 and removed SEL from the launcher release guard; host syntax check passed and matching `code.py` deployed to CIRCUITPY.
- Separated highlighted menu row (`game_selected`) from pending launch (`launch_game`) to prevent D-pad navigation from launching a game; host syntax check and deployment hash passed.
- Replaced the persistent menu reset with a one-shot post-game `reset_menu` flag, and replaced Loose Cows' unsupported two-argument `next()` call with an explicit loop; host syntax checks and deployed hashes passed.
- Optimized Last Beacon to build terrain/HUD once per mission and mutate persistent entity TileGrids rather than clearing/reallocating the full display list every frame; host syntax check and deployed hash passed.
- Optimized Wildspark to retain overworld/battle TileGrids and labels between frames, rebuilding only after a state-changing transition; host syntax check, whitespace check, and deployed hash passed.
- Performance sweep verified Sprite's Journey, Aerial Dog Fight, Dungeons CYL, Loose Cows, Last Beacon, and the launcher already retain active scenes; optimized Ironbound's tactical board, Lantern Acre's farm/market navigation, and Wildspark's starter picker. Full-library syntax/whitespace checks and deployment hashes passed.

## Recent Changes

| Date | Tags | Change | Files | Commit | Remote |
| --- | --- | --- | --- | --- | --- |
| 2026-09-25 | beacon,art,combat,extraction | Added ship/loadout flow, detailed biomes/sprites, weapons/support, timed objectives/boarding, refits, LB2 migration and pooled rendering; host/device tested, existing save preserved. | `Firmware/Games/Last_Beacon/Last_Beacon.py`, `tests/`, `tools/preview_last_beacon.py`, `docs/last-beacon/`, `README.md` | Uncommitted | Local CIRCUITPY |
| 2026-09-25 | dungeons,maps,art,combat,validation | Repaired disconnected floors; upgraded art/combat/retries; proved all seven floors complete on host and twice on ESP32-S3. | `Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py`, `tests/test_dungeons.py`, `tests/dungeons_host.py`, `tools/preview_dungeons.py`, `docs/dungeons/`, `README.md` | Uncommitted | Local CIRCUITPY; best score preserved |
| 2026-09-25 | lantern,memory,wildspark,art,gameplay | Preallocated fragmented-heap-safe Lantern menus; upgraded Wildspark creature art, real party, combat and six-route campaign. | `Firmware/Games/Lantern_Acre/`, `Firmware/Games/Wildspark/`, `tests/`, `docs/`, `tools/preview_wildspark.py` | Uncommitted | Local CIRCUITPY; saves preserved |
| 2026-09-25 | lantern,art,performance,gameplay | Rebuilt farm artwork, larger animated farmer, usable cottage, 480-second days, crop economy and robust save feedback; host/device validated and deployed without changing save. | `Firmware/Games/Lantern_Acre/Lantern_Acre.py`, `tests/`, `tools/preview_lantern_acre.py`, `docs/lantern-acre/`, `README.md` | Uncommitted | Local CIRCUITPY |
| 2026-09-18 | platformer,launcher | Added the nine-level Sprite's Journey and launcher entry. | `Firmware/code.py`, `Firmware/Games/Sprites_Journey/Sprites_Journey.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | dogfight,launcher | Replaced incomplete image-based Aerial Dog Fight and added its launcher entry. | `Firmware/code.py`, `Firmware/Games/Aerial Dog Fight/AerialDogFight.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | dungeon,launcher | Added seven-floor Dungeons CYL crawler with guardian-gated exits and launcher entry. | `Firmware/code.py`, `Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | farming,launcher | Added Lantern Acre seasonal homestead and expanded launcher to five games. | `Firmware/code.py`, `Firmware/Games/Lantern_Acre/Lantern_Acre.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | pause,save,launcher | Added SEL menus, high scores/full farm saves, and animated KeyBoy launcher backdrop. | `Firmware/code.py`, `Firmware/Games/GameMenu.py`, game modules, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | creature-adventure,launcher | Added Wildspark campaign and sixth launcher entry. | `Firmware/code.py`, `Firmware/Games/Wildspark/Wildspark.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | memory,launcher | Replaced eager game imports with lazy load/unload and post-exit collection. | `Firmware/code.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | loose-cows,gameplay | Rebuilt Loose Cows as escalating corral herding with cows, obstacles, whistles, and combos. | `Firmware/Games/Loose_Cows/Loose_Cows.py` | Uncommitted | Not confirmed |
| 2026-09-18 | tactics,launcher | Added Ironbound procedural mech tactics campaign and seventh launcher entry. | `Firmware/code.py`, `Firmware/Games/Ironbound/Ironbound.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | extraction,launcher | Added Last Beacon and paginated the launcher into two four-game pages. | `Firmware/code.py`, `Firmware/Games/Last_Beacon/Last_Beacon.py`, `README.md` | Uncommitted | Not confirmed |
| 2026-09-18 | audio,deployment | Added I2S synthesized effects and deployed full game library/launcher to connected CIRCUITPY board. | `Firmware/code.py`, `Firmware/Games/KeyBoyAudio.py`, game modules, `README.md` | Uncommitted | Local CIRCUITPY |
| 2026-09-18 | launcher,fix | Fixed CircuitPython import keyword incompatibility and startup phantom selection. | `Firmware/code.py` | Uncommitted | Local CIRCUITPY |
| 2026-09-18 | wildspark,performance | Replaced per-frame display-list reconstruction with persistent overworld and battle scenes. | `Firmware/Games/Wildspark/Wildspark.py` | Uncommitted | Local CIRCUITPY |
| 2026-09-18 | performance,sweep | Converted Ironbound and Lantern Acre hot loops to persistent scenes and completed a no-full-redraw gameplay audit. | `Firmware/Games/Ironbound/Ironbound.py`, `Firmware/Games/Lantern_Acre/Lantern_Acre.py`, `Firmware/Games/Wildspark/Wildspark.py` | Uncommitted | Local CIRCUITPY |

## Open Threads

- User approved Lantern Acre and Last Beacon visuals/gameplay after hands-on play. Wildspark balance/exploration and upgraded Dungeons shield-combat feel need hands-on feedback. Dungeons automated host and device runs prove all seven floors completable. Successful writable-mode saves are not hardware-tested while CIRCUITPY is USB-mounted. Other games' prior playtest threads remain unchanged.
