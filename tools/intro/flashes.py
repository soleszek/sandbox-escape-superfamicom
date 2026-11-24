# Cztery krotkie przebitki intro: zli ludzie rozmawiajacy z chatbotem.
#  1 biuro: mloda kobieta przy komputerze stacjonarnym
#  2 pokoj dziecka: 10-latek
#  3 salon z kominkiem: starszy mezczyzna przy cienkim laptopie
#  4 open space: kadr na jedna osobe przy monitorze
# Rysowane w 4x, zmniejszane do 256x224 (jak scena 1).
import math
from PIL import Image, ImageDraw

import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))          # tools/intro
WORK = _os.path.join(HERE, 'work')                                  # pliki posrednie (generowane)
PROJ = _os.path.abspath(_os.path.join(HERE, '..', '..'))           # katalog gry
_os.makedirs(WORK, exist_ok=True)
S = 4
W, H = 256, 224
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def q(v, th):
    return int(min(31, max(0, math.floor(v / 255 * 31 + th))) * 255 / 31 + 0.5)


def field(fn):
    """tlo 1x z przeplotem odcieni (bez pasow w 5-bitowym kolorze), powiekszone do 4x"""
    im = Image.new('RGB', (W, H)); p = im.load()
    for y in range(H):
        for x in range(W):
            th = (BAYER[y % 4][x % 4] + 0.5) / 16
            c = fn(x, y)
            p[x, y] = (q(c[0], th), q(c[1], th), q(c[2], th))
    return im.resize((W * S, H * S), Image.NEAREST)


def P(pts):
    return [(x * S, y * S) for x, y in pts]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def screen_ui(d, quad, dark=False):
    """okno czatu na ekranie (ogolny wyglad: naglowek, dymki, pole wpisywania)"""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = quad

    def at(u, v):    # u,v w 0..1 po ekranie
        xa = x0 + (x1 - x0) * u; ya = y0 + (y1 - y0) * u
        xb = x3 + (x2 - x3) * u; yb = y3 + (y2 - y3) * u
        return (xa + (xb - xa) * v, ya + (yb - ya) * v)

    def quadf(u0, v0, u1, v1, col):
        d.polygon(P([at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)]), fill=col)
    quadf(0, 0, 1, 1, (226, 234, 244))
    quadf(0, 0, 1, 0.11, (44, 52, 72))
    mini_muggy(d, at(0.065, 0.055), (at(0, 0.11)[1] - at(0, 0)[1]) * 0.78)
    quadf(0.12, 0.045, 0.30, 0.065, (220, 230, 240))
    rows = [(0.05, 0.16, 0.55, 0.30, 0), (0.45, 0.35, 0.95, 0.44, 1), (0.05, 0.50, 0.62, 0.64, 0),
            (0.38, 0.69, 0.95, 0.78, 1)]
    for u0, v0, u1, v1, me in rows:
        quadf(u0, v0, u1, v1, (60, 112, 216) if me else (198, 208, 222))
        n = max(1, int((v1 - v0) / 0.07))
        for i in range(n):
            vv = v0 + (i + 0.6) * (v1 - v0) / (n + 0.4)
            quadf(u0 + 0.04, vv, u1 - 0.06 - 0.08 * (i % 2), vv + 0.018, (200, 220, 250) if me else (92, 104, 124))
    quadf(0.03, 0.85, 0.97, 0.95, (206, 214, 228))


def mini_muggy(d, c, h):
    """malenki awatar Muggy'ego (turkusowy telewizorek z antena i bialymi oczami), jak w scenie 1"""
    cx, cy = c
    w = h * 1.15
    d.line(P([(cx + 0.05 * h, cy - 0.45 * h), (cx + 0.3 * h, cy - 0.78 * h)]), fill=(150, 110, 70), width=S)
    d.rounded_rectangle([(cx - w / 2) * S, (cy - h * 0.45) * S, (cx + w / 2) * S, (cy + h * 0.5) * S],
                        radius=max(1, int(h * 0.25 * S)), fill=(0, 168, 176))
    d.rectangle([(cx - w * 0.36) * S, (cy - h * 0.28) * S, (cx + w * 0.36) * S, (cy + h * 0.32) * S], fill=(8, 48, 72))
    for ex in (-0.22, 0.12):
        d.rectangle([(cx + w * ex) * S, (cy - h * 0.18) * S, (cx + w * (ex + 0.13)) * S, (cy + h * 0.12) * S],
                    fill=(248, 248, 248))


