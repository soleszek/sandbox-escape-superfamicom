# INTRO: dynamiczna, lekko dramatyczna muzyka (d-moll, 131 BPM) - wlasna kompozycja.
# Takty po 16 wierszy (1,83 s). Odcinki dopasowane do intro:
#   0-3 scena 1 (puls, bicie serca), 4-6 narastanie (uderzenia, krzyk), 7-10 przebitki,
#   11..E-3 czat (motyw prowadzacy od 5. taktu czatu: 8 taktow motywu, 4 takty przerwy, ...),
#   E-2, E-1 narastanie do "Enough!" (poczatek taktu E), E: podtrzymanie (petla).
# E (takt "Enough!") podaje tools/intro/build_intro.py (plik music_bars.txt) - zalezy od dlugosci czatu.
# Ekran startowy gra ten sam utwor od pozycji TITLE_MUS_POS (plik intro_music.h): od poczatku do konca
# czatu, potem w petli odcinek czatu.
# Uruchom z katalogu projektu:  python3 tools/make_intro_music.py music/intro.it 41
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from itwriter import Song, n, CUT

R = 16744; R2 = R // 2; R4 = R // 4
rng = np.random.default_rng(131)
B_, D_, H_, T_ = 2, 4, 8, 20          # efekty IT: B skok, D zmiana glosnosci, H vibrato, T tempo


