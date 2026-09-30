#!/usr/bin/env python3
"""sfx_score.py — the wolfpack-launch-15s score, written on scripts/sfx_palette.py.

python3 sfx_score.py → sfx.wav (48 kHz, peak -8 dBFS)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from sfx_palette import Score, air, glass, wood, sub, bubble, wobble, pan_of
import numpy as np
rng = np.random.default_rng(7)
s = Score(dur=15.0, T60=1.1)
place = s.place

# 1 · board hold — a soft breath as the cursor drifts in, then the click
place(air(0.5, 260, 900, 1.2, 0.6), 0.55, 0.14, pan_of(700), 0.4)
place(wood(210, 0.09), 1.05, 0.34, pan_of(700), 0.2)

# 2 · card → detail morph — a rising whoosh that lands as the panel opens
place(air(1.0, 300, 2400, 1.3, 0.45), 1.35, 0.42, -0.05, 0.5, pan_to=0.0)
place(sub(64, 0.6), 2.55, 0.24, 0.0, 0.35)

# 3 · picker opens, click Claude, avatar morphs — three quick, close-together hits
place(bubble(520, 0.22), 3.55, 0.24, 0.0, 0.3)
place(wood(230, 0.08), 3.98, 0.30, 0.0, 0.2)
place(glass(880, 0.9, 0.6), 4.15, 0.20, 0.0, 0.45)
place(bubble(640, 0.24), 4.45, 0.22, 0.0, 0.3)          # impact settle on the new avatar

# 4 · status pill ticks to In Progress
place(wood(260, 0.08), 4.65, 0.26, 0.0, 0.2)

# 5 · near-silence #1 — three activity rows rise, one glass tick each, quiet
for t, f in zip((4.95, 5.37, 5.79), (523, 587, 659)):
    place(glass(f, 0.7, 0.6), t, 0.13, 0.0, 0.45)

# 6 · list → tool timeline morph
place(air(0.5, 320, 2200, 1.3, 0.5), 6.55, 0.28, 0.0, 0.4)

# 7 · near-silence #2 — the work happens; five tool rows tick in, spaced, quiet
for i, t in enumerate((7.25, 7.80, 8.35, 8.90, 9.45)):
    place(wood(200 + i * 6, 0.07), t + 0.32, 0.16, 0.0, 0.25)

# 8 · last row completes — the emotional beat: status flips to Done
place(sub(70, 0.55), 9.85, 0.38, 0.0, 0.35)
place(glass(784, 1.1, 0.5), 10.15, 0.22, 0.0, 0.5)
place(glass(1046, 1.1, 0.4), 10.17, 0.16, 0.0, 0.5)

# 9 · detail → small card shrink, then the arc hop to Done
place(air(0.7, 2000, 300, 1.4, 0.4), 10.45, 0.30, 0.0, 0.4)
place(air(0.9, 260, 1400, 1.2, 0.55), 11.15, 0.30, 0.0, 0.5, pan_to=0.6)
place(sub(62, 0.5), 12.35, 0.28, 0.6, 0.35)             # felt landing in Done

# 10 · board hold rhymes with the open, then iris opens from the check glyph
place(air(0.6, 220, 1200, 1.1, 0.5), 13.15, 0.32, 0.6, 0.45, pan_to=0.0)

# 11 · wordmark + icon drop, end-card hold
place(sub(50, 1.2), 13.45, 0.46, 0.0, 0.45)
place(glass(392, 1.6, 0.3), 13.55, 0.12, 0.0, 0.7)

s.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx.wav"))
