# Grafiki burzy w ostatniej walce: deszcz (warstwa BG3, 2 bity na piksel) i pioruny
# (warstwa boiska, 4 bity na piksel). Zapis wprost w formacie kafelkow SNES-a.
import random

def tile2bpp(px):          # px[8][8] z wartosciami 0..3
    out = bytearray()
    for r in range(8):
        b0 = b1 = 0
        for c in range(8):
            v = px[r][c]
            b0 |= (v & 1) << (7 - c)
            b1 |= ((v >> 1) & 1) << (7 - c)
        out += bytes([b0, b1])
    return out

def tile4bpp(px):          # px[8][8] z wartosciami 0..15
    lo = bytearray(); hi = bytearray()
    for r in range(8):
        b = [0, 0, 0, 0]
        for c in range(8):
            v = px[r][c]
            for k in range(4):
                b[k] |= ((v >> k) & 1) << (7 - c)
        lo += bytes([b[0], b[1]]); hi += bytes([b[2], b[3]])
    return lo + hi

# --- deszcz: kafelek 0 pusty, 1..4 smugi (cienkie, ukosne: w dol i lekko w lewo) ---
tiles = [tile2bpp([[0] * 8 for _ in range(8)])]
rng = random.Random(7)
for v in range(4):
    px = [[0] * 8 for _ in range(8)]
    x0 = 5 + v % 3 - (v // 3)
    y0 = v % 2
    length = 5 + v % 2
    for i in range(length):
        x = x0 - i // 2; y = y0 + i
        if 0 <= x < 8 and 0 <= y < 8:
            px[y][x] = 2 if i >= length - 2 else 1   # jasniejszy koniec kropli
    tiles.append(tile2bpp(px))
open('rain.til', 'wb').write(b''.join(tiles))
# mapa 32x32: ok. 28% pol ze smuga; paleta BG3 nr 7 (kolory 28-31), priorytet = przed sprite'ami
m = bytearray()
for y in range(32):
    for x in range(32):
        t = rng.randint(1, 4) if rng.random() < 0.28 else 0
        e = t | (7 << 10) | (1 << 13)
        m += bytes([e & 0xFF, e >> 8])
open('rain.map', 'wb').write(m)

# --- pioruny: 3 ksztalty po 16 x 64 px (2 x 8 kafelkow); kolor 4 = rdzen, 3 = poswiata ---
bolts = bytearray()
for s in range(3):
    W, H = 16, 64
    img = [[0] * W for _ in range(H)]
    r = random.Random(100 + s)
    x = 8.0
    pts = []
    for y in range(H):
        if y % 6 == 0:
            x += r.choice([-3, -2, 2, 3])
            x = max(3, min(12, x))
        pts.append((int(x), y))
    for (px, py) in pts:
        for dx in (-1, 1):
            if 0 <= px + dx < W: img[py][px + dx] = max(img[py][px + dx], 3)
        img[py][px] = 4
    # krotkie odgalezienie
    by = 20 + s * 9; bx = pts[by][0]
    for i in range(10):
        xx = bx + (i // 2) * (1 if s % 2 else -1); yy = by + i
        if 0 <= xx < W and yy < H:
            img[yy][xx] = 4
    for ty in range(8):
        for tx in range(2):
            bolts += tile4bpp([[img[ty * 8 + r_][tx * 8 + c] for c in range(8)] for r_ in range(8)])
open('bolt.til', 'wb').write(bolts)
print('rain.til', len(b''.join(tiles)), 'B, rain.map', len(m), 'B, bolt.til', len(bolts), 'B')
