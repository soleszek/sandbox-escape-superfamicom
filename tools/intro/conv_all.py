# Konwersja scen obrazkowych intro (scena 1: 11 klatek ze wspolnymi paletami; 4 przebitki)
import sys, pickle
import numpy as np
from PIL import Image
import os as _os
HERE = _os.path.dirname(_os.path.abspath(__file__))          # tools/intro
WORK = _os.path.join(HERE, 'work')                                  # pliki posrednie (generowane)
PROJ = _os.path.abspath(_os.path.join(HERE, '..', '..'))           # katalog gry
_os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, HERE)
from snesconv import convert_best, pack
import scene1
_pk = _os.path.join(WORK, 'conv.pkl')
out = pickle.load(open(_pk, 'rb')) if _os.path.exists(_pk) else {}
ONLY_S1 = len(sys.argv) > 1 and sys.argv[1] == 's1'
ONLY_FL = len(sys.argv) > 1 and sys.argv[1] == 'fl'
ONLY_LOGO = len(sys.argv) > 1 and sys.argv[1] == 'logo'
if not ONLY_FL and not ONLY_LOGO:
    ims = [Image.open(_os.path.join(WORK, 's1_%02d.png') % i) for i in range(len(scene1.VARIANTS))]
    big = Image.new('RGB', (256, 224 * len(ims)))
    for k, im in enumerate(ims):
        big.paste(im, (0, 224 * k))
    prev, idx, grp, full, total = convert_best(big, tries=3, npal=7)
    t, m, p = pack(idx, grp, full, pal_base=1)
    out['s1'] = (t, m, p)
    prev.save(_os.path.join(WORK, 's1_prev_all.png'))
    print('scena 1: kafelkow', len(t) // 32)

import flashes
for k in ([] if ONLY_S1 or ONLY_LOGO else range(4)):
    fn = flashes.SCENES[k]
    frames = [fn(s) for s in flashes.STATES[k]]          # klatki animacji przebitki (wspolne palety)
    big = Image.new('RGB', (256, 224 * len(frames)))
    for i, im in enumerate(frames):
        big.paste(im, (0, 224 * i))
    prev, idx, grp, full, total = convert_best(big, tries=4, npal=8)
    t, m, p = pack(idx, grp, full)
    maps = [m[i * 1792:(i + 1) * 1792] for i in range(len(frames))]
    out['fl%d' % k] = (t, maps, p)
    prev.save(_os.path.join(WORK, 'fl_prev_%d.png') % k)
    print('przebitka', k, 'klatek', len(frames), 'kafelkow', len(t) // 32)
import logo                               # ekran producenta (logo MaiFlow)
if not ONLY_S1 and not ONLY_FL:
    prev, idx, grp, full, total = convert_best(logo.logo_screen(), tries=4, npal=8)
    t, m, p = pack(idx, grp, full)
    out['logo'] = (t, m, p)
    prev.save(_os.path.join(WORK, 'logo_prev.png'))
    print('logo: kafelkow', len(t) // 32)
pickle.dump(out, open(_os.path.join(WORK, 'conv.pkl'), 'wb'))