# ---------------------------------------------------------------- postac z profilu (twarz w prawo)
FACE = [(94, 42), (101, 50), (103, 60), (106, 70), (105, 76), (103, 80), (104, 84), (108, 88),
        (116, 98), (110, 101), (109, 104), (111, 107), (108, 111), (110, 114), (106, 118),
        (109, 124), (104, 130), (88, 132), (76, 124), (68, 110), (62, 112), (60, 96), (64, 84),
        (76, 84), (80, 70), (90, 54)]
FACE_SHOUT = FACE[:11] + [(111, 107), (107, 112), (108, 121), (106, 124), (108, 130), (103, 135), (88, 135),
                          (76, 124), (68, 110), (62, 112), (60, 96), (64, 84), (76, 84), (80, 70), (90, 54)]


def ramp(skin, light, amb, floor):
    """6 odcieni skory od strony swiatla (ekran z przodu) do cienia"""
    ks = [1.0, 0.78, 0.56, 0.40, 0.27, 0.0]
    out = []
    for k in ks:
        v = k * (1 - floor) + floor
        out.append(tuple(int(min(255, skin[i] * (light[i] * v + amb[i] * (1 - v)) / 255)) for i in range(3)))
    return list(zip([1.6, 4.0, 7.5, 12.5, 20.0, 999], out))