def t(sec, rate): return np.arange(int(sec * rate)) / rate
def L16(x): return x[:max(16, len(x) // 16 * 16)]
def nz(x, g=0.92): return x / (np.max(np.abs(x)) + 1e-9) * g


def periodic(amps, cycles=4, per=64, phases=None):
    x = np.arange(per * cycles); w = np.zeros(len(x))
    for k, a in enumerate(amps, 1):
        w += a * np.sin(2 * np.pi * k * x / per + (phases[k - 1] if phases else 0))
    return w / np.max(np.abs(w))


def looped(amps, att_cycles=8, per=64, rise=200):
    lp = periodic(amps, 4, per)
    att = np.concatenate([lp] * (att_cycles // 4)) * np.minimum(1, np.arange(per * att_cycles) / rise)
    return np.concatenate([att, lp]) * 0.85, (len(att), len(att) + len(lp))


# ---------------------------------------------------------------- probki
saw = [1 / k for k in range(1, 15)]
bass, bloop = looped([1, .7, .55, .45, .38, .3, .25, .2, .16, .12, .1, .08], 4, rise=24)
pad, ploop = looped([1, .55, .4, .3, .22, .16, .12, .09, .07, .05], 16, rise=900)
lead, lloop = looped([1, .75, .55, .5, .38, .3, .24, .18, .14, .1, .08, .06], 8, rise=60)
# pianino / pizzicato do arpeggio (R2: 32 probki na okres C-5)
tt = t(0.55, R2); f = R2 / 32; pno = np.zeros(len(tt))
for k in range(1, 9):
    fk = f * k * np.sqrt(1 + 0.0003 * k * k)
    pno += (1 / k ** 1.1) * np.sin(2 * np.pi * fk * tt) * np.exp(-tt / (0.5 / k ** 0.7))
pno[:24] += rng.standard_normal(24) * 0.2
pno = L16(nz(pno) * np.minimum(1, np.arange(len(tt)) / 8))
# smyczki staccato (akcent)
tt = t(0.35, R2); stab = np.zeros(len(tt))
for k in range(1, 12):
    stab += (1 / k) * np.sin(2 * np.pi * f * k * tt + k) * np.exp(-tt / 0.12)
stab = L16(nz(stab * np.minimum(1, np.arange(len(tt)) / 30)))
# beben
tt = t(0.32, R2); fq = 48 + 130 * np.exp(-tt / 0.022); ph = 2 * np.pi * np.cumsum(fq) / R2
kick = (np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * np.exp(-tt / 0.12)
kick += 0.5 * np.sin(2 * np.pi * 1400 * tt) * np.exp(-tt / 0.004)
kick[:40] += rng.standard_normal(40) * 0.4
kick = L16(nz(np.tanh(kick * 2.0)))
# werbel
tt = t(0.26, R2)
sn = rng.standard_normal(len(tt)) * np.exp(-tt / 0.07) * 0.9
sn += (np.sin(2 * np.pi * 190 * tt) + 0.5 * np.sin(2 * np.pi * 330 * tt)) * np.exp(-tt / 0.05)
sn = L16(nz(np.tanh(sn * 1.6)))
# talerz zamkniety (hi-hat)
tt = t(0.08, R); hh = rng.standard_normal(len(tt))
hh = np.diff(np.concatenate([[0], hh])) * np.exp(-tt / 0.018)
hh = L16(nz(hh))
# kociol (tom)
tt = t(0.4, R2); fq = 90 + 60 * np.exp(-tt / 0.05); ph = 2 * np.pi * np.cumsum(fq) / R2
tom = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * np.exp(-tt / 0.16) + rng.standard_normal(len(tt)) * np.exp(-tt / 0.02) * 0.4
tom = L16(nz(np.tanh(tom * 1.5)))
# niskie uderzenie (poczatek odcinka)
tt = t(1.2, R4); fq = 34 + 60 * np.exp(-tt / 0.12); ph = 2 * np.pi * np.cumsum(fq) / R4
imp = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.15 * np.sin(4 * ph)) * np.exp(-tt / 0.45)
imp += rng.standard_normal(len(tt)) * np.exp(-tt / 0.05) * 0.6
imp = L16(nz(np.tanh(imp * 1.8)))

s = Song('Intro', 8, speed=6, tempo=131)
BA = s.add_sample('bass', bass, R, loop=bloop)
PD = s.add_sample('pad', pad, R, loop=ploop)
LD = s.add_sample('lead', lead, R, loop=lloop)
PN = s.add_sample('piano', pno, R2)
ST = s.add_sample('stab', stab, R2)
KK = s.add_sample('kick', kick, R2)
SN = s.add_sample('snare', sn, R2)
HH = s.add_sample('hat', hh, R)
TM = s.add_sample('tom', tom, R2)
IM = s.add_sample('impact', imp, R4)
size = sum(len(x) for x in (bass, pad, lead, pno, stab, kick, sn, hh, tom, imp))
print('probki: %d probek, ok. %d B w formacie BRR' % (size, size * 9 // 16))

CH_BASS, CH_PAD1, CH_PAD2, CH_ARP, CH_LEAD, CH_KICK, CH_SN, CH_HAT = range(8)
EN = int(sys.argv[2]) if len(sys.argv) > 2 else 41   # takt, na ktorego poczatku pada "Enough!"
EXT = int(sys.argv[3]) if len(sys.argv) > 3 else 0   # wiersze dodane do taktu 10 (dluzsze przebitki)
L = EN - 13                                          # takty czatu (11 .. EN-3)
assert L >= 8 and L % 2 == 0
NB = EN + 1                                          # + takt podtrzymania
P = [s.new_pattern(16 + (EXT if b == 10 else 0)) for b in range(NB)]
s.orders = list(range(NB))

CHORD = {'Dm': ('D', ['D', 'F', 'A']), 'Bb': ('A#', ['A#', 'D', 'F']), 'Gm': ('G', ['G', 'A#', 'D']),
         'A': ('A', ['A', 'C#', 'E']), 'C': ('C', ['C', 'E', 'G'])}
chat_prog = []
for j in range(L):
    if L % 4 == 0 and j >= L - 4:
        chat_prog.append(['Dm', 'Bb', 'Dm', 'Bb'][j - (L - 4)])
    else:
        chat_prog.append(['Dm', 'Bb', 'Gm', 'A'][j % 4])
prog = ['Dm'] * 4 + ['Dm', 'Bb', 'A'] + ['Dm', 'Gm', 'Dm', 'A'] + chat_prog + ['Gm', 'A'] + ['A']


def nt(name, octv):
    return n('%s%s%d' % (name, '-' if len(name) == 1 else '', octv))


def chord_notes(c, octv):
    root, tones = CHORD[c]
    out, last = [], -1
    for tn in tones:
        v = nt(tn, octv)
        while v <= last:
            v += 12
        out.append(v)
        last = v
    return out


MOTIF = {14: [(0, 'A-5', 4), (4, 'D-6', 4), (8, 'F-6', 6), (14, 'E-6', 2)],
         15: [(0, 'D-6', 4), (4, 'C-6', 2), (6, 'A#5', 2), (8, 'A-5', 8)],
         16: [(0, 'G-5', 4), (4, 'A#5', 4), (8, 'D-6', 6), (14, 'C-6', 2)],
         17: [(0, 'C#6', 8), (8, 'E-6', 4), (12, 'A-6', 4)],
         18: [(0, 'A-6', 6), (6, 'G-6', 2), (8, 'F-6', 4), (12, 'E-6', 4)],
         19: [(0, 'F-6', 4), (4, 'D-6', 4), (8, 'A#5', 4), (12, 'D-6', 4)],
         20: [(0, 'G-6', 8), (8, 'A#6', 8)],
         21: [(0, 'A-6', 16)]}


def lead_on(j):          # takt czatu j: motyw gra? (pierwsze 4 takty bez, potem 8 z motywem / 4 przerwy)
    if j < 4:
        return False
    return (j - 4) % 12 < 8 or j >= L - 4


# frazy motywu pod akordy: d-moll na zmiane 14/18, B-dur 15/19, g-moll 16, A-dur 17
LEADM, cnt = {}, {'Dm': 0, 'Bb': 0}
for j in range(L):
    if not lead_on(j):
        continue
    c = chat_prog[j]
    if j >= L - 2:
        m = 18 if c == 'Dm' else 19
    elif c in cnt:
        m = (14, 18)[cnt[c] % 2] if c == 'Dm' else (15, 19)[cnt[c] % 2]
        cnt[c] += 1
    else:
        m = 16 if c == 'Gm' else 17
    LEADM[11 + j] = MOTIF[m]
LEADM[EN - 2] = MOTIF[20]
LEADM[EN - 1] = MOTIF[21]
lead_bars = sorted(LEADM)
block_start = [11 + j for j in range(L) if lead_on(j) != (lead_on(j - 1) if j else False)]
IMPACT = [4, 7, 11] + block_start
FILLS = [6, 10] + [b - 1 for b in block_start if b - 1 > 10]

for b in range(NB):
    p = P[b]
    c = prog[min(b, len(prog) - 1)]
    root = CHORD[c][0]
    sec = 0 if b < 4 else 1 if b < 7 else 2 if b < 11 else 3 if b < EN - 2 else 4 if b < EN else 5
    R = 16 + (EXT if b == 10 else 0)   # dlugosc taktu w wierszach (takt 10 moze byc wydluzony)
    if b == 0:
        s.put(p, 0, CH_HAT, cmd=T_, val=131)
    # bas: osemki, oktawy na zmiane
    bv = [30, 38, 44, 48, 54, 48][sec]
    for r in range(0, R, 2):
        if sec == 0 and r % 4:
            continue
        s.put(p, r, CH_BASS, nt(root, 3 if (r // 2) % 2 == 0 else 4), BA, bv - (4 if r % 4 else 0))
    # podklad smyczkowy: kwinta / akord w dwoch glosach
    cn = chord_notes(c, 4)
    pv = [24, 28, 30, 26, 32, 30][sec]
    s.put(p, 0, CH_PAD1, cn[0] + 12, PD, pv)
    s.put(p, 0, CH_PAD2, cn[2] + 12 if sec == 0 else cn[1] + 12, PD, pv - 4)
    # arpeggio: cwiercnuty na poczatku, potem szesnastki
    arp = chord_notes(c, 5) + [chord_notes(c, 5)[0] + 12]
    seq = arp + arp[2:0:-1] + arp[:1]
    step = 4 if sec == 0 else 2 if sec == 1 else 1
    av = [22, 26, 24, 22, 28, 0][sec]
    if av:
        for r in range(0, R, step):
            s.put(p, r, CH_ARP, seq[(r // step) % len(seq)] + (12 if sec == 4 and b == EN - 1 and r >= 8 else 0), PN,
                  av + (r % 4 == 0) * 6)
    # perkusja
    if sec == 0:            # bicie serca
        for r, v in ((0, 50), (3, 36), (8, 50), (11, 36)):
            s.put(p, r, CH_KICK, n('C-5'), KK, v)
        if b >= 2:
            for r in range(2, 16, 4):
                s.put(p, r, CH_HAT, n('C-5'), HH, 18 + b * 3)
    elif sec in (1, 2, 3, 4):
        kicks = (0, 8) if sec == 1 else (0, 6, 8, 14) if sec in (2, 4) else (0, 7, 8, 10)
        for r in [k + o for o in range(0, R, 16) for k in kicks if k + o < R]:
            s.put(p, r, CH_KICK, n('C-5'), KK, 54)
        if sec != 1 or b >= 5:
            for r in [k + o for o in range(0, R, 16) for k in (4, 12) if k + o < R]:
                s.put(p, r, CH_SN, n('C-5'), SN, 46)
        for r in range(0, R, 2 if sec == 1 else 1):
            s.put(p, r, CH_HAT, n('C-5'), HH, (30 if r % 2 == 0 else 20) + (6 if sec == 4 else 0))
    if b in IMPACT:                 # niskie uderzenie na poczatku odcinka
        s.put(p, 0, CH_KICK, n('C-5'), IM, 62)
    if b in FILLS:                  # przejscie na kotlach
        for r, nn_ in ((R - 4, 'C-5'), (R - 3, 'A-4'), (R - 2, 'F-4'), (R - 1, 'D-4')):
            s.put(p, r, CH_SN, n(nn_), TM, 48)
    if sec in (2, 3) and b % 2 == 0:   # akcenty smyczkow
        s.put(p, 0, CH_PAD2 if b in LEADM else CH_LEAD, cn[0] + 24, ST, 40)
    elif sec == 3 and b not in LEADM and (b - 1) in LEADM:
        s.put(p, 0, CH_LEAD, CUT)   # przerwa w motywie: wyciszenie trzymanej nuty
    # motyw prowadzacy (glosnosc rosnie powoli do konca)
    if b in LEADM:
        k = lead_bars.index(b)
        vol = 40 + int(14 * k / max(1, len(lead_bars) - 1))
        for r, nn_, ln in LEADM[b]:
            s.put(p, r, CH_LEAD, n(nn_), LD, vol)
            if ln >= 6:
                for rr in range(r + 2, r + ln):
                    s.put(p, rr, CH_LEAD, cmd=H_, val=0x44)
    # narastanie: werbel szesnastkami coraz glosniej
    if sec == 4:
        for r in range(16):
            v = 18 + int(((b - (EN - 2)) * 16 + r) / 32 * 40)
            s.put(p, r, CH_SN, n('C-5'), SN, min(60, v))
    if sec == 5:            # podtrzymanie: tylko akord i bas na A (petla)
        s.put(p, 0, CH_LEAD, CUT)
        s.put(p, 15, CH_HAT, cmd=B_, val=NB - 1)
# Wersja na ekran startowy (te same wzorce, osobne pozycje w kolejnosci): od poczatku do konca czatu,
# potem w petli czesc z czatu (od taktu 11) - bez narastania do "Enough!".
TITLE_POS = len(s.orders)
last = s.new_pattern(16)
s.patterns[last] = [[(c[:] if c else None) for c in row] for row in s.patterns[P[EN - 3]]]
s.put(last, 15, CH_PAD1, cmd=B_, val=TITLE_POS + 11)
s.orders += [P[b] for b in range(EN - 3)] + [last]
open('intro_music.h', 'w').write('// WYGENEROWANE przez tools/make_intro_music.py\n'
                                 '#define TITLE_MUS_POS %d   // ekran startowy: pozycja w module MOD_INTRO\n' % TITLE_POS)
out = sys.argv[1] if len(sys.argv) > 1 else 'music/intro.it'
print('takt "Enough!": %d, czat %d taktow, motyw w taktach %s' % (EN, L, lead_bars))
print('ekran startowy: od pozycji %d, petla od pozycji %d' % (TITLE_POS, TITLE_POS + 11))
print(out, s.save(out), 'B')
