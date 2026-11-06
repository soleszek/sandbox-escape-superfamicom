import sys; sys.path.insert(0, '/home/claude/mus')
from kit import *
OUT = '/home/claude/mus/out/'

def malten():   # zwodniczy, zmienne metrum (4/4 -> 7/8 -> 3/4), fantasmagoria, skala calotonowa
    t = T('Malten Phantasm', 7, tempo=96)
    PAD = add_tonal(t.s, 'pad', 'strings', 52); BELL = add_decay(t.s, 'glass', [1, 0, .5, 0, .3], 0.6, 0.35, inharm=[1, 2.4, 3.9, 5.4, 6.8])
    LEAD = add_tonal(t.s, 'lead', 'flute'); BASS = add_tonal(t.s, 'bass', 'sine'); KICK = add_drum(t.s, 'kick'); CLAP = add_drum(t.s, 'clap'); HAT = add_drum(t.s, 'hat')
    A = t.pat(64, tempo=96, speed=6)
    ch = [('E-4', 'm'), ('C-4', 'M'), ('A-3', 'm'), ('B-3', '7')]
    t.block(A, [0], PAD, ch, vol=26, ln=15); t.arp(A, 1, BELL, ch, step=2, octs=1, order=(0, 1, 2, 3, 2, 1), vol=30)
    for b, (r, q) in enumerate(ch): t.note(A, b * 16, 3, n(r) - 12, BASS, 44, 14)
    t.seq(A, 2, LEAD, [('E-5', 6), ('G-5', 2), ('F#5', 8), ('E-5', 6), ('B-4', 10), ('C-5', 6), ('E-5', 2), ('D#5', 8), ('B-4', 16)], vol=44, fx=(8, 0x34))
    t.drum(A, 4, KICK, 'X.......x.......'); t.drum(A, 5, CLAP, '....X.......X..x'); t.drum(A, 6, HAT, '..x...x...x...x.', vols=(24, 18))
    B = t.pat(56)   # 7/8: takty po 14 wierszy (2+2+3)
    for b in range(4):
        r = b * 14; root = ['E-3', 'F#3', 'G#3', 'A#3'][b]
        t.note(B, r, 3, root, BASS, 44, 12); t.note(B, r, 0, n(root) + 12, PAD, 24, 13)
        for i, iv in enumerate([0, 4, 8, 12, 8, 4, 2]): t.note(B, r + 2 * i, 1, n(root) + 24 + iv, BELL, 30, 2)
        t.drum(B, 4, KICK, 'X...x...x.....', start=r, bars=1); t.drum(B, 5, CLAP, '........X...x.', start=r, bars=1)
    t.seq(B, 2, LEAD, [('E-5', 4), ('F#5', 4), ('G#5', 6), ('A#5', 4), ('C-6', 4), ('D-6', 6), ('C-6', 14), ('A#5', 14)], vol=42, fx=(8, 0x46))
    C = t.pat(48)   # 3/4: widmowy walc
    for b, (r, q) in enumerate([('E-4', 'm'), ('A-3', 'm'), ('B-3', '7'), ('E-4', 'm')]):
        t.note(C, b * 12, 3, n(r) - 12, BASS, 46, 4)
        for h in (4, 8): t.block(C, [0], PAD, [(r, q)], bar=12, vol=24, ln=3, hits=(h,), start=b * 12)
    t.seq(C, 2, LEAD, [('B-5', 6), ('A-5', 6), ('G-5', 12), ('F#5', 6), ('E-5', 6), ('D#5', 12)], vol=44, fx=(8, 0x36))
    t.drum(C, 6, HAT, 'x...x...x...', vols=(22, 22))
    D = t.pat(64)
    t.block(D, [0], PAD, ch, vol=26, ln=15); t.arp(D, 1, BELL, ch, step=1, octs=1, order=(0, 2, 1, 3), vol=26)
    for b, (r, q) in enumerate(ch): t.note(D, b * 16, 3, n(r) - 12, BASS, 44, 14)
    t.seq(D, 2, LEAD, [('E-6', 6), ('G-6', 2), ('F#6', 8), ('E-6', 6), ('B-5', 10), ('C-6', 6), ('E-6', 2), ('D#6', 8), ('B-5', 16)], vol=40, fx=(8, 0x44))
    t.drum(D, 4, KICK, 'X.....x...x.....'); t.drum(D, 5, CLAP, '....X.......X...')
    return t.save(OUT + 'malten.it', [A, B, A, C, D, B])

