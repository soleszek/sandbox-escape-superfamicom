"""Syntezuje efekty dzwiekowe Super FamiPong jako WAV 12 kHz, 16 bit, mono.

Uruchom z katalogu projektu:  python3 tools/make_sfx.py
Makefile zamienia WAV na BRR (format probek SPC700) narzedziem snesbrr.
12 kHz to pitch 6 w spcSetSoundEntry (czestotliwosc = pitch * 2000 Hz).
"""
import wave
import numpy as np

RATE = 12000


def note(name):
    names = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7,
             'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    n, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (octave + 1) - 69) / 12)


def t_axis(dur):
    return np.arange(int(RATE * dur)) / RATE


def env(n, attack=0.01, decay_to=0.6, release=0.05):
    """Prosta obwiednia: narastanie, lagodny spadek, wygaszenie na koncu."""
    e = np.ones(n)
    a = max(1, int(attack * RATE))
    r = max(1, int(release * RATE))
    e[:a] = np.linspace(0, 1, a)
    e[a:] = np.linspace(1, decay_to, n - a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def pulse(freq, t, duty=0.25, vibrato=0.0):
    phase = freq * t + (vibrato * np.sin(2 * np.pi * 5.5 * t) / 5.5 if vibrato else 0)
    return np.where((phase % 1.0) < duty, 1.0, -1.0) * 0.6


def brass(freq, t, bright=1.0, vibrato=0.0):
    """Pila skladana z harmonicznych (bez aliasingu) - brzmienie w stylu traby."""
    out = np.zeros_like(t)
    vib = vibrato * np.sin(2 * np.pi * 5.5 * t) / 5.5 if vibrato else 0
    k = 1
    while freq * k < RATE / 2 * 0.9:
        out += np.sin(2 * np.pi * freq * k * (t + vib / freq)) / k * np.exp(-(k - 1) / (3.0 * bright))
        k += 1
    return out / 1.6


def mix(parts, total):
    out = np.zeros(int(RATE * total))
    for start, sig in parts:
        i = int(start * RATE)
        n = min(len(sig), len(out) - i)
        out[i:i + n] += sig[:n]
    return out


def save(sig, path, peak=0.85):
    sig = sig / max(1e-9, np.max(np.abs(sig))) * peak
    pad = (-len(sig)) % 16              # BRR koduje bloki po 16 probek
    sig = np.concatenate([sig, np.zeros(pad + 16)])
    data = (sig * 32767).astype('<i2').tobytes()
    w = wave.open(path, 'wb')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(data)
    w.close()
    print(f'{path}: {len(sig) / RATE:.2f} s')


def chord(notes, dur, **kw):
    t = t_axis(dur)
    s = sum(pulse(note(n), t, **kw) for n in notes) / len(notes)
    return s


def make_tada():
    ta = chord(['G4', 'B4', 'D5'], 0.11) * env(int(0.11 * RATE), 0.004, 0.8, 0.02)
    dam_t = t_axis(0.75)
    dam = sum(pulse(note(n), dam_t, duty=0.25, vibrato=0.004) for n in ['C5', 'E5', 'G5', 'C6']) / 4
    dam *= env(len(dam_t), 0.006, 0.35, 0.2)
    save(mix([(0, ta), (0.15, dam)], 0.95), 'tada.wav')


def make_tok(freq, path, length=0.09):
    """Odbicie pileczki: krotki klik szumu + szybko gasnacy ton, ktory lekko opada."""
    t = t_axis(length)
    f = freq * (1 - 0.08 * t / length)
    tone = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t / 0.012)
    tone += 0.35 * np.sin(2 * np.pi * np.cumsum(f * 2.7) / RATE) * np.exp(-t / 0.006)
    rng = np.random.default_rng(int(freq))
    click = rng.uniform(-1, 1, len(t)) * np.exp(-t / 0.0015) * 0.8
    save(tone + click, path, peak=0.9)


def make_fanfare():
    beat = 0.12
    melody = [('G4', 1), ('G4', 1), ('G4', 1), ('C5', 3), ('E5', 1), ('G5', 1), ('C6', 8)]
    parts, pos = [], 0.0
    for n, length in melody:
        dur = length * beat
        t = t_axis(dur + 0.03)
        long_note = length >= 8
        s = brass(note(n), t, bright=1.4, vibrato=0.006 if long_note else 0)
        s *= env(len(t), 0.015, 0.45 if long_note else 0.85, 0.25 if long_note else 0.03)
        parts.append((pos, s))
        if long_note:  # akord pod ostatnia nuta
            for h in ('C5', 'E5', 'G5'):
                hs = brass(note(h), t, bright=1.0) * env(len(t), 0.02, 0.4, 0.25) * 0.45
                parts.append((pos, hs))
        pos += dur
    save(mix(parts, pos + 0.1), 'fanfare.wav')


