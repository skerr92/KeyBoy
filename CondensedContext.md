# CondensedContext

## Context Freshness

- Last Verified Commit: `7810d77`
- Current HEAD: `7810d77`
- Status: partial — game-library work is implemented but uncommitted.
- Files requiring verification: none outstanding for this task. Current changes remain uncommitted; `7810d77` contains the earlier game/audio baseline.
- Latest validation: 169 full-suite host tests plus added racing pause-clock test (12 racing tests pass); firmware syntax/whitespace pass. Native Courier all12 completions/undo/15 menus passed. Native racing all9 combinations currently running; docs pending final hardware figures.

## Current Focus

- Current request (2026-11-01): shorten Lantern Acre days to four active minutes (240s). LA4 saves preserve fractional day progress when loading LA2/LA3 eight-minute saves; legacy saves also migrate. 172 host tests pass, including rollover, pause and migration/roundtrip coverage.

- Previous request: choose and implement two new games. Clockwork Courier (12 solvable warehouse puzzles/undo/medals) and Drift Circuit (3 circuits/3 cars/boost/cup) implemented locally; host racing tests, native deployment, documentation still pending. Launcher extended to 10 games/3 pages, KeyBoyScenes helper evicted after exit. No commits requested.
- Preserve approved game/audio upgrades and all existing saves.

## Handoff

- Four-minute Lantern Acre update installed (2026-11-01): module bytes verified on connected CP10 KeyBoy; backup `/private/tmp/keyboy-backup-before-shorter-days-2026-11-01`; launcher restarted with no startup traceback. LA4 migrates old day fractions, 172 host tests pass; docs refreshed.

- New unit installed (2026-11-01): ESP32-S3 UID CD4557BCF703, CircuitPython 10.3.1, serial `/dev/cu.usbmodemCD4557BCF7031`. Added FourWire import fallback for CP10/CP9. Backed up visible device files to `/private/tmp/keyboy-backup-2026-11-01`; installed and byte-verified 37 firmware/audio files including all ten games; existing score file preserved. 171 host tests and whitespace checks pass. Native startup diagnostic constructed launcher and printed `KEYBOY_READY 10`; rebooted into normal code.py without startup errors. No base CircuitPython replacement needed. Physical playthrough remains user validation.

- Launcher/farm load fix COMPLETE: `KeyBoyLauncher.py` owns neon logo/skyline/emblems, 8Hz retained animations and edge-safe navigation. `code.py` deletes the menu instance/module and collects before game import, remembers selection on return. Lantern crop/farmer banks are 1,600/1,344B (aligned); all farm bitmap allocations ≤2,400B. 150 host tests pass. Native eight launcher→farm→launcher cycles passed with all sprite frames, 40 panels, both areas each cycle; farm heap67,600–67,792B, after unload155,696–155,888B. Sources match CIRCUITPY, all saves/scores byte-preserved, launcher restarted. Runner `/private/tmp/keyboy_launcher_smoke.py`; docs/previews `docs/launcher/`. No work remains for this request.

