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
def band(u0, b):
    rows = []; spans = []
    for r in range(16):
        Lc = L0 + 16 * b + r + 0.5; s = fl.s_of(Lc)
        spans.append((128 + (u0 - 128) * s, 128 + (u0 + 8 - 128) * s, s))
    X0 = int(math.floor(min(a for a, _, _ in spans))) - 1
    assert max(bb for _, bb, _ in spans) <= X0 + 16, (u0, b)
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
def enc(img):
    return tile4(img[0:8, 0:8]) + tile4(img[0:8, 8:16]) + tile4(img[8:16, 0:8]) + tile4(img[8:16, 8:16])
xs = bytearray()
for side, u0 in enumerate((16, 232)):
    parts = [bytearray(), bytearray()]
    for b in range(BANDS):
        X0, img = band(u0, b); xs.append(X0)
        for v in range(31):
            m = img.copy()
            if 1 <= v <= 15: m[:v] = 0
            elif v >= 16: m[v - 15:] = 0
            parts[b // 5] += enc(m)
    open('luc_pad%d_a.bin' % side, 'wb').write(parts[0]); open('luc_pad%d_b.bin' % side, 'wb').write(parts[1])
open('luc_padx.bin', 'wb').write(xs)
if __name__ == '__main__':
    print('band X0 left:', list(xs[:10]), 'right:', list(xs[10:]), '| bytes per part', len(parts[0]))
