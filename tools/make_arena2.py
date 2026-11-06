# Tla aren strażnikow 4-9: Cyber-doppler, Changero, Chronos, Magneton, Telementor, Blinker.
# Warstwa BG3 (2 bity na piksel, za boiskiem), gradienty HDMA, tablice kolorow do cykli palet
# i kafelki sprite'ow. Zapis wprost w formatach SNES-a. Uruchom z katalogu projektu:
#   python tools/make_arena2.py [--preview KATALOG]
# Numery kolorow (CGRAM), kafelkow i sprite'ow musza sie zgadzac z superfamipong.c (sekcja ARENY 4-9).
import math, struct, sys
import numpy as np
from PIL import Image

H = 19 * 8              # wiersze 6..24 mapy BG3 = boisko (y = 48..199)
ROW0 = 6
CX, CY = 127.5, 75.5    # srodek boiska w ukladzie warstwy
PREVIEW = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None


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


def rgb15(c):
    r, g, b = (max(0, min(255, int(round(v)))) for v in c)
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def cols(lst):   # lista kolorow (r, g, b) albo 0 -> bajty CGRAM
    return b''.join(struct.pack('<H', rgb15(c) if isinstance(c, tuple) else c) for c in lst)


def save(name, data):
    open(name, 'wb').write(data)
    print(f'{name:22s} {len(data):5d} B')


