# Scena 1 intro: ciemny pokoj, mezczyzna przed laptopem (kamera lekko za nim), swiatlo tylko z ekranu.
# Rysowane w 4x (tlo w 1x z przeplotem odcieni), zmniejszane do 256x224. Warianty klatek ruchu:
#   expr: 'angry' | 'teeth' | 'shout'      arm: 'type0' | 'type1' | 'type2' | 'raise' | 'slam' | 'laptop'
#   screen: 'chat' | 'glitch'
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


def P(pts):
    return [(x * S, y * S) for x, y in pts]


def background():
    bg = Image.new('RGB', (W, H)); bp = bg.load()
    for y in range(H):
        for x in range(W):
            edge = 150 - (x / 256) * 4
            if y >= edge:      # biurko
                t = (y - 146) / 78
                g = max(0.0, 1 - math.hypot(x - 180, (y - 140) * 1.6) / 120)
                c = (22 + 40 * g - 8 * t, 20 + 44 * g - 8 * t, 24 + 58 * g - 6 * t)
            else:              # sciana z poswiata od ekranu
                dd = math.hypot((x - 176) / 1.25, y - 86)
                g = max(0.0, 1 - dd / 150) ** 2.2
                c = (7 + 30 * g, 8 + 38 * g, 13 + 62 * g)
            th = (BAYER[y % 4][x % 4] + 0.5) / 16
            bp[x, y] = tuple(int(min(31, math.floor(v / 255 * 31 + th)) * 255 / 31 + 0.5) for v in c)
    return bg


def capsule(d, a, b, r, fill):
    d.line(P([a, b]), fill=fill, width=int(2 * r * S))
    for (x, y) in (a, b):
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill)