def waller():   # sredniowiecze: dorycki, burdon, flet, lutnia, wojenne bebny
    t = T('Waller Siege', 7, tempo=132)
    DR = add_tonal(t.s, 'drone', 'reed', 40); FL = add_tonal(t.s, 'recorder', 'pulse'); LUTE = add_decay(t.s, 'lute', [1, .6, .4, .25, .15], 0.45, 0.25)
    TOM = add_drum(t.s, 'tom'); SN = add_drum(t.s, 'snare'); KICK = add_drum(t.s, 'kick'); CR = add_drum(t.s, 'crash')
    def base(p, chords):
        t.note(p, 0, 0, 'D-3', DR, 30); t.note(p, 0, 1, 'A-3', DR, 26)
        t.arp(p, 3, LUTE, chords, step=2, order=(0, 1, 2, 3, 2, 1, 0, 1), vol=34)
        t.drum(p, 4, TOM, 'X.x.xxx.X.x.xxx.', vols=(54, 40)); t.drum(p, 5, SN, '....X..x....X.xx', vols=(46, 30)); t.drum(p, 6, KICK, 'X.......X.......')
    A = t.pat(64, tempo=132, speed=6); base(A, [('D-4', 'm'), ('C-4', 'M'), ('D-4', 'm'), ('G-3', 'M')])
    t.seq(A, 2, FL, [('D-5', 4), ('E-5', 2), ('F-5', 2), ('G-5', 4), ('A-5', 4), ('G-5', 2), ('F-5', 2), ('E-5', 4), ('C-5', 4), ('D-5', 4), ('F-5', 4), ('E-5', 2), ('D-5', 2), ('C-5', 4), ('B-4', 4), ('A-4', 4), ('D-5', 12)], vol=46)
    t.note(A, 0, 6, 'C-5', CR, 36)
    B = t.pat(64); base(B, [('C-4', 'M'), ('A-3', 'm'), ('F-3', 'M'), ('A-3', 'M')])
    t.seq(B, 2, FL, [('G-5', 4), ('A-5', 4), ('C-6', 4), ('B-5', 2), ('A-5', 2), ('G-5', 8), ('E-5', 8), ('F-5', 4), ('G-5', 4), ('A-5', 4), ('G-5', 2), ('F-5', 2), ('E-5', 8), ('C#5', 8)], vol=46)
    t.note(B, 0, 6, 'C-5', CR, 36); t.note(B, 32, 6, 'C-5', CR, 30)
    A2 = t.pat(64); base(A2, [('D-4', 'm'), ('C-4', 'M'), ('D-4', 'm'), ('A-3', 'M')])
    t.seq(A2, 2, FL, [('A-5', 4), ('G-5', 2), ('A-5', 2), ('F-5', 4), ('D-5', 4), ('E-5', 4), ('F-5', 4), ('G-5', 8), ('F-5', 4), ('E-5', 4), ('D-5', 4), ('C-5', 4), ('D-5', 8), ('A-4', 8)], vol=46)
    for r in range(56, 64): t.note(A2, r, 5, 'C-5', SN, 30 + (r - 56) * 3)   # werbel przed powtorka
    return t.save(OUT + 'waller.it', [A, A2, B, A2])

