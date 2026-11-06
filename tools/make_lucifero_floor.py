# Plansza Lucifero (Mode 7): ponura, szara posadzka z betonowych plyt + linie boiska.
# Mode 7 zajmuje TYLKO slowa VRAM $2200-$3FFF: kafelki 136-255 (bajty wysokie) i wiersze 68-127
# mapy (bajty niskie). Pasek u gory (kafelki 0-15 i 256-543) zostaje nietkniety.
# Kolory podlogi: CGRAM 64-79 (paleta 4 = logo, uzywana tylko na ekranie tytulowym).
# Wyjscie: luc_floor.til (120 kafelkow x 64 B), luc_floor.map (60 wierszy x 128 B), luc_floor.pal,
#          luc_m7.bin (M7A i VOFS dla linii 48-223), luc_proj.bin (y pola -> linia ekranu, skala linii).
import math, numpy as np
FIRST_TILE, N_TILES, MAP_ROW0, CG0 = 136, 120, 68, 64
FT, FB = 48, 200                      # gora i dol boiska (wspolrzedne gry)
LF, LN, S_FAR = 70, 212, 0.72         # linia ekranu dla FT i FB, skala dalekiej krawedzi
LH = (LF - S_FAR * LN) / (1 - S_FAR)  # linia horyzontu (poza ekranem)
B = (FB - FT) / (1 / (LF - LH) - 1 / (LN - LH)); A = FB + B / (LN - LH)
def v_of(L): return A - B / (L - LH)          # wspolrzedna y pola widoczna w linii L
def s_of(L): return (L - LH) / (LN - LH)      # skala pozioma linii L
PAL = [(0, 0, 0), (26, 26, 29), (34, 34, 37), (42, 42, 45), (50, 50, 53), (58, 58, 61), (68, 68, 71),
       (80, 80, 82), (94, 94, 96), (110, 110, 112), (150, 150, 148), (184, 184, 180), (16, 16, 18),
       (40, 33, 31), (0, 0, 0), (0, 0, 0)]
rng = np.random.default_rng(13)
def slab(variant):   # plyta 16x16: szum betonu, spoina (ciemniejsza) na prawej i dolnej krawedzi
    r = np.random.default_rng(100 + variant)
    base = 4 + (variant % 3)
    t = base + r.integers(-1, 2, (16, 16))
    for _ in range(3 + variant % 4):          # drobne ciemniejsze i jasniejsze plamki
        y, x = r.integers(0, 15, 2); t[y:y + 2, x:x + 2] += r.choice([-2, 1])
    if variant in (2, 5):                     # pekniecie
        x = 3 + variant
        for y in range(16):
            x = min(14, max(1, x + r.integers(-1, 2))); t[y, x] = 12
    if variant in (3, 7):                     # ciemna plama
        cy, cx = r.integers(4, 12, 2)
        for y in range(16):
            for x in range(16):
                if (y - cy) ** 2 + (x - cx) ** 2 < 10 + variant: t[y, x] = 13
    t[:, 15] = 2; t[15, :] = 2                # spoiny
    return np.clip(t, 1, 13)
SLABS = [slab(k) for k in range(8)]
tex = np.zeros((224, 256), int)               # 0 = pustka (przezroczysta -> czarne tlo)
for v in range(FT, FB):
    for u in range(256):
        k = ((u // 16) * 7 + (v // 16) * 3 + (u // 16) * (v // 16)) % 8
        tex[v, u] = SLABS[k][v % 16, u % 16]
tex[FT - 4:FT, :] = 10; tex[FT - 4, :] = 11   # gorna banda
tex[FB:FB + 4, :] = 10; tex[FB + 3, :] = 11   # dolna banda
for v in range(FT, FB):                       # przerywana linia srodkowa (x 127-128)
    if (v // 4) % 2 == 0: tex[v, 127:129] = 10
# kafelki: deduplikacja; kafelek 0 (FIRST_TILE) = pustka
tiles = [np.zeros((8, 8), int)]; index = {tiles[0].tobytes(): 0}
tmap = np.zeros((28, 32), int)
for ty in range(28):
    for tx in range(32):
        t = tex[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]; key = t.tobytes()
        if key not in index:
            index[key] = len(tiles); tiles.append(t.copy())
        tmap[ty, tx] = index[key]
assert len(tiles) <= N_TILES, len(tiles)
til = bytearray()
for t in tiles + [np.zeros((8, 8), int)] * (N_TILES - len(tiles)):
    for y in range(8):
        for x in range(8):
            c = int(t[y, x]); til.append(0 if c == 0 else CG0 + c)
mp = bytearray([FIRST_TILE]) * (60 * 128)
for ty in range(28):
    for tx in range(32):
        mp[ty * 128 + tx] = FIRST_TILE + int(tmap[ty, tx])
pal = bytearray()
for (r, g, b) in PAL:
    c = (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10); pal += bytes([c & 255, c >> 8])
m7 = bytearray()
for L in range(48, 224):                      # M7A (8.8) dla linii 48-223
    a = int(round(256 / s_of(L))); m7 += bytes([a & 255, a >> 8])
for L in range(48, 224):                      # VOFS: tekstura y = L + VOFS (D = 1)
    vo = (int(round(v_of(L))) + MAP_ROW0 * 8 - L) & 0x1FFF; m7 += bytes([vo & 255, vo >> 8])
proj = bytearray()
for y in range(256):                          # y pola -> linia ekranu (0xF0 = poza ekranem)
    if y >= 224: proj.append(0xF0); continue
    L = LH + B / (A - y) if A - y > 0 else 999
    proj.append(int(round(L)) if 0 <= L < 224 else 0xF0)
for L in range(224):                          # skala linii x256 (najwyzej 255)
    proj.append(min(255, max(1, int(round(256 * s_of(L))))))
open('luc_floor.til', 'wb').write(til); open('luc_floor.map', 'wb').write(mp)
open('luc_floor.pal', 'wb').write(pal); open('luc_m7.bin', 'wb').write(m7); open('luc_proj.bin', 'wb').write(proj)
if __name__ == '__main__':
    print('unique tiles', len(tiles), '| horizon', round(LH, 1), '| v(48)', round(v_of(48), 1), 'v(223)', round(v_of(223), 1),
          '| proj y48->', proj[48], 'y200->', proj[200], '| scale far/near', proj[256 + 70], proj[256 + 212])
    from PIL import Image   # podglad: tekstura w perspektywie (jak na ekranie)
    img = np.zeros((224, 256, 3), np.uint8)
    for L in range(48, 224):
        v = int(round(v_of(L))); s = s_of(L)
        for x in range(256):
            u = int(round((x - 128) / s + 128))
            if 0 <= v < 224 and 0 <= u < 256 and tex[v, u]: img[L, x] = PAL[tex[v, u]]
    Image.fromarray(img).resize((512, 448), Image.NEAREST).save('/tmp/luc_floor_preview.png')