- Completed and installed: Beacon 8 missions/5 guns/5 kits; Lantern Meadow (+27 spaces, 53 total), named/seasonal packets, LA3 compatibility, and cached Season/Day sleep card; Wildspark explicit Catch/Weaken, habitat hints and all 27 forms catchable; three arcade games upgraded with illustrated/animated art and deeper objectives/upgrades.
- Lantern native stress passed 12 crossings, 60 menu openings and 4 morning cards (36–42KB free). Reuse one terrain canvas across areas: replacing strips caused fragmented-heap OOM after six crossings. Atlases and menus stay cached. Existing farm save unchanged.
- Beacon native all 8 objective/extraction sequences, all 5 guns/kits passed (93KB+ free), career unchanged. Wildspark native caught all 27 forms / all 9 families / full guide (85,968–86,432B free), original save unchanged.
- Arcade native final build passed all 9 Sprite rooms, 12 cached pause openings, both complete Dog Fight loadouts/ace fights, and 9 ranch layouts/whistles/animation frames. Original scores/saves unchanged; launcher restarted. No pending implementation work.
- Validation: 143 host tests; all firmware sources compile; whitespace clean. All 12 game/helper/launcher files and 13 WAV cues match CIRCUITPY. Device cannot write saves in USB programming mode; host serialization/migrations and native failure feedback are covered.
- Updated previews and controls/validation docs: `docs/arcade/`, `docs/lantern-acre/`, `docs/last-beacon/`, `docs/wildspark/`. Native runners remain in `/private/tmp/keyboy_{arcade_smoke,wildspark_catch,lantern_expansion,beacon_expansion}.py`; payload siblings preserve saves. Rewriting launcher recovered a temporary unresponsive serial console; latest runners assert DTR and stream results.
- Earlier Audio/Ironbound upgrades are retained, installed, tested. No commits were requested. Next useful step is normal hands-on play; no blocked checks remain for this task.

## Stable Facts

- `Firmware/code.py` owns display/button initialization and the game selector.
- Inputs are active-low `DigitalInOut` values; 240×240 display has `rotation=0`.

## Decisions

- New games fill puzzle/racing gaps: Courier has no timer/lives, progressive unlocks, gold/silver/bronze (36 medal points); Drift has 3-lap tracks, 120s active limit, +2s recovery also advances rivals, paused countdown/menus, per-track gold targets26/40/35s and 5/3/1 cup points. Small native pixel assets only, terrain reused across scenes, zero bitmap allocations during movement/racing. CC1/DC1 save completed progress/records (not mid-level state), transactional bounded parsing, atomic writes/read-only feedback.

