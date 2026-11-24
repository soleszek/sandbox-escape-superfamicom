# Ekran producenta przed intro: logo kanalu MaiFlow w kole, pod nim "PRODUCED BY MAIFLOW" i "2026"
# grubymi literami 8x8 w stylu starych gier (gora jasna, dol ciemniejszy) w odcieniach
# niebiesko-fioletowych, z ciemnym cieniem.
import os as _os
from PIL import Image, ImageDraw
HERE = _os.path.dirname(_os.path.abspath(__file__))
LOGO_SIZE = 140   # (bylo 168: mniejsze o ok. 17%)

# wlasna gruba czcionka 7x7 (w polu 8x8): tylko potrzebne znaki
GLYPHS = {
    'P': ["######.", "##...##", "##...##", "######.", "##.....", "##.....", "##....."],
    'R': ["######.", "##...##", "##...##", "######.", "##..##.", "##...##", "##...##"],
    'O': [".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", ".#####."],
    'D': ["#####..", "##..##.", "##...##", "##...##", "##...##", "##..##.", "#####.."],
    'U': ["##...##", "##...##", "##...##", "##...##", "##...##", "##...##", ".#####."],
    'C': [".#####.", "##...##", "##.....", "##.....", "##.....", "##...##", ".#####."],
    'E': ["#######", "##.....", "##.....", "######.", "##.....", "##.....", "#######"],
    'B': ["######.", "##...##", "##...##", "######.", "##...##", "##...##", "######."],
    'Y': ["##...##", "##...##", ".##.##.", "..###..", "...##..", "...##..", "...##.."],
    'M': ["##...##", "###.###", "#######", "##.#.##", "##...##", "##...##", "##...##"],
    'A': ["..###..", ".##.##.", "##...##", "##...##", "#######", "##...##", "##...##"],
    'I': ["######.", "..##...", "..##...", "..##...", "..##...", "..##...", "######."],
    'F': ["#######", "##.....", "##.....", "######.", "##.....", "##.....", "##....."],
    'L': ["##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "#######"],
    'W': ["##...##", "##...##", "##...##", "##.#.##", "#######", "###.###", "##...##"],
    '2': [".#####.", "##...##", ".....##", "..####.", ".##....", "##.....", "#######"],
    '0': [".#####.", "##...##", "##..###", "##.#.##", "###..##", "##...##", ".#####."],
    '6': [".#####.", "##.....", "##.....", "######.", "##...##", "##...##", ".#####."],
    ' ': ["......."] * 7,
}
# kolory wierszy litery: od jasnego niebieskiego u gory do glebokiego fioletu na dole
ROWS = [(206, 214, 255), (156, 168, 255), (150, 160, 255), (120, 112, 250), (132, 76, 232), (126, 62, 222),
        (100, 40, 188)]
SHADOW = (36, 10, 78)


def draw_text(im, x0, y0, text):
    px = im.load()
    for pass_ in (0, 1):                      # najpierw cien (o 1 piksel w prawo i w dol), potem litery
        x = x0
        for ch in text:
            g = GLYPHS[ch]
            for r in range(7):
                for c in range(7):
                    if g[r][c] == '#':
                        if pass_ == 0:
                            px[x + c + 1, y0 + r + 1] = SHADOW
                        else:
                            px[x + c, y0 + r] = ROWS[r]
            x += 8


def logo_screen():
    im = Image.new('RGB', (256, 224), (0, 0, 0))
    src = Image.open(_os.path.join(HERE, 'maiflow_logo.png')).convert('RGB')
    lg = src.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    m = Image.new('L', (LOGO_SIZE * 4, LOGO_SIZE * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, LOGO_SIZE * 4 - 1, LOGO_SIZE * 4 - 1], fill=255)
    m = m.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    top = (224 - (LOGO_SIZE + 10 + 13 + 8)) // 2            # logo i dwa wiersze napisu na srodku ekranu
    im.paste(lg, ((256 - LOGO_SIZE) // 2, top), m)         # logo w kole (jak awatar kanalu)
    for i, s in enumerate(('PRODUCED BY MAIFLOW', '2026')):
        draw_text(im, 128 - len(s) * 4, top + LOGO_SIZE + 10 + i * 13, s)
    return im


if __name__ == '__main__':
    logo_screen().save(_os.path.join(HERE, 'work', 'logo_screen.png'))