def scale(c, k): return tuple(v * k for v in c)
def mix(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def bg3(name, idx, pal):
    """idx: H x 256 (0..3), pal: (H/8) x 32 - numery palet BG3. Kafelek 0 jest pusty.
    Kafelki odbite w poziomie/pionie sa zapisywane raz (bity odbicia w mapie)."""
    tiles = [tile2bpp(np.zeros((8, 8), int))]; index = {tiles[0]: 0}; m = [0] * 1024
    for ty in range(H // 8):
        for tx in range(32):
            blk = idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if not blk.any(): continue
            e = None
            for fl, b in ((0, blk), (0x4000, blk[:, ::-1]), (0x8000, blk[::-1, :]), (0xC000, blk[::-1, ::-1])):
                t = tile2bpp(b)
                if t in index: e = index[t] | fl; break
            if e is None:
                e = len(tiles); t = tile2bpp(blk); index[t] = e; tiles.append(t)
            m[(ROW0 + ty) * 32 + tx] = e | (int(pal[ty, tx]) << 10)
    assert len(tiles) <= 512, (name, len(tiles))
    save(name + '.til', b''.join(tiles))
    save(name + '.map', b''.join(struct.pack('<H', e) for e in m))
    print(f'  {name}: {len(tiles)} kafelkow')


def grad(top, bot):   # HDMA kanal 6: kolor 0 co 4 linie (format jak w make_arena.py)
    out = bytearray([48, 0, 0, 0, 0])
    for i in range(38):
        c = rgb15(mix(top, bot, i / 37))
        out += bytes([4, 0, 0, c & 0xFF, c >> 8])
    out += bytes([24, 0, 0, 0, 0, 0])
    return bytes(out)


def preview(name, idx, pal, cg, top=(0, 0, 0), bot=(0, 0, 0), spr=None):
    """Podglad: warstwa BG3 na gradiencie, z bandami i siatka boiska (cg: CGRAM -> kolor)."""
    if not PREVIEW: return
    img = np.zeros((224, 256, 3), np.uint8)
    for y in range(224):
        if 48 <= y < 200: img[y, :] = mix(top, bot, min(1, (y - 48) / 151))
    for y in range(H):
        for x in range(256):
            v = idx[y, x]
            if v: img[48 + y, x] = cg.get(int(pal[y // 8, x // 8]) * 4 + int(v), (255, 0, 255))
    if spr is not None:
        for (x, y, c) in spr:
            if 0 <= x < 256 and 0 <= y < 224: img[y, x] = c
    img[44:48, :] = 255; img[200:204, :] = 255
    for y in range(48, 200):
        if ((y - 48) // 4) % 2 == 0: img[y, 127:129] = 136
    Image.fromarray(img).resize((512, 448), Image.NEAREST).save(f'{PREVIEW}/{name}.png')


# =====================================================================================
# 4. CYBER-DOPPLER: zielony kod splywajacy kolumnami. Kazda komorka nalezy do jednej z 10 klas
# (wiersz + przesuniecie kolumny) w jednym z dwoch systemow o roznej predkosci; klasa ma
# wlasny kolor, wiec cykl palety przesuwa jasna "glowe" z ogonem w dol kolumny.
# Kafelki: 16 * i + ksztalt (i = indeks koloru 1..3), wiec gra moze podmieniac ksztalt znaku.
# =====================================================================================
GLYPHS = [
    ["..#...", "..####", ".#...#", "#...#.", "...#..", "..#...", ".#...."],
    ["..#...", "######", "..#...", "######", "..#...", "..#...", "..#..."],
    ["......", ".#..#.", ".#..#.", "#....#", "#....#", "#....#", "......"],
    ["####..", "....##", "......", "####..", "....##", "######", "......"],
    ["#....#", ".#...#", ".#..#.", "....#.", "...#..", "..#...", "##...."],
    [".####.", "......", "######", ".....#", "....#.", "...#..", ".##..."],
    ["#####.", "#...#.", "#####.", "#...#.", "#...#.", "#####.", "......"],
    ["######", "#.....", "######", "#.....", "#.....", "######", "......"],
    ["#.....", ".#...#", "#....#", ".#..#.", "....#.", "..##..", "##...."],
    ["#####.", "....#.", "...#..", "..#...", ".#....", "#####.", "......"],
    ["######", ".....#", "....#.", "...#..", "..#...", "..#...", "......"],
    ["..#...", "######", "..#...", ".###..", "#.#.#.", "..#...", "..#..."],
    ["..#...", "######", "..#...", "..#...", ".#....", "#.....", "......"],
    ["..#...", "..#...", "..###.", "..#..#", "..#...", "..#...", "..#..."],
    [".....#", "#...#.", ".#.#..", "..#...", ".#.#..", "#...#.", "......"],
    [".####.", "#....#", "#...##", "#.##.#", "##...#", ".####.", "......"],
]
K = 10
SLOT_A = [(0, 2), (0, 3), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]   # CGRAM 2..15
SLOT_B = [(4, 3), (5, 1), (5, 2), (5, 3), (6, 1), (6, 2), (6, 3), (7, 1), (7, 2), (7, 3)]   # CGRAM 19..31
PROF = [(110, 200, 128), (52, 164, 84), (36, 128, 62), (26, 102, 48), (18, 80, 38),
        (13, 62, 29), (10, 48, 22), (8, 40, 18), (7, 34, 16), (7, 34, 16)]


def doppler():
    tiles = [tile2bpp(np.zeros((8, 8), int))] * 64
    for i in (1, 2, 3):
        for s, g in enumerate(GLYPHS):
            px = np.zeros((8, 8), int)
            for y, row in enumerate(g):
                for x, ch in enumerate(row):
                    if ch == '#': px[y, x + 1] = i
            tiles[16 * i + s] = tile2bpp(px)
    save('doppler_code.til', b''.join(tiles))
    rng = np.random.default_rng(5)
    m = [0] * 1024
    idx = np.zeros((H, 256), int); pal = np.zeros((H // 8, 32), int); cls = {}
    for c in range(32):
        if rng.random() > 0.62: continue
        sysno = int(rng.integers(0, 2)); off = int(rng.integers(0, K))
        for r in range(19):
            if rng.random() < 0.12: continue
            k = (r + off) % K
            p, i = (SLOT_B if sysno else SLOT_A)[k]
            s = int(rng.integers(0, 16))
            m[(ROW0 + r) * 32 + c] = (16 * i + s) | (p << 10)
            for y, row in enumerate(GLYPHS[s]):
                for x, ch in enumerate(row):
                    if ch == '#': idx[r * 8 + y, c * 8 + x + 1] = i
            pal[r, c] = p
    save('doppler_code.map', b''.join(struct.pack('<H', e) for e in m))
    ca = bytearray(); cb = bytearray(); cg = {}
    for t in range(K):
        a = [0] * 14; b = [0] * 13
        for k, (p, i) in enumerate(SLOT_A): a[p * 4 + i - 2] = PROF[(t - k) % K]
        for k, (p, i) in enumerate(SLOT_B): b[p * 4 + i - 19] = PROF[(t - k) % K]
        ca += cols(a); cb += cols(b)
        if t == 0:
            for j, c in enumerate(a): cg[2 + j] = c if c else (0, 0, 0)
            for j, c in enumerate(b): cg[19 + j] = c if c else (0, 0, 0)
    # zaklocenie (widmowy blizniak): 2 warianty szumu - czerwony wizjer Dopplera i cyjan
    grng = np.random.default_rng(9)
    for noise in ([(170, 30, 60), (60, 10, 30), (220, 220, 230), (20, 4, 12)],
                  [(40, 190, 210), (10, 60, 80), (150, 240, 200), (4, 20, 24)]):
        a = [0] * 14; b = [0] * 13
        for (p, i) in SLOT_A: a[p * 4 + i - 2] = noise[int(grng.integers(0, 4))]
        for (p, i) in SLOT_B: b[p * 4 + i - 19] = noise[int(grng.integers(0, 4))]
        ca += cols(a); cb += cols(b)
    save('doppler_ca.bin', bytes(ca)); save('doppler_cb.bin', bytes(cb))
    top, bot = (0, 6, 3), (4, 26, 14)
    save('doppler_grad.bin', grad(top, bot))
    preview('doppler', idx, pal, cg, top, bot)


# =====================================================================================
# 5. CHANGERO: psychodeliczny wzor (plazma) w 12 pasmach koloru. Palety BG3 1,2,3,5,6,7
# obejmuja po 3 kolejne pasma {2j, 2j+1, 2j+2}, wiec kafelek z dwoma sasiednimi pasmami
# zawsze ma swoja palete. Cykl kolorow przelewa barwy po pasmach; HDMA faluje warstwa.
# =====================================================================================
NL = 12
CH_CYCLES = float(sys.argv[sys.argv.index('--cycles') + 1]) if '--cycles' in sys.argv else 1.0
CH_PALS = [1, 2, 3, 5, 6, 7]


def hsv(h, s, v):
    h = (h % 1) * 6; i = int(h); f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]
    return (r * 255, g * 255, b * 255)


def changero_col(level, t):
    return hsv((4 * level + t) / 48, 0.55, 0.34 if level % 2 == 0 else 0.25)


def changero():
    # lewa polowa dowolna, prawa jest jej lustrem (kalejdoskop; kafelki z bitem odbicia)
    x = np.arange(128)[None, :]; y = np.arange(H)[:, None]
    p = (np.sin(2 * np.pi * x / 150 + 1.4 * np.sin(2 * np.pi * y / 130))
         + 0.7 * np.sin(2 * np.pi * (x / 90 - y / 95) + 0.8)
         + 0.8 * np.sin(2 * np.pi * y / 75 + 1.8 * np.cos(2 * np.pi * x / 160 + 0.3)))
    p = np.hstack([p, p[:, ::-1]])
    v = (p - p.min()) / (p.max() - p.min())
    lv = np.floor(v * CH_CYCLES * NL).astype(int) % NL
    idx = np.zeros((H, 256), int); pal = np.zeros((H // 8, 32), int); bad = 0
    for ty in range(H // 8):
        for tx in range(32):
            blk = lv[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            best = max(range(6), key=lambda j: int((((blk - 2 * j) % NL) < 3).sum()))
            pal[ty, tx] = CH_PALS[best]
            for yy in range(8):
                for xx in range(8):
                    d = (blk[yy, xx] - 2 * best) % NL
                    if d > 2:
                        bad += 1
                        d = 2 if d < 7 else 0   # najblizsze pasmo z tej palety
                    idx[ty * 8 + yy, tx * 8 + xx] = d + 1
    print(f'  changero: {bad} pikseli przesunietych do sasiedniego pasma')
    bg3('changero_plasma', idx, pal)
    tab = bytearray(); cg = {}
    for t in range(48):
        c = [0] * 22
        for j, bp in enumerate(CH_PALS):
            for i in range(3):
                n = bp * 4 + 1 + i
                c[n - 5 if n < 16 else n - 21 + 11] = changero_col((2 * j + i) % NL, t)
                if t == 0: cg[n] = changero_col((2 * j + i) % NL, t)
        tab += cols(c)
    save('changero_cols.bin', bytes(tab))
    sine = bytearray()
    for a in range(9):
        for i in range(32): sine.append(int(round(a * math.sin(2 * math.pi * i / 32))) & 0xFF)
    save('changero_wave.bin', bytes(sine))
    preview('changero', idx, pal, cg)


# =====================================================================================
# 6. CHRONOS: tarcza zegara (BG3, paleta 7) i wskazowki ze sprite'ow 8x8 (paleta 3).
# Kafelki sprite'ow 64..79: odcinek cienkiej wskazowki pod katem 0..90 st. co 6 st.,
# 80..95: grubej (odbicie poziome daje katy 90..180). Gotowe wpisy OAM dla 60 polozen:
# chronos_hm.bin (minutowa, 10 sprite'ow) i chronos_hh.bin (godzinowa, 6 sprite'ow).
# =====================================================================================
def chronos():
    yy, xx = np.mgrid[0:H, 0:256]
    dx = xx - CX; dy = yy - CY; r = np.hypot(dx, dy)
    ang = (np.degrees(np.arctan2(dx, -dy)) + 360) % 360          # 0 = godzina 12, zgodnie z zegarem
    idx = np.zeros((H, 256), int)
    idx[r < 66.5] = 1
    idx[(r >= 68) & (r < 72.5)] = 2
    idx[((r >= 66.5) & (r < 68)) | ((r >= 72.5) & (r < 74))] = 3
    ring = (r >= 44.4) & (r < 45.4) & ((ang % 6) < 3)
    idx[ring] = 2
    for k in range(60):
        a = math.radians(6 * k); ux, uy = math.sin(a), -math.cos(a)
        along = dx * ux + dy * uy; across = np.abs(-dx * uy + dy * ux)
        if k % 5 == 0:
            w = 1.6 if k else 1.0
            sel = (along >= 53) & (along <= 63.5) & (across <= w)
            if k == 0: sel |= (along >= 53) & (along <= 63.5) & (np.abs(across - 2.2) <= 0.8)
            idx[sel] = 3
        else:
            idx[(along >= 60) & (along <= 63) & (across <= 0.6)] = 2
    idx[r < 4.5] = 3
    idx[r < 2] = 2
    pal = np.full((H // 8, 32), 7)
    bg3('chronos_dial', idx, pal)
    top, bot = (8, 6, 4), (30, 22, 12)
    save('chronos_grad.bin', grad(top, bot))

    def seg(alpha, core, edge):
        a = math.radians(alpha); ddx, ddy = math.cos(a), -math.sin(a); nx, ny = math.sin(a), math.cos(a)
        px = np.zeros((8, 8), int)
        for y in range(8):
            for x in range(8):
                t = (x - 3.5) * ddx + (y - 3.5) * ddy; d = abs((x - 3.5) * nx + (y - 3.5) * ny)
                if abs(t) > 4.6: continue
                px[y, x] = 2 if d <= core else (1 if d <= edge else 0)
        return px
    st = b''.join(tile4bpp(seg(6 * i, 0.55, 1.15)) for i in range(16))
    st += b''.join(tile4bpp(seg(6 * i, 0.95, 1.65)) for i in range(16))
    save('chronos_hands.til', st)
    hm = bytearray(); hh = bytearray()
    for n in range(60):
        f = math.radians(6 * n); s, c = math.sin(f), math.cos(f)
        al = (90 - 6 * n) % 180
        ti, fl = (al // 6, 0) if al <= 90 else ((180 - al) // 6, 0x40)
        for out, cnt, tile in ((hm, 10, 64 + ti), (hh, 6, 80 + ti)):
            for k in range(cnt):
                d = 5 + 6 * k
                out += bytes([int(round(127.5 + d * s - 3.5)) & 0xFF, int(round(123.5 - d * c - 3.5)) & 0xFF, tile, 0x16 | fl])
    save('chronos_hm.bin', bytes(hm)); save('chronos_hh.bin', bytes(hh))
    # fala czasu: dluga tablica HDMA (2 linie na wpis) z garbem w srodku; okno przesuwa gra
    B, W = 128, 16
    wt = bytearray()
    for j in range(256):
        u = j - B
        v = int(round(4 * math.sin(2 * math.pi * u / 7) * math.cos(math.pi / 2 * u / W) ** 2)) if abs(u) < W else 0
        wt += bytes([2, v & 0xFF, (v >> 8) & 0xFF])
    wt += bytes([0])
    save('chronos_wave.bin', bytes(wt))
    cg = {29: (40, 30, 20), 30: (120, 88, 44), 31: (176, 136, 72)}
    sp = []
    for blk, n, base, core, edge in ((hm, 0, 64, 0.55, 1.15), (hh, 50, 80, 0.95, 1.65)):
        cnt = len(blk) // 240
        for j in range(cnt):
            sx, sy, tile, attr = blk[(n * cnt + j) * 4:(n * cnt + j) * 4 + 4]
            px = seg(6 * (tile - base), core, edge)
            if attr & 0x40: px = px[:, ::-1]
            for y in range(8):
                for x in range(8):
                    if px[y, x]: sp.append((sx + x, sy + y, (196, 156, 86) if px[y, x] == 2 else (80, 58, 28)))
    preview('chronos', idx, pal, cg, top, bot, sp)


# =====================================================================================
# 7. MAGNETON: linie pola miedzy biegunami za lewa (N) i prawa (S) krawedzia - luki okregow
# przez oba bieguny. Kreski w 3 fazach (indeksy 1..3) - cykl palety przesuwa je od N do S.
# Palety BG3 5/6/7: lewa (czerwonawa), srodkowa (fioletowa) i prawa (niebieskawa) czesc.
# =====================================================================================
MAG_BASE = [(230, 80, 80), (180, 100, 220), (90, 130, 250)]


def magneton_cols(lvl, ph):
    out = [0] * 11
    for j, bp in enumerate((5, 6, 7)):
        for i in range(3):
            k = (i - ph) % 3   # 0 = jasna kreska, 2 = srednia, 1 = ciemna
            f = [0.38 + 0.18 * lvl, 0.12 + 0.05 * lvl, 0.22 + 0.10 * lvl][k]
            out[bp * 4 + 1 + i - 21] = scale(MAG_BASE[j], min(1.0, f))
    return out


def magneton():
    idx = np.zeros((H, 256), int)
    P1, P2 = (-48.0, CY), (303.0, CY)
    half = (P2[0] - P1[0]) / 2
    for hgt in (13, 27, 43, 62, 86, 118, 165):
        for up in (True, False):
            c = (half * half - hgt * hgt) / (2 * hgt)
            cy = CY + c if up else CY - c
            rho = math.hypot(half, c)
            # luk od P1 do P2 przechodzacy przez wierzcholek (CX, CY -/+ hgt)
            a1 = math.atan2(P1[1] - cy, P1[0] - CX); a2 = math.atan2(P2[1] - cy, P2[0] - CX)
            apex = math.atan2((CY - hgt if up else CY + hgt) - cy, 0.0)
            span = (a2 - a1) % (2 * math.pi)
            if (apex - a1) % (2 * math.pi) > span: span -= 2 * math.pi
            n = int(abs(span) * rho * 4) + 1
            for k in range(n + 1):
                a = a1 + span * k / n
                x, y = CX + rho * math.cos(a), cy + rho * math.sin(a)
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < 256 and 0 <= yi < H:
                    s = abs(span) * rho * k / n
                    idx[yi, xi] = 1 + int(s // 4) % 3
    pal = np.zeros((H // 8, 32), int)
    pal[:, :11] = 5; pal[:, 11:21] = 6; pal[:, 21:] = 7
    bg3('magneton_field', idx, pal)
    tab = bytearray()
    for lvl in range(4):
        for ph in range(3): tab += cols(magneton_cols(lvl, ph))
    save('magneton_cols.bin', bytes(tab))
    top, bot = (4, 6, 12), (16, 20, 36)
    save('magneton_grad.bin', grad(top, bot))
    # iskra: 9 kafelkow sprite'ow 64..72 (wejscie u gory x = XS[a], wyjscie u dolu x = XS[b])
    XS = [1, 4, 6]
    st = b''
    for a in range(3):
        for b in range(3):
            px = np.zeros((8, 8), int)
            mid = (XS[a] + XS[b]) // 2 + (1 if (a + 2 * b) % 3 == 0 else -1)
            mid = max(0, min(7, mid))
            pts = [(XS[a], 0), (mid, 3), (mid, 4), (XS[b], 7)]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                for k in range(9):
                    x = int(round(x0 + (x1 - x0) * k / 8)); y = int(round(y0 + (y1 - y0) * k / 8))
                    px[y, x] = 2
            glow = np.zeros((8, 8), int)
            for y in range(8):
                for x in range(8):
                    if px[y, x] == 0 and ((x > 0 and px[y, x - 1] == 2) or (x < 7 and px[y, x + 1] == 2)): glow[y, x] = 1
            st += tile4bpp(px + glow)
    save('magneton_spark.til', st)
    # gotowe wpisy OAM iskry: 8 kolumn (x = 60 + 18k) x 4 warianty zygzaka, 19 sprite'ow (y = 47..191)
    srng = np.random.default_rng(31); sb = bytearray()
    for k in range(8):
        for v in range(4):
            a = int(srng.integers(0, 3))
            for i in range(19):
                b = int(srng.integers(0, 3))
                sb += bytes([60 + 18 * k, 47 + 8 * i, 64 + 3 * a + b, 0x16])
                a = b
    save('magneton_sparks.bin', bytes(sb))
    cg = {}
    for j, c in enumerate(magneton_cols(0, 0)): cg[21 + j] = c if c else (0, 0, 0)
    preview('magneton', idx, pal, cg, top, bot)


# =====================================================================================
# 8. TELEMENTOR: nocne niebo - gwiazdy migoczace w 3 grupach (paleta 7), jasne gwiazdy-krzyzyki
# (paleta 6), wzgorza na horyzoncie (paleta 5). UFO i wiazka swiatla: sprite'y 16x16 (paleta 3),
# kafelki 64..191 (UFO: 64-67/80-83, wiazka 3x3: 96 + wiersz*32 + kolumna*2).
# =====================================================================================
TWINKLE = (170, 180, 230)


def tele_cols(t):
    return [scale(TWINKLE, 0.5 + 0.5 * math.cos(2 * math.pi * (t / 16 + g / 3))) for g in range(3)]


def telementor():
    rng = np.random.default_rng(17)
    xs = np.arange(256)
    hill = np.round(H - 1 - (11 + 6 * np.sin(2 * np.pi * xs / 256 * 1.5 + 1.0) + 4 * np.sin(2 * np.pi * xs / 256 * 3.7 + 0.4))).astype(int)
    idx = np.zeros((H, 256), int); pal = np.full((H // 8, 32), 7)
    hillmask = np.zeros((H, 256), bool)
    for x in range(256):
        hillmask[hill[x]:, x] = True
        idx[hill[x]:, x] = 2
        idx[hill[x], x] = 1
    for ty in range(H // 8):
        for tx in range(32):
            if hillmask[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].any(): pal[ty, tx] = 5
    stars = []
    while len(stars) < 115:
        x, y = int(rng.integers(2, 254)), int(rng.integers(2, H - 30))
        if y > hill[x] - 10 or any(abs(x - a) < 6 and abs(y - b) < 6 for a, b, _ in stars): continue
        stars.append((x, y, 'plus' if rng.random() < 0.13 else 'dot'))
    for x, y, kind in stars:
        ty, tx = y // 8, x // 8
        if pal[ty, tx] == 5: continue
        if kind == 'plus':
            blk = idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if pal[ty, tx] == 7 and blk.any(): continue
            pal[ty, tx] = 6
            idx[y, x] = 3
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + ddx) // 8 == tx and (y + ddy) // 8 == ty: idx[y + ddy, x + ddx] = 1
        else:
            if pal[ty, tx] == 6: continue
            idx[y, x] = int(rng.integers(1, 4))
    bg3('telementor_sky', idx, pal)
    tab = bytearray()
    for t in range(16): tab += cols(tele_cols(t))
    save('telementor_cols.bin', bytes(tab))
    top, bot = (2, 2, 10), (26, 14, 46)
    save('telementor_grad.bin', grad(top, bot))
    # UFO 32x16 i wiazka 48x48 na arkuszu 128 x 64 (kafelki 64..191)
    sheet = np.zeros((64, 128), int)
    for y in range(16):
        for x in range(32):
            ex = (x + 0.5 - 16) / 15.5; ey = (y + 0.5 - 9.5) / 3.6
            dxm = (x + 0.5 - 16) / 6.5; dym = (y + 0.5 - 6.5) / 5.5
            if y < 7 and dxm * dxm + dym * dym <= 1:
                sheet[y, x] = 5 if (x < 15 and y < 4) else 4
            elif ex * ex + ey * ey <= 1:
                sheet[y, x] = 3 if y <= 7 else (2 if y <= 10 else 1)
    for i, lx in enumerate((5, 10, 16, 21, 26)): sheet[9, lx] = 6 + (i & 1); sheet[9, lx - 1] = 6 + (i & 1)
    for x in range(11, 21): sheet[14, x] = 10
    for x in range(13, 19): sheet[15, x] = 10
    beam = np.zeros((48, 48), int)
    for y in range(48):
        half = 6 + (22 - 6) * y / 47
        for x in range(48):
            if abs(x + 0.5 - 24) > half: continue
            if y < 30:
                on = (x + y) % 2 == 0
            else:
                on = (x % 2 == 0) and (y % 2 == 0)
            edge = abs(x + 0.5 - 24) > half - 2
            if on: beam[y, x] = 9 if (edge or y >= 30) else 8
    sheet[16:64, 0:48] = beam
    st = b''
    for ty in range(8):
        for tx in range(16): st += tile4bpp(sheet[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8])
    save('telementor_ufo.til', st)
    used = [int(beam[by * 16:by * 16 + 16, bx * 16:bx * 16 + 16].any()) for by in range(3) for bx in range(3)]
    print('  telementor: niepuste sprite\'y wiazki (3x3):', used)
    # gotowe wpisy OAM wiazki: 8 miejsc postoju (x = 48 + 16k) x 2 wysokosci UFO (58, 66)
    bb = bytearray()
    for k in range(8):
        for uy in (58, 66):
            for by in range(3):
                for bx in range(3):
                    bb += bytes([48 + 16 * k - 8 + 16 * bx, uy + 14 + 16 * by, 96 + 32 * by + 2 * bx, 0x16])
    save('telementor_beam.bin', bytes(bb))
    cg = {29: TWINKLE, 30: scale(TWINKLE, 0.6), 31: scale(TWINKLE, 0.3),
          25: (60, 64, 110), 26: (0, 0, 0), 27: (220, 225, 255), 21: (40, 30, 74), 22: (14, 12, 30)}
    pc = {1: (70, 70, 100), 2: (130, 130, 170), 3: (190, 190, 220), 4: (90, 170, 190), 5: (180, 240, 250),
          6: (255, 220, 80), 7: (255, 90, 120), 8: (150, 190, 120), 9: (90, 130, 80), 10: (120, 200, 160)}
    sp = []
    ux, uy = 96, 66
    for y in range(48):
        for x in range(48):
            if beam[y, x]: sp.append((ux + 16 - 24 + x, uy + 14 + y, pc[beam[y, x]]))
    for y in range(16):
        for x in range(32):
            if sheet[y, x]: sp.append((ux + x, uy + y, pc[sheet[y, x]]))
    preview('telementor', idx, pal, cg, top, bot, sp)


# =====================================================================================
# 9. BLINKER: tecza nad boiskiem - 7 pasow po 6 px. Palety BG3 1,2,3,5,6 obejmuja po 3 kolejne
# pasy {j, j+1, j+2}, wiec kazdy kafelek ma swoja palete. Barwy pasow lekko sie mienia
# (32 fazy w blinker_cols.bin, jak u Changero: kolory 5-15 i 21-31).
# =====================================================================================
RB_HUES = [0, 28, 52, 120, 205, 245, 280]   # od zewnatrz: czerwony ... fioletowy
RB_PALS = [1, 2, 3, 5, 6]


def blinker_col(b, t):
    h = RB_HUES[b] / 360 + 0.03 * math.sin(2 * math.pi * (t / 32 + b / 7))
    v = 0.74 * (0.92 + 0.08 * math.sin(2 * math.pi * (2 * t / 32 + b / 3.5)))
    return hsv(h, 0.5, v)


def blinker():
    yy, xx = np.mgrid[0:H, 0:256]
    r = np.hypot(xx + 0.5 - 128, yy + 0.5 - 205)
    band = np.floor((175 - r) / 6).astype(int)
    inside = (band >= 0) & (band < 7)
    idx = np.zeros((H, 256), int); pal = np.full((H // 8, 32), 7)
    for ty in range(H // 8):
        for tx in range(32):
            sl = (slice(ty * 8, ty * 8 + 8), slice(tx * 8, tx * 8 + 8))
            b = band[sl][inside[sl]]
            if b.size == 0: continue
            j = min(int(b.min()), 4)
            pal[ty, tx] = RB_PALS[j]
            idx[sl] = np.where(inside[sl], np.clip(band[sl] - j + 1, 1, 3), 0)
    bg3('blinker_rainbow', idx, pal)
    tab = bytearray(); cg = {}
    for t in range(32):
        c = [0] * 22
        for j, bp in enumerate(RB_PALS):
            for i in range(3):
                n = bp * 4 + 1 + i
                c[n - 5 if n < 16 else n - 21 + 11] = blinker_col(j + i, t)
                if t == 0: cg[n] = blinker_col(j + i, t)
        tab += cols(c)
    save('blinker_cols.bin', bytes(tab))
    for k, back in enumerate(((150, 36, 36), (40, 64, 176), (36, 128, 56))):
        preview(f'blinker{k}', idx, pal, cg, back, back)


if __name__ == '__main__':
    doppler()
    changero()
    chronos()
    magneton()
    telementor()
    blinker()
