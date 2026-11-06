# Tla aren: Ruden (gradient, kurz, ogry) i Malten (gradient, mgla). Zapis wprost w formatach SNES.
import numpy as np, struct
from PIL import Image, ImageDraw
rng = np.random.default_rng(21)

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

def layer_bg3(img, name, pal=7, row0=6):
    # img: 256 x (rows*8), wartosci 0..3; mapa 32x32 od wiersza row0, reszta pusta
    tiles = [tile2bpp(np.zeros((8, 8)))]; index = {tiles[0]: 0}
    m = [0] * (32 * 32)
    for ty in range(img.shape[0] // 8):
        for tx in range(32):
            t = tile2bpp(img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8])
            if t not in index: index[t] = len(tiles); tiles.append(t)
            m[(row0 + ty) * 32 + tx] = index[t] | (pal << 10)
    open(name + '.til', 'wb').write(b''.join(tiles))
    open(name + '.map', 'wb').write(b''.join(struct.pack('<H', e) for e in m))
    return len(tiles)

def smooth_noise(h, w, sx, sy, seed):
    r = np.random.default_rng(seed)
    g = r.random((h // sy + 3, w // sx + 3))
    ys = np.arange(h) / sy; xs = np.arange(w) / sx
    y0 = ys.astype(int); x0 = xs.astype(int); fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0 % (w // sx)]; b = g[y0][:, (x0 + 1) % (w // sx)]; c = g[y0 + 1][:, x0 % (w // sx)]; d = g[y0 + 1][:, (x0 + 1) % (w // sx)]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def dither(v, t1, t2):   # 0..1 -> 0/1/2 z szachownica (na kineskopie wyglada jak polprzezroczystosc)
    H, W = v.shape; chk = (np.add.outer(np.arange(H), np.arange(W)) % 2) == 0
    out = np.zeros((H, W), int)
    out[(v > t1) & chk] = 1
    out[v > t2] = 1
    out[(v > t2 + 0.08) & chk] = 2
    return out

H = 19 * 8   # wiersze 6..24 (boisko)
# --- Ruden: kurz (dwie oktawy szumu, powtarzalny w poziomie) ---
dust = 0.65 * smooth_noise(H, 256, 32, 16, 1) + 0.35 * smooth_noise(H, 256, 16, 8, 2)
print('ruden_dust tiles', layer_bg3(dither(dust, 0.58, 0.70), 'ruden_dust'))
# --- Malten: mgla (pasma rozciagniete w poziomie) ---
fog = 0.7 * smooth_noise(H, 256, 64, 12, 3) + 0.3 * smooth_noise(H, 256, 32, 6, 4)
print('malten_fog tiles', layer_bg3(dither(fog, 0.55, 0.68), 'malten_fog'))

# --- Ruden: ogry i trolle - rysowane w tools/make_ogres.py (sylwetki na szkielecie, swiecace oczy)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_ogres
print('ruden_crowd tiles', make_ogres.write_crowd())

# --- Waller: noc, mur z blankami i otworami, plamy swiatla pochodni (BG3: paleta 7 kamien, 6 oswietlony) ---
TORCH_X = (60, 108, 156, 204); TORCH_Y = 118; SLITS = ((84, 100), (180, 100))
W = np.zeros((H, 256), int); P = np.full((H, 256), 7, int)   # indeks koloru i paleta (dla kafelka)
top = 88 - 48   # gora muru (y=88) w ukladzie warstwy (od y=48)
for yy in range(H):
    y = yy + 48
    for x in range(256):
        if y < 80: continue
        if y < 88:   # blanki: 16 px zeba, 8 px przerwy
            if (x % 24) >= 16: continue
        # cegly 10x5 z przesunieciem co rzad
        row = (y - 80) // 5; off = 5 if row % 2 else 0
        mortar = ((y - 80) % 5 == 4) or ((x + off) % 10 == 9)
        if mortar: W[yy, x] = 1
        else:
            W[yy, x] = 3 if ((y - 80) % 5 == 0 and (x + off) % 10 < 8) else 2
        if y < 88 and (y - 80) == 0: W[yy, x] = 3
for sx, sy in SLITS:   # otwory strzelnicze: ciemne szczeliny
    for y in range(sy, sy + 14):
        for x in range(sx - 1, sx + 2):
            W[y - 48, x] = 1
    for x in range(sx - 3, sx + 4): W[sy + 6 - 48, x] = 1
lit_tiles = set()
for tx in TORCH_X:
    for ty in range((TORCH_Y - 30 - 48) // 8, (TORCH_Y + 30 - 48) // 8 + 1):
        for cx in range((tx - 30) // 8, (tx + 30) // 8 + 1):
            if 0 <= ty < H // 8 and 0 <= cx < 32: lit_tiles.add((ty, cx))
chk = (np.add.outer(np.arange(H), np.arange(256)) % 2) == 0
for (ty, cx) in lit_tiles:
    for yy in range(ty * 8, ty * 8 + 8):
        for x in range(cx * 8, cx * 8 + 8):
            if W[yy, x] == 0: continue
            dmin = min(((x - tx) ** 2 + (yy + 48 - TORCH_Y) ** 2) ** 0.5 for tx in TORCH_X)
            L = max(0.0, 1 - dmin / 30)
            v = W[yy, x]   # paleta 6: 1 zaprawa i 2 kamien jak w zwyklym murze, 3 cieple swiatlo
            if v == 1: nv = 1
            elif L > 0.5: nv = 3
            elif L > 0.2: nv = 3 if chk[yy, x] else 2
            else: nv = 2
            W[yy, x] = nv
    P[ty * 8:ty * 8 + 8, cx * 8:cx * 8 + 8] = 6
tiles = [tile2bpp(np.zeros((8, 8)))]; index = {tiles[0]: 0}; m = [0] * 1024
for ty in range(H // 8):
    for tx in range(32):
        t = tile2bpp(W[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8])
        if t not in index: index[t] = len(tiles); tiles.append(t)
        m[(6 + ty) * 32 + tx] = index[t] | (int(P[ty * 8, tx * 8]) << 10)
open('waller_wall.til', 'wb').write(b''.join(tiles)); open('waller_wall.map', 'wb').write(b''.join(struct.pack('<H', e) for e in m))
print('waller wall tiles', len(tiles))

# pochodnie - 8 klatek plomienia w tools/make_torches.py
import make_torches
print('torch tiles', make_torches.write_torches())

# nietoperz: lewa polowa 8x8 (prawa = odbicie), 2 klatki skrzydel; paleta sprite'ow 7: 1 cialo, 2 blona, 3 oczy
def bat(frame):
    a = np.zeros((8, 8), int)
    a[3:7, 6:8] = 1; a[2, 6] = 1           # cialo i ucho
    a[4, 7] = 3                              # oko (na krawedzi - po odbiciu para oczu)
    if frame == 0:   # skrzydla w gorze
        for x in range(0, 6): a[max(0, 3 - (6 - x) // 2), x] = 1; a[4, x] = 2 if x % 2 else 1
        a[1:4, 1:6] = np.where(a[1:4, 1:6] == 0, 2, a[1:4, 1:6]); a[0, 0] = 1
    else:            # skrzydla w dole
        for x in range(0, 6): a[4 + (6 - x) // 3, x] = 1
        a[4:6, 1:6] = np.where(a[4:6, 1:6] == 0, 2, a[4:6, 1:6]); a[7, 0] = 1
    return a
open('bat.til', 'wb').write(tile4bpp(bat(0)) + tile4bpp(bat(1)))
bp = np.hstack([np.hstack([bat(f), bat(f)[:, ::-1]]) for f in (0, 1)])
Image.fromarray((bp * 80).astype(np.uint8)).resize((256, 64), Image.NEAREST).save('/tmp/bat_preview.png')
wp = np.where((P == 6) & (W == 3), 7, W)
Image.fromarray((wp * 30).astype(np.uint8)).resize((768, 456), Image.NEAREST).save('/tmp/wall_preview.png')

# --- gradienty tla (HDMA: kolor 0 palety co 4 linie) ---
def grad(top, bot):
    out = bytearray([48, 0, 0, 0, 0])   # linie 0-47 (pasek u gory): czern
    for i in range(38):
        t = i / 37; r, g, b = [int(round((top[k] + (bot[k] - top[k]) * t) / 8)) for k in range(3)]
        c = r | (g << 5) | (b << 10)
        out += bytes([4, 0, 0, c & 0xFF, c >> 8])
    out += bytes([24, 0, 0, 0, 0, 0])    # reszta ekranu czarna, koniec tablicy
    return out
open('ruden_grad.bin', 'wb').write(grad((40, 12, 6), (125, 50, 14)))
open('malten_grad.bin', 'wb').write(grad((6, 6, 20), (26, 26, 64)))
open('waller_grad.bin', 'wb').write(grad((2, 2, 10), (22, 24, 60)))
print('ok')
