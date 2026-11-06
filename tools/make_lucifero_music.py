# LUCIFERO: ciemny ambient (mgla) i industrialna przemiana (rdza) - wlasna kompozycja.
import numpy as np, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from itwriter import Song, n, CUT
R = 16744; R2 = R // 2; R4 = R // 4
rng = np.random.default_rng(66)
def t(sec, rate): return np.arange(int(sec * rate)) / rate
def L16(x): return x[:max(16, len(x) // 16 * 16)]
def nz(x, g=0.92): return x / (np.max(np.abs(x)) + 1e-9) * g
def periodic(amps, cycles=4, per=64):
    x = np.arange(per * cycles); w = np.zeros(len(x))
    for k, a in enumerate(amps, 1): w += a * np.sin(2 * np.pi * k * x / per)
    return w / np.max(np.abs(w))
def looped(amps, att_cycles=8, per=64, rise=200):
    lp = periodic(amps, 4, per); att = np.concatenate([lp] * (att_cycles // 4)) * np.minimum(1, np.arange(per * att_cycles) / rise)
    return np.concatenate([att, lp]) * 0.85, (len(att), len(att) + len(lp))
# 1-2 pogłos (dwie kopie, druga o ok. 10 centow wyzej - dudnienie)
drone, dloop = looped([.8, .75, .6, .45, .32, .22, .14, .08], 8, rise=480)   # MIKS: wiecej wyzszych harmonicznych
# 3 rozstrojone pianino (dwie struny rozjechane o ok. 8 centow), R2: 32 probki na okres C-5
tt = t(1.4, R2); f = R2 / 32; pno = np.zeros(len(tt))
for k in range(1, 9):
    fk = f * k * np.sqrt(1 + 0.0004 * k * k); a = 1 / k ** 1.2; tau = 1.3 / k ** 0.6
    pno += a * (np.sin(2 * np.pi * fk * tt) + 0.8 * np.sin(2 * np.pi * fk * 1.0047 * tt + 0.7)) * np.exp(-tt / tau)
pno[:40] += rng.standard_normal(40) * 0.15
pno = L16(nz(pno) * np.minimum(1, np.arange(len(tt)) / 12))
# 4 odlegle uderzenie metalu (R4 - stlumione, jakby z daleka)
tt = t(0.9, R4); f = R4 / 16; cl = np.zeros(len(tt))
for r, a, tau in ((1, 1, .5), (2.76, .7, .35), (5.4, .45, .2), (8.93, .3, .12)):
    if f * r < R4 / 2: cl += a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt / tau)
cl += rng.standard_normal(len(tt)) * np.exp(-tt / 0.05) * 0.4
cl = L16(nz(cl))
# 5 gluche dudnienie
tt = t(0.6, R4); fq = 40 + 50 * np.exp(-tt / 0.05); ph = 2 * np.pi * np.cumsum(fq) / R4
th = (np.sin(ph) + 0.55 * np.sin(2 * ph) + 0.35 * np.sin(3 * ph) + 0.2 * np.sin(4 * ph)) * np.exp(-tt / 0.22)   # MIKS2: bas slyszalny na malych glosnikach
th = np.tanh(th * 1.6) + 0.5 * np.sin(2 * np.pi * 400 * tt) * np.exp(-tt / 0.012)   # MIKS2: stukniecie
th[:60] += rng.standard_normal(60) * 0.4; th = L16(nz(th))
# 6 trzaski radia (petla szumu z trzaskami)
st = rng.standard_normal(2048); st = np.convolve(st, [0.4, 0.3, 0.2, 0.1], mode='same')
for i in rng.integers(0, 2048, 40): st[i:i + 3] += rng.choice([-2.5, 2.5])
st = nz(st, 0.8)
# 7 wysoki, drzacy ton
eer, eloop = looped([1, .15, .05], 8, rise=300)
# 8 uderzenie w rure (krotkie, metaliczne)
tt = t(0.35, R2); f = R2 / 32; bg = np.zeros(len(tt))
for r, a, tau in ((1, 1, .18), (2.4, .8, .12), (3.9, .6, .08), (6.3, .4, .05)):
    bg += a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt / tau)
bg += rng.standard_normal(len(tt)) * np.exp(-tt / 0.02) * 0.8; bg = L16(nz(bg))
# 9 zgrzyt (szum przez filtr grzebieniowy - metaliczny), petla
gr = rng.standard_normal(2048 + 64); d = 32
for i in range(d, len(gr)): gr[i] += 0.85 * gr[i - d]
gr = nz(gr[64:], 0.8)
# 10 syrena
sir, sloop = looped([1, 0, .3, 0, .12], 8, rise=600)
# 11 przesterowany bas (prawie prostokat)
bas, bloop = looped([1, .5, .6, .35, .45, .25, .3, .18, .2, .12, .1, .07], 4, rise=20)   # MIKS2: wyrazniejszy bas
# 12 bęben
tt = t(0.3, R2); fq = 45 + 120 * np.exp(-tt / 0.025); ph = 2 * np.pi * np.cumsum(fq) / R2
kk = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.exp(-tt / 0.11) + 0.6 * np.sin(2 * np.pi * 1500 * tt) * np.exp(-tt / 0.004)   # MIKS2: klikniecie
kk[:50] += rng.standard_normal(50) * 0.5; kk = L16(nz(np.tanh(kk * 2.2)))

def build(preview):
    s = Song('Lucifero', 8, speed=6, tempo=90)
    DR = s.add_sample('drone', drone, R, loop=dloop, vol=64)
    DR2 = s.add_sample('drone2', drone, int(R * 1.006), loop=dloop, vol=64)
    PN = s.add_sample('piano', pno, R2)
    CL = s.add_sample('clang', cl, R4)
    TH = s.add_sample('thud', th, R4)
    ST = s.add_sample('static', st, R2, loop=(0, len(st)))
    EE = s.add_sample('eerie', eer, R, loop=eloop)
    BG = s.add_sample('pipe', bg, R2)
    GR = s.add_sample('grind', gr, R2, loop=(0, len(gr)))
    SI = s.add_sample('siren', sir, R, loop=sloop)
    BA = s.add_sample('bass', bas, R, loop=bloop)
    KK = s.add_sample('kick', kk, R2)
    P = [s.new_pattern(64) for _ in range(6)]
    X = 24; D = 4; E = 5; F = 6; H = 8; T = 20; B = 2
    pan = [0x50, 0xB0, 0x70, 0xD0, 0x80, 0x80, 0x30, 0xC0]
    for ch in range(8): s.put(P[0], 0, ch, cmd=X, val=pan[ch])
    # --- MGLA ---
    s.put(P[0], 0, 0, n('A-2'), DR, 17); s.put(P[0], 0, 1, n('A-2'), DR2, 17)   # MIKS: poglos glosniej
    for r, v in ((8, 27), (16, 37), (24, 44)):
        s.put(P[0], r, 0, vol=v); s.put(P[0], r, 1, vol=v)
    for p, mot in ((P[0], [(8, 'A-4', 40), (20, 'C-5', 34), (28, 'B-4', 30), (44, 'E-4', 36), (52, 'F-4', 30)]),
                   (P[1], [(4, 'A-4', 38), (10, 'A#4', 34), (22, 'E-5', 30), (34, 'D#5', 32), (46, 'C-5', 30), (58, 'B-4', 26)]),
                   (P[2], [(0, 'G-4', 36), (6, 'A#4', 32), (16, 'C#5', 34), (32, 'A-4', 30), (40, 'A#4', 28), (48, 'A-4', 24)]),
                   (P[3], [(16, 'E-4', 30), (40, 'F-4', 28)])):
        for r, nt, v in mot: s.put(p, r, 2, n(nt), PN, min(64, v * 7 // 4))   # MIKS: melodia glosniej
    for p, r, nt, v in ((P[0], 36, 'C-4', 22), (P[1], 50, 'F#3', 20), (P[2], 12, 'C-4', 24), (P[2], 44, 'G#3', 20), (P[3], 28, 'C-4', 18)):
        s.put(p, r, 3, n(nt), CL, min(64, v * 3 // 2))
    for p, r in ((P[1], 0), (P[3], 0), (P[3], 40)): s.put(p, r, 4, n('C-5'), TH, 60)
    for p, swell in ((P[1], [(16, 8), (20, 20), (24, 28), (28, 14), (32, None)]),
                     (P[3], [(24, 8), (30, 20), (36, 34), (44, 45), (52, 25), (56, None)])):
        for i, (r, v) in enumerate(swell):
            if v is None: s.put(p, r, 5, CUT)
            elif i == 0: s.put(p, r, 5, n('C-5'), ST, v)
            else: s.put(p, r, 5, vol=v)
    s.put(P[2], 0, 0, n('A#2'), DR, 41); s.put(P[2], 0, 1, n('A#2'), DR2, 41)
    s.put(P[3], 0, 0, n('A-2'), DR, 41); s.put(P[3], 0, 1, n('A-2'), DR2, 41)
    for r, v in ((48, 31), (56, 20)): s.put(P[3], r, 0, vol=v); s.put(P[3], r, 1, vol=v)
    s.put(P[2], 24, 6, n('E-6'), EE, 28, H, 0x34)
    for r in range(25, 48): s.put(P[2], r, 6, cmd=H, val=0x34)
    s.put(P[2], 48, 6, CUT)
    # --- RDZA (przemiana) ---
    for k, p in enumerate((P[4], P[5])):
        s.put(p, 0, 0, cmd=T, val=112)
        s.put(p, 0, 5, CUT); s.put(p, 0, 6, CUT)
        if k == 0:
            s.put(p, 0, 2, CUT); s.put(p, 0, 3, CUT); s.put(p, 0, 4, CUT)
        for r in (0, 3, 8, 14, 16, 19, 24, 30, 32, 35, 40, 46, 48, 51, 56, 62):
            s.put(p, r, 0, n('A-1') if (r // 16) % 2 == 0 else n('A#1'), BA, 46)
            if r + 2 < 64: s.put(p, r + 2, 0, CUT)
        hits = (0, 6, 10, 16, 22, 26, 32, 38, 42, 48, 54, 58) if k == 0 else (2, 6, 12, 18, 20, 26, 34, 38, 44, 50, 52, 58)
        for i, r in enumerate(hits): s.put(p, r, 1, n(('C-5', 'A#4', 'F#4', 'C#5')[i % 4]), BG, 60)
        for r, v in ((0, 60), (16, 58), (28, 40), (32, 60), (48, 58), (60, 40)): s.put(p, r, 2, n('C-5'), KK, v)
        s.put(p, 0, 3, n('C-4'), GR, 32)
        for r in range(1, 64): s.put(p, r, 3, cmd=(F if (r // 16) % 2 == 0 else E), val=0x05)
        s.put(p, 0, 4, n('A-4' if k == 0 else 'E-5'), SI, 34)
        for r in range(1, 64): s.put(p, r, 4, cmd=(F if r < 32 else E), val=0x03)
        for r in (8, 24, 40, 56): s.put(p, r, 5, n('C-5'), ST, 30); s.put(p, r + 2, 5, CUT)
        for r, a, b in ((12, 'A-3', 'A#3'), (44, 'D#4', 'E-4')):
            s.put(p, r, 6, n(a), PN, 62); s.put(p, r, 7, n(b), PN, 58)
    if preview:
        s.orders = [P[0], P[1], P[2], P[3], P[4], P[5], P[4], P[5]]
    else:   # gra: petla mgly (0-3) i osobna petla rdzy (od pozycji 4)
        s.put(P[3], 63, 7, cmd=B, val=0); s.put(P[5], 63, 7, cmd=B, val=4)
        s.orders = [P[0], P[1], P[2], P[3], P[4], P[5]]
    return s
if __name__ == '__main__':
    build(True).save('lucifero_preview.it')
    build(False).save('music/lucifero.it')
    tot = sum(len(x[1]) for x in build(False).samples)
    print('samples total bytes (8-bit):', tot)
