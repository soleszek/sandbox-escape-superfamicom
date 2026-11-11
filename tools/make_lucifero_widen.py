# Rozszerzenie boiska Lucifero (dzialanie mocy 2): kamera C0 -> C1 w 16 krokach (tablice HDMA i
# projekcji w ROM), podloga z rozszerzona strona gracza (skosne bandy) i pasy paletek dla kamery C1.
import importlib.util, os, math
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('fl', os.path.join(here, 'make_lucifero_floor.py'))
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
C0 = (48, 200, 70, 212, 0.72, 1.0); C1 = (24, 224, 60, 214, 0.60, 0.84); W = 24; STEPS = 16
class Cam:
    def __init__(s, vt, vb, Lt, Lb, st, sb):
        r = st / sb; s.LH = (Lt - r * Lb) / (1 - r); s.sb, s.Lb = sb, Lb
        s.B = (vb - vt) / (1 / (Lt - s.LH) - 1 / (Lb - s.LH)); s.A = vb + s.B / (Lb - s.LH)
    def s(s, L): return s.sb * (L - s.LH) / (s.Lb - s.LH)
    def v(s, L): return s.A - s.B / (L - s.LH)
def cam_at(k):
    t = k / (STEPS - 1); t = t * t * (3 - 2 * t)
    return Cam(*[a + (b - a) * t for a, b in zip(C0, C1)])
def hdma_tables(cam):   # gotowe tablice HDMA (M7A i VOFS) jak w luc_setup
    a = bytearray([48, 0x00, 0x01, 0x80 | 127]); v = bytearray([48, 0x00, 0x00, 0x80 | 127])
    vals_a = []; vals_v = []
    for L in range(48, 224):
        aa = int(round(256 / cam.s(L))); vals_a.append(aa)
        vo = (int(round(cam.v(L))) + fl.MAP_ROW0 * 8 - L) & 0x1FFF; vals_v.append(vo)
    for i, (x, y) in enumerate(zip(vals_a, vals_v)):
        if i == 127: a.append(0x80 | 49); v.append(0x80 | 49)
        a += bytes([x & 255, x >> 8]); v += bytes([y & 255, y >> 8])
    a.append(0); v.append(0)
    return a, v
def proj(cam):
    out = bytearray()
    for y in range(256):
        if y >= 240: out.append(0xF0); continue
        L = cam.LH + cam.B / (cam.A - y) if cam.A - y > 0 else 999
        out.append(int(round(L)) if 0 <= L < 224 else 0xF0)
    for L in range(224):
        out.append(min(255, max(1, int(round(256 * cam.s(L))))))
    return out
hd = bytearray(); pj = bytearray()
for k in range(STEPS):
    c = cam_at(k); a, v = hdma_tables(c); hd += a + v; pj += proj(c)
open('luc_cam_hdma.bin', 'wb').write(hd); open('luc_cam_proj.bin', 'wb').write(pj)
# podloga rozszerzona (w = 24 przy lewej bandzie; prawa strona jak zwykle)
tex = np.zeros((224, 256), int)
for v in range(0, 224):
    for u in range(256):
        f = (1 - u / 256) * W; top, bot = 48 - f, 200 + f
        if top - 4 <= v < top or bot <= v < bot + 4:
            tex[v, u] = 10
        elif top <= v < bot:
            k = ((u // 16) * 7 + (v // 16) * 3 + (u // 16) * (v // 16)) % 8
            tex[v, u] = fl.SLABS[k][v % 16, u % 16]
            if abs(u - 127.5) < 1.0 and (v // 4) % 2 == 0: tex[v, u] = 10
base_tiles = {}
t0 = np.frombuffer(open('luc_floor.til', 'rb').read(), np.uint8).reshape(120, 8, 8)
for i in range(59): base_tiles.setdefault(t0[i].tobytes(), i)   # tylko prawdziwe kafelki podlogi (0-58)
new = []; tmap = np.zeros((28, 32), int)
for ty in range(28):
    for tx in range(32):
        t = tex[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
        tt = np.where(t > 0, fl.CG0 + t, 0).astype(np.uint8); key = tt.tobytes()
        if key in base_tiles: tmap[ty, tx] = base_tiles[key]; continue
        base_tiles[key] = 59 + len(new); new.append(tt); tmap[ty, tx] = base_tiles[key]
if __name__ == '__main__':
    print('new tiles for widened floor:', len(new), '-> total', 59 + len(new), 'of 120')
# --- zapis podlogi rozszerzonej: nowe kafelki 4-63 (slowa $0100-$0FFF, w miejscu logo z ekranu
# tytulowego) i 195-255 (za kafelkami podlogi), mapa 28 wierszy x 128 ---
slots = list(range(4, 64)) + list(range(195, 256))
assert len(new) <= len(slots), len(new)
remap = {}
for i in range(len(new)): remap[59 + i] = slots[i]
mp = bytearray([136]) * (28 * 128)
for ty in range(28):
    for tx in range(32):
        t = int(tmap[ty, tx]); mp[ty * 128 + tx] = remap[t] if t >= 59 else 136 + t
lo = bytearray(); hi = bytearray()
for i, tt in enumerate(new):
    (lo if slots[i] < 64 else hi).extend(tt.flatten().tolist())
lo += bytes(60 * 64 - len(lo))
open('luc_wide.map', 'wb').write(mp); open('luc_wide_lo.til', 'wb').write(lo); open('luc_wide_hi.til', 'wb').write(hi)
# --- pasy paletek dla kamery C1 (te same zasady co make_lucifero_pads.py) ---
cam1 = cam_at(STEPS - 1)
def tile4(px):
    out = bytearray(32)
    for r in range(8):
        for c in range(8):
            vv = int(px[r][c]); bit = 7 - c
            out[2 * r] |= (vv & 1) << bit; out[2 * r + 1] |= ((vv >> 1) & 1) << bit
            out[16 + 2 * r] |= ((vv >> 2) & 1) << bit; out[16 + 2 * r + 1] |= ((vv >> 3) & 1) << bit
    return out
def band(u0, b, sh={}):   # sh: {wiersz: zwezenie z kazdej strony, czesc szerokosci wiersza} (zaokraglone konce)
    spans = []
    for r in range(16):
        Lc = 64 + 16 * b + r + 0.5; s = cam1.s(Lc)
        spans.append((128 + (u0 - 128) * s, 128 + (u0 + 8 - 128) * s, s))
    X0 = int(math.floor(min(a for a, _, _ in spans))) - 1
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
xs = bytearray()
for side, u0 in enumerate((16, 232)):
    parts = [bytearray(), bytearray()]
    for b in range(10):
        X0, vs = variants(u0, b); xs.append(X0 & 255)
        for m in vs:
            parts[b // 5] += tile4(m[0:8, 0:8]) + tile4(m[0:8, 8:16]) + tile4(m[8:16, 0:8]) + tile4(m[8:16, 8:16])
    open('luc_wpad%d_a.bin' % side, 'wb').write(parts[0]); open('luc_wpad%d_b.bin' % side, 'wb').write(parts[1])
open('luc_wpadx.bin', 'wb').write(xs)
if __name__ == '__main__':
    print('files ok | hdma bytes', len(hd), 'proj bytes', len(pj), '| lo tiles', len(lo), 'hi tiles', len(hi), '| C1 band X0', list(xs))
