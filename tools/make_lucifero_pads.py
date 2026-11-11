# Paletki na planszy Lucifero: skosne, wygladzone (jak zatwierdzony podglad), ze sprite'ow 16x16.
# Paletka jezdzi po stalym torze na podlodze (u = 16..24 lewa, 232..240 prawa), wiec wyglad kazdej
# linii obrazu jest staly. Tor dzielimy na 10 pasow po 16 linii (linie 64-223); dla kazdego pasa:
# wariant 0 = pelny, 1-15 = bez wierszy powyzej k (gorny koniec), 16-30 = bez wierszy od k (dolny).
# Kolory (palety sprite'ow 0 i 1): 1 wypelnienie, 12 jasny pas, 13/14/15 brzeg 75/50/25%.
import importlib.util, math, os, sys
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('fl', os.path.join(here, 'make_lucifero_floor.py'))
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
BANDS, L0 = 10, 64
def tile4(px):
    out = bytearray(32)
    for r in range(8):
        for c in range(8):
            v = int(px[r][c]); bit = 7 - c
            out[2 * r] |= (v & 1) << bit; out[2 * r + 1] |= ((v >> 1) & 1) << bit
            out[16 + 2 * r] |= ((v >> 2) & 1) << bit; out[16 + 2 * r + 1] |= ((v >> 3) & 1) << bit
    return out
def band(u0, b, sh={}):   # sh: {wiersz: zwezenie z kazdej strony, czesc szerokosci wiersza} (zaokraglone konce)
    rows = []; spans = []
    for r in range(16):
        Lc = L0 + 16 * b + r + 0.5; s = fl.s_of(Lc)
        spans.append((128 + (u0 - 128) * s, 128 + (u0 + 8 - 128) * s, s))
    X0 = int(math.floor(min(a for a, _, _ in spans))) - 1
    assert max(bb for _, bb, _ in spans) <= X0 + 16, (u0, b)
    spans = [(xl + sh.get(r, 0.0) * (xr - xl), xr - sh.get(r, 0.0) * (xr - xl), s) for r, (xl, xr, s) in enumerate(spans)]
    img = np.zeros((16, 16), int)
    for r, (xl, xr, s) in enumerate(spans):
        for i in range(16):
            x = X0 + i; cov = max(0.0, min(x + 1, xr) - max(x, xl))
            if cov >= 0.875:
                uc = (x + 0.5 - 128) / s + 128 - u0
                img[r, i] = 12 if 1 <= uc < 3.2 else 1
            else:
                img[r, i] = {3: 13, 2: 14, 1: 15}.get(int(round(cov * 4)), 0)
    return X0, img
# Konce paletek zaokraglone jak na innych planszach: skrajny wiersz paletki wezszy z kazdej strony o 30%
# jego szerokosci (ok. 2 px przy zwyklej skali; przy waskiej paletce wiersz nigdy nie znika).
# Warianty pasa (49): 0 pelny; 1-15 gorny koniec w wierszu v; 16-30 dolny koniec (wiersze 0..v-16);
# 31 gorny koniec rowno z poczatkiem pasa; 32 dolny rowno z koncem; 33-48 oba konce w pasie (wiersze 0..v-33).
# (Identyczne w make_lucifero_pads.py i make_lucifero_widen.py.)
VAR, ROUND = 49, 0.3
def variants(u0, b):
    X0, full = band(u0, b)
    out = []
    for v in range(VAR):
        if v == 0:
            m = full.copy()
        elif v <= 15:
            m = band(u0, b, {v: ROUND})[1]; m[:v] = 0
        elif v <= 30:
            L = v - 15; m = band(u0, b, {L - 1: ROUND})[1]; m[L:] = 0
        elif v == 31:
            m = band(u0, b, {0: ROUND})[1]
        elif v == 32:
            m = band(u0, b, {15: ROUND})[1]
        else:
            L = v - 32; m = band(u0, b, {0: ROUND, L - 1: ROUND})[1]; m[L:] = 0
        out.append(m)
    return X0, out
def enc(img):
    return tile4(img[0:8, 0:8]) + tile4(img[0:8, 8:16]) + tile4(img[8:16, 0:8]) + tile4(img[8:16, 8:16])
xs = bytearray()
for side, u0 in enumerate((16, 232)):
    parts = [bytearray(), bytearray()]
    for b in range(BANDS):
        X0, vs = variants(u0, b); xs.append(X0)
        for m in vs:
            parts[b // 5] += enc(m)
    open('luc_pad%d_a.bin' % side, 'wb').write(parts[0]); open('luc_pad%d_b.bin' % side, 'wb').write(parts[1])
open('luc_padx.bin', 'wb').write(xs)
if __name__ == '__main__':
    print('band X0 left:', list(xs[:10]), 'right:', list(xs[10:]), '| bytes per part', len(parts[0]))
