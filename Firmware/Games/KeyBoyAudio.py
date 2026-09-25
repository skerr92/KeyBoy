# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Envelope-shaped, streamed cues on a continuously running I2S mixer.

Three reserved voices keep actions, feedback, and outcomes independent.
An occupied voice finishes naturally rather than being abruptly restarted.
"""
import audiobusio
import audiocore
import audiomixer
import board
from digitalio import DigitalInOut, Direction


class KeyBoyAudio:
    SAMPLE_RATE = 16000
    # Actions / feedback / outcomes. Important melodies never lose their
    # voice to rapid firing, footsteps, damage, or collections.
    _CHANNELS = {
        'move':0, 'select':0, 'jump':0, 'shoot':0, 'lasso':0, 'strike':0,
        'hit':1, 'collect':1, 'support':1, 'block':1,
        'win':2, 'lose':2, 'upgrade':2,
    }

    def __init__(self, volume=0.85):
        self._enable=DigitalInOut(board.IO8)
        self._enable.direction=Direction.OUTPUT
        self._enable.value=False
        self._audio=audiobusio.I2SOut(bit_clock=board.IO5,word_select=board.IO6,data=board.IO7)
        self._mixer=audiomixer.Mixer(voice_count=3,buffer_size=2048,
                                   channel_count=1,bits_per_sample=16,
                                   samples_signed=True,sample_rate=self.SAMPLE_RATE)
        self._buffers=[bytearray(1024) for _ in range(3)]
        self._files=[None]*3
        self._samples=[None]*3
        self._effects=[None]*3
        self._missing=set()
        self.volume=volume
        # Keep the digital clock/data stream running through silence. Starting
        # and stopping the I2S device for every effect causes amplifier pops.
        self._audio.play(self._mixer)
        self._enable.value=True

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self,value):
        self._volume=max(0.0,min(1.0,float(value)))
        for voice in self._mixer.voice:
            voice.level=self._volume*0.6  # Headroom even with all three voices active.

    def _release(self,channel):
        sample=self._samples[channel]
        if sample is not None:
            sample.deinit()
            self._samples[channel]=None
        stream=self._files[channel]
        if stream is not None:
            stream.close()
            self._files[channel]=None
        self._effects[channel]=None

    def play(self,effect):
        channel=self._CHANNELS.get(effect)
        if channel is None or effect in self._missing or self._volume==0:
            return False
        voice=self._mixer.voice[channel]
        if voice.playing:
            return False
        # No allocation for repeated gunshots/footsteps on the same channel.
        if self._effects[channel]!=effect:
            self._release(channel)
            stream=None
            sample=None
            try:
                stream=open('/lib/KeyBoySounds/'+effect+'.wav','rb')
                sample=audiocore.WaveFile(stream,self._buffers[channel])
                self._files[channel],self._samples[channel]=stream,sample
                self._effects[channel]=effect
            except (OSError,ValueError):
                if sample is not None:
                    sample.deinit()
                if stream is not None:
                    stream.close()
                # A missing/bad optional cue must not crash or repeatedly
                # hammer the filesystem from the game's update loop.
                self._missing.add(effect)
                return False
        try:
            voice.play(self._samples[channel])
            return True
        except RuntimeError:
            return False
