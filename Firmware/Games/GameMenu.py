# SPDX-FileCopyrightText: Copyright (c) 2026 Seth Kerr
# SPDX-License-Identifier: MIT
"""Shared SEL pause menu and tiny high-score persistence helpers for KeyBoy."""

import time
import displayio
from adafruit_display_text import label
import terminalio


def save_high_score(path, score):
    """Keep the greater of score and the existing integer stored at path."""
    previous = 0
    try:
        score_file = open(path, "rt")
        previous = int(score_file.readline())
        score_file.close()
    except (OSError, ValueError):
        pass
    if score > previous:
        try:
            score_file = open(path, "wt")
            score_file.write(str(score))
            score_file.close()
            return score
        except OSError:
            return previous
    return previous


class PauseMenu:
    """Modal overlay controlled by SEL, D-pad, and A; returns True to leave."""
    def __init__(self, splash, sel_btn, a_btn, up_btn, down_btn):
        self._splash = splash
        self._sel = sel_btn
        self._a = a_btn
        self._up = up_btn
        self._down = down_btn
        self._cache = None

    def pressed(self):
        return self._sel.value == 0

    def open(self, title, score, score_path=None, save_callback=None):
        if self._cache is None:
            panel_bitmap = displayio.Bitmap(196, 126, 1)
            panel_palette = displayio.Palette(1)
            panel_palette[0] = 0x18233E
            panel = displayio.Group(x=22, y=55)
            panel.append(displayio.TileGrid(panel_bitmap, pixel_shader=panel_palette))
            title_label = label.Label(terminalio.FONT, text=title, color=0xFFE5A3, x=14, y=18)
            panel.append(title_label)
            score_label = label.Label(terminalio.FONT, text="SCORE " + str(score), color=0xD8E9FF, x=14, y=36)
            panel.append(score_label)
            options = ("Resume", "Save", "Leave game")
            option_labels = []
            for index, option in enumerate(options):
                option_label = label.Label(terminalio.FONT, text=option, color=0xFFFFFF, x=32, y=57 + index * 20)
                panel.append(option_label)
                option_labels.append(option_label)
            selector = label.Label(terminalio.FONT, text=">", color=0xFFE5A3, x=15, y=57)
            panel.append(selector)
            self._cache = (panel, title_label, score_label, selector)
        panel, title_label, score_label, selector = self._cache
        title_label.text = title
        score_label.text = "SCORE " + str(score)
        selector.y = 57
        options = ("Resume", "Save", "Leave game")
        self._splash.append(panel)
        choice = 0
        last_move = 0
        a_was_down = not self._a.value
        # Finish the SEL press that opened the menu before accepting a new action.
        while self._sel.value == 0:
            time.sleep(0.03)
        while True:
            now = time.monotonic()
            if now - last_move > 0.15:
                if self._up.value == 0:
                    choice = (choice - 1) % len(options)
                    selector.y = 57 + choice * 20
                    last_move = now
                elif self._down.value == 0:
                    choice = (choice + 1) % len(options)
                    selector.y = 57 + choice * 20
                    last_move = now
            a_down = self._a.value == 0
            if a_down and not a_was_down:
                if choice == 0:
                    self._splash.remove(panel)
                    return False
                if choice == 1:
                    if save_callback:
                        save_callback()
                        score_label.text = "SAVED"
                    elif score_path:
                        score_label.text = "BEST " + str(save_high_score(score_path, score))
                else:
                    if save_callback:
                        save_callback()
                    elif score_path:
                        save_high_score(score_path, score)
                    self._splash.remove(panel)
                    return True
            a_was_down = a_down
            if self._sel.value == 0:
                self._splash.remove(panel)
                return False
            time.sleep(0.03)