def laptop(d, screen, dy=0):
    # podstawa z klawiatura
    d.polygon(P([(110, 131 + dy), (236, 135 + dy), (252, 160 + dy), (96, 156 + dy)]), fill=(48, 54, 70))
    d.polygon(P([(116, 134 + dy), (232, 138 + dy), (244, 153 + dy), (106, 150 + dy)]), fill=(28, 32, 44))
    for r in range(4):
        y0 = 136 + r * 4 + dy
        for k in range(16):
            x0 = 117 + k * 8 - r * 0.8 - (y0 - dy - 136) * 0.6
            d.rectangle(P([(x0, y0), (x0 + 5, y0 + 2)]), fill=(62, 72, 98))
    d.line(P([(96, 156 + dy), (252, 160 + dy)]), fill=(90, 104, 140), width=S)
    # ekran
    d.polygon(P([(118, 36 + dy), (236, 42 + dy), (234, 134 + dy), (120, 130 + dy)]), fill=(26, 28, 36))
    scr = [(123, 41 + dy), (231, 46 + dy), (229, 129 + dy), (125, 125 + dy)]
    d.polygon(P(scr), fill=(226, 234, 244))
    d.polygon(P([(123, 41 + dy), (231, 46 + dy), (231, 55 + dy), (123, 50 + dy)]), fill=(44, 52, 72))
    d.line(P([(131, 42 + dy), (132.5, 40.5 + dy)]), fill=(150, 110, 70), width=S)
    d.rounded_rectangle([127 * S, (43 + dy) * S, 135 * S, (50 + dy) * S], radius=2 * S, fill=(0, 168, 176))
    d.rectangle(P([(128.5, 44.5 + dy), (133.5, 48.5 + dy)]), fill=(8, 48, 72))
    d.rectangle(P([(129.2, 45.2 + dy), (130.6, 46.8 + dy)]), fill=(248, 248, 248))
    d.rectangle(P([(131.6, 45.2 + dy), (133.0, 46.8 + dy)]), fill=(248, 248, 248))
    d.line(P([(137, 46 + dy), (152, 47 + dy)]), fill=(220, 230, 240), width=S)

    def bubble(x0, y0, w, h, col, txt):
        sk = (y0 - 41) / 84 * 2 + (x0 - 123) * 0.045
        d.rounded_rectangle(P([(x0, y0 + sk + dy), (x0 + w, y0 + h + sk + dy)]), radius=2 * S, fill=col)
        for i in range(h // 4):
            ln = w - 6 - (i * 7) % 11
            d.line(P([(x0 + 3, y0 + sk + 3 + i * 4 + dy), (x0 + 3 + ln, y0 + sk + 3 + i * 4 + dy)]), fill=txt, width=S)
    bubble(128, 58, 52, 12, (198, 208, 222), (92, 104, 124))
    bubble(178, 74, 46, 8, (60, 112, 216), (200, 220, 250))
    bubble(128, 86, 60, 16, (198, 208, 222), (92, 104, 124))
    bubble(170, 106, 54, 8, (60, 112, 216), (200, 220, 250))
    d.polygon(P([(126, 118 + dy), (229, 122 + dy), (229, 128 + dy), (126, 124 + dy)]), fill=(206, 214, 228))
    if screen == 'glitch':   # po uderzeniu: obraz na ekranie sie rozjezdza
        for i, (yy, sh, col) in enumerate(((52, 9, (240, 60, 90)), (66, -7, (60, 230, 230)), (80, 12, (255, 255, 255)),
                                             (93, -10, (30, 30, 40)), (104, 6, (240, 60, 90)), (114, -5, (60, 230, 230)))):
            d.polygon(P([(124, yy + dy), (230, yy + 4 + dy), (230, yy + 7 + dy), (124, yy + 3 + dy)]), fill=col)
            d.polygon(P([(124 + sh if sh > 0 else 124, yy + 3 + dy), (180 + sh, yy + 5 + dy), (180 + sh, yy + 6 + dy),
                         (124 + sh if sh > 0 else 124, yy + 4 + dy)]), fill=(226, 234, 244))


SKIN = [(1.6, (208, 216, 238)), (4.0, (166, 166, 192)), (7.5, (118, 106, 124)), (12.5, (78, 62, 68)),
        (20.0, (48, 36, 40)), (999, (30, 23, 25))]


def man(im, expr, hx=0):
    skin = [(94, 42), (101, 50), (103, 60), (106, 70), (105, 76), (103, 80), (104, 84), (108, 88),
            (116, 98), (110, 101), (109, 104), (111, 107), (108, 111), (110, 114), (106, 118),
            (109, 124), (104, 130), (88, 132), (76, 124), (68, 110), (62, 112), (60, 96), (64, 84),
            (76, 84), (80, 70), (90, 54)]
    if expr == 'shout':   # usta otwarte: zuchwa opada
        skin = skin[:11] + [(111, 107), (107, 112), (108, 121), (106, 124), (108, 130), (103, 135), (88, 135),
                             (76, 124), (68, 110), (62, 112), (60, 96), (64, 84), (76, 84), (80, 70), (90, 54)]
    skin = [(x + hx, y) for x, y in skin]
    neck = [(74 + hx, 120), (100 + hx, 128), (102, 150), (60, 150), (62, 118)]
    hair = [(x + hx, y) for x, y in [(95, 40), (86, 31), (66, 27), (46, 33), (32, 47), (26, 66), (28, 86), (36, 102),
                                     (48, 112), (62, 115), (66, 104), (64, 88), (75, 85), (79, 72), (89, 56), (98, 46)]]
    d = ImageDraw.Draw(im)
    # tulow (ciemna bluza)
    d.polygon(P([(0, 128), (24, 120), (60, 132), (98, 150), (124, 170), (140, 224), (0, 224)]), fill=(14, 15, 20))
    d.line(P([(24, 121), (60, 133), (98, 151), (122, 168)]), fill=(46, 54, 76), width=2 * S)
    m = Image.new('L', im.size, 0)
    md = ImageDraw.Draw(m)
    md.polygon(P(skin), fill=255)
    md.polygon(P(neck), fill=255)
    mp = m.load(); ip = im.load()
    for y in range(H * S):
        xs = [x for x in range(40 * S, 125 * S) if mp[x, y]]
        if not xs:
            continue
        xr = max(xs)
        for x in xs:
            dist = (xr - x) / S
            if y > 134 * S:
                dist = dist * 1.6 + 3
            for lim, c in SKIN:
                if dist <= lim:
                    ip[x, y] = c
                    break
    d = ImageDraw.Draw(im)
    o = hx
    d.ellipse(P([(63 + o, 84), (74 + o, 103)]), fill=(52, 40, 42))
    d.arc(P([(63 + o, 84), (74 + o, 103)]), 300, 80, fill=(96, 92, 110), width=S)
    d.arc(P([(66 + o, 88), (72 + o, 99)]), 90, 270, fill=(34, 26, 28), width=S)
    d.polygon(P(hair), fill=(11, 11, 15))
    for i, (tx, ty) in enumerate(((44, 34), (34, 46), (28, 62), (27, 80), (33, 96), (42, 108), (56, 34), (70, 28))):
        d.polygon(P([(tx + o, ty), (tx - 3 + o, ty - 2 + i % 2), (tx - 1 + o, ty + 3)]), fill=(11, 11, 15))
    d.line(P([(66 + o, 28), (86 + o, 31), (95 + o, 40), (98 + o, 46)]), fill=(62, 70, 96), width=S)
    d.line(P([(89 + o, 56), (79 + o, 72)]), fill=(40, 44, 60), width=S)
    # brew sciagnieta w dol ku nosowi, zmarszczki
    d.line(P([(92 + o, 75), (99 + o, 77), (106 + o, 80)]), fill=(16, 12, 14), width=2 * S)
    d.line(P([(96 + o, 66), (103 + o, 69)]), fill=(120, 112, 130), width=S)
    d.line(P([(97 + o, 71), (102 + o, 73)]), fill=(100, 92, 108), width=S)
    # oko: przekrwione
    d.polygon(P([(96 + o, 83), (100 + o, 81), (104 + o, 83), (101 + o, 86), (97 + o, 86)]), fill=(206, 150, 154))
    d.line(P([(97 + o, 84), (100 + o, 84)]), fill=(186, 52, 60), width=S)
    d.line(P([(98 + o, 85), (100 + o, 86)]), fill=(186, 52, 60), width=S)
    d.rectangle(P([(101 + o, 82), (103 + o, 85)]), fill=(22, 14, 18))
    d.line(P([(96 + o, 82), (100 + o, 80), (104 + o, 82)]), fill=(20, 14, 16), width=S)
    d.line(P([(97 + o, 87), (102 + o, 87)]), fill=(150, 84, 96), width=S)
    d.line(P([(110 + o, 100), (112 + o, 101)]), fill=(40, 30, 34), width=S)
    d.line(P([(104 + o, 100), (103 + o, 108)]), fill=(86, 76, 90), width=S)
    if expr == 'angry':
        d.line(P([(101 + o, 110), (110 + o, 109)]), fill=(26, 16, 20), width=S)
        d.line(P([(84 + o, 114), (92 + o, 124)]), fill=(98, 88, 104), width=S)
    elif expr == 'teeth':
        d.polygon(P([(102 + o, 108), (110 + o, 107), (110 + o, 111), (102 + o, 112)]), fill=(214, 218, 228))
        d.line(P([(102 + o, 110), (110 + o, 109)]), fill=(120, 116, 130), width=S)
        d.line(P([(101 + o, 107), (110 + o, 106)]), fill=(26, 16, 20), width=S)
        d.line(P([(101 + o, 112), (110 + o, 111)]), fill=(26, 16, 20), width=S)
        d.line(P([(84 + o, 114), (92 + o, 124)]), fill=(98, 88, 104), width=S)
    elif expr == 'shout':   # krzyk: szeroko otwarte usta, gorne zeby
        d.polygon(P([(100 + o, 108), (111 + o, 107), (108 + o, 121), (101 + o, 119)]), fill=(20, 8, 12))
        d.polygon(P([(101 + o, 108), (111 + o, 107), (111 + o, 110), (101 + o, 110)]), fill=(214, 218, 228))
        d.line(P([(102 + o, 118), (107 + o, 119)]), fill=(150, 70, 84), width=S)    # jezyk
        d.line(P([(84 + o, 116), (90 + o, 128)]), fill=(98, 88, 104), width=S)
    d.polygon(P([(56, 136), (102, 142), (110, 158), (50, 150)]), fill=(16, 17, 23))
    d.line(P([(76, 140), (102, 143), (110, 156)]), fill=(52, 60, 84), width=S)


HAND = {'K': (26, 18, 20), 'D': (66, 46, 48), 'M': (104, 76, 78), 'L': (150, 120, 126), 'H': (204, 192, 208)}
SLEEVE, CUFF, RIM = (16, 17, 23), (30, 32, 44), (58, 66, 92)
ROW = (1.0, 0.03)          # kierunek rzedow klawiatury


def _shrink(pts, a):
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        l = math.hypot(dx, dy) or 1
        k = max(0.0, (l - a) / l)
        out.append((cx + dx * k, cy + dy * k))
    return out


def forearm(d, elbow, wrist, w0, w1, rim_side=-1):
    """rekaw bluzy od lokcia do nadgarstka (zwezajacy sie), z jasna krawedzia od strony ekranu"""
    (x0, y0), (x1, y1) = elbow, wrist
    l = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / l, (x1 - x0) / l
    pts = [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
           (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]
    d.polygon(P(pts), fill=SLEEVE)
    s = rim_side
    d.line(P([(x0 + s * nx * w0 / 2, y0 + s * ny * w0 / 2), (x1 + s * nx * w1 / 2, y1 + s * ny * w1 / 2)]),
           fill=RIM, width=S)


def cuff(d, elbow, wrist, w):
    """mankiet: krotki pasek rekawa na nadgarstku (przykrywa poczatek dloni)"""
    (x0, y0), (x1, y1) = elbow, wrist
    l = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / l, (y1 - y0) / l
    nx, ny = -uy, ux
    a = (x1 - ux * 4, y1 - uy * 4); b = (x1 + ux * 1.2, y1 + uy * 1.2)
    pts = [(a[0] + nx * w / 2, a[1] + ny * w / 2), (b[0] + nx * w / 2, b[1] + ny * w / 2),
           (b[0] - nx * w / 2, b[1] - ny * w / 2), (a[0] - nx * w / 2, a[1] - ny * w / 2)]
    d.polygon(P(pts), fill=CUFF)
    d.line(P([pts[1], pts[2]]), fill=RIM, width=S)


def hand(d, wrist, knuck, frame, side='L', scale=1.0):
    """dlon na klawiaturze widziana z tylu: nadgarstek -> wierzch dloni -> 4 palce, kciuk do srodka.
    Cala sylwetka jest pelna (klawiatura nie przeswituje), palce rozdziela ciemna kreska."""
    sg = 1 if side == 'L' else -1
    wx, wy = wrist; kx, ky = knuck
    VK = 12.0

    def at(u, v):
        u = u * scale * sg
        return (wx + (kx - wx) * v / VK + ROW[0] * u, wy + (ky - wy) * v / VK + ROW[1] * u)

    def poly(pts, col, shrink=0.0):
        pts = [at(u, v) for u, v in pts]
        if shrink:
            pts = _shrink(pts, shrink * scale)
        d.polygon(P(pts), fill=col)
    back = [(-5.5, -1), (5.5, -1), (10.5, 9), (12.2, 12.5), (-12.2, 12.5), (-10.5, 9)]
    thumb = [(4.5, 1), (8.5, 3.5), (14, 8.5), (15.5, 12), (12.5, 13), (8, 8.5), (3.5, 5)]
    cen = [-9.0, -3.0, 3.0, 9.0]          # maly, serdeczny, srodkowy, wskazujacy
    lng = [5.5, 7.5, 8.5, 7.5]
    fingers = []
    for k in range(4):
        up = (frame + k * 2) % 4 == 0      # palec uniesiony nad klawiszem
        L = lng[k] - (1.8 if up else 0)
        c = cen[k]
        fingers.append(([(c - 3.1, 10.5), (c + 3.1, 10.5), (c + 2.8, 12 + L), (c + 1.6, 12.8 + L),
                         (c - 1.6, 12.8 + L), (c - 2.8, 12 + L)], L, up, c))
    # 1) pelna ciemna sylwetka
    poly(back, HAND['K'])
    poly(thumb, HAND['K'])
    for pts, L, up, c in fingers:
        poly(pts, HAND['K'])
    # 2) kciuk, wierzch dloni (ciemniej przy nadgarstku, jasniej przy knykciach)
    poly(thumb, HAND['D'], 0.9)
    poly(back, HAND['D'], 0.9)
    poly([(-8.5, 5), (8.5, 5), (10.5, 9), (11.5, 11.8), (-11.5, 11.8), (-10.5, 9)], HAND['M'], 0.5)
    poly([(-11.2, 9.8), (11.2, 9.8), (11.4, 12), (-11.4, 12)], HAND['L'])
    # 3) palce: srodek, jasny czubek (zgiety ku ekranowi)
    for pts, L, up, c in fingers:
        poly([(c - 2.0, 11.6), (c + 2.0, 11.6), (c + 1.8, 12 + L), (c - 1.8, 12 + L)], HAND['M'])
        poly([(c - 1.8, 12 + L * 0.5), (c + 1.8, 12 + L * 0.5), (c + 1.6, 12.2 + L), (c - 1.6, 12.2 + L)],
             HAND['H'] if up else HAND['L'])
        x, y = at(c, 11.2)
        r = 1.1 * scale
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=HAND['L'])


def fist(d, fx, fy, scale=1.0):
    """zacisnieta piesc ustawiona do uderzenia z gory ("mlotkiem"): maly palec na dole, kciuk na gorze.
    Widac strone dloni: cztery zgiete palce poziomo, jeden nad drugim, przod (knykcie) w strone ekranu,
    kciuk ukosnie przez palec wskazujacy i srodkowy; nadgarstek z tylu, na dole (x<0)."""
    r = scale

    def rr(x0, y0, x1, y1, rad, col):
        d.rounded_rectangle([(fx + x0 * r) * S, (fy + y0 * r) * S, (fx + x1 * r) * S, (fy + y1 * r) * S],
                            radius=max(1, int(rad * r * S)), fill=col)

    def cap(a, b, w, col):
        (x0, y0), (x1, y1) = a, b
        d.line(P([(fx + x0 * r, fy + y0 * r), (fx + x1 * r, fy + y1 * r)]), fill=col, width=int(w * r * S))
        for x, y in (a, b):
            d.ellipse([(fx + (x - w / 2) * r) * S, (fy + (y - w / 2) * r) * S,
                       (fx + (x + w / 2) * r) * S, (fy + (y + w / 2) * r) * S], fill=col)
    rr(-8.5, -10, 8.5, 10.5, 5, HAND['K'])            # sylwetka
    rr(-7.6, -9.1, 0, 9.6, 4, HAND['D'])              # nasada dloni (od strony nadgarstka, w cieniu)
    bands = [(-9.1, -4.6, 7.6), (-4.6, -0.1, 7.9), (-0.1, 4.6, 7.5), (4.6, 9.6, 6.6)]   # wskazujacy..maly
    for y0, y1, xf in bands:
        rr(-3.5, y0 + 0.35, xf, y1 - 0.35, 2.2, HAND['M'])
        rr(xf - 4.2, y0 + 0.6, xf, y1 - 0.6, 2.0, HAND['L'])        # przod palca oswietlony ekranem
        rr(xf - 2.2, y0 + 0.8, xf - 0.4, y0 + 1.9, 0.6, HAND['H'])  # knykiec
    cap((-6.2, -8.0), (3.0, -3.2), 4.4, HAND['K'])    # kciuk
    cap((-6.2, -8.0), (3.0, -3.2), 2.8, HAND['M'])
    cap((-5.4, -8.6), (2.6, -4.3), 1.0, HAND['L'])


# Prawa reka (blizej kamery) - widoczna cala, przed tulowiem. Lewa reka (dalsza) - rysowana PRZED
# tulowiem, wiec cialo ja zaslania; widac tylko dlon (piesc) i kawalek przedramienia.
R_ELBOW, R_WRIST, R_KNUCK = (146, 236), (184, 160), (192, 147)


def right_arm(d, pose, fr):
    if pose == 'laptop':
        wr, kn, f = (186, 161), (195, 148), 3
    else:
        wr, kn, f = R_WRIST, R_KNUCK, fr + 1
    forearm(d, R_ELBOW, wr, 24, 13, rim_side=-1)
    hand(d, wr, kn, f, 'R', 0.95)
    cuff(d, R_ELBOW, wr, 13)


def left_arm(d, pose, fr):
    if pose.startswith('type'):
        el, wr = (92, 186), (124, 158)
        forearm(d, el, wr, 20, 12, rim_side=-1)
        hand(d, wr, (133, 146), fr, 'L')
        cuff(d, el, wr, 12)
    elif pose == 'raise':     # piesc uniesiona nad klawiatura, na tle jasnego ekranu
        el, wr = (114, 172), (138, 124)
        forearm(d, el, wr, 20, 13, rim_side=1)
        fist(d, 146, 112, 1.15)
        cuff(d, el, wr, 13)
    elif pose == 'slam':      # piesc na biurku przed laptopem
        el, wr = (100, 196), (141, 180)
        forearm(d, el, wr, 20, 13, rim_side=-1)
        fist(d, 152, 176, 1.15)
        cuff(d, el, wr, 13)
    elif pose == 'laptop':    # piesc na klawiaturze laptopa
        el, wr = (102, 176), (147, 146)
        forearm(d, el, wr, 20, 13, rim_side=-1)
        fist(d, 158, 142, 1.15)
        cuff(d, el, wr, 13)


def scene(expr='angry', pose='type0', screen='chat', laptop_dy=0, hx=0):
    im = background().resize((W * S, H * S), Image.NEAREST)
    d = ImageDraw.Draw(im)
    d.rectangle(P([(196, 18), (256, 21)]), fill=(20, 24, 38))
    for i, (bx, bh) in enumerate(((200, 14), (206, 11), (211, 15), (218, 9), (226, 13), (233, 12))):
        d.rectangle(P([(bx, 18 - bh), (bx + 4, 18)]), fill=(16 + i % 2 * 3, 19, 30 + i % 3 * 3))
    d.line(P([(0, 150), (256, 146)]), fill=(70, 82, 110), width=S)
    d.rectangle(P([(240, 128), (252, 146)]), fill=(30, 34, 48))
    d.rectangle(P([(240, 128), (241, 146)]), fill=(70, 86, 120))
    laptop(d, screen, laptop_dy)
    fr = int(pose[-1]) if pose.startswith('type') else 0
    left_arm(d, pose, fr)            # dalsza reka: za tulowiem
    man(im, expr, hx)
    d = ImageDraw.Draw(im)
    right_arm(d, pose, fr)           # blizsza reka: przed tulowiem
    return im.resize((W, H), Image.LANCZOS)


VARIANTS = [
    ('angry', 'type0', 'chat', 0, 0), ('angry', 'type1', 'chat', 0, 0), ('angry', 'type2', 'chat', 0, 0),
    ('teeth', 'type0', 'chat', 0, 0), ('teeth', 'type1', 'chat', 0, 0), ('teeth', 'type2', 'chat', 0, 0),
    ('teeth', 'raise', 'chat', 0, 0), ('teeth', 'slam', 'chat', 0, 0),
    ('teeth', 'laptop', 'glitch', 0, 0), ('teeth', 'laptop', 'chat', 0, 0),
    ('shout', 'laptop', 'chat', 0, 0),
]

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        for i, v in enumerate(VARIANTS):
            scene(*v).save(_os.path.join(WORK, 's1_%02d.png') % i)
    else:
        scene().save(_os.path.join(WORK, 'scene1_key.png'))