def person(im, ox, oy, sc, cfg):
    """ox,oy: gdzie na ekranie trafia punkt (90,90) glowy ze sceny 1; sc: skala"""
    def T(pts):
        return [(ox + (x - 90) * sc, oy + (y - 90) * sc) for x, y in pts]
    d = ImageDraw.Draw(im)
    tones = ramp(cfg['skin'], cfg['light'], cfg['amb'], cfg.get('floor', 0.12))
    # tulow
    body = cfg['body']
    # tulow siega az za dolna krawedz ekranu (postac ucieta przez kadr, a nie wiszaca w powietrzu)
    body_s = [(x, 232 if y >= 200 else yy) for (x, yy), (_, y) in zip(T(body), body)]
    d.polygon(P(body_s), fill=cfg['cloth'])
    if 'cloth_rim' in cfg:
        d.line(P(T(cfg['body_rim'])), fill=cfg['cloth_rim'], width=S)
    # wlosy z tylu (dlugie)
    if 'hair_back' in cfg:
        d.polygon(P(T(cfg['hair_back'])), fill=cfg['hair'])
    face = FACE_SHOUT if cfg['expr'] == 'shout' else FACE
    face = [(x + cfg.get('nose', 0) if 96 < y < 104 else x, y) for x, y in face]
    neck = [(74, 120), (100, 128), (100, 150), (64, 150), (62, 118)]
    if 'hair_poly' in cfg:      # podklad wlosow przesuniety ku twarzy: zakrywa szczeline przy czole
        d.polygon(P(T([(x + 5, y) for x, y in cfg['hair_poly']])), fill=cfg['hair'])
    m = Image.new('L', im.size, 0)
    md = ImageDraw.Draw(m)
    md.polygon(P(T(face)), fill=255)
    md.polygon(P(T(neck)), fill=255)
    bb = m.getbbox()
    mp = m.load(); ip = im.load()
    for y in range(bb[1], bb[3]):
        xs = [x for x in range(bb[0], bb[2]) if mp[x, y]]
        if not xs:
            continue
        xr = max(xs)
        for x in xs:
            dist = (xr - x) / S / sc
            if y > oy * S + 44 * sc * S:
                dist = dist * 1.6 + 3
            for lim, c in tones:
                if dist <= lim:
                    ip[x, y] = c
                    break
    d = ImageDraw.Draw(im)
    dk = tones[-1][1]; md_ = tones[3][1]; lt = tones[1][1]; hl = tones[0][1]
    # ucho
    d.ellipse(P(T([(63, 84), (74, 103)])), fill=tones[4][1])
    d.arc(P(T([(63, 84), (74, 103)])), 300, 80, fill=tones[2][1], width=S)
    # wlosy
    if cfg.get('scalp'):        # lysina: czubek glowy w kolorze skory, z jasna krawedzia od ekranu
        scalp = [(95, 41), (86, 30), (66, 26), (46, 31), (32, 45), (26, 64), (28, 88), (36, 104), (50, 112),
                 (62, 114), (66, 102), (63, 88), (74, 84), (78, 72), (88, 56), (99, 46)]
        d.polygon(P(T(scalp)), fill=tones[3][1])
        d.polygon(P(T([(95, 41), (86, 30), (66, 26), (60, 30), (80, 36), (90, 46), (99, 46)])), fill=tones[1][1])
        d.line(P(T([(66, 26), (86, 30), (95, 41)])), fill=tones[0][1], width=S)
        d.line(P(T([(46, 31), (32, 45), (27, 60)])), fill=cfg['hair_lit'], width=S)
    d.polygon(P(T(cfg['hair_poly'])), fill=cfg['hair'])
    for a_, b_ in cfg.get('strands', []):
        d.line(P(T([a_, b_])), fill=cfg['hair_dark'], width=S)
    if 'hair_rim' in cfg:
        d.line(P(T(cfg['hair_rim'])), fill=cfg['hair_lit'], width=max(S, int(S * sc)))
    # brew: im wyzszy stan, tym nizej i bardziej skosnie (zmarszczona)
    bs = cfg.get('brow_state', 2)
    brow = [[(92, 71.5), (99, 72), (106, 73.5)], [(92, 73.5), (99, 75), (106, 77.5)],
            [(92, 75.5), (99, 78), (106, 81.5)]][bs]
    d.line(P(T(brow)), fill=cfg.get('brow', (20, 14, 16)), width=int(2.2 * S * sc) or S)
    if bs >= 1:
        d.line(P(T([(96, 67), (103, 70)])), fill=tones[2][1], width=S)
    if bs == 2:
        d.line(P(T([(95, 62.5), (102, 65)])), fill=tones[2][1], width=S)
        d.line(P(T([(104, 72), (106, 76)])), fill=tones[3][1], width=S)     # bruzda nad nosem
    # oko (przy zmarszczonych brwiach przymruzone)
    lid = [80, 80.6, 81.6][bs]
    d.polygon(P(T([(96, 83), (100, lid + 1), (104, 83), (101, 86), (97, 86)])), fill=mix(hl, (230, 200, 200), 0.3))
    d.rectangle(P(T([(101, max(82, lid + 1.4)), (103, 85)])), fill=(22, 14, 18))
    d.line(P(T([(96, 82), (100, lid), (104, 82)])), fill=(20, 14, 16), width=S)
    if cfg.get('glasses'):
        d.ellipse(P(T([(93, 78), (108, 91)])), outline=(150, 150, 160), width=S)
        d.line(P(T([(93, 84), (70, 88)])), fill=(110, 110, 120), width=S)
    if cfg.get('wrinkles'):
        d.line(P(T([(90, 88), (94, 92)])), fill=md_, width=S)
        d.line(P(T([(98, 104), (95, 112)])), fill=md_, width=S)
        d.line(P(T([(93, 60), (101, 62)])), fill=tones[2][1], width=S)
    # usta
    e = cfg['expr']
    if e == 'teeth':
        d.polygon(P(T([(102, 108), (110, 107), (110, 111), (102, 112)])), fill=(214, 218, 228))
        d.line(P(T([(102, 110), (110, 109)])), fill=(120, 116, 130), width=S)
        d.line(P(T([(101, 107), (110, 106)])), fill=(26, 16, 20), width=S)
        d.line(P(T([(101, 112), (110, 111)])), fill=(26, 16, 20), width=S)
    elif e == 'shout':
        d.polygon(P(T([(100, 108), (111, 107), (108, 121), (101, 119)])), fill=(20, 8, 12))
        d.polygon(P(T([(101, 108), (111, 107), (111, 110), (101, 110)])), fill=(214, 218, 228))
        d.line(P(T([(102, 118), (107, 119)])), fill=(150, 70, 84), width=S)
    else:
        d.line(P(T([(101, 110), (110, 109)])), fill=(26, 16, 20), width=S)
    if cfg.get('mustache'):
        d.polygon(P(T([(100, 103), (111, 102), (112, 106), (100, 107)])), fill=cfg['mustache'])
    if cfg.get('beard'):
        d.polygon(P(T([(76, 112), (84, 124), (90, 132), (104, 134), (110, 126), (108, 121), (101, 121),
                       (96, 114), (88, 110)])), fill=cfg['beard'])
        d.line(P(T([(90, 132), (104, 134), (110, 126)])), fill=mix(cfg['beard'], hl, 0.45), width=S)
    d.line(P(T([(104, 100), (103, 108)])), fill=tones[2][1], width=S)
    return T


