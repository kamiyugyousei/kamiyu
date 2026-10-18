import numpy as np, wave
SR = 44100; DUR = 5.2
N = int(SR * DUR); out = np.zeros(N)
rng = np.random.default_rng(3)
BEAT = 60 / 150; T0 = 1.0

def add(sig, t, gain=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i < N: out[i:j] += sig[:j - i] * gain

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def lowpass(x, alpha):
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)): acc += alpha * (x[i] - acc); y[i] = acc
    return y

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 1.0
def snare():
    n = int(0.25 * SR); t = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.6 * np.exp(-t * 18) + np.sin(2 * np.pi * 190 * t) * 0.5 * np.exp(-t * 25))
def hat(op=False):
    n = int((0.12 if op else 0.05) * SR); x = rng.standard_normal(n)
    x = x - lowpass(x, 0.3)
    return x * np.exp(-np.arange(n) / SR * (20 if op else 70)) * 0.35
def crash():
    n = int(1.6 * SR); x = rng.standard_normal(n); x = x - lowpass(x, 0.2)
    return x * env(n, 0.002, 0.55) * 0.45

def ks(freq, dur, bright=0.5):
    n = int(dur * SR); p = int(SR / freq)
    buf = rng.uniform(-1, 1, p); buf = lowpass(np.concatenate([buf]), bright)[:p]
    y = np.zeros(n)
    for i in range(n):
        y[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return y

mid = lambda m: 440 * 2 ** ((m - 69) / 12)
CH = {'C': [48, 52, 55, 60, 64], 'D': [50, 57, 62, 66], 'Bm': [47, 54, 59, 62, 66], 'Em': [40, 47, 52, 55, 59, 64]}
PROG = [(0, 'C'), (1.8, 'D'), (2.6, 'Bm'), (3.4, 'Em'), (4.2, 'C')]
def chord_at(t):
    c = 'C'
    for s, n in PROG:
        if t >= s - 0.01: c = n
    return c
cache = {}
def note(m, dur):
    k = (m, dur)
    if k not in cache: cache[k] = ks(mid(m), dur)
    return cache[k]

def strum(t, name, down, gain, dur=0.45):
    notes = CH[name] if down else CH[name][-4:][::-1]
    for i, m in enumerate(notes if down else notes):
        add(note(m, dur) * gain, t + i * (0.009 if down else 0.007))

# intro: breath + reverse-swell
n = int(0.8 * SR); b = rng.standard_normal(n); b = lowpass(b, 0.08)
add(b * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.5, 0.1)
n = int(0.9 * SR); r = rng.standard_normal(n); r = r - lowpass(r, 0.15)
add(r * (np.arange(n) / n) ** 3 * 0.35, 0.1)
# soft pre-strum ring at 0
strum(0.05, 'C', True, 0.25, 1.0)

step = BEAT / 2
k = 0; t = T0
while t < 4.6 - 1e-6:
    down = k % 2 == 0
    strum(t, chord_at(t), down, (0.55 if down else 0.35) * (1 + 0.3 * (t > 2.5)), 0.4)
    if k % 2 == 0:  # beat
        beat = k // 2
        add(kick(), t, 0.9)
        if beat % 2 == 1: add(snare(), t, 0.7)
        # bass root
        root = CH[chord_at(t)][0] - 12 if chord_at(t) != 'Em' else 28
        bn = int(BEAT * SR); tt = np.arange(bn) / SR
        bs = np.sign(np.sin(2 * np.pi * mid(root) * tt)) * 0.5 + np.sin(2 * np.pi * mid(root) * tt)
        add(lowpass(bs, 0.05) * np.exp(-tt * 3) * 0.6, t)
    add(hat(), t, 0.8 if not (t > 2.5) else 1.0)
    if t > 2.5: add(hat(), t + step / 2, 0.5)
    k += 1; t = T0 + k * step
# fills & crashes
for ct in [1.0, 2.6, 4.0]: add(crash(), ct, 1.0 if ct == 4.0 else 0.7)
for i in range(4): add(snare(), 3.8 + i * 0.05, 0.4 + i * 0.1)
add(kick(), 4.0, 1.0)
# final big strum let ring
strum(4.6, 'C', True, 0.9, 0.6)
add(kick(), 4.6, 1.0); add(crash(), 4.6, 0.8)

# distorted power layer from 2.5 for energy
for s, e, name in [(2.5, 3.4, 'Bm'), (3.4, 4.2, 'Em'), (4.2, 5.2, 'C')]:
    n = int((e - s) * SR); tt = np.arange(n) / SR
    root = CH[name][0]
    sig = sum(np.sin(2 * np.pi * mid(root + iv) * tt) for iv in (0, 7, 12))
    sig = np.tanh(sig * 3) * 0.12 * (1 - np.exp(-tt * 30))
    if name == 'C': sig *= np.exp(-tt * 1.5)
    add(sig, s)

out = np.tanh(out * 0.9)
out /= np.max(np.abs(out)) * 1.1
fade = int(0.15 * SR); out[-fade:] *= np.linspace(1, 0, fade)
pcm = (np.stack([out, out], 1) * 32767).astype(np.int16)
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
