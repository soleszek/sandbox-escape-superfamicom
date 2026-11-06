# RUDEN: ciezki marsz kawalerii - kotly, werbel, toporne ostinato tuby, rogi w kwintach
import numpy as np, sys
sys.path.insert(0, '/home/claude/mus')
from itwriter import Song, n, CUT
R = 16744                      # 64 probki na okres przy C-5 (261.6 Hz)
f0 = R / 64.0
rng = np.random.default_rng(3)
def t(sec, rate=R): return np.arange(int(sec * rate)) / rate
def L16(x): return x[:len(x) // 16 * 16]
# 1 kotly (graja 2 oktawy nizej, wiec probka jest "4x szybsza")
tt = t(0.22); glide = f0 * (1 + 0.08 * np.exp(-tt / 0.01))
timp = np.sin(2 * np.pi * np.cumsum(glide) / R) * np.exp(-tt / 0.07) + 0.25 * np.sin(4 * np.pi * np.cumsum(glide) / R) * np.exp(-tt / 0.03)
timp[:160] += rng.standard_normal(160) * np.linspace(0.6, 0, 160)
timp = L16(timp / np.max(np.abs(timp)) * 0.95)
# 2 werbel
tt = t(0.19); sn = rng.standard_normal(len(tt)) * np.exp(-tt / 0.045) + 0.5 * np.sin(2 * np.pi * 196 * tt) * np.exp(-tt / 0.03)
sn = np.convolve(sn, [0.5, 0.5], mode='same'); sn = L16(sn / np.max(np.abs(sn)) * 0.9)
# 3 tuba: jasny, chropawy dzwiek blaszany; 1024 probki ataku + petla 256 (4 okresy)
def periodic(amps, cycles, phase=None):
    x = np.arange(64 * cycles); w = np.zeros(len(x))
    for k, a in enumerate(amps, 1): w += a * np.sin(2 * np.pi * k * x / 64 + (0 if phase is None else phase[k - 1]))
    return w / np.max(np.abs(w))
tuba_loop = periodic([1 / k ** 1.25 for k in range(1, 13)], 4)
att = np.concatenate([tuba_loop] * 4) * np.linspace(1.25, 1.0, 1024)
tuba = np.concatenate([att * np.minimum(1, np.arange(1024) / 60), tuba_loop]) * 0.8
# 4 rog: cieplejszy, mniej harmonicznych
horn_loop = periodic([1, .55, .35, .2, .12, .07], 4)
horn = np.concatenate([np.concatenate([horn_loop] * 2) * np.minimum(1, np.arange(512) / 120), horn_loop]) * 0.75
# 5 talerz (8372 Hz)
R2 = R // 2; tt = t(0.95, R2)
cr = rng.standard_normal(len(tt)); cr = cr - np.convolve(cr, np.ones(3) / 3, mode='same')
cr = L16(cr / np.max(np.abs(cr)) * np.exp(-tt / 0.3) * 0.7)

s = Song('Ruden March', 7, speed=6, tempo=112)
TIMP = s.add_sample('timpani', timp, R)
SNARE = s.add_sample('snare', sn, R)
TUBA = s.add_sample('tuba', tuba, R, loop=(1024, 1280))
HORN = s.add_sample('horn', horn, R, loop=(512, 768))
CRASH = s.add_sample('crash', cr, R2)

def drums(p, bars=4, fill_last=False, roll=False):
    for b in range(bars):
        r = b * 16
        s.put(p, r + 0, 0, n('D-3'), TIMP, 64); s.put(p, r + 8, 0, n('A-2'), TIMP, 56)
        for row, v in ((0, 56), (4, 38), (6, 34), (7, 34), (8, 56), (12, 38), (14, 34), (15, 44)):
            s.put(p, r + row, 1, n('C-5'), SNARE, v)
    if fill_last:
        r = (bars - 1) * 16
        for row, v in ((6, 50), (12, 54), (14, 58)): s.put(p, r + row, 0, n('D-3'), TIMP, v)
    if roll:   # narastajacy werbel i kotly przed powrotem tematu
        r = (bars - 1) * 16
        for row in range(8, 16):
            s.put(p, r + row, 1, n('C-5'), SNARE, 30 + row * 2)
            if row % 2 == 0: s.put(p, r + row, 0, n('A-2'), TIMP, 40 + row * 2)

def tuba_bar(p, bar, notes):   # notes: [(row, note, len)]
    for row, nt, ln in notes:
        s.put(p, bar * 16 + row, 2, n(nt), TUBA, 60)
        if bar * 16 + row + ln < 64: s.put(p, bar * 16 + row + ln, 2, CUT)

def melody(p, seq, ch=3, vol=52, start=0, shift=0, smp=None):
    row = start
    for nt, ln in seq:
        if nt != '-':
            s.put(p, row, ch, n(nt) + shift, smp or HORN, vol)
            if ln > 1 and row + ln - 1 < 64: s.put(p, row + ln - 1, ch, CUT)
        row += ln

ost_d = [(0, 'D-4', 3), (6, 'D-4', 2), (8, 'F-4', 3), (12, 'E-4', 2), (14, 'C-4', 2)]
ost_d2 = [(0, 'D-4', 3), (6, 'D-4', 2), (8, 'A-3', 3), (12, 'C-4', 2), (14, 'D-4', 2)]
ost_g = [(0, 'G-3', 3), (6, 'G-3', 2), (8, 'A#3', 3), (12, 'A-3', 2), (14, 'F-3', 2)]
ost_a = [(0, 'A-3', 3), (6, 'A-3', 2), (8, 'C#4', 3), (12, 'E-4', 2), (14, 'A-3', 2)]

# P0: wstep - same bebny
p0 = s.new_pattern(); drums(p0, fill_last=True)
s.put(p0, 0, 6, cmd=1, val=6); s.put(p0, 0, 5, n('C-5'), CRASH, 44, cmd=20, val=112)
# P1: temat
p1 = s.new_pattern(); drums(p1)
for b, o in enumerate((ost_d, ost_d2, ost_d, ost_d2)): tuba_bar(p1, b, o)
mel_a = [('D-5', 8), ('A-5', 8), ('G-5', 6), ('F-5', 2), ('E-5', 8), ('F-5', 6), ('E-5', 2), ('D-5', 4), ('C-5', 4), ('D-5', 16)]
melody(p1, mel_a); melody(p1, mel_a, ch=4, vol=30, shift=-7)
s.put(p1, 0, 5, n('C-5'), CRASH, 40)
# P2: wariacja tematu
p2 = s.new_pattern(); drums(p2, fill_last=True)
for b, o in enumerate((ost_d, ost_d2, ost_d, ost_d2)): tuba_bar(p2, b, o)
mel_a2 = [('D-5', 8), ('A-5', 8), ('A#5', 6), ('A-5', 2), ('G-5', 8), ('A-5', 6), ('G-5', 2), ('F-5', 4), ('E-5', 4), ('D-5', 8), ('A-4', 8)]
melody(p2, mel_a2); melody(p2, mel_a2, ch=4, vol=30, shift=-7)
s.put(p2, 32, 5, n('C-5'), CRASH, 36)
# P3: czesc srodkowa (g-moll -> A-dur)
p3 = s.new_pattern(); drums(p3, roll=True)
for b, o in enumerate((ost_g, ost_g, ost_a, ost_a)): tuba_bar(p3, b, o)
mel_b = [('A#5', 8), ('A-5', 8), ('G-5', 8), ('D-5', 8), ('E-5', 8), ('C#5', 8), ('A-5', 16)]
melody(p3, mel_b); melody(p3, mel_b, ch=4, vol=30, shift=-7)
s.put(p3, 0, 5, n('C-5'), CRASH, 40); s.put(p3, 32, 5, n('C-5'), CRASH, 40)
# P4: wariacja z powrotem do tematu (petla)
p4 = s.new_pattern(); drums(p4, fill_last=True)
for b, o in enumerate((ost_d, ost_d2, ost_d, ost_d2)): tuba_bar(p4, b, o)
melody(p4, mel_a2); melody(p4, mel_a2, ch=4, vol=30, shift=-7)
s.put(p4, 63, 6, cmd=2, val=1)   # B01: wroc do tematu
s.orders = [p0, p1, p2, p3, p1, p4]
size = s.save('/home/claude/mus/out/ruden.it')
print('ruden.it', size, 'bytes')