def make_sad():
    """Smutne wah-wah-wah-waaah: cztery opadajace nuty z filtrem 'wah'."""
    notes = [('G3', 0.42), ('F#3', 0.42), ('F3', 0.42), ('E3', 1.15)]
    parts, pos = [], 0.0
    for i, (n, dur) in enumerate(notes):
        t = t_axis(dur)
        last = i == len(notes) - 1
        f0 = note(n)
        vib = 0.012 * np.sin(2 * np.pi * 5.0 * t) * (t > 0.25) if last else 0
        f = f0 * (1 + vib)
        phase = np.cumsum(f) / RATE
        # jasnosc rosnie i opada w kazdej nucie, co daje efekt "wah"
        bright = 0.6 + 2.6 * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
        s = np.zeros_like(t)
        k = 1
        while f0 * k < RATE / 2 * 0.9:
            s += np.sin(2 * np.pi * k * phase) / k * np.exp(-(k - 1) / bright)
            k += 1
        s *= env(len(t), 0.03, 0.7, 0.3 if last else 0.06)
        parts.append((pos, s))
        pos += dur
    save(mix(parts, pos + 0.05), 'sad.wav')


# --- Dzwieki mocy specjalnych i ekranu wyboru ---------------------------------
def sweep(f0, f1, dur, shape='sine', curve=None):
    t = t_axis(dur)
    k = t / dur if curve is None else curve(t / dur)
    f = f0 + (f1 - f0) * k
    ph = np.cumsum(f) / RATE
    if shape == 'square':
        return np.where((ph % 1.0) < 0.5, 1.0, -1.0) * 0.6
    return np.sin(2 * np.pi * ph)


def make_thunder():
    # grzmot: krotki trzask i dlugi, niski pomruk (szum brazowy z wolnym zanikiem)
    sr = 12000; n = int(sr * 1.1); t = np.arange(n) / sr
    rng = np.random.default_rng(5)
    crack = rng.standard_normal(n) * np.exp(-t / 0.035)
    brown = np.cumsum(rng.standard_normal(n)); brown -= np.convolve(brown, np.ones(400) / 400, mode='same')
    rumble = brown / (np.max(np.abs(brown)) + 1e-9)
    k = np.ones(25) / 25; rumble = np.convolve(rumble, k, mode='same')          # ciemniejszy pomruk
    swell = (1 - np.exp(-t / 0.08)) * np.exp(-t / 0.45) * (1 + 0.35 * np.sin(2 * np.pi * 3.1 * t))
    save(0.35 * crack + 1.0 * rumble * swell, 'thunder.wav', peak=0.9)


def make_tick():
    t = t_axis(0.03)
    save(pulse(1800, t, duty=0.5) * np.exp(-t / 0.008), 'tick.wav', peak=0.6)


def make_confirm():
    a = pulse(note('E6'), t_axis(0.06), duty=0.5) * env(int(0.06 * RATE), 0.002, 0.8, 0.01)
    b = pulse(note('A6'), t_axis(0.1), duty=0.5) * env(int(0.1 * RATE), 0.002, 0.4, 0.04)
    save(mix([(0, a), (0.06, b)], 0.17), 'confirm.wav', peak=0.7)


def make_ready():
    parts = []
    for i, n in enumerate(['C5', 'E5', 'G5', 'C6']):
        d = 0.09 if i < 3 else 0.2
        parts.append((i * 0.07, pulse(note(n), t_axis(d), duty=0.25) * env(int(d * RATE), 0.003, 0.6, 0.04)))
    save(mix(parts, 0.45), 'ready.wav')


def make_arm():
    s = sweep(300, 1300, 0.25, 'square', curve=lambda k: k ** 1.6)
    save(s * env(len(s), 0.01, 0.9, 0.05), 'arm.wav', peak=0.7)


def make_super():
    t = t_axis(0.4)
    rng = np.random.default_rng(7)
    noise = rng.uniform(-1, 1, len(t))
    noise = np.convolve(noise, np.ones(3) / 3, mode='same')   # lekko przyciemniony szum
    whoosh = noise * np.exp(-t / 0.12) * 0.7
    boom = np.sin(2 * np.pi * np.cumsum(110 * np.exp(-t / 0.15) + 45) / RATE) * np.exp(-t / 0.14)
    save(whoosh + boom, 'super.wav')


def make_curve():
    s = sweep(800, 1600, 0.2) 
    s2 = sweep(1600, 900, 0.2)
    sig = np.concatenate([s, s2])
    save(sig * env(len(sig), 0.01, 0.7, 0.08), 'curve.wav', peak=0.7)


def make_zigzag():
    t = t_axis(0.35)
    f = np.where((np.floor(t / 0.04) % 2) == 0, 420.0, 940.0)
    ph = np.cumsum(f) / RATE
    sig = np.where((ph % 1.0) < 0.5, 1.0, -1.0) * np.exp(-t / 0.14)
    save(sig, 'zigzag.wav', peak=0.6)


def make_ghost():
    t = t_axis(0.5)
    f = 520 * (1 + 0.06 * np.sin(2 * np.pi * 7 * t)) * (1 - 0.25 * t / 0.5)
    sig = np.sin(2 * np.pi * np.cumsum(f) / RATE) * (0.6 + 0.4 * np.sin(2 * np.pi * 11 * t))
    sig += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / RATE)
    save(sig * env(len(t), 0.06, 0.6, 0.15), 'ghost.wav', peak=0.7)


if __name__ == '__main__':
    make_tada()
    make_tok(1320, 'tok1.wav')
    make_tok(1060, 'tok2.wav')
    make_tok(760, 'tokwall.wav', length=0.07)
    make_fanfare()
    make_sad()
    make_tick()
    make_confirm()
    make_ready()
    make_arm()
    make_super()
    make_curve()
    make_zigzag()
    make_ghost()
    make_thunder()
