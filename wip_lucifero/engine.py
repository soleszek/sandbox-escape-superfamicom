# Silnik podgladow planszy Lucifero (te same wzory perspektywy co gra), obraz 256x224 bez powiekszania.
import numpy as np, importlib.util, math
from PIL import Image
spec = importlib.util.spec_from_file_location('fl', '/tmp/prev/make_lucifero_floor.py'); fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
PAL = np.array(fl.PAL, np.uint8)
HUD = np.array(Image.open('/tmp/luc_s9x3.png').convert('RGB'))[::2, ::2][:48]
# tekstura plyt na calej wysokosci (do rozszerzonego boiska); obszar boiska wyznacza maska
TEX = np.zeros((256, 256), int)
for v in range(256):
    for u in range(256):
        k = ((u // 16) * 7 + (v // 16) * 3 + (u // 16) * (v // 16)) % 8
        TEX[v, u] = fl.SLABS[k][v % 16, u % 16]
class Cam:   # vt/vb: gora/dol boiska (y pola), Lt/Lb: ich linie ekranu, st/sb: skala pozioma
    def __init__(s, vt, vb, Lt, Lb, st, sb):
        r = st / sb; s.LH = (Lt - r * Lb) / (1 - r); s.sb, s.Lb = sb, Lb
        s.B = (vb - vt) / (1 / (Lt - s.LH) - 1 / (Lb - s.LH)); s.A = vb + s.B / (Lb - s.LH)
    def s(s, L): return s.sb * (L - s.LH) / (s.Lb - s.LH)
    def v(s, L): return s.A - s.B / (L - s.LH)
    def L(s, v): return s.LH + s.B / (s.A - v)
    def x(s, u, L): return 128 + (u - 128) * s.s(L)
CAM0 = Cam(48, 200, 70, 212, 0.72, 1.0)   # kamera gry
def lerp_cam(c0p, c1p, t): return Cam(*[a + (b - a) * t for a, b in zip(c0p, c1p)])
def floor(cam, w=0.0):   # w: rozszerzenie strony gracza (px pola przy lewej bandzie)
    img = np.zeros((224, 256, 3), np.uint8); img[:48] = HUD
    X = np.arange(256)
    for L in range(48, 224):
        s = cam.s(L + 0.5); v = cam.v(L + 0.5)
        u = (X + 0.5 - 128) / s + 128
        ui = np.floor(u).astype(int); vi = int(math.floor(v))
        if vi < 0 or vi > 251: continue
        ok = (ui >= 0) & (ui < 256)
        f = np.clip(1 - u / 256, 0, 1) * w
        top = 48 - f; bot = 200 + f
        inside = ok & (v >= top) & (v < bot)
        band = ok & (((v >= top - 4) & (v < top)) | ((v >= bot) & (v < bot + 4)))
        row = np.zeros(256, int)
        row[inside] = TEX[vi, np.clip(ui[inside], 0, 255)]
        cl = inside & ((np.abs(u - 128) < 1.0)) & ((vi // 4) % 2 == 0); row[cl] = 10
        row[band] = 10
        img[L] = PAL[row]
    return img
GRAY = np.array([56, 56, 59], float)
P1 = (np.array([0, 160, 170.]), np.array([130, 235, 240.]))
P2 = (np.array([140, 20, 18.]), np.array([230, 70, 45.]))
def paddle(img, cam, u0, y, h, col):
    fill, lit = col
    for L in range(int(cam.L(y)) - 1, int(cam.L(y + h)) + 2):
        if L < 48 or L > 223: continue
        vc = cam.v(L + 0.5)
        if not (y <= vc < y + h): continue
        s = cam.s(L + 0.5); xl = cam.x(u0, L + 0.5); xr = cam.x(u0 + 8, L + 0.5)
        for x in range(int(xl) - 1, int(xr) + 2):
            if x < 0 or x > 255: continue
            cov = max(0.0, min(x + 1, xr) - max(x, xl))
            if cov >= 0.875:
                uc = (x + 0.5 - 128) / s + 128 - u0
                img[L, x] = (lit if 1 <= uc < 3.2 else fill).astype(np.uint8)
            else:
                q = round(cov * 4) / 4
                if q > 0: img[L, x] = (q * fill + (1 - q) * GRAY).astype(np.uint8)
def ball(img, cam, x, y):
    L = int(round(cam.L(y))); X = int(round(cam.x(x, L)))
    if 48 <= L < 218: img[L:L + 6, max(0, X):X + 6] = 255
def save_gif(frames, path, ms=30):
    ims = [Image.fromarray(f) for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, optimize=False)