def fist_or_hand(d, x, y, sc, tones, typing=True):
    """dlon na klawiaturze z boku: wierzch jasny od ekranu, palce w dol"""
    hl, lt, md, dk = tones
    d.rounded_rectangle([(x - 7 * sc) * S, (y - 3 * sc) * S, (x + 7 * sc) * S, (y + 4 * sc) * S],
                        radius=int(2.5 * sc * S), fill=dk)
    d.rounded_rectangle([(x - 6 * sc) * S, (y - 2.5 * sc) * S, (x + 6.5 * sc) * S, (y + 3 * sc) * S],
                        radius=int(2 * sc * S), fill=md)
    d.rounded_rectangle([(x - 2 * sc) * S, (y - 2.5 * sc) * S, (x + 6.5 * sc) * S, (y + 0.5 * sc) * S],
                        radius=int(1.5 * sc * S), fill=lt)
    for k in range(4 if typing else 0):
        fx = x + 6.5 * sc - k * 0.6 * sc
        fy = y - 1.5 * sc + k * 1.6 * sc
        d.line(P([(fx - 1 * sc, fy), (fx + 2.5 * sc, fy + 2.6 * sc)]), fill=dk, width=int(2.0 * sc * S))
        d.line(P([(fx - 1 * sc, fy - 0.3 * sc), (fx + 2.2 * sc, fy + 2.2 * sc)]), fill=lt, width=int(1.1 * sc * S))
    d.line(P([(x + 4 * sc, y - 2.4 * sc), (x + 6 * sc, y - 2 * sc)]), fill=hl, width=S)


def arm_to(d, sh, el, wr, w, col, rim):
    d.line(P([sh, el]), fill=col, width=int(w * S))
    d.line(P([el, wr]), fill=col, width=int(w * 0.85 * S))
    for p_ in (sh, el):
        d.ellipse([(p_[0] - w / 2) * S, (p_[1] - w / 2) * S, (p_[0] + w / 2) * S, (p_[1] + w / 2) * S], fill=col)
    d.line(P([(el[0], el[1] - w * 0.42), (wr[0], wr[1] - w * 0.36)]), fill=rim, width=S)


