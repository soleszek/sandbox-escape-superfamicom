# Grzmot burzy w walce z Kimantero: osobny efekt z banku dzwiekow (music/stormfx.it, pierwszy modul),
# grany przez spcEffect na wlasnym glosie - odbicia pilki (strumien spcPlaySound) go nie ucinaja.
# Glosniejszy i jasniejszy od dawnego grzmotu (thunder.wav, ktory zostaje dla Lucifero), zeby przebijal
# sie przez muzyke: krotszy trzask, pomruk z wiekszym udzialem srednich czestotliwosci, lagodne nasycenie.
# Uruchamiac z katalogu projektu: python3 tools/make_storm_fx.py
import os, sys
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from itwriter import Song, n
sr = 12000; N = int(sr * 1.0); t = np.arange(N) / sr
rng = np.random.default_rng(7)
crack = rng.standard_normal(N) * np.exp(-t / 0.05)
brown = np.cumsum(rng.standard_normal(N)); brown -= np.convolve(brown, np.ones(240) / 240, mode='same')
rum = brown / (np.abs(brown).max() + 1e-9)
rum = np.convolve(rum, np.ones(6) / 6, mode='same')
swell = (1 - np.exp(-t / 0.03)) * np.exp(-t / 0.40) * (1 + 0.45 * np.sin(2 * np.pi * 4.3 * t))
x = 0.6 * crack + 1.2 * rum * swell
x = np.tanh(2.2 * x / np.abs(x).max()); x = 0.97 * x / np.abs(x).max()
fade = np.ones(N); fade[-600:] = np.linspace(1, 0, 600); x *= fade
s = Song('STORMFX', 1)
s.add_sample('THUNDER', x, sr, vol=64)
p = s.new_pattern(16); s.put(p, 0, 0, note=n('C-5'), smp=1)
os.makedirs('music', exist_ok=True)
s.save(os.path.join('music', 'stormfx.it'))
print('music/stormfx.it: grzmot burzy %.2f s, srednia glosnosc %.3f' % (N / sr, np.sqrt((x ** 2).mean())))
