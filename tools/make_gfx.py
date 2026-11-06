"""Generuje grafiki PNG dla Super FamiPong (indeksowane, 16 kolorow, indeks 0 = przezroczysty).

Uruchom z katalogu projektu:  python3 tools/make_gfx.py
Portrety generuje osobny skrypt tools/portrait.py (ze zdjecia).
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


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [0] * (w * h)

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y * self.w + x]
        return 0

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, c)


# ---------------------------------------------------------------------------
# Boisko (BG1 w trakcie gry): bandy i przerywana siatka
def make_court():
    cv = Canvas(256, 224)
    cv.rect(0, 44, 256, 48, 1)     # gorna banda y 44..47
    cv.rect(0, 200, 256, 204, 1)   # dolna banda y 200..203
    for y in range(48, 200):
        if ((y - 48) // 4) % 2 == 0:
            cv.put(127, y, 2)
            cv.put(128, y, 2)
    pal = [(0, 0, 0), (255, 255, 255), (136, 136, 136)] + [(0, 0, 0)] * 13
    save_indexed(cv.px, 256, 224, pal, 'court.png')


# ---------------------------------------------------------------------------
# Logo "SUPER FAMIPONG": wlasna pikselowa czcionka 5x7
GLYPHS = {
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'I': ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
}

# indeksy palety logo
L_SHADOW, L_WHITE, L_GRAY = 15, 13, 14
HUES = [  # (jasny, glowny, ciemny) dla czerwieni, zolci, zieleni, niebieskiego
    (1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12),
]
LOGO_PAL = [
    (0, 0, 0),
    (255, 140, 140), (224, 40, 48), (128, 16, 24),     # czerwony
    (255, 240, 150), (248, 200, 24), (160, 104, 0),    # zolty
    (150, 240, 150), (40, 176, 64), (8, 88, 32),       # zielony
    (150, 190, 255), (48, 96, 224), (16, 32, 120),     # niebieski
    (255, 255, 255), (150, 150, 168), (24, 16, 48),    # bialy, szary, cien
]


def draw_text(cv, text, x0, y0, scale, colorize):
    """Rysuje tekst; colorize(i) zwraca (jasny, glowny, ciemny) dla i-tej litery.
    Zwraca maske pikseli kazdej litery do pozniejszego cieniowania."""
    x = x0
    for i, ch in enumerate(text):
        g = GLYPHS[ch]
        light, main, dark = colorize(i)
        gw = len(g[0])
        # najpierw maska litery w powiekszeniu
        mask = set()
        for gy, row in enumerate(g):
            for gx, c in enumerate(row):
                if c == '#':
                    for dy in range(scale):
                        for dx in range(scale):
                            mask.add((x + gx * scale + dx, y0 + gy * scale + dy))
        # cien przesuniety o (2,2)
        for (px, py) in mask:
            for sx, sy in ((2, 2), (1, 2), (2, 1)):
                if (px + sx, py + sy) not in mask and cv.get(px + sx, py + sy) == 0:
                    cv.put(px + sx, py + sy, L_SHADOW)
        # wypelnienie z jasna gorna i ciemna dolna krawedzia
        for (px, py) in mask:
            c = main
            if (px, py - 1) not in mask or (px - 1, py) not in mask and (px, py - 2) not in mask:
                c = light
            if (px, py + 1) not in mask:
                c = dark
            cv.put(px, py, c)
        x += gw * scale + (scale if scale > 2 else 2)
    return x


def text_width(text, scale):
    w = 0
    for i, ch in enumerate(text):
        w += len(GLYPHS[ch][0]) * scale
        if i < len(text) - 1:
            w += scale if scale > 2 else 2
    return w


def make_logo():
    W, H = 192, 48
    cv = Canvas(W, H)
    # duze FAMIPONG, kazda litera w innym kolorze
    big = "FAMIPONG"
    bw = text_width(big, 4)
    draw_text(cv, big, (W - bw - 2) // 2, 18, 4, lambda i: HUES[i % 4])
    # male SUPER na gorze, biale z szarym spodem
    small = "SUPER"
    sw = text_width(small, 2)
    sx = (W - sw - 2) // 2
    draw_text(cv, small, sx, 1, 2, lambda i: (L_WHITE, L_WHITE, L_GRAY))
    save_indexed(cv.px, W, H, LOGO_PAL, 'logo.png')


# ---------------------------------------------------------------------------
# Robot 32x32 jako portret przeciwnika "SUPER FAMICOM"
def make_robot():
    cv = Canvas(32, 32)
    OUT, BODY, LIGHT, EYE, EYEL, RED, MOUTH = 1, 2, 3, 4, 5, 6, 7
    # antena
    cv.rect(15, 2, 17, 7, OUT)
    cv.rect(14, 0, 18, 3, RED)
    # glowa z zaokraglonymi rogami
    cv.rect(5, 7, 27, 27, OUT)
    cv.rect(6, 8, 26, 26, BODY)
    for (x, y) in ((5, 7), (26, 7), (5, 26), (26, 26)):
        cv.put(x, y, 0)
    cv.rect(6, 8, 26, 9, LIGHT)
    cv.rect(6, 8, 7, 26, LIGHT)
    # uszy
    cv.rect(2, 13, 5, 21, OUT)
    cv.rect(27, 13, 30, 21, OUT)
    cv.rect(3, 14, 5, 20, BODY)
    cv.rect(27, 14, 29, 20, BODY)
    # oczy
    for ex in (9, 18):
        cv.rect(ex, 11, ex + 5, 17, OUT)
        cv.rect(ex + 1, 12, ex + 4, 16, EYE)
        cv.put(ex + 1, 12, EYEL)
        cv.put(ex + 2, 12, EYEL)
    # usta z kratka
    cv.rect(9, 19, 23, 24, OUT)
    cv.rect(10, 20, 22, 23, MOUTH)
    for mx in range(12, 22, 3):
        cv.rect(mx, 20, mx + 1, 23, OUT)
    pal = [(0, 0, 0), (24, 24, 40), (144, 152, 176), (208, 216, 232),
           (40, 216, 248), (200, 248, 255), (232, 48, 48), (64, 72, 96)] + [(0, 0, 0)] * 8
    save_indexed(cv.px, 32, 32, pal, 'robot32.png')


# ---------------------------------------------------------------------------
# Sprite'y: kafelek 0 = gora paletki, 1 = srodek paletki, 2 = pilka.
# Dol paletki to kafelek 0 odbity w pionie.
# Kolory: 1 = wypelnienie, 2 = jasna krawedz, 3 = bialy (pilka).
# Paleta z pliku to paletka gracza 1 (bordo); paleta gracza 2 jest w pong.c.
def make_sprites():
    """Sprite'y 8x8: 0 = gora paletki, 1 = srodek paletki, 2 = pilka,
    3..7 = kropki ogona komety (6, 5, 4, 3, 2 px; kolory 1..5 palety sprite'ow nr 4),
    8 = rog ramki kursora (gorny lewy; reszta przez odbicia).
    Kolory w palecie z PNG (gracz 1): 1 = wypelnienie, 2 = jasna krawedz, 3 = bialy."""
    cv = Canvas(72, 8)
    for y in range(8):
        for x in range(8):
            edge = x in (0, 7)
            cv.put(x, y, 2 if (edge or y == 0) else 1)       # gora paletki
            cv.put(8 + x, y, 2 if edge else 1)              # srodek paletki
            corner = (x in (0, 7)) and (y in (0, 7))
            cv.put(16 + x, y, 0 if corner else 3)          # pilka
    for x in (0, 7):  # zaokraglone rogi gory paletki
        cv.put(x, 0, 0)
    for k, size in enumerate((6, 5, 4, 3, 2)):          # ogon komety
        x0 = 24 + 8 * k + (8 - size) // 2
        y0 = (8 - size) // 2
        for y in range(size):
            for x in range(size):
                if size >= 4 and (x in (0, size - 1)) and (y in (0, size - 1)):
                    continue
                cv.put(x0 + x, y0 + y, k + 1)
    for i in range(8):                                   # rog ramki: litera L, 2 px
        for t in range(2):
            cv.put(64 + i, t, 2)
            cv.put(64 + t, i, 2)
    pal = [(0, 0, 0), (150, 20, 50), (225, 100, 125), (255, 255, 255)] + [(0, 0, 0)] * 12
    save_indexed(cv.px, 72, 8, pal, 'sprites.png')


# ---------------------------------------------------------------------------
# Ikony mocy 16x16 (ekran wyboru) i 8x8 (pasek nad boiskiem), paleta BG nr 6
ICON_PAL = [(0, 0, 0), (24, 16, 40), (255, 255, 255), (255, 224, 48), (255, 144, 0),
            (224, 40, 40), (64, 208, 88), (24, 112, 48), (176, 216, 255), (80, 136, 232),
            (150, 150, 170), (80, 80, 96)] + [(0, 0, 0)] * 4
ICON_KEYS = {'.': 0, 'o': 1, 'w': 2, 'y': 3, 'r': 4, 'R': 5, 'g': 6, 'G': 7, 'b': 8, 'B': 9, 'k': 10, 'K': 11}
ICONS = [
    [  # SUPER SHOT: pilka z plomieniem
        "................",
        "................",
        "...RR...........",
        "..RrrR....oooo..",
        ".Rrryyr..owwwwo.",
        "Rrryyyy.owwwwwwo",
        ".Rryyyyyowwwwwwo",
        "Rrryyyyyowwwwwwo",
        ".Rryyyyyowwwwwwo",
        "Rrryyyy.owwwwwwo",
        ".Rrryyr..owwwwo.",
        "..RrrR....oooo..",
        "...RR...........",
        "................",
        "................",
        "................",
    ],
    [  # CURVE: zielona strzalka po luku
        "................",
        "..........ggg...",
        ".........ggggg..",
        "........ggggggg.",
        "..........ggG...",
        "..........ggG...",
        ".........ggG....",
        ".........ggG....",
        "........ggG.....",
        ".......ggG......",
        "......ggG.......",
        "....gggG........",
        "..gggGG.........",
        ".ggGG...........",
        ".gG.............",
        "................",
    ],
    [  # ZIGZAG: zolta blyskawica
        "................",
        ".........yyyyy..",
        "........yyyyr...",
        ".......yyyyr....",
        "......yyyyr.....",
        ".....yyyyyyyyy..",
        "....yyyyyyyyr...",
        "........yyyr....",
        ".......yyyr.....",
        "......yyyr......",
        ".....yyyr.......",
        "....yyr.........",
        "...yr...........",
        "..y.............",
        "................",
        "................",
    ],
    [  # GHOST: duch z przescieradla z wijacym sie ogonkiem
        "................",
        "......bbbb......",
        "....bbbbbbbb....",
        "...bbbbbbbbbb...",
        "...bboobboobb...",
        "...bboobboobb...",
        "...bbbbbbbbbb...",
        "...bbbbooobbb...",
        "...bbbbooobbb...",
        "....bbbbbbbbb...",
        ".....bbbbbbbb...",
        "......bbbbbbB...",
        ".......bbbbbB...",
        "........bbbB....",
        "..........bB....",
        "...........B....",
    ],
    [  # GROW: paletka ze strzalkami
        "................", ".......w........", "......www.......", ".....wwwww......",
        ".......w........", "......RRR.......", "......RrR.......", "......RrR.......",
        "......RrR.......", "......RrR.......", "......RRR.......", ".......w........",
        ".....wwwww......", "......www.......", ".......w........", "................",
    ],
    [  # SPLIT: pilka dzielaca sie na dwie
        "................", "...........ww...", "..........wwww..", "..........wwww..",
        "........y..ww...", "......yy........", ".ww..y..........", "wwwwy...........",
        "wwwwy...........", ".ww..y..........", "......yy........", "........y..ww...",
        "..........wwww..", "..........wwww..", "...........ww...", "................",
    ],
    [  # FORTRESS: mur z blankami
        "................", ".kk..kk..kk..kk.", ".kk..kk..kk..kk.", ".kkkkkkkkkkkkkk.",
        ".kKkkkKkkkKkkkk.", ".kkkkkkkkkkkkkk.", ".kkKkkkKkkkKkkk.", ".kkkkkkkkkkkkkk.",
        ".kKkkkKkkkKkkkk.", ".kkkkkkkkkkkkkk.", ".kkKkkkKkkkKkkk.", ".kkkkkkkkkkkkkk.",
        ".kKkkkKkkkKkkkk.", ".kkkkkkkkkkkkkk.", "................", "................",
    ],
    [  # TWIN: dwie paletki
        "................", "...kkk....kkk...", "...kwk....kwk...", "...kwk....kwk...",
        "...kwk....kwk...", "...kwk....kwk...", "...kwk....kwk...", "...kwk....kwk...",
        "...kwk....kwk...", "...kwk....kwk...", "...kwk....kwk...", "...kwk....kwk...",
        "...kwk....kwk...", "...kkk....kkk...", "................", "................",
    ],
    [  # SWAP: zakrecone strzalki
        "................", "....rrrrrr......", "...rr....rr.....", "..rr......rr....",
        "..r.......rrr...", "..r......rrrrr..", "..r.......rrr...", "................",
        "...bbb.......b..", "..bbbbb......b..", "...bbb.......b..", "....bb......bb..",
        ".....bb....bb...", "......bbbbbb....", "................", "................",
    ],
    [  # SLOW: klepsydra
        "................", "...kkkkkkkkkk...", "....kyyyyyyk....", ".....kyyyyk.....",
        "......kyyk......", ".......kk.......", ".......kk.......", "......k..k......",
        ".....k.yy.k.....", "....k.yyyy.k....", "...kyyyyyyyyk...", "...kkkkkkkkkk...",
        "................", "................", "................", "................",
    ],
    [  # CATCH: podkowa magnesu
        "................", "..RR........bb..", "..RR........bb..", "..RR........bb..",
        "..rr........BB..", "..rr........BB..", "..rr........BB..", "..rr........BB..",
        "..rr........BB..", "...rr......BB...", "....rrr..BBB....", ".....rrrBBB.....",
        "................", "....y......y....", "................", "................",
    ],
    [  # BLINK STRIKE: blysk teleportacji
        "................", ".......b........", ".......b........", "...b...b...b....",
        "....b..b..b.....", ".....bbbbb......", "..bbbbwwwbbbb...", ".....bbbbb......",
        "....b..b..b.....", "...b...b...b....", ".......b........", ".......b........",
        "................", "................", "................", "................",
    ],
    [  # CAMO: przekreslone oko
        "................", "................", "...........R....", ".....kkkkkRk....",
        "...kkwwwwRwwk...", "..kwwwwoRowwwk..", ".kwwwwoRoowwwwk.", "..kwwwRooowwwk..",
        "...kkRwwwwwkk...", ".....Rkkkkk.....", "....R...........", "................",
        "................", "................", "................", "................",
    ],
    [  # CHAOS: spirala
        "................", ".....yyyyyy.....", "...yy......yy...", "..y...rrrr...y..",
        ".y...r....r...y.", ".y..r..gg..r..y.", ".y..r.g..g.r..y.", ".y..r.g....r..y.",
        ".y..r..ggg..r.y.", ".y...r.......y..", "..y...rrrrrr.y..", "...yy.......y...",
        ".....yyyyyyy....", "................", "................", "................",
    ],
    [  # zablokowana moc: znak zapytania w ramce
        "................", "..KKKKKKKKKKKK..", "..K..........K..", "..K...kkkk...K..",
        "..K..kk..kk..K..", "..K......kk..K..", "..K.....kk...K..", "..K....kk....K..",
        "..K....kk....K..", "..K..........K..", "..K....kk....K..", "..K....kk....K..",
        "..K..........K..", "..KKKKKKKKKKKK..", "................", "................",
    ],
]


def make_icons():
    n = len(ICONS)
    big = Canvas(16 * n, 16)
    small = Canvas(8 * n, 8)
    for i, rows in enumerate(ICONS):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row[:16]):
                big.put(16 * i + x, y, ICON_KEYS[ch])
        # wersja 8x8: z kazdego bloku 2x2 bierzemy pierwszy niepusty kolor
        for y in range(8):
            for x in range(8):
                c = 0
                for dy in (0, 1):
                    for dx in (0, 1):
                        v = ICON_KEYS[rows[2 * y + dy][2 * x + dx]]
                        if v and not c:
                            c = v
                small.put(8 * i + x, y, c)
    save_indexed(big.px, 16 * n, 16, ICON_PAL, 'icons.png')
    save_indexed(small.px, 8 * n, 8, ICON_PAL, 'minicons.png')


# ---------------------------------------------------------------------------
# Kafelki paska mocy (paleta BG nr 7): 2 segmenty po 3 px w kafelku 8x8
# 0 = puste, 1 = gracz 1 lewy segment, 2 = gracz 1 oba,
# 3 = gracz 2 prawy segment (pasek gracza 2 laduje sie od prawej), 4 = gracz 2 oba
def make_bar():
    cv = Canvas(40, 8)
    variants = [(1, 1), (2, 1), (2, 2), (1, 3), (3, 3)]
    for t, (a, b) in enumerate(variants):
        for y in range(1, 7):
            for x in range(3):
                cv.put(8 * t + x, y, a)
                cv.put(8 * t + 4 + x, y, b)
    pal = [(0, 0, 0), (64, 64, 80), (205, 60, 90), (80, 140, 240)] + [(0, 0, 0)] * 12
    save_indexed(cv.px, 40, 8, pal, 'bar.png')


if __name__ == '__main__':
    make_court()
    make_logo()
    make_robot()
    make_sprites()
    make_icons()
    make_bar()
    print('ok')

# Nowe logo (Sandbox Escape), AI Agent, Robocik-dzojstik i ekran tytulowy nadpisuja stare grafiki
exec(open('tools/make_title.py').read())
