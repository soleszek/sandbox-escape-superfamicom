# Duch na arenie Maltena: przescieradlo przodem, rysowane recznie wiersz po wierszu. 32x48
# (6 sprite'ow 16x16), 2 klatki. Kafelki sprite'ow od 64 (TILE_ARSPR), siatka 16 kafelkow w wierszu:
# klatka 0 = kolumny 0-3, klatka 1 = kolumny 4-7, wiersze 0-5.
# Kolory palety sprite'ow 7: 1 cialo, 2 kontur/cien, 3 oczy i usta, 4 rozblysk.
import numpy as np
W, H = 32, 48
LEFT = {1: [(13, 15)], 2: [(11, 15)], 3: [(10, 15)], 4: [(9, 15)], 5: [(9, 15)], 6: [(8, 15)], 7: [(8, 15)],
        8: [(8, 15)], 9: [(8, 15)], 10: [(8, 15)], 11: [(8, 15)], 12: [(7, 15)], 13: [(5, 15)], 14: [(3, 15)],
        15: [(2, 15)], 16: [(1, 15)]}
for y in range(17, 27): LEFT[y] = [(1, 15)]
LEFT.update({27: [(1, 3), (5, 15)], 28: [(1, 3), (6, 15)], 29: [(2, 3), (7, 15)], 30: [(2, 2), (8, 9), (11, 15)],
             31: [(9, 9), (11, 15)], 32: [(12, 15)], 33: [(12, 15)], 34: [(13, 15)], 35: [(13, 15)], 36: [(13, 15)],
             37: [(14, 15)], 38: [(14, 15)], 39: [(14, 15)], 40: [(15, 15)], 41: [(15, 15)]})
def sheet(f):
    m = np.zeros((H, W), bool)
    for y, spans in LEFT.items():
        for (x0, x1) in spans:
            m[y, x0:x1 + 1] = True
            m[y, 31 - x1:31 - x0 + 1] = True
    m[42, 15] = True
    m[43, 14] = True
    if f:   # druga klatka: zacieki po bokach i szpic kolysza sie
        m[30, 2] = False; m[31, 3] = True
        m[30, 29] = False; m[30, 28] = True
        m[42, 15] = False; m[43, 14] = False; m[42, 16] = True; m[43, 17] = True
        m[16:18, 0] = True; m[14, 3] = False
    a = np.where(m, 1, 0)
    pad = np.pad(m, 1)
    edge = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    a[edge] = 2
    for x in (4, 8, 12, 19, 23, 27):   # ciemniejace faldy u dolu
        for y in range(20 + abs(x - 15) // 3, H):
            if a[y, x] == 1: a[y, x] = 2
    for y in range(28, H):
        for x in range(W):
            if a[y, x] == 1 and (y > 34 or (x + y) % 2 == 0): a[y, x] = 2
    for (x, y) in ((12, 6), (11, 7), (12, 7), (11, 8), (12, 8), (11, 9),
                   (19, 6), (19, 7), (20, 7), (19, 8), (20, 8), (20, 9),
                   (15, 10), (16, 10), (15, 11), (16, 11), (15, 12), (16, 12), (15, 13), (16, 13)):
        a[y, x] = 3
    a[10, 15] = 1; a[13, 16] = 1
    for (x, y) in ((14, 2), (15, 2), (16, 2), (12, 3), (13, 3)):
        if a[y, x] == 1: a[y, x] = 4
    return a
def tile4bpp(px):
    lo = bytearray(); hi = bytearray()
    for r in range(8):
        b = [0, 0, 0, 0]
        for c in range(8):
            v = int(px[r][c])
            for k in range(4): b[k] |= ((v >> k) & 1) << (7 - c)
        lo += bytes([b[0], b[1]]); hi += bytes([b[2], b[3]])
    return bytes(lo + hi)
frames = [sheet(0), sheet(1)]
tiles = []
for row in range(6):
    for col in range(16):
        f, c = divmod(col, 4)
        tiles.append(tile4bpp(frames[f][row * 8:row * 8 + 8, c * 8:c * 8 + 8]) if f < 2 else bytes(32))
open('malten_ghost.til', 'wb').write(b''.join(tiles))
print('ghost tiles', len(tiles))