- Use code-native pixel art rather than raster assets: it is smaller, deterministic, and needs no image loader or additional files.
- Sprite's Journey: 9 spark-gated rooms, 16×22 animated hero, ranged pooled magic, telegraphed guardian thorns, 3 hearts per room, life retries, buffered/coyote jumps and room4+ glide. Guardians on 3/6/9; art matches hitboxes. Legal-input completion policy in `tests/journey_solver.py`.
- Dog Fight: 4 coastal sectors, twin/rapid/armored starting choices (armor trades speed for +2 HP), inter-sector repair/loadout refits, rechargeable boost, hit invulnerability, 7 plane/28 projectile slots. Final 20HP ace stays until destroyed; only its defeat grants victory. Simulation clocks pause in overlays.
- Dungeons CYL has seven repaired, fully connected floors; guardian defeat opens the exit sprite. Cardinal BFS pursuit, fixed-target attack windups, guard/recovery combat, timed spike windows, preserved-at-full-health supplies, six hearts and full-health same-floor retries. Existing integer best-floor file `/dungeons.txt` stays compatible, written via temporary file/rename with failure feedback. Terrain/menu art remains resident through normal play.
- Lantern Acre uses small static 4-bit terrain/interior strips, 32-color crop/farmer atlases, 1-bit HUD, small banked crop/farmer atlases (≤1,600B), and preallocated 2-bit dual-skin menu atlas strips. Reuse one panel/label set for cottage/market/pause; collect before setup. Opening menus allocates no bitmap, avoiding fragmented-heap failures.
- User preference: richer sprite art, larger character, usable house, slower days, and no routine full-screen reconstruction. Movement/tending retain all farm objects; only dusk/night/dawn recolor the world palette (broad refresh at phase transitions).
- Lantern Acre days last 240 active seconds; menus freeze time. Cottage sleep advances growth and attempts save; crop values vary, copper can waters a row of three, cart adds $1/item, daily herbs prevent bankruptcy.
- Lantern Acre LA3 saves retain LA2 state plus area, selected seed, and four packet stocks. Load LA2/legacy 8-field saves transactionally; meadow uses x+12 crop keys. Six plots/53 spaces across two areas; only one terrain is resident, crop/farmer atlases and overlays persist. Named seeds grow any season with seasonal price discounts; mixed seeds remain current-season crops. Sleep shows a cached 1.8s Season/Day card, with save feedback. Use tuple concatenation rather than starred tuple literals on CP9.
- Standardize SEL (IO40) pause menus with high-score persistence, and give Lantern Acre full farm-state persistence.
- Wildspark: retained 4-bit scenery strips and two-frame 48px creatures; scene rebuilds only at route/battle transitions. Reuse menu backings/labels; keep one selected portrait. Catch at half HP is guaranteed and consumes no item; Weaken leaves ≥1 HP. Late trails4–6 cycle all27 forms, guide has count/habitats. Nine usable party families evolve at levels 4/8; Ember > Grove > Tide > Ember, focus-powered bursts and telegraphed enemy attacks. Six relics gate trails, emblems gate routes 2/4/6, then rival finale. WS2 persists party/XP/guide/relics/supplies; legacy seven-field saves preserve active creature/campaign but cannot recover unrecorded old species.
- Load selected games lazily and evict the game and shared pause-menu modules from `sys.modules` after exit; run `gc.collect()` after clearing display objects.
- Loose Cows: animated cream/gold cows and rancher, visible/releasable lasso, collision-safe whistles, quota-based deadlines ≥28s, combo/gold scores, 3 lives, rope/whistle/boots upgrades every3 rounds. Whistle/HP HUD, pause freezes timer/combo. Sprite/Cows/Flight share reusable 1920B terrain strips in KeyBoyArcade and cached GameMenu backing; launcher evicts both helpers.
- Ironbound: eight deterministic connected 8×8 operations (purge/relay/salvage/commander), retained terrain strips and 24×28 mech sprites, illustrated refit bay. Cardinal pathfinding, blocked-corner LOS, visible fixed-tile fire plans followed by a recovery turn. Cannon range3/free; rail range5/+2 damage/1 energy with cannon fallback. B guard recharges energy; systems offer guarded repair/EMP. Refit choices power/hull/armor, full supplies on deployment/retry. IB2 saves checkpoint campaign stats/loadout/finale, migrates legacy four fields, restarts current mission fresh. Atomic writes and explicit failure feedback.
- Last Beacon starts aboard the Wayfarer: choose any of eight contracts, carbine/scattergun/lancer/autocannon/breacher, and orbital/sentry/resupply/shield/stasis. Complete objectives, call extraction at E, survive 18 seconds, board within 12 seconds; overall deadlines 100–170s and menus freeze all clocks.
- Combat uses cover collision, held-A strafe/aim assist, magazines/auto reload/fallback sidearm, supply caches, invulnerability and limited support. Extraction-only credits fund three armor/power refit levels.
- Last Beacon LB2 stores contract/loadout, credits, cleared mask and refits. Legacy progress/power migrate; extra old support charges convert to $20 each. Debrief autosaves, ship services save manually, read-only failures are explicit; no mid-operation saves.
- Keep Last Beacon ship/terrain in <=2.3 KB static 4-bit strips, shared sprite atlases, 1-bit panels and bounded pools; avoid large contiguous background allocations. Target 33ms frame budget subtracts work time instead of adding a fixed sleep.
- Launcher: three pages (4/4/2 entries), Up/Down wraps selection, Left/Right pages, A edge confirms only after release. Custom bevelled logo, skyline, 10 themed emblems, twinkling stars/light sweep/bobbing icon. All bitmap assets retained while browsing, entire launcher released before game load, rebuilt on return with last selection.
- Audio uses IO8 amp enable and IO5/IO6/IO7 I2S pins. Continuous 3-voice mixer streams envelope-shaped WAV cues at 16 kHz/16-bit mono from `/lib/KeyBoySounds`; never restart a busy voice. Dedicated outcomes avoid gunfire interruption. Use positional WaveFile buffer for old CP9 compatibility; missing cues fail quietly. Generator/docs: `tools/generate_audio.py`, `docs/audio/`.
- Connected test board reports CircuitPython 9.0.0-beta.2 on ESP32-S3-DevKitM-1-N8; launcher uses `display.root_group` for that runtime.

