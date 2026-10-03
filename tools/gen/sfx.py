"""Synthesized sound effects and a looping chiptune track (16-bit mono WAV, 22.05 kHz)."""
import math
import random
import struct
import wave

SR = 22050
TAU = 2 * math.pi


def wav_write(path, samples, gain=0.9):
    peak = max(1e-9, max(abs(s) for s in samples))
    k = min(1.0, gain / peak) if peak > gain else 1.0
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s * k)) * 32767)) for s in samples))


def osc(kind, ph):
    p = ph % 1.0
    if kind == "sine":
        return math.sin(TAU * p)
    if kind == "square":
        return 1.0 if p < 0.5 else -1.0
    if kind == "saw":
        return 2 * p - 1
    if kind == "tri":
        return 4 * abs(p - 0.5) - 1
    return 0.0


def tone(f0, dur, kind="sine", f1=None, vol=1.0, attack=0.004, decay=None, vib=0.0):
    """One voice: frequency glide f0 -> f1, exponential-ish decay."""
    n = int(dur * SR)
    out = []
    ph = 0.0
    f1 = f0 if f1 is None else f1
    decay = dur if decay is None else decay
    for i in range(n):
        t = i / SR
        f = f0 + (f1 - f0) * (i / n)
        if vib:
            f *= 1 + vib * math.sin(TAU * 6 * t)
        ph += f / SR
        env = min(1.0, t / attack) * math.exp(-4.0 * t / decay)
        out.append(osc(kind, ph) * env * vol)
    return out


def noise(dur, vol=1.0, decay=None, lp=1.0, seed=1):
    rnd = random.Random(seed)
    n = int(dur * SR)
    decay = dur if decay is None else decay
    out, y = [], 0.0
    for i in range(n):
        x = rnd.uniform(-1, 1)
        y += (x - y) * lp  # one-pole low-pass: lp 1 = white, small = rumble
        out.append(y * math.exp(-4.0 * (i / SR) / decay) * vol)
    return out


def mix(*tracks, length=None):
    n = length or max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t[:n]):
            out[i] += v
    return out


def at(track, offset):
    return [0.0] * int(offset * SR) + track


def seq(*items):
    out = []
    for it in items:
        out += it
    return out


def note(n):  # semitones from A4
    return 440.0 * 2 ** (n / 12)


def effects():
    fx = {}
    fx["arrow"] = mix(noise(0.13, 0.5, 0.06, 0.5, 3), tone(900, 0.12, "tri", 380, 0.45, decay=0.07))
    fx["cannon"] = mix(tone(150, 0.4, "sine", 38, 1.0, decay=0.25), noise(0.35, 0.8, 0.12, 0.12, 4))
    fx["frost"] = mix(tone(1500, 0.28, "sine", 2300, 0.4, decay=0.14, vib=0.03), tone(2200, 0.22, "sine", 1700, 0.25, decay=0.1))
    fx["hit"] = mix(noise(0.05, 0.7, 0.025, 0.7, 5), tone(300, 0.05, "square", 160, 0.25, decay=0.03))
    fx["explode"] = mix(noise(0.55, 1.0, 0.3, 0.2, 6), tone(110, 0.5, "sine", 30, 0.9, decay=0.3))
    fx["die"] = mix(tone(520, 0.26, "square", 130, 0.35, decay=0.14), noise(0.12, 0.3, 0.06, 0.4, 7))
    fx["coin"] = seq(tone(988, 0.07, "square", None, 0.35, decay=0.05), tone(1319, 0.2, "square", None, 0.35, decay=0.14))
    fx["build"] = mix(tone(180, 0.12, "square", 90, 0.5, decay=0.07), noise(0.1, 0.6, 0.05, 0.25, 8), at(tone(420, 0.14, "tri", 640, 0.4, decay=0.1), 0.08))
    fx["sell"] = seq(tone(1319, 0.06, "square", None, 0.3, decay=0.05), tone(1047, 0.06, "square", None, 0.3, decay=0.05), tone(784, 0.14, "square", None, 0.3, decay=0.1))
    fx["upgrade"] = seq(*[tone(note(n), 0.1, "square", None, 0.3, decay=0.08) for n in (0, 4, 7, 12)])
    fx["leak"] = mix(tone(220, 0.45, "saw", 70, 0.55, decay=0.3), noise(0.25, 0.3, 0.12, 0.3, 9))
    fx["wave"] = mix(tone(165, 0.7, "saw", None, 0.35, attack=0.05, decay=0.7), tone(247, 0.7, "saw", None, 0.28, attack=0.05, decay=0.7), at(tone(330, 0.6, "saw", None, 0.28, attack=0.04, decay=0.5), 0.35))
    fx["win"] = seq(*[tone(note(n), 0.16, "square", None, 0.3, decay=0.14) for n in (-9, -5, -2, 3)], tone(note(3), 0.7, "square", None, 0.3, decay=0.6, vib=0.01))
    fx["lose"] = seq(*[tone(note(n), 0.28, "tri", None, 0.5, decay=0.25) for n in (-2, -5, -9)], tone(note(-14), 0.9, "tri", note(-16), 0.5, decay=0.8))
    fx["fire"] = mix(noise(0.22, 0.5, 0.12, 0.35, 11), tone(420, 0.2, "saw", 160, 0.3, decay=0.12))
    fx["merge"] = seq(*[tone(note(n), 0.09, "square", None, 0.3, decay=0.08) for n in (-2, 2, 5, 9)], tone(note(14), 0.35, "tri", None, 0.45, decay=0.3, vib=0.01))
    fx["summon"] = mix(tone(300, 0.18, "tri", 700, 0.45, decay=0.12), noise(0.12, 0.35, 0.06, 0.4, 12), at(tone(900, 0.16, "sine", 1300, 0.3, decay=0.1), 0.1))
    fx["click"] = tone(1200, 0.04, "square", 800, 0.25, decay=0.03)
    fx["deny"] = seq(tone(180, 0.08, "square", None, 0.3, decay=0.06), tone(140, 0.12, "square", None, 0.3, decay=0.09))
    return fx


