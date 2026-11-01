# KeyBoy audio

[Listen to the sound tour](sound-tour.wav). Cues play in this order, separated
by half a second of silence:

| Cue | Meaning and sound |
| --- | --- |
| Move | Quiet rounded tap for a small action |
| Select | Two ascending confirmation notes |
| Jump | Rising pitch sweep |
| Shoot | Short falling laser pulse |
| Hit | Low descending impact |
| Collect | Bright two-note pickup chime |
| Win | Ascending victory phrase with a held final note |
| Lose | Descending defeat phrase |
| Lasso | Down-and-up whip sweep |
| Support | Three ascending system tones |
| Upgrade | Four-note rising arpeggio |
| Block | Brief metallic shield clang |
| Strike | Broader falling sword swipe |

The old engine played only eight sine cycles per cue, about 8–76 ms, with
abrupt endings and immediate interruption by the next event. The replacement
uses original 16 kHz, mono, 16-bit PCM assets with smooth attack/release
envelopes and silent boundaries. Most action cues last 80–235 ms; victory
and defeat have time to form recognizable melodies. Dungeons now distinguishes
sword swings from shield blocks; Wildspark uses the strike cue for strikes.

A continuously running I2S mixer avoids restarting the output for every cue.
Three voices reserve separate space for actions, feedback, and outcomes;
an occupied voice finishes naturally and drops new requests on that voice.
Rapid firing therefore cannot chop up a victory melody. Three reusable 1 KB
WAV buffers and a 2 KB mixer buffer stream assets from flash. Only the current
sample/file for each voice is retained; repeated identical cues reuse both.
The default volume is 0.85 with mixing headroom; `audio.volume` accepts 0–1.
Missing/bad assets are skipped without crashing the game.

## Install and regenerate

Copy `Firmware/Games/KeyBoyAudio.py` to `/lib/KeyBoyAudio.py` **and the entire
`Firmware/Games/KeyBoySounds` folder to `/lib/KeyBoySounds`**. The folder contains
13 WAV files totaling about 114 KB including headers. Install both components.
The existing I2S pins and launcher interface are unchanged.

```sh
python3 tools/generate_audio.py
python3 tests/test_audio.py
```

The generator creates every cue and the sound tour from deterministic synthesis;
there are no downloaded or licensed audio recordings. The runtime uses
CircuitPython's [mixer](https://docs.circuitpython.org/en/latest/shared-bindings/audiomixer/index.html)
and [WAV reader](https://docs.circuitpython.org/en/stable/shared-bindings/audiocore/).
The WAV buffer is passed positionally for compatibility with the board's older
CircuitPython 9.0.0-beta.2 firmware.

## Verification — 2026-09-26

Eight host tests pass: file format/duration, smooth silent boundaries, signal
levels/DC offset, complete cue coverage, voice isolation, replay reuse, decoder
lifetime, missing assets, mute/volume, and playback failures. All 83 game
regression tests pass; syntax and whitespace checks pass.

On the connected ESP32-S3, all 13 cues played to completion, three overlapping
voices worked, repeated firing did not interrupt the victory voice, and the
I2S mixer remained running through silence. Measured voice activity ranged
from about 0.11 to 0.77 seconds (includes decoder/buffer scheduling).
Lantern Acre then passed 30 menu cycles with audio active: 37,344 bytes free
at farm setup and 37,280 after the stress run. Source and assets are installed,
all existing save/high-score files were preserved, and the launcher restarted.
These checks validate playback and memory, not a microphone measurement or
a subjective speaker listening test.