## File Map

- `Firmware/Games/ClockworkCourier.py`: 12 delivery puzzles, reversible 128-move history, push medals and CC1 saves. `tests/test_courier.py`, `tests/courier_solutions.py`: all12 legal solutions/7 tests; `docs/clockwork-courier/` previews/controls.
- `Firmware/Games/DriftCircuit.py`: 3 tracks × 3 handling choices, finite boost, ordered checkpoints, non-contact pace rivals, cup/time trials and DC1 saves. `tests/test_drift.py`, `tests/drift_driver.py`: all9 combinations/legal controller policy/12 tests; `docs/drift-circuit/` previews/controls.
- `Firmware/Games/KeyBoyScenes.py`: shared retained 1920B terrain strips, cached scrolling panel, atomic save helper; launcher evicts it on exit. `tests/new_games_host.py`, `tools/preview_new_games.py`: host adapter/reproducible previews.

- `Firmware/code.py`: hardware setup/lazy game dispatch; `Firmware/Games/KeyBoyLauncher.py`: releasable animated menu. `tests/test_launcher.py`: 7 input/allocation checks; `tools/preview_launcher.py`, `docs/launcher/`: actual-art previews, deployment/memory notes.
- `Firmware/Games/Sprites_Journey/Sprites_Journey.py`: game runtime, art, stages, and collision.
- `Firmware/Games/Aerial Dog Fight/AerialDogFight.py`: top-down dogfight, generated planes, waves, and ace battle.
- `Firmware/Games/Dungeons Can You Leave/Dungeons_CYL.py`: dungeon art, repaired maps, shield combat/AI, gate progression, retries, best-score compatibility. `tests/dungeons_host.py`, `tests/test_dungeons.py`: display adapter and 18 behavioral/completion tests. `tools/preview_dungeons.py`, `docs/dungeons/`: seven-floor previews and controls/validation.
- `Firmware/Games/Lantern_Acre/Lantern_Acre.py`: self-contained pixel art, retained farm, movement, cottage/market/pause, timed days, crop economy and save migration.
- `tests/lantern_host.py`, `tests/test_lantern_acre.py`: display doubles/PNG renderer and 25 behavioral checks.
- `tools/preview_lantern_acre.py`, `docs/lantern-acre/`: reproducible art previews, controls, rendering limits and board validation.
- `Firmware/Games/GameMenu.py`: shared SEL pause overlay and high-score helper.
- `Firmware/Games/Loose_Cows/Loose_Cows.py`: illustrated herding, gold cows, ranch upgrades, collision-aware whistles and best scores.
- `Firmware/Games/Wildspark/Wildspark.py`: Wildspark art, exploration/party, tactical battles, relic/emblem campaign, evolution, WS2 persistence. `tests/test_wildspark.py` / `tests/wildspark_host.py`: 25 behavior checks using shared display doubles. `tools/preview_wildspark.py`, `docs/wildspark/`: actual-art previews and controls/validation.
- `Firmware/Games/Ironbound/Ironbound.py`: illustrated bay/8 operations, targeting/AI/systems/objectives/refits and IB2 checkpoints. `tests/test_ironbound.py`, `tests/ironbound_host.py`, `tests/ironbound_solver.py`: 26 tests and legal completion policy; `tools/preview_ironbound.py`, `docs/ironbound/`: art/controls/device validation.
- `Firmware/Games/Last_Beacon/Last_Beacon.py`: standalone ship/loadout, art, pooled combat, mission/extraction state machine, refits and career persistence.
- `tests/beacon_host.py`, `tests/test_last_beacon.py`: shared display double integration and 30 behavior/retention tests.
- `tools/preview_last_beacon.py`, `docs/last-beacon/`: actual-art previews and player/validation documentation.
- `Firmware/Games/KeyBoyAudio.py`: continuous three-voice I2S engine; `Firmware/Games/KeyBoySounds/`: 13 streamed original WAV cues. `tools/generate_audio.py`, `tests/test_audio.py`, `docs/audio/`: deterministic synthesis, eight host tests, sound tour and deployment/validation notes.

