"""Build original, deterministic KeyBoy PCM effects; no external audio assets."""
import math
import struct
import wave
from pathlib import Path

RATE = 16000
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'Firmware/Games/KeyBoySounds'


def tone(start, end, duration, level=0.48, color='bell'):
    count = round(RATE * duration)
    result = []
    phase = 0.0
    for i in range(count):
        t = i / max(1, count - 1)
        phase += 2 * math.pi * (start + (end-start)*t) / RATE
        # 6 ms attack and 22 ms release remove hard waveform edges.
        attack = min(1, i / (RATE * .006))
        release = min(1, (count-1-i) / (RATE * .022))
        envelope = math.sin(attack*math.pi/2)**2 * math.sin(release*math.pi/2)**2
        if color == 'bell':
            value = (math.sin(phase) + .23*math.sin(phase*2) + .08*math.sin(phase*3)) / 1.31
            envelope *= math.exp(-2.2*t)
        elif color == 'round':
            value = (math.sin(phase) + .18*math.sin(phase*3)) / 1.18
        else:
            value = (math.sin(phase) + .35*math.sin(phase*2) + .2*math.sin(phase*5)) / 1.55
            envelope *= 1 - .6*t
        result.append(round(32767 * level * envelope * value))
    return result


def notes(pitches, length=.10, color='bell'):
    data=[]
    for pitch in pitches:
        data += tone(pitch,pitch,length,color=color)
        data += [0]*round(.012*RATE)
    return data


def build():
    sounds = {
        'move': tone(420,480,.065,.30),
        'select': notes((660,880),.065),
        'jump': tone(300,1050,.18,.48,'round'),
        'shoot': tone(1450,260,.075,.48,'edge'),
        'hit': tone(210,95,.16,.56,'edge'),
        'collect': notes((880,1320),.095),
        'win': notes((523,659,784),.11)+tone(1047,1047,.24,.48,'round'),
        'lose': notes((392,311,247),.16,'round')+tone(196,147,.22,.44,'round'),
        'lasso': tone(850,340,.12,.43,'round')+tone(340,680,.10,.43,'round'),
        'support': notes((330,440,660),.09,'round'),
        'upgrade': notes((523,659,784,1047),.095),
        'block': tone(900,600,.095,.40,'edge'),
        'strike': tone(1100,350,.11,.43,'edge'),
    }
    # Silence at the boundaries also gives the decoder a quiet final buffer.
    return {name: [0]*80+data+[0]*160 for name,data in sounds.items()}


def write_wav(path,data):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(struct.pack('<%dh'%len(data),*data))


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    sounds=build()
    for name,data in sounds.items():
        write_wav(OUTPUT/(name+'.wav'),data)
    # Preview follows the table order in docs/audio/README.md, with clear gaps.
    preview=[]
    for data in sounds.values():
        preview+=data+[0]*(RATE//2)
    out=ROOT/'docs/audio'
    out.mkdir(parents=True,exist_ok=True)
    write_wav(out/'sound-tour.wav',preview)
    print('Generated',len(sounds),'effects;',sum(len(v)*2 for v in sounds.values()),'PCM bytes')


if __name__=='__main__':
    main()
