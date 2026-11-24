# Konwersja obrazu RGB 256x224 do grafiki SNES (tryb 1, warstwa 4bpp):
# 8 palet po 15 kolorow + kolor 0 wspolny (tlo), kazdy kafelek 8x8 uzywa jednej palety.
# Wynik: podglad tego, co pokaze konsola, kafelki (4bpp), mapa (32x28 slow), palety (BGR555).
import sys
import numpy as np
from PIL import Image

import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))          # tools/intro
WORK = _os.path.join(HERE, 'work')                                  # pliki posrednie (generowane)
PROJ = _os.path.abspath(_os.path.join(HERE, '..', '..'))           # katalog gry
_os.makedirs(WORK, exist_ok=True)
NPAL, NCOL = 8, 15


def to555(a):
    return (np.clip(np.round(a / 255 * 31), 0, 31)).astype(int)


def from555(c):
    return (c * 255 + 15) // 31


def kmeans(pts, k, w=None, it=12, seed=0):
    pts = np.asarray(pts, float)
    if w is None:
        w = np.ones(len(pts))
    uniq = np.unique(pts, axis=0)
    if len(uniq) <= k:
        return uniq
    rng = np.random.default_rng(seed)
    # k-means++ start
    c = [pts[rng.choice(len(pts), p=w / w.sum())]]
    for _ in range(1, k):
        dd = np.min(((pts[:, None, :] - np.array(c)[None]) ** 2).sum(2), 1) * w
        c.append(pts[rng.choice(len(pts), p=dd / dd.sum())] if dd.sum() > 0 else pts[0])
    c = np.array(c)
    for _ in range(it):
        lab = np.argmin(((pts[:, None, :] - c[None]) ** 2).sum(2), 1)
        for j in range(k):
            m = lab == j
            if m.any():
                c[j] = (pts[m] * w[m, None]).sum(0) / w[m].sum()
    return c


def convert(img, bg=(1, 1, 2), seed=0, npal=NPAL):
    a = to555(np.asarray(img.convert('RGB'), float)).astype(float)
    Ht, Wt = a.shape[0] // 8, a.shape[1] // 8
    tiles = a.reshape(Ht, 8, Wt, 8, 3).transpose(0, 2, 1, 3, 4).reshape(Ht * Wt, 64, 3)
    bgc = np.array(bg, float)
    # start: grupowanie kafelkow po sredniej barwie
    feat = np.array([np.concatenate([t.mean(0), t.std(0)]) for t in tiles])
    grp = np.argmin(((feat[:, None] - kmeans(feat, npal, seed=seed)[None]) ** 2).sum(2), 1)
    pals = None
    for rnd in range(10):
        pals = []
        for g in range(npal):
            px = tiles[grp == g].reshape(-1, 3)
            px = px[((px - bgc) ** 2).sum(1) > 0.5] if len(px) else px
            if len(px) == 0:
                pals.append(np.zeros((NCOL, 3)) + bgc)
                continue
            cols, cnt = np.unique(px, axis=0, return_counts=True)
            p = kmeans(cols, NCOL, w=cnt.astype(float), seed=seed + g)
            p = np.round(p)
            if len(p) < NCOL:
                p = np.vstack([p, np.zeros((NCOL - len(p), 3)) + bgc])
            pals.append(p)
        pals = np.array(pals)
        full = np.concatenate([np.repeat(bgc[None, None], npal, 0), pals], 1)   # 8 x 16 x 3
        err = np.zeros((len(tiles), npal))
        for g in range(npal):
            dd = ((tiles[:, :, None, :] - full[g][None, None]) ** 2).sum(3)
            err[:, g] = dd.min(2).sum(1)
        grp = err.argmin(1)
    full = np.concatenate([np.repeat(bgc[None, None], npal, 0), pals], 1)
    idx = np.zeros((len(tiles), 64), int)
    for t in range(len(tiles)):
        dd = ((tiles[t][:, None, :] - full[grp[t]][None]) ** 2).sum(2)
        idx[t] = dd.argmin(1)
    out = full[grp[:, None], idx]                                     # (n, 64, 3) w 0..31
    prev = out.reshape(Ht, Wt, 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(Ht * 8, Wt * 8, 3)
    prev = Image.fromarray(from555(prev.astype(int)).astype(np.uint8))
    total = float(((out - tiles) ** 2).sum())
    return prev, idx.reshape(len(tiles), 8, 8), grp, full, total


def convert_best(img, tries=6, **kw):
    best = None
    for sd in range(tries):
        r = convert(img, seed=sd * 7 + 1, **kw)
        if best is None or r[4] < best[4]:
            best = r
    return best


def tile_bytes(t):
    b = bytearray(32)
    for r in range(8):
        for c in range(8):
            v = t[r, c]; bit = 7 - c
            b[2 * r] |= (v & 1) << bit; b[2 * r + 1] |= ((v >> 1) & 1) << bit
            b[16 + 2 * r] |= ((v >> 2) & 1) << bit; b[16 + 2 * r + 1] |= ((v >> 3) & 1) << bit
    return bytes(b)


def pack(idx, grp, full, base_tile=0, pal_base=0, prio=0):
    """kafelki bez powtorzen (takze odbicia), mapa 32 kolumny, palety BGR555"""
    seen = {}; tiles = bytearray(); mp = []
    n, Wt = len(idx), 32
    for t in range(n):
        cand = [(idx[t], 0), (idx[t][:, ::-1], 0x4000), (idx[t][::-1], 0x8000), (idx[t][::-1, ::-1], 0xC000)]
        hit = None
        for arr, fl in cand:
            k = arr.tobytes()
            if k in seen:
                hit = seen[k] | fl
                break
        if hit is None:
            num = len(tiles) // 32
            seen[idx[t].tobytes()] = num
            tiles += tile_bytes(idx[t])
            hit = num
        mp.append(((hit & 0x3FF) + base_tile) | (hit & 0xC000) | ((grp[t] + pal_base) << 10) | (prio << 13))
    pal = bytearray()
    for g in range(len(full)):
        for c in full[g]:
            v = int(c[0]) | (int(c[1]) << 5) | (int(c[2]) << 10)
            pal += bytes([v & 255, v >> 8])
    mapb = bytearray()
    for v in mp:
        mapb += bytes([v & 255, (v >> 8) & 255])
    return bytes(tiles), bytes(mapb), bytes(pal)


if __name__ == '__main__':
    img = Image.open(sys.argv[1])
    prev, idx, grp, full, total = convert_best(img)
    t, m, p = pack(idx, grp, full)
    print('blad calkowity %.0f' % total)
    prev.save(sys.argv[2])
    print('kafelkow unikalnych: %d (%d bajtow), palet: %d' % (len(t) // 32, len(t), len(full)))