- `Firmware/Games/KeyBoyArcade.py`: shared retained scenery/animated actors/loadout overlay. `tests/arcade_host.py`, `tests/test_arcade.py`, `tests/journey_solver.py`: 12 arcade behavior/completion checks; `tools/preview_arcade.py` and `docs/arcade/`: previews, deployment and native results.

## Validation Memory

- Current sweep (2026-09-26): `python3 -m unittest discover -s tests -q` passes 143 tests. Native Beacon8 extractions, Lantern12 crossings/60 panels/4 cards, Wildspark27 catches, Sprite9 rooms, Flight2 full campaigns, Ranch9 layouts all pass. All12 deployed source files/13 audio cues match; saves/scores byte-preserved. New arcade pause stress leaves87,792B; flight79KB; ranch≥94KB. Details in game docs.

- Ironbound overhaul (2026-09-26): 26 host tests pass, including 48 legal mission completions (8 maps × 2 weapons × 3 refit paths), all tiles reachable, IB2 migration and full finale. Entire suite: 117 tests pass. Syntax/whitespace pass. ESP32-S3 completed 16 operations across both weapons, ~66–69 KB free; bay+field builds 8.28–8.97s combined. Source deployed, save unchanged, launcher restarted. `tests/ironbound_solver.py` is the reusable completion policy; `tools/preview_ironbound.py` renders actual art into `docs/ironbound/`.

- Audio (2026-09-26): 8 audio + 83 game host tests pass. ESP32-S3 plays all 13 WAVs, overlaps 3 voices, repeated firing and persistent silent I2S validated; 30 Lantern audio/menu cycles pass (~37 KB free). Module/assets installed, saves unchanged. Real listening feedback remains subjective.

- Dungeons upgrade (2026-09-25): 18 host tests; real ESP32-S3 completes all 7 floors twice without damage using guard/trap timing, no HP edits/teleports. Free heap matches per floor across runs (65,744–67,168 bytes), ~3.64–3.97s builds. Read-only save failure, installed source equality, score preservation, and launcher restart verified. Other three games: 65 regressions pass.

- Lantern menu fix (2026-09-25): 17 host tests, actual 90-cycle fragmented-memory menu stress pass; ~38,464 bytes free during stress, 44,352 after releasing fragments. Preallocated panels take ~7.18s at startup. Source installed, save unchanged. Supersedes earlier large-bitmap menu design.
- Wildspark overhaul (2026-09-25): 23 host tests, syntax/whitespace pass; real ESP32-S3 18-cycle world/battle/portrait-menu stress passes, all 27 forms and read-only save failure exercised. World build ~2.29s; battle free memory stable ~78 KB, final world 87,824 bytes. Deployed source matches, save unchanged. Last Beacon 25 regressions pass.

- Last Beacon (2026-09-25): 25 host checks pass; Lantern Acre 15 regression checks pass; syntax and whitespace pass. Connected ESP32-S3 smoke validates all five contracts/extraction, ship/refit/field overlays, actor pool stress, save migration and read-only failure. Small bitmap strips resolved contiguous allocation failures; ~90 KB heap free after collection. Source installed, old save unchanged. Detailed final figures in `docs/last-beacon/README.md`.

- Lantern Acre (2026-09-25): 15 host tests, host syntax and whitespace checks pass; real ESP32-S3/CircuitPython 9.0.0-beta.2 smoke with launcher/audio resident passes, source/deployment bytes match, original save unchanged. Initial 8-bit menu/interior allocations exhausted heap; fixed with low-bit-depth palettes and pre-menu collection. No measured SPI/frame-rate benchmark.