def music():
    """8 bars of 4/4 at 116 bpm: pad + arpeggio + bass + drums, loops seamlessly."""
    bpm = 116
    beat = 60 / bpm
    bars = 8
    total = int(bars * 4 * beat * SR)
    out = [0.0] * total

    def put(track, t0):
        i0 = int(t0 * SR)
        for i, v in enumerate(track):
            if i0 + i < total:
                out[i0 + i] += v

    # chord roots (semitones from A4) and minor/major triads
    prog = [(-12, "m"), (-16, "M"), (-21, "M"), (-14, "M"), (-12, "m"), (-16, "M"), (-14, "M"), (-17, "M")]
    # (root of A=-12 is A3). triads in semitones above the root
    tri = {"m": (0, 3, 7), "M": (0, 4, 7)}
    melody = [  # (beat offset in bar, semitone from A4 or None, beats)
        [(0, 12, 1), (1, 15, 0.5), (1.5, 14, 0.5), (2, 12, 1), (3, 10, 1)],
        [(0, 12, 1.5), (1.5, 10, 0.5), (2, 8, 1), (3, 12, 1)],
        [(0, 7, 1), (1, 12, 1), (2, 14, 1), (3, 12, 1)],
        [(0, 14, 2), (2, 11, 1), (3, 14, 1)],
        [(0, 12, 1), (1, 15, 1), (2, 19, 1), (3, 15, 1)],
        [(0, 17, 1.5), (1.5, 15, 0.5), (2, 12, 2)],
        [(0, 14, 1), (1, 11, 1), (2, 14, 1), (3, 11, 1)],
        [(0, 12, 3), (3, 7, 1)],
    ]
    for b, ((root, q), mel) in enumerate(zip(prog, melody)):
        t_bar = b * 4 * beat
        for i in range(8):  # arpeggio, eighth notes
            semis = root + 12 + tri[q][[0, 1, 2, 1, 0, 1, 2, 1][i]]
            put(tone(note(semis), beat * 0.5, "square", None, 0.07, decay=beat * 0.45), t_bar + i * beat * 0.5)
        put(tone(note(root), beat * 3.8, "sine", None, 0.34, attack=0.02, decay=beat * 3.5), t_bar)  # bass
        put(tone(note(root - 12 + 12), beat * 1.0, "tri", None, 0.0), t_bar)
        for s in tri[q]:  # pad
            put(tone(note(root + 12 + s), beat * 4, "tri", None, 0.06, attack=0.15, decay=beat * 6), t_bar)
        for off, semis, ln in mel:
            put(tone(note(semis), ln * beat * 0.95, "square", None, 0.1, attack=0.01, decay=ln * beat * 0.8, vib=0.004), t_bar + off * beat)
        for k in (0, 2):  # kick
            put(tone(130, 0.18, "sine", 45, 0.55, decay=0.1), t_bar + k * beat)
        for k in range(8):  # hats
            put(noise(0.04, 0.12 if k % 2 else 0.07, 0.02, 0.9, 50 + k + b), t_bar + k * beat * 0.5)
        put(noise(0.14, 0.2, 0.07, 0.6, 99 + b), t_bar + 1 * beat)  # snare
        put(noise(0.14, 0.2, 0.07, 0.6, 199 + b), t_bar + 3 * beat)
    return out