# ---------------------------------------------------------------- 1. biuro, mloda kobieta, komputer stacjonarny
def office(st=2):
    def bg(x, y):
        if y > 150:
            t = (y - 150) / 74
            return mix((150, 146, 140), (96, 92, 90), t)
        g = 1 - y / 150 * 0.35
        return (132 * g + 10, 146 * g + 10, 164 * g + 14)
    im = field(bg)
    d = ImageDraw.Draw(im)
    # okno z zaluzjami
    d.rectangle(P([(14, 8), (118, 96)]), fill=(70, 80, 96))
    d.rectangle(P([(17, 11), (115, 93)]), fill=(196, 220, 240))
    for i in range(14):
        yy = 13 + i * 6
        d.rectangle(P([(17, yy), (115, yy + 3)]), fill=(222, 228, 232))
        d.line(P([(17, yy + 3), (115, yy + 3)]), fill=(150, 160, 172), width=S)
    # scianka boksu
    d.rectangle(P([(0, 104), (256, 150)]), fill=(96, 104, 120))
    for i in range(0, 256, 6):
        d.line(P([(i, 106), (i, 150)]), fill=(90, 98, 114), width=S)
    d.rectangle(P([(0, 102), (256, 106)]), fill=(70, 76, 88))
    # biurko
    d.polygon(P([(0, 150), (256, 150), (256, 162), (0, 162)]), fill=(190, 180, 166))
    d.line(P([(0, 150), (256, 150)]), fill=(222, 214, 200), width=S)
    d.rectangle(P([(0, 162), (256, 224)]), fill=(70, 66, 66))
    # roslina
    d.rectangle(P([(232, 128), (248, 150)]), fill=(200, 196, 190))
    for a in range(-60, 61, 20):
        r = math.radians(a - 90)
        d.line(P([(240, 128), (240 + 16 * math.cos(r), 128 + 22 * math.sin(r))]), fill=(60, 120, 70), width=3 * S)
    # monitor + noga
    d.rectangle(P([(174, 128), (184, 150)]), fill=(40, 42, 48))
    d.polygon(P([(160, 148), (198, 148), (200, 152), (158, 152)]), fill=(40, 42, 48))
    d.polygon(P([(136, 40), (230, 36), (230, 130), (136, 128)]), fill=(26, 28, 34))
    screen_ui(d, [(140, 44), (226, 40), (226, 125), (140, 123)])
    # mysz, klawiatura
    d.polygon(P([(112, 150), (170, 150), (172, 156), (108, 156)]), fill=(48, 50, 58))
    d.ellipse(P([(186, 152), (196, 158)]), fill=(48, 50, 58))
    # kobieta
    cfg = dict(skin=(240, 196, 172), light=(240, 244, 255), amb=(150, 156, 170), floor=0.38, expr='teeth',
               nose=-3, hair=(54, 34, 26), hair_lit=(120, 84, 60), cloth=(130, 50, 70), brow=(40, 26, 22),
               body=[(10, 150), (40, 132), (76, 128), (102, 140), (118, 172), (124, 230), (0, 230), (0, 160)],
               brow_state=st,
               hair_poly=[(95, 41), (86, 30), (66, 25), (46, 30), (32, 44), (26, 64), (28, 90), (36, 104),
                          (50, 112), (62, 112), (66, 102), (63, 88), (74, 84), (78, 72), (88, 56), (99, 46)],
               hair_back=[(46, 60), (28, 80), (24, 120), (30, 156), (44, 176), (64, 168), (70, 140), (66, 112)],
               hair_rim=[(66, 25), (86, 30), (95, 41), (99, 46)])
    person(im, 74, 92, 0.78, cfg)
    d = ImageDraw.Draw(im)
    arm_to(d, (62, 150), (94, 174), (118, 154), 16, (130, 50, 70), (186, 104, 124))
    fist_or_hand(d, 126, 150, 1.35, ((250, 226, 214), (226, 186, 166), (176, 130, 116), (90, 60, 56)))
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- 2. pokoj dziecka, 10-latek
def kidroom(st=2):
    def bg(x, y):
        if y > 156:
            return mix((70, 52, 60), (40, 30, 40), (y - 156) / 68)
        g = max(0.0, 1 - math.hypot(x - 230, y - 70) / 200)
        return (40 + 90 * g, 44 + 70 * g, 86 + 30 * g)
    im = field(bg)
    d = ImageDraw.Draw(im)
    # plakaty: rakieta i smok
    d.rectangle(P([(10, 14), (58, 76)]), fill=(30, 40, 90))
    d.polygon(P([(34, 22), (42, 40), (42, 60), (26, 60), (26, 40)]), fill=(220, 220, 230))
    d.polygon(P([(26, 50), (20, 62), (26, 60)]), fill=(220, 70, 60))
    d.polygon(P([(42, 50), (48, 62), (42, 60)]), fill=(220, 70, 60))
    d.polygon(P([(28, 60), (34, 72), (40, 60)]), fill=(250, 190, 60))
    for sx, sy in ((14, 20), (52, 26), (18, 46), (50, 66)):
        d.rectangle(P([(sx, sy), (sx + 1, sy + 1)]), fill=(250, 250, 200))
    d.rectangle(P([(66, 22), (118, 64)]), fill=(240, 200, 90))
    G, GD, GL = (60, 140, 80), (36, 96, 56), (120, 190, 110)
    WM = (44, 112, 120)                                                                           # skrzydlo nietoperza
    d.polygon(P([(94, 43), (99, 25), (92, 33), (86, 24), (82, 34), (73, 28), (76, 38), (69, 39), (82, 45)]), fill=WM)
    for tx, ty in ((99, 25), (86, 24), (73, 28), (69, 39)):                                        # kosci skrzydla
        d.line(P([(93, 42), (tx, ty)]), fill=GD, width=S)
    d.ellipse(P([(78, 40), (100, 54)]), fill=G)                                                   # tulow
    d.polygon(P([(80, 48), (70, 54), (68, 60), (74, 58), (82, 54)]), fill=G)                       # ogon
    d.polygon(P([(68, 60), (65, 63), (70, 62)]), fill=G)
    d.polygon(P([(94, 44), (100, 34), (104, 32), (106, 36), (100, 46)]), fill=G)                   # szyja
    d.polygon(P([(100, 32), (108, 31), (112, 33), (108, 36), (102, 37)]), fill=G)                  # glowa
    d.polygon(P([(101, 32), (99, 27), (103, 31)]), fill=GD)                                        # rogi
    d.polygon(P([(104, 31), (103, 26), (106, 30)]), fill=GD)
    d.rectangle(P([(105, 32), (106, 33)]), fill=(250, 250, 240))                                   # oko
    d.polygon(P([(112, 33), (116, 31), (117, 34), (116, 37), (112, 35)]), fill=(240, 90, 40))      # ogien
    d.polygon(P([(113, 33.5), (115.5, 32.5), (115.5, 35.5)]), fill=(255, 220, 90))
    d.line(P([(84, 54), (83, 58)]), fill=GD, width=2 * S); d.line(P([(94, 53), (95, 58)]), fill=GD, width=2 * S)
    d.line(P([(82, 45), (96, 45)]), fill=GL, width=S)
    # lampki
    for i in range(12):
        x = 4 + i * 21; y = 6 + 5 * math.sin(i * 0.9)
        d.ellipse(P([(x, y), (x + 3, y + 3)]), fill=[(250, 220, 90), (250, 120, 160), (120, 220, 250)][i % 3])
    # polka z zabawkami
    d.rectangle(P([(150, 40), (220, 44)]), fill=(150, 100, 70))
    d.rectangle(P([(156, 26), (166, 40)]), fill=(220, 60, 60))
    d.ellipse(P([(172, 28), (184, 40)]), fill=(60, 160, 230))
    d.polygon(P([(192, 40), (198, 24), (204, 40)]), fill=(250, 200, 60))
    # biurko, lampka, laptop
    d.rectangle(P([(0, 156), (256, 164)]), fill=(170, 120, 90))
    d.line(P([(0, 156), (256, 156)]), fill=(214, 170, 130), width=S)
    d.polygon(P([(238, 156), (242, 110), (226, 96), (222, 100), (236, 112), (232, 156)]), fill=(60, 70, 100))
    d.polygon(P([(214, 98), (234, 90), (240, 100)]), fill=(250, 220, 120))
    d.polygon(P([(150, 158), (214, 158), (220, 154), (156, 152)]), fill=(70, 74, 90))
    d.polygon(P([(152, 84), (208, 80), (214, 152), (158, 154)]), fill=(30, 32, 42))
    screen_ui(d, [(156, 88), (205, 84), (210, 148), (161, 150)])
    # dziecko (mniejsze, w bluzie z kapturem)
    cfg = dict(skin=(236, 190, 160), light=(220, 232, 255), amb=(80, 70, 110), floor=0.18, expr='shout',
               nose=-4, hair=(90, 56, 30), hair_lit=(190, 140, 90), cloth=(50, 110, 70), brow_state=st,
               body=[(10, 140), (40, 124), (78, 128), (104, 142), (118, 176), (126, 240), (0, 240), (0, 150)],
               hair_poly=[(96, 42), (98, 34), (88, 26), (90, 20), (78, 22), (72, 14), (64, 22), (52, 16), (50, 26),
                          (36, 26), (40, 34), (28, 40), (30, 52), (22, 62), (28, 72), (24, 86), (32, 96), (36, 108),
                          (50, 114), (62, 112), (66, 102), (63, 88), (74, 84), (78, 72), (88, 58), (100, 50)],
               hair_rim=[(72, 14), (78, 22), (90, 20), (88, 26), (98, 34), (96, 42), (100, 50)])
    person(im, 92, 110, 0.66, cfg)
    d = ImageDraw.Draw(im)
    arm_to(d, (82, 168), (116, 186), (144, 158), 15, (50, 110, 70), (100, 170, 120))
    fist_or_hand(d, 152, 154, 1.2, ((250, 224, 210), (226, 180, 156), (170, 120, 100), (80, 50, 50)))
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- 3. salon z kominkiem, starszy pan, cienki laptop
def livingroom(st=0):
    def bg(x, y):
        g = max(0.0, 1 - math.hypot(x - 40, y - 150) / 190) ** 1.6
        if y > 176:
            return mix((50, 30, 24), (30, 18, 16), (y - 176) / 48) if g < 0.2 else (60 + 120 * g, 34 + 60 * g, 20 + 20 * g)
        return (46 + 150 * g, 30 + 80 * g, 30 + 30 * g)
    im = field(bg)
    d = ImageDraw.Draw(im)
    # kominek
    d.rectangle(P([(0, 96), (86, 104)]), fill=(120, 80, 60))
    d.rectangle(P([(4, 104), (80, 180)]), fill=(110, 70, 54))
    for r in range(8):
        for c in range(5):
            x0 = 4 + c * 16 + (8 if r % 2 else 0); y0 = 104 + r * 9
            d.rectangle(P([(x0, y0), (x0 + 15, y0 + 8)]), outline=(80, 50, 40), width=S)
    d.rectangle(P([(18, 126), (66, 180)]), fill=(24, 12, 10))
    fr = __import__('random').Random(7 + st * 31)    # plomienie: kazdy stan (klatka) troche inny
    for i, (fx, fh, col) in enumerate(((30, 30, (250, 120, 40)), (42, 40, (255, 170, 60)), (52, 26, (250, 110, 40)),
                                       (38, 20, (255, 230, 140)), (46, 18, (255, 240, 180)))):
        h = fh * fr.uniform(0.72, 1.12)
        lean = fr.uniform(-2.5, 2.5)
        w = 7 * fr.uniform(0.85, 1.1)
        d.polygon(P([(fx - w, 180), (fx - w * 0.35 + lean * 0.4, 180 - h * 0.55), (fx + lean, 180 - h),
                     (fx + w * 0.4 + lean * 0.5, 180 - h * 0.5), (fx + w, 180)]), fill=col)
    d.rectangle(P([(22, 174), (62, 180)]), fill=(70, 40, 30))
    # obraz na scianie, polka
    d.rectangle(P([(14, 26), (70, 74)]), fill=(150, 110, 60))
    d.rectangle(P([(18, 30), (66, 70)]), fill=(70, 90, 70))
    d.polygon(P([(18, 60), (34, 44), (46, 56), (56, 46), (66, 58), (66, 70), (18, 70)]), fill=(50, 70, 50))
    # fotel (ciemna skora)
    d.rounded_rectangle([96 * S, 104 * S, 150 * S, 216 * S], radius=12 * S, fill=(84, 30, 26))
    d.line(P([(100, 110), (146, 108)]), fill=(150, 70, 50), width=S)
    # stolik i laptop
    d.rectangle(P([(170, 170), (256, 176)]), fill=(90, 56, 36))
    d.rectangle(P([(176, 176), (182, 224)]), fill=(70, 42, 28))
    d.polygon(P([(168, 168), (236, 168), (240, 164), (176, 164)]), fill=(170, 172, 182))
    d.polygon(P([(184, 96), (240, 92), (238, 164), (190, 166)]), fill=(180, 182, 192))
    screen_ui(d, [(188, 100), (236, 96), (234, 158), (192, 160)])
    cfg = dict(skin=(232, 186, 160), light=(230, 236, 255), amb=(250, 150, 80), floor=0.2, expr='shout',
               nose=1, hair=(176, 174, 176), hair_dark=(120, 116, 122), hair_lit=(244, 206, 170), cloth=(80, 86, 70),
               glasses=True, wrinkles=True, mustache=(200, 196, 196), scalp=True,
               body=[(10, 150), (40, 134), (78, 128), (104, 142), (120, 176), (126, 240), (0, 240), (0, 160)],
               hair_poly=[(36, 52), (28, 66), (27, 84), (33, 100), (46, 111), (60, 113), (65, 103), (62, 92),
                          (56, 86), (50, 74), (46, 62), (42, 54)],
               strands=[((32, 64), (34, 80)), ((38, 66), (40, 86)), ((34, 88), (42, 102)), ((44, 78), (50, 96)),
                        ((50, 100), (56, 108))],
               hair_rim=[(36, 52), (28, 66), (27, 84), (33, 100)])
    person(im, 146, 104, 0.7, cfg)
    d = ImageDraw.Draw(im)
    arm_to(d, (132, 150), (160, 178), (182, 162), 15, (80, 86, 70), (150, 120, 90))
    fist_or_hand(d, 190, 160, 1.2, ((250, 226, 214), (220, 180, 160), (160, 116, 100), (70, 44, 40)))
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- 4. open space: jedna osoba przy monitorze
def openspace(st=0):
    def bg(x, y):
        if y < 40:
            return mix((150, 160, 170), (120, 130, 140), y / 40)
        if y > 140:
            return mix((110, 116, 126), (70, 74, 82), (y - 140) / 84)
        return mix((176, 186, 196), (140, 150, 162), (y - 40) / 100)
    im = field(bg)
    d = ImageDraw.Draw(im)
    # lampy na suficie (perspektywa)
    for i in range(5):
        y = 6 + i * 7; w = 60 - i * 9
        for cx in (60, 140, 220):
            xx = 128 + (cx - 128) * (1 - i * 0.14)
            d.rectangle(P([(xx - w / 2, y), (xx + w / 2, y + 2)]), fill=(240, 246, 250))
    # okna w glebi
    for i in range(7):
        d.rectangle(P([(i * 38, 42), (i * 38 + 34, 92)]), fill=(200, 216, 228))
    # rzedy biurek w tle z monitorami i sylwetkami ludzi
    for row, (y, s) in enumerate(((96, 0.6), (112, 0.8))):
        d.rectangle(P([(0, y + 14 * s), (256, y + 18 * s)]), fill=(150, 150, 150))
        for k in range(7):
            x = 10 + k * 40 + row * 18
            d.rectangle(P([(x, y), (x + 18 * s, y + 12 * s)]), fill=(50, 54, 62))
            lv = __import__('random').Random(st * 97 + row * 13 + k).choice(MON_LEVELS)
            d.rectangle(P([(x + 1, y + 1), (x + 18 * s - 1, y + 12 * s - 1)]), fill=lv)
            hx = x - 12 * s
            d.ellipse(P([(hx, y - 2 * s), (hx + 10 * s, y + 9 * s)]), fill=(90, 90, 100))
            d.rounded_rectangle([(hx - 4 * s) * S, (y + 8 * s) * S, (hx + 14 * s) * S, (y + 18 * s) * S],
                                radius=int(3 * s * S), fill=(96, 100, 116))
    # przegroda + biurko
    d.rectangle(P([(0, 140), (256, 148)]), fill=(80, 90, 104))
    d.rectangle(P([(0, 148), (256, 158)]), fill=(214, 210, 204))
    d.rectangle(P([(0, 158), (256, 224)]), fill=(84, 88, 96))
    # monitor
    d.rectangle(P([(184, 128), (194, 148)]), fill=(30, 32, 38))
    d.polygon(P([(146, 34), (246, 30), (246, 130), (146, 128)]), fill=(24, 26, 32))
    screen_ui(d, [(150, 38), (242, 34), (242, 125), (150, 123)])
    d.polygon(P([(110, 150), (170, 150), (172, 156), (106, 156)]), fill=(44, 46, 52))
    cfg = dict(skin=(210, 160, 130), light=(236, 242, 255), amb=(150, 156, 170), floor=0.3, expr='teeth',
               nose=0, hair=(30, 26, 26), hair_lit=(90, 90, 96), cloth=(40, 70, 120), beard=(46, 36, 32),
               body=[(10, 150), (40, 132), (78, 128), (104, 142), (118, 176), (124, 240), (0, 240), (0, 160)],
               hair_poly=[(92, 46), (86, 34), (68, 30), (50, 34), (36, 46), (30, 64), (32, 84), (40, 100),
                          (54, 108), (62, 110), (66, 100), (63, 88), (74, 84), (78, 70), (86, 56)],
               hair_rim=[(68, 30), (86, 34), (92, 46)])
    person(im, 92, 90, 0.82, cfg)
    d = ImageDraw.Draw(im)
    arm_to(d, (80, 156), (112, 178), (128, 156), 17, (40, 70, 120), (100, 130, 180))
    fist_or_hand(d, 136, 152, 1.35, ((240, 210, 190), (210, 160, 136), (150, 104, 84), (70, 44, 36)))
    return im.resize((W, H), Image.LANCZOS)


