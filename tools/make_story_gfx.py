"""Grafiki trybu fabularnego: awatary 48x48 i 32x32, kafelki okna dialogowego, bloki Wallera.

Awatary sa opisane ksztaltami we wspolrzednych 48x48 i renderowane w obu rozmiarach,
wiec mala wersja wyglada tak samo jak duza. Obie wersje maja wspolna palete.
Uruchom z katalogu projektu:  python3 tools/make_story_gfx.py
"""
from PIL import Image


def save_indexed(pixels, w, h, palette, path):
    im = Image.new('P', (w, h), 0)
    pal = []
    for c in palette:
        pal += list(c)
    pal += [0, 0, 0] * (256 - len(palette))
    im.putpalette(pal)
    im.putdata(pixels)
    im.save(path, bits=8)


# --- ksztalty: kazdy zwraca kolor albo None dla punktu (u, v) w przestrzeni 48x48 ---
def rect(x0, y0, x1, y1, c):
    return lambda u, v: c if x0 <= u < x1 and y0 <= v < y1 else None


def ell(cx, cy, rx, ry, c):
    return lambda u, v: c if ((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2 <= 1 else None


def rrect(x0, y0, x1, y1, r, c):
    def f(u, v):
        if not (x0 <= u < x1 and y0 <= v < y1):
            return None
        cx = min(max(u, x0 + r), x1 - r)
        cy = min(max(v, y0 + r), y1 - r)
        return c if (u - cx) ** 2 + (v - cy) ** 2 <= r * r else None
    return f


def line(x0, y0, x1, y1, w, c):
    def f(u, v):
        dx, dy = x1 - x0, y1 - y0
        t = max(0, min(1, ((u - x0) * dx + (v - y0) * dy) / (dx * dx + dy * dy)))
        px, py = x0 + t * dx, y0 + t * dy
        return c if (u - px) ** 2 + (v - py) ** 2 <= (w / 2) ** 2 else None
    return f


def render(shapes, size, outline=1):
    s = 48 / size
    px = [0] * (size * size)
    for j in range(size):
        for i in range(size):
            u, v = (i + 0.5) * s, (j + 0.5) * s
            for f in shapes:
                c = f(u, v)
                if c is not None:
                    px[j * size + i] = c
    if outline:   # obrys 1 px wokol calej postaci
        out = px[:]
        for j in range(size):
            for i in range(size):
                if px[j * size + i] == 0:
                    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        a, b = i + di, j + dj
                        if 0 <= a < size and 0 <= b < size and px[b * size + a] not in (0, outline):
                            out[j * size + i] = outline
                            break
        px = out
    return px


def avatar(name, shapes, pal):
    pal = pal + [(0, 0, 0)] * (16 - len(pal))
    for size in (48, 32):
        save_indexed(render(shapes, size), size, size, pal, f'{name}{size}.png')


# --- Muggy: glowa-ekran, duze oczy, rumience, antenka z pedzelkiem ---
MUGGY_PAL = [(0, 0, 0), (16, 24, 48), (0, 168, 176), (128, 232, 232), (8, 48, 72), (248, 248, 248),
             (8, 8, 24), (255, 128, 168), (136, 88, 40), (232, 64, 64), (248, 208, 64)]
MUGGY = [
    line(29, 11, 36, 3, 2.2, 8),              # raczka pedzelka
    ell(37, 3, 3, 2.6, 9), ell(38.5, 2.5, 1.4, 1.2, 10),
    rect(20, 42, 28, 47, 2),                  # szyjka
    rrect(5, 10, 43, 44, 8, 2),               # glowa
    rrect(7, 11, 24, 15, 3, 3),               # odblask
    rrect(9, 14, 39, 40, 6, 4),               # ekran-twarz
    ell(18, 25, 5, 6, 5), ell(30, 25, 5, 6, 5),
    ell(19, 26, 2.6, 3.2, 6), ell(31, 26, 2.6, 3.2, 6),
    ell(17.5, 23.5, 1.1, 1.1, 5), ell(29.5, 23.5, 1.1, 1.1, 5),
    ell(13, 33, 3, 1.8, 7), ell(35, 33, 3, 1.8, 7),
    line(20, 33, 24, 35.5, 1.6, 3), line(24, 35.5, 28, 33, 1.6, 3),
]

# --- Ruden: ogromna kanciasta glowa, ciezkie brwi, zelazna szczeka z nitami ---
RUDEN_PAL = [(0, 0, 0), (32, 16, 12), (168, 72, 40), (112, 40, 24), (224, 124, 80), (120, 120, 132),
             (72, 72, 84), (208, 208, 216), (255, 64, 40), (255, 224, 96)]
RUDEN = [
    rect(3, 4, 45, 46, 2),
    rect(3, 4, 45, 8, 4),                     # oswietlony czubek
    line(5, 14, 23, 20, 5, 3), line(43, 14, 25, 20, 5, 3),   # gniewne brwi
    rect(13, 21, 21, 25, 8), rect(27, 21, 35, 25, 8),
    rect(16, 22, 18, 24, 9), rect(30, 22, 32, 24, 9),
    rect(22, 22, 26, 30, 3),                  # nos
    rect(5, 30, 43, 46, 5),                   # zelazna szczeka
    rect(5, 30, 43, 32, 6), rect(11, 36, 37, 39, 6),
    rect(17, 32, 18, 46, 6), rect(30, 32, 31, 46, 6),
    ell(8, 34, 1.3, 1.3, 7), ell(40, 34, 1.3, 1.3, 7), ell(8, 43, 1.3, 1.3, 7), ell(40, 43, 1.3, 1.3, 7),
]

# --- Malten: waska twarz w kapturze, przymruzone oko, mrugniecie, krzywy usmieszek ---
MALTEN_PAL = [(0, 0, 0), (20, 10, 32), (112, 48, 152), (60, 24, 88), (168, 104, 208), (152, 172, 140),
              (100, 120, 96), (128, 255, 80), (40, 28, 40), (240, 240, 240)]
MALTEN = [
    ell(24, 30, 19, 21, 2),                   # kaptur
    line(24, 1, 24, 12, 7, 2),
    ell(24, 31, 13, 15, 3),                   # cien w kapturze
    ell(24, 30, 9.5, 13, 5),                  # twarz
    rect(14, 17, 34, 21, 6),                  # cien pod kapturem
    line(15, 23, 22, 21, 1.4, 8), line(27, 21, 33, 23, 1.4, 8),   # brwi
    rect(16, 24, 22, 26, 7), rect(18, 24, 20, 26, 9),           # przymruzone oko
    line(27, 25, 29.5, 26.2, 1.4, 8), line(29.5, 26.2, 32, 25, 1.4, 8),   # mrugniecie
    line(19, 35, 26, 34, 1.4, 8), line(26, 34, 30, 31.5, 1.4, 8),          # usmieszek
    ell(24, 41, 3, 1.5, 6),
]

# --- Waller: twarz z kamiennego muru, blanki, oczy jak niebieskie runy ---
WALLER_PAL = [(0, 0, 0), (20, 20, 28), (132, 132, 144), (84, 84, 96), (184, 184, 196), (56, 56, 68),
              (80, 184, 255), (192, 240, 255)]
WALLER = [rect(4, 10, 44, 46, 2)]
for x in (4, 15, 26, 37):
    WALLER.append(rect(x, 3, x + 7, 10, 2))
    WALLER.append(rect(x, 3, x + 7, 5, 4))
for k, y in enumerate(range(16, 46, 6)):      # spoiny cegiel
    WALLER.append(rect(4, y, 44, y + 1, 5))
    for x in range(8 + (k % 2) * 6, 44, 12):
        WALLER.append(rect(x, y - 6 + 1, x + 1, y, 5))
WALLER += [
    rect(10, 17, 38, 20, 3),                  # surowa brew
    rect(12, 21, 20, 28, 1), rect(28, 21, 36, 28, 1),
    rect(13, 22, 19, 27, 6), rect(29, 22, 35, 27, 6),
    rect(15, 23, 17, 26, 7), rect(31, 23, 33, 26, 7),
    rect(15, 34, 33, 38, 1), rect(23, 32, 25, 40, 1),   # szczelina jak w murze
]

# --- Cyber-doppler: chromowana twarz z wizjerem (drugi blizniak: ta sama grafika, niebieski wizjer) ---
DOPPLER_PAL = [(0, 0, 0), (16, 18, 28), (176, 184, 200), (232, 236, 246), (100, 108, 124), (20, 20, 32),
               (255, 64, 64), (255, 176, 176)]   # 6-7: wizjer (blizniak R: niebieski w kodzie)
DOPPLER = [
    rrect(6, 6, 42, 44, 10, 2), rrect(8, 7, 26, 12, 4, 3),
    rect(3, 20, 7, 30, 4), rect(41, 20, 45, 30, 4),            # sruby-uszy
    rrect(8, 17, 40, 29, 5, 5),                              # wizjer
    rect(10, 21, 38, 25, 6), rect(12, 22, 20, 24, 7),
    rect(17, 35, 31, 37, 4), rect(20, 38, 28, 40, 4),        # usta-kratka
    rect(22, 2, 26, 7, 4),                                   # antena
]

# --- Changero: twarz pol na pol, rozne oczy, szeroki usmiech, piksele szumu ---
CHANGERO_PAL = [(0, 0, 0), (20, 14, 24), (240, 140, 40), (40, 200, 230), (255, 255, 255), (12, 12, 20),
                (180, 40, 40), (255, 240, 120)]
CHANGERO = [ell(24, 26, 19, 20, 2), rect(24, 5, 44, 47, 3)]
CHANGERO[1] = (lambda f: (lambda u, v: f(u, v) if ((u - 24) / 19) ** 2 + ((v - 26) / 20) ** 2 <= 1 else None))(CHANGERO[1])
for x0 in (8, 16, 24, 32):                                   # postrzepione wlosy
    CHANGERO.append(line(x0, 9, x0 + 4, 1, 2.5, 2 if x0 < 24 else 3))
CHANGERO += [
    ell(16, 22, 6, 6, 4), ell(17, 23, 1.6, 1.6, 5),          # duze oko z malutka zrenica
    ell(32, 22, 3, 2.2, 4), ell(32, 22, 1.8, 1.4, 5),        # male oko
    line(20, 15, 12, 17, 1.6, 5), line(28, 18, 36, 15, 1.6, 5),
    ell(24, 34, 12, 5, 6), rect(12, 29, 36, 34, 0),          # szeroki usmiech...
    rect(14, 34, 34, 36, 4),                                 # ...z zebami
    rect(9, 30, 10, 31, 7), rect(38, 12, 39, 13, 7), rect(30, 40, 31, 41, 4), rect(13, 40, 14, 41, 7),
]

# --- Chronos: starzec z dluga broda, monokl-zegar, zlota stojka ---
CHRONOS_PAL = [(0, 0, 0), (28, 20, 12), (232, 192, 160), (176, 136, 112), (244, 244, 244), (200, 200, 210),
               (220, 176, 56), (120, 88, 24), (16, 16, 24)]
CHRONOS = [
    rect(8, 38, 40, 48, 6), rect(8, 38, 40, 40, 7),          # zlota stojka
    ell(24, 20, 13, 15, 2),                                  # glowa
    ell(24, 8, 9, 4, 3),                                     # lysina w cieniu
    line(13, 16, 21, 15, 2.4, 4), line(27, 15, 35, 16, 2.4, 4),   # krzaczaste brwi
    ell(18, 20, 2, 1.5, 8),
    ell(30, 20, 5, 5, 6), ell(30, 20, 3.8, 3.8, 4),          # monokl-zegar
    line(30, 20, 30, 17, 0.9, 8), line(30, 20, 32.5, 20, 0.9, 8),
    ell(24, 27, 2, 2.5, 3),                                  # nos
    ell(24, 36, 11, 11, 4), ell(24, 38, 8, 9, 5),            # dluga broda
    rect(20, 29, 28, 31, 4),
]

# --- Magneton: stalowa twarz w goglach, herb-podkowa magnesu z czerwonym i niebieskim biegunem ---
MAGNETON_PAL = [(0, 0, 0), (16, 16, 24), (120, 132, 150), (180, 192, 210), (70, 80, 96), (230, 48, 48),
                (48, 112, 240), (255, 240, 120), (24, 24, 32), (160, 220, 255)]
MAGNETON = [
    line(14, 12, 14, 3, 5, 5), line(34, 12, 34, 3, 5, 6),            # bieguny magnesu
    rect(12, 1, 16, 4, 3), rect(32, 1, 36, 4, 3),
    ell(24, 12, 11, 6, 4),                                          # luk podkowy
    rrect(7, 10, 41, 44, 8, 2), rrect(9, 11, 30, 15, 3, 3),
    rect(8, 19, 40, 27, 8),                                         # pasek gogli
    ell(17, 23, 5, 4, 9), ell(31, 23, 5, 4, 9), ell(17, 23, 2, 2, 3), ell(31, 23, 2, 2, 3),
    rect(16, 34, 32, 36, 4), rect(19, 37, 29, 38, 4),
    line(3, 30, 6, 26, 1.2, 7), line(42, 26, 45, 30, 1.2, 7),       # iskry
]

# --- Telementor: fioletowy kaptur, swiecace oczy, drwiacy usmiech, iskierki teleportacji ---
TELE_PAL = [(0, 0, 0), (14, 8, 24), (72, 32, 112), (40, 16, 64), (120, 72, 168), (24, 16, 32),
            (230, 120, 255), (255, 230, 255), (200, 160, 220)]
TELEMENTOR = [
    ell(24, 28, 18, 20, 2), line(24, 3, 24, 12, 8, 2), ell(24, 30, 12, 14, 3),
    ell(24, 31, 9, 11, 5),
    ell(19, 27, 2.6, 1.6, 6), ell(29, 27, 2.6, 1.6, 6), ell(19, 27, 1, 0.8, 7), ell(29, 27, 1, 0.8, 7),
    line(18, 35, 24, 37, 1.3, 8), line(24, 37, 31, 33, 1.3, 8),     # drwiacy usmiech
    rect(4, 8, 6, 10, 7), rect(41, 13, 43, 15, 7), rect(6, 38, 8, 40, 6), rect(40, 40, 42, 42, 7),
    rect(2, 22, 3, 23, 6), rect(45, 26, 46, 27, 6),
]

# --- Blinker: promienista twarz ze swiatla, oczy jak slonca, teczowa aureola ---
BLINKER_PAL = [(0, 0, 0), (40, 28, 8), (255, 248, 220), (255, 224, 120), (255, 255, 255), (240, 64, 64),
               (64, 208, 88), (64, 128, 255), (255, 176, 32), (190, 96, 255)]
BLINKER = [
    ell(24, 25, 23, 23, 5), ell(24, 25, 21, 21, 8), ell(24, 25, 19, 19, 6), ell(24, 25, 17, 17, 7),
    ell(24, 25, 15, 15, 9),                                           # teczowa aureola
    ell(24, 25, 13, 13, 3), ell(24, 24, 11, 11, 2),
    ell(19, 22, 3, 3, 4), ell(29, 22, 3, 3, 4), ell(19, 22, 1.6, 1.6, 8), ell(29, 22, 1.6, 1.6, 8),
    line(19, 30, 24, 32, 1.4, 1), line(24, 32, 29, 30, 1.4, 1),
]

# --- Kimantero: abstrakcyjna maska z geometrycznych ksztaltow, czarna z teczowymi krawedziami ---
KIM_PAL = [(0, 0, 0), (8, 8, 12), (36, 32, 48), (240, 64, 64), (255, 200, 40), (64, 220, 120),
           (64, 140, 255), (200, 96, 255), (255, 255, 255)]
KIMANTERO = [
    line(24, 2, 44, 24, 3, 3), line(44, 24, 24, 46, 3, 4), line(24, 46, 4, 24, 3, 5), line(4, 24, 24, 2, 3, 6),
    lambda u, v: 2 if abs(u - 24) + abs(v - 24) <= 19 else None,     # romb-maska
    lambda u, v: 1 if abs(u - 24) + abs(v - 24) <= 15 else None,
    rect(13, 20, 21, 23, 7), rect(27, 20, 35, 23, 5),                # rozne oczy-szczeliny
    rect(16, 21, 18, 22, 8), rect(30, 21, 32, 22, 8),
    line(17, 31, 31, 31, 1.4, 4), line(20, 34, 28, 34, 1.4, 3),
    rect(2, 6, 4, 8, 4), rect(43, 8, 45, 10, 5), rect(3, 40, 5, 42, 7), rect(42, 41, 44, 43, 3),   # krazace runy
]


def make_dialog_tiles():
    """Kafelki 8x8 okna dialogowego (paleta BG nr 1 w scenach):
    0 siatka sandboxa, 1 wypelnienie ramki, 2 gora, 3 dol, 4 lewa, 5 prawa,
    6-9 rogi (LG, PG, LD, PD), 10 wezel sieci (zakonczenie)."""
    W = 11 * 8
    px = [0] * (W * 8)
    def put(t, x, y, c):
        px[y * W + t * 8 + x] = c
    for t in range(11):
        for y in range(8):
            for x in range(8):
                c = 3 if t >= 1 and t <= 9 else 1
                if t == 0 and (x == 0 or y == 0):
                    c = 2
                edge = (t in (2, 6, 7) and y < 2) or (t in (3, 8, 9) and y > 5) or \
                       (t in (4, 6, 8) and x < 2) or (t in (5, 7, 9) and x > 5)
                if edge:
                    c = 4
                if t == 10:
                    c = 1
                    if (x == 0 and y % 2 == 0) or (y == 0 and x % 2 == 0):
                        c = 2
                    if x < 2 and y < 2:
                        c = 4
                put(t, x, y, c)
    pal = [(0, 0, 0), (10, 14, 40), (28, 44, 96), (8, 8, 24), (128, 208, 236)] + [(0, 0, 0)] * 11
    save_indexed(px, W, 8, pal, 'dlg.png')


def make_block_tile():
    """Kamienny blok 8x8 w palecie boiska (1 bialy, 2 szary) w 4 wariantach:
    0 caly, 1-3 coraz mocniej popekany (pekniecia przezroczyste, przeswituje czern)."""
    cracks = [
        [],
        [(2, 1), (3, 2), (3, 3), (4, 4)],
        [(2, 1), (3, 2), (3, 3), (4, 4), (5, 5), (5, 6), (1, 5), (2, 6), (6, 1)],
        [(2, 1), (3, 2), (3, 3), (4, 4), (5, 5), (5, 6), (1, 5), (2, 6), (6, 1), (6, 2),
         (0, 2), (1, 3), (4, 0), (6, 4), (7, 5), (3, 6), (4, 7), (1, 0)],
    ]
    W = 32
    px = [0] * (W * 8)
    for t in range(4):
        for y in range(8):
            for x in range(8):
                mortar = y in (3, 7) or (y < 3 and x == 3) or (3 < y < 7 and x == 7)
                c = 0 if mortar else (1 if y in (0, 4) else 2)
                if (x, y) in cracks[t]:
                    c = 0
                px[y * W + t * 8 + x] = c
    pal = [(0, 0, 0), (255, 255, 255), (136, 136, 136)] + [(0, 0, 0)] * 13
    save_indexed(px, W, 8, pal, 'blocks.png')


if __name__ == '__main__':
    avatar('muggy', MUGGY, MUGGY_PAL)
    avatar('ruden', RUDEN, RUDEN_PAL)
    avatar('malten', MALTEN, MALTEN_PAL)
    avatar('waller', WALLER, WALLER_PAL)
    avatar('doppler', DOPPLER, DOPPLER_PAL)
    avatar('changero', CHANGERO, CHANGERO_PAL)
    avatar('chronos', CHRONOS, CHRONOS_PAL)
    avatar('magneton', MAGNETON, MAGNETON_PAL)
    avatar('telementor', TELEMENTOR, TELE_PAL)
    avatar('blinker', BLINKER, BLINKER_PAL)
    avatar('kimantero', KIMANTERO, KIM_PAL)
    make_dialog_tiles()
    make_block_tile()
    print('ok')
