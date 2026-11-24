"""Dzwieki intro (WAV 12 kHz mono, Makefile zamienia je na BRR):
   ithud.wav  - uderzenie piescia w biurko
   icrash.wav - uderzenie w laptopa (trzask plastiku, klawisze, zaklocenie ekranu)
   ishout.wav - krotki, chrapliwy krzyk mezczyzny
   iboom.wav  - kinowe uderzenie ("Enough!")
Uruchom z katalogu projektu:  python3 tools/make_intro_sfx.py
"""
import wave
import numpy as np

RATE = 12000
rng = np.random.default_rng(2211)


def t_axis(dur):
    return np.arange(int(RATE * dur)) / RATE


def save(sig, path, peak=0.92):
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * peak
    n = len(sig) // 16 * 16
    data = (sig[:n] * 32767).astype('<i2').tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)
    print(path, '%.2f s' % (n / RATE))


def reson(x, f, bw):
    """rezonator 2. rzedu (formant / pasmo)"""
    r = np.exp(-np.pi * bw / RATE)
    c = 2 * r * np.cos(2 * np.pi * f / RATE)
    y = np.zeros(len(x))
    y1 = y2 = 0.0
    g = (1 - r)
    for i in range(len(x)):
        v = g * x[i] + c * y1 - r * r * y2
        y[i] = v
        y2, y1 = y1, v
    return y


def reson_var(x, fs, bw):
    """rezonator o zmiennej czestotliwosci (fs: tablica)"""
    r = np.exp(-np.pi * bw / RATE)
    y = np.zeros(len(x))
    y1 = y2 = 0.0
    g = (1 - r)
    for i in range(len(x)):
        c = 2 * r * np.cos(2 * np.pi * fs[i] / RATE)
        v = g * x[i] + c * y1 - r * r * y2
        y[i] = v
        y2, y1 = y1, v
    return y


def lowpass(x, a):
    y = np.zeros(len(x))
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def reverb(x, dur, decay, mix):
    """poglos: splot z zanikajacym szumem"""
    tt = t_axis(dur)
    ir = rng.standard_normal(len(tt)) * np.exp(-tt / decay)
    ir = lowpass(ir, 0.35)
    ir[0] = 0
    wet = np.convolve(x, ir)[:len(x) + len(tt)]
    wet = wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(x))
    out = np.zeros(len(wet))
    out[:len(x)] += x
    return out + wet * mix


