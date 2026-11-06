# Zestaw do komponowania utworow na SNES (modul .it -> smconv): instrumenty i pomocnicze funkcje
import numpy as np, sys
sys.path.insert(0, '/home/claude/mus')
from itwriter import Song, n, CUT
R = 16744                 # 64 probki na okres dla C-5 (261.6 Hz)
rng = np.random.default_rng(11)
def _t(sec, rate=R): return np.arange(int(sec * rate)) / rate
def _L16(x): return x[:max(16, len(x) // 16 * 16)]
def _norm(x, g=0.9): return x / (np.max(np.abs(x)) + 1e-9) * g

def periodic(amps, cycles=4):
    x = np.arange(64 * cycles); w = np.zeros(len(x))
    for k, a in enumerate(amps, 1):
        if a: w += a * np.sin(2 * np.pi * k * x / 64)
    return _norm(w, 1.0)
def looped(amps, attack_cycles=8, loop_cycles=4, rise=60, bright=1.0):
    lp = periodic(amps, loop_cycles)
    att = np.concatenate([lp] * (attack_cycles // loop_cycles)) * np.linspace(bright, 1.0, 64 * attack_cycles)
    att = att * np.minimum(1, np.arange(len(att)) / rise)
    return np.concatenate([att, lp]) * 0.8, (len(att), len(att) + len(lp))

SAW = [1 / k for k in range(1, 16)]
SQUARE = [1 / k if k % 2 else 0 for k in range(1, 16)]
PULSE25 = [abs(np.sin(np.pi * k * 0.25)) / k for k in range(1, 16)]
INSTR = {
    'organ':   ([1, .8, .6, 0, .5, 0, .3, .25, 0, .1], 8, 60, 1.0),
    'strings': ([1 / k ** 1.15 for k in range(1, 14)], 16, 700, 0.9),
    'brass':   ([1 / k ** 1.25 for k in range(1, 13)], 16, 60, 1.25),
    'horn':    ([1, .55, .35, .2, .12, .07], 8, 120, 1.0),
    'flute':   ([1, .18, .06, .03], 8, 200, 1.0),
    'pulse':   (PULSE25, 8, 20, 1.0),
    'square':  (SQUARE, 8, 20, 1.0),
    'saw':     (SAW, 8, 20, 1.0),
    'reed':    ([1, .7, .9, .4, .6, .25, .35, .15, .2, .1], 8, 80, 1.1),   # bandoneon
    'sine':    ([1], 8, 200, 1.0),
    'power':   ([1, .9, .8, .75, .7, .6, .55, .5, .45, .4, .35, .3, .3, .25], 8, 10, 1.3),  # przesterowana gitara
}
def add_tonal(s, name, kind, vol=64):
    amps, att, rise, bright = INSTR[kind]
    d, loop = looped(amps, attack_cycles=att, rise=rise, bright=bright)
    return s.add_sample(name, d, R, loop=loop, vol=vol)

def add_decay(s, name, amps, dur, tau, vol=64, inharm=None):   # szarpane, fortepian, dzwony (bez petli)
    tt = _t(dur); w = np.zeros(len(tt)); f0 = R / 64
    for k, a in enumerate(amps, 1):
        f = f0 * (inharm[k - 1] if inharm else k)
        w += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / (tau / (1 + 0.4 * (k - 1))))
    w[:64] *= np.linspace(0, 1, 64)
    return s.add_sample(name, _L16(_norm(w)), R, vol=vol)

def add_drum(s, kind, vol=64):
    if kind == 'kick':
        tt = _t(0.28); f = 45 + 110 * np.exp(-tt / 0.03); w = np.sin(2 * np.pi * np.cumsum(f) / R) * np.exp(-tt / 0.12)
        w[:40] += rng.standard_normal(40) * 0.3
    elif kind == 'snare':
        tt = _t(0.2); w = rng.standard_normal(len(tt)) * np.exp(-tt / 0.05) + 0.5 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt / 0.03)
        w = np.convolve(w, [.5, .5], mode='same')
    elif kind == 'clap':
        tt = _t(0.2); env = np.exp(-tt / 0.06); w = rng.standard_normal(len(tt)) * env
        for o in (0.0, 0.012, 0.024): w[int(o * R):int(o * R) + 60] *= 2.0
    elif kind == 'hat':
        tt = _t(0.06); w = rng.standard_normal(len(tt)); w = w - np.convolve(w, np.ones(2) / 2, mode='same'); w *= np.exp(-tt / 0.015)
    elif kind == 'ohat':
        tt = _t(0.3); w = rng.standard_normal(len(tt)); w = w - np.convolve(w, np.ones(2) / 2, mode='same'); w *= np.exp(-tt / 0.1)
    elif kind == 'tom':
        tt = _t(0.3); f = 90 + 90 * np.exp(-tt / 0.05); w = np.sin(2 * np.pi * np.cumsum(f) / R) * np.exp(-tt / 0.1)
    elif kind == 'timp':   # gra 2 oktawy nizej
        tt = _t(0.22); g = (R / 64) * (1 + 0.08 * np.exp(-tt / 0.01)); w = np.sin(2 * np.pi * np.cumsum(g) / R) * np.exp(-tt / 0.07)
        w[:160] += rng.standard_normal(160) * np.linspace(0.6, 0, 160)
    elif kind == 'crash':
        r2 = R // 2; tt = _t(0.95, r2); w = rng.standard_normal(len(tt)); w = w - np.convolve(w, np.ones(3) / 3, mode='same'); w *= np.exp(-tt / 0.3)
        return s.add_sample('crash', _L16(_norm(w, 0.7)), r2, vol=vol)
    elif kind == 'tick':   # zegar: tyk
        tt = _t(0.05); w = np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt / 0.006) + 0.3 * rng.standard_normal(len(tt)) * np.exp(-tt / 0.002)
    elif kind == 'wood':
        tt = _t(0.08); w = np.sin(2 * np.pi * 900 * tt) * np.exp(-tt / 0.015)
    elif kind == 'zap':    # impuls elektryczny
        tt = _t(0.25); f = 3000 * np.exp(-tt / 0.05) + 200; w = np.sign(np.sin(2 * np.pi * np.cumsum(f) / R)) * np.exp(-tt / 0.08) * 0.6
        w += rng.standard_normal(len(tt)) * np.exp(-tt / 0.03) * 0.5
    elif kind == 'beep':   # ufo
        tt = _t(0.12); w = np.sign(np.sin(2 * np.pi * 1760 * tt)) * np.exp(-tt / 0.05) * 0.5
    elif kind == 'knock':  # golpe w tangu (uderzenie w pudlo)
        tt = _t(0.1); w = np.sin(2 * np.pi * 220 * tt) * np.exp(-tt / 0.02) + rng.standard_normal(len(tt)) * np.exp(-tt / 0.004) * 0.4
    else:
        raise ValueError(kind)
    return s.add_sample(kind, _L16(_norm(w)), R, vol=vol)

CHORD = {'m': [0, 3, 7], 'M': [0, 4, 7], '7': [0, 4, 7, 10], 'm7': [0, 3, 7, 10], 'dim': [0, 3, 6], 'sus4': [0, 5, 7], 'M7': [0, 4, 7, 11]}

class T:
    """Pomocnik: nuty z dlugoscia (automatyczne wyciszenie), rytmy perkusji, akordy, arpeggia."""
    def __init__(self, name, ch, tempo, speed=6):
        self.s = Song(name, ch, speed=speed, tempo=tempo); self.tempo = tempo
    def pat(self, rows=64, tempo=None, speed=None):
        p = self.s.new_pattern(rows)
        if tempo: self.s.put(p, 0, self.s.nch - 1, cmd=20, val=tempo)
        if speed: self.s.put(p, 0, self.s.nch - 2, cmd=1, val=speed)
        return p
    def rows(self, p): return len(self.s.patterns[p])
    def note(self, p, row, ch, nt, smp, vol=48, ln=None):
        if row >= self.rows(p): return
        self.s.put(p, row, ch, n(nt) if isinstance(nt, str) else nt, smp, vol)
        if ln and row + ln < self.rows(p): self.s.put(p, row + ln, ch, CUT)
    def seq(self, p, ch, smp, items, vol=48, start=0, shift=0, legato=False, fx=None):
        row = start                     # items: [('A-5', 4), ('-', 2), ...]
        for nt, ln in items:
            if nt != '-':
                nn = (n(nt) if isinstance(nt, str) else nt) + shift
                self.note(p, row, ch, nn, smp, vol, None if legato else ln)
                if fx and row < self.rows(p): self.s.put(p, row, ch, cmd=fx[0], val=fx[1])
            elif row < self.rows(p) and not legato:
                self.s.put(p, row, ch, CUT)
            row += ln
        return row
    def drum(self, p, ch, smp, pattern, nt='C-5', vols=(56, 40), start=0, bars=None):
        # pattern: 'X' mocno, 'x' slabiej, '.' nic; powtarzany do konca wzoru
        L = len(pattern); end = self.rows(p) if bars is None else start + bars * L
        for r in range(start, end):
            c = pattern[(r - start) % L]
            if c in 'Xx': self.note(p, r, ch, nt, smp, vols[0] if c == 'X' else vols[1])
    def chord_notes(self, root, q): return [n(root) + i for i in CHORD[q]]
    def arp(self, p, ch, smp, chords, step=2, bar=16, vol=36, order=(0, 1, 2, 1), octs=0, start=0):
        # chords: [('A-4','m'), ...] po jednym na takt; arpeggio co `step` wierszy
        for b, (root, q) in enumerate(chords):
            ns = self.chord_notes(root, q) + [self.chord_notes(root, q)[0] + 12]
            for i, r in enumerate(range(0, bar, step)):
                nt = ns[order[i % len(order)] % len(ns)] + 12 * octs
                self.note(p, start + b * bar + r, ch, nt, smp, vol, step)
    def block(self, p, chs, smp, chords, bar=16, vol=30, ln=None, hits=(0,), start=0):
        for b, (root, q) in enumerate(chords):
            ns = self.chord_notes(root, q)
            for h in hits:
                for k, ch in enumerate(chs):
                    self.note(p, start + b * bar + h, ch, ns[k % len(ns)], smp, vol, ln)
    def save(self, path, orders):
        self.s.orders = orders; return self.s.save(path)
