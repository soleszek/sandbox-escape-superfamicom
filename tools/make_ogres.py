# Ogry i trolle z areny Rudena: sylwetki budowane na szkielecie (stawy w obrysie tulowia,
# wiec rece sa zawsze polaczone z cialem). Kolory: 5 sylwetka, 6 obrys od nieba, 7 oczy,
# 8 poswiata wokol oczu (oczy i poswiata pulsuja w grze zmiana koloru palety).
import numpy as np
from PIL import Image, ImageDraw
CH = 56
def cap(d, a, b, w):   # konczyna: gruba linia z zaokraglonymi koncami
    d.line([a, b], fill=5, width=w); r = w / 2
    for p in (a, b): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=5)
def blob(d, c, rx, ry): d.ellipse([c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry], fill=5)
def club(d, hand, tip, big):   # maczuga trzymana w dloni: trzonek od dloni do glowicy
    cap(d, hand, tip, 3)
    blob(d, tip, big, big + 1)
def eyes(e, x, y): e += [(x - 3, y), (x - 2, y), (x + 2, y), (x + 3, y)]

def ogre(d, e, x, g, pose, s):   # wielki ogr z maczuga (s = 1: maczuga w prawej, -1: w lewej)
    y = g - 1
    cap(d, (x - 6, y - 12), (x - 7, y - 1), 7); cap(d, (x + 6, y - 12), (x + 7, y - 1), 7)   # nogi
    blob(d, (x - 8, y - 1), 5, 2); blob(d, (x + 8, y - 1), 5, 2)                               # stopy
    d.polygon([(x - 15, y - 34), (x + 15, y - 34), (x + 13, y - 12), (x - 13, y - 12)], fill=5)   # tulow
    blob(d, (x, y - 18), 14, 9)                                                                  # brzuch
    blob(d, (x, y - 39), 7, 6); blob(d, (x, y - 35), 6, 3)                                       # glowa, szczeka
    eyes(e, x, y - 40); RIM.extend([(x - 4, y - 34), (x - 4, y - 33), (x + 4, y - 34), (x + 4, y - 33)])   # oczy, jasne kly
    sh_c, sh_f = (x + 13 * s, y - 31), (x - 13 * s, y - 31)   # bark z maczuga, bark wolny
    # uderzenie maczuga: 2 zamach nad glowa -> 1 cios w ukosie -> 0 uderzenie w ziemie (z kurzem)
    if pose == 0:   hand = (x + 18 * s, y - 13); tip = (x + 25 * s, y - 4)
    elif pose == 1: hand = (x + 17 * s, y - 31); tip = (x + 19 * s, y - 45)   # cios: prawie pionowo (odstep od sasiada)
    else:           hand = (x + 13 * s, y - 47); tip = (x + 5 * s, y - 53)   # zamach: maczuga nad glowa
    elbow = ((sh_c[0] + hand[0]) // 2 + 3 * s, (sh_c[1] + hand[1]) // 2 + (2 if pose < 2 else 0))
    cap(d, sh_c, elbow, 6); cap(d, elbow, hand, 5); blob(d, hand, 3, 3); club(d, hand, tip, 4)
    if pose == 0:   # kurz spod glowicy przy uderzeniu
        DUST.extend([(tip[0] + dx, y - dy) for dx, dy in ((-7, 2), (-6, 4), (7, 2), (6, 4), (-9, 1), (9, 1), (-4, 6), (4, 6))])
    if pose == 3:   free = (x - 17 * s, y - 50)       # wiwat: obie rece w gorze
    elif pose == 0: free = (x - 17 * s, y - 26)       # rownowaga przy uderzeniu
    elif pose == 2: free = (x - 17 * s, y - 20)       # przy zamachu reka na bok (poza obrysem tulowia)
    else:           free = (x - 18 * s, y - 15)
    fe = ((sh_f[0] + free[0]) // 2 - 2 * s, (sh_f[1] + free[1]) // 2)
    cap(d, sh_f, fe, 6); cap(d, fe, free, 5); blob(d, free, 3, 3)

def troll(d, e, x, g, pose, s):   # rogaty troll, chudszy, z piesciami
    y = g - 1
    cap(d, (x - 4, y - 14), (x - 5, y - 1), 5); cap(d, (x + 4, y - 14), (x + 5, y - 1), 5)
    blob(d, (x - 6, y - 1), 4, 2); blob(d, (x + 6, y - 1), 4, 2)
    d.polygon([(x - 11, y - 36), (x + 11, y - 36), (x + 8, y - 14), (x - 8, y - 14)], fill=5)
    blob(d, (x, y - 41), 6, 6)
    d.polygon([(x - 4, y - 45), (x - 10, y - 53), (x - 1, y - 46)], fill=5); d.polygon([(x + 4, y - 45), (x + 10, y - 53), (x + 1, y - 46)], fill=5)
    eyes(e, x, y - 42)
    for side in (-1, 1):
        sh = (x + 10 * side, y - 33)
        if pose == 0:   el, hd = (x + 13 * side, y - 22), (x + 13 * side, y - 11)
        elif pose == 1: el, hd = (x + 16 * side, y - 33), (x + 16 * side, y - 43)   # prezenie muskulow
        elif pose == 2: el, hd = (x + 15 * side, y - 40), (x + 13 * side, y - 49)
        else:           el, hd = (x + 14 * side, y - 40), (x + 16 * side, y - 49)
        cap(d, sh, el, 5); cap(d, el, hd, 4); blob(d, hd, 3, 3)

def thug(d, e, x, g, pose, s):   # przysadzisty zakapior z maczuga na ramieniu
    y = g - 1
    cap(d, (x - 6, y - 9), (x - 6, y - 1), 7); cap(d, (x + 6, y - 9), (x + 6, y - 1), 7)
    blob(d, (x - 7, y - 1), 5, 2); blob(d, (x + 7, y - 1), 5, 2)
    d.polygon([(x - 14, y - 27), (x + 14, y - 27), (x + 13, y - 9), (x - 13, y - 9)], fill=5)
    blob(d, (x, y - 15), 14, 7)
    blob(d, (x, y - 31), 6, 5)
    eyes(e, x, y - 32)
    sh_c, sh_f = (x + 12 * s, y - 25), (x - 12 * s, y - 25)
    if pose == 0:   hand = (x + 15 * s, y - 18); tip = (x + 6 * s, y - 40)    # maczuga oparta o bark
    elif pose == 1: hand = (x + 18 * s, y - 28); tip = (x + 23 * s, y - 40)   # ukosnie w gore
    else:           hand = (x + 16 * s, y - 40); tip = (x + 18 * s, y - 52)
    el = ((sh_c[0] + hand[0]) // 2 + 3 * s, (sh_c[1] + hand[1]) // 2 + 2)
    cap(d, sh_c, el, 6); cap(d, el, hand, 5); blob(d, hand, 3, 3); club(d, hand, tip, 4)
    free = (x - 15 * s, y - 44) if pose == 3 else (x - 16 * s, y - 11)
    fe = ((sh_f[0] + free[0]) // 2 - 2 * s, (sh_f[1] + free[1]) // 2)
    cap(d, sh_f, fe, 6); cap(d, fe, free, 5); blob(d, free, 3, 3)

FIGS = [(53, ogre, 1, 0), (100, troll, 1, 2), (156, troll, -1, 0), (204, thug, -1, 2)]   # x, postac, strona, faza
CYC = [0, 1, 2, 1]
RIM = []
DUST = []
def frame(step):
    im = Image.new('P', (256, CH), 0); d = ImageDraw.Draw(im); e = []; RIM.clear(); DUST.clear()
    for x, f, s, ph in FIGS:
        pose = 3 if step == 3 else CYC[(step + ph) % 4]
        f(d, e, x, CH, pose, s)
    a = np.array(im)
    for _ in range(2):   # sprzatanie: pojedyncze piksele i dziurki
        n = sum(np.roll(np.roll(a == 5, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
        a[(a == 5) & (n <= 1)] = 0; a[(a == 0) & (n >= 7)] = 5
    rim = (a == 5) & (np.vstack([np.zeros((1, 256), int), a[:-1]]) == 0)
    a[rim] = 6
    for px, py in e:
        if 0 <= py < CH and a[py, px] in (5, 6): a[py, px] = 7
    for px, py in RIM:
        if 0 <= py < CH and a[py, px] == 5: a[py, px] = 6
    ey = (a == 7)   # poswiata: piksele sylwetki wokol oczu (kolor 8)
    near = np.zeros_like(ey)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= np.roll(np.roll(ey, dy, 0), dx, 1)
    a[near & (a == 5)] = 8
    for px, py in DUST:   # kurz (kolor obrysu) tylko na tle
        if 0 <= py < CH and a[py, px] == 0: a[py, px] = 6
    return a
if __name__ == '__main__':
    fr = [frame(k) for k in range(4)]
    sky = np.zeros((CH, 256, 3), np.uint8)
    for y in range(CH):
        t = y / (CH - 1); sky[y] = (np.array([78, 32, 10]) * (1 - t) + np.array([125, 50, 14]) * t)
    pal = {5: (26, 12, 8), 6: (120, 50, 14), 7: (235, 40, 20)}
    rows = []
    for a in fr:
        img = sky.copy()
        for k, c in pal.items(): img[a == k] = c
        rows.append(img); rows.append(np.full((4, 256, 3), 40, np.uint8))
    Image.fromarray(np.vstack(rows)).resize((256 * 4, (CH + 4) * 4 * 4), Image.NEAREST).save('/home/claude/ogres/preview.png')
    import sys; sys.path.insert(0, 'tools')
    def t4(px):
        lo = bytearray(); hi = bytearray()
        for r in range(8):
            b = [0, 0, 0, 0]
            for c in range(8):
                v = int(px[r][c])
                for k in range(4): b[k] |= ((v >> k) & 1) << (7 - c)
            lo += bytes([b[0], b[1]]); hi += bytes([b[2], b[3]])
        return bytes(lo + hi)
    seen = {t4(np.zeros((8, 8)))}
    for a in fr:
        for ty in range(CH // 8):
            for tx in range(32):
                blk = a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                if blk.any() and tx not in (15, 16): seen.add(t4(blk))
    print('tiles', len(seen), '(limit 224) | x range', min(np.nonzero(np.any(np.array(fr) > 0, axis=(0, 1)))[0]), '-', max(np.nonzero(np.any(np.array(fr) > 0, axis=(0, 1)))[0]))

def write_crowd():
    # kafelki (4 bity, od kafelka 544, paleta boiska 1) i 4 mapy po 7 wierszy dla gry:
    # 0 dol/gora, 1 srodek, 2 gora/dol, 3 wiwat; 0xFFFF = puste pole (zostaje boisko)
    import struct
    def t4(px):
        lo = bytearray(); hi = bytearray()
        for r in range(8):
            b = [0, 0, 0, 0]
            for c in range(8):
                v = int(px[r][c])
                for k in range(4): b[k] |= ((v >> k) & 1) << (7 - c)
            lo += bytes([b[0], b[1]]); hi += bytes([b[2], b[3]])
        return bytes(lo + hi)
    tiles = [t4(np.zeros((8, 8)))]; index = {tiles[0]: 0}; maps = []
    for step in range(4):
        a = frame(step)
        for ty in range(CH // 8):
            for tx in range(32):
                blk = a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                if not blk.any() or tx in (15, 16): maps.append(0xFFFF); continue
                t = t4(blk)
                if t not in index: index[t] = len(tiles); tiles.append(t)
                maps.append((544 + index[t]) | (1 << 10))
    assert len(tiles) <= 224
    open('ruden_crowd.til', 'wb').write(b''.join(tiles))
    open('ruden_crowd.map', 'wb').write(b''.join(struct.pack('<H', e) for e in maps))
    return len(tiles)
