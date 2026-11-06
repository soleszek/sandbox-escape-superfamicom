# Pochodnie na arenie Wallera: uchwyt + 8 klatek plomienia (8x16) tworzacych plynny cykl:
# kolysanie na boki, wzrost i opadanie, czasem odrywajacy sie jezyk ognia.
# Kolory palety boiska: 3 zelazo, 4 drewno, 5 ciemna czerwien, 6 pomarancz, 7 zolty, 12 jadro.
import math
import numpy as np
def tile4bpp(px):
    lo = bytearray(); hi = bytearray()
    for r in range(8):
        b = [0, 0, 0, 0]
        for c in range(8):
            v = int(px[r][c])
            for k in range(4): b[k] |= ((v >> k) & 1) << (7 - c)
        lo += bytes([b[0], b[1]]); hi += bytes([b[2], b[3]])
    return bytes(lo + hi)
FRAMES = 8
# 8 roznych, niewiele rozniacych sie ksztaltow (drganie plomienia); gra wybiera je w przypadkowej
# kolejnosci i w nierownych odstepach, wiec plomien nie kolysze sie rytmicznie.
SHAPES = [(12.0, 0.2, 3.4, 0), (12.8, -0.3, 3.3, 0), (11.4, 0.4, 3.5, 0), (13.4, 0.1, 3.2, 1),
          (12.3, -0.5, 3.4, 0), (11.8, 0.6, 3.3, 0), (13.0, -0.2, 3.5, 1), (12.5, 0.3, 3.2, 0)]
def flame(k):
    hgt, lean, wid, lick = SHAPES[k]
    a = np.zeros((16, 8), int)
    for y in range(16):
        u = (15 - y) / hgt   # 0 u podstawy, 1 na czubku
        if u > 1: continue
        w = wid * (1 - u) ** 0.8
        cx = 3.5 + lean * u * u
        for x in range(8):
            dd = abs(x - cx) / max(w, 0.01)
            if dd < 1:
                a[y, x] = 12 if (dd < 0.35 and u < 0.45) else (7 if dd < 0.6 and u < 0.7 else (6 if dd < 0.85 else 5))
    if lick:   # odrywajacy sie jezyk ognia nad czubkiem
        top = int(round(15 - hgt)) - 2; tx = int(round(3.5 + lean))
        if 0 <= top < 16 and 0 <= tx < 8:
            a[top, tx] = 6
            if top - 1 >= 0: a[top - 1, tx] = 5
    return a
def write_torches():
    br = np.zeros((8, 8), int)   # uchwyt: zelazna obejma i drewniany trzonek
    br[0:6, 3:5] = 4; br[0, 2:6] = 3; br[1, 2:6] = 3; br[5:7, 2:6] = 3; br[6, 1] = 3; br[6, 6] = 3
    tiles = [tile4bpp(br)]
    for f in range(FRAMES):
        fa = flame(f)
        tiles += [tile4bpp(fa[0:8]), tile4bpp(fa[8:16])]
    open('waller_torch.til', 'wb').write(b''.join(tiles))
    return len(tiles)
if __name__ == '__main__':
    from PIL import Image
    pal = {0: (40, 30, 40), 5: (150, 30, 10), 6: (240, 120, 24), 7: (255, 214, 64), 12: (255, 250, 210)}
    row = []
    for f in range(FRAMES):
        fa = flame(f); img = np.zeros((16, 8, 3), np.uint8)
        for k, c in pal.items(): img[fa == k] = c
        row += [img, np.full((16, 2, 3), 80, np.uint8)]
    Image.fromarray(np.hstack(row)).resize((len(row) // 2 * 10 * 8, 16 * 8), Image.NEAREST).save('/tmp/torch_frames.png')
    print('ok')
