# Konwersja obrazow o znanych, dokladnych kolorach (tekst, interfejs czatu) do kafelkow SNES.
# Kazdy kafelek 8x8 musi miescic sie w jednej z podanych palet. Wspolny slownik kafelkow
# (z odbiciami) pozwala skladac wiele stanow ekranu z tych samych kafelkow.
import numpy as np


import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))          # tools/intro
WORK = _os.path.join(HERE, 'work')                                  # pliki posrednie (generowane)
PROJ = _os.path.abspath(_os.path.join(HERE, '..', '..'))           # katalog gry
_os.makedirs(WORK, exist_ok=True)
def q5(c):
    return tuple(int(round(v / 255 * 31)) for v in c)


class TileSet:
    def __init__(self, bpp=4, first=0):
        self.bpp = bpp
        self.first = first          # numer pierwszego kafelka w VRAM (wzgledem bazy warstwy)
        self.data = bytearray()
        self.seen = {}

    def count(self):
        return len(self.data) // (8 * self.bpp)

    def tile_bytes(self, t):
        b = bytearray(8 * self.bpp)
        for r in range(8):
            for c in range(8):
                v = int(t[r, c]); bit = 7 - c
                for p in range(self.bpp):
                    off = (p // 2) * 16 + 2 * r + (p & 1)
                    b[off] |= ((v >> p) & 1) << bit
        return bytes(b)

    def add(self, t, allow_flip=True):
        """zwraca (numer, flagi odbicia) - nowy kafelek tylko gdy nie ma takiego (takze odbitego)"""
        cand = [(t, 0)]
        if allow_flip:
            cand += [(t[:, ::-1], 0x4000), (t[::-1], 0x8000), (t[::-1, ::-1], 0xC000)]
        for arr, fl in cand:
            k = arr.astype(np.uint8).tobytes()
            if k in self.seen:
                return self.seen[k], fl
        n = self.count()
        self.seen[t.astype(np.uint8).tobytes()] = n
        self.data += self.tile_bytes(t)
        return n, 0


def palettes555(pals):
    return [[q5(c) for c in p] for p in pals]


def convert(img, pals, tileset, pal_ids, transparent, prio=0, rows=None, fixed=None):
    """img: PIL RGB; pals: lista palet (lista kolorow RGB, kolor 0 = przezroczysty, pomijany);
    pal_ids: numery palet SNES odpowiadajace pals; transparent: kolor RGB oznaczajacy przezroczystosc.
    fixed: slownik (wiersz,kolumna) -> numer kafelka (kafelki o stalym miejscu, np. pole wpisywania)
    Zwraca mape (lista slow) dla calego obrazu."""
    a = np.asarray(img.convert('RGB')).astype(int)
    a = np.round(a / 255 * 31).astype(int)
    H, W = a.shape[0] // 8, a.shape[1] // 8
    tr = q5(transparent)
    p5 = palettes555(pals)
    lut = []
    for p in p5:
        d = {}
        for i, c in enumerate(p):
            if i and c not in d:
                d[c] = i
        lut.append(d)
    mp = [0] * (H * W)
    for ty in range(H):
        if rows is not None and ty not in rows:
            continue
        for tx in range(W):
            blk = a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].reshape(64, 3)
            cols = set(map(tuple, blk))
            cols.discard(tr)
            if not cols and not (fixed and (ty, tx) in fixed):
                mp[ty * W + tx] = 0
                continue
            g = None
            for k, d in enumerate(lut):
                if all(c in d for c in cols):
                    g = k
                    break
            if g is None:
                raise ValueError('kafelek %d,%d: kolory spoza palet %s' % (tx, ty, sorted(cols)[:6]))
            idx = np.array([0 if tuple(c) == tr else lut[g][tuple(c)] for c in blk]).reshape(8, 8)
            if fixed and (ty, tx) in fixed:
                num = fixed[(ty, tx)]
                fixed_tiles = getattr(tileset, 'fixed_out', {})
                fixed_tiles[num] = tileset.tile_bytes(idx)
                tileset.fixed_out = fixed_tiles
                fl = 0
            else:
                num, fl = tileset.add(idx)
            mp[ty * W + tx] = (num + tileset.first) | fl | (pal_ids[g] << 10) | (prio << 13)
    return mp


def pal_bytes(pal, n=16):
    out = bytearray()
    cols = list(pal) + [(0, 0, 0)] * (n - len(pal))
    for c in cols[:n]:
        r, g, b = q5(c)
        v = r | (g << 5) | (b << 10)
        out += bytes([v & 255, v >> 8])
    return bytes(out)
