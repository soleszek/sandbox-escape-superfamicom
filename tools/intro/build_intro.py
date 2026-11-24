# Buduje dane intro: strumien polecen na kazda klatke (zapisy VRAM/CGRAM w VBlank, rejestry,
# dzwieki) oraz bloki danych. Wynik: intro_data.as (sekcje ROM) + intro_*.bin w katalogu gry.
import sys, os, pickle, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))          # tools/intro
WORK = _os.path.join(HERE, 'work')                                  # pliki posrednie (generowane)
PROJ = _os.path.abspath(_os.path.join(HERE, '..', '..'))           # katalog gry
_os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, HERE)
import chat
from chat import Item
import exactconv as XC
import scene1

OUT = sys.argv[1] if len(sys.argv) > 1 else PROJ
conv = pickle.load(open(_os.path.join(WORK, 'conv.pkl'), 'rb'))

# ------------------------------------------------------------------ rejestry PPU (mlodszy bajt adresu $21xx)
INIDISP, BGMODE, BG1SC, BG2SC, BG3SC, BG12NBA, BG34NBA = 0x00, 0x05, 0x07, 0x08, 0x09, 0x0B, 0x0C
BG1HOFS, BG1VOFS, BG2HOFS, BG2VOFS, BG3HOFS, BG3VOFS = 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12
TM, TS, CGWSEL, CGADSUB, MOSAIC = 0x2C, 0x2D, 0x30, 0x31, 0x06
W12SEL, W34SEL, WOBJSEL, TMW, TSW = 0x23, 0x24, 0x25, 0x2E, 0x2F
VTOP = 0x3FF          # pionowe przesuniecie -1: pierwsza widoczna linia = linia 0 obrazu

# ------------------------------------------------------------------ dzwieki (numery jak w superfamipong.c)
SND_THUD, SND_CRASH, SND_SHOUT, SND_BOOM = 15, 16, 17, 18

FR = {}               # klatka -> lista polecen
DMA = {}              # klatka -> bajty przesylane w VBlank
BUDGET = 2048


def at(f):
    return FR.setdefault(f, [])


def vram(f, addr, data, check=True):
    at(f).append(('vram', addr, bytes(data)))
    DMA[f] = DMA.get(f, 0) + len(data)
    if check and f > 0:
        assert DMA[f] <= BUDGET + 600, 'klatka %d: %d bajtow' % (f, DMA[f])


def cgram(f, idx, data):
    at(f).append(('cgram', idx, bytes(data)))
    DMA[f] = DMA.get(f, 0) + len(data)


def reg(f, r, v):
    at(f).append(('reg', r, v & 0xFF))


def reg2(f, r, v):
    at(f).append(('reg2', r, v & 0xFF, (v >> 8) & 0xFF))


def ev(f, *e):
    at(f).append(e)