def make_thud():
    tt = t_axis(0.42)
    f = 70 + 80 * np.exp(-tt / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    body = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * np.exp(-tt / 0.10)
    knock = reson(rng.standard_normal(len(tt)), 520, 260) * np.exp(-tt / 0.025) * 7
    knock += reson(rng.standard_normal(len(tt)), 1150, 400) * np.exp(-tt / 0.012) * 4
    rattle = np.zeros(len(tt))
    for d in (0.035, 0.06, 0.085, 0.13, 0.17):     # drobiazgi na biurku podskakuja
        i = int(d * RATE)
        n = int(0.02 * RATE)
        burst = reson(rng.standard_normal(n), rng.uniform(2200, 3600), 500) * np.exp(-np.arange(n) / (0.004 * RATE))
        rattle[i:i + n] += burst * rng.uniform(1.5, 3.0) * np.exp(-d / 0.1)
    sig = np.tanh((body * 1.2 + knock + rattle) * 1.4)
    save(sig, 'ithud.wav')


def make_crash():
    tt = t_axis(0.72)
    f = 80 + 90 * np.exp(-tt / 0.03)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    body = (np.sin(ph) + 0.5 * np.sin(2 * ph)) * np.exp(-tt / 0.09)
    crack = np.zeros(len(tt))
    for fr, bw, tau, a in ((1800, 300, 0.03, 6), (2650, 380, 0.022, 5), (3400, 500, 0.015, 4), (900, 250, 0.04, 4)):
        crack += reson(rng.standard_normal(len(tt)), fr, bw) * np.exp(-tt / tau) * a
    keys = np.zeros(len(tt))
    for k in range(22):                              # klawisze klekoca
        d = 0.01 + rng.exponential(0.06)
        if d > 0.3:
            continue
        i = int(d * RATE)
        n = int(0.012 * RATE)
        burst = reson(rng.standard_normal(n), rng.uniform(1500, 4200), 600) * np.exp(-np.arange(n) / (0.003 * RATE))
        keys[i:i + n] += burst * rng.uniform(0.8, 2.0) * np.exp(-d / 0.15)
    # zaklocenie ekranu: brzeczenie z przerwami
    bz = np.sign(np.sin(2 * np.pi * 118 * tt)) * 0.5 + np.sign(np.sin(2 * np.pi * 236.5 * tt)) * 0.25
    bz = np.round(bz * 3) / 3
    gate = (np.sin(2 * np.pi * 23 * tt) > -0.2).astype(float)
    benv = np.where(tt > 0.05, np.exp(-(tt - 0.05) / 0.22), 0) * gate
    sig = np.tanh((body * 1.3 + crack + keys) * 2.2) + bz * benv * 0.45
    save(sig, 'icrash.wav')


def make_shout():
    """krotki, chrapliwy krzyk ("Aaargh!"): zrodlo krtaniowe z chrypka przez formanty samogloski"""
    dur = 0.78
    tt = t_axis(dur)
    n = len(tt)
    f0 = np.interp(tt, [0, 0.10, 0.45, 0.78], [175, 238, 226, 160])
    f0 = f0 * (1 + 0.025 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1)))   # drzenie
    ph = np.cumsum(f0) / RATE
    src = np.zeros(n)
    k = 1
    while k * 300 < RATE / 2:                        # pila bez aliasingu (wiele harmonicznych)
        amp = np.where(f0 * k < RATE / 2 * 0.95, 1.0 / k, 0)
        src += amp * np.sin(2 * np.pi * k * ph)
        k += 1
    cyc = np.floor(ph)
    sub = np.where(cyc % 2 == 0, 1.0, 0.55)           # co drugi cykl slabszy: chrypka (podwojenie okresu)
    src *= sub
    asp = rng.standard_normal(n) * (0.55 + 0.45 * np.sin(2 * np.pi * ph))   # szum oddechu w rytmie glosni
    src = src + asp * 0.9
    src = np.tanh(src * 2.2)                           # zdarte gardlo
    f1 = np.interp(tt, [0, 0.4, 0.78], [820, 760, 640])
    f2 = np.interp(tt, [0, 0.4, 0.78], [1300, 1220, 1080])
    v = reson_var(src, f1, 110) * 1.0 + reson_var(src, f2, 140) * 0.75
    v += reson(src, 2650, 200) * 0.45 + reson(src, 3500, 260) * 0.25
    env = np.minimum(1, tt / 0.035) * np.where(tt > 0.6, np.exp(-(tt - 0.6) / 0.07), 1.0)
    env *= 1 + 0.25 * np.sin(2 * np.pi * 9 * tt)        # lekkie lamanie sie glosu
    sig = np.tanh(v * env * 3.0)
    sig = reverb(sig, 0.35, 0.08, 0.18)
    save(sig, 'ishout.wav')


def make_boom():
    dur = 2.2
    tt = t_axis(dur)
    f = 32 + 48 * np.exp(-tt / 0.35)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    sub = (np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.12 * np.sin(4 * ph)) * np.exp(-tt / 0.9)
    hit = reson(rng.standard_normal(len(tt)), 160, 120) * np.exp(-tt / 0.06) * 6
    hit += lowpass(rng.standard_normal(len(tt)), 0.25) * np.exp(-tt / 0.03) * 2.5
    braam = np.zeros(len(tt))
    for fq, a in ((55, 1.0), (55.6, 0.8), (82.4, 0.6), (110.3, 0.45)):   # niski, chropowaty akord
        p = 2 * np.pi * fq * tt
        for k in range(1, 30):
            if fq * k > RATE / 2 * 0.9:
                break
            braam += a * np.sin(k * p + k) / k * np.exp(-k / 9)
    braam *= np.minimum(1, tt / 0.02) * np.exp(-tt / 0.8)
    braam = lowpass(braam, 0.3)
    sig = np.tanh((sub * 1.6 + hit + braam * 0.9) * 3.0)
    sig = reverb(sig, 1.4, 0.5, 0.25)[:len(tt)]
    sig = np.tanh(sig / np.max(np.abs(sig)) * 2.2)
    sig *= np.where(tt > 1.7, np.exp(-(tt - 1.7) / 0.18), 1.0)
    save(sig, 'iboom.wav')


if __name__ == '__main__':
    make_thud()
    make_crash()
    make_shout()
    make_boom()
