# Prosty zapis modulu Impulse Tracker (.it) w trybie probek (bez instrumentow).
import struct, numpy as np

class Song:
    def __init__(self, name, channels, speed=6, tempo=125):
        self.name, self.nch, self.speed, self.tempo = name, channels, speed, tempo
        self.samples, self.patterns, self.orders = [], [], []
    def add_sample(self, name, data, rate, loop=None, vol=64):
        # data: float -1..1; zapis 16-bit ze znakiem. loop = (poczatek, koniec) w probkach
        pcm = np.clip(np.round(np.asarray(data) * 125), -128, 127).astype('i1')   # 8 bitow ze znakiem
        self.samples.append((name, pcm, rate, loop, vol)); return len(self.samples)
    def new_pattern(self, rows=64):
        self.patterns.append([[None] * self.nch for _ in range(rows)]); return len(self.patterns) - 1
    def put(self, pat, row, ch, note=None, smp=None, vol=None, cmd=None, val=0):
        cur = self.patterns[pat][row][ch] or [None, None, None, None, 0]
        if note is not None: cur[0] = note
        if smp is not None: cur[1] = smp
        if vol is not None: cur[2] = vol
        if cmd is not None: cur[3], cur[4] = cmd, val
        self.patterns[pat][row][ch] = cur
    def save(self, path):
        nord = len(self.orders) + 1
        hdr = bytearray(192)
        hdr[0:4] = b'IMPM'; hdr[4:4 + len(self.name)] = self.name.encode()[:25]
        struct.pack_into('<HHHHHHHHH', hdr, 30, 0x1004, nord, len(self.samples), len(self.samples), len(self.patterns), 0x0214, 0x0200, 0x000D, 0)
        hdr[48:54] = bytes([128, 48, self.speed, self.tempo, 128, 0])
        for c in range(64):
            hdr[64 + c] = 32 if c < self.nch else 160
            hdr[128 + c] = 64
        orders = bytes(self.orders) + b'\xff'
        ns = len(self.samples)
        off = 192 + len(orders) + 4 * ns + 4 * ns + 4 * len(self.patterns)
        ins_off, ins_blob = [], b''
        for i, (name, pcm, rate, loop, vol) in enumerate(self.samples):
            ih = bytearray(554)
            ih[0:4] = b'IMPI'; ih[4:4 + min(12, len(name))] = name.encode()[:12]
            ih[17] = 0                      # NNA: cut
            struct.pack_into('<H', ih, 20, 256)   # fadeout
            ih[23] = 60; ih[24] = 128; ih[25] = 160   # PPC, glosnosc globalna, bez wymuszonej panoramy
            struct.pack_into('<H', ih, 28, 0x0214); ih[30] = 1
            ih[32:32 + min(25, len(name))] = name.encode()[:25]
            ih[58] = 0; ih[59] = 0; ih[60] = 0; ih[61] = 0xFF
            for k in range(120):
                ih[64 + 2 * k] = k; ih[64 + 2 * k + 1] = i + 1   # kazda nuta -> ta probka
            # obwiednia glosnosci: pelna glosnosc podtrzymana do konca nuty (bez niej sterownik
            # konsoli od razu wycisza dzwiek)
            ih[304] = 1 | 4; ih[305] = 2; ih[306] = 0; ih[307] = 0; ih[308] = 1; ih[309] = 1
            struct.pack_into('<BH', ih, 310, 64, 0); struct.pack_into('<BH', ih, 313, 64, 10)
            ins_off.append(off + len(ins_blob)); ins_blob += bytes(ih)
        off += len(ins_blob)
        smp_off, smp_hdrs = [], b''
        for _ in self.samples:
            smp_off.append(off); off += 80
        pat_off, pat_data = [], b''
        for p in self.patterns:
            body = bytearray()
            for row in p:
                for ch, e in enumerate(row):
                    if not e: continue
                    mask = (1 if e[0] is not None else 0) | (2 if e[1] is not None else 0) | (4 if e[2] is not None else 0) | (8 if e[3] is not None else 0)
                    body += bytes([(ch + 1) | 0x80, mask])
                    if mask & 1: body.append(e[0])
                    if mask & 2: body.append(e[1])
                    if mask & 4: body.append(e[2])
                    if mask & 8: body += bytes([e[3], e[4]])
                body.append(0)
            blk = struct.pack('<HHI', len(body), len(p), 0) + bytes(body)
            pat_off.append(off + len(pat_data)); pat_data += blk
        off += len(pat_data)
        data_blob = b''
        for i, (name, pcm, rate, loop, vol) in enumerate(self.samples):
            sh = bytearray(80)
            sh[0:4] = b'IMPS'; sh[4:4 + min(12, len(name))] = name.encode()[:12]
            flg = 1 | (0x10 if loop else 0)
            sh[17] = 64; sh[18] = flg; sh[19] = vol
            sh[20:20 + min(25, len(name))] = name.encode()[:25]
            sh[46] = 1; sh[47] = 32
            lb, le = loop if loop else (0, 0)
            struct.pack_into('<IIIIIII', sh, 48, len(pcm), lb, le, int(rate), 0, 0, off + len(data_blob))
            smp_hdrs += bytes(sh); data_blob += pcm.tobytes()
        out = bytes(hdr) + orders + b''.join(struct.pack('<I', o) for o in ins_off) + b''.join(struct.pack('<I', o) for o in smp_off) + b''.join(struct.pack('<I', o) for o in pat_off)
        out += ins_blob + smp_hdrs + pat_data + data_blob
        open(path, 'wb').write(out)
        return len(out)

NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def n(name):   # 'D-4', 'A#5', 'C#3'
    if name[1] == '#': return NOTE[name[:2]] + 12 * int(name[2:])
    return NOTE[name[0]] + 12 * int(name[2:])
CUT = 254
