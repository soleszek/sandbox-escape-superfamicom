# Ekran tytulowy Sandbox Escape: logo i blyskawice;
# awatary nowych postaci: Robocik-dzojstik (JOYBOT) i AI Agent.
import numpy as np, struct, colorsys
from PIL import Image, ImageDraw
def tile2bpp(px):
    out = bytearray()
    for r in range(8):
        b0 = b1 = 0
        for c in range(8):
            v = int(px[r][c]); b0 |= (v & 1) << (7 - c); b1 |= ((v >> 1) & 1) << (7 - c)
        out += bytes([b0, b1])
    return bytes(out)
def tile4bpp(px):
    lo = bytearray(); hi = bytearray()
    for r in range(8):
        b = [0, 0, 0, 0]
        for c in range(8):
            v = int(px[r][c])
            for k in range(4): b[k] |= ((v >> k) & 1) << (7 - c)
        lo += bytes([b[0], b[1]]); hi += bytes([b[2], b[3]])
    return bytes(lo + hi)
def bgr15(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)
def save_p(a, pal, name):
    im = Image.fromarray(a.astype(np.uint8), 'P'); flat = []
    for c in pal: flat += list(c)
    flat += [0] * (768 - len(flat)); im.putpalette(flat); im.save(name)

# ---------- logo 256x48 ----------
F = {'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
     'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
     'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
     'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
     'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
     'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
     'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
     'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
     'C': ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
     'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"]}
LPAL = [(0, 0, 0), (20, 20, 36), (232, 40, 48), (255, 128, 120), (248, 196, 32), (255, 240, 140),
        (40, 180, 72), (150, 240, 150), (48, 104, 232), (150, 184, 255)]
L = np.zeros((48, 256), int)
CW, CH = 4, 3   # komorka litery: 5x7 komorek -> 20x21 px
def word(w, y0, col0):
    width = len(w) * (5 * CW + 3) - 3; x0 = (256 - width) // 2
    for i, ch in enumerate(w):
        g = F[ch]; base = 2 + 2 * ((i + col0) % 4); x = x0 + i * (5 * CW + 3)
        m = np.zeros((7 * CH, 5 * CW), bool)
        for r in range(7):
            for c in range(5):
                if g[r][c] == '1': m[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW] = True
        for dy in (1, 2):   # cien
            for dx in (1, 2):
                ys, xs = np.nonzero(m); L[y0 + ys + dy, x + xs + dx] = np.where(L[y0 + ys + dy, x + xs + dx] == 0, 1, L[y0 + ys + dy, x + xs + dx])
        ys, xs = np.nonzero(m)
        L[y0 + ys, x + xs] = base
        for yy, xx in zip(ys, xs):   # jasna krawedz od gory i z lewej
            if yy == 0 or not m[yy - 1, xx] or xx == 0 or not m[yy, xx - 1]: L[y0 + yy, x + xx] = base + 1
word("SANDBOX", 1, 0); word("ESCAPE", 25, 2)
save_p(L, LPAL, 'logo.png')

# ---------- JOYBOT 32x32 ----------
JP = [(0, 0, 0), (16, 16, 24), (200, 40, 44), (255, 110, 100), (255, 200, 190), (250, 250, 250), (20, 20, 30),
      (90, 94, 110), (150, 156, 172), (60, 62, 76), (255, 210, 40), (60, 200, 255), (255, 150, 170)]
J = Image.new('P', (32, 32), 0); d = ImageDraw.Draw(J)
d.rounded_rectangle([3, 21, 28, 30], 3, fill=1); d.rounded_rectangle([4, 21, 27, 29], 3, fill=9)
d.rectangle([5, 22, 26, 23], fill=7)
d.ellipse([6, 24, 10, 28], fill=1); d.ellipse([7, 25, 10, 28], fill=10)      # przycisk zolty
d.ellipse([21, 24, 25, 28], fill=1); d.ellipse([22, 25, 25, 28], fill=11)    # przycisk niebieski
d.rectangle([13, 14, 18, 22], fill=1); d.rectangle([14, 14, 17, 22], fill=8); d.line([(14, 14), (14, 22)], fill=7)
d.ellipse([5, 0, 26, 18], fill=1); d.ellipse([6, 1, 25, 17], fill=2)          # glowa-kulka
d.ellipse([8, 2, 18, 9], fill=3); d.ellipse([9, 3, 12, 5], fill=4)            # blask
for ex in (10, 17):   # duze oczy jak u Muggy'ego
    d.ellipse([ex - 1, 6, ex + 4, 12], fill=5); d.ellipse([ex + 1, 8, ex + 3, 11], fill=6); d.point([(ex + 2, 8)], fill=5)
d.point([(9, 13), (10, 13), (21, 13), (22, 13)], fill=12)                       # rumience
d.line([(13, 14), (15, 15), (16, 15), (18, 14)], fill=6)                       # usmiech
save_p(np.array(J), JP, 'joybot32.png')

# ---------- AI AGENT 32x32 (zastepuje robota) ----------
AP = [(0, 0, 0), (12, 14, 20), (44, 50, 66), (86, 96, 120), (8, 10, 14), (70, 210, 255), (210, 250, 255),
      (60, 220, 110), (150, 255, 180), (130, 140, 160), (30, 34, 46)]
A = Image.new('P', (32, 32), 0); d = ImageDraw.Draw(A)
d.rectangle([12, 26, 19, 29], fill=1); d.rectangle([13, 26, 18, 28], fill=10); d.rectangle([8, 29, 23, 31], fill=1); d.rectangle([9, 29, 22, 30], fill=2)
d.rounded_rectangle([1, 2, 30, 26], 5, fill=1); d.rounded_rectangle([2, 3, 29, 25], 4, fill=2)
d.line([(4, 3), (26, 3)], fill=3); d.line([(2, 6), (2, 21)], fill=3)
d.rounded_rectangle([5, 6, 26, 22], 2, fill=4)                                  # ekran
d.rectangle([8, 10, 13, 12], fill=5); d.rectangle([9, 11, 12, 11], fill=6)     # oczy: swiecace kreski
d.rectangle([18, 10, 23, 12], fill=5); d.rectangle([19, 11, 22, 11], fill=6)
d.line([(10, 16), (12, 17), (10, 18)], fill=7)                                  # znak zachety >_
d.rectangle([14, 18, 18, 18], fill=8)
d.point([(26, 4), (27, 4)], fill=8)                                             # dioda
save_p(np.array(A), AP, 'robot32.png')

# ---------- blyskawice (BG3, 2 bity): lewa paleta 1, prawa paleta 2 ----------
rng = np.random.default_rng(7); B = np.zeros((136, 256), int); P3 = np.zeros((17, 32), int)
def bolt(x0, pal):
    x = x0; pts = [(x, 0)]
    for y in range(8, 136, 8): x += rng.integers(-9, 10); pts.append((x, y))
    im = Image.new('L', (256, 136), 0); dd = ImageDraw.Draw(im)
    dd.line(pts, fill=2, width=3); dd.line(pts, fill=1, width=1)
    k = pts[6]; br = [k]; xx = k[0]
    for y in range(k[1] + 8, k[1] + 48, 8): xx += rng.integers(4, 12) * (1 if x0 < 128 else -1); br.append((xx, y))
    dd.line(br, fill=2, width=2); dd.line(br, fill=1, width=1)
    a = np.array(im); B[a > 0] = a[a > 0]
    P3[:, (0 if x0 < 128 else 16):(16 if x0 < 128 else 32)] = pal
bolt(30, 1); bolt(226, 2)
bt = [tile2bpp(np.zeros((8, 8)))]; bix = {bt[0]: 0}; bm = [0] * 1024
for ty in range(17):
    for tx in range(32):
        t = tile2bpp(B[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8])
        if t not in bix: bix[t] = len(bt); bt.append(t)
        bm[(1 + ty) * 32 + tx] = bix[t] | (int(P3[ty, tx]) << 10)
open('title_bolt.til', 'wb').write(b''.join(bt)); open('title_bolt.map', 'wb').write(b''.join(struct.pack('<H', e) for e in bm))
print('bolt tiles', len(bt))
