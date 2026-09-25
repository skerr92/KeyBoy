"""Asset signal checks and streaming/voice-lifetime behavior."""
import importlib.util
import io
import struct
import sys
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]


class Voice:
    def __init__(self):self.playing=False;self.level=0;self.calls=[]
    def play(self,sample):self.calls.append(sample);self.playing=True
class Mixer:
    def __init__(self,**kwargs):self.voice=[Voice() for _ in range(kwargs['voice_count'])];self.options=kwargs
class Output:
    def __init__(self,**kwargs):self.calls=[]
    def play(self,sample):self.calls.append(sample)
class Pin:
    def __init__(self,pin):self.value=False
class Sample:
    def __init__(self,stream,buffer):self.stream=stream;self.buffer=buffer;self.closed=False
    def deinit(self):self.closed=True


def load():
    modules={'audiobusio':types.SimpleNamespace(I2SOut=Output),'audiomixer':types.SimpleNamespace(Mixer=Mixer),
             'audiocore':types.SimpleNamespace(WaveFile=Sample),'board':types.SimpleNamespace(IO8=8,IO5=5,IO6=6,IO7=7),
             'digitalio':types.SimpleNamespace(DigitalInOut=Pin,Direction=types.SimpleNamespace(OUTPUT=1))}
    with patch.dict(sys.modules,modules):
        spec=importlib.util.spec_from_file_location('audio_under_test',ROOT/'Firmware/Games/KeyBoyAudio.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
M=load()


class AudioTests(unittest.TestCase):
    def setUp(self):self.a=M.KeyBoyAudio()
    def test_i2s_runs_once_with_fixed_format_and_silent_idle(self):
        self.assertEqual(self.a._audio.calls,[self.a._mixer])
        self.assertEqual(self.a._mixer.options['sample_rate'],16000)
        self.assertEqual(self.a._mixer.options['bits_per_sample'],16)
        self.assertTrue(self.a._enable.value)
        self.assertFalse(any(v.playing for v in self.a._mixer.voice))
    def test_busy_actions_never_restart_or_cut_off_outcomes(self):
        with patch('builtins.open',side_effect=lambda *a:io.BytesIO()):
            self.assertTrue(self.a.play('shoot'))
            self.assertFalse(self.a.play('shoot'))
            self.assertTrue(self.a.play('win'))
            self.assertTrue(self.a.play('hit'))
            self.assertFalse(self.a.play('move'))
        self.assertEqual([len(v.calls) for v in self.a._mixer.voice],[1,1,1])
        self.assertEqual(len(self.a._audio.calls),1)
    def test_repeated_effect_reuses_file_sample_and_buffer(self):
        with patch('builtins.open',return_value=io.BytesIO()) as opened:
            self.a.play('shoot');sample=self.a._samples[0]
            for _ in range(20):
                self.a._mixer.voice[0].playing=False
                self.a.play('shoot')
            self.assertEqual(opened.call_count,1)
            self.assertIs(self.a._samples[0],sample)
            self.assertIs(sample.buffer,self.a._buffers[0])
    def test_changing_cue_releases_completed_stream_and_reuses_buffer(self):
        with patch('builtins.open',side_effect=lambda *a:io.BytesIO()):
            self.a.play('shoot');old=self.a._samples[0]
            self.a._mixer.voice[0].playing=False
            self.a.play('jump')
        self.assertTrue(old.closed);self.assertTrue(old.stream.closed)
        self.assertIs(self.a._samples[0].buffer,old.buffer)
    def test_missing_and_bad_assets_are_skipped_without_repeat_opens(self):
        with patch('builtins.open',side_effect=OSError) as opened:
            self.assertFalse(self.a.play('hit'));self.assertFalse(self.a.play('hit'))
            self.assertEqual(opened.call_count,1)
        f=io.BytesIO()
        with patch('builtins.open',return_value=f),patch.object(M.audiocore,'WaveFile',side_effect=ValueError):
            self.assertFalse(self.a.play('collect'))
        self.assertTrue(f.closed)
    def test_unknown_muted_and_runtime_busy_are_safe(self):
        self.assertFalse(self.a.play('not-a-cue'))
        self.a.volume=0
        with patch('builtins.open',side_effect=AssertionError('muted file opened')):
            self.assertFalse(self.a.play('shoot'))
        self.a.volume=2
        self.assertEqual(self.a.volume,1)
        self.assertTrue(all(v.level==.6 for v in self.a._mixer.voice))
        with patch('builtins.open',return_value=io.BytesIO()),patch.object(self.a._mixer.voice[0],'play',side_effect=RuntimeError):
            self.assertFalse(self.a.play('shoot'))
    def test_assets_have_audible_lengths_smooth_edges_and_matching_format(self):
        signatures=set()
        for effect in M.KeyBoyAudio._CHANNELS:
            with self.subTest(effect=effect),wave.open(str(ROOT/'Firmware/Games/KeyBoySounds'/(effect+'.wav')),'rb') as f:
                self.assertEqual((f.getframerate(),f.getnchannels(),f.getsampwidth()),(16000,1,2))
                data=f.readframes(f.getnframes());samples=struct.unpack('<%dh'%(len(data)//2),data)
                self.assertGreaterEqual(len(samples)/16000,.075)
                self.assertLess(len(samples)/16000,.8)
                self.assertTrue(all(v==0 for v in samples[:80]+samples[-160:]))
                self.assertLess(max(abs(v) for v in samples),19000)
                self.assertGreater(max(abs(v) for v in samples),4000)
                self.assertLess(abs(sum(samples)/len(samples)),100)
                signatures.add(data)
        self.assertEqual(len(signatures),len(M.KeyBoyAudio._CHANNELS))
    def test_every_game_cue_has_an_asset(self):
        import re
        for p in (ROOT/'Firmware/Games').rglob('*.py'):
            if p.name=='KeyBoyAudio.py':continue
            for cue in re.findall(r"\.play\(['\"]([^'\"]+)['\"]\)",p.read_text()):
                self.assertIn(cue,M.KeyBoyAudio._CHANNELS,str(p))


if __name__=='__main__':unittest.main()