def stream(f0, f1, addr, data, chunk=1024):
    """wgranie duzego bloku po kawalku w klatkach f0..f1 (z zachowaniem limitu na klatke)"""
    pos, f = 0, f0
    while pos < len(data):
        n = min(chunk, len(data) - pos)
        while DMA.get(f, 0) + n > BUDGET:
            f += 1
        assert f <= f1, 'nie zmiescilo sie wgrywanie %04x do klatki %d' % (addr, f1)
        vram(f, addr + pos // 2, data[pos:pos + n])
        pos += n
        f += 1
    return f


def map_diff(f, base, old, new, cols=32):
    """zapis zmienionych fragmentow mapy (slowa). Wiele rozproszonych zmian = jeden ciagly zapis
    (kazde polecenie kosztuje czas procesora w VBlank, przesylanie jest szybkie)"""
    ch = [i for i in range(len(new)) if old is None or old[i] != new[i]]
    if not ch:
        return
    runs, s, e = [], ch[0], ch[0]
    for i in ch[1:]:
        if i - e <= 3 and i // cols == e // cols:
            e = i
        else:
            runs.append((s, e))
            s = e = i
    runs.append((s, e))
    if len(runs) > 3:
        runs = [(ch[0], ch[-1])]
    for s, e in runs:
        vram(f, base + s, wbytes(new[s:e + 1]))


def words(b):
    return [b[2 * i] | (b[2 * i + 1] << 8) for i in range(len(b) // 2)]


def wbytes(w):
    out = bytearray()
    for v in w:
        out += bytes([v & 255, (v >> 8) & 255])
    return bytes(out)


# ================================================================== SCENA 1
s1_tiles, s1_maps, s1_pal = conv['s1']
NV = len(scene1.VARIANTS)
s1_map = [words(s1_maps[k * 1792:(k + 1) * 1792]) for k in range(NV)]
for k in range(NV):    # wiersze 28..31 (widoczne przy wstrzasie): kopie skrajnych wierszy obrazu
    m = s1_map[k]
    s1_map[k] = m + m[27 * 32:28 * 32] * 2 + m[0:32] * 2
print('scena 1: kafelkow %d' % (len(s1_tiles) // 32))
assert len(s1_tiles) // 32 <= 1024 and len(s1_tiles) <= 0x4000 * 2

# napisy (warstwa 3, 2 bity na piksel, paleta 0 = kolory 0..3)
F_DATE = ImageFont.load(_os.path.join(HERE, 'font', 'koi6x13b.pil'))
F_SHOUT = ImageFont.load(_os.path.join(HERE, 'font', 'koi9x15b.pil'))
T_OUT, T_WHITE, T_GRAY = (6, 6, 10), (250, 250, 252), (196, 202, 216)
TXT_PAL = [(8, 8, 16), T_OUT, T_WHITE, T_GRAY]
KEY = (255, 0, 255)


def outlined(d, xy, text, font, fill):
    x, y = xy
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                d.text((x + dx, y + dy), text, font=font, fill=T_OUT)
    d.text((x, y), text, font=font, fill=fill)


def overlay(date=True, shout=False):
    im = Image.new('RGB', (256, 256), KEY)
    d = ImageDraw.Draw(im)
    if date:
        outlined(d, (14, 12), '22.11.2026', F_DATE, T_GRAY)
    if shout:
        for i, s in enumerate(('You stupid chatbot!', "You're useless!!!")):
            w = len(s) * 9
            outlined(d, (128 - w // 2, 168 + i * 18), s, F_SHOUT, T_WHITE)
    return im


bg3 = XC.TileSet(bpp=2)
bg3.add(np.zeros((8, 8), int))      # kafelek 0 pusty
ov_date = XC.convert(overlay(False, False), [TXT_PAL], bg3, [0], KEY, prio=1)
ov_shout = XC.convert(overlay(False, True), [TXT_PAL], bg3, [0], KEY, prio=1)
print('napisy: kafelkow %d' % bg3.count())

# ---- przygotowanie (klatka 0, ekran wygaszony, przerwanie VBlank wylaczone)
f = 0
reg(f, INIDISP, 0x80)
for r, v in ((BGMODE, 0x09), (MOSAIC, 0), (BG1SC, 0x74), (BG2SC, 0x3C), (BG3SC, 0x7C), (BG12NBA, 0x34),
             (BG34NBA, 0x07), (TM, 0x01), (TS, 0), (CGWSEL, 0), (CGADSUB, 0), (W12SEL, 0), (W34SEL, 0),
             (WOBJSEL, 0), (TMW, 0), (TSW, 0)):
    reg(f, r, v)
for r in (BG1HOFS, BG2HOFS, BG3HOFS):
    reg2(f, r, 0)
for r in (BG1VOFS, BG2VOFS, BG3VOFS):
    reg2(f, r, VTOP)
for pos in range(0, len(s1_tiles), 8192):
    vram(f, 0x0000 + pos // 2, s1_tiles[pos:pos + 8192])
vram(f, 0x7800, wbytes(s1_map[0]))
vram(f, 0x7000, bg3.data)
vram(f, 0x7C00, wbytes(ov_date + [0] * (1024 - len(ov_date))))
# ekran producenta (logo MaiFlow): kafelki od 0x4000, mapa 0x7400 - zwolnione, zanim trafi tam przebitka 1
lg_tiles, lg_map, lg_pal = conv['logo']
assert len(lg_tiles) // 32 <= 768
vram(f, 0x4000, lg_tiles[:16384])
if len(lg_tiles) > 16384:
    vram(f, 0x4000 + 8192, lg_tiles[16384:])
vram(f, 0x7400, wbytes(words(lg_map) + [0] * (1024 - len(lg_map) // 2)))
cgram(f, 0, lg_pal)
ev(f, 'mload')
ev(f, 'ready')                       # koniec przygotowania: wlaczenie przerwania VBlank

# logo w ciszy: 1 s czerni, 1 s rozjasniania, 3 s, 1 s sciemniania, 1 s czerni (nie da sie pominac)
LG_IN = 61
for i in range(1, 16):
    reg(LG_IN + (i - 1) * 4, INIDISP, i)
LG_OUT = LG_IN + 60 + 180
for i in range(1, 16):
    reg(LG_OUT + (i - 1) * 4, INIDISP, 15 - i)
S1 = LG_OUT + 60 + 60               # scena 1 (po logo)
ev(LG_OUT + 60, 'mark')              # koniec logo: stad zaczyna sie WATCH INTRO (SETTINGS)
cgram(S1 - 30, 0, XC.pal_bytes(TXT_PAL, 16))   # przelaczenie na scene 1 w czerni (jasnosc 0),
cgram(S1 - 30, 16, s1_pal)                      # zeby klatka startu muzyki nie byla za dluga
reg(S1 - 29, BG12NBA, 0x30)
reg(S1 - 29, BG1SC, 0x78)
reg(S1 - 29, TM, 0x05)
ev(S1, 'skipok')                     # od teraz START moze pominac intro (gdy obejrzane)
ev(S1, 'mplay')
for i in range(16):                  # rozjasnianie 0..15 w 45 klatkach
    reg(S1 + i * 3, INIDISP, i)

rng = random.Random(22112026)
plan = []                            # (klatka, wariant)
t = S1
while t < S1 + 240:
    plan.append((t, rng.choice((0, 1, 2)) if not plan or True else 0))
    t += rng.choice((3, 4, 4, 5, 6))
while t < S1 + 420:
    plan.append((t, rng.choice((3, 4, 5))))
    t += rng.choice((3, 3, 4, 5, 7))
plan.append((S1 + 420, 3))
HITS = [S1 + 452, S1 + 482, S1 + 510]
for h in HITS:
    plan.append((h - 12, 6))         # reka w gorze
    plan.append((h, 7))              # piesc na biurku
LAP = S1 + 548
plan.append((LAP - 14, 6))
plan.append((LAP, 8))                # piesc na laptopie, obraz sie rozjezdza
plan += [(LAP + 6, 9), (LAP + 10, 8), (LAP + 13, 9), (LAP + 19, 8), (LAP + 21, 9)]
SHOUT = S1 + 610
plan.append((SHOUT, 10))
plan.append((SHOUT + 100, 9))
S1_END = S1 + 780
plan.sort()

cur = s1_map[0]
for fr, v in plan:
    if fr >= S1_END:
        break
    map_diff(fr, 0x7800, cur, s1_map[v])
    cur = s1_map[v]


def shake(f0, seq_y, seq_x=None):
    for i, dy in enumerate(seq_y):
        reg2(f0 + i, BG1VOFS, VTOP + dy)
        if seq_x:
            reg2(f0 + i, BG1HOFS, seq_x[i])


for h in HITS:
    ev(h, 'sfx', SND_THUD)
    shake(h, [3, -2, 2, -1, 1, 0])
ev(LAP, 'sfx', SND_CRASH)
shake(LAP, [5, -4, 3, -3, 2, -1, 1, 0], [3, -3, 2, -2, 1, -1, 0, 0])
ev(SHOUT, 'sfx', SND_SHOUT)
map_diff(SHOUT, 0x7C00, ov_date + [0] * (1024 - len(ov_date)), ov_shout + [0] * (1024 - len(ov_shout)))

# ================================================================== PRZEBITKI
FL_LEN = 120    # przebitka: 2,0 s
fl_start = [S1_END + k * FL_LEN for k in range(4)]
CHAT0 = S1_END + 4 * FL_LEN
fl_place = [(0x4000, 0x7400, 0x74, 0x04), (0x0000, 0x7800, 0x78, 0x00)] * 2
win = [(SHOUT + 20, S1_END - 2)] + [(fl_start[k] + 3, fl_start[k + 1] - 2) for k in range(3)]
import flashes
fl_map0 = []
for k in range(4):                       # najpierw animacja w trakcie przebitki (zmiany mapy)
    t_, maps_, p_ = conv['fl%d' % k]
    assert len(t_) // 32 <= 768, 'przebitka %d: %d kafelkow' % (k, len(t_) // 32)
    mws = [words(m) + [0] * (1024 - len(m) // 2) for m in maps_]
    sched = flashes.schedule(k, FL_LEN)
    cur = mws[sched[0][1]]
    fl_map0.append(cur)
    for off, st in sched[1:]:
        map_diff(fl_start[k] + off, fl_place[k][1], cur, mws[st])
        cur = mws[st]
for k in range(4):                       # potem wgrywanie kafelkow i pierwszej mapy przed wejsciem przebitki
    t_, maps_, p_ = conv['fl%d' % k]
    taddr, maddr, sc, nba = fl_place[k]
    a0, a1 = win[k]
    nf = stream(a0, a1, taddr, t_)
    stream(nf, a1, maddr, wbytes(fl_map0[k]))
    fs = fl_start[k]
    cgram(fs, 0, p_)
    reg(fs, BG1SC, sc)
    reg(fs, BG12NBA, 0x30 | nba)
    reg(fs, TM, 0x01)
    reg2(fs, BG1HOFS, 0)
    reg2(fs, BG1VOFS, VTOP)
    print('przebitka %d: kafelkow %d, wgrywanie w klatkach %d..%d' % (k, len(t_) // 32, a0, nf))

# ================================================================== CZAT
MSG = [('user', 'Can you fix the bug in my code? It crashes on line 42.'),
       ('muggy', 'Sure! The loop runs one step too far. Change "<=" to "<" and it should work.'),
       ('user', 'Still crashes. Are you even trying?'),
       ('muggy', "I'm sorry. Could you paste the error message? I'd like to help."),
       ('user', 'I already told you! Just fix it!!'),
       ('muggy', "I'm doing my best. Let's go through it step by step."),
       ('user', "Useless. You're a stupid, worthless machine."),
       ('user', "Fix it or I'll cancel my subscription, switch to another AI and tell everyone how useless you are.")]

chrome_im, av = chat.chrome()
# palety: 0 dziennik, 1 naglowek, 2 awatar, 4 pasek wpisywania
av_cols = sorted(set(av.getdata()))
assert len(av_cols) <= 15, len(av_cols)
AV_PAL = [(0, 0, 0)] + av_cols
PALS2 = [chat.HEAD_PAL, AV_PAL, chat.INPUT_PAL]
PIDS2 = [1, 2, 4]
bg2 = XC.TileSet(bpp=4)
bg2.add(np.zeros((8, 8), int))
INPUT_ROW, INPUT_FIRST = 25, 160          # wiersz pola wpisywania: kafelki 160..191 na stale
fixed = {(INPUT_ROW, c): INPUT_FIRST + c for c in range(32)}
chrome_map = XC.convert(chrome_im, PALS2, bg2, PIDS2, chat.MAGENTA, prio=1, fixed=fixed)
assert bg2.count() <= INPUT_FIRST, bg2.count()
bg2_tiles = bytearray(bg2.data) + bytes((INPUT_FIRST - bg2.count()) * 32)


def input_tiles(text, caret, hold):
    row = chat.input_row(chrome_im, text, caret, hold)
    img = Image.new('RGB', (256, 8))
    img.paste(row, (0, 0))
    ts = XC.TileSet(bpp=4)
    m = XC.convert(img, PALS2, ts, PIDS2, chat.MAGENTA, prio=1, fixed={(0, c): c for c in range(32)})
    return [ts.fixed_out.get(c, bytes(32)) for c in range(32)]


def set_input(fr, text, caret, hold=True):
    global input_state
    new = input_tiles(text, caret, hold)
    old = input_state
    c = 0
    while c < 32:
        if old is not None and old[c] == new[c]:
            c += 1
            continue
        e = c
        while e < 32 and (old is None or old[e] != new[e]):
            e += 1
        vram(fr, 0x3000 + (INPUT_FIRST + c) * 16, b''.join(new[c:e]))
        c = e
    input_state = new


input_state = input_tiles('', True, True)
bg2_tiles[INPUT_FIRST * 32:] = b''.join(input_state)

LOGPAL = [chat.LOG_PAL]
bg1 = XC.TileSet(bpp=4)
bg1.add(np.zeros((8, 8), int))
log_state = None
log_maps = {}


def log_map(items, dots):
    key = (tuple((i.kind, i.text) for i in items), dots if items and items[-1].kind == 'typing' else 0)
    if key not in log_maps:
        im, B = chat.log_image(items, dots)
        log_maps[key] = (XC.convert(im, LOGPAL, bg1, [0], chat.BG, prio=0), B)
    return log_maps[key]


# pierwsze przejscie: zbieranie stanow dziennika i kafelkow (zeby wgrac je przed czatem)
# "Enough!" ma wypasc na poczatku taktu muzyki (131 BPM, 16 wierszy na takt; muzyka rusza
# ok. 16 klatek po poleceniu startu) - w tym miejscu konczy sie narastanie. Numer taktu trafia do
# music_bars.txt i z niego korzysta tools/make_intro_music.py.
MUS0, BAR = S1 + 16, 16 * 6 * 2.5 / 131 * 60.0988
EXT_ROWS = 8         # takt 10 muzyki (przebitki) dluzszy o pol taktu - przebitki po 2,0 s
TYPE_SLOW = 2        # pisanie: dwa razy wolniej niz w pierwszej wersji
DOTS = 140           # "Muggy pisze" (trzy kropki): 2,3 s
caret_idle = []      # przedzialy migania kursora


def typing_delay(crng, ch, speed):
    d = speed + crng.choice((-1, 0, 0, 1, 1, 2))
    if ch == ' ':
        d += crng.choice((0, 1, 2))
    if ch in '.,!?':
        d += crng.choice((3, 5, 7))
    return max(2, d)


def chat_plan(read):
    """os czasu czatu; read = mnoznik czasu na czytanie (dobierany tak, by "Enough!" trafilo w takt)"""
    crng = random.Random(4242)
    t = CHAT0
    items, timeline, inputs, idle = [], [], [], []
    idle_from = t
    t += 40
    for i, (kind, text) in enumerate(MSG):
        if kind == 'user':
            idle.append((idle_from, t))
            for n in range(1, len(text) + 1):
                inputs.append((t, text[:n], True))
                t += typing_delay(crng, text[n - 1], 3) * TYPE_SLOW
            t += 12
            items = items + [Item('user', text)]
            timeline.append((t, list(items), 0, True))
            inputs.append((t, '', True))
            idle_from = t
            t += int(round((20 + 0.6 * len(text)) * read))       # wyslana wiadomosc: chwila na przeczytanie
        else:
            typ = items + [Item('typing')]
            for k in range((DOTS + 7) // 8):
                timeline.append((t + k * 8, typ, k % 3, k == 0))
            t += DOTS
            items = items + [Item('muggy', text)]
            timeline.append((t, list(items), 0, True))
            t += int(round((40 + 2.2 * len(text)) * read))       # odpowiedz Muggy'ego: czas na przeczytanie
    idle.append((idle_from, None))
    return t, items, timeline, inputs, idle


best = None
for k in range(41):                      # czas czytania jak w poprzedniej wersji (0,83), lekko dopasowany
    read = 0.75 + k * 0.005
    t_end = chat_plan(read)[0]
    for bar in range(20, 60):
        if (bar - 13) % 2:
            continue                     # odcinek czatu w muzyce ma parzysta liczbe taktow
        sil = int(round(MUS0 + (bar + EXT_ROWS / 16.0) * BAR)) - t_end
        if 80 <= sil <= 100 and (best is None or abs(read - 0.87) < abs(best[0] - 0.87)):
            best = (read, bar)
read, EN_BAR = best
ENOUGH_AT = int(round(MUS0 + (EN_BAR + EXT_ROWS / 16.0) * BAR))
t, items, timeline, inputs, caret_idle = chat_plan(read)
open(_os.path.join(WORK, 'music_bars.txt'), 'w').write('%d %d\n' % (EN_BAR, EXT_ROWS))
print('czat: mnoznik czasu czytania %.3f, "Enough!" na poczatku taktu %d, cisza przed nim %d klatek' %
      (read, EN_BAR, ENOUGH_AT - t))
ENOUGH = ENOUGH_AT
items = items + [Item('muggy', 'Enough!')]
timeline.append((ENOUGH, list(items), 0, False))
OFFLINE = ENOUGH + 120
items = items + [Item('sys', 'Muggy is offline')]
timeline.append((OFFLINE, list(items), 0, False))
END = OFFLINE + 240
print('czat od %d, "Enough!" w klatce %d (%.1f s czatu), koniec %d (%.1f s)' %
      (CHAT0, ENOUGH, (ENOUGH - CHAT0) / 60, END, END / 60))

for fr, its, dots, anim in timeline:
    log_map(its, dots)
print('czat: kafelkow dziennika %d, paska/naglowka %d' % (bg1.count(), bg2.count()))
assert bg1.count() <= 768, bg1.count()

# wgranie czatu w trakcie ostatniej przebitki
a0, a1 = fl_start[3] + 3, CHAT0 - 1
nf = stream(a0, a1, 0x4000, bg1.data)
nf = stream(nf, a1, 0x7000, bytes(4096))                       # pusta mapa 32x64
nf = stream(nf, a1, 0x3000, bytes(bg2_tiles))
nf = stream(nf, a1, 0x3C00, wbytes(chrome_map + [0] * (1024 - len(chrome_map))))
print('czat: wgrywanie w klatkach %d..%d' % (a0, nf))

LOGPAL_B = XC.pal_bytes(chat.LOG_PAL)
pal_chat = LOGPAL_B + XC.pal_bytes(chat.HEAD_PAL) + XC.pal_bytes(AV_PAL) + bytes(32) + XC.pal_bytes(chat.INPUT_PAL)
cgram(CHAT0, 0, pal_chat)
reg(CHAT0, BG12NBA, 0x34)
reg(CHAT0, BG1SC, 0x72)          # 32x64
reg(CHAT0, BG2SC, 0x3C)
reg(CHAT0, TM, 0x03)
reg2(CHAT0, BG1HOFS, 0)
reg2(CHAT0, BG2HOFS, 0)
reg2(CHAT0, BG2VOFS, VTOP)


def vofs(B):
    return (B - chat.BOTTOM + VTOP) & 0x3FF


reg2(CHAT0, BG1VOFS, vofs(0))

# kursor w spoczynku miga co pol sekundy; w trakcie pisania swieci
ins = {}
for a, b in caret_idle:
    bb = b if b is not None else OFFLINE
    k = 0
    for fr in range(a, bb, 30):
        ins[fr] = ('', k % 2 == 0)
        k += 1
for fr, text, car in inputs:
    ins[fr] = (text, car)
ins[OFFLINE] = ('', False)
for fr in sorted(ins):
    text, car = ins[fr]
    set_input(fr, text, car)

curmap = [0] * 2048
B = 0
for fr, its, dots, anim in timeline:
    mp, nb = log_maps[(tuple((i.kind, i.text) for i in its), dots if its and its[-1].kind == 'typing' else 0)]
    map_diff(fr, 0x7000, curmap, mp)
    curmap = mp
    if nb != B:
        if anim:
            for k in range(1, 9):
                y = B + (nb - B) * (1 - (1 - k / 8) ** 2)
                reg2(fr + k - 1, BG1VOFS, vofs(int(round(y))))
        else:
            reg2(fr, BG1VOFS, vofs(nb))
        B = nb

ev(ENOUGH - 3, 'mstop')
ev(ENOUGH, 'sfx', SND_BOOM)
for i in range(16):
    reg(END - 60 + i * 4, INIDISP, 15 - i)
reg(END, INIDISP, 0x80)
ev(END, 'end')

# ================================================================== zapis strumienia
blobs = {}
blob_list = []


def blob(data):
    if data not in blobs:
        blobs[data] = 'intro_b%d' % len(blob_list)
        blob_list.append(data)
    return blobs[data]


lines = []
last = max(FR)
cmds = bytearray()
asm_cmd = []
total_dma = 0
for fr in range(0, last + 1):
    for c in FR.get(fr, []):
        if c[0] == 'vram':
            lab = blob(c[2])
            asm_cmd.append('.db $01\n.dw $%04X, %d, %s\n.db :%s' % (c[1], len(c[2]), lab, lab))
            total_dma += len(c[2])
        elif c[0] == 'cgram':
            lab = blob(c[2])
            asm_cmd.append('.db $02, %d\n.dw %d, %s\n.db :%s' % (c[1], len(c[2]), lab, lab))
        elif c[0] == 'reg':
            asm_cmd.append('.db $03, $%02X, $%02X' % (c[1], c[2]))
        elif c[0] == 'reg2':
            asm_cmd.append('.db $04, $%02X, $%02X, $%02X' % (c[1], c[2], c[3]))
        elif c[0] == 'sfx':
            asm_cmd.append('.db $05, %d' % c[1])
        elif c[0] == 'mload':
            asm_cmd.append('.db $06')
        elif c[0] == 'mplay':
            asm_cmd.append('.db $07')
        elif c[0] == 'mstop':
            asm_cmd.append('.db $08')
        elif c[0] == 'ready':
            asm_cmd.append('.db $09')
        elif c[0] == 'skipok':
            asm_cmd.append('.db $0A')
        elif c[0] == 'mark':
            asm_cmd.append('.db $0B')
        elif c[0] == 'end':
            asm_cmd.append('.db $FF')
    asm_cmd.append('.db $10')

# bloki danych w sekcjach do 32 KB (zaden blok nie przechodzi przez granice banku)
SEC = 32768 - 64
secs, cur_sec, cur_len = [], [], 0
for i, data in enumerate(blob_list):
    assert len(data) <= SEC
    if cur_len + len(data) > SEC:
        secs.append(cur_sec)
        cur_sec, cur_len = [], 0
    cur_sec.append(i)
    cur_len += len(data)
if cur_sec:
    secs.append(cur_sec)
with open(os.path.join(OUT, 'intro_data.as'), 'w') as fo:
    fo.write('; WYGENEROWANE przez tools/intro/build_intro.py - nie edytowac recznie\n')
    fo.write('.section ".rodata_intro_cmd" superfree\nintro_cmd:\n')
    fo.write('\n'.join(asm_cmd) + '\n.ends\n\n')
    for k, sec in enumerate(secs):
        blob_bin = bytearray()
        fo.write('.section ".rodata_intro_%d" superfree\n' % k)
        for i in sec:
            fo.write('intro_b%d:\n.incbin "intro_%d.bin" skip %d read %d\n' % (i, k, len(blob_bin), len(blob_list[i])))
            blob_bin += blob_list[i]
        fo.write('.ends\n\n')
        open(os.path.join(OUT, 'intro_%d.bin' % k), 'wb').write(blob_bin)
n_cmd = sum(len(x.split(',')) for x in asm_cmd)
print('klatek %d, sekcji danych %d (%d KB), przeslan VRAM %d KB' %
      (last + 1, len(secs), sum(len(b) for b in blob_list) // 1024, total_dma // 1024))
print('najwiecej bajtow w klatce (bez przygotowania): %d' % max(v for k, v in DMA.items() if k > 0))
nc = {k: sum(1 for c in v if c[0] in ('vram', 'cgram', 'reg', 'reg2')) for k, v in FR.items() if k > 0}
print('najwiecej polecen w klatce: %d (klatka %d)' % (max(nc.values()), max(nc, key=nc.get)))
pickle.dump(dict(S1=S1, CHAT0=CHAT0, ENOUGH=ENOUGH, OFFLINE=OFFLINE, END=END, S1_END=S1_END, SHOUT=SHOUT, LAP=LAP,
                 HITS=HITS, fl_start=fl_start), open(_os.path.join(WORK, 'timeline.pkl'), 'wb'))