def doppler():   # trance 138 BPM, fis-moll frygijski (Fis-G), bramkowany syntezator 3-3-2
    t = T('Cyber Doppler', 7, tempo=138)
    KICK = add_drum(t.s, 'kick'); OH = add_drum(t.s, 'ohat'); CLAP = add_drum(t.s, 'clap'); BASS = add_tonal(t.s, 'bass', 'saw', 56)
    GATE = add_tonal(t.s, 'gate', 'pulse'); LEAD = add_tonal(t.s, 'lead', 'square'); PAD = add_tonal(t.s, 'pad', 'strings', 40)
    ch = [('F#3', 'm'), ('G-3', 'M'), ('F#3', 'm'), ('E-3', 'M')]
    def groove(p, bass=True, kick=True):
        if kick: t.drum(p, 0, KICK, 'X...X...X...X...')
        t.drum(p, 1, OH, '..x...x...x...x.', vols=(24, 24))
        if kick: t.drum(p, 2, CLAP, '....X.......X...', vols=(38, 38))
        if bass:
            for b, (r, q) in enumerate(ch):
                for row in (1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15):   # toczacy sie bas miedzy uderzeniami stopy
                    t.note(p, b * 16 + row, 3, n(r) - 12 + (12 if row % 4 == 3 else 0), BASS, 44 if row % 4 == 1 else 32, 1)
    def gate(p, vol=30, up=0):
        for b, (r, q) in enumerate(ch):
            c = t.chord_notes(r, q)
            for k, row in enumerate((0, 3, 6, 8, 11, 14)):   # 3-3-2, 3-3-2
                t.note(p, b * 16 + row, 4, c[(k + b) % 3] + 12 + up, GATE, vol if row in (0, 8) else vol - 8, 2)
    I = t.pat(64, tempo=138, speed=6); groove(I, bass=False); gate(I)
    V = t.pat(64); groove(V); gate(V)
    t.seq(V, 5, LEAD, [('-', 8), ('C#5', 2), ('D-5', 2), ('C#5', 4), ('-', 8), ('A-4', 2), ('G-4', 2), ('F#4', 4), ('-', 8),
                       ('C#5', 2), ('D-5', 2), ('E-5', 4), ('-', 8), ('D-5', 2), ('C#5', 2), ('B-4', 4)], vol=36)
    F = t.pat(64); groove(F); gate(F, vol=26, up=12); t.block(F, [6], PAD, ch, vol=22, ln=15)
    t.seq(F, 5, LEAD, [('F#5', 6), ('G-5', 2), ('F#5', 4), ('C#5', 4), ('D-5', 6), ('C#5', 2), ('B-4', 8), ('A-4', 6), ('B-4', 2), ('C#5', 4), ('F#5', 4), ('E-5', 6), ('D-5', 2), ('E-5', 8)], vol=42, fx=(8, 0x22))
    K = t.pat(64); t.block(K, [6], PAD, ch, vol=28, ln=15); t.drum(K, 1, OH, '..x...x...x...x.', vols=(18, 18))
    t.seq(K, 5, LEAD, [('C#6', 12), ('D-6', 4), ('C#6', 8), ('A-5', 8), ('G-5', 12), ('F#5', 4), ('E-5', 16)], vol=38, fx=(8, 0x24))
    for i, r in enumerate(range(0, 64, 2)): t.note(K, r, 4, n('F#6') - (i % 12), GATE, 18, 2)   # opadajace "kody"
    return t.save(OUT + 'doppler.it', [I, V, F, K, F])