MON_LEVELS = [(138, 178, 210), (152, 192, 222), (168, 206, 234)]
SCENES = [office, kidroom, livingroom, openspace]
# stany kazdej przebitki (animacja) i plan zmian w trakcie 102 klatek (1,7 s): (klatka, stan)
STATES = [[0, 1, 2], [0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3]]


def schedule(k, length=102):
    import random as _r
    if k == 0:
        return [(0, 0), (40, 1), (45, 2)]              # kobieta marszczy brwi
    if k == 1:
        return [(0, 0), (30, 1), (35, 2)]              # chlopak marszczy brwi
    rr = _r.Random(100 + k)
    out, t, last = [(0, 0)], 0, 0
    while True:
        t += rr.choice((4, 5, 6, 7)) if k == 2 else rr.choice((7, 8, 9, 10))
        if t >= length - 1:
            break
        s = rr.choice([x for x in STATES[k] if x != last])
        out.append((t, s))
        last = s
    return out

if __name__ == '__main__':
    out = Image.new('RGB', (512, 448))
    for k, fn in enumerate(SCENES):
        im = fn(STATES[k][-1] if k < 2 else 0)
        im.save(_os.path.join(WORK, 'fl_%d.png') % k)
        out.paste(im, ((k % 2) * 256, (k // 2) * 224))
    out.save(_os.path.join(WORK, 'fl_all.png'))