- Known validation commands: `python3 -m unittest discover -s tests -q`, `python3 tools/preview_<game>.py`, built-in `compile()` for firmware syntax, and `git diff --check`. Host display doubles do not measure SPI throughput or physical frame rate.

## Known Constraints

- Native target is ESP32-S3/CircuitPython 9.0.0-beta.2. Use positional `__import__` arguments and WaveFile buffer; starred tuple literals are unsupported (concatenate tuples). Terrain buffers must use small strips and be reused where fragmentation was observed.
- USB programming mode makes game saves read-only. Never overwrite player saves during device tests; stage test progress only in RAM and verify original bytes afterward.
- Launcher navigation separates selected row from pending launch and waits for button release; SEL is IO40. Clear display references and evict game/helper modules on exit before garbage collection.
- Native serial checks use `/dev/cu.usbmodemCD4557BCF74A1` and `/Volumes/CIRCUITPY`; assert raw-REPL handshake and a complete success marker, then restart the launcher. An empty handshake is not a passed test.

## Coverage

- All eight game runtimes, launcher, shared audio/menu/art helpers and behavior tests are indexed above. Detailed actual-art previews and native results live under `docs/`. No frame-rate or SPI benchmark was performed.

## Recent Changes

| Date | Tags | Change | Files | Commit | Remote |
| --- | --- | --- | --- | --- | --- |
| 2026-09-26 | launcher,art,lantern,memory | Animated arcade menu; release menu before game load; small farm sprite banks; 150 host tests and eight native launcher/farm cycles pass, saves unchanged. | KeyBoyLauncher.py, code.py, Lantern_Acre.py, tests, docs/launcher | Uncommitted | CIRCUITPY verified |
| 2026-09-26 | arcade,capture,expansion,validation | Finished Beacon/Lantern expansions, made all Wildspark forms catchable, polished three arcade games and cached pause overlays; 143 host tests and native completion/stress checks pass. | game modules, tests, docs, launcher | Uncommitted | CIRCUITPY verified; saves preserved |
| 2026-09-25 | beacon,art,combat,extraction | Added ship/loadout flow, detailed biomes/sprites, weapons/support, timed objectives/boarding, refits, LB2 migration and pooled rendering; host/device tested, existing save preserved. | `Firmware/Games/Last_Beacon/Last_Beacon.py`, `tests/`, `tools/preview_last_beacon.py`, `docs/last-beacon/`, `README.md` | Uncommitted | Local CIRCUITPY |
| 2026-09-26 | ironbound,art,tactics,campaign,saves | Rebuilt mech art/refit bay, ranged targeting, enemy intent/recovery, objectives, systems and chosen refits; IB2 migration and host completion proofs. | `Firmware/Games/Ironbound/Ironbound.py`, `tests/ironbound*`, `tests/test_ironbound.py`, `tools/preview_ironbound.py`, `docs/ironbound/` | Uncommitted | Local CIRCUITPY; save preserved |
| 2026-09-26 | audio,streaming,assets | Replaced click-like sine bursts with 13 shaped effects, continuous three-voice I2S mixer, streamed WAVs, distinct strike/block cues; board validated. | `Firmware/Games/KeyBoyAudio.py`, `Firmware/Games/KeyBoySounds/`, `tools/generate_audio.py`, `tests/test_audio.py`, `docs/audio/` | Uncommitted | Local CIRCUITPY; saves preserved |
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

- User approved Lantern Acre and Last Beacon visuals/gameplay after hands-on play. Wildspark balance/exploration, Dungeons shield combat, Ironbound tactics, and new audio timbre/volume benefit from hands-on feedback. Dungeons automated host and device runs prove all seven floors completable. Successful writable-mode saves are not hardware-tested while CIRCUITPY is USB-mounted. Other games' prior playtest threads remain unchanged.