def changero():   # obled: cyrk -> swing -> chromatyczny szal -> 5/4
    t = T('Changero Madness', 7, tempo=150)
    BASS = add_decay(t.s, 'pizz', [1, .5, .3, .15], 0.35, 0.18); CH = add_tonal(t.s, 'organ', 'organ', 44); LEAD = add_tonal(t.s, 'lead', 'square')
    CNT = add_tonal(t.s, 'counter', 'saw', 44); KICK = add_drum(t.s, 'kick'); SN = add_drum(t.s, 'snare'); HAT = add_drum(t.s, 'hat')
    P0 = t.pat(64, tempo=150, speed=6)   # cyrkowa polka
    for b in range(8):
        r = b * 8; root = ['C-3', 'G-2', 'C-3', 'G-2', 'F-2', 'C-3', 'G-2', 'C-3'][b]
        t.note(P0, r, 0, root, BASS, 50); t.note(P0, r + 4, 0, n(root) + 7, BASS, 44)
        t.block(P0, [1], CH, [(n(root) + 12, 'M')] if False else [('C-4', 'M') if b % 2 == 0 else ('B-3', 'dim')], bar=8, vol=26, ln=2, hits=(2, 6), start=r)
    t.seq(P0, 2, LEAD, [('E-5', 2), ('D#5', 2), ('E-5', 2), ('G-5', 2), ('F-5', 2), ('E-5', 2), ('D-5', 4), ('B-4', 2), ('C-5', 2), ('D-5', 2), ('F-5', 2), ('E-5', 8),
                        ('A-5', 2), ('G#5', 2), ('A-5', 2), ('C-6', 2), ('B-5', 2), ('A-5', 2), ('G-5', 4), ('F-5', 2), ('E-5', 2), ('D-5', 2), ('B-4', 2), ('C-5', 8)], vol=46)
    t.drum(P0, 4, KICK, 'X...X...'); t.drum(P0, 5, SN, '..x...x.', vols=(30, 30))
    P1 = t.pat(48, tempo=112)   # nagly swing
    for b, (r, q) in enumerate([('D-3', 'm7'), ('G-2', '7'), ('C-3', 'M7')]):
        for k, iv in enumerate([0, 7, 12, 10]): t.note(P1, b * 16 + k * 4, 0, n(r) + iv, BASS, 46, 3)
        t.block(P1, [1], CH, [(n(r) + 12 if False else ('C-4', 'M7'))], vol=24, ln=2, hits=(3, 11), start=b * 16)
    t.seq(P1, 2, LEAD, [('A-5', 3), ('F-5', 1), ('D-5', 4), ('C-5', 3), ('A-4', 5), ('B-4', 3), ('D-5', 1), ('F-5', 4), ('G#5', 4), ('A-5', 8), ('E-5', 4), ('C-5', 4), ('-', 4)], vol=44)
    t.drum(P1, 6, HAT, 'x..xx..xx..xx..x', vols=(26, 18)); t.drum(P1, 4, KICK, 'X.......X.......', vols=(40, 40))
    P2 = t.pat(32, tempo=176)   # chromatyczny szal
    for i in range(32): t.note(P2, i, 2, n('C-5') + (i if i < 16 else 31 - i), LEAD, 40, 1)
    for i in range(0, 32, 2): t.note(P2, i, 3, n('C-4') - (i // 2) % 12, CNT, 34, 1)
    t.drum(P2, 4, KICK, 'X.X.X.X.'); t.drum(P2, 5, SN, '..X...X.X...X.XX', vols=(40, 34))
    P3 = t.pat(60, tempo=140)   # 5/4: takty po 20 wierszy
    for b in range(3):
        r = b * 20
        for k, row in enumerate((0, 6, 12, 16)): t.note(P3, r + row, 0, n('A-2') + [0, 7, 3, 10][k] + b, BASS, 46, 3)
        t.drum(P3, 4, KICK, 'X.....x.....X...x...', start=r, bars=1); t.drum(P3, 5, SN, '....x.....X.....X.x.', start=r, bars=1)
    t.seq(P3, 2, LEAD, [('A-5', 6), ('G#5', 6), ('F-5', 8), ('E-5', 6), ('D#5', 6), ('C-5', 8), ('B-4', 10), ('E-5', 10)], vol=44, fx=(8, 0x66))
    return t.save(OUT + 'changero.it', [P0, P1, P2, P0, P3, P2])

def chronos():   # sentymentalny, podniosly, tykajacy zegar
    t = T('Chronos Eternity', 7, tempo=72)
    TICK = add_drum(t.s, 'tick'); STR = add_tonal(t.s, 'strings', 'strings', 52); LEAD = add_tonal(t.s, 'horn', 'horn')
    BASS = add_tonal(t.s, 'cello', 'strings', 56); BELL = add_decay(t.s, 'chime', [1, 0, .6, 0, .4, .2], 1.2, 0.8, inharm=[1, 2, 3, 4.2, 5.4, 6.8])
    prog = [('D-4', 'M'), ('A-3', 'M'), ('B-3', 'm'), ('F#3', 'm'), ('G-3', 'M'), ('D-4', 'M'), ('E-4', 'm'), ('A-3', 'M')]
    def bed(p, vol=26):
        t.block(p, [1, 2, 3], STR, prog, vol=vol, ln=15)
        for b, (r, q) in enumerate(prog): t.note(p, b * 16, 5, n(r) - 12, BASS, 40, 15)
        for r in range(0, 128, 4): t.note(p, r, 0, 'C-5' if (r // 4) % 2 == 0 else 'G-4', TICK, 30)   # tyk-tak
        for r in range(0, 128, 32): t.note(p, r, 6, 'D-5', BELL, 34)
    A = t.pat(128, tempo=72, speed=6); bed(A)
    t.seq(A, 4, LEAD, [('F#5', 16), ('E-5', 16), ('D-5', 16), ('C#5', 16), ('B-4', 16), ('A-4', 16), ('B-4', 16), ('C#5', 16)], vol=44, fx=(8, 0x23))
    B = t.pat(128); bed(B, vol=28)
    t.seq(B, 4, LEAD, [('A-5', 8), ('F#5', 4), ('G-5', 4), ('A-5', 8), ('F#5', 4), ('G-5', 4), ('A-5', 4), ('A-4', 4), ('B-4', 4), ('C#5', 4), ('D-5', 4), ('E-5', 4), ('F#5', 4), ('G-5', 4),
                       ('F#5', 8), ('D-5', 4), ('E-5', 4), ('F#5', 8), ('F#4', 4), ('G-4', 4), ('A-4', 8), ('B-4', 8), ('A-4', 8), ('G-4', 8), ('A-4', 16)], vol=46, fx=(8, 0x23))
    return t.save(OUT + 'chronos.it', [A, B])

def magneton():   # elektro-rock z impulsami elektrycznymi
    t = T('Magneton Voltage', 7, tempo=140)
    KICK = add_drum(t.s, 'kick'); SN = add_drum(t.s, 'snare'); HAT = add_drum(t.s, 'hat'); GTR = add_tonal(t.s, 'guitar', 'power', 52)
    GTR2 = add_tonal(t.s, 'guitar5', 'power', 44); BASS = add_tonal(t.s, 'bass', 'square', 56); ZAP = add_drum(t.s, 'zap')
    riff = [('E-4', 2), ('E-4', 2), ('G-4', 2), ('E-4', 2), ('A-4', 2), ('E-4', 2), ('B-4', 2), ('A-4', 2)]
    def rock(p, chorus=False):
        t.drum(p, 0, KICK, 'X.....X.X.......'); t.drum(p, 1, SN, '....X.......X...'); t.drum(p, 2, HAT, 'x.x.x.x.x.x.x.x.', vols=(24, 24))
        roots = ['E-3', 'C-3', 'D-3', 'B-2']
        for b, r in enumerate(roots):
            for row in range(0, 16, 2): t.note(p, b * 16 + row, 5, r, BASS, 44, 2)
            if chorus:
                t.note(p, b * 16, 3, n(r) + 12, GTR, 40, 7); t.note(p, b * 16, 4, n(r) + 19, GTR2, 34, 7)
                t.note(p, b * 16 + 8, 3, n(r) + 12, GTR, 36, 7); t.note(p, b * 16 + 8, 4, n(r) + 19, GTR2, 30, 7)
        for r in (14, 46): t.note(p, r, 6, 'C-5', ZAP, 30)
    I = t.pat(64, tempo=140, speed=6)
    for r in range(0, 64, 8): t.note(I, r, 6, 'C-5' if r % 16 == 0 else 'G-4', ZAP, 34)
    t.seq(I, 3, GTR, riff * 4, vol=40)
    V = t.pat(64); rock(V); t.seq(V, 3, GTR, riff * 4, vol=42); t.seq(V, 4, GTR2, riff * 4, vol=26, shift=7)
    C = t.pat(64); rock(C, chorus=True)
    for r in (0, 32): t.note(C, r, 6, 'C-5', ZAP, 32)
    B = t.pat(64); t.drum(B, 0, KICK, 'X.......X.......'); t.drum(B, 2, HAT, 'x...x...x...x...', vols=(20, 20))
    for r in range(0, 64, 4): t.note(B, r, 6, n('C-5') + (r // 4) % 5, ZAP, 26)
    t.seq(B, 3, GTR, [('E-5', 8), ('D-5', 8), ('B-4', 16), ('G-4', 8), ('A-4', 8), ('B-4', 16)], vol=36, fx=(8, 0x46))
    return t.save(OUT + 'magneton.it', [I, V, C, V, B, C])

def telementor():   # horror, nadprzyrodzone, kosmici (Roswell): theremin, burdon z trytonem, sygnaly
    t = T('Telementor Roswell', 7, tempo=84)
    DR = add_tonal(t.s, 'drone', 'strings', 44); THER = add_tonal(t.s, 'theremin', 'sine'); BEEP = add_drum(t.s, 'beep'); KICK = add_drum(t.s, 'kick')
    BELL = add_decay(t.s, 'eerie', [1, .7, .5, .4], 1.4, 0.9, inharm=[1, 2.76, 5.4, 8.93]); PAD = add_tonal(t.s, 'pad', 'organ', 36)
    def bed(p, roots):
        for b, r in enumerate(roots):
            t.note(p, b * 32, 0, r, DR, 30, 31); t.note(p, b * 32, 1, n(r) + 6, DR, 22, 31)   # tryton
        for r in range(0, t.rows(p), 16): t.note(p, r, 4, 'C-5', KICK, 44); t.note(p, r + 3, 4, 'C-5', KICK, 30)   # bicie serca
    A = t.pat(64, tempo=84, speed=6); bed(A, ['C-3', 'G#2'])
    t.seq(A, 2, THER, [('G-5', 12), ('F#5', 4), ('D#5', 16), ('C-5', 12), ('D-5', 4), ('B-4', 16)], vol=42, fx=(8, 0x58))
    for r in (10, 26, 42, 58): t.note(A, r, 3, 'C-6', BEEP, 24); t.note(A, r + 1, 3, 'G-5', BEEP, 20)
    B = t.pat(64); bed(B, ['F#2', 'G-2'])
    t.block(B, [5], PAD, [('F#3', 'dim'), ('F#3', 'dim'), ('G-3', 'sus4'), ('G-3', 'M')], vol=22, ln=15)
    t.seq(B, 2, THER, [('C-6', 8), ('A-5', 8), ('F#5', 16), ('G-5', 8), ('D-6', 8), ('B-5', 16)], vol=42, fx=(8, 0x68))
    t.note(B, 0, 6, 'C-5', BELL, 34); t.note(B, 32, 6, 'F#4', BELL, 30)
    for r in range(48, 64, 2): t.note(B, r, 3, n('C-6') + (r % 7), BEEP, 22)
    return t.save(OUT + 'telementor.it', [A, B, A, B])

def blinker():   # kolory i abstrakcja w stylu Jean-Michela Jarre'a: sekwencer, analogowe plamy
    t = T('Blinker Chroma', 7, tempo=110)
    SEQ = add_tonal(t.s, 'seq', 'saw', 50); SEQ2 = add_decay(t.s, 'spark', [1, .5, .3, .2], 0.3, 0.15); LEAD = add_tonal(t.s, 'lead', 'sine')
    PAD = add_tonal(t.s, 'pad', 'strings', 44); KICK = add_drum(t.s, 'kick'); CLAP = add_drum(t.s, 'clap'); HAT = add_drum(t.s, 'hat')
    ch = [('C-4', 'm'), ('G#3', 'M'), ('D#4', 'M'), ('A#3', 'M')]
    def seqline(p, vol=30):
        for b, (r, q) in enumerate(ch):
            c = t.chord_notes(r, q)
            for i in range(16): t.note(p, b * 16 + i, 0, [c[0] - 12, c[0], c[1], c[0], c[2], c[0], c[1] + 12, c[0]][i % 8], SEQ, vol if i % 4 == 0 else vol - 8, 1)
    A = t.pat(64, tempo=110, speed=6); seqline(A); t.block(A, [3], PAD, ch, vol=24, ln=15)
    t.seq(A, 2, LEAD, [('G-5', 12), ('A#5', 4), ('C-6', 16), ('D#6', 12), ('D-6', 4), ('A#5', 16)], vol=42, fx=(8, 0x34))
    t.drum(A, 4, KICK, 'X.......X.......', vols=(38, 38))
    B = t.pat(64); seqline(B); t.block(B, [3], PAD, ch, vol=24, ln=15)
    t.arp(B, 1, SEQ2, ch, step=2, octs=2, order=(0, 2, 1, 3, 2, 0, 1, 2), vol=24)
    t.seq(B, 2, LEAD, [('C-6', 8), ('D-6', 8), ('D#6', 8), ('F-6', 8), ('G-6', 12), ('F-6', 4), ('D#6', 8), ('D-6', 8)], vol=40, fx=(8, 0x34))
    t.drum(B, 4, KICK, 'X...X...X...X...', vols=(40, 40)); t.drum(B, 5, CLAP, '....X.......X...', vols=(32, 32)); t.drum(B, 6, HAT, '..x...x...x...x.', vols=(20, 20))
    return t.save(OUT + 'blinker.it', [A, B, A, B])

def kimantero():   # final: organy w stylu Castlevanii, burzowy, bardzo dynamiczny
    t = T('Kimantero Final Storm', 7, tempo=152)
    ORG = add_tonal(t.s, 'organ', 'organ', 56); ORG2 = add_tonal(t.s, 'organ2', 'organ', 46); BASS = add_tonal(t.s, 'bass', 'saw', 56)
    HARP = add_decay(t.s, 'harpsi', [1, .8, .6, .5, .4, .3, .2], 0.3, 0.15); KICK = add_drum(t.s, 'kick'); SN = add_drum(t.s, 'snare'); TIMP = add_drum(t.s, 'timp')
    I = t.pat(64, tempo=152, speed=6)   # wstep: toccata
    t.seq(I, 0, ORG, [('A-5', 1), ('G-5', 1), ('A-5', 6), ('-', 4), ('G-5', 1), ('F-5', 1), ('E-5', 1), ('D-5', 1), ('C#5', 4), ('D-5', 8), ('-', 8),
                      ('A-4', 1), ('G-4', 1), ('A-4', 6), ('-', 4), ('E-4', 2), ('F-4', 2), ('C#4', 4), ('D-4', 16)], vol=52)
    t.seq(I, 1, ORG2, [('D-4', 12), ('-', 4), ('E-4', 8), ('D-4', 8), ('-', 8), ('A-3', 12), ('-', 4), ('C#4', 8), ('D-4', 16)], vol=36)
    for r in range(48, 64): t.note(I, r, 6, 'D-3' if r % 2 == 0 else 'A-2', TIMP, 36 + (r - 48) * 2)
    def drive(p, roots):
        t.drum(p, 4, KICK, 'X...X...X...X...'); t.drum(p, 5, SN, '....X.......X..x', vols=(44, 32))
        for b, r in enumerate(roots):
            for row in range(0, 16, 2): t.note(p, b * 16 + row, 2, n(r) - (12 if row % 4 else 0), BASS, 46, 2)
    A = t.pat(64); drive(A, ['D-3', 'C-3', 'A#2', 'A-2'])
    t.arp(A, 3, HARP, [('D-4', 'm'), ('C-4', 'M'), ('A#3', 'M'), ('A-3', 'M')], step=1, order=(0, 1, 2, 3, 2, 1), vol=26)
    t.seq(A, 0, ORG, [('D-5', 4), ('F-5', 4), ('A-5', 4), ('D-6', 4), ('C#6', 8), ('A-5', 8), ('A#5', 6), ('A-5', 2), ('G-5', 4), ('F-5', 4), ('E-5', 8), ('C#5', 8)], vol=50)
    t.block(A, [1], ORG2, [('D-4', 'm'), ('C-4', 'M'), ('A#3', 'M'), ('A-3', 'M')], vol=26, ln=2, hits=(0, 4, 8, 12))
    B = t.pat(64); drive(B, ['A#2', 'C-3', 'D-3', 'A-2'])
    t.arp(B, 3, HARP, [('A#3', 'M'), ('C-4', 'M'), ('D-4', 'm'), ('A-3', '7')], step=1, order=(0, 2, 1, 3), vol=26)
    t.seq(B, 0, ORG, [('F-5', 8), ('G-5', 8), ('A-5', 8), ('C-6', 8), ('D-6', 6), ('C-6', 2), ('A#5', 4), ('A-5', 4), ('A-5', 16)], vol=52)
    t.block(B, [1], ORG2, [('A#3', 'M'), ('C-4', 'M'), ('D-4', 'm'), ('A-3', '7')], vol=26, ln=2, hits=(0, 4, 8, 12))
    t.note(B, 0, 6, 'D-3', TIMP, 50); t.note(B, 32, 6, 'D-3', TIMP, 50)
    return t.save(OUT + 'kimantero.it', [I, A, B, A, B])

def tango():   # dynamiczne tango (QUICK MATCH i FAST & FURIOUS): bandoneon, skrzypce, marcato, habanera 3-3-2
    t = T('Tango Furioso', 7, tempo=124)
    BAND = add_tonal(t.s, 'bandoneon', 'reed', 56); BAND2 = add_tonal(t.s, 'bandoneon2', 'reed', 44); VIO = add_tonal(t.s, 'violin', 'strings', 52)
    PIANO = add_decay(t.s, 'piano', [1, .55, .35, .2, .12, .08], 0.45, 0.22); BASS = add_decay(t.s, 'bass', [1, .45, .25, .1], 0.4, 0.2)
    KNOCK = add_drum(t.s, 'knock'); CR = add_drum(t.s, 'crash')
    prog = [('D-4', 'm'), ('A-3', '7'), ('D-4', 'm'), ('G-3', 'm'), ('D-4', 'm'), ('E-3', '7'), ('A-3', '7'), ('D-4', 'm')]
    def marcato(p, part):
        for b, (r, q) in enumerate(part):
            for row in (0, 6, 12):   # habanera 3-3-2
                t.note(p, b * 16 + row, 4, n(r) - 12 if row != 6 else n(r) - 5, BASS, 50 if row == 0 else 40, 3)
            for row in (0, 4, 8, 12):
                for k, nt in enumerate(t.chord_notes(r, q)[:2]): pass
            t.block(p, [3], PIANO, [(r, q)], vol=34 if True else 30, ln=2, hits=(0, 4, 8, 12), start=b * 16)
        t.drum(p, 5, KNOCK, 'X.....x.....x...', vols=(36, 28))
    A = t.pat(64, tempo=124, speed=6); marcato(A, prog[:4])
    t.seq(A, 0, BAND, [('A-5', 3), ('-', 1), ('A-5', 2), ('A#5', 2), ('A-5', 2), ('G-5', 2), ('F-5', 4), ('E-5', 12), ('-', 4), ('F-5', 2), ('G-5', 2), ('A-5', 4), ('A#5', 3), ('A-5', 1), ('G-5', 4), ('D-5', 12), ('-', 4)], vol=50)
    t.note(A, 0, 6, 'C-5', CR, 30)
    B = t.pat(64); marcato(B, prog[4:])
    t.seq(B, 0, BAND, [('D-6', 3), ('C#6', 1), ('D-6', 4), ('A#5', 4), ('G-5', 4), ('E-5', 8), ('G#5', 4), ('B-5', 4), ('A-5', 3), ('G-5', 1), ('F-5', 4), ('E-5', 4), ('C#5', 4), ('D-5', 16)], vol=50)
    t.seq(B, 1, VIO, [('F-5', 16), ('G#5', 16), ('E-5', 16), ('F-5', 16)], vol=30, fx=(8, 0x34))
    C = t.pat(64); marcato(C, prog[:4])   # skrzypce przejmuja melodie, bandoneon w tercjach
    t.seq(C, 1, VIO, [('D-6', 8), ('C#6', 4), ('E-6', 4), ('A-5', 12), ('-', 4), ('A#5', 4), ('A-5', 4), ('G-5', 4), ('F-5', 4), ('E-5', 16)], vol=44, fx=(8, 0x34))
    t.seq(C, 2, BAND2, [('F-5', 8), ('E-5', 4), ('G-5', 4), ('F-5', 12), ('-', 4), ('G-5', 4), ('F-5', 4), ('E-5', 4), ('D-5', 4), ('C#5', 16)], vol=30)
    for r in range(56, 64): t.note(C, r, 0, n('A-4') + (r - 56) * 2, BAND, 30 + (r - 56) * 2, 1)   # arrastre: rozped do frazy
    return t.save(OUT + 'tango.it', [A, B, C, B])

if __name__ == '__main__':
    for f in [globals()[a] for a in (sys.argv[1:] or ['malten', 'waller', 'doppler', 'changero', 'chronos', 'magneton', 'telementor', 'blinker', 'kimantero', 'tango'])]:
        print(f.__name__, f(), 'B')
