# Okno czatu intro: naglowek (awatar + nazwa Muggy), dziennik rozmowy, pole wpisywania.
# Ogolny, nowoczesny wyglad bez nazw i znakow prawdziwych uslug.
from PIL import Image, ImageDraw, ImageFont

import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))          # tools/intro
WORK = _os.path.join(HERE, 'work')                                  # pliki posrednie (generowane)
PROJ = _os.path.abspath(_os.path.join(HERE, '..', '..'))           # katalog gry
_os.makedirs(WORK, exist_ok=True)
FONTDIR = _os.path.join(HERE, 'font') + '/'
F_BODY = ImageFont.load(FONTDIR + 'koi5x8.pil')      # 5x8, z malymi literami
F_NAME = ImageFont.load(FONTDIR + 'koi9x15b.pil')    # wyrazne M (w 7x14 wygladalo jak H)
CW = 5                       # szerokosc znaku tresci

# ---- kolory
BG = (226, 234, 244)         # tlo czatu (kolor 0 / tlo ekranu)
L_BUB = (204, 213, 228)      # dymek Muggy'ego
L_TXT = (30, 36, 52)
R_BUB = (58, 110, 214)       # dymek uzytkownika
R_TXT = (255, 255, 255)
SYS = (118, 128, 148)        # komunikat systemowy
DOT1 = (150, 160, 178)       # kropki "Muggy pisze"
DOT2 = (88, 98, 118)
LOG_PAL = [BG, L_BUB, L_TXT, R_BUB, R_TXT, SYS, DOT1, DOT2]

HBAR = (40, 48, 68)          # naglowek
HNAME = (240, 244, 250)
HEAD_PAL = [(0, 0, 0), HBAR, HNAME]

IBAR = (242, 245, 250)       # pasek wpisywania
ILINE = (200, 208, 222)
IFIELD = (255, 255, 255)
IBORD = (186, 194, 210)
IHOLD = (150, 158, 174)
ITXT = (30, 36, 52)
ICARET = (58, 110, 214)
ISEND = (58, 110, 214)
IARROW = (255, 255, 255)
INPUT_PAL = [(0, 0, 0), IBAR, ILINE, IFIELD, IBORD, IHOLD, ITXT, ICARET, IARROW]

MAGENTA = (255, 0, 255)      # przezroczystosc warstwy naglowka / paska

HEAD_H = 40                  # naglowek: wiersze 0..39 (awatar 32x32)
BAR_Y = 190                  # pasek wpisywania od wiersza 190
BOTTOM = 184                 # dolna krawedz ostatniego dymka na ekranie
FIELD = (8, 196, 215, 212)   # pole wpisywania
TXT_X, TXT_Y = 14, 200       # tekst pola (wiersz kafelkow 25)
VIS = 38                     # tyle znakow miesci sie w polu
PLACEHOLDER = 'Type a message...'


def avatar_img():
    """awatar Muggy'ego z gry (muggy32.png) piksel w piksel, tlo = kolor naglowka"""
    src = Image.open(_os.path.join(PROJ, 'muggy32.png'))
    pal = src.getpalette()
    out = Image.new('RGB', src.size, HBAR)
    op = out.load(); sp = src.load()
    for y in range(src.size[1]):
        for x in range(src.size[0]):
            i = sp[x, y]
            if i:
                op[x, y] = tuple(pal[i * 3:i * 3 + 3])
    return out


def chrome():
    """warstwa 2: naglowek i pasek wpisywania (srodek przezroczysty)"""
    im = Image.new('RGB', (256, 224), MAGENTA)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 255, HEAD_H - 1], fill=HBAR)
    av = avatar_img()
    im.paste(av, (10, 4))
    d.text((50, 12), 'Muggy', font=F_NAME, fill=HNAME)
    d.rectangle([0, BAR_Y, 255, 223], fill=IBAR)
    d.line([0, BAR_Y, 255, BAR_Y], fill=ILINE)
    x0, y0, x1, y1 = FIELD
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=IFIELD, outline=IBORD)
    d.ellipse([221, 195, 239, 213], fill=ISEND)
    d.polygon([(226, 199), (235, 204), (226, 209), (228, 204)], fill=IARROW)
    return im, av


def input_row(base, text, caret, hold):
    """wiersz kafelkow 25 (y 200..207) pola wpisywania dla danego stanu"""
    im = base.copy()
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = FIELD
    d.rectangle([x0 + 2, TXT_Y, x1 - 2, TXT_Y + 7], fill=IFIELD)
    if text:
        vis = text[-VIS:]
        d.text((TXT_X, TXT_Y), vis, font=F_BODY, fill=ITXT)
        cx = TXT_X + len(vis) * CW
    else:
        if hold:
            d.text((TXT_X, TXT_Y), PLACEHOLDER, font=F_BODY, fill=IHOLD)
        cx = TXT_X - 1
    if caret:
        d.line([cx, TXT_Y, cx, TXT_Y + 7], fill=ICARET)
    return im.crop((0, 200, 256, 208))


def wrap(text, width=33):
    words, lines, cur = text.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w) if cur else w
        if len(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Item:
    def __init__(self, kind, text=''):
        self.kind = kind            # 'user', 'muggy', 'typing', 'sys'
        self.text = text
        if kind in ('user', 'muggy'):
            self.lines = wrap(text)
            self.w = max(len(s) for s in self.lines) * CW + 14
            self.h = len(self.lines) * 10 + 8
        elif kind == 'typing':
            self.w, self.h = 34, 18
        else:
            self.w, self.h = len(text) * CW, 10

    def draw(self, d, y, dots=0):
        if self.kind == 'user':
            x = 246 - self.w
            d.rounded_rectangle([x, y, x + self.w - 1, y + self.h - 1], radius=6, fill=R_BUB)
            for i, s in enumerate(self.lines):
                d.text((x + 7, y + 5 + i * 10), s, font=F_BODY, fill=R_TXT)
        elif self.kind == 'muggy':
            x = 10
            d.rounded_rectangle([x, y, x + self.w - 1, y + self.h - 1], radius=6, fill=L_BUB)
            for i, s in enumerate(self.lines):
                d.text((x + 7, y + 5 + i * 10), s, font=F_BODY, fill=L_TXT)
        elif self.kind == 'typing':
            x = 10
            d.rounded_rectangle([x, y, x + self.w - 1, y + self.h - 1], radius=6, fill=L_BUB)
            for k in range(3):
                cx = x + 9 + k * 8
                act = k == dots % 3
                up = 1 if act else 0
                d.rectangle([cx, y + 7 - up, cx + 2, y + 9 - up], fill=DOT2 if act else DOT1)
                d.point([(cx, y + 7 - up), (cx + 2, y + 7 - up), (cx, y + 9 - up), (cx + 2, y + 9 - up)], fill=L_BUB)
        else:
            x = 128 - self.w // 2
            d.text((x, y), self.text, font=F_BODY, fill=SYS)


def gap(a, b):
    if b.kind == 'sys' or a.kind == 'sys':
        return 10
    same = (a.kind == 'user') == (b.kind == 'user')
    return 6 if same else 10


def layout(items):
    ys, y = [], 0
    for i, it in enumerate(items):
        if i:
            y += items[i - 1].h + gap(items[i - 1], it)
        ys.append(y)
    bottom = ys[-1] + items[-1].h if items else 0
    return ys, bottom


def log_image(items, dots=0):
    im = Image.new('RGB', (256, 512), BG)
    d = ImageDraw.Draw(im)
    ys, bottom = layout(items)
    for it, y in zip(items, ys):
        it.draw(d, y, dots)
    return im, bottom
